import uuid
from typing import Any

import numpy as np
import pandas as pd

from app.config import settings
from app.models.schemas import (
    ColumnProfile,
    DatasetAnalysis,
    DatasetStats,
    HealthScore,
    ModelEligibilityFinding,
    PredictionSuggestion,
)


def _is_id_like(series: pd.Series) -> bool:
    name = str(series.name).lower().strip()
    if name in ("id", "index", "uuid", "row_id", "record_id", "key"):
        return True
    if name.endswith("_id") or name.startswith("id_"):
        return True
    if "uuid" in name or "guid" in name:
        return True
    # High-cardinality numeric only when the column name implies an identifier
    if series.dtype in ("int64", "int32", "object") and "id" in name.replace("_", ""):
        nunique = series.nunique(dropna=True)
        return nunique >= len(series) * 0.95
    return False


def _infer_datetime(series: pd.Series) -> bool:
    if pd.api.types.is_datetime64_any_dtype(series):
        return True

    sample = series.dropna().head(20)
    if len(sample) == 0:
        return False

    if series.dtype == object:
        parsed = pd.to_datetime(sample, errors="coerce", format="mixed")
        return parsed.notna().mean() > 0.8

    if pd.api.types.is_numeric_dtype(series):
        # Check if values look like Unix timestamps (seconds or milliseconds)
        # 946684800 = 2000-01-01, 2524608000 = 2050-01-01 (in seconds)
        is_seconds = sample.between(946684800, 2524608000).mean() > 0.8
        is_ms = sample.between(946684800000, 2524608000000).mean() > 0.8
        return is_seconds or is_ms

    return False


def _profile_columns(df: pd.DataFrame) -> list[ColumnProfile]:
    profiles: list[ColumnProfile] = []
    n = len(df)

    for col in df.columns:
        s = df[col]
        missing = int(s.isna().sum())
        nunique = int(s.nunique(dropna=True))
        is_dt = _infer_datetime(s)
        is_num = pd.api.types.is_numeric_dtype(s) and not is_dt
        is_cat = not is_num and not is_dt and nunique < max(50, n * 0.5)
        dtype = str(s.dtype)

        samples: list[Any] = []
        for v in s.dropna().head(3):
            if isinstance(v, (np.integer, np.floating)):
                samples.append(float(v) if np.isfinite(v) else None)
            elif isinstance(v, (pd.Timestamp, np.datetime64)):
                samples.append(str(v))
            else:
                samples.append(str(v)[:80])

        profiles.append(
            ColumnProfile(
                name=str(col),
                dtype=dtype,
                missing_count=missing,
                missing_pct=round(100 * missing / n, 2) if n else 0,
                unique_count=nunique,
                is_numeric=is_num,
                is_categorical=is_cat,
                is_datetime=is_dt,
                is_id_like=_is_id_like(s),
                sample_values=samples,
            )
        )
    return profiles


def _compute_stats(df: pd.DataFrame, profiles: list[ColumnProfile]) -> DatasetStats:
    numeric_cols = [p.name for p in profiles if p.is_numeric]
    stats = DatasetStats()

    if not numeric_cols:
        return stats

    num_df = df[numeric_cols].apply(pd.to_numeric, errors="coerce")
    bool_cols = [
        col for col in numeric_cols if pd.api.types.is_bool_dtype(df[col])]
    if bool_cols:
        num_df[bool_cols] = num_df[bool_cols].astype(float)
    stats.mean = {c: _safe_float(num_df[c].mean()) for c in numeric_cols}
    stats.median = {c: _safe_float(num_df[c].median()) for c in numeric_cols}
    stats.std = {c: _safe_float(num_df[c].std()) for c in numeric_cols}
    stats.skewness = {c: _safe_float(num_df[c].skew()) for c in numeric_cols}

    if len(numeric_cols) >= 2:
        corr = num_df.corr()
        stats.correlation = {
            r: {c: _safe_float(corr.loc[r, c]) for c in numeric_cols}
            for r in numeric_cols
        }

    for col in numeric_cols:
        s = num_df[col].dropna()
        if len(s) < 4:
            stats.outlier_counts[col] = 0
            continue
        q1, q3 = s.quantile(0.25), s.quantile(0.75)
        iqr = q3 - q1
        if iqr == 0:
            stats.outlier_counts[col] = 0
        else:
            low, high = q1 - 1.5 * iqr, q3 + 1.5 * iqr
            stats.outlier_counts[col] = int(((s < low) | (s > high)).sum())

    return stats


def _safe_float(v: Any) -> float | None:
    if v is None or (isinstance(v, float) and (np.isnan(v) or np.isinf(v))):
        return None
    try:
        return round(float(v), 4)
    except (TypeError, ValueError):
        return None


def _health_score(df: pd.DataFrame, profiles: list[ColumnProfile]) -> HealthScore:
    n_cells = max(len(df) * len(df.columns), 1)
    missing_pct = sum(p.missing_count for p in profiles) / n_cells
    missing_score = int(max(0, 100 - missing_pct * 200))

    dup_pct = df.duplicated().sum() / max(len(df), 1)
    quality_score = int(max(0, 100 - dup_pct * 150))

    usable_targets = sum(
        1
        for p in profiles
        if not p.is_id_like and not p.is_datetime and p.unique_count >= 2
    )
    readiness = min(100, 40 + usable_targets * 12)

    constant_cols = sum(1 for p in profiles if p.unique_count <= 1)
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


def _suggest_predictions(
    df: pd.DataFrame, profiles: list[ColumnProfile]
) -> list[PredictionSuggestion]:
    suggestions: list[PredictionSuggestion] = []

    for p in profiles:
        if p.is_id_like or p.is_datetime:
            continue
        if p.unique_count < 2:
            continue
        if not p.is_numeric and p.unique_count > len(df) * 0.95:
            continue

        col_lower = p.name.lower()
        if any(
            k in col_lower
            for k in ("churn", "fraud", "default", "spam", "target", "label")
        ):
            suggestions.append(
                PredictionSuggestion(
                    target_column=p.name,
                    problem_type="classification",
                    confidence=0.92,
                    description=f"Predict {p.name.replace('_', ' ')} — strong classification signal from column name.",
                )
            )
            continue

        if p.is_numeric and p.unique_count > 20:
            suggestions.append(
                PredictionSuggestion(
                    target_column=p.name,
                    problem_type="regression",
                    confidence=0.78,
                    description=f"Forecast continuous values for {p.name.replace('_', ' ')}.",
                )
            )
        elif p.is_categorical and 2 <= p.unique_count <= 30:
            suggestions.append(
                PredictionSuggestion(
                    target_column=p.name,
                    problem_type="classification",
                    confidence=0.85,
                    description=f"Classify {p.name.replace('_', ' ')} across {p.unique_count} categories.",
                )
            )

    suggestions.sort(key=lambda s: s.confidence, reverse=True)
    return suggestions[:6]


def _model_eligibility(
    df: pd.DataFrame,
    profiles: list[ColumnProfile],
    suggestions: list[PredictionSuggestion],
) -> list[ModelEligibilityFinding]:
    candidate_map = {
        "classification": [
            suggestion.target_column
            for suggestion in suggestions
            if suggestion.problem_type == "classification"
        ],
        "regression": [
            suggestion.target_column
            for suggestion in suggestions
            if suggestion.problem_type == "regression"
        ],
    }
    usable_columns = [
        profile.name
        for profile in profiles
        if not profile.is_id_like and profile.unique_count > 1
    ]
    enough_rows = len(df) >= 10
    enough_columns = len(usable_columns) >= 2
    base_blocker = (
        "At least 10 rows are required to train reliable saved models."
        if not enough_rows
        else "A target and at least one usable input column are required."
    )

    findings: list[ModelEligibilityFinding] = []
    for task, examples in (
        (
            "classification",
            ["Logistic Regression", "Random Forest", "Gradient Boosting"],
        ),
        (
            "regression",
            [
                "Linear Regression",
                "Random Forest Regressor",
                "Gradient Boosting Regressor",
            ],
        ),
    ):
        targets = candidate_map[task]
        eligible = enough_rows and enough_columns and bool(targets)
        if eligible:
            reason = (
                f"{len(targets)} suitable {task} target candidate"
                f"{'s' if len(targets) != 1 else ''} detected with usable input columns."
            )
        elif not targets:
            reason = f"No strong {task} target was detected automatically; you can still choose one manually."
        else:
            reason = base_blocker
        findings.append(
            ModelEligibilityFinding(
                task=task,
                eligible=eligible,
                reason=reason,
                target_candidates=targets,
                model_examples=examples if eligible else [],
            )
        )

    date_columns = [
        profile.name for profile in profiles if profile.is_datetime]
    numeric_columns = [
        profile.name for profile in profiles if profile.is_numeric]
    ts_targets = [c for c in numeric_columns if c not in date_columns]
    ts_eligible = bool(date_columns and ts_targets)
    time_reason = (
        f"Use Exploration Modes with date column "
        f"({date_columns[0]}) and numeric target for trend forecasting."
        if ts_eligible
        else (
            "Add a date/time column and numeric metric column to run forecasting in Exploration Modes."
            if not date_columns
            else "Add a numeric metric column alongside the detected date column for forecasting."
        )
    )
    findings.append(
        ModelEligibilityFinding(
            task="time-series forecasting",
            eligible=ts_eligible,
            reason=time_reason,
            target_candidates=ts_targets[:5] if ts_eligible else date_columns,
            model_examples=["Linear trend forecast"] if ts_eligible else [],
        )
    )
    findings.append(
        ModelEligibilityFinding(
            task="clustering",
            eligible=True,
            reason="Run K-Means segmentation in Exploration Modes on the Overview tab.",
            model_examples=["K-Means"],
        )
    )
    return findings


def _semantic_summary(df: pd.DataFrame, profiles: list[ColumnProfile]) -> str:
    names = [p.name.lower() for p in profiles]
    themes: list[str] = []

    if any("churn" in n or "customer" in n for n in names):
        themes.append("customer behavior")
    if any("price" in n or "amount" in n or "revenue" in n for n in names):
        themes.append("financial transactions")
    if any("date" in n or "time" in n for n in names) or any(
        p.is_datetime for p in profiles
    ):
        themes.append("temporal patterns")
    if any("age" in n or "gender" in n or "income" in n for n in names):
        themes.append("demographic attributes")

    numeric = sum(1 for p in profiles if p.is_numeric)
    categorical = sum(1 for p in profiles if p.is_categorical)

    if themes:
        theme_str = ", ".join(themes)
        return (
            f"This dataset ({len(df):,} rows × {len(profiles)} columns) appears to capture "
            f"{theme_str}. It contains {numeric} numerical and {categorical} categorical features "
            f"suitable for autonomous predictive modeling."
        )

    return (
        f"This dataset contains {len(df):,} observations across {len(profiles)} variables "
        f"({numeric} numerical, {categorical} categorical). Nexora can profile it for "
        f"classification, regression, or clustering tasks."
    )


def analyze_dataset(
    df: pd.DataFrame, filename: str, dataset_id: str | None = None
) -> DatasetAnalysis:
    dataset_id = dataset_id or str(uuid.uuid4())
    profiles = _profile_columns(df)
    stats = _compute_stats(df, profiles)
    health = _health_score(df, profiles)
    suggestions = _suggest_predictions(df, profiles)
    model_eligibility = _model_eligibility(df, profiles, suggestions)
    summary = _semantic_summary(df, profiles)

    preview_df = df.head(settings.max_rows_preview)
    preview = preview_df.replace({np.nan: None}).to_dict(orient="records")

    memory_mb = round(df.memory_usage(deep=True).sum() / (1024 * 1024), 3)

    return DatasetAnalysis(
        dataset_id=dataset_id,
        filename=filename,
        rows=len(df),
        columns=len(df.columns),
        duplicate_rows=int(df.duplicated().sum()),
        memory_mb=memory_mb,
        column_profiles=profiles,
        stats=stats,
        health=health,
        prediction_suggestions=suggestions,
        model_eligibility=model_eligibility,
        semantic_summary=summary,
        preview=preview,
    )
