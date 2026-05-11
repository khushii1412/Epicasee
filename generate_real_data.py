"""
Generate standardized quarterly CSVs from real official annual data.

Sources:
  COVID-19  : covid19india.org crowd-sourced verified data (Jan 2020 – Oct 2021)
              https://data.covid19india.org/csv/latest/states.csv
  Dengue    : NCVBDC annual state-wise reports 2019-2023
              https://ncvbdc.mohfw.gov.in/
  Malaria   : NCVBDC annual state-wise reports 2019-2023
              https://ncvbdc.mohfw.gov.in/
              data.gov.in – Malaria Cases 2018-2021

Methodology: Annual totals are from published official sources.
Quarterly distribution uses documented Indian epidemic wave patterns:
  COVID   –  Wave-1 peak Q3/Q4 2020 · Wave-2 peak Q2 2021
  Dengue  –  Monsoon-driven peak Q3 (Jul-Sep) every year
  Malaria –  Transmission-season peak Q3 every year
"""

import os
import pandas as pd
import numpy as np

# ── Output directories ──────────────────────────────────────────────────
BASE_DIR    = os.path.dirname(__file__)
BACKEND_DIR = os.path.join(BASE_DIR, "backend", "data_processed")
ROOT_DIR    = os.path.join(BASE_DIR, "data_processed")


def write_csv(df, disease, dirs):
    for base in dirs:
        outdir = os.path.join(base, disease)
        os.makedirs(outdir, exist_ok=True)
        path = os.path.join(outdir, "standardized.csv")
        df.to_csv(path, index=False)
        print(f"  [SUCCESS] {path}  ({len(df)} rows)")


def quarterly_split(annual, dist):
    """Split annual total across 4 quarters using dist (4 fractions summing to 1)."""
    q = [round(annual * d) for d in dist]
    # Fix rounding so sum matches
    diff = annual - sum(q)
    q[0] += diff
    return q


def load_annual_data(filepath, case_col, death_col):
    """Load annual data from CSV and return as a dict of {State: ([cases], [deaths])}."""
    df = pd.read_csv(filepath)
    # Sort by State and Year to ensure chronological order in lists
    df = df.sort_values(["State/UT", "Year"])
    
    data_map = {}
    for state, group in df.groupby("State/UT"):
        cases = group[case_col].tolist()
        deaths = group[death_col].tolist()
        data_map[state] = (cases, deaths)
    return data_map


# ═══════════════════════════════════════════════════════════════════════
#  COVID-19  (covid19india.org – real verified data)
# ═══════════════════════════════════════════════════════════════════════
print("\n── COVID-19 ──")

# Source: covid19india.org states.csv
# Notes: Data covers Jan 30 2020 – Oct 31 2021
covid_csv = os.path.join(BASE_DIR, "data_raw/covid/source_notes/covid19india_statewise_annual_2020_2021.csv")
covid_annual = load_annual_data(covid_csv, "Confirmed_Cases", "Deaths")

# Quarterly fraction [Q1, Q2, Q3, Q4] per year
covid_qdist = {
    2020: [0.001, 0.093, 0.453, 0.453],  # Wave-1 peak Q3/Q4
    2021: [0.14,  0.55,  0.20,  0.11],   # Wave-2 peak Q2 (April-May)
}

covid_rows = []
for state, (cases_yrs, deaths_yrs) in covid_annual.items():
    for yi, year in enumerate([2020, 2021]):
        dist = covid_qdist[year]
        qcases  = quarterly_split(cases_yrs[yi],  dist)
        qdeaths = quarterly_split(deaths_yrs[yi], dist)
        months  = [1, 4, 7, 10]
        for qi in range(4):
            covid_rows.append({
                "state":      state,
                "district":   "",
                "time_index": f"{year}-{months[qi]:02d}-01",
                "cases":      qcases[qi],
                "deaths":     qdeaths[qi],
            })

covid_df = pd.DataFrame(covid_rows).sort_values(["state", "time_index"])
write_csv(covid_df, "covid", [BACKEND_DIR, ROOT_DIR])
print(f"  States: {covid_df['state'].nunique()}  |  Quarters: {len(covid_df) // covid_df['state'].nunique()}")


# ═══════════════════════════════════════════════════════════════════════
#  DENGUE  (NCVBDC annual state-wise reports — real data)
# ═══════════════════════════════════════════════════════════════════════
print("\n── Dengue ──")

# Source: NCVBDC dengue status reports 2019-2023
dengue_csv = os.path.join(BASE_DIR, "data_raw/dengue/source_notes/ncvbdc_dengue_statewise_annual_2019_2023.csv")
dengue_annual = load_annual_data(dengue_csv, "Total_Cases", "Deaths")

# Dengue seasonal split – strongly monsoon-driven (Q3 = Jul-Sep peak)
dengue_qdist = [0.08, 0.17, 0.52, 0.23]

dengue_rows = []
for state, (cases_yrs, deaths_yrs) in dengue_annual.items():
    for yi, year in enumerate([2019, 2020, 2021, 2022, 2023]):
        qcases  = quarterly_split(cases_yrs[yi],  dengue_qdist)
        qdeaths = quarterly_split(deaths_yrs[yi], dengue_qdist)
        months  = [1, 4, 7, 10]
        for qi in range(4):
            dengue_rows.append({
                "state":      state,
                "district":   "",
                "time_index": f"{year}-{months[qi]:02d}-01",
                "cases":      qcases[qi],
                "deaths":     qdeaths[qi],
            })

dengue_df = pd.DataFrame(dengue_rows).sort_values(["state", "time_index"])
write_csv(dengue_df, "dengue", [BACKEND_DIR, ROOT_DIR])
print(f"  States: {dengue_df['state'].nunique()}  |  Quarters per state: {len(dengue_df) // dengue_df['state'].nunique()}")


# ═══════════════════════════════════════════════════════════════════════
#  MALARIA  (NCVBDC / data.gov.in — real data)
# ═══════════════════════════════════════════════════════════════════════
print("\n── Malaria ──")

# Source: NCVBDC malaria annual reports + data.gov.in + PIB releases
malaria_csv = os.path.join(BASE_DIR, "data_raw/malaria/extracted/ncvbdc_malaria_statewise_annual_2019_2023.csv")
malaria_annual = load_annual_data(malaria_csv, "Total_Malaria_Cases", "Deaths")

# Malaria seasonal split – transmission season peaks Q3 (Jul-Sep)
malaria_qdist = [0.10, 0.20, 0.45, 0.25]

malaria_rows = []
for state, (cases_yrs, deaths_yrs) in malaria_annual.items():
    for yi, year in enumerate([2019, 2020, 2021, 2022, 2023]):
        qcases  = quarterly_split(cases_yrs[yi],  malaria_qdist)
        qdeaths = quarterly_split(deaths_yrs[yi], malaria_qdist)
        months  = [1, 4, 7, 10]
        for qi in range(4):
            malaria_rows.append({
                "state":      state,
                "district":   "",
                "time_index": f"{year}-{months[qi]:02d}-01",
                "cases":      qcases[qi],
                "deaths":     qdeaths[qi],
            })

malaria_df = pd.DataFrame(malaria_rows).sort_values(["state", "time_index"])
write_csv(malaria_df, "malaria", [BACKEND_DIR, ROOT_DIR])
print(f"  States: {malaria_df['state'].nunique()}  |  Quarters per state: {len(malaria_df) // malaria_df['state'].nunique()}")

print("\n[COMPLETE] All datasets written successfully.")
print("\nSource attribution:")
print("  COVID-19 : covid19india.org crowd-sourced verified data (Jan 2020–Oct 2021)")
print("             https://data.covid19india.org/csv/latest/states.csv")
print("  Dengue   : NCVBDC Annual Dengue Status Reports 2019-2023 (real data)")
print("             https://ncvbdc.mohfw.gov.in/")
print("  Malaria  : NCVBDC Annual Malaria Reports + data.gov.in 2019-2023 (real data)")
print("             https://ncvbdc.mohfw.gov.in/")
print("             https://data.gov.in/")
print("\nNote: All numbers loaded from official raw CSV files in data_raw/.")
print("Quarterly distribution derived from documented epidemic wave timelines.")
