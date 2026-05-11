# India Multi-Disease Epidemiology Framework

## Project Overview

This framework provides a unified platform for tracking, analyzing, and visualizing epidemiological data across multiple diseases in India. The system aggregates data from various sources including COVID-19, Dengue, Malaria, and IDSP (Integrated Disease Surveillance Programme) reports.

## Goals

1. **Data Unification**: Standardize data from multiple disease surveillance sources into a common schema
2. **Scalable Architecture**: Support easy addition of new diseases and data sources
3. **Analytics Ready**: Provide clean, processed data suitable for ML/AI analysis
4. **User-Friendly Interface**: Modern dashboard for data exploration and visualization

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Frontend (React)                       │
│  - Dashboard with disease/state/district selection          │
│  - Data visualization components                            │
│  - Real-time data loading                                   │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                     Backend (Flask)                         │
│  - REST API endpoints                                       │
│  - Data aggregation services                                │
│  - Disease-specific adapters                                │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                   Data Processing Layer                     │
│  - Raw data ingestion                                       │
│  - Cleaning & standardization                               │
│  - Unified schema transformation                            │
└─────────────────────────────────────────────────────────────┘
```

## Supported Diseases

| Disease | Data Source | Status |
|---------|-------------|--------|
| COVID-19 | covid19india.org API, MoHFW | Planned |
| Dengue | NVBDCP, State Health Departments | Planned |
| Malaria | NVL Portal, State Reports | Planned |
| IDSP | Weekly Outbreak Reports | Planned |

## Tech Stack

- **Backend**: Python 3.10+, Flask, Pandas, NumPy, Scikit-learn
- **Frontend**: React 18, Vite, Vanilla CSS
- **Data Storage**: CSV files (initial), PostgreSQL (future)

## Directory Structure

```
.
├── backend/              # Flask API server
├── frontend/             # React dashboard
├── data_raw/             # Original/source data files
├── data_processed/       # Cleaned, standardized data
└── docs/                 # Project documentation
```

## Getting Started

See the [README.md](../README.md) for setup and run instructions.

## Milestones

- [ ] Phase 1: Project scaffold and basic API
- [ ] Phase 2: COVID-19 data adapter
- [ ] Phase 3: Dengue & Malaria adapters
- [ ] Phase 4: IDSP integration
- [ ] Phase 5: ML prediction models
- [ ] Phase 6: Advanced visualizations
