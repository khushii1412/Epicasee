# Adapters Implementation Plan

## Overview

Adapters are responsible for transforming raw data from various sources into the unified schema. Each disease has one or more adapters corresponding to its data sources.

---

## Adapter Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     BaseAdapter (ABC)                       │
│  - fetch_raw()           Abstract method to get raw data    │
│  - parse()               Abstract method to parse data      │
│  - transform()           Convert to unified schema          │
│  - validate()            Validate against schema            │
│  - save()                Write to data_processed/           │
└─────────────────────────────────────────────────────────────┘
                              │
          ┌───────────────────┼───────────────────┐
          ▼                   ▼                   ▼
   CovidAdapter        DengueAdapter       MalariaAdapter
```

---

## Base Adapter Interface

```python
# backend/adapters/base.py

from abc import ABC, abstractmethod
import pandas as pd

class BaseAdapter(ABC):
    """Base class for all disease adapters."""
    
    disease_key: str  # e.g., "covid", "dengue"
    
    @abstractmethod
    def fetch_raw(self) -> None:
        """Download/copy raw data to data_raw/{disease}/"""
        pass
    
    @abstractmethod
    def parse(self) -> pd.DataFrame:
        """Parse raw data into DataFrame."""
        pass
    
    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        """Transform to unified schema."""
        # Common transformations
        pass
    
    def validate(self, df: pd.DataFrame) -> bool:
        """Validate against unified schema."""
        pass
    
    def save(self, df: pd.DataFrame) -> str:
        """Save to data_processed/{disease}/standardized.csv"""
        pass
    
    def run(self) -> str:
        """Execute full pipeline."""
        self.fetch_raw()
        df = self.parse()
        df = self.transform(df)
        if self.validate(df):
            return self.save(df)
```

---

## COVID-19 Adapter

### Sources to Handle

1. **covid19india.org API** (historical JSON)
2. **MoHFW scraped data** (current)
3. **State-wise CSV archives**

### Implementation Steps

- [ ] Create `CovidAdapter` class
- [ ] Implement JSON parser for covid19india.org format
- [ ] Add state name normalization
- [ ] Calculate daily deltas from cumulative
- [ ] Handle district-level data
- [ ] Add data validation

### File: `backend/adapters/covid_adapter.py`

---

## Dengue Adapter

### Sources to Handle

1. **NVBDCP PDFs** (monthly reports)
2. **State health portal data** (scraped)

### Implementation Steps

- [ ] Create `DengueAdapter` class
- [ ] Implement PDF extraction using tabula-py
- [ ] Parse yearly/monthly aggregates
- [ ] Handle inconsistent column names
- [ ] Aggregate to state level

### File: `backend/adapters/dengue_adapter.py`

---

## Malaria Adapter

### Sources to Handle

1. **NVBDCP Excel files**
2. **Annual report PDFs**

### Implementation Steps

- [ ] Create `MalariaAdapter` class
- [ ] Implement Excel parser
- [ ] Handle Pf/Pv breakdown
- [ ] Extract from annual report tables
- [ ] Normalize district names

### File: `backend/adapters/malaria_adapter.py`

---

## IDSP Adapter

### Sources to Handle

1. **Weekly outbreak reports (PDF)**

### Implementation Steps

- [ ] Create `IDSPAdapter` class
- [ ] Implement PDF table extraction
- [ ] Parse outbreak-specific format
- [ ] Map disease names to codes
- [ ] Handle multi-disease reports

### File: `backend/adapters/idsp_adapter.py`

---

## Common Utilities

### State Name Mapper

```python
# backend/utils/state_mapper.py

STATE_ALIASES = {
    "orissa": "Odisha",
    "pondicherry": "Puducherry",
    "a & n islands": "Andaman and Nicobar Islands",
    "d & n haveli": "Dadra and Nagar Haveli and Daman and Diu",
    # ... more aliases
}

def normalize_state(name: str) -> str:
    """Normalize state name to standard form."""
    pass
```

### Date Parser

```python
# backend/utils/date_parser.py

def parse_various_dates(date_str: str) -> str:
    """Handle multiple date formats, return YYYY-MM-DD."""
    pass
```

---

## Testing Strategy

1. **Unit tests** for each adapter's parse/transform methods
2. **Integration tests** with sample raw data files
3. **Schema validation tests** for output CSVs
4. **Regression tests** to detect format changes in sources

---

## Priority Order

| Priority | Adapter | Complexity | Reason |
|----------|---------|------------|--------|
| 1 | COVID | Medium | Most complete data available |
| 2 | Malaria | Low | Well-structured Excel files |
| 3 | Dengue | Medium | PDF extraction needed |
| 4 | IDSP | High | Complex PDF parsing |

---

## Future Adapters

| Disease | Source | Notes |
|---------|--------|-------|
| Chikungunya | NVBDCP | Similar to Dengue |
| Typhoid | IDSP | Part of outbreak reports |
| Cholera | IDSP | Part of outbreak reports |
| TB | TB India Portal | Separate system |
