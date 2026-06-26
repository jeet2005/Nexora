# Nexora Quick Start Guide

## Installation

```bash
pip install nexora-prediction
```

---

## 5-Minute Quick Start

### Option 1: Interactive Wizard (Recommended)
```bash
nexora
```
This launches a beautiful interactive wizard that walks you through:
- Data upload & profiling
- Target selection
- Preprocessing settings
- Model training with live leaderboard
- Predictions
- Explanations
- Export options

### Option 2: Quick Terminal Commands

#### 1. Profile your dataset
```bash
nexora profile sales.csv
```
Output:
- Health score (0-100)
- Missing values
- Data types
- Suggested targets

#### 2. Train models (30 seconds)
```bash
nexora quick sales.csv --target revenue
```

#### 3. Train models (full control)
```bash
nexora train sales.csv \
  --target revenue \
  --max-models 8 \
  --test-size 0.2 \
  --seed 42 \
  --out sales_model.nx
```

#### 4. Make predictions
```bash
nexora predict sales_model.nx new_customers.csv \
  --output predictions.csv
```

#### 5. Explain the model
```bash
nexora explain sales_model.nx --top-features 10
```

#### 6. Deploy as API
```bash
nexora serve sales_model.nx --port 5000
```
Then access API at: `http://localhost:5000/docs`

---

## What Each Command Does

| Command | Purpose | Use When |
|---------|---------|----------|
| `nexora` | Interactive wizard | You want guided experience |
| `nexora train` | Full training control | You know exact parameters |
| `nexora quick` | Fast training (2 models) | You want results in 30 seconds |
| `nexora profile` | Analyze dataset | You need dataset insights |
| `nexora predict` | Batch predictions | You have new data |
| `nexora explain` | Feature importance | You want model interpretability |
| `nexora cluster` | Unsupervised clustering | You want to segment data |
| `nexora forecast` | Time series prediction | You have time-series data |
| `nexora serve` | Start prediction API | You want REST endpoint |
| `nexora serve` | Start API | You want REST endpoint |

---

## Complete Workflow Example

### Scenario: Predict customer churn

```bash
# Step 1: Explore the data
nexora profile customers.csv

# Step 2: Train models (will save to customers.nx)
nexora train customers.csv \
  --target churn \
  --max-models 6 \
  --out churn_model.nx

# Step 3: Understand what drives predictions
nexora explain churn_model.nx --top-features 15

# Step 4: Segment customers
nexora cluster customers.csv --n-clusters 4

# Step 5: Make predictions on new data
nexora predict churn_model.nx new_customers.csv \
  --output churn_predictions.csv

# Step 6: Deploy as REST API
nexora serve churn_model.nx --port 8000

# Step 7: Deploy production REST API
nexora serve churn_model.nx --port 8000
```

---

## Python API Usage

### Basic Training
```python
from nexora import Nexora

# Create session
nx = Nexora("data.csv", target="sales")

# Train models
report = nx.run(max_models=6)

# View results
print(f"Best model: {report.best_model}")
print(f"Score: {report.best_score:.4f}")
print(report.leaderboard)
```

### Make Predictions
```python
import pandas as pd

# Load saved model
report = Nexora.load("model.nx")

# Make predictions
new_data = pd.read_csv("new_data.csv")
predictions = report.predict(new_data)

# Save results
predictions.to_csv("predictions.csv", index=False)
```

### Generate Deployment Code
```python
# FastAPI
report.save_fastapi("api.py")

# Flask
report.save_flask("app.py")

# Streamlit
report.save_streamlit("dashboard.py")

# Docker
report.save_docker("Dockerfile", "requirements.txt")

# Jupyter
report.save_notebook("explore.ipynb")
```

---

## Common Use Cases

### 1. Quick Experiment
```bash
# 30-second training
nexora quick data.csv --target target_col
```

### 2. Production Model
```bash
# Full training, best model
nexora train data.csv \
  --target target_col \
  --max-models 20 \
  --cv-folds 10 \
  --seed 42 \
  --out production_model.nx

# Deploy as API
nexora serve production_model.nx
```

### 3. Data Cleaning Only
```bash
# Preprocess without training
nexora clean raw_data.csv --target col --out clean_data.csv
```

### 4. Model Explanation
```bash
# Understand predictions
nexora explain model.nx --top-features 20
```

### 5. What-If Analysis
```bash
# Test scenarios
nexora whatif model.nx scenarios.csv
```

### 6. Generate Reports
```bash
# HTML report
nexora report model.nx --format html --out report.html

# PDF report
nexora report model.nx --format pdf --out report.pdf
```

---

## Supported Data Formats

 CSV  
 Excel (XLSX, XLS)  
 Parquet  
 JSON / JSONL  
 TSV  
 SQL Database  
 MongoDB  
 AWS S3  
 Google Sheets  
 scikit-learn datasets  
 Clipboard data  
 HDF5, ORC, Feather  
 100+ more formats via pandas

```python
# Load from various sources
nx = Nexora("data.csv")
nx = Nexora.from_sql("SELECT * FROM table", "connection_string")
nx = Nexora.from_s3("bucket", "key")
nx = Nexora.from_google_sheets("sheet_id")
nx = Nexora.from_clipboard()  # Paste from spreadsheet
```

---

## Output Formats

Save trained models in multiple formats:

```bash
# Nexora format (recommended - portable)
nexora train data.csv --target y --out model.nx

# Joblib (Python scikit-learn)
report.save_model("model.joblib")

# Pickle
report.save_model("model.pkl")

# FastAPI application
report.save_fastapi("api.py")

# Docker container
report.save_docker("Dockerfile")

# Jupyter notebook
report.save_notebook("explore.ipynb")

# PDF report
report.to_pdf("report.pdf")

# HTML report
report.to_html("report.html")

# Standalone Python script
report.save_code("standalone.py")
```

---

## Getting Help

### See all commands
```bash
nexora --help
```

### Get help for a specific command
```bash
nexora train --help
nexora predict --help
``` 

### See wizard stages
```bash
nexora wizard
# Walks through all 9 stages
```

---

## Performance Tips

### For Large Datasets (>100k rows)
```bash
nexora quick data.csv --target y
# Use 2-model quick mode instead of full training
```

### For Speed
```bash
nexora train data.csv --target y --max-models 3 --timeout 30
# Limit models and timeout
```

### For Accuracy
```bash
nexora train data.csv --target y --max-models 20 --cv-folds 10
# More models and CV folds (slower but more accurate)
```

---

## Troubleshooting

### "Column not found" error
Make sure column name exactly matches your CSV header (case-sensitive)

### Training takes too long
Use `--timeout 60` to limit per-model time:
```bash
nexora train data.csv --target y --timeout 60
```

### Memory issues with large files
Use quick mode or filter rows:
```bash
# Take first 100k rows
pandas -c "import pandas as pd; df = pd.read_csv('data.csv'); df.head(100000).to_csv('small.csv')"
nexora train small.csv --target y
```

### Missing values in predictions
Ensure new data has same columns as training data (in any order)

---

## Next Steps

1.  Install: `pip install nexora-prediction`
2.  Run wizard: `nexora`
3.  Check out examples: Browse [examples/](../examples/)
4.  Read full CLI guide: [CLI_FEATURES.md](CLI_FEATURES.md)
5.  Try Python API: See docs at [nexora-360r.onrender.com/docs](https://nexora-360r.onrender.com/docs)

---

## Resources

-  [Full CLI Reference](CLI_FEATURES.md)
-  [Completion Status](COMPLETION_STATUS.md)
-  [Web App](https://nexoraprediction.netlify.app/)
-  [API Docs](https://nexora-360r.onrender.com/docs)
-  [GitHub Discussions](https://github.com/jeet2005/Nexora/discussions)

---

**Nexora v0.1.1** - Autonomous Predictive Analytics Platform
