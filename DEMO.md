# 🚀 Nexora — Complete Usage Guide

> **Autonomous Predictive Analytics: From CSV to trained model in one line.**

[![PyPI](https://img.shields.io/pypi/v/nexora-prediction)](https://pypi.org/project/nexora-prediction/)
[![Python](https://img.shields.io/pypi/pyversions/nexora-prediction)](https://pypi.org/project/nexora-prediction/)
[![GitHub](https://img.shields.io/github/stars/jeet2005/Nexora)](https://github.com/jeet2005/Nexora)

---

## 📦 Installation

```bash
pip install nexora-prediction
```

After installing, you import the package as `nexora`:

```python
from nexora import Nexora
```

---

## 🖥️ Local Usage (PowerShell / CMD / Terminal)

### Quick Start Script

Create a file called `train.py`:

```python
from nexora import Nexora

# Load data and train
report = Nexora("sales_data.csv", target="revenue").run()

# View results
print(f"🏅 Best Model: {report.best_model}")
print(f"📊 Score ({report.best_score_label}): {report.best_score:.4f}")
print(report.leaderboard)

# Make predictions
import pandas as pd
new_data = pd.read_csv("new_customers.csv")
predictions = report.predict(new_data)
print(predictions)

# Save model
report.save("my_model.nx")
```

Run it:

```powershell
python train.py
```

**Expected Output:**

```
🏅 Best Model: XGBRegressor
📊 Score (r2): 0.9234

  rank        model_id          model_name        family    status  primary_metric  primary_score  train_time_sec  speed
     1  xgb_regressor       XGBRegressor       xgboost  completed              r2         0.9234           1.245   fast
     2  lgbm_regressor      LGBMRegressor      lightgbm  completed              r2         0.9102           0.892   fast
     3  rf_regressor  RandomForestRegressor  sklearn  completed              r2         0.8871           0.567   fast
     4  linear         LinearRegression       sklearn  completed              r2         0.7543           0.034   fast

   revenue_predicted  confidence       model_used
0          345000.50        None   XGBRegressor
1          128000.75        None   XGBRegressor
2          560000.00        None   XGBRegressor
```

---

### 📁 Loading Data — All Supported Sources

```python
from nexora import Nexora

# 1. From CSV file
nx = Nexora("data.csv", target="price")

# 2. From pandas DataFrame
import pandas as pd
df = pd.read_csv("data.csv")
nx = Nexora(df, target="price")

# 3. From Excel file
nx = Nexora("data.xlsx", target="price")

# 4. From Parquet file
nx = Nexora("data.parquet", target="price")

# 5. From a URL
nx = Nexora.from_url("https://example.com/data.csv", target="price")

# 6. From sklearn built-in datasets
nx = Nexora.from_sklearn("california_housing", target="MedHouseVal")
nx = Nexora.from_sklearn("iris", target="target")
nx = Nexora.from_sklearn("wine", target="target")
nx = Nexora.from_sklearn("diabetes", target="target")
nx = Nexora.from_sklearn("breast_cancer", target="target")

# 7. From SQL database
nx = Nexora.from_sql("SELECT * FROM sales", "sqlite:///mydb.sqlite", target="revenue")

# 8. From PostgreSQL
nx = Nexora.from_postgres("postgresql://user:pass@host/db", "sales_table", target="revenue")

# 9. From MongoDB
nx = Nexora.from_mongodb("mongodb://localhost:27017", "sales_collection", target="revenue")

# 10. From S3
nx = Nexora.from_s3("my-bucket", "data/sales.csv", target="revenue")

# 11. From Google Sheets
nx = Nexora.from_google_sheets("1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgVE2upms", target="revenue")

# 12. From clipboard
nx = Nexora.from_clipboard(target="revenue")
```

---

### 🔍 Step-by-Step Walkthrough

#### Step 1: Profile Your Dataset

```python
from nexora import Nexora

nx = Nexora("house_prices.csv", target="SalePrice")
profile = nx.profile()

print(f"📊 Dataset: {profile.source_name}")
print(f"📏 Shape:   {profile.num_rows:,} rows × {profile.num_columns} columns")
print(f"🎯 Target:  {profile.target}")
print(f"📈 Task:    {profile.task_type}")
print(f"💚 Health:  {profile.health_score:.1f}/100")
print(f"🔢 Numeric:     {profile.num_numeric} features")
print(f"🏷️  Categorical: {profile.num_categorical} features")
print(f"❓ Missing:     {profile.total_missing} cells")
```

**Expected Output:**

```
📊 Dataset: house_prices.csv
📏 Shape:   1,460 rows × 81 columns
🎯 Target:  SalePrice
📈 Task:    regression
💚 Health:  78.5/100
🔢 Numeric:     36 features
🏷️  Categorical: 43 features
❓ Missing:     6,965 cells
```

#### Step 2: Train Models

```python
# Full training (trains up to 6 models)
report = nx.run()

# Quick mode (top 2 models only, ~30 seconds)
report = nx.quick()

# Custom training
report = nx.run(
    max_models=3,                           # Limit number of models
    model_names=["XGBRegressor", "LGBMRegressor"],  # Specific models
    test_size=0.25,                          # Custom split
    random_state=123,                        # Reproducibility
)
```

#### Step 3: View Leaderboard

```python
# Pandas DataFrame with all results
print(report.leaderboard)

# Best model info
print(f"🏅 Best: {report.best_model}")
print(f"📊 Score: {report.best_score:.4f}")
print(f"📏 Metric: {report.best_score_label}")
```

#### Step 4: Make Predictions

```python
import pandas as pd

# Load new data (must have same feature columns, no target)
new_data = pd.read_csv("new_houses.csv")
predictions = report.predict(new_data)

print(predictions)
# Output:
#    SalePrice_predicted  confidence       model_used
# 0           215000.50        None    XGBRegressor
# 1           189500.25        None    XGBRegressor
# 2           342000.00        None    XGBRegressor
```

#### Step 5: Save & Load

```python
# Save everything (model + metadata + profiling)
report.save("house_model.nx")

# Load it back anytime
from nexora import Nexora
loaded = Nexora.load("house_model.nx")
predictions = loaded.predict(new_data)
```

---

### 🧠 Explainability & Diagnostics

```python
# Feature importance (SHAP-based)
importance = report.explain()
print(importance)
#        feature  importance
# 0  OverallQual    0.3421
# 1    GrLivArea    0.1832
# 2   GarageCars    0.0921
# 3   TotalBsmtSF   0.0854

# Feature importance with plot
report.explain(plot=True)

# Natural language explanation (requires OpenAI or Ollama)
explanation = report.explain(in_words=True)
print(explanation)

# Ask questions about your model
answer = report.ask("Why is OverallQual the most important feature?")
print(answer)

# What-if analysis
result = report.what_if(
    feature="GarageCars",
    value=3,
    row_data={"OverallQual": 7, "GrLivArea": 1500, "GarageCars": 1, ...}
)
print(result)

# Partial dependence
pd_result = report.partial_dependence("GrLivArea")

# Sensitivity analysis
sens = report.sensitivity("OverallQual")
print(sens)
```

---

### 📊 Diagnostics & Monitoring

```python
# Regression diagnostics
report.residuals()            # Residual plot
report.learning_curve()       # Bias-variance curve
report.error_analysis()       # High-error segments

# Classification diagnostics
report.confusion_matrix()     # Confusion matrix + report
report.roc_curve()            # ROC curve
report.pr_curve()             # Precision-Recall curve
report.calibration_curve()    # Probability calibration

# Data drift detection
new_batch = pd.read_csv("new_batch.csv")
drift_report = report.drift(new_batch)
monitoring = report.monitor(new_batch)

# Retrain on new data
new_report = report.retrain(new_batch)
```

---

### 🚀 Code Generation & Deployment

Nexora auto-generates production-ready deployment code:

```python
# Generate standalone Python script
print(report.code)
report.save_code("model_script.py")

# Generate FastAPI REST API
report.save_fastapi("api.py")
# Run: uvicorn api:app --reload

# Generate Flask web server
report.save_flask("server.py")
# Run: python server.py

# Generate Streamlit dashboard
report.save_streamlit("dashboard.py")
# Run: streamlit run dashboard.py

# Generate Jupyter notebook
report.save_notebook("analysis.ipynb")

# Generate Docker deployment
report.save_docker("Dockerfile", "requirements.txt")
# Run: docker build -t nexora-model . && docker run -p 8000:8000 nexora-model

# Generate MLflow tracking script
report.save_mlflow("mlflow_train.py")

# Generate sklearn Pipeline code
report.save_pipeline("pipeline.py")

# Publish to Hugging Face Hub
url = report.publish("your-username/house-price-model")
print(f"Published at: {url}")
```

---

### 🔧 CLI (Command Line Interface)

```powershell
# Profile a dataset
nexora profile data.csv --target price

# Train models
nexora run data.csv --target price --max-models 4

# Quick training
nexora quick data.csv --target price

# Generate code
nexora codegen session.nx --format fastapi --output api.py
```

---

## 📓 Jupyter Notebook Usage

### Cell 1: Install

```python
!pip install nexora-prediction -q
```

### Cell 2: Import & Load

```python
from nexora import Nexora
import pandas as pd

# Load from sklearn (no file needed!)
nx = Nexora.from_sklearn("california_housing", target="MedHouseVal")
print(nx)
```

### Cell 3: Profile

```python
profile = nx.profile()

print(f"📊 Dataset: {profile.source_name}")
print(f"📏 Shape: {profile.num_rows:,} rows × {profile.num_columns} cols")
print(f"🎯 Target: {profile.target}")
print(f"📈 Task: {profile.task_type}")
print(f"💚 Health: {profile.health_score:.1f}/100")
print(f"🔢 Numeric: {profile.num_numeric}")
print(f"🏷️ Categorical: {profile.num_categorical}")
print(f"❓ Missing: {profile.total_missing}")
```

### Cell 4: Train Models

```python
report = nx.run()
```

### Cell 5: Leaderboard

```python
report.leaderboard
```

### Cell 6: Best Model Summary

```python
print(f"🏅 Best Model: {report.best_model}")
print(f"📊 {report.best_score_label}: {report.best_score:.4f}")
```

### Cell 7: Feature Importance (with plot)

```python
report.explain(plot=True)
```

### Cell 8: Predictions

```python
# Use first 10 rows as new data
sample = nx.df.drop(columns=["MedHouseVal"]).head(10)
preds = report.predict(sample)

# Compare predictions vs actuals
comparison = pd.DataFrame({
    "Actual": nx.df["MedHouseVal"].head(10).values,
    "Predicted": preds["MedHouseVal_predicted"].values,
})
comparison["Error"] = abs(comparison["Actual"] - comparison["Predicted"])
comparison
```

### Cell 9: Diagnostics

```python
# Residual plot (regression)
report.residuals()
```

```python
# Learning curve
report.learning_curve()
```

### Cell 10: Save Model

```python
report.save("california_model.nx")
print("✅ Saved!")

# Load back
loaded = Nexora.load("california_model.nx")
print(f"✅ Loaded: {loaded.best_model}")
```

### Cell 11: Generate API Code

```python
# Print FastAPI code
print(report.code_fastapi())
```

### Cell 12: Classification Example

```python
# Auto-detects classification!
nx_iris = Nexora.from_sklearn("iris", target="target")
report_iris = nx_iris.run()

print(f"🎯 Task: {report_iris.task_type}")
report_iris.leaderboard
```

```python
# Classification diagnostics
report_iris.confusion_matrix()
```

```python
report_iris.roc_curve()
```

---

## 📋 Complete API Reference

### `Nexora` — Entry Point

| Method | Description |
|--------|-------------|
| `Nexora(data, target)` | Create session from CSV, DataFrame, or array |
| `Nexora.from_url(url, target)` | Load from URL |
| `Nexora.from_sklearn(name, target)` | Load sklearn dataset |
| `Nexora.from_sql(query, conn, target)` | Load from SQL |
| `Nexora.from_postgres(uri, table, target)` | Load from PostgreSQL |
| `Nexora.from_mongodb(uri, collection, target)` | Load from MongoDB |
| `Nexora.from_s3(bucket, key, target)` | Load from AWS S3 |
| `Nexora.from_google_sheets(id, target)` | Load from Google Sheets |
| `Nexora.from_clipboard(target)` | Load from clipboard |
| `Nexora.load(path)` | Load a saved `.nx` session |
| `nx.profile()` | Dataset health check |
| `nx.run()` | Train all models |
| `nx.quick()` | Fast 30s training |

### `NexoraReport` — Results

| Property/Method | Description |
|----------------|-------------|
| `report.leaderboard` | Model rankings (DataFrame) |
| `report.best_model` | Best model name |
| `report.best_score` | Best model score |
| `report.best_score_label` | Metric name (r2, accuracy, etc.) |
| `report.predict(df)` | Make predictions |
| `report.explain()` | Feature importance |
| `report.explain(plot=True)` | Feature importance with chart |
| `report.explain(in_words=True)` | Natural language explanation |
| `report.ask(question)` | Ask about your model |
| `report.what_if(feat, val, row)` | What-if analysis |
| `report.partial_dependence(feat)` | Partial dependence |
| `report.sensitivity(feat)` | Sensitivity analysis |
| `report.save(path)` | Save session |
| `report.code` | Generated Python script |
| `report.code_fastapi()` | FastAPI server code |
| `report.code_flask()` | Flask server code |
| `report.code_streamlit()` | Streamlit dashboard |
| `report.code_docker()` | Docker deployment files |
| `report.code_notebook()` | Jupyter notebook |
| `report.code_mlflow()` | MLflow tracking script |
| `report.code_pipeline()` | sklearn Pipeline code |
| `report.residuals()` | Residual plot (regression) |
| `report.confusion_matrix()` | Confusion matrix (classification) |
| `report.roc_curve()` | ROC curve (classification) |
| `report.pr_curve()` | PR curve (classification) |
| `report.learning_curve()` | Bias-variance plot |
| `report.calibration_curve()` | Calibration plot |
| `report.error_analysis()` | High-error segments |
| `report.drift(new_df)` | Data drift detection |
| `report.monitor(new_df)` | Monitoring report |
| `report.retrain(new_df)` | Retrain on new data |
| `report.publish(repo_id)` | Publish to Hugging Face |

---

## 🧪 Supported Models

### Regression
- LinearRegression
- RandomForestRegressor
- XGBRegressor
- LGBMRegressor
- CatBoostRegressor
- GradientBoostingRegressor

### Classification
- LogisticRegression
- RandomForestClassifier
- XGBClassifier
- LGBMClassifier
- CatBoostClassifier
- GradientBoostingClassifier

---

## 📬 Links

- **PyPI:** [pypi.org/project/nexora-prediction](https://pypi.org/project/nexora-prediction/)
- **GitHub:** [github.com/jeet2005/Nexora](https://github.com/jeet2005/Nexora)
- **Issues:** [github.com/jeet2005/Nexora/issues](https://github.com/jeet2005/Nexora/issues)

---

*Built with ❤️ by Jeet Patel*
