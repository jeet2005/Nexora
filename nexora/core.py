"""Main Nexora entry point."""

from __future__ import annotations

from pathlib import Path

from nexora.io.loaders import load_source
from nexora.io.serializer import load_report
from nexora.models.task_detector import detect_task_type
from nexora.models.trainer import train_models
from nexora.preprocessing.pipeline_builder import build_preprocessing
from nexora.profiler.dataset_profile import profile_dataset
from nexora.report import NexoraReport
from nexora.types import DatasetProfile, LoadedData


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
    def from_url(cls, url: str, target: str | None = None) -> "Nexora":
        from nexora.io.remote import load_from_url
        return cls(load_from_url(url), target=target)

    @classmethod
    def from_sql(cls, query: str, connection_string: str | None = None, target: str | None = None) -> "Nexora":
        from nexora.io.remote import load_from_sql
        return cls(load_from_sql(query, connection_string), target=target)

    @classmethod
    def from_postgres(cls, uri: str, table: str, target: str | None = None) -> "Nexora":
        from nexora.io.remote import load_from_postgres
        return cls(load_from_postgres(uri, table), target=target)

    @classmethod
    def from_mongodb(cls, uri: str, collection: str, target: str | None = None) -> "Nexora":
        from nexora.io.remote import load_from_mongodb
        return cls(load_from_mongodb(uri, collection), target=target)

    @classmethod
    def from_s3(cls, bucket: str, key: str, target: str | None = None) -> "Nexora":
        from nexora.io.remote import load_from_s3
        return cls(load_from_s3(bucket, key), target=target)

    @classmethod
    def from_google_sheets(cls, sheet_id: str, target: str | None = None) -> "Nexora":
        from nexora.io.remote import load_from_google_sheets
        return cls(load_from_google_sheets(sheet_id), target=target)

    @classmethod
    def from_sklearn(cls, dataset_name: str, target: str | None = None) -> "Nexora":
        from nexora.io.remote import load_from_sklearn
        return cls(load_from_sklearn(dataset_name), target=target)

    @classmethod
    def from_clipboard(cls, target: str | None = None) -> "Nexora":
        from nexora.io.remote import load_from_clipboard
        return cls(load_from_clipboard(), target=target)

    @classmethod
    def load(cls, path: str | Path) -> "NexoraReport":
        from nexora.io.serializer import load_report
        return load_report(path)

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

    def run(
        self,
        *,
        target: str | None = None,
        max_models: int | None = 6,
        model_names: list[str] | None = None,
        test_size: float = 0.2,
        random_state: int = 42,
    ) -> NexoraReport:
        """Run profiling, preprocessing, model training, and report creation.

        Args:
            target: Optional target override.
            max_models: Maximum models to train; defaults to the MVP registry size.
            model_names: Optional explicit model names to train.
            test_size: Holdout split ratio.
            random_state: Reproducible random seed.

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

        task_type = detect_task_type(self.df, resolved_target)
        profile = profile_dataset(
            self.df,
            source_name=self.source_name,
            target=resolved_target,
        )
        preprocessing = build_preprocessing(self.df, resolved_target)
        artifacts = train_models(
            self.df,
            resolved_target,
            task_type,
            preprocessing,
            max_models=max_models,
            model_names=model_names,
            test_size=test_size,
            random_state=random_state,
        )
        self.target = resolved_target
        return NexoraReport(
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
        )

    def quick(self, target: str | None = None) -> NexoraReport:
        """30-second speed mode — top models only.
        
        Args:
            target: Optional target override.
            
        Returns:
            Trained NexoraReport.
        """
        return self.run(target=target, max_models=2)

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
