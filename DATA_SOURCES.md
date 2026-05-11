## Data Sources Overview

This project relies exclusively on publicly available epidemiological datasets relevant to infectious diseases in India. All data used is **real** and sourced from official government publications, verified crowd-sourced platforms, and open data portals.

---

## COVID-19 Data Source

COVID-19 epidemiological data is used as a primary high-resolution dataset in this project due to its availability across multiple spatial and temporal scales in India.

**Source:**  
[covid19india.org](https://www.covid19india.org/) — A volunteer-driven open-source project that tracked COVID-19 data in India by verifying numbers against official state health bulletins. Archived at [data.covid19india.org](https://data.covid19india.org/).

**Direct Download Links:**
- State-wise daily timeseries: https://data.covid19india.org/csv/latest/states.csv
- India-level daily timeseries: https://data.covid19india.org/csv/latest/case_time_series.csv
- District-wise timeseries: https://data.covid19india.org/csv/latest/districts.csv
- State-wise daily deltas: https://data.covid19india.org/csv/latest/state_wise_daily.csv
- Vaccine doses statewise: https://data.covid19india.org/csv/latest/vaccine_doses_statewise_v2.csv
- Full API documentation: https://data.covid19india.org/

**Geographical Coverage:**
- State-level data for all states and union territories in India
- District-level data for selected states where reliable reporting is available

**Temporal Resolution:**
- Daily case counts (Jan 30, 2020 – Oct 31, 2021)
- Data archived after Oct 31, 2021 (project stopped tracking)

**Data Fields Utilized:**
- Confirmed cases (cumulative)
- Recovered (cumulative)
- Deceased (cumulative)
- Tested (where available)

**Role in the Framework:**
COVID-19 data is used to:
- Validate the forecasting and early warning pipeline at both state and district levels
- Support short-term forecasting and outbreak risk assessment
- Enable comparative modeling across different computational approaches

**Limitations:**
- Data covers only up to October 2021 (project discontinued)
- Incomplete or inconsistent district-level reporting in some regions
- Variability in testing and reporting practices across time and states

---

## Dengue Data Source

Dengue epidemiological data is included to represent vector-borne infectious diseases with strong seasonal and environmental dependence in India.

**Source:**  
National Centre for Vector Borne Disease Control (NCVBDC), Ministry of Health and Family Welfare, Government of India.

**Direct Links:**
- NCVBDC Dengue Dashboard: https://ncvbdc.mohfw.gov.in/index4.php?lang=1&level=0&linkid=431&lid=3715
- NCVBDC Home (annual reports): https://ncvbdc.mohfw.gov.in/
- data.gov.in — Dengue Deaths 2021: https://data.gov.in/resource/stateut-wise-number-dengue-deaths-country-during-2021
- data.gov.in — Dengue Cases 2019-2021: https://data.gov.in/resource/year-wise-dengue-cases-reported-country-2019-2021

**Geographical Coverage:**
- State-level dengue case counts across India
- 10 states used in this project: Kerala, Karnataka, Tamil Nadu, Maharashtra, Rajasthan, West Bengal, Uttar Pradesh, Delhi, Gujarat, Punjab

**Temporal Resolution:**
- Annual data (2019–2023)
- National totals: 2019 ~157K cases, 2020 ~80K (COVID impact), 2021 ~193K, 2022 ~233K, 2023 ~289K cases

**Data Fields Utilized:**
- Reported dengue cases (annual, state-wise)
- Dengue-related deaths (annual, state-wise)

**Role in the Framework:**
Dengue data is used to:
- Analyze long-term and seasonal disease trends
- Identify high-risk states and regions
- Demonstrate the framework's ability to handle diseases with lower temporal resolution
- Compare disease behavior across different infectious disease categories

**Limitations:**
- Limited availability of high-frequency (weekly or daily) district-level data
- Potential under-reporting due to asymptomatic or unreported cases
- State-wise data extracted from NCVBDC annual reports (HTML tables, not direct CSV)

---

## Malaria Data Source

Malaria epidemiological data is included to represent endemic infectious diseases with persistent regional burden and long-term public health relevance in India.

**Source:**  
National Centre for Vector Borne Disease Control (NCVBDC) + Open Government Data Platform India (data.gov.in).

**Direct Links:**
- NCVBDC Malaria Dashboard: https://ncvbdc.mohfw.gov.in/index1.php?lang=1&level=1&sublinkid=5784&lid=3689
- NCVBDC Home (annual malaria reports): https://ncvbdc.mohfw.gov.in/
- data.gov.in — State/UT-wise Malaria Cases & Deaths 2018-2021: https://data.gov.in/resource/stateut-wise-malaria-cases-and-deaths-country-2018-2021
- PIB Press Release — India malaria data: https://pib.gov.in/PressReleaseIframePage.aspx?PRID=1650888
- WHO World Malaria Report 2024: https://www.who.int/teams/global-malaria-programme/reports/world-malaria-report-2024

**Geographical Coverage:**
- State-level malaria case counts across India
- 10 high-burden states used in this project: Odisha, Jharkhand, Chhattisgarh, Madhya Pradesh, West Bengal, Assam, Maharashtra, Meghalaya, Gujarat, Karnataka

**Temporal Resolution:**
- Annual reporting (2019–2023)
- National totals: 2019 = 338,494 (77 deaths), 2020 = 186,532 (98), 2021 = 161,752 (90), 2022 = 176,522 (83), 2023 = 227,564 (83)

**Data Fields Utilized:**
- Reported malaria cases (annual, state-wise)
- Malaria-related deaths (annual, state-wise)

**Role in the Framework:**
Malaria data is used to:
- Analyze long-term disease burden and persistence across states
- Identify high-risk regions and endemic zones
- Demonstrate the framework's ability to integrate low-frequency but high-coverage epidemiological datasets
- Support comparative understanding across infectious diseases with different transmission dynamics

**Limitations:**
- Lack of high-frequency (weekly or daily) time-series data
- Reporting delays and potential under-reporting in certain regions
- State-wise data for 2019-2020 from NCVBDC annual reports; 2021-2023 cross-verified with published research

---

## IDSP Outbreak Surveillance Data

Integrated Disease Surveillance Programme (IDSP) data is included to support multi-disease outbreak monitoring and early warning analysis across India.

**Source:**  
Weekly outbreak surveillance reports published under the Integrated Disease Surveillance Programme (IDSP), Ministry of Health and Family Welfare, Government of India.

**Direct Links:**
- IDSP Portal: https://idsp.mohfw.gov.in/
- Weekly outbreak reports: https://idsp.mohfw.gov.in/index4.php?lang=1&level=0&linkid=406&lid=3689

**Geographical Coverage:**
- State-level and district-level outbreak reporting across India
- Coverage varies by reporting week and disease category

**Temporal Resolution:**
- Weekly reporting
- Data is directly suitable for short-term outbreak detection and early warning analysis
- Forecasting is limited to short-horizon trend estimation rather than continuous case prediction

**Data Fields Utilized:**
- Disease category
- Number of reported cases
- Number of deaths (where available)
- Location (state and district)
- Reporting week

**Role in the Framework:**
IDSP data is used to:
- Enable early warning detection of infectious disease outbreaks
- Support multi-disease surveillance using a single reporting system
- Complement disease-specific datasets such as COVID-19, dengue, and malaria
- Demonstrate the framework's capability to operate on surveillance-based epidemiological data

**Limitations:**
- Irregular reporting across weeks and regions
- Focus on outbreak events rather than continuous case time series
- Variation in reporting completeness across disease categories

---

## Data Provenance Summary

| Disease | Primary Source | Data Type | Period | Verification |
|---------|---------------|-----------|--------|-------------|
| **COVID-19** | [covid19india.org](https://data.covid19india.org/) | Real CSV download | 2020–2021 | Verified against state bulletins |
| **Dengue** | [NCVBDC](https://ncvbdc.mohfw.gov.in/) | Official annual reports | 2019–2023 | Cross-checked with PIB, WHO, PubMed |
| **Malaria** | [NCVBDC](https://ncvbdc.mohfw.gov.in/) + [data.gov.in](https://data.gov.in/) | Official annual reports | 2019–2023 | Cross-checked with PIB, WHO WMR 2024 |
| **IDSP** | [IDSP/MoHFW](https://idsp.mohfw.gov.in/) | Weekly outbreak reports | Ongoing | Official government surveillance |
