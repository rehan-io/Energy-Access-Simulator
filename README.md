# Electrification & Energy Access Policy Simulator

An interactive policy modeling and simulation platform for projecting national, rural, and urban electrification trajectories across a five-tier energy access framework (2026–2050). Built on calibrated empirical data from the World Bank, the simulator enables policymakers and analysts to test grid expansion, off-grid adoption, and reliability interventions in real time.

---

## Project Status

**Phase: Active Development — Core Backend, Data Pipeline & Test Suite Implemented**

* **Data Pipeline (`backend/app/data/`):** Automated World Bank API ingestion, cleaning, schema/range validation, and data refresh workflows are complete.
* **Simulation Engine (`backend/app/core/simulation.py`):** Calibrated five-tier coupled stock simulation model is implemented and verified.
* **Backend API (`backend/app/main.py`):** FastAPI REST endpoints (including `POST /api/simulate`) are operational.
* **Automated Testing (`backend/tests/`):** 63 backend unit and integration tests passing.
* **Frontend (`frontend/`):** React 19 application scaffolded with Material-UI, Apache ECharts, Zustand, Axios, and Leaflet.

---

## Key Features & Project USPs

1. **Five-Tier Coupled Electrification Model:** Models household transitions across five distinct energy access tiers (from basic solar lighting/SHS to reliable high-capacity grid connections) rather than relying on binary electrified/unelectrified metrics.
2. **Rural–Urban & Equity Disaggregation:** Tracks national, rural, and urban electrification rates independently alongside bottom-80% equity dynamics, accounting for differential grid reliability and tier splits.
3. **Automated World Bank Data Pipeline:** End-to-end ETL workflow (`fetch`, `clean`, `validate`, `refresh`) that pulls historical country-level electrification indicators directly from the World Bank API with built-in data integrity checks.
4. **Real-Time Policy Parameter Simulation:** FastAPI simulation endpoint (`POST /api/simulate`) computes multi-decade projections (2026–2050) on the fly in response to adjustments in grid expansion rates, off-grid adoption, and reliability parameters.
5. **Interactive Data Visualization & Mapping:** Combines Apache ECharts for multi-tier trajectory charts and scenario comparisons with Leaflet for spatial visualization.

---

## Tech Stack

### Backend
* **Language:** Python 3.10+
* **Web Framework & Server:** FastAPI, Uvicorn
* **Data Processing & HTTP:** Pandas, Requests, urllib3
* **Testing:** Pytest

### Frontend
* **Framework:** React 19
* **UI Component Library:** Material-UI (`@mui/material`)
* **Data Visualization:** Apache ECharts (`echarts`, `echarts-for-react`)
* **Mapping:** Leaflet (`leaflet`, `react-leaflet`)
* **State Management & Networking:** Zustand, Axios

### Data Sources
* **World Bank Open Data API:** Historical national, rural, and urban electricity access indicators.

---

## Repository Structure

```text
.
├── backend/
│   ├── app/
│   │   ├── core/
│   │   │   └── simulation.py        # Calibrated 5-tier coupled simulation engine
│   │   ├── data/
│   │   │   ├── fetch_worldbank.py   # World Bank API ingestion, cleaning, validation & refresh
│   │   │   └── ...
│   │   └── main.py                  # FastAPI application and REST API endpoints
│   ├── tests/                       # 63 unit & integration tests (pipeline, simulation, API)
│   └── requirements.txt             # Python runtime dependencies
├── frontend/
│   ├── src/
│   │   ├── components/              # Reusable UI, chart, and map components
│   │   ├── pages/                   # Dashboard and scenario views
│   │   ├── hooks/                   # Custom React hooks
│   │   └── styles/                  # Application styling and theme configuration
│   ├── package.json                 # Node dependencies and scripts
│   └── package-lock.json
└── README.md
```

---

## Getting Started

### Prerequisites
* Python 3.10+
* Node.js 18+ and npm

### 1. Backend Setup & Execution

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
pip install pytest

# Run the FastAPI server
uvicorn app.main:app --reload --port 8000
```

Interactive API documentation is available at `http://localhost:8000/docs`.

### 2. Run Backend Tests

```bash
cd backend
pytest
```

### 3. Frontend Setup & Execution

```bash
cd frontend
npm install
npm start
```

---

## Core API Endpoints

* **`POST /api/simulate`**: Runs the five-tier coupled electrification simulation for a target country and policy parameter configuration, returning projected national, rural, and urban electrification percentages along with five-tier stock shares over the 2026–2050 horizon.
* **Data & Health Endpoints (`backend/app/main.py`)**: Serves available country baselines, historical World Bank indicator series, and API health status.