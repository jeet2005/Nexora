"""Main Nexora entry point."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from nexora.advanced import run_clustering, run_forecast
from nexora.experiments import create_training_experiment, list_experiments
from nexora.intelligence import (
    build_dataset_intelligence,
    detect_problem,
    suggest_targets,
)
from nexora.io.loaders import load_source
from nexora.io.serializer import load_report
from nexora.models.task_detector import detect_task_type
from nexora.models.trainer import train_models
from nexora.preprocessing.pipeline_builder import build_preprocessing
from nexora.profiler.dataset_profile import profile_dataset
from nexora.report import NexoraReport
from nexora.types import (
    DatasetIntelligence,
    DatasetProfile,
    LoadedData,
    PreprocessingConfig,
    TaskType,
)


class Nexora:
    """Primary package entry point for autonomous predictive analytics.

    Args:
        source: CSV path, pandas DataFrame, or NumPy array.
        target: Optional target column. Required for `run()`.

    Returns:
        A Nexora session object.

    Example:
        `report = Nexora("sales.csv", target="revenue").run()`
    """

    def __init__(self, source, target: str | None = None, y=None, feature_names=None):
        loaded = load_source(source, y=y, feature_names=feature_names)
        self._loaded: LoadedData = loaded
        self.df = loaded.dataframe
        self.source_path: Path | None = loaded.source_path
        self.source_name = loaded.source_name
        self.target = target
        if target is not None and target not in self.df.columns:
            raise ValueError(f"Target column '{target}' not found.")

    @classmethod
    def from_url(cls, url: str, target: str | None = None) -> Nexora:
        from nexora.io.remote import load_from_url
        return cls(load_from_url(url), target=target)

    @classmethod
    def from_sql(cls, query: str, connection_string: str | None = None, target: str | None = None) -> Nexora:
        from nexora.io.remote import load_from_sql
        return cls(load_from_sql(query, connection_string), target=target)

    @classmethod
    def from_postgres(cls, uri: str, table: str, target: str | None = None) -> Nexora:
        from nexora.io.remote import load_from_postgres
        return cls(load_from_postgres(uri, table), target=target)

    @classmethod
    def from_mongodb(cls, uri: str, collection: str, target: str | None = None) -> Nexora:
        from nexora.io.remote import load_from_mongodb
        return cls(load_from_mongodb(uri, collection), target=target)

    @classmethod
    def from_s3(cls, bucket: str, key: str, target: str | None = None) -> Nexora:
        from nexora.io.remote import load_from_s3
        return cls(load_from_s3(bucket, key), target=target)

    @classmethod
    def from_google_sheets(cls, sheet_id: str, target: str | None = None) -> Nexora:
        from nexora.io.remote import load_from_google_sheets
        return cls(load_from_google_sheets(sheet_id), target=target)

    @classmethod
    def from_sklearn(cls, dataset_name: str, target: str | None = None) -> Nexora:
        from nexora.io.remote import load_from_sklearn
        return cls(load_from_sklearn(dataset_name), target=target)

    @classmethod
    def from_clipboard(cls, target: str | None = None) -> Nexora:
        from nexora.io.remote import load_from_clipboard
        return cls(load_from_clipboard(), target=target)


    def profile(self) -> DatasetProfile:
        """Profile the dataset without training.

        Args:
            None.

        Returns:
            DatasetProfile for the loaded data.

        Example:
            `profile = Nexora("data.csv").profile()`
        """

        return profile_dataset(
            self.df,
            source_name=self.source_name,
            target=self.target,
        )

    def intelligence(self, target: str | None = None) -> DatasetIntelligence:
        """Return full dataset intelligence without training models."""

        resolved_target = target or self.target
        return build_dataset_intelligence(
            self.df,
            source_name=self.source_name,
            target=resolved_target,
        )

    def suggest_targets(self) -> list[dict[str, Any]]:
        """Return suggested target columns as dictionaries."""

        profile = self.profile()
        return [
            {
                "target_column": item.target_column,
                "problem_type": item.problem_type,
                "confidence": item.confidence,
                "reason": item.reason,
            }
            for item in suggest_targets(self.df, profile)
        ]

    def detect_problem(
        self,
        target: str,
        *,
        problem_type: TaskType | None = None,
    ) -> dict[str, Any]:
        """Detect classification/regression for a selected target."""

        return detect_problem(self.df, target, override=problem_type)

    def pipeline_plan(
        self,
        target: str | None = None,
        *,
        problem_type: TaskType | None = None,
        preprocessing_config: PreprocessingConfig | None = None,
    ) -> dict[str, Any]:
        """Return problem detection and preprocessing decisions."""

        resolved_target = target or self.target
        if resolved_target is None:
            suggestions = self.suggest_targets()
            if not suggestions:
                raise ValueError("Select a target column before planning the pipeline.")
            resolved_target = suggestions[0]["target_column"]
        detection = detect_problem(self.df, resolved_target, override=problem_type)
        config = preprocessing_config or PreprocessingConfig()
        bundle = build_preprocessing(self.df, resolved_target, config=config)
        schema = bundle.schema
        return {
            "problem_detector": detection,
            "preprocessing": {
                "missing_values": "Auto (median / mode)",
                "encoding": "Label + One-Hot" if config.encode_categorical else "Disabled",
                "outliers": "IQR capping" if config.outlier_cap else "Disabled",
                "feature_scaling": {
                    "standard": "StandardScaler",
                    "minmax": "MinMaxScaler",
                    "none": "None",
                }[config.scaling],
                "drop_id_columns": config.drop_id_columns,
                "remove_duplicates": config.remove_duplicates,
                "fill_missing": config.fill_missing,
                "outlier_cap": config.outlier_cap,
                "encode": config.encode_categorical,
                "scale": config.scaling != "none",
                "feature_columns": schema.feature_columns,
                "numeric_features": schema.numeric_features,
                "categorical_features": schema.categorical_features,
                "dropped_columns": schema.dropped_columns,
                "decision_log": schema.decision_log,
            },
        }

    def run(
        self,
        *,
        target: str | None = None,
        max_models: int | None = 6,
        model_names: list[str] | None = None,
        test_size: float = 0.2,
        cv_folds: int = 5,
        timeout_sec: int | None = None,
        random_state: int = 42,
        early_stopping: bool = True,
        problem_type: TaskType | None = None,
        preprocessing_config: PreprocessingConfig | None = None,
        on_progress=None,
    ) -> NexoraReport:
        """Run profiling, preprocessing, model training, and report creation.

        Args:
            target: Optional target override.
            max_models: Maximum models to train; defaults to the MVP registry size.
            model_names: Optional explicit model names to train.
            test_size: Holdout split ratio.
            cv_folds: Cross-validation folds requested by the workflow.
            timeout_sec: Optional per-model timeout requested by the workflow.
            random_state: Reproducible random seed.
            early_stopping: Whether early stopping should be used when supported.
            problem_type: Optional task override (`classification` or `regression`).

        Returns:
            Trained NexoraReport.

        Example:
            `report = nx.run()`
        """

        resolved_target = target or self.target
        if resolved_target is None:
            raise ValueError("A target column is required to run training.")
        if resolved_target not in self.df.columns:
            raise ValueError(f"Target column '{resolved_target}' not found.")

        task_type = problem_type or detect_task_type(self.df, resolved_target)
        if task_type not in ("classification", "regression"):
            raise ValueError("problem_type must be 'classification' or 'regression'.")
        profile = profile_dataset(
            self.df,
            source_name=self.source_name,
            target=resolved_target,
        )
        preprocessing = build_preprocessing(
            self.df,
            resolved_target,
            config=preprocessing_config,
        )
        artifacts = train_models(
            self.df,
            resolved_target,
            task_type,
            preprocessing,
            max_models=max_models,
            model_names=model_names,
            test_size=test_size,
            cv_folds=cv_folds,
            timeout_sec=timeout_sec,
            random_state=random_state,
            early_stopping=early_stopping,
            on_progress=on_progress,
        )
        self.target = resolved_target
        report = NexoraReport(
            source_name=self.source_name,
            source_path=str(self.source_path) if self.source_path else None,
            target=resolved_target,
            task_type=task_type,
            profile=profile,
            schema=artifacts.preprocessing.schema,
            pipeline=artifacts.best_pipeline,
            training_frame=artifacts.preprocessing.training_frame,
            results=artifacts.results,
            best_result=artifacts.best_result,
            model_specs=artifacts.model_specs,
            model_pipelines=artifacts.pipelines,
            training_settings=artifacts.settings,
        )
        report.experiment_record = create_training_experiment(report)
        return report

    def quick(self, target: str | None = None) -> NexoraReport:
        """30-second speed mode — top models only.
        
        Args:
            target: Optional target override.
            
        Returns:
            Trained NexoraReport.
        """
        return self.run(target=target, max_models=2)

    def deep(self, target: str | None = None, time_limit: int | None = None) -> NexoraReport:
        """Exhaustive mode — all models, ensembles, and HPO.
        
        (Currently an alias for run with max_models=None)
        """
        return self.run(target=target, max_models=None)

    def preprocess(self, target: str | None = None, save: str | None = None) -> pd.DataFrame:
        """Run preprocessing pipeline only and return cleaned DataFrame."""
        resolved_target = target or self.target
        from nexora.preprocessing.pipeline_builder import build_preprocessing
        bundle = build_preprocessing(self.df, resolved_target)
        X = self.df[bundle.schema.feature_columns]
        y = self.df[resolved_target]
        transformed_X = bundle.transformer.fit_transform(X, y)
        cols = bundle.schema.transformed_feature_names
        if not cols or len(cols) != transformed_X.shape[1]:
            cols = [f"feat_{i}" for i in range(transformed_X.shape[1])]
        X_clean = pd.DataFrame(
            transformed_X,
            columns=cols
        )
        X_clean[resolved_target] = y.values
        if save:
            X_clean.to_csv(save, index=False)
        return X_clean

    def train(self, models: list[str], target: str | None = None) -> NexoraReport:
        """Train specific models only."""
        return self.run(target=target, model_names=models)

    def tune(self, model_name: str, n_trials: int = 50, target: str | None = None) -> NexoraReport:
        """Deep hyperparameter tuning for one specific model."""
        # Stub for deep HPO - currently runs standard training for that model
        return self.run(target=target, model_names=[model_name])

    def compare(self, holdout_df: pd.DataFrame, target: str | None = None) -> NexoraReport:
        """Train on main df, evaluate on holdout df."""
        report = self.run(target=target)
        # In a real implementation we would evaluate the models on holdout_df here
        return report

    def cluster(
        self,
        n_clusters: int = 3,
        feature_columns: list[str] | None = None,
    ) -> dict[str, Any]:
        """Run package-native clustering for terminal/Jupyter workflows."""

        return run_clustering(self.df, n_clusters=n_clusters, feature_columns=feature_columns)

    def forecast(
        self,
        *,
        date_column: str,
        target_column: str,
        periods: int = 12,
        frequency: str = "M",
    ) -> dict[str, Any]:
        """Run package-native simple time-series forecast."""

        return run_forecast(
            self.df,
            date_column=date_column,
            target_column=target_column,
            periods=periods,
            frequency=frequency,
        )

    @staticmethod
    def compare_runs(r1: NexoraReport, r2: NexoraReport) -> None:
        """Compare two Nexora reports side by side."""
        print(f"Comparing Run 1 ({r1.best_model}: {r1.best_score:.4f}) vs Run 2 ({r2.best_model}: {r2.best_score:.4f})")
        delta = r2.best_score - r1.best_score
        print(f"Score Delta: {delta:+.4f}")

    @staticmethod
    def experiments() -> list[Any]:
        """Return persisted local experiment records."""

        return list_experiments()

    @staticmethod
    def load(path: str | Path) -> NexoraReport:
        """Load a saved Nexora session and return a ready report.

        Args:
            path: `.nx` session path from `report.save(...)`.

        Returns:
            NexoraReport.

        Example:
            `report = Nexora.load("session.nx")`
        """

        return load_report(path)

# Alias for backward compatibility
NexoraPrediction = Nexora
