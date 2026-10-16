"""
fetch_worldbank.py
------------------
Download World Bank indicators (electricity access, population, GDP, ...) for
one or more countries and save them as tidy CSV files.

No API key is needed. Docs: https://datahelpdesk.worldbank.org/knowledgebase/articles/889392

Examples
--------
    # Kenya + Rwanda, all default indicators, 2000-2024
    python fetch_worldbank.py --countries KEN RWA

    # Only two indicators, different years
    python fetch_worldbank.py --countries KEN --indicators EG.ELC.ACCS.ZS EG.ELC.ACCS.RU.ZS --start 1990 --end 2023

Outputs (in --outdir, default data/raw/worldbank)
-------
    worldbank_long.csv   one row per country-year-indicator (best for storing)
    worldbank_wide.csv   one row per country-year, one column per indicator (best for modelling)
"""

import argparse
import sys
import time
from datetime import date
from pathlib import Path

import pandas as pd
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

BASE_URL = "https://api.worldbank.org/v2"

# short name -> World Bank indicator code
# Find more codes at https://data.worldbank.org/indicator
DEFAULT_INDICATORS = {
    "elec_access_total": "EG.ELC.ACCS.ZS",      # Access to electricity (% of population)
    "elec_access_rural": "EG.ELC.ACCS.RU.ZS",   # ... rural
    "elec_access_urban": "EG.ELC.ACCS.UR.ZS",   # ... urban
    "clean_cooking_access": "EG.CFT.ACCS.ZS",   # Access to clean fuels for cooking (% pop)
    "elec_use_kwh_pc": "EG.USE.ELEC.KH.PC",     # Electric power consumption (kWh per capita)
    "population": "SP.POP.TOTL",                # Total population
    "rural_pop_share": "SP.RUR.TOTL.ZS",        # Rural population (% of total)
    "gdp_per_capita_usd": "NY.GDP.PCAP.CD",     # GDP per capita (current US$)
    # Income share held by each 20% group (sparse: only survey years). Useful for the "bottom 80%".
    "income_share_q1": "SI.DST.FRST.20",
    "income_share_q2": "SI.DST.02ND.20",
    "income_share_q3": "SI.DST.03RD.20",
    "income_share_q4": "SI.DST.04TH.20",
    "income_share_q5": "SI.DST.05TH.20",
}


def make_session() -> requests.Session:
    """A requests session that automatically retries on temporary errors."""
    session = requests.Session()
    retry = Retry(
        total=4,
        backoff_factor=1.5,                      # waits 1.5s, 3s, 6s, ...
        status_forcelist=[429, 500, 502, 503, 504],
    )
    session.mount("https://", HTTPAdapter(max_retries=retry))
    session.headers.update({"User-Agent": "energy-access-simulator-student-project"})
    return session


def fetch_indicator(session, countries, code, start, end):
    """Fetch one indicator for all given countries. Returns a list of row dicts."""
    url = f"{BASE_URL}/country/{';'.join(countries)}/indicator/{code}"
    params = {"format": "json", "per_page": 1000, "date": f"{start}:{end}", "page": 1}
    rows = []

    while True:
        resp = session.get(url, params=params, timeout=30)
        resp.raise_for_status()
        payload = resp.json()

        # The API returns [metadata, data]. On an error it returns just [{"message": ...}].
        if not isinstance(payload, list) or len(payload) < 2 or payload[1] is None:
            raise ValueError(f"API returned no data for {code}: {payload}")

        meta, data = payload
        for rec in data:
            rows.append(
                {
                    "country": rec["country"]["value"],
                    "iso3": rec["countryiso3code"],
                    "year": int(rec["date"]),
                    "indicator_code": rec["indicator"]["id"],
                    "value": rec["value"],          # None where the World Bank has no data
                }
            )

        if params["page"] >= int(meta["pages"]):
            break
        params["page"] += 1
        time.sleep(0.3)                              # be polite to the server

    return rows


def main():
    parser = argparse.ArgumentParser(description="Fetch World Bank indicators.")
    parser.add_argument("--countries", nargs="+", required=True,
                        help="ISO3 codes, e.g. KEN RWA IND")
    parser.add_argument("--indicators", nargs="+", default=None,
                        help="World Bank indicator codes (default: a curated list)")
    parser.add_argument("--start", type=int, default=2000)
    parser.add_argument("--end", type=int, default=date.today().year)
    parser.add_argument("--outdir", default="data/raw/worldbank")
    args = parser.parse_args()

    # Work out which indicators to fetch, keeping short names where we know them
    if args.indicators:
        code_to_name = {v: k for k, v in DEFAULT_INDICATORS.items()}
        indicators = {code_to_name.get(c, c): c for c in args.indicators}
    else:
        indicators = DEFAULT_INDICATORS

    session = make_session()
    all_rows, failed = [], []

    for name, code in indicators.items():
        try:
            rows = fetch_indicator(session, args.countries, code, args.start, args.end)
            n_valid = sum(r["value"] is not None for r in rows)
            print(f"  OK   {code:<20} {name:<22} {n_valid}/{len(rows)} non-empty values")
            all_rows.extend(rows)
        except Exception as exc:                     # keep going if one indicator fails
            print(f"  FAIL {code:<20} {name:<22} {exc}", file=sys.stderr)
            failed.append(code)
        time.sleep(0.3)

    if not all_rows:
        sys.exit("Nothing downloaded. Check your internet connection and country codes.")

    long_df = pd.DataFrame(all_rows)
    code_to_short = {v: k for k, v in indicators.items()}
    long_df["indicator"] = long_df["indicator_code"].map(code_to_short)
    long_df["retrieved_on"] = date.today().isoformat()
    long_df = long_df.sort_values(["iso3", "indicator", "year"]).reset_index(drop=True)

    wide_df = (
        long_df.pivot_table(index=["country", "iso3", "year"], columns="indicator",
                            values="value", aggfunc="first")
        .reset_index()
        .sort_values(["iso3", "year"])
    )

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    long_df.to_csv(outdir / "worldbank_long.csv", index=False)
    wide_df.to_csv(outdir / "worldbank_wide.csv", index=False)

    print(f"\nSaved to {outdir.resolve()}")
    if failed:
        print(f"Indicators that failed (retry later or check the code): {failed}")


if __name__ == "__main__":
    main()
