"""Typed internal objects used by the Nexora MVP package."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from importlib import import_module
from pathlib import Path
from typing import Any, Literal

import pandas as pd

TaskType = Literal["classification", "regression"]


@dataclass(frozen=True)
class LoadedData:
    """A loaded tabular dataset and source metadata."""

    dataframe: pd.DataFrame
    source_path: Path | None
    source_name: str


@dataclass(frozen=True)
class ColumnProfile:
    """Profile information for one dataframe column."""

    name: str
    dtype: str
    missing_count: int
    missing_pct: float
    unique_count: int
    is_numeric: bool
    is_categorical: bool
    is_datetime: bool
    is_id_like: bool
    sample_values: list[Any] = field(default_factory=list)


@dataclass(frozen=True)
class HealthScore:
    """Dataset health score components."""

    missing_values: int
    data_quality: int
    prediction_readiness: int
    feature_quality: int
    overall: int


@dataclass(frozen=True)
class DatasetProfile:
    """Dataset profile returned by `Nexora.profile()` and `report.profile`.

    Args:
        source_name: Filename or logical dataset name.
        row_count: Number of rows.
        column_count: Number of columns.

    Returns:
        A typed dataset profile with tabular column details.

    Example:
        `profile.health_score`
    """

    source_name: str
    row_count: int
    column_count: int
    duplicate_rows: int
    memory_mb: float
    target: str | None
    column_profiles: list[ColumnProfile]
    stats: dict[str, Any]
    health: HealthScore
    semantic_summary: str

    @property
    def rows(self) -> int:
        """Number of rows in the profiled dataset."""

        return self.row_count

    # Compatibility aliases for legacy code and tests
    @property
    def num_rows(self) -> int:
        """Alias for rows (used in tests)."""
        return self.row_count

    @property
    def num_columns(self) -> int:
        """Alias for column_count (used in publishing)."""
        return self.column_count

    @property
    def missing_cells(self) -> int:
        """Total missing cells across all columns."""
        return sum(c.missing_count for c in self.column_profiles)

    @property
    def health_score(self) -> int:
        """Overall health score from 0 to 100."""

        return self.health.overall

    @property
    def columns(self) -> pd.DataFrame:
        """Column profile table as a pandas DataFrame."""

        return pd.DataFrame(asdict(col) for col in self.column_profiles)


@dataclass
class PreprocessingSchema:
    """Dataset-specific preprocessing decisions."""

    target: str
    feature_columns: list[str]
    numeric_features: list[str]
    categorical_features: list[str]
    dropped_columns: list[str]
    id_columns: list[str]
    datetime_columns: list[str]
    constant_columns: list[str]
    decision_log: dict[str, str] = field(default_factory=dict)
    transformed_feature_names: list[str] = field(default_factory=list)


@dataclass
class PreprocessingBundle:
    """An unfitted sklearn preprocessor plus the dataframe it was planned from."""

    transformer: Any
    schema: PreprocessingSchema
    training_frame: pd.DataFrame


@dataclass(frozen=True)
class ModelSpec:
    """Definition for a trainable model in the MVP registry."""

    model_id: str
    model_name: str
    family: str
    task_type: TaskType
    import_path: str
    class_name: str
    params: dict[str, Any] = field(default_factory=dict)
    speed: str = "fast"
    min_samples: int = 10
    max_samples: int | None = None

    def factory(self) -> Any:
        """Create a fresh estimator instance."""

        module = import_module(self.import_path)
        cls = getattr(module, self.class_name)
        return cls(**self.params)

    def matches(self, name: str) -> bool:
        """Return True if `name` identifies this model."""

        normalized = name.strip().casefold()
        return normalized in {
            self.model_id.casefold(),
            self.model_name.casefold(),
            self.class_name.casefold(),
        }


@dataclass(frozen=True)
class ModelResult:
    """Training result for one model."""

    model_id: str
    model_name: str
    family: str
    status: str
    primary_metric: str
    primary_score: float
    metrics: dict[str, float] = field(default_factory=dict)
    train_time_sec: float = 0.0
    speed: str = "fast"
    error: str | None = None


@dataclass
class TrainingArtifacts:
    """Artifacts produced by a completed Nexora training run."""

    task_type: TaskType
    target: str
    primary_metric: str
    results: list[ModelResult]
    best_result: ModelResult
    best_pipeline: Any
    model_specs: dict[str, ModelSpec]
    preprocessing: PreprocessingBundle
