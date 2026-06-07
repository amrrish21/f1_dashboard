"""
F1 Telemetry & Analytics Dashboard
====================================
Main Streamlit application entry point.
Handles all UI rendering, user controls, and visualization orchestration.
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
import warnings

from data_provider import (
    load_session,
    get_driver_fastest_lap,
    get_lap_telemetry,
    get_all_driver_laps,
    get_session_results,
    YEARS,
    CIRCUITS,
    SESSION_TYPES,
)

warnings.filterwarnings("ignore")


def hex_to_rgba(hex_color: str, alpha: float = 1.0) -> str:
    """Convert a '#rrggbb' hex string to a valid 'rgba(r,g,b,a)' string for Plotly."""
    hex_color = hex_color.lstrip("#")
    r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
    return f"rgba({r},{g},{b},{alpha})"

# ─────────────────────────────────────────────
#  Page config
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="F1 Telemetry Dashboard",
    page_icon="🏎️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────
#  Custom CSS — dark racing aesthetic
# ─────────────────────────────────────────────
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Inter:wght@300;400;600&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
        background-color: #0a0a0f;
        color: #e0e0e0;
    }
    .stApp { background-color: #0a0a0f; }

    h1, h2, h3 {
        font-family: 'Orbitron', monospace;
        letter-spacing: 0.05em;
    }
    h1 { color: #e10600; font-size: 2rem; }
    h2 { color: #ffffff; font-size: 1.2rem; }
    h3 { color: #cccccc; font-size: 1rem; }

    /* Sidebar */
    section[data-testid="stSidebar"] {
        background-color: #111118;
        border-right: 1px solid #1e1e2e;
    }
    section[data-testid="stSidebar"] .stSelectbox label,
    section[data-testid="stSidebar"] .stSlider label {
        color: #aaaaaa;
        font-size: 0.8rem;
        text-transform: uppercase;
        letter-spacing: 0.1em;
    }

    /* Metric cards */
    [data-testid="metric-container"] {
        background: linear-gradient(135deg, #111118, #1a1a28);
        border: 1px solid #2a2a3e;
        border-radius: 8px;
        padding: 12px 16px;
    }
    [data-testid="metric-container"] label {
        color: #888 !important;
        font-size: 0.7rem !important;
        text-transform: uppercase;
        letter-spacing: 0.12em;
    }
    [data-testid="metric-container"] [data-testid="stMetricValue"] {
        color: #ffffff !important;
        font-family: 'Orbitron', monospace;
        font-size: 1.1rem !important;
    }
    [data-testid="metric-container"] [data-testid="stMetricDelta"] {
        font-size: 0.75rem !important;
    }

    /* Selectboxes */
    .stSelectbox > div > div {
        background-color: #111118;
        border-color: #2a2a3e;
        color: #e0e0e0;
    }

    /* Divider */
    hr { border-color: #1e1e2e; }

    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {
        background-color: #111118;
        border-radius: 8px;
        padding: 4px;
        gap: 4px;
    }
    .stTabs [data-baseweb="tab"] {
        font-family: 'Orbitron', monospace;
        font-size: 0.7rem;
        letter-spacing: 0.1em;
        color: #666;
        background-color: transparent;
        border-radius: 6px;
    }
    .stTabs [aria-selected="true"] {
        color: #e10600 !important;
        background-color: #1e1e2e !important;
    }

    /* Info / warning boxes */
    .stAlert { background-color: #111118; border-radius: 8px; }

    /* Header banner */
    .dashboard-header {
        background: linear-gradient(90deg, #e10600 0%, #a00400 50%, #0a0a0f 100%);
        padding: 20px 28px;
        border-radius: 10px;
        margin-bottom: 24px;
    }
    .dashboard-header h1 { color: #ffffff; margin: 0; font-size: 1.8rem; }
    .dashboard-header p  { color: rgba(255,255,255,0.7); margin: 4px 0 0; font-size: 0.85rem; }

    /* Driver color badges */
    .driver-badge {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 20px;
        font-family: 'Orbitron', monospace;
        font-size: 0.7rem;
        font-weight: 700;
        letter-spacing: 0.1em;
        margin-right: 8px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ─────────────────────────────────────────────
#  Header
# ─────────────────────────────────────────────
st.markdown(
    """
    <div class="dashboard-header">
        <h1>🏎️ F1 TELEMETRY DASHBOARD</h1>
        <p>Real-time Formula 1 data analytics powered by FastF1 • Compare drivers, explore telemetry</p>
    </div>
    """,
    unsafe_allow_html=True,
)

# ─────────────────────────────────────────────
#  Sidebar — Session & Driver Controls
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown("## ⚙️ SESSION CONFIG")
    st.markdown("---")

    selected_year = st.selectbox("📅 Season", YEARS, index=0)
    selected_circuit = st.selectbox("🏁 Circuit", CIRCUITS.get(selected_year, []))
    selected_session = st.selectbox("🎯 Session Type", SESSION_TYPES)

    st.markdown("---")
    st.markdown("## 👤 DRIVER COMPARISON")

    load_btn = st.button("🔄 Load Session Data", use_container_width=True, type="primary")

    st.markdown("---")
    st.markdown(
        """
        <small style='color:#555; font-size:0.72rem;'>
        Data provided by FastF1 & Ergast API.<br>
        Results cached locally for performance.
        </small>
        """,
        unsafe_allow_html=True,
    )

# ─────────────────────────────────────────────
#  Session loading
# ─────────────────────────────────────────────
if "session" not in st.session_state:
    st.session_state["session"] = None
    st.session_state["results"] = None

if load_btn:
    with st.spinner(f"Loading {selected_year} {selected_circuit} — {selected_session}…"):
        try:
            session = load_session(selected_year, selected_circuit, selected_session)
            results = get_session_results(session)
            st.session_state["session"] = session
            st.session_state["results"] = results
            st.session_state["year"] = selected_year
            st.session_state["circuit"] = selected_circuit
            st.session_state["session_type"] = selected_session
            st.success("✅ Session loaded successfully!")
        except Exception as exc:
            st.error(f"❌ Failed to load session: {exc}")
            st.stop()

session = st.session_state.get("session")
results = st.session_state.get("results")

if session is None:
    st.info(
        "👈 **Select a season, circuit, and session type** in the sidebar, then click **Load Session Data** to begin."
    )
    st.stop()

# ─────────────────────────────────────────────
#  Driver selectors (populated after session load)
# ─────────────────────────────────────────────
available_drivers = list(results["Abbreviation"].dropna().unique()) if results is not None else []

if len(available_drivers) < 2:
    st.warning("Not enough driver data in this session.")
    st.stop()

col_d1, col_d2 = st.columns(2)
with col_d1:
    driver1 = st.selectbox("🔴 Driver 1", available_drivers, index=0, key="d1")
with col_d2:
    remaining = [d for d in available_drivers if d != driver1]
    driver2 = st.selectbox("🔵 Driver 2", remaining, index=min(1, len(remaining) - 1), key="d2")

# ─────────────────────────────────────────────
#  Fetch lap + telemetry data for both drivers
# ─────────────────────────────────────────────
DRIVER_COLORS = {driver1: "#e10600", driver2: "#00aaff"}

with st.spinner("Fetching telemetry data…"):
    try:
        lap1 = get_driver_fastest_lap(session, driver1)
        lap2 = get_driver_fastest_lap(session, driver2)
        tel1 = get_lap_telemetry(lap1) if lap1 is not None else None
        tel2 = get_lap_telemetry(lap2) if lap2 is not None else None
        laps1 = get_all_driver_laps(session, driver1)
        laps2 = get_all_driver_laps(session, driver2)
    except Exception as exc:
        st.error(f"❌ Telemetry fetch error: {exc}")
        st.stop()

# ─────────────────────────────────────────────
#  KPI Metrics Row
# ─────────────────────────────────────────────
st.markdown("## 📊 KEY PERFORMANCE INDICATORS")
kpi_cols = st.columns(6)

def fmt_lap(t) -> str:
    """Format a lap timedelta as M:SS.mmm string."""
    if t is None or pd.isna(t):
        return "N/A"
    total = t.total_seconds()
    mins = int(total // 60)
    secs = total % 60
    return f"{mins}:{secs:06.3f}"

def max_speed(tel) -> str:
    """Return max speed from telemetry or 'N/A'."""
    if tel is None or "Speed" not in tel.columns:
        return "N/A"
    return f"{tel['Speed'].max():.0f} km/h"

def avg_lap(laps) -> str:
    """Return mean lap time from a laps dataframe."""
    if laps is None or laps.empty or "LapTime" not in laps.columns:
        return "N/A"
    mean_t = laps["LapTime"].dropna().mean()
    if pd.isna(mean_t):
        return "N/A"
    return fmt_lap(mean_t)

lap1_time = lap1["LapTime"] if lap1 is not None else None
lap2_time = lap2["LapTime"] if lap2 is not None else None

delta_sec: float | None = None
if lap1_time is not None and lap2_time is not None:
    delta_sec = (lap2_time - lap1_time).total_seconds()

kpi_cols[0].metric(f"🔴 {driver1} Best", fmt_lap(lap1_time))
kpi_cols[1].metric(f"🔵 {driver2} Best", fmt_lap(lap2_time),
                   delta=f"{delta_sec:+.3f}s" if delta_sec is not None else None,
                   delta_color="inverse")
kpi_cols[2].metric(f"🔴 {driver1} Top Speed", max_speed(tel1))
kpi_cols[3].metric(f"🔵 {driver2} Top Speed", max_speed(tel2))
kpi_cols[4].metric(f"🔴 {driver1} Avg Lap", avg_lap(laps1))
kpi_cols[5].metric(f"🔵 {driver2} Avg Lap", avg_lap(laps2))

st.markdown("---")

# ─────────────────────────────────────────────
#  Tab layout
# ─────────────────────────────────────────────
tab_tele, tab_pace, tab_track, tab_sectors = st.tabs(
    ["📡 Speed Trace", "⏱️ Lap Pace", "🗺️ Track Map", "📈 Sector Analysis"]
)

# ════════════════════════════════════════════
#  TAB 1 — Telemetry Speed Trace
# ════════════════════════════════════════════
with tab_tele:
    st.markdown("### SPEED TRACE — Fastest Lap Comparison")
    if tel1 is None and tel2 is None:
        st.warning("No telemetry data available for either driver.")
    else:
        fig = make_subplots(
            rows=3, cols=1,
            shared_xaxes=True,
            subplot_titles=("Speed (km/h)", "Throttle (%)", "Brake"),
            vertical_spacing=0.07,
            row_heights=[0.55, 0.25, 0.20],
        )

        for tel, driver, color in [(tel1, driver1, DRIVER_COLORS[driver1]),
                                   (tel2, driver2, DRIVER_COLORS[driver2])]:
            if tel is None:
                continue
            dist = tel.get("Distance", tel.index)
            fig.add_trace(
                go.Scatter(x=dist, y=tel["Speed"], name=f"{driver} — Speed",
                           line=dict(color=color, width=2), legendgroup=driver),
                row=1, col=1,
            )
            if "Throttle" in tel.columns:
                fig.add_trace(
                    go.Scatter(x=dist, y=tel["Throttle"], name=f"{driver} — Throttle",
                               line=dict(color=color, width=1.5, dash="dot"),
                               legendgroup=driver, showlegend=False),
                    row=2, col=1,
                )
            if "Brake" in tel.columns:
                brake = tel["Brake"].astype(float)
                fig.add_trace(
                    go.Scatter(x=dist, y=brake, name=f"{driver} — Brake",
                               fill="tozeroy", fillcolor=hex_to_rgba(color, 0.15),
                               line=dict(color=color, width=1),
                               legendgroup=driver, showlegend=False),
                    row=3, col=1,
                )

        fig.update_layout(
            template="plotly_dark",
            paper_bgcolor="#0a0a0f",
            plot_bgcolor="#111118",
            font=dict(family="Inter", size=12, color="#cccccc"),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0),
            height=540,
            margin=dict(l=10, r=10, t=40, b=10),
        )
        fig.update_xaxes(gridcolor="#1e1e2e", title_text="Distance (m)", row=3, col=1)
        fig.update_yaxes(gridcolor="#1e1e2e")
        st.plotly_chart(fig, use_container_width=True)

# ════════════════════════════════════════════
#  TAB 2 — Lap Pace (violin + scatter)
# ════════════════════════════════════════════
with tab_pace:
    st.markdown("### LAP PACE DISTRIBUTION")

    frames = []
    for laps, driver, color in [(laps1, driver1, DRIVER_COLORS[driver1]),
                                 (laps2, driver2, DRIVER_COLORS[driver2])]:
        if laps is None or laps.empty:
            continue
        df = laps[["LapNumber", "LapTime"]].dropna().copy()
        df["LapTimeSec"] = df["LapTime"].dt.total_seconds()
        df["Driver"] = driver
        df["Color"] = color
        frames.append(df)

    if frames:
        combined = pd.concat(frames, ignore_index=True)

        fig = go.Figure()
        for driver, color in DRIVER_COLORS.items():
            sub = combined[combined["Driver"] == driver]
            if sub.empty:
                continue
            fig.add_trace(go.Violin(
                y=sub["LapTimeSec"],
                name=driver,
                box_visible=True,
                meanline_visible=True,
                fillcolor=hex_to_rgba(color, 0.25),
                line_color=color,
                opacity=0.8,
            ))
            fig.add_trace(go.Scatter(
                x=[driver] * len(sub),
                y=sub["LapTimeSec"],
                mode="markers",
                marker=dict(color=color, size=5, opacity=0.6,
                            line=dict(color="#0a0a0f", width=0.5)),
                name=driver,
                showlegend=False,
            ))

        fig.update_layout(
            template="plotly_dark",
            paper_bgcolor="#0a0a0f",
            plot_bgcolor="#111118",
            yaxis_title="Lap Time (seconds)",
            height=420,
            margin=dict(l=10, r=10, t=20, b=10),
            violinmode="overlay",
        )
        st.plotly_chart(fig, use_container_width=True)

        st.markdown("### LAP-BY-LAP EVOLUTION")
        fig2 = go.Figure()
        for driver, color in DRIVER_COLORS.items():
            sub = combined[combined["Driver"] == driver]
            if sub.empty:
                continue
            fig2.add_trace(go.Scatter(
                x=sub["LapNumber"], y=sub["LapTimeSec"],
                mode="lines+markers",
                name=driver,
                line=dict(color=color, width=2),
                marker=dict(size=5),
            ))
        fig2.update_layout(
            template="plotly_dark",
            paper_bgcolor="#0a0a0f",
            plot_bgcolor="#111118",
            xaxis_title="Lap Number",
            yaxis_title="Lap Time (s)",
            height=340,
            margin=dict(l=10, r=10, t=10, b=10),
        )
        st.plotly_chart(fig2, use_container_width=True)
    else:
        st.warning("No lap data available for selected drivers.")

# ════════════════════════════════════════════
#  TAB 3 — Track Map
# ════════════════════════════════════════════
with tab_track:
    st.markdown("### TRACK MAP — Colour-coded by Speed")

    col_ref, _ = st.columns([1, 3])
    map_driver = col_ref.selectbox("Map reference driver", [driver1, driver2], key="map_drv")

    ref_tel = tel1 if map_driver == driver1 else tel2

    if ref_tel is None or "X" not in ref_tel.columns or "Y" not in ref_tel.columns:
        st.warning("Track coordinates unavailable for this driver / session.")
    else:
        color_by = st.radio("Colour by", ["Speed", "nGear", "Throttle"], horizontal=True)
        color_col = color_by if color_by in ref_tel.columns else "Speed"
        color_series = ref_tel[color_col].fillna(0)

        fig = go.Figure(go.Scatter(
            x=ref_tel["X"],
            y=ref_tel["Y"],
            mode="markers",
            marker=dict(
                color=color_series,
                colorscale="plasma" if color_col == "Speed" else "viridis",
                size=4,
                colorbar=dict(title=color_col, tickfont=dict(color="#aaa")),
                line=dict(width=0),
            ),
            text=[f"{color_col}: {v:.1f}" for v in color_series],
            hoverinfo="text",
        ))
        fig.update_layout(
            template="plotly_dark",
            paper_bgcolor="#0a0a0f",
            plot_bgcolor="#0a0a0f",
            xaxis=dict(visible=False, scaleanchor="y", scaleratio=1),
            yaxis=dict(visible=False),
            height=520,
            margin=dict(l=0, r=0, t=20, b=0),
        )
        st.plotly_chart(fig, use_container_width=True)

# ════════════════════════════════════════════
#  TAB 4 — Sector Analysis
# ════════════════════════════════════════════
with tab_sectors:
    st.markdown("### SECTOR TIME BREAKDOWN — Fastest Lap")

    sector_data = []
    for lap, driver in [(lap1, driver1), (lap2, driver2)]:
        if lap is None:
            continue
        for s in ["Sector1Time", "Sector2Time", "Sector3Time"]:
            val = lap.get(s)
            if val is not None and not pd.isna(val):
                sector_data.append({
                    "Driver": driver,
                    "Sector": s.replace("Time", "").replace("Sector", "S"),
                    "Seconds": val.total_seconds(),
                })

    if sector_data:
        df_s = pd.DataFrame(sector_data)
        fig = px.bar(
            df_s, x="Sector", y="Seconds", color="Driver",
            barmode="group",
            color_discrete_map=DRIVER_COLORS,
            template="plotly_dark",
            text=df_s["Seconds"].apply(lambda x: f"{x:.3f}s"),
        )
        fig.update_traces(textposition="outside")
        fig.update_layout(
            paper_bgcolor="#0a0a0f",
            plot_bgcolor="#111118",
            height=380,
            margin=dict(l=10, r=10, t=20, b=10),
            yaxis_title="Time (seconds)",
            legend=dict(orientation="h", y=1.05),
        )
        st.plotly_chart(fig, use_container_width=True)

        # Delta table
        st.markdown("#### ⏱️ Sector Deltas")
        pivot = df_s.pivot(index="Sector", columns="Driver", values="Seconds")
        if driver1 in pivot.columns and driver2 in pivot.columns:
            pivot["Delta (D2 - D1)"] = pivot[driver2] - pivot[driver1]
            pivot = pivot.reset_index()
            st.dataframe(
                pivot.style.format(
                    {c: "{:.3f}s" for c in pivot.columns if c != "Sector"}
                ).background_gradient(subset=["Delta (D2 - D1)"], cmap="RdYlGn_r"),
                use_container_width=True,
            )
    else:
        st.warning("Sector times not available for this session.")

# ─────────────────────────────────────────────
#  Footer
# ─────────────────────────────────────────────
st.markdown("---")
st.markdown(
    """
    <div style='text-align:center; color:#333; font-size:0.75rem; padding:12px 0;'>
    F1 Telemetry Dashboard • Built with FastF1, Streamlit & Plotly •
    Data © Formula One Management Ltd
    </div>
    """,
    unsafe_allow_html=True,
)
