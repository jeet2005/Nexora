# Nexora CLI - Complete Feature Reference

## Overview
Nexora now provides **full terminal feature parity with the web interface**. All machine learning workflows can be run directly from the command line without any GUI.

---

## Quick Start

### Interactive Wizard (Recommended)
```bash
nexora
# or
nexora wizard
```
Launches an interactive 9-stage wizard matching the web interface exactly:
1. Data Upload & Profiling
2. Advanced Settings
3. Target Selection & Task Detection
4. Preprocessing Pipeline Display
5. Model Battle Arena (training + live leaderboard)
6. Prediction Studio
7. SHAP Explanation
8. Advanced Tracks (clustering, forecasting)
9. Export

---

## Complete Command Reference

### 1. Training & Model Management

#### `nexora train`
Train models with full control.
```bash
nexora train data.csv \
  --target sales_amount \
  --max-models 10 \
  --test-size 0.2 \
  --cv-folds 5 \
  --seed 42 \
  --out trained_model.nx
```
**Options:**
- `--target` (required): Target column to predict
- `--out`: Output session file path (default: data.nx)
- `--max-models`: Number of models to train (1-20, default: 6)
- `--test-size`: Holdout split ratio (0.1-0.4, default: 0.2)
- `--cv-folds`: Cross-validation folds (default: 5)
- `--timeout`: Per-model timeout in seconds
- `--seed`: Random seed for reproducibility (default: 42)
- `--early-stopping`: Enable early stopping (default: True)

#### `nexora quick`
Fast 30-second training with top 2 models.
```bash
nexora quick data.csv --target revenue
```

#### `nexora compare`
Compare multiple trained models.
```bash
nexora compare session.nx --limit 10
```
Shows: Rank, Model Name, Family, Score, Training Time

#### `nexora models`
List all available ML algorithms.
```bash
nexora models --task classification --category tree-based
```
**Options:**
- `--task`: Filter by 'classification' or 'regression'
- `--category`: Filter by family (linear, tree-based, boosting, neural)

---

### 2. Dataset Analysis

#### `nexora profile`
Generate comprehensive dataset health report.
```bash
nexora profile data.csv --export profile.html
```
**Outputs:**
- Health Score (0-100)
- Missing values analysis
- Column type detection
- Outlier signals
- Feature distributions
- Suggested targets

#### `nexora clean`
Preprocess dataset without training.
```bash
nexora clean data.csv \
  --target sales \
  --out cleaned_data.csv
```
Applies: Missing imputation, encoding, scaling, outlier capping, deduplication

---

### 3. Predictions & Analytics

#### `nexora predict`
Make batch predictions with best model.
```bash
nexora predict session.nx new_data.csv \
  --output predictions.csv \
  --show-top 20
```
**Outputs:**
- Predictions CSV file
- Confidence scores
- Model metadata

#### `nexora whatif`
Scenario analysis - what-if predictions.
```bash
nexora whatif session.nx scenarios.csv --sample-size 100
```
Tests multiple feature variations to understand prediction sensitivity.

---

### 4. Explainability & Interpretation

#### `nexora explain`
SHAP feature importance analysis.
```bash
nexora explain session.nx --top-features 15
```
**Outputs:**
- Feature importance scores
- Model decision drivers
- Impact on predictions

---

### 5. Advanced Analytics

#### `nexora cluster`
Unsupervised clustering exploration.
```bash
nexora cluster data.csv --n-clusters 5
```
**Outputs:**
- Cluster memberships
- Cluster profiles
- Silhouette score
- Inertia metric

#### `nexora forecast`
Time series forecasting (Prophet/ARIMA).
```bash
nexora forecast data.csv \
  --date-col date \
  --target-col revenue \
  --periods 24 \
  --freq M
```
**Options:**
- `--freq`: D (daily), W (weekly), M (monthly)
- `--periods`: Number of periods to forecast

**Outputs:**
- Forecast values
- MAE (Mean Absolute Error)
- R² Score

#### `nexora drift`
Feature drift detection on new data.
```bash
nexora drift session.nx production_data.csv --threshold 0.15
```
Alerts if production data deviates from training distribution.

---

### 6. Deployment & Export

#### `nexora serve`
Start a REST API server for predictions.
```bash
nexora serve session.nx --port 8000 --host 0.0.0.0
```
API Endpoints:
- `POST /predict` - Make predictions
- `GET /health` - Health check
- `GET /model-info` - Model metadata

#### `nexora report`
Generate HTML/PDF report.
```bash
nexora report session.nx --format pdf --out analysis_report.pdf

# or for HTML
nexora report session.nx --format html --out report.html
```

---

### 7. Session Management
Generate HTML/PDF report.
```bash
nexora report session.nx --format pdf --out analysis_report.pdf

# or for HTML
nexora report session.nx --format html --out report.html
```

---

### 7. Session Management

#### `nexora info`
Display session metadata.
```bash
nexora info session.nx --json
```
Shows:
- Source dataset name
- Target column
- Task type (classification/regression)
- Best model & score
- Number of models trained
- Feature list

#### `nexora history`
Show recent training sessions.
```bash
nexora history --limit 20
```

#### `nexora configuration`
Manage global settings.
```bash
nexora configuration --show
nexora configuration --set llm_provider ollama
nexora configuration --set llm_model phi-3
```

---

##  Workflow Examples

### Example 1: Complete Classification Pipeline
```bash
# 1. Profile the data
nexora profile customers.csv

# 2. Train models
nexora train customers.csv --target churn --max-models 8

# 3. Explain the best model
nexora explain customers.nx --top-features 15

# 4. Make predictions
nexora predict customers.nx new_customers.csv --output predictions.csv

# 5. Deploy as API
nexora serve customers.nx --port 5000
```

### Example 2: Quick Exploration
```bash
# Quick 30-second training
nexora quick data.csv --target target_col

# Check what models were trained
nexora compare data.nx --limit 5
```

### Example 3: Advanced Analysis
```bash
# Cluster customers
nexora cluster customers.csv --n-clusters 5

# Forecast revenue
nexora forecast sales.csv --date-col date --target-col revenue --periods 12

# What-if analysis
nexora whatif model.nx scenarios.csv

# Check for drift in production
nexora drift model.nx production_data.csv --threshold 0.1
```

---

##  CLI vs Web - Feature Parity Table

| Feature | CLI | Web | Notes |
|---------|-----|-----|-------|
| Interactive Wizard |  |  | Same 9-stage workflow |
| Fast Training |  |  | 30-second quick mode |
| Standard Training |  |  | Full hyperparameter control |
| Dataset Profiling |  |  | Health scores, distributions |
| Model Comparison |  |  | Side-by-side leaderboard |
| SHAP Explanations |  |  | Feature importance |
| Predictions |  |  | Batch or single |
| What-If Analysis |  |  | Scenario testing |
| Clustering |  |  | K-means, hierarchical |
| Forecasting |  |  | Time series prediction |
| Drift Detection |  |  | Production monitoring |
| Code Generation |  |  | FastAPI, Flask, Streamlit, Docker |
| PDF/HTML Reports |  |  | Full analysis export |
| API Deployment |  |  | REST server |
| Session History |  |  | Track past runs |
| Data Cleaning |  |  | Preprocessing only |

---

##  Configuration

Store settings in `~/.nexora/config.yml`:
```yaml
llm_provider: ollama
llm_model: phi-3
default_test_size: 0.2
default_cv_folds: 5
enable_drift_detection: true
```

---

##  Installation

```bash
pip install nexora-prediction

# Or from source
git clone https://github.com/jeet2005/nexora
cd nexora
pip install -e .
```

---

##  Key Features

 **No Web Browser Required** - Run everything from terminal  
 **Full Feature Parity** - Web and CLI support same workflows  
 **Production-Ready** - Generate deployable APIs and Docker containers  
 **Reproducible** - Save sessions and reload anytime  
 **Explainable** - SHAP, feature importance, decision trees  
 **Extensible** - Python library for custom workflows  

---

##  Help & Support

```bash
nexora --help
nexora <command> --help

# Examples
nexora train --help
nexora predict --help
```

---

##  Advanced Usage

### Python API (in scripts)
```python
from nexora import Nexora

# Load a saved session
report = Nexora.load("trained_model.nx")

# Make predictions
predictions = report.predict(new_df)

# Get explanations
explanation = report.explain()

# Generate code
fastapi_code = report.save_fastapi("api.py")
```

### Custom Preprocessing
```bash
nexora clean raw_data.csv \
  --target revenue \
  --out processed.csv

# Then train on cleaned data
nexora train processed.csv --target revenue
```

---

**Nexora v0.1.1 - Autonomous Predictive Analytics Platform**
