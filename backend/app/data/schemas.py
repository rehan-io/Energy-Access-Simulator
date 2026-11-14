
"""Shared schema and validation metadata for World Bank indicator data."""

# Short name -> World Bank indicator code.

INDICATOR_CODES = {
    "elec_access_total": "EG.ELC.ACCS.ZS",
    "elec_access_rural": "EG.ELC.ACCS.RU.ZS",
    "elec_access_urban": "EG.ELC.ACCS.UR.ZS",
    "clean_cooking_access": "EG.CFT.ACCS.ZS",
    "elec_use_kwh_pc": "EG.USE.ELEC.KH.PC",
    "population": "SP.POP.TOTL",
    "rural_pop_share": "SP.RUR.TOTL.ZS",
    "gdp_per_capita_usd": "NY.GDP.PCAP.CD",
    "income_share_q1": "SI.DST.FRST.20",
    "income_share_q2": "SI.DST.02ND.20",
    "income_share_q3": "SI.DST.03RD.20",
    "income_share_q4": "SI.DST.04TH.20",
    "income_share_q5": "SI.DST.05TH.20",
}

# Required columns in the long-format World Bank dataset.
LONG_COLUMNS = (
    "country",
    "iso3",
    "year",
    "indicator_code",
    "indicator",
    "value",
    "retrieved_on",
)

# Unique identifier for an observation.
# A country can have only one value for a given indicator in a given year
# after duplicate resolution.
KEY_COLUMNS = ("iso3", "year", "indicator")

# Indicators whose values represent percentages.
# Valid range: 0 to 100.
PERCENTAGE_INDICATORS = {
    "elec_access_total",
    "elec_access_rural",
    "elec_access_urban",
    "clean_cooking_access",
    "rural_pop_share",
    "income_share_q1",
    "income_share_q2",
    "income_share_q3",
    "income_share_q4",
    "income_share_q5",
}

# All indicators in our curated dataset should be non-negative.
NON_NEGATIVE_INDICATORS = set(INDICATOR_CODES)
