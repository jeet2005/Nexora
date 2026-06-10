"""Dataset profiling heuristics ported from the Nexora web backend."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from nexora.types import ColumnProfile, DatasetProfile, HealthScore


def is_id_like(series: pd.Series) -> bool:
    """Detect identifier-like columns that should not be model features.

    Args:
        series: Column to inspect.

    Returns:
        True when the column appears to be an identifier.

    Example:
        `is_id_like(df["customer_id"])`
    """

    name = str(series.name).lower().strip()
    if name in {"id", "index", "uuid", "row_id", "record_id", "key"}:
        return True
    if name.endswith("_id") or name.startswith("id_"):
        return True
    if "uuid" in name or "guid" in name:
        return True
    if series.dtype in ("int64", "int32", "object") and "id" in name.replace("_", ""):
        nunique = series.nunique(dropna=True)
        return nunique >= len(series) * 0.95
    return False


def infer_datetime(series: pd.Series) -> bool:
    """Infer whether a column behaves like datetime data.

    Args:
        series: Column to inspect.

    Returns:
        True when values are datetime-like.

    Example:
        `infer_datetime(df["created_at"])`
    """

    if pd.api.types.is_datetime64_any_dtype(series):
        return True
    if series.dtype == object:
        sample = series.dropna().head(20)
        if sample.empty:
            return False
        parsed = pd.to_datetime(sample, errors="coerce", format="mixed")
        return bool(parsed.notna().mean() > 0.8)
    return False


def profile_dataset(
    df: pd.DataFrame,
    *,
    source_name: str = "dataset",
    target: str | None = None,
) -> DatasetProfile:
    """Profile a dataframe for data quality, feature types, and model readiness.

    Args:
        df: DataFrame to profile.
        source_name: Human-readable dataset name.
        target: Optional prediction target.

    Returns:
        DatasetProfile with health score and per-column details.

    Example:
        `profile = profile_dataset(df, source_name="sales.csv", target="revenue")`
    """

    if df.empty:
        raise ValueError("Cannot profile an empty dataframe.")

    column_profiles = [_profile_column(df[col], len(df)) for col in df.columns]
    stats = _compute_stats(df, column_profiles)
    health = _health_score(df, column_profiles, target)
    return DatasetProfile(
        source_name=source_name,
        row_count=len(df),
        column_count=len(df.columns),
        duplicate_rows=int(df.duplicated().sum()),
        memory_mb=round(df.memory_usage(deep=True).sum() / (1024 * 1024), 3),
        target=target,
        column_profiles=column_profiles,
        stats=stats,
        health=health,
        semantic_summary=_semantic_summary(df, column_profiles),
    )


def _profile_column(series: pd.Series, row_count: int) -> ColumnProfile:
    missing = int(series.isna().sum())
    unique = int(series.nunique(dropna=True))
    is_dt = infer_datetime(series)
    is_num = bool(
        pd.api.types.is_numeric_dtype(series) 
        and not is_dt 
        and not pd.api.types.is_bool_dtype(series)
    )
    is_cat = bool(not is_num and not is_dt and unique < max(50, row_count * 0.5))

    samples: list[Any] = []
    for value in series.dropna().head(3):
        if isinstance(value, (np.integer, np.floating)):
            samples.append(float(value) if np.isfinite(value) else None)
        elif isinstance(value, (pd.Timestamp, np.datetime64)):
            samples.append(str(value))
        else:
            samples.append(str(value)[:80])

    return ColumnProfile(
        name=str(series.name),
        dtype=str(series.dtype),
        missing_count=missing,
        missing_pct=round(100 * missing / row_count, 2) if row_count else 0.0,
        unique_count=unique,
        is_numeric=is_num,
        is_categorical=is_cat,
        is_datetime=is_dt,
        is_id_like=is_id_like(series),
        sample_values=samples,
    )


def _safe_float(value: Any) -> float | None:
    if value is None or (isinstance(value, float) and not np.isfinite(value)):
        return None
    try:
        out = float(value)
    except (TypeError, ValueError):
        return None
    return round(out, 4) if np.isfinite(out) else None


def _compute_stats(
    df: pd.DataFrame, profiles: list[ColumnProfile]
) -> dict[str, dict[str, Any]]:
    numeric_cols = [profile.name for profile in profiles if profile.is_numeric]
    if not numeric_cols:
        return {
            "mean": {},
            "median": {},
            "std": {},
            "skewness": {},
            "correlation": {},
            "outlier_counts": {},
        }

    numeric = df[numeric_cols].apply(pd.to_numeric, errors="coerce")
    stats: dict[str, dict[str, Any]] = {
        "mean": {col: _safe_float(numeric[col].mean()) for col in numeric_cols},
        "median": {col: _safe_float(numeric[col].median()) for col in numeric_cols},
        "std": {col: _safe_float(numeric[col].std()) for col in numeric_cols},
        "skewness": {col: _safe_float(numeric[col].skew()) for col in numeric_cols},
        "correlation": {},
        "outlier_counts": {},
    }

    if len(numeric_cols) >= 2:
        corr = numeric.corr()
        stats["correlation"] = {
            row: {col: _safe_float(corr.loc[row, col]) for col in numeric_cols}
            for row in numeric_cols
        }

    for col in numeric_cols:
        clean = numeric[col].dropna()
        if len(clean) < 4:
            stats["outlier_counts"][col] = 0
            continue
        q1, q3 = clean.quantile(0.25), clean.quantile(0.75)
        iqr = q3 - q1
        if iqr == 0:
            stats["outlier_counts"][col] = 0
            continue
        low, high = q1 - 1.5 * iqr, q3 + 1.5 * iqr
        stats["outlier_counts"][col] = int(((clean < low) | (clean > high)).sum())

    return stats


def _health_score(
    df: pd.DataFrame, profiles: list[ColumnProfile], target: str | None
) -> HealthScore:
    n_cells = max(len(df) * len(df.columns), 1)
    missing_pct = sum(profile.missing_count for profile in profiles) / n_cells
    missing_score = int(max(0, 100 - missing_pct * 200))

    duplicate_pct = df.duplicated().sum() / max(len(df), 1)
    quality_score = int(max(0, 100 - duplicate_pct * 150))

    usable_features = sum(
        1
        for profile in profiles
        if profile.name != target
        and not profile.is_id_like
        and not profile.is_datetime
        and profile.unique_count > 1
    )
    readiness = min(100, 40 + usable_features * 12)

    constant_cols = sum(profile.unique_count <= 1 for profile in profiles)
    feature_score = int(max(0, 100 - constant_cols * 15))

    overall = int(
        0.25 * missing_score
        + 0.25 * quality_score
        + 0.3 * readiness
        + 0.2 * feature_score
    )
    return HealthScore(
        missing_values=missing_score,
        data_quality=quality_score,
        prediction_readiness=readiness,
        feature_quality=feature_score,
        overall=overall,
    )


def _semantic_summary(df: pd.DataFrame, profiles: list[ColumnProfile]) -> str:
    names = [profile.name.lower() for profile in profiles]
    themes: list[str] = []
    if any("churn" in name or "customer" in name for name in names):
        themes.append("customer behavior")
    if any("price" in name or "amount" in name or "revenue" in name for name in names):
        themes.append("financial outcomes")
    if any("date" in name or "time" in name for name in names) or any(
        profile.is_datetime for profile in profiles
    ):
        themes.append("temporal patterns")

    numeric_count = sum(profile.is_numeric for profile in profiles)
    categorical_count = sum(profile.is_categorical for profile in profiles)
    base = (
        f"This dataset contains {len(df):,} rows and {len(profiles)} columns "
        f"({numeric_count} numeric, {categorical_count} categorical)."
    )
    if not themes:
        return base
    return f"{base} It appears to include {', '.join(themes)}."
