```
███╗   ██╗    ███████╗    ██╗  ██╗     ██████╗     ██████╗      █████╗
████╗  ██║    ██╔════╝    ╚██╗██╔╝    ██╔═══██╗    ██╔══██╗    ██╔══██╗
██╔██╗ ██║    █████╗       ╚███╔╝     ██║   ██║    ██████╔╝    ███████║
██║╚██╗██║    ██╔══╝       ██╔██╗     ██║   ██║    ██╔══██╗    ██╔══██║
██║ ╚████║    ███████╗    ██╔╝ ██╗    ╚██████╔╝    ██║  ██║    ██║  ██║
╚═╝  ╚═══╝    ╚══════╝    ╚═╝  ╚═╝     ╚═════╝     ╚═╝  ╚═╝    ╚═╝  ╚═╝
```

# Nexora — Autonomous AI Predictive Analytics Platform

An autonomous predictive analytics platform that profiles datasets, builds optimized preprocessing pipelines, trains reproducible model registries, runs batch predictions, monitors feature drift, and provides grounded AI educational interactive chats from a single CSV upload.


---

[![Backend CI](https://github.com/jeet2005/Nexora/actions/workflows/ci-backend.yml/badge.svg?branch=main)](https://github.com/jeet2005/Nexora/actions/workflows/ci-backend.yml)
[![Frontend CI](https://github.com/jeet2005/Nexora/actions/workflows/ci-frontend.yml/badge.svg?branch=main)](https://github.com/jeet2005/Nexora/actions/workflows/ci-frontend.yml)
[![GitHub stars](https://img.shields.io/github/stars/jeet2005/Nexora?style=social)](https://github.com/jeet2005/Nexora/stargazers)
[![GitHub issues](https://img.shields.io/github/issues/jeet2005/Nexora)](https://github.com/jeet2005/Nexora/issues)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)
[![Made with FastAPI](https://img.shields.io/badge/Made%20with-FastAPI-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Python](https://img.shields.io/badge/Python-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![scikit-learn](https://img.shields.io/badge/scikit--learn-5C9E48?logo=scikit-learn&logoColor=white)](https://scikit-learn.org/)
[![XGBoost](https://img.shields.io/badge/XGBoost-1A4B8D?logo=xgboost&logoColor=white)](https://xgboost.ai/)
[![LightGBM](https://img.shields.io/badge/LightGBM-00A8A1?logo=lightgbm&logoColor=white)](https://lightgbm.ai/)
[![CatBoost](https://img.shields.io/badge/CatBoost-1F8E4B?logo=catboost&logoColor=white)](https://catboost.ai/)
[![SHAP](https://img.shields.io/badge/SHAP-FF6F00?logo=shap&logoColor=white)](https://github.com/slundberg/shap)
[![React](https://img.shields.io/badge/Frontend-React-61dafb?logo=react&logoColor=white)](https://reactjs.org/)
[![TypeScript](https://img.shields.io/badge/TypeScript-3178C6?logo=typescript&logoColor=white)](https://www.typescriptlang.org/)
[![Recharts](https://img.shields.io/badge/Recharts-181717?logo=recharts&logoColor=white)](https://recharts.org/)
[![Completion](https://img.shields.io/badge/Completion-90%25-brightgreen)](COMPLETION_STATUS.md)

---

## Why Nexora?

Data scientists and developers often spend hours writing repetitive code for data profiling, exploratory analysis, preprocessing, model benchmarking, and production endpoint deployments. Nexora bridges this gap by serving as a unified prediction engine. 

By uploading a single dataset (supporting CSV, Excel, Parquet, JSON, JSONL, TSV, HTML, XML, Feather, ORC, Stata, SAS, SPSS, SQL, Pickles, HDF5, and 100+ more formats), developers can instantly audit dataset health, clean features, benchmark leading machine learning models side-by-side, analyze SHAP explainability insights, download compiled PDF reports, converse with a grounded AI dataset assistant, export trained models (.joblib), and deploy production-ready prediction API endpoints secured by unique API keys.

---

## Key Features - Full Terminal Parity!

[*] Interactive CLI Wizard - Same 9-stage workflow as web, no browser needed
[*] Full Terminal Access - `nexora train`, `nexora predict`, `nexora explain`, `nexora cluster`, `nexora forecast`
[*] Python Library - Import Nexora in scripts for automation
[*] 100+ Data Formats - CSV, Excel, Parquet, SQL, MongoDB, S3, Google Sheets, scikit-learn datasets
[*] 6 ML Families - Linear, Tree-based, Boosting (XGB/LGBM/CatBoost), Neural Networks, Ensemble
[*] Auto Preprocessing - Missing imputation, encoding, scaling, outlier handling, deduplication
[*] SHAP Explanations - Feature importance, what-if analysis, decision drivers
[*] Deployment - FastAPI, Flask, Streamlit, Docker, Jupyter export  

### Quick Command Examples
```bash
nexora                                    # Interactive wizard
nexora train data.csv --target revenue   # Train models
nexora predict model.nx new_data.csv     # Make predictions
nexora explain model.nx                  # Feature importance
nexora serve model.nx --port 8000        # REST API
```

**No web browser required. Everything in the terminal!** See [CLI_FEATURES.md](CLI_FEATURES.md) for all commands.

---

## Live Deployments

| Component | URL | Host Provider |
| :--- | :--- | :--- |
| **Frontend Web App** | [nexoraprediction.netlify.app](https://nexoraprediction.netlify.app/) | Netlify |
| **Backend API** | [nexora-360r.onrender.com](https://nexora-360r.onrender.com/) | Render |
| **API Documentation** | [nexora-360r.onrender.com/docs](https://nexora-360r.onrender.com/docs) | Render |

*Note: The backend API runs on Render's free tier and spins down after periods of inactivity. Please allow 30 to 60 seconds for the initial cold start when first accessing the application.*

*Note: The educational assistant (Ollama integration) requires a local Ollama instance and is only active when running the application locally. See local setup guidelines below.*

---

Visit the frontend demo page at `/how_nexora_works.html` to learn how Nexora works, including monitoring and drift detection features.

## System Architecture

The diagram below outlines the end-to-end data flow, processing components, and communication layers in Nexora:

```mermaid
graph TD
    subgraph Client Layer
        A[React Frontend]
    end

    subgraph Service API Layer
        B[FastAPI Backend Gateway]
        C[Dataset Analyzer & Validator]
        D[Preprocessing Engine]
        E[Training Manager & Registry]
        F[SHAP Explainability Engine]
        G[Grounded Chat Agent]
        H[API Key Deployment Manager]
    end

    subgraph Storage & Compute
        I[(Local Uploads / MongoDB)]
        J[Local Ollama / Phi-3 Mini]
        K[ML Models: XGBoost, CatBoost, LightGBM, Scikit-Learn]
    end

    A -->|Upload CSV & Configuration| B
    B --> C
    B --> D
    B --> E
    B --> F
    B --> G
    B --> H

    C <-->|Read / Write Datasets| I
    D <-->|Save Clean Pipelines| I
    E <-->|Real-time Socket Updates| A
    E <-->|Benchmark & Serialize| K
    F -->|Render Report| I
    G <-->|Dataset Context Queries| J
    H <-->|Authorize Keys & Serves| K
```

---

## Core Features

### 1. Dataset Intelligence Engine
* **Automated Multi-Format Validation** - Handles CSV, Excel, Parquet, JSON, and 100+ tabular file formats. Formats columns, assesses size boundaries, and verifies integrity.
* **Health Profiling** - Evaluates structural completeness, statistical anomalies, and generates per-column scorecards.
* **Preview and Distributions** - Offers statistical summaries, skew metrics, and categorical balance diagnostics.

### 2. Dynamic Preprocessing Pipelines
* **Type Parsing** - Separates numerical parameters, categorical labels, datetimes (with enhanced Unix timestamp detection), and identifier variables.
* **Intelligent Preprocessing** - Implements missing values imputation, standard scaling, target-label encoding, outlier detection, and duplicate record cleaning.
* **Interactive Configuration** - Provides controls to select prediction targets and customize individual preprocessing steps.

### 3. Prediction Studio and Benchmarking
* **Model Registry** - Supports multiple algorithms including XGBoost, CatBoost, LightGBM, and Scikit-Learn ensembles.
* **Training Pipeline** - Executes cross-validation splits, train-test isolation, and hyperparameter parameter sweeps.
* **WebSocket Leaderboard** - Streams active model training metrics and charts real-time scores directly to the UI.
* **Comparison Arena** - Visualizes metrics, prediction drift charts, and latency histograms of trained models.

### 4. Interactive Data Visualization
* **Multi-Chart Dashboard** - Displays numerical trends, categorical patterns, and completeness heatmaps.
* **Data Health Visualization** - Compiles data quality stats, missing records rates, and unique features counts.
* **Correlation Insights** - Flags linear dependencies, high associations, and outlier counts.

### 5. Production Suite
* **Model Export** - Easily download compiled `.joblib` model artifacts for offline use.
* **API Endpoints** - Deploys production-grade prediction endpoints secured by custom API keys.
* **Batch Processing** - Enables bulk uploads to retrieve fully enriched output prediction sheets.
* **Drift Detection** - Compares historical prediction request signatures to highlight potential target concept drift.
* **Grounded LLM Chat** - Integrates local Ollama models (Phi-3 Mini) to act as a database context tutor answering questions regarding data distribution trends.

---

## Technical Stack

| Layer | Technologies |
| :--- | :--- |
| **Frontend Web App** | React 18, Vite, TypeScript, Tailwind CSS, Framer Motion, Recharts, Axios, Lucide Icons |
| **Backend Service API** | Python 3.11, FastAPI, Uvicorn, Pydantic, Pandas, NumPy, Scikit-learn, CatBoost, LightGBM, XGBoost |
| **Data Persistence** | MongoDB Atlas / Local File Storage |
| **Local LLM Integration** | Ollama Engine (Phi-3 Mini) |
| **Infrastructure Platforms** | Netlify (Frontend), Render (Backend) |

---

## Local Development

### Installation Prerequisites

| Dependency | Minimum Version |
| :--- | :--- |
| Python | 3.11 or higher |
| Node.js | 20 or higher |
| npm | 10 or higher |
| Ollama | Latest (optional, for grounded Q&A) |

### Development Option 1: Standard Installation

#### 1. Clone the Project
```bash
git clone https://github.com/jeet2005/Nexora.git
cd Nexora
```

#### 2. Configure Backend Service
```bash
cd backend
python -m venv .venv

# Activate Virtual Environment (Windows)
.venv\Scripts\activate

# Activate Virtual Environment (macOS / Linux)
source .venv/bin/activate

# Install dependencies and setup configuration
pip install -r requirements.txt
cp .env.example .env

# Run development server
python run.py
```
The backend service will be available at `http://localhost:8000`. You can test endpoints on Swagger UI at `http://localhost:8000/docs`.

#### 3. Configure Frontend Application
```bash
cd ../frontend
npm install
cp .env.example .env.local

# Run development server
npm run dev
```
The React frontend application will be active at `http://localhost:5173`.

---

### Development Option 2: Docker Compose Setup

Run the entire stack (FastAPI, React, and MongoDB) with a single command:

```bash
docker compose up --build
```

* **Frontend Web App**: Access at `http://localhost:3000`
* **Backend API**: Access at `http://localhost:8000`
* **MongoDB Instance**: Running on port `27017`

---

### Development Option 3: Makefile Shortcuts

If you have Make installed, you can orchestrate development commands directly from the project root:

* Install all package dependencies: `make install`
* Launch backend locally: `make dev-backend`
* Launch frontend locally: `make dev-frontend`
* Run backend pytest suite: `make test`
* Format all file types: `make format`
* Spin up Docker containers: `make docker-up`
* Spin down Docker containers: `make docker-down`

---

## Grounded Q&A Assistant Setup (Optional)

To enable the dataset assistant using a local LLM instance:

1. Download and install [Ollama](https://ollama.com/).
2. Pull the default micro-LLM model in your terminal:
   ```bash
   ollama pull phi3:mini
   ```
3. Keep Ollama active in the background. The assistant will detect local hosting at `http://localhost:11434` and enable custom educational conversations.

---

## Repository Roadmap

- [ ] Add Pytest code coverage reports in the Backend CI pipeline.
- [ ] Implement multi-file comparison dashboards within the Frontend page.
- [ ] Add support for automated time-series forecasting hyperparameter tuning.
- [ ] Integrate PostgreSQL database schema mappings for enterprise persistence layers.
- [ ] Add REST API key rotation options inside the Production UI.
- [ ] Create automated end-to-end integration tests using Playwright.

---

## Contributing and Governance

Contributions are welcome. Please read our [Contributing Guidelines](CONTRIBUTING.md) to understand branch conventions, pull request structures, and developer standards. Ensure all contributions align with our [Code of Conduct](CODE_OF_CONDUCT.md).

For vulnerability notifications, refer to our [Security Policy](SECURITY.md).

---

## License

Nexora is open-source software licensed under the [MIT License](LICENSE).
