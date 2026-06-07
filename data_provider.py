"""
data_provider.py
================
Handles all data fetching, caching, and preprocessing via the FastF1 library.

Separating data concerns from UI ensures the module is independently testable
and keeps app.py focused on rendering logic.
"""

from __future__ import annotations

import os
import logging
from pathlib import Path
from typing import Optional

import fastf1
import pandas as pd
import streamlit as st

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────
#  Cache Configuration
# ─────────────────────────────────────────────
CACHE_DIR = Path(".fastf1_cache")
CACHE_DIR.mkdir(exist_ok=True)
fastf1.Cache.enable_cache(str(CACHE_DIR))

# ─────────────────────────────────────────────
#  Static Reference Data
# ─────────────────────────────────────────────
YEARS: list[int] = [2026, 2025, 2024, 2023, 2022, 2021, 2020]

SESSION_TYPES: list[str] = ["Qualifying", "Race", "Sprint", "Practice 1", "Practice 2", "Practice 3"]

# Representative circuit lists per season.
# Covers official calendar names recognised by FastF1 / Ergast.
# 2025 & 2026 calendars reflect confirmed/expected rounds as of mid-2025.
CIRCUITS: dict[int, list[str]] = {
    # ── 2026 ── (confirmed calendar; subject to change)
    2026: [
        "Australia", "China", "Bahrain", "Saudi Arabia", "Miami",
        "Emilia Romagna", "Monaco", "Spain", "Canada", "Austria",
        "Great Britain", "Belgium", "Hungary", "Netherlands", "Italy",
        "Azerbaijan", "Singapore", "United States", "Mexico City",
        "São Paulo", "Las Vegas", "Qatar", "Abu Dhabi",
    ],
    # ── 2025 ──
    2025: [
        "Australia", "China", "Japan", "Bahrain", "Saudi Arabia",
        "Miami", "Emilia Romagna", "Monaco", "Spain", "Canada",
        "Austria", "Great Britain", "Belgium", "Hungary", "Netherlands",
        "Italy", "Azerbaijan", "Singapore", "United States", "Mexico City",
        "São Paulo", "Las Vegas", "Qatar", "Abu Dhabi",
    ],
    # ── 2024 ──
    2024: [
        "Bahrain", "Saudi Arabia", "Australia", "Japan", "China",
        "Miami", "Emilia Romagna", "Monaco", "Canada", "Spain",
        "Austria", "Great Britain", "Hungary", "Belgium", "Netherlands",
        "Italy", "Azerbaijan", "Singapore", "United States", "Mexico City",
        "São Paulo", "Las Vegas", "Qatar", "Abu Dhabi",
    ],
    # ── 2023 ──
    2023: [
        "Bahrain", "Saudi Arabia", "Australia", "Azerbaijan", "Miami",
        "Monaco", "Spain", "Canada", "Austria", "Great Britain",
        "Hungary", "Belgium", "Netherlands", "Italy", "Singapore",
        "Japan", "Qatar", "United States", "Mexico City", "São Paulo",
        "Las Vegas", "Abu Dhabi",
    ],
    # ── 2022 ──
    2022: [
        "Bahrain", "Saudi Arabia", "Australia", "Emilia Romagna", "Miami",
        "Spain", "Monaco", "Azerbaijan", "Canada", "Great Britain",
        "Austria", "France", "Hungary", "Belgium", "Netherlands",
        "Italy", "Singapore", "Japan", "United States", "Mexico City",
        "São Paulo", "Abu Dhabi",
    ],
    # ── 2021 ──
    2021: [
        "Bahrain", "Emilia Romagna", "Portugal", "Spain", "Monaco",
        "Azerbaijan", "France", "Styria", "Austria", "Great Britain",
        "Hungary", "Belgium", "Netherlands", "Italy", "Russia",
        "Turkey", "United States", "Mexico City", "São Paulo",
        "Qatar", "Saudi Arabia", "Abu Dhabi",
    ],
    # ── 2020 ── (COVID-shortened season, no Australian GP)
    2020: [
        "Austria", "Styria", "Hungary", "Great Britain", "70th Anniversary",
        "Spain", "Belgium", "Italy", "Tuscany", "Russia",
        "Eifel", "Portugal", "Emilia Romagna", "Turkey", "Bahrain",
        "Sakhir", "Abu Dhabi",
    ],
}


# ─────────────────────────────────────────────
#  Session Loading
# ─────────────────────────────────────────────
@st.cache_resource(show_spinner=False)
def load_session(year: int, circuit: str, session_type: str) -> fastf1.core.Session:
    """
    Load and return a FastF1 session, fully parsed with laps and telemetry.

    Uses Streamlit's ``cache_resource`` so the heavy network call only runs once
    per unique (year, circuit, session_type) combination per app process.

    Parameters
    ----------
    year : int
        Championship season (e.g. 2023).
    circuit : str
        Circuit or event name recognised by FastF1 / Ergast (e.g. "Monaco").
    session_type : str
        One of: "Race", "Qualifying", "Sprint", "Practice 1/2/3".

    Returns
    -------
    fastf1.core.Session
        Fully loaded session object.

    Raises
    ------
    ValueError
        If the session cannot be found or loaded.
    """
    try:
        session = fastf1.get_session(year, circuit, session_type)
        session.load(telemetry=True, laps=True, weather=False, messages=False)
        logger.info("Session loaded: %d %s %s", year, circuit, session_type)
        return session
    except Exception as exc:
        raise ValueError(
            f"Could not load session [{year} | {circuit} | {session_type}]: {exc}"
        ) from exc


# ─────────────────────────────────────────────
#  Session Results
# ─────────────────────────────────────────────
@st.cache_data(show_spinner=False, ttl=3600)
def get_session_results(_session: fastf1.core.Session) -> Optional[pd.DataFrame]:
    """
    Extract a tidy results DataFrame containing driver abbreviations and names.

    Parameters
    ----------
    _session : fastf1.core.Session
        Loaded FastF1 session object. Prefixed with _ to skip Streamlit hashing.

    Returns
    -------
    pd.DataFrame or None
        Columns: Abbreviation, FullName (where available).
    """
    try:
        results = _session.results
        if results is None or results.empty:
            laps = _session.laps
            abbrevs = laps["Driver"].dropna().unique()
            return pd.DataFrame({"Abbreviation": abbrevs})
        return results[["Abbreviation", "FullName"]].drop_duplicates().reset_index(drop=True)
    except Exception as exc:
        logger.warning("Could not extract results: %s", exc)
        return None


# ─────────────────────────────────────────────
#  Fastest Lap
# ─────────────────────────────────────────────
@st.cache_data(show_spinner=False, ttl=3600)
def get_driver_fastest_lap(
    _session: fastf1.core.Session,
    driver: str,
) -> Optional[fastf1.core.Lap]:
    """
    Retrieve the single fastest recorded lap for a driver within a session.

    Parameters
    ----------
    _session : fastf1.core.Session
        Loaded session.
    driver : str
        Three-letter driver abbreviation (e.g. "VER", "HAM").

    Returns
    -------
    fastf1.core.Lap or None
        The fastest lap row, or None if unavailable.
    """
    try:
        laps = _session.laps.pick_driver(driver).pick_quicklaps()
        if laps.empty:
            logger.warning("No quick laps found for driver %s", driver)
            return None
        return laps.pick_fastest()
    except Exception as exc:
        logger.warning("Failed to get fastest lap for %s: %s", driver, exc)
        return None


# ─────────────────────────────────────────────
#  Telemetry for a single lap
# ─────────────────────────────────────────────
@st.cache_data(show_spinner=False, ttl=3600)
def get_lap_telemetry(
    _lap: fastf1.core.Lap,
    smoothing_window: int = 5,
) -> Optional[pd.DataFrame]:
    """
    Extract and lightly smooth telemetry data for a given lap.

    Applies a rolling-mean smooth to the Speed channel to reduce sensor noise
    without distorting braking/acceleration profiles.

    Parameters
    ----------
    _lap : fastf1.core.Lap
        Lap object from which to fetch telemetry.
    smoothing_window : int, optional
        Rolling window size for speed smoothing (default 5 samples).

    Returns
    -------
    pd.DataFrame or None
        Columns include: Distance, Speed, Throttle, Brake, nGear, X, Y.
    """
    try:
        tel = _lap.get_telemetry().add_distance()
        if tel.empty:
            return None

        # Smooth speed trace
        if "Speed" in tel.columns:
            tel["Speed"] = tel["Speed"].rolling(window=smoothing_window, center=True).mean()

        # Normalise Brake to 0–1 float
        if "Brake" in tel.columns:
            tel["Brake"] = tel["Brake"].astype(float)

        return tel.reset_index(drop=True)
    except Exception as exc:
        logger.warning("Telemetry extraction failed: %s", exc)
        return None


# ─────────────────────────────────────────────
#  All laps for a driver (for pace analysis)
# ─────────────────────────────────────────────
@st.cache_data(show_spinner=False, ttl=3600)
def get_all_driver_laps(
    _session: fastf1.core.Session,
    driver: str,
    exclude_outliers: bool = True,
    outlier_threshold: float = 1.07,
) -> Optional[pd.DataFrame]:
    """
    Return all valid laps for a driver with optional outlier filtering.

    Outliers (e.g. in/out laps, safety-car laps) are removed by discarding
    laps longer than ``outlier_threshold`` × the fastest lap time.

    Parameters
    ----------
    _session : fastf1.core.Session
        Loaded session.
    driver : str
        Three-letter driver abbreviation.
    exclude_outliers : bool, optional
        Whether to drop anomalously slow laps (default True).
    outlier_threshold : float, optional
        Multiplier above fastest lap used to identify slow laps (default 1.07).

    Returns
    -------
    pd.DataFrame or None
        Cleaned laps DataFrame.
    """
    try:
        laps = _session.laps.pick_driver(driver).copy()
        if laps.empty:
            return None

        laps = laps.dropna(subset=["LapTime"])
        laps["LapTimeSec"] = laps["LapTime"].dt.total_seconds()

        if exclude_outliers and not laps.empty:
            fastest = laps["LapTimeSec"].min()
            laps = laps[laps["LapTimeSec"] <= fastest * outlier_threshold]

        return laps.reset_index(drop=True)
    except Exception as exc:
        logger.warning("Failed to fetch laps for %s: %s", driver, exc)
        return None


# ─────────────────────────────────────────────
#  Sector comparison helper
# ─────────────────────────────────────────────
def extract_sector_times(lap: Optional[fastf1.core.Lap]) -> dict[str, Optional[float]]:
    """
    Pull sector times from a lap object into a plain dictionary of floats.

    Parameters
    ----------
    lap : fastf1.core.Lap or None
        Target lap.

    Returns
    -------
    dict
        Keys: "S1", "S2", "S3" — values in seconds (float) or None.
    """
    if lap is None:
        return {"S1": None, "S2": None, "S3": None}

    out: dict[str, Optional[float]] = {}
    for key, col in [("S1", "Sector1Time"), ("S2", "Sector2Time"), ("S3", "Sector3Time")]:
        val = lap.get(col)
        out[key] = val.total_seconds() if val is not None and not pd.isna(val) else None

    return out
