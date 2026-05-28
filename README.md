#  India Multi-Disease Epidemiology Framework

A comprehensive platform for tracking, analyzing, and visualizing epidemiological data across multiple diseases in India.

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.10+-green.svg)
![React](https://img.shields.io/badge/react-18-blue.svg)

## Overview

This framework provides a unified platform for:
- **Data Aggregation**: Collect data from multiple disease surveillance sources
- **Standardization**: Transform heterogeneous data into a common schema
- **Visualization**: Interactive dashboard for data exploration
- **Analysis**: Foundation for ML/AI epidemiological models

### Supported Diseases

| Disease | Status | Data Source |
|---------|--------|-------------|
|  COVID-19 | Active / Supported | MoHFW, covid19india.org |
|  Dengue | Active / Supported | NVBDCP |
|  Malaria | Active / Supported | NVBDCP |
|  IDSP | Planned | NCDC Weekly Reports |

##  Project Structure

```
.
├── backend/                 # Flask API server
│   ├── app.py              # Main application
│   ├── config.py           # Configuration
│   ├── requirements.txt    # Python dependencies
│   ├── adapters/           # Disease-specific data adapters
│   ├── services/           # Business logic
│   ├── routes/             # API route definitions
│   ├── utils/              # Helper utilities
│   └── data_processed/     # Backend processed data (local)
│
├── frontend/               # React dashboard
│   ├── package.json        # Node dependencies
│   ├── vite.config.js      # Vite configuration
│   ├── index.html          # Entry HTML
│   └── src/
│       ├── main.jsx        # React entry point
│       ├── App.jsx         # Root component
│       ├── index.css       # Global styles
│       ├── api/            # API client
│       ├── components/     # Reusable components
│       └── pages/          # Page components
│
├── data_raw/               # Original source data
│   ├── covid/              # COVID-19 raw data
│   ├── dengue/             # Dengue raw data
│   ├── malaria/            # Malaria raw data
│   └── idsp/               # IDSP raw data
│
├── data_processed/         # Cleaned, standardized data
│   ├── covid/              # Processed COVID data
│   ├── dengue/             # Processed Dengue data
│   ├── malaria/            # Processed Malaria data
│   ├── idsp/               # Processed IDSP data
│   └── unified/            # Combined cross-disease data
│
├── docs/                   # Documentation
│   ├── PROJECT_SPEC.md     # Project specification
│   ├── DATA_SOURCES.md     # Data source catalog
│   ├── UNIFIED_SCHEMA.md   # Unified schema definition
│   ├── ADAPTERS_PLAN.md    # Adapter implementation plan
│   └── DATA_PIPELINE_RULES.md  # Processing rules
│
└── README.md               # This file
```

## Getting Started

### Prerequisites

- **Python 3.10+** with pip
- **Node.js 18+** with npm
- **Git**

### Clone the Repository

```bash
git clone <repository-url>
cd "Major Project"
```

---

## 🔧 Backend Setup

The backend is a Flask API server that serves epidemiological data.

### 1. Navigate to Backend Directory

```bash
cd backend
```

### 2. Create Virtual Environment (Recommended)

```bash
python -m venv venv
source venv/bin/activate  # On macOS/Linux
# OR
venv\Scripts\activate     # On Windows
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Run the Backend Server

```bash
python app.py
```

The backend will start on **http://localhost:5001**

### Available API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/health` | GET | Health check |
| `/api/diseases` | GET | List available diseases |
| `/api/states?disease_key=<key>` | GET | List states for a disease |
| `/api/districts?disease_key=<key>&state=<state>` | GET | List districts for a state |
| `/api/state-profile?state=<state>&disease=<disease>` | GET | Get comprehensive state profile, Z-score anomalies, risk scores, best ML model, and forecasts |
| `/api/data-quality` | GET | Dynamic data quality score, missing value rates, data granularity notes, and schema validations |
| `/api/briefing` | GET | Deterministic executive multi-disease early warning brief summarizing hotspots and forecast trends |
| `/api/intelligence-summary` | GET | Government-style Executive Intelligence Report aggregating pathogen metrics and active alerts |
| `/api/disease-comparison-v2` | GET | Pathogen-to-pathogen comparison across COVID, Dengue, and Malaria risk profiles |

### 🧠 Advanced Epidemiological Intelligence Services

The framework integrates several decoupled analytical engines running under `backend/services/`:

1. **Risk Engine (`services/risk_engine.py`)**: Computes comprehensive weighted risk scores (out of 100) combining case volume (30%), expansion growth (20%), mortality CFR (15%), seasonal monsoon flags (15%), statistical anomalies (10%), and outbreak intensity (10%).
2. **Anomaly Detection (`services/anomaly_detection.py`)**: Performs time-series outbreak detection using a 4-quarter rolling Z-score statistical baseline to flag possible outbreak spikes.
3. **Model Leaderboard (`services/model_leaderboard.py` & `services/backtesting.py`)**: Backtests Machine Learning regression models (Linear, Ridge, Random Forest, and Gradient Boosting Regressors) using rolling-origin backtesting (RMSE, MAE, R2, sMAPE) to automatically select and rank the highest-performing forecasting model.
4. **Recursive Forecasting (`services/forecasting_v2.py`)**: Generates 4-quarter-ahead recursive forecasts with custom uncertainty bounds (+/- 1.96 * RMSE) for future quarters.
5. **Data Quality Auditor (`services/data_quality.py`)**: Analyzes standardized dataset schemas, counts missingness excluding intentional state-level district blanks, and scores the dataset out of 100.
6. **Early Warning Briefing (`services/briefing.py`)**: Harmonizes risk, alert feeds, and forecast trends into a deterministic, highly-readable executive briefing summary.

---

##  Frontend Setup

The frontend is a React application built with Vite.

### 1. Navigate to Frontend Directory

```bash
cd frontend
```

### 2. Install Dependencies

```bash
npm install
```

### 3. Run the Development Server

```bash
npm run dev
```

The frontend will start on **http://localhost:5173** (Vite default port)

---

## 🖥️ Running Both Servers

For development, run both servers in separate terminals:

**Terminal 1 (Backend):**
```bash
cd backend
python app.py
```

**Terminal 2 (Frontend):**
```bash
cd frontend
npm run dev
```

Then open **http://localhost:5173** in your browser.

---

## 📊 Adding Data

To see data in the dashboard, you need to add `standardized.csv` files:

### Expected Data Location

```
data_processed/
├── covid/
│   └── standardized.csv    # COVID-19 data
├── dengue/
│   └── standardized.csv    # Dengue data
├── malaria/
│   └── standardized.csv    # Malaria data
└── idsp/
    └── standardized.csv    # IDSP data
```

### Required CSV Format

```csv
date,state,district,cases,deaths,recovered,source,disease
2023-06-15,Maharashtra,Pune,1234,12,1100,mohfw,covid
```

See [docs/UNIFIED_SCHEMA.md](docs/UNIFIED_SCHEMA.md) for the complete schema.

---

##  Documentation

| Document | Description |
|----------|-------------|
| [PROJECT_SPEC.md](docs/PROJECT_SPEC.md) | Project goals and architecture |
| [DATA_SOURCES.md](docs/DATA_SOURCES.md) | Catalog of data sources |
| [UNIFIED_SCHEMA.md](docs/UNIFIED_SCHEMA.md) | Standardized data schema |
| [ADAPTERS_PLAN.md](docs/ADAPTERS_PLAN.md) | Adapter implementation plan |
| [DATA_PIPELINE_RULES.md](docs/DATA_PIPELINE_RULES.md) | Data processing rules |

---

##  Development

### Backend Development

```bash
cd backend
pip install -r requirements.txt
python app.py
```

The Flask server runs in debug mode with auto-reload.

### Frontend Development

```bash
cd frontend
npm install
npm run dev
```

Vite provides hot module replacement (HMR) for fast development.

### Build for Production

**Frontend:**
```bash
cd frontend
npm run build
npm run preview  # Preview production build
```

---

##  Testing

*(Tests to be added)*

```bash
# Backend tests
cd backend
pytest

# Frontend tests
cd frontend
npm run test
```

---

##  Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

##  License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

##  Acknowledgments

- Data providers: MoHFW, NVBDCP, NCDC, covid19india.org
- Open source community for Flask, React, and related tools

---

##  Support

For questions or issues, please open a GitHub issue or contact the maintainers.
