# 🏎️ F1 Telemetry & Analytics Dashboard

> A production-grade **Formula 1 telemetry analytics web app** built with FastF1, Streamlit, and Plotly.
> Explore driver comparisons, speed traces, track maps, and sector breakdowns for any session from 2021–2024.

[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python&logoColor=white)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.35%2B-FF4B4B?logo=streamlit&logoColor=white)](https://streamlit.io)
[![FastF1](https://img.shields.io/badge/FastF1-3.3%2B-orange)](https://docs.fastf1.dev)
[![Plotly](https://img.shields.io/badge/Plotly-5.22%2B-3F4F75?logo=plotly&logoColor=white)](https://plotly.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

---

## 📸 Features at a Glance

| Feature | Description |
|---|---|
| **Session Selector** | Choose any Season (2020–2026), Circuit, and Session type (Race, Qualifying, Practice, Sprint) |
| **Driver Comparison** | Pick any two drivers from the loaded session for head-to-head analysis |
| **KPI Metrics** | Fastest lap time, top speed, average lap time — with head-to-head delta |
| **Speed Trace** | Speed, Throttle, and Brake plotted against lap distance for each driver's fastest lap |
| **Lap Pace** | Violin + scatter plot of all laps; lap-by-lap evolution line chart |
| **Track Map** | 2-D circuit geometry colour-coded by Speed, Gear, or Throttle |
| **Sector Analysis** | S1/S2/S3 bar chart + delta table with conditional formatting |
| **Smart Caching** | FastF1 disk cache + Streamlit `@cache_resource` / `@cache_data` prevent redundant API calls |

---

## 🗂️ Project Structure

```
f1_dashboard/
├── app.py               # Streamlit UI — all rendering & user controls
├── data_provider.py     # Data layer — FastF1 fetching, caching & preprocessing
├── requirements.txt     # Python dependencies
├── .gitignore           # Excludes cache dirs, venvs, secrets
└── README.md            # This file
```

The project follows a strict **separation of concerns**:

- **`data_provider.py`** — knows nothing about Streamlit. Every public function is independently importable and unit-testable.
- **`app.py`** — knows nothing about FastF1 internals. It only calls functions from `data_provider` and renders results.

---

## ⚙️ Installation

### Prerequisites

- Python **3.10 or newer**
- `pip` or a virtual environment manager (`venv`, `conda`, `poetry`)

### 1. Clone the repository

```bash
git clone https://github.com/<your-username>/f1-telemetry-dashboard.git
cd f1-telemetry-dashboard
```

### 2. Create and activate a virtual environment

```bash
python -m venv .venv

# macOS / Linux
source .venv/bin/activate

# Windows (PowerShell)
.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Run the dashboard

```bash
streamlit run app.py
```

The app will open at **http://localhost:8501**.

---

## 🚀 Quick Start

1. Open the app in your browser.
2. In the **sidebar**, choose a **Season**, **Circuit**, and **Session Type**.
3. Click **🔄 Load Session Data** — FastF1 fetches and caches the data automatically.
4. Select **Driver 1** and **Driver 2** from the dropdowns that appear.
5. Explore the four analysis tabs:
   - 📡 **Speed Trace** — overlaid speed / throttle / brake profiles
   - ⏱️ **Lap Pace** — violin distribution and lap-by-lap evolution
   - 🗺️ **Track Map** — circuit geometry with speed/gear colour coding
   - 📈 **Sector Analysis** — sector time comparison with delta table

> **Note:** The first load of a session may take 15–60 seconds depending on your connection. Subsequent loads are served from the local `.fastf1_cache/` directory and are near-instant.

---

## 🏗️ Architecture & Design Decisions

### Caching Strategy

Two layers of caching are used to maximise performance:

| Layer | Mechanism | Scope |
|---|---|---|
| **Disk cache** | `fastf1.Cache.enable_cache(".fastf1_cache")` | Persists raw API responses across app restarts |
| **Process cache** | `@st.cache_resource` on `load_session()` | Keeps parsed session objects in RAM for the app lifetime |
| **Per-call cache** | `@st.cache_data` with `ttl=3600` on helper functions | Caches derived DataFrames per unique input combination |

### Data Flow

```
User Interaction (app.py)
        │
        ▼
data_provider.load_session()          ← FastF1 API + disk cache
        │
        ├─► get_session_results()      → Driver list for selector
        ├─► get_driver_fastest_lap()   → Single lap for telemetry
        ├─► get_lap_telemetry()        → Speed / Throttle / Brake / XY
        └─► get_all_driver_laps()      → Pace distribution data
```

### Error Handling

- All data-fetching functions wrap FastF1 calls in `try/except` and return `None` on failure.
- The UI checks for `None` before rendering each visualisation and shows a contextual `st.warning()` instead of crashing.

---

## 🛠️ Tech Stack

| Library | Version | Purpose |
|---|---|---|
| [FastF1](https://docs.fastf1.dev) | ≥ 3.3 | F1 telemetry & timing data via Ergast + F1 live timing |
| [Streamlit](https://streamlit.io) | ≥ 1.35 | Web app framework |
| [Plotly](https://plotly.com/python/) | ≥ 5.22 | Interactive charts (speed trace, violin, track map) |
| [pandas](https://pandas.pydata.org) | ≥ 2.2 | DataFrame manipulation and time arithmetic |
| [NumPy](https://numpy.org) | ≥ 1.26 | Numerical operations |

---

## 📊 Visualisation Details

### Speed Trace (Tab 1)
Three-panel subplot: **Speed (km/h)** / **Throttle (%)** / **Brake** — all plotted against **Distance (m)** on the same x-axis. Speed is smoothed with a rolling-mean window to reduce sensor noise while preserving the shape of braking events.

### Lap Pace (Tab 2)
- **Violin + scatter** overlay: shows the statistical distribution of all clean laps, individual lap points, and the mean marker.
- **Line chart**: chronological pace evolution to spot tyre degradation, traffic, or safety-car periods.

### Track Map (Tab 3)
Scatter plot of `(X, Y)` telemetry coordinates, coloured by **Speed**, **Gear (nGear)**, or **Throttle** using the Plasma / Viridis colour scales. Axes are hidden and aspect ratio is locked so the circuit shape is preserved.

### Sector Analysis (Tab 4)
Grouped bar chart of S1/S2/S3 times in seconds, plus a pivot table showing per-sector deltas with conditional green/red colouring (negative = driver 1 faster, positive = driver 2 faster).

---

## 🔧 Configuration & Customisation

### Changing the cache directory

Edit the constant in `data_provider.py`:

```python
CACHE_DIR = Path(".fastf1_cache")   # Change to any writable path
```

### Adding more seasons or circuits

Extend the `YEARS` list and `CIRCUITS` dictionary in `data_provider.py`:

```python
YEARS = [2026, 2025, 2024, 2023, 2022, 2021, 2020]

CIRCUITS[2027] = ["Bahrain", "Saudi Arabia", ...]   # add future seasons here
```

### Changing the colour palette

Driver colours are set in `app.py`:

```python
DRIVER_COLORS = {driver1: "#e10600", driver2: "#00aaff"}
```

---

## 📝 Code Quality

- All public functions include **NumPy-style docstrings** (Parameters, Returns, Raises).
- Code is formatted to **PEP 8** standards (88-char line length, `black`-compatible).
- Type hints throughout for IDE support.
- Logging via Python's `logging` module instead of bare `print()` statements.

---

## 🚧 Known Limitations & Roadmap

| Item | Status |
|---|---|
| Pre-2020 data (limited FastF1 support) | ⚠️ Not included |
| Live timing (in-season real-time) | 🔜 Planned |
| Tyre strategy visualisation | 🔜 Planned |
| Export charts as PNG / PDF | 🔜 Planned |
| Multi-driver comparison (> 2) | 🔜 Planned |
| Docker deployment guide | 🔜 Planned |

---

## 🤝 Contributing

Pull requests are welcome! Please:

1. Fork the repo and create a feature branch: `git checkout -b feat/my-feature`
2. Write tests for any new `data_provider.py` functions.
3. Follow PEP 8 — run `black .` and `flake8 .` before committing.
4. Open a PR describing what you changed and why.

---

## ⚖️ License

This project is licensed under the **MIT License** — see [LICENSE](LICENSE) for details.

Formula 1 telemetry data is provided by [FastF1](https://docs.fastf1.dev) which sources it from the official F1 live timing stream. Data is © Formula One Management Ltd and used here for educational / non-commercial purposes only.

---

## 🙏 Acknowledgements

- [**FastF1**](https://github.com/theOehrly/Fast-F1) by Oehrly — the incredible library that makes F1 telemetry accessible.
- [**Ergast Developer API**](http://ergast.com/mrd/) — historical race data.
- The F1 data science community for inspiration.

---

*Made with ❤️ and too much Red Bull.*
