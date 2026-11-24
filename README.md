# Energy Access Dynamics Simulator

**CS699 Project | Policy exploration for electricity access and clean cooking**

The Energy Access Dynamics Simulator is an interactive dashboard and Python simulation backend for exploring how policy settings may affect electricity access, clean cooking access, and the distribution of households across a five-tier energy ladder.

This README describes the functionality currently present in the repository. It does not describe planned integrations or features that are not implemented.

## Current implementation

- Interactive React dashboard with country selection, projection horizon, historical trend window, policy controls, KPI summaries, and time-series visualizations.
- Country-level historical data and model inputs loaded from processed World Bank datasets bundled in the repository.
- Two simulation paths exposed by the API:
  - Historical access trend estimation using recent valid observations and least-squares linear trends.
  - A coupled Bass-Logistic and five-tier stock-and-flow model, driven by country baseline data, macroeconomic context, and policy levers.
- Four supported countries: India (IND), Kenya (KEN), Rwanda (RWA), and Nigeria (NGA).
- Manual World Bank dataset refresh from the dashboard, with background execution and status reporting.
- Command-line full and incremental World Bank refresh workflows, including cleaning, validation, staged output, and promotion of validated datasets.
- Backend unit/API tests for the data pipeline and coupled simulation.

## What the model currently represents

The coupled simulation tracks five household energy tiers:

1. Traditional fuels
2. Solar lanterns
3. Solar home systems (SHS)
4. Mini-grids
5. National grid

It also models national, rural, and urban electricity access, plus clean cooking access.

The dashboard exposes these policy controls:

- **Subsidy percentage**
- **Carbon tax**
- **Off-grid deployment rate**
- **Grid extension speed**
- **Recycle carbon-tax revenue** (on/off)

The API accepts a projection horizon of 1–100 years and a historical trend window of 2–30 years.

### Important interpretation notes

- Electricity access and clean cooking access are separate indicators.
- The five-tier model uses country-specific **illustrative initial tier splits**. These are model assumptions, not a directly observed breakdown of household connections by technology.
- Historical observations and model projections are distinguished in the returned simulation history and in the dashboard charts.
- Missing source observations are not automatically interpreted as zero.
- The map currently renders an Esri basemap centred on India. It is geographic context only; it is not a choropleth or a map of simulated infrastructure deployment.
- Saved scenarios are held in the running frontend application's Zustand state. They are not persisted to a database or browser storage, so they are lost when the application state is reset or the page is reloaded.
- The dashboard's refresh action updates the shared processed dataset files used by the backend. It is a manual action, not an automatic refresh on every dashboard load.

## Data

The repository includes processed World Bank data for the supported countries under:

```text
backend/data/processed/worldbank/
├── worldbank_long.csv
├── worldbank_wide.csv
├── worldbank_latest.csv
└── worldbank_quality_report.txt
```

The loader uses this directory by default. It can be overridden with the `WORLD_BANK_DATA_DIR` environment variable.

The long dataset stores country-year-indicator observations. The wide dataset pivots indicators into columns for model input and calibration. The latest dataset stores the latest available observation independently for each country and indicator.

The refresh pipeline retrieves data from the World Bank API. It does not currently ingest IEA, OpenStreetMap, or national ministry datasets.

## Architecture

### Frontend

- React 19
- TypeScript
- Vite
- Material UI (MUI)
- Apache ECharts via `echarts-for-react`
- Leaflet via `react-leaflet`
- Zustand for in-memory application state
- Browser Fetch API for backend requests

### Backend

- Python
- FastAPI and Uvicorn
- Pydantic request/response models
- Pandas for dataset processing
- Requests and urllib3 for World Bank API access

The Vite development server proxies `/api` requests to the local FastAPI server at `http://127.0.0.1:8000`.

## Repository layout

```text
Energy-Access-Simulator/
├── backend/
│   ├── app/
│   │   ├── core/
│   │   │   ├── access_simulation.py
│   │   │   └── simulation.py
│   │   ├── data/
│   │   │   ├── fetch_worldbank.py
│   │   │   ├── clean_worldbank.py
│   │   │   ├── validate_worldbank.py
│   │   │   ├── refresh_worldbank.py
│   │   │   ├── dataset_loader.py
│   │   │   └── schemas.py
│   │   ├── model/
│   │   │   ├── simulation_inputs.py
│   │   │   ├── calibration.py
│   │   │   └── calibration_schema.py
│   │   └── main.py
│   ├── data/
│   │   └── processed/worldbank/
│   ├── tests/
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── services/
│   │   ├── store/
│   │   └── types/
│   ├── package.json
│   └── vite.config.ts
└── README.md
```

## Requirements

Install the following before running the application:

- Python 3.10 or newer
- Node.js and npm (use a Node.js version compatible with the Vite version in `frontend/package.json`)
- Git

The frontend and backend run as separate development processes.

## Run locally

The commands below are written for **Windows PowerShell**. Run the backend and frontend in two separate terminals.

### 1. Clone the repository

```powershell
git clone https://github.com/rehan-io/Energy-Access-Simulator.git
cd Energy-Access-Simulator
```

If you are working from an existing clone, first switch to the branch containing the implementation you want to run.

### 2. Set up and start the backend

```powershell
cd backend

py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1

python -m pip install --upgrade pip
pip install -r requirements.txt

python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

If PowerShell blocks virtual-environment activation, allow it for the current terminal session and activate again:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

The API is available at:

- Health check: `http://127.0.0.1:8000/api/health`
- Interactive API documentation: `http://127.0.0.1:8000/docs`

Keep this terminal running.

### 3. Set up and start the frontend

Open a **second PowerShell terminal** at the repository root:

```powershell
cd frontend
npm ci
npm run dev
```

Open the local URL printed by Vite (normally `http://localhost:5173`).

The frontend's Vite configuration proxies API requests to the backend on port 8000. Start the backend before using the dashboard.

### macOS / Linux equivalents

From the repository root, the backend setup is:

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

In a second terminal:

```bash
cd frontend
npm ci
npm run dev
```

## Refresh World Bank data

The processed datasets are already included in the repository, so a first run does not require a data refresh.

### From the dashboard

Use **Refresh Data** in the dashboard header. The frontend starts a background refresh for IND, KEN, RWA, and NGA in incremental mode, polls the refresh status endpoint, and reloads the country data and simulation after a successful refresh.

### From the command line

Run these commands from the `backend` directory with the backend virtual environment activated.

Full refresh (fetches the requested year range):

```powershell
python -m app.data.refresh_worldbank --countries IND KEN RWA NGA --mode full --start 2000 --end 2026
```

Incremental refresh (uses a three-year overlap by default):

```powershell
python -m app.data.refresh_worldbank --countries IND KEN RWA NGA --mode incremental --overlap-years 3
```

Replace `2026` with the current year when running the full-refresh command in a later year. The API and CLI validate that the end year is not in the future.

The refresh process fetches the source data, merges it with the existing long dataset, regenerates the long/wide/latest outputs, validates the merged data, writes a quality report, and promotes the staged files only after validation succeeds. If promotion fails, the previous files are restored.

## API endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/api/health` | Backend health check |
| GET | `/api/countries` | Supported countries and latest baseline access values |
| GET | `/api/baseline/{country_code}` | Historical observations and estimated trends |
| POST | `/api/simulate` | Run an access-trend or coupled policy simulation |
| POST | `/api/worldbank` | Fetch selected World Bank indicators for a request |
| POST | `/api/data/refresh` | Start a background processed-data refresh |
| GET | `/api/data/refresh/status` | Read the current refresh job status |

The coupled simulation request supplies `policyLevers`. If `policyLevers` is omitted, the API uses the access-trend simulation path and accepts `policyAdjustments` for the supported access indicators. See `backend/app/main.py` and the interactive API documentation at `/docs` for request schemas.

## Run tests

Run backend tests from the `backend` directory with the backend virtual environment activated:

```powershell
python -m unittest discover -s tests -v
```

The tests cover World Bank data normalization, duplicate handling, wide/latest dataset generation, validation, coupled simulation behavior, bounds and tier conservation, and API behavior.

Check the frontend TypeScript build from the `frontend` directory:

```powershell
npm run build
```

Run the configured frontend linter with:

```powershell
npm run lint
```

## Current limitations

- The application is a local development setup; production hosting and deployment configuration are not documented or configured here.
- There is no database-backed scenario persistence or cross-user scenario sharing.
- The map is a basemap only and is not connected to the model's outputs.
- The five-tier initial splits are illustrative assumptions; the model should not be interpreted as having observed technology-level household connection data for each country.
- The model is a policy exploration tool. Its projections depend on model structure, calibration inputs, and assumptions; they should not be treated as official forecasts.

## License

The repository currently identifies the project license as MIT. See the repository's license file for the applicable terms.
