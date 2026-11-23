# Energy Access Dynamics Simulator

**Policy Planning for Universal Electrification**

---

## 📌 Project Status
> **🚀 Phase: Active Development (MVP Implemented)**  
> Core backend services (World Bank data pipeline, country calibration, coupled five-tier simulation engine, FastAPI endpoints, and test suite) and the interactive React dashboard are implemented and functional.

---

## 📖 Overview

**Energy Access Dynamics Simulator** is a data-driven policy sandbox designed to help researchers, policymakers, and NGOs navigate the complex transition from traditional fuels to modern electricity in developing regions. 

Nearly 1 billion people lack reliable electricity, and the poorest 80% of households are consistently the last to be reached. Governments face a critical dilemma: Should they extend the national grid, subsidize off-grid Solar Home Systems (SHS), or invest in community mini-grids? 

This project answers these "what-if" questions by combining **real-world public data**, **system dynamics modeling**, and an **interactive, beautiful geospatial dashboard** to simulate the long-term cascading effects of energy policies.

---

## 🎯 Motivation & Problem Statement

- **The Reality:** Rural households climb an "energy ladder"—starting with kerosene/diesel, moving to solar lanterns, then Solar Home Systems, then mini-grids, and finally the national grid. 
- **The Challenge:** Each step involves trade-offs between cost, reliability, and infrastructure availability. The poorest households are often left behind because grid extension is expensive and upfront costs for solar are too high.
- **The Gap:** There is a lack of open-source, transparent tools that allow stakeholders to simulate how subsidies, carbon taxes, and infrastructure speeds affect the bottom 80% over a 20–30 year horizon.
- **Our Solution:** A dynamic simulation engine paired with a modern, interactive dashboard that visualizes both temporal trends and spatial infrastructure layouts.

---

## 📊 Public Data Sources

The simulator automatically ingests and calibrates itself using:

- **World Bank / ESMAP** – Country-wise electrification rates and access indicators.
- **IEA Energy Access Database** – Historical energy transition trends and adoption curves.
- **OpenStreetMap (OSM)** – Existing grid lines, off-grid infrastructure, and mini-grid locations.
- **National Energy Ministry Portals** – Country-specific pricing, tariff structures, and subsidy data.

---

## ⚙️ Core System Dynamics (The Simulation Engine)

The mathematical heart of the project is a **Stock & Flow** model updated annually.

### 1. The "Stocks" (Household Categories)
- **Stock A:** Traditional Fuels (Kerosene, Diesel, Biomass)
- **Stock B:** Solar Lanterns (Basic lighting & phone charging)
- **Stock C:** Solar Home Systems (SHS – Panels + Battery for appliances)
- **Stock D:** Mini-Grids (Community-level local power networks)
- **Stock E:** National Grid (Full, unlimited utility-scale electricity)

### 2. The "Flows" (Adoption Rates)
Households move from lower stocks to higher stocks based on 4 key drivers:
- **Price** (Upfront & operational costs)
- **Subsidies** (Government financial support)
- **Reliability** (Uptime and maintenance)
- **Awareness** (Social diffusion & marketing)

### 3. The Feedback Loops
The simulation incorporates a positive feedback loop (learning curve):  
*More adoption → Increased manufacturing scale → Lower unit costs → Even faster adoption.*  
This ensures the model captures realistic market acceleration.

### 4. User Controls (The Policy Levers)
Users can adjust 4 primary dials via the dashboard:
- **Subsidy Percentage** – Reduces upfront capital costs.
- **Carbon Tax** – Raises the price of traditional fuels to incentivize switching.
- **Off-Grid Deployment Rate** – Speed at which solar companies reach rural areas.
- **Grid Extension Speed** – Annual rate at which the national power company builds new lines.

---

## ✨ Project USP (Unique Selling Points) - Baseline Features

### ✅ 1. Multi-Tier "Energy Ladder" Modeling
Instead of a binary "electrified/not electrified" flag, the model tracks the gradual, realistic transition across 5 distinct energy tiers alongside rural, urban, and clean cooking access.

### ✅ 2. Endogenous Feedback Loops
The simulation dynamically reduces off-grid technology costs based on cumulative adoption (Wright's Law), mimicking real-world manufacturing learning curves.

### ✅ 3. Real-Time Interactive Policy Levers
Users can move sliders for subsidies, carbon taxes, off-grid deployment, and grid extension speeds on the dashboard and instantly see the projected results update.

### ✅ 4. Automated Data Calibration
Python ingestion, cleaning, and validation scripts automatically pull World Bank data to calibrate the model's baseline to match a selected country's current reality.

### ✅ 5. Interactive Geospatial Map Visualization
Instead of just spreadsheets, the dashboard features an interactive Leaflet map visualizing country-level electrification and clean cooking access across supported regions.

### ✅ 6. Comparative Scenario Dashboard
Users can run multiple policy scenarios side-by-side (e.g., "High Subsidy" vs. "Fast Grid") and toggle between them to compare multi-decade access trajectories.

---

## 🧰 Tech Stack

| Layer | Technology |
| :--- | :--- |
| **Frontend (Dashboard)** | **React** (TypeScript) + **Vite** for fast builds; **Material-UI (MUI)** for responsive UI components; **Apache ECharts** for interactive charts; **Leaflet** (`react-leaflet`) for geospatial map rendering; **Zustand** & **Axios** for state management and API requests. |
| **Backend (API)** | **FastAPI** + **Uvicorn** (Python) to serve RESTful endpoints, handle simulation requests, and return JSON results with automatic Swagger documentation. |
| **Simulation Engine** | **Python 3.10+** with **Pandas** and standard-library **`math`** for coupled Bass-Logistic & five-tier stock-and-flow difference equations and OLS trend calibration. |
| **Data Pipeline** | **Python** CLI modules (`fetch_worldbank.py`, `clean_worldbank.py`, `validate_worldbank.py`, `refresh_worldbank.py`) using **Pandas** and **Requests** to ingest, validate, and refresh World Bank datasets. |
| **Testing & Linting** | **Git** for version control; **pytest** / `unittest` for backend test suites; **Oxlint** for React/TypeScript linting. |

---

## 📁 Repository Structure
```text
energy-access-simulator/
├── backend/
│   ├── app/
│   │   ├── core/                # Simulation engines (access_simulation.py, simulation.py)
│   │   ├── data/                # World Bank ingestion, cleaning, validation & loaders
│   │   ├── model/               # Country calibration, schemas & simulation input builders
│   │   └── main.py              # FastAPI endpoints (/api/health, /api/countries, /api/simulate, etc.)
│   ├── data/
│   │   └── processed/worldbank/ # Cleaned World Bank CSVs & data quality report
│   ├── tests/                   # Unit & API test suites (pytest / unittest)
│   └── requirements.txt
├── frontend/
│   ├── public/                  # Static assets (favicon.svg)
│   ├── src/                     # React + TypeScript dashboard source
│   ├── index.html
│   ├── package.json
│   └── package-lock.json
├── .gitignore
└── README.md                    # You are here!
```


## 🔄 How It Works (User Journey)

1. **Ingest:** The system runs `fetch_energy_data.sh` to pull the latest World Bank, IEA, and OSM data.
2. **Calibrate:** `calibrate_model.sh` uses a Python script to fit the initial stocks to the real-world baseline of the selected country.
3. **Configure:** The user opens the React dashboard and adjusts the 4 policy levers using intuitive sliders.
4. **Simulate:** The frontend sends a POST request to the FastAPI backend. The backend runs the system dynamics difference equations for the next 25 years.
5. **Visualize:** The backend returns time-series data and GeoJSON map layers. The frontend:
   - Animates the stacked area charts to show households moving up the ladder.
   - Updates the Mapbox heatmaps to show geographical electrification spread.
6. **Compare:** The user can create a new Git branch to save this scenario and run an alternative policy, comparing both side-by-side on the dashboard.

---

## 🚀 Future Scope & Stretch Goals

- **Agent-Based Modeling (ABM):** Introduce heterogeneous household characteristics (wealth, location, family size) to refine adoption predictions.
- **Real-time Weather Integration:** Hook in solar irradiance data to model the reliability of Solar Home Systems under different climate conditions.
- **Cost-Benefit Analysis Module:** Automatically compute the Net Present Value (NPV) and Internal Rate of Return (IRR) for each policy mix.
- **Mobile Responsiveness:** Optimize the dashboard for tablet usage during field surveys.

---

<!-- ## 🤝 Contributing

*Currently, this project is in the planning phase. Contribution guidelines will be published once the initial codebase is scaffolded. Please check back later for development milestones.*

--- -->

## 📄 License

[MIT](https://choosealicense.com/licenses/mit/)

---

## 📧 Contact

For inquiries regarding this project blueprint, please reach out to the project maintainers.

---
`````[cite: 1]