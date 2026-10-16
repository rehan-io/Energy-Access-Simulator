
from datetime import date
import re
import time

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from app.data.fetch_worldbank import (
    DEFAULT_INDICATORS,
    fetch_indicator,
    make_session,
)

app = FastAPI(title="Energy Access Simulator API")

# Permit the local Vite frontend to communicate with FastAPI.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=False,
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
