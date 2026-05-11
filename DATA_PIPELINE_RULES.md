## Data Pipeline Rules

This document defines the folder structure and naming conventions used to ensure reproducible ingestion and standardization across multiple diseases.

### Folder Structure

Raw data (unchanged):
- `data_raw/covid/`
- `data_raw/dengue/`
- `data_raw/malaria/`
- `data_raw/idsp/`

Recommended subfolders:
- `data_raw/<disease>/source_notes/`  (links, source description, extraction notes)
- `data_raw/malaria/pdfs/`            (official report PDFs)
- `data_raw/malaria/extracted/`       (tables extracted from PDFs as CSV)
- `data_raw/idsp/reports/`            (weekly report files if stored)
- `data_raw/idsp/compiled/`           (compiled weekly dataset if used)

Processed data (standardized outputs):
- `data_processed/covid/standardized.csv`
- `data_processed/dengue/standardized.csv`
- `data_processed/malaria/standardized.csv`
- `data_processed/idsp/standardized.csv`

Unified merged dataset (optional but recommended):
- `data_processed/unified/all_diseases_standardized.csv`

### Naming Conventions

- Use lowercase folder names for diseases: `covid`, `dengue`, `malaria`, `idsp`.
- Use consistent output name: `standardized.csv` for every adapter output.
- If multiple raw files exist, keep original filenames and store a short note in `source_notes/`.

### Adapter Execution Convention

Each adapter reads from:
- `data_raw/<disease>/`

Each adapter writes to:
- `data_processed/<disease>/standardized.csv`

Adapters must not overwrite raw data.

### Traceability

Every standardized row must include:
- `source` field referencing the dataset origin (name + date/version if known)

This ensures every forecast, risk score, and plot can be traced back to its source.
Status: Draft v1 (Phase 2 Step 8 completed)
