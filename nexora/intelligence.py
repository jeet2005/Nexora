"""Dataset intelligence helpers for the CSV-first Nexora workflow."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from nexora.models.task_detector import detect_task_type
from nexora.profiler.dataset_profile import profile_dataset
from nexora.types import (
    ColumnIntelligence,
    DatasetIntelligence,
    DatasetProfile,
    ModelReadiness,
    OutlierSignal,
    RelationshipSignal,
    TargetSuggestion,
    TaskType,
)

TARGET_NAME_HINTS = {
    "target",
    "label",
    "class",
    "churn",
    "fraud",
    "default",
    "spam",
    "outcome",
    "result",
    "status",
    "converted",
    "conversion",
    "clicked",
    "approved",
    "education",
}

REGRESSION_NAME_HINTS = {
    "price",
    "revenue",
    "sales",
    "amount",
    "cost",
    "value",
    "score",
    "rating",
    "income",
    "profit",
    "quantity",
    "duration",
}


def build_dataset_intelligence(
    df: pd.DataFrame,
    *,
    source_name: str = "dataset",
    target: str | None = None,
    preview_rows: int = 5,
) -> DatasetIntelligence:
    """Build the full dataset intelligence object from a dataframe."""

    profile = profile_dataset(df, source_name=source_name, target=target)
    return intelligence_from_profile(df, profile, preview_rows=preview_rows)


def intelligence_from_profile(
    df: pd.DataFrame,
    profile: DatasetProfile,
    *,
    preview_rows: int = 5,
) -> DatasetIntelligence:
    """Create dataset intelligence from an existing profile."""

    preview = _preview_records(df, preview_rows)
    return DatasetIntelligence(
        profile=profile,
        preview=preview,
        data_quality_scorecard={
            "overall": profile.health.overall,
            "missing_values": profile.health.missing_values,
            "data_quality": profile.health.data_quality,
            "prediction_readiness": profile.health.prediction_readiness,
            "feature_quality": profile.health.feature_quality,
        },
        suggested_targets=suggest_targets(df, profile),
        model_readiness=model_readiness(df, profile, profile.target),
        column_intelligence=column_intelligence(df, profile),
        strongest_relationships=strongest_relationships(profile),
        outlier_signals=outlier_signals(df, profile),
        numeric_distributions=numeric_distributions(df, profile),
        categorical_distributions=categorical_distributions(df, profile),
    )


def suggest_targets(
    df: pd.DataFrame,
    profile: DatasetProfile,
    *,
    limit: int = 6,
) -> list[TargetSuggestion]:
    """Suggest likely target columns and problem types."""

    suggestions: list[TargetSuggestion] = []
    last_column = str(df.columns[-1]) if len(df.columns) else ""

    for column in profile.column_profiles:
        if column.is_id_like or column.is_datetime or column.unique_count < 2:
            continue
        if not column.is_numeric and column.unique_count > max(50, len(df) * 0.95):
            continue

        name = column.name
        lower = name.lower()
        task = _target_task(df, name, column.is_categorical, column.unique_count)
        confidence = 0.58
        reasons: list[str] = []

        if any(hint in lower for hint in TARGET_NAME_HINTS):
            confidence += 0.28
            reasons.append("name suggests an outcome")
        if (
            any(hint in lower for hint in REGRESSION_NAME_HINTS)
            and task == "regression"
        ):
            confidence += 0.16
            reasons.append("numeric business metric")
        if name == last_column:
            confidence += 0.08
            reasons.append("last-column convention")
        if task == "classification" and 2 <= column.unique_count <= 20:
            confidence += 0.08
            reasons.append(f"{column.unique_count} classes")
        if task == "regression" and column.is_numeric:
            confidence += 0.08
            reasons.append("continuous numeric values")

        if not reasons:
            reasons.append(f"{task} candidate")

        suggestions.append(
            TargetSuggestion(
                target_column=name,
                problem_type=task,
                confidence=round(min(confidence, 0.98), 2),
                reason=", ".join(reasons),
            )
        )

    suggestions.sort(key=lambda item: item.confidence, reverse=True)
    return suggestions[:limit]


def model_readiness(
    df: pd.DataFrame,
    profile: DatasetProfile,
    target: str | None = None,
) -> ModelReadiness:
    """Recommend useful model families and explain readiness."""

    rows = len(df)
    usable = [
        column
        for column in profile.column_profiles
        if column.name != target
        and not column.is_id_like
        and not column.is_datetime
        and column.unique_count > 1
    ]
    numeric = [column for column in usable if column.is_numeric]
    categorical = [column for column in usable if column.is_categorical]
    missing_pct = profile.missing_cells / max(rows * max(len(df.columns), 1), 1)

    score = profile.health.prediction_readiness
    if rows < 30:
        score = min(score, 45)
    elif rows >= 500:
        score = min(100, score + 8)
    if not usable:
        score = 0

    warnings: list[str] = []
    reasons: list[str] = [
        f"{len(usable)} usable feature columns detected",
        f"{rows:,} rows available for training",
    ]
    if missing_pct > 0.2:
        warnings.append(
            "More than 20% of cells are missing; imputation may dominate signal."
        )
    if rows < 30:
        warnings.append(
            "Very small dataset; prefer simple models and validate carefully."
        )
    if len(categorical) > len(numeric) * 2 and categorical:
        reasons.append("categorical-heavy data; encoding-aware models are useful")
    if numeric:
        reasons.append(
            f"{len(numeric)} numeric feature(s) support scaling and linear/tree models"
        )

    families = ["baseline"]
    if numeric:
        families.append("linear")
    if usable:
        families.extend(["tree", "ensemble"])
    if rows >= 100 and usable:
        families.append("boosting")
    if rows >= 300 and len(usable) >= 3:
        families.append("neighbors")
    if rows >= 5000 and len(usable) >= 8:
        families.append("neural")

    if score >= 80:
        status = "ready"
    elif score >= 55:
        status = "usable with caution"
    elif score > 0:
        status = "limited"
    else:
        status = "blocked"

    return ModelReadiness(
        score=int(max(0, min(100, score))),
        status=status,
        recommended_families=_dedupe(families),
        reasons=reasons,
        warnings=warnings,
    )


def strongest_relationships(
    profile: DatasetProfile,
    *,
    limit: int = 8,
) -> list[RelationshipSignal]:
    """Return strongest pairwise numeric correlations."""

    correlations = profile.stats.get("correlation", {})
    pairs: list[RelationshipSignal] = []
    seen: set[frozenset[str]] = set()
    for left, cols in correlations.items():
        for right, value in cols.items():
            key = frozenset({left, right})
            if left == right or key in seen or value is None:
                continue
            seen.add(key)
            absolute = abs(float(value))
            if absolute >= 0.7:
                strength = "strong"
            elif absolute >= 0.4:
                strength = "moderate"
            else:
                strength = "weak"
            pairs.append(
                RelationshipSignal(
                    feature_a=left,
                    feature_b=right,
                    correlation=round(float(value), 4),
                    strength=strength,
                )
            )
    pairs.sort(key=lambda item: abs(item.correlation), reverse=True)
    return pairs[:limit]


def outlier_signals(df: pd.DataFrame, profile: DatasetProfile) -> list[OutlierSignal]:
    """Return IQR outlier signals."""

    signals: list[OutlierSignal] = []
    for column, count in profile.stats.get("outlier_counts", {}).items():
        if count:
            signals.append(
                OutlierSignal(
                    column=column,
                    count=int(count),
                    percentage=round(100 * int(count) / max(len(df), 1), 2),
                )
            )
    signals.sort(key=lambda item: item.count, reverse=True)
    return signals


def numeric_distributions(
    df: pd.DataFrame,
    profile: DatasetProfile,
) -> dict[str, dict[str, float | None]]:
    """Return numeric percentile summaries by column."""

    output: dict[str, dict[str, float | None]] = {}
    for column in profile.column_profiles:
        if not column.is_numeric:
            continue
        series = pd.to_numeric(df[column.name], errors="coerce").dropna()
        if series.empty:
            output[column.name] = {
                key: None
                for key in (
                    "min",
                    "p5",
                    "p25",
                    "p50",
                    "p75",
                    "p95",
                    "max",
                    "mean",
                    "std",
                )
            }
            continue
        quantiles = series.quantile([0, 0.05, 0.25, 0.5, 0.75, 0.95, 1.0])
        output[column.name] = {
            "min": _safe_float(quantiles.loc[0]),
            "p5": _safe_float(quantiles.loc[0.05]),
            "p25": _safe_float(quantiles.loc[0.25]),
            "p50": _safe_float(quantiles.loc[0.5]),
            "p75": _safe_float(quantiles.loc[0.75]),
            "p95": _safe_float(quantiles.loc[0.95]),
            "max": _safe_float(quantiles.loc[1.0]),
            "mean": _safe_float(series.mean()),
            "std": _safe_float(series.std()),
        }
    return output


def categorical_distributions(
    df: pd.DataFrame,
    profile: DatasetProfile,
    *,
    limit: int = 8,
) -> dict[str, list[dict[str, Any]]]:
    """Return top categorical values by column."""

    output: dict[str, list[dict[str, Any]]] = {}
    for column in profile.column_profiles:
        if not column.is_categorical or column.is_id_like:
            continue
        counts = (
            df[column.name]
            .astype("string")
            .fillna("<missing>")
            .value_counts()
            .head(limit)
        )
        output[column.name] = [
            {
                "value": str(value),
                "count": int(count),
                "percentage": round(100 * int(count) / max(len(df), 1), 2),
            }
            for value, count in counts.items()
        ]
    return output


def column_intelligence(
    df: pd.DataFrame,
    profile: DatasetProfile,
) -> list[ColumnIntelligence]:
    """Return per-column role, quality, and modeling guidance."""

    rows: list[ColumnIntelligence] = []
    for column in profile.column_profiles:
        warnings: list[str] = []
        quality = 100
        quality -= min(60, int(column.missing_pct))
        if column.unique_count <= 1:
            quality -= 35
            warnings.append("constant value")
        if column.missing_pct >= 30:
            warnings.append("high missingness")
        if column.is_id_like:
            role = "id"
            recommendation = "Drop from model features to avoid memorization."
        elif column.is_datetime:
            role = "datetime"
            recommendation = "Use calendar-derived features when time context matters."
        elif column.is_numeric:
            role = "numeric"
            recommendation = "Impute with median, cap extreme outliers, and scale for distance/linear models."
        elif column.is_categorical:
            role = "categorical"
            recommendation = (
                "Impute with mode and encode with one-hot or label encoding."
            )
        else:
            role = "text"
            recommendation = (
                "Treat as free text or exclude until text embeddings are enabled."
            )

        if column.is_id_like:
            quality = min(quality, 60)
        if column.unique_count > max(50, len(df) * 0.75) and not column.is_numeric:
            warnings.append("high cardinality")

        rows.append(
            ColumnIntelligence(
                name=column.name,
                role=role,
                quality_score=max(0, min(100, quality)),
                recommendation=recommendation,
                warnings=warnings,
            )
        )
    return rows


def detect_problem(
    df: pd.DataFrame,
    target: str,
    override: TaskType | None = None,
) -> dict[str, Any]:
    """Detect or override problem type with confidence and human hints."""

    if target not in df.columns:
        raise ValueError(f"Target column '{target}' not found.")

    detected = detect_task_type(df, target)
    problem_type = override or detected
    unique = int(df[target].nunique(dropna=True))
    y = df[target].dropna()
    is_numeric = pd.api.types.is_numeric_dtype(y)

    if override is not None and override != detected:
        confidence = 0.65
        hint = f"User override from detected {detected}."
    elif problem_type == "classification":
        confidence = 0.95 if unique <= 5 else (0.86 if unique <= 20 else 0.72)
        hint = f"Categorical target with {unique} classes."
    else:
        confidence = 0.92 if is_numeric and unique > 20 else 0.78
        hint = f"Continuous numeric target with {unique} unique values."

    features = [
        column
        for column in df.columns
        if column != target and df[column].nunique(dropna=True) > 1
    ]
    return {
        "problem_type": problem_type,
        "confidence": round(confidence, 2),
        "target_column": target,
        "unique_values": unique,
        "feature_count": len(features),
        "hints": [hint],
    }


def _target_task(
    df: pd.DataFrame,
    column: str,
    is_categorical: bool,
    unique_count: int,
) -> TaskType:
    try:
        return detect_task_type(df, column)
    except ValueError:
        if is_categorical or unique_count <= 20:
            return "classification"
        return "regression"


def _preview_records(df: pd.DataFrame, rows: int) -> list[dict[str, Any]]:
    preview = df.head(rows).replace({np.nan: None})
    return [
        {str(key): _json_ready(value) for key, value in row.items()}
        for row in preview.to_dict(orient="records")
    ]


def _json_ready(value: Any) -> Any:
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        return None if not np.isfinite(value) else float(value)
    if isinstance(value, (pd.Timestamp, np.datetime64)):
        return str(value)
    return value


def _safe_float(value: Any) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return round(number, 4) if np.isfinite(number) else None


def _dedupe(items: list[str]) -> list[str]:
    seen: set[str] = set()
    output: list[str] = []
    for item in items:
        if item not in seen:
            seen.add(item)
            output.append(item)
    return output
