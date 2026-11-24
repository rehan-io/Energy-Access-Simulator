from datetime import date
import re
import time

from fastapi.middleware.cors import CORSMiddleware
import threading
import uuid
from typing import Literal

from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field

from app.data.refresh_worldbank import refresh_worldbank_data
from app.data.dataset_loader import get_data_directory

from app.data.fetch_worldbank import (
    DEFAULT_INDICATORS,
    fetch_indicator,
    make_session,
)
from app.core.access_simulation import ACCESS_INDICATORS
from app.model.simulation_inputs import (
    run_country_access_simulation,
    run_country_coupled_simulation,
)

app = FastAPI(title="Energy Access Simulator API")

# Permit the local Vite frontend to communicate with FastAPI.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class WorldBankRequest(BaseModel):
    countries: list[str] = Field(min_length=1, max_length=10)
    start: int = Field(default=2000, ge=1960)
    end: int = Field(default_factory=lambda: date.today().year, ge=1960)
    indicators: list[str] = Field(
        default_factory=lambda: [
            "elec_access_total",
            "population",
            "gdp_per_capita_usd",
        ],
        min_length=1,
    )


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.post("/api/worldbank")
def get_worldbank_data(request: WorldBankRequest):
    countries = list(dict.fromkeys(
        country.strip().upper() for country in request.countries
    ))

    if request.start > request.end:
        raise HTTPException(
            status_code=422,
            detail="Start year must not exceed end year.",
        )

    if request.end > date.today().year:
        raise HTTPException(
            status_code=422,
            detail="End year cannot exceed the current year.",
        )

    if any(not re.fullmatch(r"[A-Z]{3}", c) for c in countries):
        raise HTTPException(
            status_code=422,
            detail="Use three-letter ISO country codes, e.g. IND or KEN.",
        )

    if len(request.indicators) > len(DEFAULT_INDICATORS):
        raise HTTPException(status_code=422, detail="Too many indicators.")

    indicators = list(dict.fromkeys(request.indicators))
    unknown = [
        name for name in indicators
        if name not in DEFAULT_INDICATORS
    ]

    if unknown:
        raise HTTPException(
            status_code=422,
            detail=f"Unknown indicators: {unknown}",
        )

    rows = []
    failures = []
    session = make_session()

    try:
        for name in indicators:
            code = DEFAULT_INDICATORS[name]

            try:
                records = fetch_indicator(
                    session,
                    countries,
                    code,
                    request.start,
                    request.end,
                )

                for record in records:
                    record["indicator"] = name

                rows.extend(records)

            except Exception as exc:
                failures.append({
                    "indicator": name,
                    "code": code,
                    "error": str(exc),
                })

            time.sleep(0.3)

    finally:
        session.close()

    if failures and not rows:
        raise HTTPException(
            status_code=502,
            detail={"message": "World Bank request failed", "failures": failures},
        )
    return {
        "countries": countries,
        "start": request.start,
        "end": request.end,
        "retrieved_on": date.today().isoformat(),
        "row_count": len(rows),
        "rows": rows,
        "failures": failures,
    }


AVAILABLE_COUNTRIES = [
    {"code": "IND", "name": "India"},
    {"code": "KEN", "name": "Kenya"},
    {"code": "RWA", "name": "Rwanda"},
    {"code": "NGA", "name": "Nigeria"},
    {"code": "SYR", "name": "SYria"},
]


def validate_country(country_code: str) -> str:
    country_code = country_code.strip().upper()

    supported = {country["code"] for country in AVAILABLE_COUNTRIES}

    if country_code not in supported:
        raise HTTPException(
            status_code=404,
            detail=f"Unsupported country: {country_code}",
        )

    return country_code

class DataRefreshRequest(BaseModel):
    countries: list[str] = Field(
        default_factory=lambda: ["IND", "KEN", "RWA", "NGA", "SYR"],
        min_length=1,
        max_length=5,
    )
    mode: Literal["incremental", "full"] = "incremental"
    start: int = Field(default=2000, ge=1960)
    end: int = Field(default_factory=lambda: date.today().year, ge=1960)
    overlapYears: int = Field(default=3, ge=0, le=10)


_refresh_lock = threading.Lock()

_refresh_state = {
    "job_id": None,
    "status": "idle",
    "countries": [],
    "mode": None,
    "started_at": None,
    "finished_at": None,
    "error": None,
}


def _run_data_refresh(
    countries: list[str],
    mode: str,
    start: int,
    end: int,
    overlap_years: int,
):
    with _refresh_lock:
        _refresh_state["status"] = "running"

    try:
        refresh_worldbank_data(
            countries=countries,
            start=start,
            end=end,
            active_dir=get_data_directory(),
            mode=mode,
            overlap_years=overlap_years,
        )

        with _refresh_lock:
            _refresh_state["status"] = "succeeded"

    except Exception as exc:
        with _refresh_lock:
            _refresh_state["status"] = "failed"
            _refresh_state["error"] = str(exc)

    finally:
        with _refresh_lock:
            _refresh_state["finished_at"] = time.time()


@app.post("/api/data/refresh", status_code=202)
def start_data_refresh(
    request: DataRefreshRequest,
    background_tasks: BackgroundTasks,
):
    countries = list(dict.fromkeys(
        validate_country(country) for country in request.countries
    ))

    if request.start > request.end:
        raise HTTPException(
            status_code=422,
            detail="Start year must not exceed end year.",
        )

    if request.end > date.today().year:
        raise HTTPException(
            status_code=422,
            detail="End year cannot exceed the current year.",
        )

    with _refresh_lock:
        if _refresh_state["status"] == "running":
            raise HTTPException(
                status_code=409,
                detail="A World Bank refresh is already running.",
            )

        job_id = str(uuid.uuid4())

        _refresh_state.update({
            "job_id": job_id,
            "status": "running",
            "countries": countries,
            "mode": request.mode,
            "started_at": time.time(),
            "finished_at": None,
            "error": None,
        })

    background_tasks.add_task(
        _run_data_refresh,
        countries,
        request.mode,
        request.start,
        request.end,
        request.overlapYears,
    )

    return {
        "job_id": job_id,
        "status": "running",
        "message": "World Bank data refresh started.",
    }


@app.get("/api/data/refresh/status")
def get_data_refresh_status():
    with _refresh_lock:
        return dict(_refresh_state)
@app.get("/api/countries")
def get_countries():
    """Return supported countries and their observed baseline access."""

    countries = []

    for country in AVAILABLE_COUNTRIES:
        code = country["code"]

        try:
            result = run_country_access_simulation(
                country_code=code,
                years=1,
            )

            baseline = next(
                row for row in result["history"]
                if row["year"] == result["baselineYear"]
                and row["kind"] == "historical"
            )

            countries.append({
                **country,
                "access": baseline["elec_access_total"],
                "cleanCookingAccess": baseline["clean_cooking_access"],
                "baselineYear": result["baselineYear"],
            })

        except (ValueError, FileNotFoundError) as exc:
            raise HTTPException(
                status_code=503,
                detail=f"Could not load baseline for {code}: {exc}",
            ) from exc

    return countries


class PolicyLevers(BaseModel):
    subsidy: float = Field(default=0.0, ge=0.0, le=100.0)
    carbon_tax: float = Field(default=0.0, ge=0.0, le=100.0)
    off_grid: float = Field(default=0.0, ge=0.0, le=100.0)
    grid_ext: float = Field(default=0.0, ge=0.0, le=100.0)
    recycle_tax_revenue: bool = Field(default=True)


class SimulationRequest(BaseModel):
    country: str = Field(default="IND", min_length=3, max_length=3)
    years: int = Field(default=25, ge=1, le=100)
    trendWindow: int = Field(default=10, ge=2, le=30)
    policyAdjustments: dict[str, float] = Field(default_factory=dict)
    policyLevers: PolicyLevers | None = None


@app.post("/api/simulate")
def simulate_endpoint(payload: SimulationRequest):
    """Run a country-specific access and five-tier energy-ladder simulation."""

    country_code = validate_country(payload.country)

    unknown_indicators = (
        set(payload.policyAdjustments) - set(ACCESS_INDICATORS)
    )

    if unknown_indicators:
        raise HTTPException(
            status_code=422,
            detail={
                "message": "Unknown policy adjustment indicators",
                "indicators": sorted(unknown_indicators),
                "allowed": list(ACCESS_INDICATORS),
            },
        )

    try:
        if payload.policyLevers is not None:
            return run_country_coupled_simulation(
                country_code=country_code,
                years=payload.years,
                trend_window=payload.trendWindow,
                policy_levers=payload.policyLevers.model_dump(),
            )

        return run_country_access_simulation(
            country_code=country_code,
            years=payload.years,
            trend_window=payload.trendWindow,
            policy_adjustments=payload.policyAdjustments,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc

    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=503,
            detail=f"Processed World Bank dataset unavailable: {exc}",
        ) from exc


@app.get("/api/baseline/{country_code}")
def get_country_baseline(country_code: str):
    """Return historical observations and estimated trends for a country."""

    country_code = validate_country(country_code)

    try:
        result = run_country_access_simulation(
            country_code=country_code,
            years=1,
        )

        historical = [
            row for row in result["history"]
            if row["kind"] == "historical"
        ]

        return {
            "countryCode": country_code,
            "baselineYear": result["baselineYear"],
            "trendWindow": result["trendWindow"],
            "trends": result["trends"],
            "historical": historical,
        }

    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc

    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=503,
            detail=f"Processed World Bank dataset unavailable: {exc}",
        ) from exc