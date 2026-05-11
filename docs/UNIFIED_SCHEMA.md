# Unified Data Schema

## Overview

This document defines the standardized schema used across all disease datasets. By transforming heterogeneous source data into a common format, we enable cross-disease analysis and consistent API responses.

---

## Core Schema: `standardized.csv`

Each disease adapter must produce a `standardized.csv` file in `data_processed/{disease}/` with the following columns:

### Required Fields

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| `date` | DATE | Date of observation (YYYY-MM-DD) | 2023-06-15 |
| `state` | STRING | Standardized state name | Maharashtra |
| `cases` | INTEGER | Number of cases | 1234 |
| `deaths` | INTEGER | Number of deaths | 12 |

### Optional Fields

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| `district` | STRING | District name (if available) | Pune |
| `recovered` | INTEGER | Number of recoveries | 1100 |
| `active` | INTEGER | Current active cases | 122 |
| `tested` | INTEGER | Number tested | 5000 |
| `week` | INTEGER | Epidemiological week (1-52) | 24 |
| `month` | INTEGER | Month (1-12) | 6 |
| `year` | INTEGER | Year | 2023 |

### Metadata Fields

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| `source` | STRING | Data source identifier | nvbdcp |
| `disease` | STRING | Disease identifier | dengue |
| `ingested_at` | DATETIME | When data was processed | 2023-12-01T10:30:00 |

---

## State Name Standardization

All state names must be normalized to official Census 2011 names:

```
Andhra Pradesh
Arunachal Pradesh
Assam
Bihar
Chhattisgarh
Goa
Gujarat
Haryana
Himachal Pradesh
Jharkhand
Karnataka
Kerala
Madhya Pradesh
Maharashtra
Manipur
Meghalaya
Mizoram
Nagaland
Odisha
Punjab
Rajasthan
Sikkim
Tamil Nadu
Telangana
Tripura
Uttar Pradesh
Uttarakhand
West Bengal
```

### Union Territories

```
Andaman and Nicobar Islands
Chandigarh
Dadra and Nagar Haveli and Daman and Diu
Delhi
Jammu and Kashmir
Ladakh
Lakshadweep
Puducherry
```

---

## Data Types & Constraints

### Date Handling

- All dates in ISO 8601 format: `YYYY-MM-DD`
- For weekly data without specific date, use Monday of that week
- For monthly data without specific date, use 1st of month

### Numeric Fields

- Use `-1` for missing/unknown values (not NaN)
- All counts must be non-negative integers
- Rates should be calculated fields, not stored

### String Fields

- UTF-8 encoding throughout
- No leading/trailing whitespace
- State names: Title Case
- District names: Title Case

---

## Disease-Specific Extensions

### COVID-19 Extension

| Column | Type | Description |
|--------|------|-------------|
| `confirmed` | INTEGER | Cumulative confirmed |
| `daily_cases` | INTEGER | New cases that day |
| `daily_deaths` | INTEGER | New deaths that day |
| `daily_recovered` | INTEGER | New recoveries that day |

### Malaria Extension

| Column | Type | Description |
|--------|------|-------------|
| `pf_cases` | INTEGER | P. falciparum cases |
| `pv_cases` | INTEGER | P. vivax cases |
| `mixed_cases` | INTEGER | Mixed infection cases |

### IDSP Extension

| Column | Type | Description |
|--------|------|-------------|
| `outbreak_id` | STRING | Unique outbreak identifier |
| `reporting_week` | STRING | YYYY-WXX format |
| `disease_name` | STRING | Specific disease name |

---

## Validation Rules

1. `date` must be valid and not in the future
2. `state` must exist in the standardized state list
3. `cases >= deaths` (deaths cannot exceed cases)
4. `active + recovered + deaths <= cases` (for COVID)
5. No duplicate rows for same `(date, state, district)`

---

## Example Record

```csv
date,state,district,cases,deaths,recovered,active,source,disease,ingested_at
2023-06-15,Maharashtra,Pune,1234,12,1100,122,mohfw,covid,2023-12-01T10:30:00
```

---

## Unified Cross-Disease View

For unified analysis, a `data_processed/unified/all_diseases.csv` may be generated:

| Column | Type | Description |
|--------|------|-------------|
| `date` | DATE | Date of observation |
| `state` | STRING | State name |
| `district` | STRING | District (nullable) |
| `disease` | STRING | Disease identifier |
| `cases` | INTEGER | Case count |
| `deaths` | INTEGER | Death count |
