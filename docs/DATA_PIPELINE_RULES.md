# Data Pipeline Rules

## Overview

This document defines the rules and conventions for processing data through the epidemiology framework. Following these rules ensures data quality, reproducibility, and maintainability.

---

## Directory Conventions

### Raw Data (`data_raw/`)

```
data_raw/
├── {disease}/
│   ├── source_notes/     # Notes about data sources
│   ├── {format}/         # e.g., pdfs/, json/, csv/
│   └── archive/          # Old versions
```

**Rules:**
1. Never modify raw files after download
2. Use descriptive filenames with dates: `nvbdcp_dengue_2023-06.pdf`
3. Keep a `source_notes/README.md` documenting each file's origin
4. Archive old versions, don't delete

### Processed Data (`data_processed/`)

```
data_processed/
├── {disease}/
│   ├── standardized.csv  # Main output (required)
│   ├── metadata.json     # Processing metadata
│   └── intermediate/     # Intermediate processing files
└── unified/
    └── all_diseases.csv  # Combined view (optional)
```

**Rules:**
1. Always produce `standardized.csv` per disease
2. Include `metadata.json` with processing timestamps
3. Keep intermediate files for debugging

---

## Processing Pipeline Stages

### Stage 1: Ingestion

```
Raw Source → data_raw/{disease}/
```

**Tasks:**
- Download/copy source files
- Verify checksums if available
- Log source URL and timestamp
- Preserve original format

**Naming Convention:**
```
{source}_{disease}_{date}.{ext}
Example: nvbdcp_malaria_2023-07.xlsx
```

### Stage 2: Extraction

```
data_raw/{disease}/ → Parsed DataFrame
```

**Tasks:**
- Read source format (PDF, Excel, JSON, HTML)
- Extract tabular data
- Handle encoding issues
- Preserve all original columns

**Tools:**
- PDF: `tabula-py`, `camelot`
- Excel: `pandas`, `openpyxl`
- HTML: `BeautifulSoup`, `pandas.read_html`

### Stage 3: Cleaning

```
Parsed DataFrame → Clean DataFrame
```

**Tasks:**
- Remove empty rows/columns
- Handle missing values consistently
- Fix encoding issues
- Normalize whitespace

**Missing Value Rules:**
| Scenario | Value |
|----------|-------|
| Not applicable | `null` / empty |
| Unknown | `-1` (for integers) |
| Not reported | `-1` |

### Stage 4: Transformation

```
Clean DataFrame → Unified Schema DataFrame
```

**Tasks:**
- Rename columns to standard names
- Normalize state/district names
- Convert date formats to ISO 8601
- Calculate derived fields
- Add metadata columns

**Column Mapping Template:**
```python
COLUMN_MAP = {
    "original_col": "standardized_col",
    "State/UT": "state",
    "No. of Cases": "cases",
}
```

### Stage 5: Validation

```
Unified DataFrame → Validated DataFrame
```

**Validation Checks:**
1. ✅ All required columns present
2. ✅ Date format is YYYY-MM-DD
3. ✅ State names in approved list
4. ✅ Numeric fields are integers
5. ✅ No negative counts (except -1 for missing)
6. ✅ No duplicate (date, state, district) combinations
7. ✅ Deaths ≤ Cases

**Validation Output:**
```json
{
  "valid": true,
  "rows_total": 1000,
  "rows_valid": 998,
  "warnings": ["2 rows with missing district"],
  "errors": []
}
```

### Stage 6: Output

```
Validated DataFrame → data_processed/{disease}/standardized.csv
```

**Output Rules:**
1. UTF-8 encoding
2. No BOM
3. Unix line endings (LF)
4. Header row required
5. No index column
6. Null represented as empty string

---

## Metadata Schema

Each processed disease must have a `metadata.json`:

```json
{
  "disease": "covid",
  "sources": [
    {
      "name": "covid19india.org",
      "url": "https://api.covid19india.org/v4/data.json",
      "downloaded_at": "2023-12-01T10:30:00Z"
    }
  ],
  "processing": {
    "pipeline_version": "1.0.0",
    "processed_at": "2023-12-01T10:35:00Z",
    "rows_input": 5000,
    "rows_output": 4950,
    "rows_dropped": 50,
    "drop_reasons": {
      "invalid_date": 20,
      "unknown_state": 30
    }
  },
  "schema_version": "1.0"
}
```

---

## State Name Normalization

### Approved State Names

See [UNIFIED_SCHEMA.md](./UNIFIED_SCHEMA.md) for the complete list.

### Common Aliases

```python
STATE_ALIASES = {
    # Old names
    "orissa": "Odisha",
    "uttaranchal": "Uttarakhand",
    
    # Abbreviations
    "ap": "Andhra Pradesh",
    "up": "Uttar Pradesh",
    "mp": "Madhya Pradesh",
    "wb": "West Bengal",
    "tn": "Tamil Nadu",
    
    # Variations
    "delhi ncr": "Delhi",
    "new delhi": "Delhi",
    "j&k": "Jammu and Kashmir",
    "a&n islands": "Andaman and Nicobar Islands",
    
    # Typos
    "maharashtr": "Maharashtra",
    "karnatka": "Karnataka",
}
```

---

## Date Handling

### Input Formats to Support

```python
DATE_FORMATS = [
    "%Y-%m-%d",      # 2023-06-15
    "%d-%m-%Y",      # 15-06-2023
    "%d/%m/%Y",      # 15/06/2023
    "%d %b %Y",      # 15 Jun 2023
    "%B %d, %Y",     # June 15, 2023
    "%Y%m%d",        # 20230615
]
```

### Output Format

Always: `YYYY-MM-DD` (ISO 8601)

### Special Cases

| Scenario | Resolution |
|----------|------------|
| Weekly data | Use Monday of that week |
| Monthly data | Use 1st of month |
| Yearly data | Use January 1st |
| Incomplete date "Jun 2023" | Use `2023-06-01` |

---

## Error Handling

### Severity Levels

| Level | Action | Example |
|-------|--------|---------|
| ERROR | Stop processing | Schema violation |
| WARNING | Log and continue | Minor data quality issue |
| INFO | Log only | Processing statistics |

### Error Logging

```python
import logging

logging.basicConfig(
    filename='logs/pipeline_{date}.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
```

---

## Idempotency

**Rule:** Running the same pipeline twice on the same input must produce identical output.

**Implementation:**
1. Use deterministic sorting before output
2. Set random seeds if any randomness involved
3. Include source file checksums in metadata
4. Version the pipeline code

---

## Change Detection

When processing updates:

1. Compare new output with existing `standardized.csv`
2. Log rows added, modified, or removed
3. Keep history of changes for auditing

```python
def detect_changes(old_df, new_df):
    """Return added, removed, and modified rows."""
    pass
```

---

## Performance Guidelines

| Dataset Size | Approach |
|-------------|----------|
| < 100K rows | In-memory pandas |
| 100K - 1M rows | Chunked processing |
| > 1M rows | Consider Dask/Spark |

---

## Quality Metrics

Track these metrics per pipeline run:

1. **Completeness**: % of non-null values per column
2. **Validity**: % of rows passing all validation
3. **Uniqueness**: % of unique key combinations
4. **Timeliness**: Data lag from source date

Report format:
```
Pipeline Run Summary (2023-12-01)
================================
Disease: COVID-19
Rows processed: 5,000
Rows valid: 4,950 (99.0%)
Completeness:
  - date: 100%
  - state: 100%
  - district: 75%
  - cases: 100%
  - deaths: 98%
```
