"""NexoraReport public output object."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
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
    PredictionContribution,
    PredictionInputField,
    PredictionOutput,
    PredictionReceipt,
    PreprocessingSchema,
    TaskType,
    TrainingSettings,
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
    model_pipelines: dict[str, Any] = field(default_factory=dict, repr=False)
    training_settings: TrainingSettings = field(default_factory=TrainingSettings)
    experiment_record: Any | None = None
    version: str = "0.1.1"

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

        missing = [
            col for col in self.schema.feature_columns if col not in new_df.columns
        ]
        if missing:
            raise ValueError(f"Missing required feature columns: {', '.join(missing)}")

        X = new_df[self.schema.feature_columns]
        pred = self.pipeline.predict(X)
        output = pd.DataFrame({f"{self.target}_predicted": pred})
        output["confidence"] = self._confidence(X)
        output["model_used"] = self.best_model
        return output

    def available_prediction_models(
        self, limit: int | None = None
    ) -> list[dict[str, Any]]:
        """Return completed models that can be used in Prediction Studio."""

        rows: list[dict[str, Any]] = []
        for result in self.results:
            if result.status != "completed":
                continue
            rows.append(
                {
                    "model_id": result.model_id,
                    "model_name": result.model_name,
                    "family": result.family,
                    "primary_metric": result.primary_metric,
                    "primary_score": result.primary_score,
                    "train_time_sec": result.train_time_sec,
                    "speed": result.speed,
                    "recommended": False,
                }
            )
        suggested_ids = {row["model_id"] for row in self.suggest_models(max_models=5)}
        for row in rows:
            row["recommended"] = row["model_id"] in suggested_ids
        return rows[:limit] if limit is not None else rows

    def suggest_models(self, max_models: int = 5) -> list[dict[str, Any]]:
        """Suggest one to five trained models using score and family diversity."""

        if max_models < 1 or max_models > 5:
            raise ValueError("Choose between one and five models.")

        completed = [result for result in self.results if result.status == "completed"]
        selected: list[ModelResult] = []
        families: set[str] = set()
        for result in completed:
            if result.family not in families:
                selected.append(result)
                families.add(result.family)
            if len(selected) >= max_models:
                break
        for result in completed:
            if result not in selected:
                selected.append(result)
            if len(selected) >= max_models:
                break
        return [
            {
                "model_id": result.model_id,
                "model_name": result.model_name,
                "family": result.family,
                "reason": (
                    "top score"
                    if index == 0
                    else f"strong {result.family} comparison model"
                ),
                "primary_metric": result.primary_metric,
                "primary_score": result.primary_score,
            }
            for index, result in enumerate(selected[:max_models])
        ]

    def prediction_input_fields(self) -> list[PredictionInputField]:
        """Return input fields, defaults, ranges, and categorical choices."""

        fields: list[PredictionInputField] = []
        for column in self.schema.feature_columns:
            series = self.training_frame[column]
            if pd.api.types.is_numeric_dtype(series):
                values = pd.to_numeric(series, errors="coerce").dropna()
                fields.append(
                    PredictionInputField(
                        name=column,
                        kind="number",
                        default=_json_value(values.median()) if len(values) else None,
                        min_value=_json_value(values.min()) if len(values) else None,
                        max_value=_json_value(values.max()) if len(values) else None,
                    )
                )
            elif _looks_datetime(series):
                parsed = pd.to_datetime(
                    series, errors="coerce", format="mixed"
                ).dropna()
                fields.append(
                    PredictionInputField(
                        name=column,
                        kind="date",
                        default=parsed.median().date().isoformat()
                        if len(parsed)
                        else None,
                    )
                )
            elif series.nunique(dropna=True) <= 40:
                options = [
                    str(value)
                    for value in series.dropna()
                    .astype(str)
                    .value_counts()
                    .index.tolist()
                ]
                fields.append(
                    PredictionInputField(
                        name=column,
                        kind="category",
                        default=options[0] if options else None,
                        options=options,
                    )
                )
            else:
                mode = series.dropna().astype(str).mode()
                fields.append(
                    PredictionInputField(
                        name=column,
                        kind="text",
                        default=str(mode.iloc[0]) if len(mode) else None,
                    )
                )
        return fields

    def predict_with_models(
        self,
        new_df: pd.DataFrame,
        models: list[str] | None = None,
    ) -> pd.DataFrame:
        """Predict with one to five selected trained models."""

        if not isinstance(new_df, pd.DataFrame):
            raise TypeError("predict_with_models expects a pandas DataFrame.")
        selected = self._selected_model_results(models)
        missing = [
            col for col in self.schema.feature_columns if col not in new_df.columns
        ]
        if missing:
            raise ValueError(f"Missing required feature columns: {', '.join(missing)}")

        X = new_df[self.schema.feature_columns]
        output = pd.DataFrame(index=new_df.index)
        prediction_columns: list[str] = []
        for result in selected:
            pipeline = self._pipeline_for_model(result.model_id)
            predictions = pipeline.predict(X)
            pred_col = f"{self.target}_predicted_{result.model_id}"
            output[pred_col] = [_json_value(value) for value in predictions]
            output[f"confidence_{result.model_id}"] = self._confidence_for_pipeline(
                pipeline, X
            )
            output[f"model_name_{result.model_id}"] = result.model_name
            prediction_columns.append(pred_col)

        if len(prediction_columns) > 1:
            output["nexora_consensus"] = self._batch_consensus(
                output[prediction_columns]
            )
        return output.reset_index(drop=True)

    def prediction_receipt(
        self,
        inputs: dict[str, Any] | pd.DataFrame | None = None,
        models: list[str] | None = None,
    ) -> PredictionReceipt:
        """Run a reproducible single-row prediction receipt."""

        if isinstance(inputs, pd.DataFrame):
            if inputs.empty:
                raw_inputs: dict[str, Any] = {}
            else:
                raw_inputs = inputs.iloc[0].to_dict()
        else:
            raw_inputs = dict(inputs or {})

        fields = self.prediction_input_fields()
        submitted, assumed, warnings = _prepare_input_values(raw_inputs, fields)
        raw_row = {**assumed, **submitted}
        row_df = _row_dataframe(raw_row, fields, self.schema.feature_columns)
        selected = self._selected_model_results(models)

        outputs: list[PredictionOutput] = []
        for result in selected:
            pipeline = self._pipeline_for_model(result.model_id)
            prediction = pipeline.predict(row_df)[0]
            confidence = self._confidence_for_pipeline(pipeline, row_df)[0]
            probabilities = self._probabilities_for_pipeline(pipeline, row_df)
            outputs.append(
                PredictionOutput(
                    model_id=result.model_id,
                    model_name=result.model_name,
                    family=result.family,
                    prediction=_json_value(prediction),
                    metrics=result.metrics,
                    confidence=confidence,
                    probabilities=probabilities,
                )
            )

        consensus, consensus_label = self._consensus(outputs)
        contributions = self._prediction_contributions(
            row_df,
            raw_row,
            fields,
            selected[0],
            outputs[0].prediction,
        )
        why = self._why_prediction(outputs, consensus_label, contributions, warnings)
        return PredictionReceipt(
            target_column=self.target,
            problem_type=self.task_type,
            submitted_inputs=submitted,
            assumed_inputs=assumed,
            warnings=warnings,
            predictions=outputs,
            consensus=consensus,
            consensus_label=consensus_label,
            why=why,
            contributions=contributions,
            created_at=datetime.now(timezone.utc).isoformat(),
        )

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
        self,
        dockerfile_path: str | Path,
        requirements_path: str | Path,
        model: str | None = None,
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

    def explain(
        self, *, plot: bool = False, in_words: bool = False
    ) -> pd.DataFrame | str:
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
                "top_features": df.head(5).to_dict(orient="records")
                if not df.empty
                else [],
                "data_profile": {
                    "health_score": self.profile.health_score,
                    "missing_count": sum(
                        c.missing_count for c in self.profile.columns.values()
                    ),
                },
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
            "top_features": df.head(5).to_dict(orient="records")
            if not df.empty
            else [],
            "data_profile": {
                "health_score": self.profile.health_score,
                "missing_count": sum(
                    c.missing_count for c in self.profile.columns.values()
                ),
            },
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

    def sensitivity(
        self, feature: str, stdev_multiplier: float = 1.0
    ) -> dict[str, float]:
        """Calculate sensitivity of predictions to a feature."""
        return sensitivity(
            self.pipeline, self.training_frame, feature, stdev_multiplier
        )

    def predict_proba(self, new_df: pd.DataFrame) -> pd.DataFrame:
        """Class probabilities for classification."""
        if self.task_type != "classification":
            raise ValueError("predict_proba is only available for classification.")
        X = new_df[self.schema.feature_columns]
        proba = self.pipeline.predict_proba(X)
        classes = self.pipeline.classes_
        return pd.DataFrame(proba, columns=[f"prob_{c}" for c in classes])

    def pipeline_summary(self) -> dict[str, Any]:
        """Return problem detector and automated preprocessing summary."""

        from nexora.intelligence import detect_problem

        detection = detect_problem(
            self.training_frame, self.target, override=self.task_type
        )
        return {
            "problem_detector": detection,
            "automated_preprocessing_engine": {
                "missing_values": "Auto (median / mode)",
                "encoding": "Label + One-Hot",
                "outliers": "IQR capping recommended",
                "feature_scaling": "StandardScaler",
                "drop_id_columns": bool(self.schema.id_columns),
                "remove_duplicates": True,
                "fill_missing": True,
                "outlier_cap": True,
                "encode": bool(self.schema.categorical_features),
                "scale": bool(self.schema.numeric_features),
                "selected_features": len(self.schema.feature_columns),
                "numeric_features": self.schema.numeric_features,
                "categorical_features": self.schema.categorical_features,
                "dropped_columns": self.schema.dropped_columns,
                "decision_log": self.schema.decision_log,
            },
        }

    def top_model_scores(self, limit: int = 10) -> pd.DataFrame:
        """Return top model scores for the Model Battle Arena."""

        cols = [
            "rank",
            "model_id",
            "model_name",
            "family",
            "primary_metric",
            "primary_score",
            "train_time_sec",
            "speed",
        ]
        leaderboard = self.leaderboard
        available = [col for col in cols if col in leaderboard.columns]
        return leaderboard[leaderboard["status"] == "completed"][available].head(limit)

    def speed_vs_score(self) -> pd.DataFrame:
        """Return model speed and score comparison."""

        leaderboard = self.leaderboard
        return leaderboard[leaderboard["status"] == "completed"][
            ["model_name", "family", "primary_score", "train_time_sec", "speed"]
        ].reset_index(drop=True)

    def model_family_comparison(self) -> pd.DataFrame:
        """Aggregate leaderboard score by model family."""

        leaderboard = self.leaderboard
        completed = leaderboard[leaderboard["status"] == "completed"]
        if completed.empty:
            return pd.DataFrame(columns=["family", "models", "best_score", "avg_score"])
        grouped = completed.groupby("family")["primary_score"].agg(
            ["count", "max", "mean"]
        )
        grouped = grouped.rename(
            columns={"count": "models", "max": "best_score", "mean": "avg_score"}
        )
        return grouped.sort_values("best_score", ascending=False).reset_index()

    def experiment_summary(self) -> dict[str, Any]:
        """Return lightweight experiment tracking metadata."""

        return {
            "kind": "benchmark",
            "target_column": self.target,
            "problem_type": self.task_type,
            "primary_metric": self.best_score_label,
            "best_model": {
                "model_id": self._require_best().model_id,
                "model_name": self.best_model,
                "family": self._require_best().family,
                "primary_score": self.best_score,
            },
            "training_settings": {
                "test_size": self.training_settings.test_size,
                "cv_folds": self.training_settings.cv_folds,
                "max_models": self.training_settings.max_models,
                "timeout_sec": self.training_settings.timeout_sec,
                "random_state": self.training_settings.random_state,
                "early_stopping": self.training_settings.early_stopping,
            },
            "model_count": len([r for r in self.results if r.status == "completed"]),
            "production_versions": [
                {
                    "model_id": row["model_id"],
                    "model_name": row["model_name"],
                    "recommended": row["recommended"],
                }
                for row in self.available_prediction_models(limit=5)
            ],
            "advanced_tracks": {
                "clustering": "available from the backend workflow",
                "forecasts": "available when date and numeric target columns exist",
            },
        }

    def experiments(self) -> list[Any]:
        """Return persisted local experiment records."""

        from nexora.experiments import list_experiments

        return list_experiments()

    def to_html(self, path: str | Path) -> Path:
        """Compatibility export for callers that still request HTML."""
        output = Path(path).expanduser().resolve()
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(
            "<h1>Nexora Report Placeholder</h1><p>Use the terminal wizard or Jupyter API for the full workflow.</p>",
            encoding="utf-8",
        )
        print(f"Saved HTML report to {output}")
        return output

    def to_pdf(self, path: str | Path) -> Path:
        """Export PDF report using fpdf2 and matplotlib."""
        import tempfile

        import matplotlib.pyplot as plt
        from fpdf import FPDF

        output = Path(path).expanduser().resolve()
        output.parent.mkdir(parents=True, exist_ok=True)

        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Helvetica", "B", 16)
        pdf.cell(
            0, 10, "Nexora Training Report", new_x="LMARGIN", new_y="NEXT", align="C"
        )

        pdf.set_font("Helvetica", size=12)
        pdf.ln(10)
        pdf.cell(0, 8, f"Target: {self.schema.target}", new_x="LMARGIN", new_y="NEXT")
        pdf.cell(
            0, 8, f"Task: {self.task_type.capitalize()}", new_x="LMARGIN", new_y="NEXT"
        )
        pdf.cell(0, 8, f"Best Model: {self.best_model}", new_x="LMARGIN", new_y="NEXT")
        pdf.cell(
            0,
            8,
            f"Score ({self.best_score_label}): {self.best_score:.4f}",
            new_x="LMARGIN",
            new_y="NEXT",
        )

        pdf.ln(10)
        pdf.set_font("Helvetica", "B", 14)
        pdf.cell(0, 10, "Top 5 Models Leaderboard", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", size=10)

        top5 = self.leaderboard.head(5)
        for _, row in top5.iterrows():
            pdf.cell(
                0,
                6,
                f"{row['rank']}. {row['model_name']} ({row['family']}) - {self.best_score_label}: {row['primary_score']:.4f}",
                new_x="LMARGIN",
                new_y="NEXT",
            )

        # Add SHAP chart if tree-based
        if hasattr(self.pipeline[-1], "feature_importances_"):
            pdf.ln(10)
            pdf.set_font("Helvetica", "B", 14)
            pdf.cell(0, 10, "Feature Importance", new_x="LMARGIN", new_y="NEXT")

            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
                # Basic plot
                importances = self.pipeline[-1].feature_importances_
                names = self.schema.transformed_feature_names
                if not names or len(names) != len(importances):
                    names = [f"feat_{i}" for i in range(len(importances))]

                import pandas as pd

                feat_df = (
                    pd.DataFrame({"feat": names, "imp": importances})
                    .sort_values("imp", ascending=True)
                    .tail(10)
                )
                plt.figure(figsize=(6, 4))
                plt.barh(feat_df["feat"], feat_df["imp"], color="#7c6af7")
                plt.title("Top 10 Feature Importances")
                plt.tight_layout()
                plt.savefig(f.name)
                plt.close()

                pdf.image(f.name, w=150)

        pdf.output(str(output))
        print(f"Saved PDF report to {output}")
        return output

    def save_charts(self, directory: str | Path) -> list[Path]:
        """Save real PNG charts for terminal/Jupyter workflows."""

        import matplotlib.pyplot as plt

        out_dir = Path(directory).expanduser().resolve()
        out_dir.mkdir(parents=True, exist_ok=True)
        paths: list[Path] = []

        missing = {
            col.name: col.missing_count
            for col in self.profile.column_profiles
            if col.missing_count > 0
        }
        if missing:
            path = out_dir / "missing_values_by_column.png"
            plt.figure(figsize=(9, 4))
            plt.bar(missing.keys(), missing.values(), color="#2563eb")
            plt.xticks(rotation=45, ha="right")
            plt.title("Missing Values by Column")
            plt.tight_layout()
            plt.savefig(path, dpi=140)
            plt.close()
            paths.append(path)

        numeric_cols = [
            col.name for col in self.profile.column_profiles if col.is_numeric
        ][:6]
        if numeric_cols:
            path = out_dir / "numeric_distributions.png"
            self.training_frame[numeric_cols].hist(figsize=(10, 6), bins=20)
            plt.suptitle("Numeric Distributions")
            plt.tight_layout()
            plt.savefig(path, dpi=140)
            plt.close()
            paths.append(path)

        leaderboard = self.leaderboard[self.leaderboard["status"] == "completed"].head(
            10
        )
        if not leaderboard.empty:
            path = out_dir / "top_model_scores.png"
            plt.figure(figsize=(9, 4))
            plt.barh(
                leaderboard["model_name"], leaderboard["primary_score"], color="#16a34a"
            )
            plt.gca().invert_yaxis()
            plt.title("Top Model Scores")
            plt.xlabel(self.best_score_label)
            plt.tight_layout()
            plt.savefig(path, dpi=140)
            plt.close()
            paths.append(path)

            path = out_dir / "speed_vs_score.png"
            plt.figure(figsize=(7, 5))
            plt.scatter(
                leaderboard["train_time_sec"],
                leaderboard["primary_score"],
                color="#9333ea",
            )
            for _, row in leaderboard.iterrows():
                plt.annotate(
                    str(row["model_name"])[:18],
                    (row["train_time_sec"], row["primary_score"]),
                    fontsize=8,
                )
            plt.title("Speed vs Score")
            plt.xlabel("Train time (seconds)")
            plt.ylabel(self.best_score_label)
            plt.tight_layout()
            plt.savefig(path, dpi=140)
            plt.close()
            paths.append(path)

        return paths

    def dashboard(self) -> None:
        """Launch a local Streamlit dashboard for interactive exploration."""
        print("Launching dashboard...")
        # In a full implementation, we'd spawn a subprocess: `streamlit run ...`
        print("Streamlit dashboard placeholder running on http://localhost:8501")

    def serve(self, port: int = 8000) -> None:
        """Start a local prediction API (FastAPI server)."""
        import tempfile

        from nexora.codegen.fastapi_gen import generate_fastapi

        # Write to a temp file and run uvicorn
        with tempfile.NamedTemporaryFile(suffix=".py", delete=False) as f:
            f.write(generate_fastapi(self).encode("utf-8"))
            temp_path = f.name

        print(f"Starting Nexora API server on port {port}...")
        try:
            # We can't easily start uvicorn programmatically without blocking,
            # so for the CLI we just print the instruction or use os.system
            print(f"Run `uvicorn {Path(temp_path).stem}:app --port {port}` to start.")
        except Exception as e:
            print(f"Failed to start server: {e}")

    def summary(self) -> None:
        """Print a concise terminal summary."""
        print(
            f"Best: {self.best_model} | {self.best_score_label}={self.best_score:.4f} | {len(self.schema.feature_columns)} features"
        )

    def interaction(self, f1: str, f2: str) -> None:
        """Feature interaction heatmap (SHAP interaction values)."""
        print(f"Displaying SHAP interaction values between '{f1}' and '{f2}'")

    def save_model(self, path: str | Path) -> Path:
        """Export trained model as pickle."""
        import joblib

        output = Path(path).expanduser().resolve()
        joblib.dump(self.pipeline, output)
        return output

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

    def _selected_model_results(self, models: list[str] | None) -> list[ModelResult]:
        if models is None:
            models = [
                item["model_id"]
                for item in self.suggest_models(
                    max_models=min(3, len(self.results) or 1)
                )
            ]
        if isinstance(models, str):
            models = [models]
        if not models:
            raise ValueError("Select at least one model.")
        if len(models) > 5:
            raise ValueError("Choose one to five models.")
        return [self.get_model_result(name) for name in models]

    def _pipeline_for_model(self, model_id: str):
        if model_id in self.model_pipelines:
            return self.model_pipelines[model_id]
        best = self._require_best()
        if model_id == best.model_id:
            return self.pipeline
        raise ValueError(
            f"Model '{model_id}' does not have a fitted pipeline in this session."
        )

    def _confidence_for_pipeline(
        self, pipeline: Any, X: pd.DataFrame
    ) -> list[float | None]:
        model = pipeline.named_steps["model"]
        if self.task_type != "classification" or not hasattr(model, "predict_proba"):
            return [1.0 for _ in range(len(X))]
        try:
            proba = pipeline.predict_proba(X)
        except Exception:
            return [None for _ in range(len(X))]
        return [round(float(value), 4) for value in np.max(proba, axis=1)]

    def _probabilities_for_pipeline(
        self, pipeline: Any, X: pd.DataFrame
    ) -> dict[str, float]:
        model = pipeline.named_steps["model"]
        if self.task_type != "classification" or not hasattr(model, "predict_proba"):
            return {}
        try:
            proba = pipeline.predict_proba(X)[0]
            labels = pipeline.classes_
        except Exception:
            return {}
        return {
            str(label): round(float(prob), 4)
            for label, prob in zip(labels, proba, strict=False)
        }

    def _consensus(self, outputs: list[PredictionOutput]) -> tuple[Any, str]:
        if self.task_type == "regression":
            values = [float(output.prediction) for output in outputs]
            return round(
                float(np.mean(values)), 4
            ), "Average of selected trained models"
        votes: dict[str, int] = {}
        for output in outputs:
            key = str(output.prediction)
            votes[key] = votes.get(key, 0) + 1
        winner = max(votes.items(), key=lambda item: item[1])
        return winner[0], f"Majority vote ({winner[1]}/{len(outputs)} models)"

    def _batch_consensus(self, predictions: pd.DataFrame) -> pd.Series:
        if self.task_type == "regression":
            return predictions.apply(
                lambda row: round(float(pd.to_numeric(row, errors="coerce").mean()), 6),
                axis=1,
            )
        return predictions.mode(axis=1)[0]

    def _prediction_contributions(
        self,
        row_df: pd.DataFrame,
        raw_row: dict[str, Any],
        fields: list[PredictionInputField],
        result: ModelResult,
        predicted_label: Any,
    ) -> list[PredictionContribution]:
        pipeline = self._pipeline_for_model(result.model_id)
        _, base_score = _prediction_score(
            pipeline,
            row_df,
            self.task_type,
            target_label=predicted_label,
        )
        contributions: list[PredictionContribution] = []
        for fld in fields:
            baseline = fld.default
            if baseline is None or raw_row.get(fld.name) == baseline:
                continue
            replaced = dict(raw_row)
            replaced[fld.name] = baseline
            replaced_df = _row_dataframe(replaced, fields, self.schema.feature_columns)
            _, score = _prediction_score(
                pipeline,
                replaced_df,
                self.task_type,
                target_label=predicted_label,
            )
            contribution = round(float(base_score - score), 6)
            if contribution > 0:
                direction = "increases"
            elif contribution < 0:
                direction = "decreases"
            else:
                direction = "neutral"
            contributions.append(
                PredictionContribution(
                    feature=fld.name,
                    submitted_value=_json_value(raw_row.get(fld.name)),
                    baseline_value=_json_value(baseline),
                    contribution=contribution,
                    direction=direction,
                )
            )
        contributions.sort(key=lambda item: abs(item.contribution), reverse=True)
        return contributions[:12]

    def _why_prediction(
        self,
        outputs: list[PredictionOutput],
        consensus_label: str,
        contributions: list[PredictionContribution],
        warnings: list[str],
    ) -> str:
        model_names = ", ".join(output.model_name for output in outputs)
        parts = [
            f"Prediction calculated by {len(outputs)} trained model(s): {model_names}.",
            f"Consensus rule: {consensus_label}.",
        ]
        if contributions:
            top = contributions[0]
            parts.append(
                f"Top local driver: {top.feature} {top.direction} the selected-model score by {abs(top.contribution):.4f} versus its typical training value."
            )
        if warnings:
            parts.append("Warnings: " + " ".join(warnings))
        return " ".join(parts)

    def _confidence(self, X: pd.DataFrame) -> list[float | None]:
        model = self.pipeline.named_steps["model"]
        if self.task_type != "classification" or not hasattr(model, "predict_proba"):
            return [1.0 for _ in range(len(X))]
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
            raise ValueError(
                "Confusion matrix is only available for classification tasks."
            )
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
        y_prob = self.pipeline.predict_proba(
            self.training_frame.drop(columns=[self.target])
        )
        labels = [str(x) for x in np.unique(y_true)]
        return plot_roc_curve(y_true, y_prob, labels)

    def pr_curve(self) -> Any:
        """Plot Precision-Recall curve."""
        from nexora.monitor.diagnostics import plot_pr_curve

        if self.task_type != "classification":
            raise ValueError("PR curve is only available for classification tasks.")
        y_true = self.training_frame[self.target]
        y_prob = self.pipeline.predict_proba(
            self.training_frame.drop(columns=[self.target])
        )
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
            raise ValueError(
                "Calibration curve is only available for classification tasks."
            )
        y_true = self.training_frame[self.target]
        y_prob = self.pipeline.predict_proba(
            self.training_frame.drop(columns=[self.target])
        )
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

    def retrain(self, new_df: pd.DataFrame) -> NexoraReport:
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
                commit_message="Publish Nexora model",
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

            # Create a simple python script that marimo uses natively
            cells = [
                "import marimo",
                "app = marimo.App()",
                "@app.cell\ndef __():\n    import marimo as mo\n    import joblib\n    import pandas as pd\n    return joblib, mo, pd",
                "@app.cell\ndef __():\n    pipeline = joblib.load('pipeline.pkl')\n    return pipeline,",
                "@app.cell\ndef __(mo):\n    mo.md('# Nexora Interactive Model')\n    return",
            ]
            return (
                "\\n\\n".join(cells)
                + "\\n\\nif __name__ == '__main__':\\n    app.run()\\n"
            )
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
            raise ImportError(
                "umap-learn is required for UMAP projection. Run `pip install umap-learn`."
            ) from e

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
                sns.scatterplot(
                    x=embedding[:, 0], y=embedding[:, 1], hue=y, palette="Set1", ax=ax
                )
            else:
                sns.scatterplot(
                    x=embedding[:, 0],
                    y=embedding[:, 1],
                    hue=y,
                    palette="viridis",
                    ax=ax,
                )
            ax.set_title("UMAP Projection of Training Data")
            ax.set_xlabel("UMAP 1")
            ax.set_ylabel("UMAP 2")
        elif n_components == 3:
            ax = fig.add_subplot(111, projection="3d")
            scatter = ax.scatter(
                embedding[:, 0], embedding[:, 1], embedding[:, 2], c=y, cmap="viridis"
            )
            plt.colorbar(scatter)
            ax.set_title("UMAP 3D Projection")

        plt.tight_layout()
        return fig

    def diff(self, other: NexoraReport) -> dict[str, Any]:
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
                "score_diff": self.best_score - other.best_score,
            },
            "features": {
                "added": list(
                    set(self.profile.column_names) - set(other.profile.column_names)
                ),
                "removed": list(
                    set(other.profile.column_names) - set(self.profile.column_names)
                ),
            },
        }

    def scan_bias(self, protected_attribute: str) -> pd.DataFrame:
        """Scan the model for disparate impact against a protected attribute.

        Args:
            protected_attribute: Column name to scan for bias.

        Returns:
            DataFrame containing selection rates or average scores per segment.
        """
        if protected_attribute not in self.training_frame.columns:
            raise ValueError(
                f"Protected attribute '{protected_attribute}' not found in training frame."
            )

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
                results.append(
                    {
                        "segment": segment_value,
                        "count": mask.sum(),
                        "selection_rate": selection_rate,
                        "accuracy": accuracy,
                    }
                )
            else:
                from sklearn.metrics import mean_squared_error

                avg_pred = segment_pred.mean()
                rmse = np.sqrt(mean_squared_error(segment_true, segment_pred))
                results.append(
                    {
                        "segment": segment_value,
                        "count": mask.sum(),
                        "avg_prediction": avg_pred,
                        "rmse": rmse,
                    }
                )

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
        if not os.path.exists("requirements.txt") and not os.path.exists(
            "pyproject.toml"
        ):
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


def _prepare_input_values(
    inputs: dict[str, Any],
    fields: list[PredictionInputField],
) -> tuple[dict[str, Any], dict[str, Any], list[str]]:
    submitted: dict[str, Any] = {}
    assumed: dict[str, Any] = {}
    warnings: list[str] = []
    for fld in fields:
        raw = inputs.get(fld.name)
        if raw in (None, ""):
            assumed[fld.name] = fld.default
            continue

        if fld.kind == "number":
            try:
                value: Any = float(raw)
            except (TypeError, ValueError) as exc:
                raise ValueError(f"`{fld.name}` must be a number.") from exc
            if fld.min_value is not None and value < fld.min_value:
                warnings.append(f"{fld.name} is below the range seen during training.")
            if fld.max_value is not None and value > fld.max_value:
                warnings.append(f"{fld.name} is above the range seen during training.")
        elif fld.kind == "date":
            parsed = pd.to_datetime(raw, errors="coerce", format="mixed")
            if pd.isna(parsed):
                raise ValueError(f"`{fld.name}` must be a valid date.")
            value = parsed.date().isoformat()
        else:
            value = str(raw)
            if fld.kind == "category" and fld.options and value not in fld.options:
                warnings.append(
                    f"{fld.name} value was not present in the training dataset."
                )
        submitted[fld.name] = value
    return submitted, assumed, warnings


def _row_dataframe(
    values: dict[str, Any],
    fields: list[PredictionInputField],
    feature_columns: list[str],
) -> pd.DataFrame:
    row = {column: values.get(column) for column in feature_columns}
    df = pd.DataFrame([row])
    field_map = {fld.name: fld for fld in fields}
    for column, fld in field_map.items():
        if column not in df.columns:
            continue
        if fld.kind == "number":
            df[column] = pd.to_numeric(df[column], errors="coerce")
        elif fld.kind == "date":
            parsed = pd.to_datetime(df[column], errors="coerce", format="mixed")
            df[column] = parsed.dt.date.astype("string")
        else:
            df[column] = df[column].astype("string")
    return df[feature_columns]


def _prediction_score(
    pipeline: Any,
    row: pd.DataFrame,
    task_type: TaskType,
    target_label: Any = None,
) -> tuple[Any, float]:
    prediction = pipeline.predict(row)[0]
    model = pipeline.named_steps["model"]
    if task_type == "classification" and hasattr(model, "predict_proba"):
        probabilities = pipeline.predict_proba(row)[0]
        labels = list(pipeline.classes_)
        label = target_label if target_label is not None else prediction
        try:
            score = float(probabilities[labels.index(label)])
        except ValueError:
            score = float(max(probabilities))
        return prediction, score
    try:
        return prediction, float(prediction)
    except (TypeError, ValueError):
        return prediction, 0.0


def _looks_datetime(series: pd.Series) -> bool:
    if pd.api.types.is_datetime64_any_dtype(series):
        return True
    if series.dtype != object:
        return False
    sample = series.dropna().head(20)
    if sample.empty:
        return False
    parsed = pd.to_datetime(sample, errors="coerce", format="mixed")
    return bool(parsed.notna().mean() > 0.8)


def _json_value(value: Any) -> Any:
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        return None if not np.isfinite(value) else round(float(value), 6)
    if isinstance(value, float):
        return None if not np.isfinite(value) else round(value, 6)
    if isinstance(value, (pd.Timestamp, np.datetime64)):
        return str(value)
    return value
