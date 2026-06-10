"""NexoraReport public output object."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from nexora.codegen.docker_gen import generate_docker
from nexora.codegen.fastapi_gen import generate_fastapi
from nexora.codegen.flask_gen import generate_flask
from nexora.codegen.mlflow_gen import generate_mlflow
from nexora.codegen.notebook_gen import generate_notebook
from nexora.codegen.pipeline_gen import generate_pipeline
from nexora.codegen.script import generate_script
from nexora.codegen.streamlit_gen import generate_streamlit
from nexora.explainer.llm_explainer import ask_question, generate_explanation, what_if
from nexora.explainer.pdp import get_partial_dependence
from nexora.explainer.sensitivity import sensitivity
from nexora.explainer.shap_explainer import explain_report
from nexora.io.serializer import save_report
from nexora.types import (
    DatasetProfile,
    ModelResult,
    ModelSpec,
    PreprocessingSchema,
    TaskType,
)


@dataclass
class NexoraReport:
    """Trained Nexora report with leaderboard, prediction, codegen, and save APIs.

    Args:
        source_name: Original dataset filename.
        target: Target column name.
        task_type: Detected supervised task type.

    Returns:
        A report object returned by `Nexora.run()`.

    Example:
        `report.best_model`
    """

    source_name: str
    source_path: str | None
    target: str
    task_type: TaskType
    profile: DatasetProfile
    schema: PreprocessingSchema
    pipeline: Any = field(repr=False)
    training_frame: pd.DataFrame = field(repr=False)
    results: list[ModelResult] = field(default_factory=list)
    best_result: ModelResult | None = None
    model_specs: dict[str, ModelSpec] = field(default_factory=dict)
    version: str = "0.1.0"

    @property
    def leaderboard(self) -> pd.DataFrame:
        """Ranked model leaderboard as a pandas DataFrame."""

        rows: list[dict[str, Any]] = []
        completed_rank = 0
        for result in self.results:
            row = {
                "rank": None,
                "model_id": result.model_id,
                "model_name": result.model_name,
                "family": result.family,
                "status": result.status,
                "primary_metric": result.primary_metric,
                "primary_score": (
                    np.nan
                    if not np.isfinite(result.primary_score)
                    else result.primary_score
                ),
                "train_time_sec": result.train_time_sec,
                "speed": result.speed,
                "error": result.error,
            }
            row.update(result.metrics)
            if result.status == "completed":
                completed_rank += 1
                row["rank"] = completed_rank
            rows.append(row)
        return pd.DataFrame(rows)

    @property
    def best_model(self) -> str:
        """Winning model name."""

        return self._require_best().model_name

    @property
    def best_score(self) -> float:
        """Winning model primary metric value."""

        return self._require_best().primary_score

    @property
    def best_score_label(self) -> str:
        """Winning model primary metric label."""

        return self._require_best().primary_metric

    @property
    def code(self) -> str:
        """Standalone Python code for the best model."""

        return generate_script(self)

    def predict(self, new_df: pd.DataFrame) -> pd.DataFrame:
        """Predict with the best fitted pipeline.

        Args:
            new_df: DataFrame containing the original feature columns.

        Returns:
            DataFrame with prediction, confidence, and model metadata.

        Example:
            `predictions = report.predict(customers)`
        """

        if not isinstance(new_df, pd.DataFrame):
            raise TypeError("report.predict expects a pandas DataFrame.")

        missing = [col for col in self.schema.feature_columns if col not in new_df.columns]
        if missing:
            raise ValueError(f"Missing required feature columns: {', '.join(missing)}")

        X = new_df[self.schema.feature_columns]
        pred = self.pipeline.predict(X)
        output = pd.DataFrame({f"{self.target}_predicted": pred})
        output["confidence"] = self._confidence(X)
        output["model_used"] = self.best_model
        return output

    def code_for(self, model_name: str) -> str:
        """Generate standalone Python for any completed leaderboard model.

        Args:
            model_name: Model id, model name, or estimator class name.

        Returns:
            Standalone Python script text.

        Example:
            `report.code_for("RandomForestRegressor")`
        """

        return generate_script(self, model_name)

    def save_code(self, path: str | Path, model: str | None = None) -> Path:
        """Write generated standalone Python to disk.

        Args:
            path: Destination `.py` file.
            model: Optional model name for `code_for`; defaults to best model.

        Returns:
            Resolved path written to disk.

        Example:
            `report.save_code("model.py")`
        """

        output = Path(path).expanduser().resolve()
        output.parent.mkdir(parents=True, exist_ok=True)
        code = self.code if model is None else self.code_for(model)
        output.write_text(code, encoding="utf-8")
        return output

    def code_fastapi(self, model_name: str | None = None) -> str:
        """Generate FastAPI application code for model serving.

        Args:
            model_name: Optional model id, name, or class name. Defaults to best.

        Returns:
            Complete FastAPI application code (standalone, ready to run).

        Example:
            `code = report.code_fastapi()` → Runnable with `uvicorn app:app`
        """

        return generate_fastapi(self, model_name)

    def save_fastapi(self, path: str | Path, model: str | None = None) -> Path:
        """Write FastAPI application to disk.

        Args:
            path: Destination `.py` file (typically `app.py`).
            model: Optional model name; defaults to best model.

        Returns:
            Resolved path written to disk.

        Example:
            `report.save_fastapi("app.py")`
        """

        output = Path(path).expanduser().resolve()
        output.parent.mkdir(parents=True, exist_ok=True)
        code = self.code_fastapi(model_name=model)
        output.write_text(code, encoding="utf-8")
        return output

    def code_streamlit(self, model_name: str | None = None) -> str:
        """Generate Streamlit interactive dashboard for model prediction.

        Args:
            model_name: Optional model id, name, or class name. Defaults to best.

        Returns:
            Complete Streamlit application code (standalone, ready to run).

        Example:
            `code = report.code_streamlit()` → Run with `streamlit run app.py`
        """

        return generate_streamlit(self, model_name)

    def save_streamlit(self, path: str | Path, model: str | None = None) -> Path:
        """Write Streamlit dashboard to disk.

        Args:
            path: Destination `.py` file (typically `app.py`).
            model: Optional model name; defaults to best model.

        Returns:
            Resolved path written to disk.

        Example:
            `report.save_streamlit("dashboard.py")`
        """

        output = Path(path).expanduser().resolve()
        output.parent.mkdir(parents=True, exist_ok=True)
        code = self.code_streamlit(model_name=model)
        output.write_text(code, encoding="utf-8")
        return output

    def code_flask(self, model_name: str | None = None) -> str:
        """Generate Flask web server code for model serving.

        Args:
            model_name: Optional model id, name, or class name. Defaults to best.

        Returns:
            Complete Flask application code (standalone, ready to run).

        Example:
            `code = report.code_flask()` → Run with `flask run` or `python app.py`
        """

        return generate_flask(self, model_name)

    def save_flask(self, path: str | Path, model: str | None = None) -> Path:
        """Write Flask application to disk.

        Args:
            path: Destination `.py` file (typically `app.py`).
            model: Optional model name; defaults to best model.

        Returns:
            Resolved path written to disk.

        Example:
            `report.save_flask("app.py")`
        """

        output = Path(path).expanduser().resolve()
        output.parent.mkdir(parents=True, exist_ok=True)
        code = self.code_flask(model_name=model)
        output.write_text(code, encoding="utf-8")
        return output

    def code_docker(self, model_name: str | None = None) -> tuple[str, str]:
        """Generate Docker deployment files.

        Args:
            model_name: Optional model id, name, or class name. Defaults to best.

        Returns:
            Tuple of (dockerfile_content, requirements_content).

        Example:
            `docker, reqs = report.code_docker()`
        """

        return generate_docker(self, model_name)

    def save_docker(
        self, dockerfile_path: str | Path, requirements_path: str | Path, model: str | None = None
    ) -> tuple[Path, Path]:
        """Write Docker deployment files to disk.

        Args:
            dockerfile_path: Destination for Dockerfile.
            requirements_path: Destination for requirements.txt.
            model: Optional model name; defaults to best model.

        Returns:
            Tuple of (dockerfile_path, requirements_path) written to disk.

        Example:
            `docker_path, req_path = report.save_docker("Dockerfile", "requirements.txt")`
        """

        docker_code, req_code = self.code_docker(model_name=model)

        docker_path = Path(dockerfile_path).expanduser().resolve()
        docker_path.parent.mkdir(parents=True, exist_ok=True)
        docker_path.write_text(docker_code, encoding="utf-8")

        req_path = Path(requirements_path).expanduser().resolve()
        req_path.parent.mkdir(parents=True, exist_ok=True)
        req_path.write_text(req_code, encoding="utf-8")

        return docker_path, req_path

    def code_notebook(self, model_name: str | None = None) -> str:
        """Generate Jupyter notebook (.ipynb) for model training and prediction.

        Args:
            model_name: Optional model id, name, or class name. Defaults to best.

        Returns:
            JSON string for .ipynb file (Jupyter notebook format).

        Example:
            `nb_json = report.code_notebook()` → Run with Jupyter
        """

        return generate_notebook(self, model_name)

    def save_notebook(self, path: str | Path, model: str | None = None) -> Path:
        """Write Jupyter notebook to disk.

        Args:
            path: Destination `.ipynb` file (typically `notebook.ipynb`).
            model: Optional model name; defaults to best model.

        Returns:
            Resolved path written to disk.

        Example:
            `report.save_notebook("model_notebook.ipynb")`
        """

        output = Path(path).expanduser().resolve()
        output.parent.mkdir(parents=True, exist_ok=True)
        code = self.code_notebook(model_name=model)
        output.write_text(code, encoding="utf-8")
        return output

    def code_mlflow(self, model_name: str | None = None) -> str:
        """Generate MLflow experiment tracking code.

        Args:
            model_name: Optional model id, name, or class name. Defaults to best.

        Returns:
            Python script with MLflow tracking integration.

        Example:
            `code = report.code_mlflow()` → Logs experiments to MLflow UI
        """

        return generate_mlflow(self, model_name)

    def save_mlflow(self, path: str | Path, model: str | None = None) -> Path:
        """Write MLflow tracking script to disk.

        Args:
            path: Destination `.py` file.
            model: Optional model name; defaults to best model.

        Returns:
            Resolved path written to disk.

        Example:
            `report.save_mlflow("train.py")`
        """

        output = Path(path).expanduser().resolve()
        output.parent.mkdir(parents=True, exist_ok=True)
        code = self.code_mlflow(model_name=model)
        output.write_text(code, encoding="utf-8")
        return output

    def code_pipeline(self, model_name: str | None = None) -> str:
        """Generate sklearn Pipeline code for model reuse.

        Args:
            model_name: Optional model id, name, or class name. Defaults to best.

        Returns:
            Python script to recreate the sklearn Pipeline programmatically.

        Example:
            `code = report.code_pipeline()` → Can fit/predict with new data
        """

        return generate_pipeline(self, model_name)

    def save_pipeline(self, path: str | Path, model: str | None = None) -> Path:
        """Write sklearn Pipeline code to disk.

        Args:
            path: Destination `.py` file.
            model: Optional model name; defaults to best model.

        Returns:
            Resolved path written to disk.

        Example:
            `report.save_pipeline("pipeline.py")`
        """

        output = Path(path).expanduser().resolve()
        output.parent.mkdir(parents=True, exist_ok=True)
        code = self.code_pipeline(model_name=model)
        output.write_text(code, encoding="utf-8")
        return output

    def explain(self, *, plot: bool = False, in_words: bool = False) -> pd.DataFrame | str:
        """Return ranked feature importance for the best model.

        Args:
            plot: When True, render a matplotlib bar chart.
            in_words: When True, return a natural language explanation from LLM.

        Returns:
            DataFrame with feature importance values, or natural language string.

        Example:
            `report.explain()`
        """

        df = explain_report(self, plot=plot)
        if in_words:
            context = {
                "model_type": self.best_model,
                "metric_name": self.best_score_label,
                "metric_value": self.best_score,
                "task_type": self.task_type,
                "n_rows": len(self.training_frame),
                "n_features": len(self.schema.feature_columns),
                "target_col": self.target,
                "top_features": df.head(5).to_dict(orient="records") if not df.empty else [],
                "data_profile": {
                    "health_score": self.profile.health_score,
                    "missing_count": sum(c.missing_count for c in self.profile.columns.values()),
                }
            }
            fallback = "Model feature importance:\n" + df.head(5).to_string()
            return generate_explanation(context, fallback)
        return df

    def ask(self, question: str) -> str:
        """Ask a free-form question grounded in model stats and data profile."""
        df = explain_report(self, plot=False)
        context = {
            "model_type": self.best_model,
            "metric_name": self.best_score_label,
            "metric_value": self.best_score,
            "task_type": self.task_type,
            "n_rows": len(self.training_frame),
            "n_features": len(self.schema.feature_columns),
            "target_col": self.target,
            "top_features": df.head(5).to_dict(orient="records") if not df.empty else [],
            "data_profile": {
                "health_score": self.profile.health_score,
                "missing_count": sum(c.missing_count for c in self.profile.columns.values()),
            }
        }
        return ask_question(context, question)

    def what_if(self, feature: str, value: Any, row_data: dict[str, Any]) -> str:
        """Predict the impact of changing one feature value and explain it."""
        row_df = pd.DataFrame([row_data])
        row_df_changed = row_df.copy()
        row_df_changed[feature] = value
        
        # Predict original and changed
        new_pred = self.predict(row_df_changed).iloc[0, 0]
        
        context = {
            "model_type": self.best_model,
            "metric_name": self.best_score_label,
            "metric_value": self.best_score,
            "task_type": self.task_type,
            "target_col": self.target,
        }
        return what_if(context, feature, value, row_data, new_pred)

    def partial_dependence(self, feature: str) -> dict[str, list[float]]:
        """Calculate partial dependence for a feature."""
        return get_partial_dependence(self.pipeline, self.training_frame, feature)

    def sensitivity(self, feature: str, stdev_multiplier: float = 1.0) -> dict[str, float]:
        """Calculate sensitivity of predictions to a feature."""
        return sensitivity(self.pipeline, self.training_frame, feature, stdev_multiplier)

    def save(self, path: str | Path) -> Path:
        """Save this report as a `.nx` session.

        Args:
            path: Destination session file.

        Returns:
            Resolved session path.

        Example:
            `report.save("session.nx")`
        """

        return save_report(self, path)

    def get_model_result(self, name: str) -> ModelResult:
        """Return a completed leaderboard result by id, name, or class name."""

        spec = self.get_model_spec(name)
        for result in self.results:
            if result.model_id == spec.model_id and result.status == "completed":
                return result
        raise ValueError(f"Model is not completed in this report: {name}")

    def get_model_spec(self, name: str) -> ModelSpec:
        """Return a model spec by id, name, or class name."""

        for spec in self.model_specs.values():
            if spec.matches(name):
                return spec
        known = ", ".join(spec.model_name for spec in self.model_specs.values())
        raise ValueError(f"Unknown model '{name}'. Known models: {known}")

    def _require_best(self) -> ModelResult:
        if self.best_result is None:
            raise RuntimeError("This report has no trained best model.")
        return self.best_result

    def _confidence(self, X: pd.DataFrame) -> list[float | None]:
        model = self.pipeline.named_steps["model"]
        if self.task_type != "classification" or not hasattr(model, "predict_proba"):
            return [None for _ in range(len(X))]
        try:
            proba = self.pipeline.predict_proba(X)
        except Exception:
            return [None for _ in range(len(X))]
        return [round(float(value), 4) for value in np.max(proba, axis=1)]

    # --- Diagnostics & Monitoring (Phase 5) ---
    
    def residuals(self) -> Any:
        """Plot residuals for regression models."""
        from nexora.monitor.diagnostics import plot_residuals
        if self.task_type != "regression":
            raise ValueError("Residuals plot is only available for regression tasks.")
        y_true = self.training_frame[self.target]
        y_pred = self.pipeline.predict(self.training_frame.drop(columns=[self.target]))
        return plot_residuals(y_true, y_pred)
        
    def confusion_matrix(self) -> Any:
        """Plot confusion matrix and print classification report."""
        from nexora.monitor.diagnostics import plot_confusion_matrix
        if self.task_type != "classification":
            raise ValueError("Confusion matrix is only available for classification tasks.")
        y_true = self.training_frame[self.target]
        y_pred = self.pipeline.predict(self.training_frame.drop(columns=[self.target]))
        labels = [str(x) for x in np.unique(y_true)]
        return plot_confusion_matrix(y_true, y_pred, labels)
        
    def roc_curve(self) -> Any:
        """Plot ROC curve."""
        from nexora.monitor.diagnostics import plot_roc_curve
        if self.task_type != "classification":
            raise ValueError("ROC curve is only available for classification tasks.")
        y_true = self.training_frame[self.target]
        y_prob = self.pipeline.predict_proba(self.training_frame.drop(columns=[self.target]))
        labels = [str(x) for x in np.unique(y_true)]
        return plot_roc_curve(y_true, y_prob, labels)
        
    def pr_curve(self) -> Any:
        """Plot Precision-Recall curve."""
        from nexora.monitor.diagnostics import plot_pr_curve
        if self.task_type != "classification":
            raise ValueError("PR curve is only available for classification tasks.")
        y_true = self.training_frame[self.target]
        y_prob = self.pipeline.predict_proba(self.training_frame.drop(columns=[self.target]))
        labels = [str(x) for x in np.unique(y_true)]
        return plot_pr_curve(y_true, y_prob, labels)
        
    def learning_curve(self, cv: int = 5) -> Any:
        """Plot bias-variance learning curve."""
        from nexora.monitor.diagnostics import plot_learning_curve
        X = self.training_frame.drop(columns=[self.target])
        y = self.training_frame[self.target]
        return plot_learning_curve(self.pipeline, X, y, cv=cv)
        
    def calibration_curve(self) -> Any:
        """Plot probability calibration curve."""
        from nexora.monitor.diagnostics import plot_calibration_curve
        if self.task_type != "classification":
            raise ValueError("Calibration curve is only available for classification tasks.")
        y_true = self.training_frame[self.target]
        y_prob = self.pipeline.predict_proba(self.training_frame.drop(columns=[self.target]))
        return plot_calibration_curve(y_true, y_prob)
        
    def error_analysis(self) -> pd.DataFrame:
        """Find segments where the model has highest error."""
        from nexora.monitor.performance import error_analysis
        y_true = self.training_frame[self.target]
        y_pred = self.pipeline.predict(self.training_frame.drop(columns=[self.target]))
        features = self.training_frame.drop(columns=[self.target])
        return error_analysis(y_true, y_pred, features, self.task_type)
        
    def drift(self, new_df: pd.DataFrame, threshold: float = 0.1) -> Any:
        """Detect feature distribution shift against training data."""
        from nexora.monitor.drift import detect_drift
        X_train = self.training_frame.drop(columns=[self.target])
        if self.target in new_df.columns:
            new_df = new_df.drop(columns=[self.target])
        return detect_drift(X_train, new_df, threshold)
        
    def monitor(self, new_df: pd.DataFrame) -> pd.DataFrame:
        """Generate a tabular monitoring report of drift metrics."""
        from nexora.monitor.drift import full_monitoring_report
        X_train = self.training_frame.drop(columns=[self.target])
        if self.target in new_df.columns:
            new_df = new_df.drop(columns=[self.target])
        return full_monitoring_report(X_train, new_df)
        
    def retrain(self, new_df: pd.DataFrame) -> "NexoraReport":
        """Retrain the best model pipeline on new data."""
        from nexora.core import Nexora
        # Since we just want to retrain the exact model, we could either:
        # 1. Run full automl again
        # 2. Re-fit the pipeline
        # For simplicity, we create a new Nexora object and force it to train only this model
        nx = Nexora(new_df, target=self.target)
        return nx.run(model_names=[self.best_model], max_models=1)

    def publish(self, repo_id: str, private: bool = False) -> str:
        """Publish the model and a generated model card to Hugging Face Hub.
        
        Args:
            repo_id: The ID of the repository to create/update on HF Hub (e.g. "user/model").
            private: Whether the repository should be private.
            
        Returns:
            The URL of the published repository.
        """
        import os
        import tempfile
        import joblib
        from huggingface_hub import HfApi
        
        api = HfApi()
        
        # Create repo
        url = api.create_repo(repo_id=repo_id, private=private, exist_ok=True)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # 1. Save pipeline
            model_path = os.path.join(tmpdir, "pipeline.pkl")
            joblib.dump(self.pipeline, model_path)
            
            # 2. Generate and save model card
            card = f"""---
tags:
- nexora
- tabular
- {self.task_type}
---

# {self.best_model} trained by Nexora

This model was automatically trained by [Nexora](https://github.com/jeet2005/Nexora) for a **{self.task_type}** task.

## Model Performance

The best model is **{self.best_model}** with a {self.best_score_label} of **{self.best_score:.4f}**.

### Leaderboard

| Model | Score |
|-------|-------|
"""
            for res in self.results:
                if res.status == "completed":
                    card += f"| {res.model_name} | {res.primary_score:.4f} |\n"
                    
            card += f"""
## Dataset Profile

- Target: `{self.target}`
- Rows: {self.profile.num_rows}
- Columns: {self.profile.num_columns}
- Missing values: {self.profile.missing_cells}

"""
            with open(os.path.join(tmpdir, "README.md"), "w", encoding="utf-8") as f:
                f.write(card)
                
            # Upload folder
            api.upload_folder(
                folder_path=tmpdir,
                repo_id=repo_id,
                repo_type="model",
                commit_message="Publish Nexora model"
            )
            
        return url

    def code_gradio(self) -> str:
        """Generate Gradio app code for model serving.
        
        Returns:
            Complete Gradio application code (standalone, ready to run).
        """
        # Ensure our codegen module has this function
        from nexora.export.codegen import generate_gradio_app
        return generate_gradio_app(self)

    def notebook(self, format: str = "ipynb") -> str:
        """Generate a notebook for the model.
        
        Args:
            format: "ipynb" (Jupyter) or "marimo" (Reactive).
            
        Returns:
            Notebook content as a string.
        """
        if format.lower() == "marimo":
            # Very basic marimo code generator
            import json
            
            # Create a simple python script that marimo uses natively
            cells = [
                "import marimo",
                "app = marimo.App()",
                "@app.cell\ndef __():\n    import marimo as mo\n    import joblib\n    import pandas as pd\n    return joblib, mo, pd",
                f"@app.cell\ndef __():\n    pipeline = joblib.load('pipeline.pkl')\n    return pipeline,",
                f"@app.cell\ndef __(mo):\n    mo.md('# Nexora Interactive Model')\n    return",
            ]
            return "\\n\\n".join(cells) + "\\n\\nif __name__ == '__main__':\\n    app.run()\\n"
        else:
            return self.code_notebook(self.best_model)

    def umap(self, n_components: int = 2) -> Any:
        """Plot a UMAP projection of the training data.
        
        Args:
            n_components: Number of dimensions to project to (2 or 3).
            
        Returns:
            A matplotlib or seaborn plot of the UMAP projection.
        """
        try:
            import umap
        except ImportError as e:
            raise ImportError("umap-learn is required for UMAP projection. Run `pip install umap-learn`.") from e
            
        import matplotlib.pyplot as plt
        import seaborn as sns
        
        X = self.training_frame.drop(columns=[self.target])
        y = self.training_frame[self.target]
        
        # Transform the data using the fitted pipeline's preprocessor
        preprocessor = self.pipeline.named_steps["preprocess"]
        X_trans = preprocessor.transform(X)
        
        reducer = umap.UMAP(n_components=n_components, random_state=42)
        embedding = reducer.fit_transform(X_trans)
        
        fig, ax = plt.subplots(figsize=(10, 8))
        if n_components == 2:
            if self.task_type == "classification":
                sns.scatterplot(x=embedding[:, 0], y=embedding[:, 1], hue=y, palette="Set1", ax=ax)
            else:
                sns.scatterplot(x=embedding[:, 0], y=embedding[:, 1], hue=y, palette="viridis", ax=ax)
            ax.set_title("UMAP Projection of Training Data")
            ax.set_xlabel("UMAP 1")
            ax.set_ylabel("UMAP 2")
        elif n_components == 3:
            ax = fig.add_subplot(111, projection='3d')
            scatter = ax.scatter(embedding[:, 0], embedding[:, 1], embedding[:, 2], c=y, cmap="viridis")
            plt.colorbar(scatter)
            ax.set_title("UMAP 3D Projection")
            
        plt.tight_layout()
        return fig

    def diff(self, other: "NexoraReport") -> dict[str, Any]:
        """Compare this session with another report session.
        
        Args:
            other: Another NexoraReport to compare against.
            
        Returns:
            Dictionary containing the differences in data shape, best models, and performance.
        """
        return {
            "data_profile": {
                "rows_diff": self.profile.num_rows - other.profile.num_rows,
                "columns_diff": self.profile.num_columns - other.profile.num_columns,
            },
            "performance": {
                "best_model_self": self.best_model,
                "best_model_other": other.best_model,
                "score_diff": self.best_score - other.best_score
            },
            "features": {
                "added": list(set(self.profile.column_names) - set(other.profile.column_names)),
                "removed": list(set(other.profile.column_names) - set(self.profile.column_names))
            }
        }

    def scan_bias(self, protected_attribute: str) -> pd.DataFrame:
        """Scan the model for disparate impact against a protected attribute.
        
        Args:
            protected_attribute: Column name to scan for bias.
            
        Returns:
            DataFrame containing selection rates or average scores per segment.
        """
        if protected_attribute not in self.training_frame.columns:
            raise ValueError(f"Protected attribute '{protected_attribute}' not found in training frame.")
            
        y_true = self.training_frame[self.target]
        X = self.training_frame.drop(columns=[self.target])
        y_pred = self.pipeline.predict(X)
        
        segments = self.training_frame[protected_attribute]
        
        results = []
        for segment_value in segments.unique():
            mask = segments == segment_value
            segment_true = y_true[mask]
            segment_pred = y_pred[mask]
            
            if self.task_type == "classification":
                from sklearn.metrics import accuracy_score
                selection_rate = segment_pred.mean()
                accuracy = accuracy_score(segment_true, segment_pred)
                results.append({
                    "segment": segment_value,
                    "count": mask.sum(),
                    "selection_rate": selection_rate,
                    "accuracy": accuracy
                })
            else:
                from sklearn.metrics import mean_squared_error
                avg_pred = segment_pred.mean()
                rmse = np.sqrt(mean_squared_error(segment_true, segment_pred))
                results.append({
                    "segment": segment_value,
                    "count": mask.sum(),
                    "avg_prediction": avg_pred,
                    "rmse": rmse
                })
                
        return pd.DataFrame(results)

    def reproducibility_score(self) -> int:
        """Score how easily this session can be re-run (0-100)."""
        score = 100
        
        # Deduct if data wasn't tracked by DVC (assuming we have a flag or file path check)
        import os
        if not os.path.exists(".dvc"):
            score -= 30
            
        # Deduct if no specific random state was passed (we default to 42, but assume static)
        
        # Deduct if pip freeze isn't pinned in pyproject.toml / requirements.txt
        if not os.path.exists("requirements.txt") and not os.path.exists("pyproject.toml"):
            score -= 20
            
        return max(0, score)

    def code_github_actions(self) -> str:
        """Generate a GitHub Actions workflow for training and deployment."""
        return f"""name: Nexora Train and Publish

on:
  push:
    branches:
      - main

jobs:
  train_and_publish:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
          
      - name: Install dependencies
        run: pip install nexora huggingface_hub
        
      - name: Run Nexora Training Script
        env:
          HF_TOKEN: ${{{{ secrets.HF_TOKEN }}}}
        run: |
          python -c "
          from nexora import Nexora
          import pandas as pd
          df = pd.read_csv('data/dataset.csv')
          nx = Nexora(df, target='{self.target}')
          report = nx.run()
          report.publish('my-org/my-nexora-model')
          "
"""
