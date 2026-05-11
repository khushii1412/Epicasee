# Raw Data Sources

This folder contains raw annual state-wise data from **official Indian government publications** and **verified crowd-sourced data**.

All data in this project is real and sourced from publicly available datasets.

---

## COVID-19 — `covid/`

### `covid/extracted/` — Original daily timeseries (real data)

| File | Rows | Source | Direct Download Link |
|------|------|--------|---------------------|
| `states.csv` | 21,676 | covid19india.org | [states.csv](https://data.covid19india.org/csv/latest/states.csv) |
| `case_time_series.csv` | 641 | covid19india.org | [case_time_series.csv](https://data.covid19india.org/csv/latest/case_time_series.csv) |

### `covid/source_notes/` — Aggregated annual summary

| File | Source |
|------|--------|
| `covid19india_statewise_annual_2020_2021.csv` | Aggregated from `states.csv` above |

**Format:** Daily cumulative Confirmed, Recovered, Deceased, Tested per state  
**Period:** Jan 30, 2020 – Oct 31, 2021  
**States:** Maharashtra, Kerala, Karnataka, Tamil Nadu, Delhi, West Bengal, Uttar Pradesh, Andhra Pradesh, Gujarat, Rajasthan

**About the source:**  
[covid19india.org](https://www.covid19india.org/) was a volunteer-driven open-source project that tracked COVID-19 data in India by verifying numbers against official state health bulletins. The project stopped tracking on Oct 31, 2021. All data is archived at [data.covid19india.org](https://data.covid19india.org/).

**All available CSV endpoints:**
- States timeseries: https://data.covid19india.org/csv/latest/states.csv
- India timeseries: https://data.covid19india.org/csv/latest/case_time_series.csv
- Districts timeseries: https://data.covid19india.org/csv/latest/districts.csv
- State-wise daily: https://data.covid19india.org/csv/latest/state_wise_daily.csv
- Vaccine data: https://data.covid19india.org/csv/latest/vaccine_doses_statewise_v2.csv
- Full API docs: https://data.covid19india.org/

---

## Dengue — `dengue/source_notes/`

| File | Source | Links |
|------|--------|-------|
| `ncvbdc_dengue_statewise_annual_2019_2023.csv` | NCVBDC Annual Dengue Status Reports | See below |

**Format:** Annual cases and deaths per state  
**Period:** 2019–2023  
**States:** Kerala, Karnataka, Tamil Nadu, Maharashtra, Rajasthan, West Bengal, Uttar Pradesh, Delhi, Gujarat, Punjab

**Data sourced from:**
1. **NCVBDC Dengue Dashboard:** https://ncvbdc.mohfw.gov.in/index4.php?lang=1&level=0&linkid=431&lid=3715
2. **NCVBDC Home (annual reports & fact sheets):** https://ncvbdc.mohfw.gov.in/
3. **data.gov.in — Dengue Deaths 2021:** https://data.gov.in/resource/stateut-wise-number-dengue-deaths-country-during-2021
4. **data.gov.in — Dengue Cases 2019-2021:** https://data.gov.in/resource/year-wise-dengue-cases-reported-country-2019-2021
5. **PIB Press Release (2023 data):** https://pib.gov.in/

**Cross-verification:**
- National totals verified against WHO India dengue epidemiological reports
- 2021-2023 state-wise numbers from published peer-reviewed research citing NCVBDC (NCBI/PubMed)

---

## Malaria — `malaria/extracted/`

| File | Source | Links |
|------|--------|-------|
| `ncvbdc_malaria_statewise_annual_2019_2023.csv` | NCVBDC Malaria Reports + data.gov.in | See below |

**Format:** Annual total malaria cases and deaths per state  
**Period:** 2019–2023  
**States:** Odisha, Jharkhand, Chhattisgarh, Madhya Pradesh, West Bengal, Assam, Maharashtra, Meghalaya, Gujarat, Karnataka

**Data sourced from:**
1. **NCVBDC Malaria Dashboard:** https://ncvbdc.mohfw.gov.in/index1.php?lang=1&level=1&sublinkid=5784&lid=3689
2. **NCVBDC Home (annual malaria reports):** https://ncvbdc.mohfw.gov.in/
3. **data.gov.in — State/UT-wise Malaria Cases & Deaths 2018-2021:** https://data.gov.in/resource/stateut-wise-malaria-cases-and-deaths-country-2018-2021
4. **PIB Press Release (national totals, 2019):** https://pib.gov.in/PressReleaseIframePage.aspx?PRID=1650888
5. **WHO World Malaria Report 2024 — India profile:** https://www.who.int/teams/global-malaria-programme/reports/world-malaria-report-2024

**Cross-verification:**
- National totals verified: 2019 = 338,494 cases (77 deaths), 2020 = 186,532 (98), 2021 = 161,752 (90), 2022 = 176,522 (83), 2023 = 227,564 (83) — source: NCVBDC via PIB
- State-wise breakdowns from published research citing NCVBDC and data.gov.in datasets

---

## Processing Pipeline

```
data_raw/ (annual/daily, official format)
    ↓  generate_real_data.py
backend/data_processed/ (quarterly, standardized schema)
    ↓  Flask API (backend/app.py)
frontend/ (ML forecasting dashboard)
```

The script `generate_real_data.py` (project root) converts annual totals → quarterly data using documented Indian epidemic wave patterns (COVID) and monsoon-season transmission patterns (Dengue, Malaria).

---

## Data Provenance Summary

| Disease | Primary Source | Data Type | Verification |
|---------|---------------|-----------|-------------|
| **COVID-19** | covid19india.org | Real CSV download | Verified against state bulletins |
| **Dengue** | NCVBDC (MoHFW) | Official annual reports | Cross-checked with PIB, WHO, PubMed |
| **Malaria** | NCVBDC + data.gov.in | Official annual reports | Cross-checked with PIB, WHO WMR 2024 |

> **Note:** COVID-19 data covers 2020-2021 only (covid19india.org stopped Oct 2021). Dengue and Malaria cover 2019-2023 from NCVBDC annual reports.
