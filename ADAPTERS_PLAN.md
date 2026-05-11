## Adapter Design Plan

Each disease dataset is converted into the unified schema using a dedicated adapter. Adapters ensure that heterogeneous epidemiological datasets (different formats, different frequencies, different geographic detail) can be processed by a single shared forecasting and early warning pipeline.

All adapters follow the same contract:

Input:
- Raw dataset file(s) in `data_raw/<disease>/`
- Metadata (source name, frequency, geo-level)

Output:
- A standardized CSV in `data_processed/<disease>/standardized.csv`
- Columns must match the unified schema defined in `UNIFIED_SCHEMA.md`

General Responsibilities (all adapters):
- Parse and load raw files
- Normalize column names and data types
- Normalize state and district naming
- Normalize time indexing (daily/weekly/yearly)
- Handle missing values explicitly (missing ≠ zero)
- Add a `source` field for traceability
Status: Draft v1 (Phase 2 Step 7.1 completed)

## Adapter: COVID-19 (`covid_adapter.py`)

Purpose:
Convert COVID-19 time-series data (daily, state/district) into the unified schema and provide a weekly standardized dataset for forecasting and early warning.

Raw Input Location:
- `data_raw/covid/` (CSV/JSON files depending on source)

Expected Raw Fields (typical):
- date
- state
- district (optional)
- confirmed / cases
- deaths (optional)
- tests (optional)
- positivity (optional)

Key Transformations:
1. Column Standardization
- Map raw fields to standard names: cases, deaths, tests, positivity.
- Ensure numeric fields are parsed as integers/floats.

2. Geographic Normalization
- Standardize state names to a single canonical list.
- Standardize district names where present.
- If district is missing, set `geo_level = "state"` and district = null.

3. Time Normalization
- Parse daily dates into ISO date format.
- Aggregate daily data into weekly counts:
  - week_start = Monday of the week (ISO week start)
  - weekly_cases = sum(daily_cases) within the week
  - weekly_deaths = sum(daily_deaths) if available
  - tests and positivity:
    - tests: sum if daily tests exist
    - positivity: weekly weighted average if possible, else null

4. Missing Data Handling
- Keep missing values as null.
- Record weeks with partial data for data-quality reporting.

Unified Output Mapping:
- disease = "COVID-19"
- geo_level = "district" if district exists else "state"
- state = normalized state
- district = normalized district or null
- time_index = week_start (ISO date)
- frequency = "weekly"
- cases = weekly_cases
- deaths = weekly_deaths or null
- tests = weekly_tests or null
- positivity = weekly_positivity or null
- source = dataset reference string

Output File:
- `data_processed/covid/standardized.csv`
Status: Draft v1 (Phase 2 Step 7.2 completed)

## Adapter: Dengue (`dengue_adapter.py`)

Purpose:
Convert dengue surveillance data (typically annual, sometimes monthly/weekly depending on source) into the unified schema for trend analysis, regional comparison, and risk assessment.

Raw Input Location:
- `data_raw/dengue/` (often CSV, Excel, or manually extracted tables)

Expected Raw Fields (typical):
- year (or date/month if available)
- state
- cases
- deaths (optional)

Key Transformations:
1. Column Standardization
- Map raw fields to standard names: cases, deaths.
- Parse numeric fields as integers.

2. Geographic Normalization
- Standardize state names to a canonical list.
- If district-level dengue is available in selected sources, include district and set geo_level accordingly; otherwise district = null and geo_level = "state".

3. Time Normalization
- If data is annual:
  - time_index = year (string)
  - frequency = "yearly"
- If data is monthly/weekly (where available):
  - convert to weekly using week_start rules or keep monthly only for visualization (weekly preferred if forecasting is applied)

4. Missing Data Handling
- Missing values remain null.
- If deaths are not reported, set deaths = null.

Unified Output Mapping (annual default):
- disease = "Dengue"
- geo_level = "state" (or "district" if district data exists)
- state = normalized state
- district = normalized district or null
- time_index = year (or week_start if weekly is available)
- frequency = "yearly" (or "weekly" if weekly data exists)
- cases = reported_cases
- deaths = reported_deaths or null
- source = dataset reference string

Output File:
- `data_processed/dengue/standardized.csv`
Status: Draft v1 (Phase 2 Step 7.3 completed)

## Adapter: Malaria (`malaria_adapter.py`)

Purpose:
Convert malaria surveillance data (typically annual, often district-level in official reports) into the unified schema for spatial risk mapping, long-term trend analysis, and cross-disease comparison.

Raw Input Location:
- `data_raw/malaria/` (often PDFs with district tables; extracted into CSV for processing)

Expected Raw Fields (typical, after extraction):
- year
- state
- district (often available)
- cases
- deaths (optional)

Key Transformations:
1. Column Standardization
- Map extracted fields to standard names: cases, deaths.
- Ensure numeric types for cases/deaths.

2. Geographic Normalization
- Standardize state names.
- Standardize district names (remove spelling inconsistencies, casing, extra spaces).
- If district is present, set geo_level = "district"; otherwise use geo_level = "state".

3. Time Normalization
- time_index = year (string)
- frequency = "yearly"
- This dataset is primarily used for trend and risk assessment rather than short-horizon forecasting.

4. Missing Data Handling
- Keep missing values as null.
- If deaths are not reported, set deaths = null.

Unified Output Mapping:
- disease = "Malaria"
- geo_level = "district" if district exists else "state"
- state = normalized state
- district = normalized district or null
- time_index = year
- frequency = "yearly"
- cases = reported_cases
- deaths = reported_deaths or null
- source = dataset reference string

Output File:
- `data_processed/malaria/standardized.csv`
Status: Draft v1 (Phase 2 Step 7.4 completed)

## Adapter: IDSP Outbreak Surveillance (`idsp_adapter.py`)

Purpose:
Convert IDSP weekly outbreak surveillance data into the unified schema to support multi-disease outbreak monitoring and early warning analysis at weekly resolution.

Raw Input Location:
- `data_raw/idsp/` (weekly report tables or compiled datasets)

Expected Raw Fields (typical):
- report_week (or week_start / week_end)
- state
- district (often available)
- disease (or disease_category)
- cases
- deaths (optional)

Key Transformations:
1. Column Standardization
- Ensure disease labels are standardized (consistent naming for disease/category).
- Map raw fields to standard names: cases, deaths.

2. Geographic Normalization
- Standardize state and district names.
- If district is missing in a record, set geo_level = "state" and district = null.

3. Time Normalization
- Convert report week into a single standardized `week_start` date (ISO date).
- frequency = "weekly"
- time_index = week_start

4. Missing Data Handling
- Keep missing values as null.
- Track missing weeks or missing districts for data-quality reporting.

Unified Output Mapping:
- disease = standardized disease name from IDSP record
- geo_level = "district" if district exists else "state"
- state = normalized state
- district = normalized district or null
- time_index = week_start (ISO date)
- frequency = "weekly"
- cases = reported_cases
- deaths = reported_deaths or null
- source = dataset reference string

Output File:
- `data_processed/idsp/standardized.csv`
Status: Draft v1 (Phase 2 Step 7.5 completed)
