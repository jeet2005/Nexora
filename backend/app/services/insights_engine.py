from typing import Any

import numpy as np
import pandas as pd


def _top_correlations(df: pd.DataFrame, target: str, limit: int = 8) -> list[dict]:
    if target not in df.columns:
        return []

    numeric = df.select_dtypes(include=[np.number]).columns.tolist()
    if target not in numeric or len(numeric) < 2:
        return []

    corr = (
        df[numeric]
        .corr()[target]
        .drop(target, errors="ignore")
        .abs()
        .sort_values(ascending=False)
    )
    return [
        {"feature": name, "correlation": round(float(val), 4)}
        for name, val in corr.head(limit).items()
        if not np.isnan(val)
    ]


def _class_balance(df: pd.DataFrame, target: str) -> list[dict]:
    counts = df[target].value_counts(normalize=True).head(10)
    return [
        {"class": str(k), "percentage": round(float(v) * 100, 2)}
        for k, v in counts.items()
    ]


def _target_stats(df: pd.DataFrame, target: str, problem_type: str) -> dict:
    s = df[target].dropna()
    if problem_type == "regression":
        return {
            "min": _safe(s.min()),
            "max": _safe(s.max()),
            "mean": _safe(s.mean()),
            "std": _safe(s.std()),
        }
    return {
        "classes": int(s.nunique()),
        "most_common": str(s.mode().iloc[0]) if len(s.mode()) else None,
    }


def _safe(v: Any) -> float | None:
    try:
        f = float(v)
        return None if np.isnan(f) or np.isinf(f) else round(f, 4)
    except (TypeError, ValueError):
        return None


def _quality_warnings(
    df: pd.DataFrame, target: str, feature_cols: list[str]
) -> list[str]:
    warnings: list[str] = []
    n = len(df)

    missing_target = df[target].isna().sum()
    if missing_target:
        warnings.append(
            f"{missing_target} rows ({100 * missing_target / n:.1f}%) have missing target values."
        )

    for col in feature_cols[:20]:
        if col not in df.columns:
            continue
        pct = df[col].isna().sum() / max(n, 1)
        if pct > 0.3:
            warnings.append(
                f"Column '{col}' has {pct * 100:.0f}% missing values — may hurt model performance."
            )

    if len(feature_cols) < 2:
        warnings.append("Very few features remain — model may underfit.")

    if len(feature_cols) > 100:
        warnings.append(
            f"High dimensionality ({len(feature_cols)} features) — consider feature selection."
        )

    return warnings


def _difficulty_score(
    df: pd.DataFrame, target: str, problem_type: str, correlations: list[dict]
) -> int:
    score = 70
    n = len(df)

    if n < 100:
        score -= 15
    elif n > 10000:
        score += 10

    if problem_type == "classification":
        balance = df[target].value_counts(normalize=True)
        if len(balance) >= 2:
            imbalance = balance.max() - balance.min()
            if imbalance > 0.4:
                score -= 20

    if correlations and correlations[0]["correlation"] > 0.7:
        score += 15
    elif correlations and correlations[0]["correlation"] < 0.1:
        score -= 10

    return max(10, min(95, score))


def generate_insights(
    df: pd.DataFrame,
    raw_df: pd.DataFrame,
    target_column: str,
    problem_type: str,
    feature_columns: list[str],
    preprocessing_steps: list[dict],
    raw_feature_columns: list[str] | None = None,
) -> dict:
    correlations = _top_correlations(df, target_column)
    class_balance = (
        _class_balance(raw_df, target_column)
        if problem_type == "classification"
        else []
    )
    target_stats = _target_stats(raw_df, target_column, problem_type)
    warnings = _quality_warnings(
        raw_df, target_column, raw_feature_columns or feature_columns
    )
    difficulty = _difficulty_score(df, target_column, problem_type, correlations)

    narrative_parts = [
        f"Target '{target_column}' configured for {problem_type}.",
        f"{len(feature_columns)} features selected after preprocessing.",
    ]

    if correlations:
        top = correlations[0]
        narrative_parts.append(
            f"Strongest signal: '{top['feature']}' (|r|={top['correlation']:.2f}) with the target."
        )

    if class_balance and len(class_balance) >= 2:
        dominant = class_balance[0]
        if dominant["percentage"] > 70:
            narrative_parts.append(
                f"Class imbalance detected — '{dominant['class']}' is {dominant['percentage']}% of samples."
            )

    if difficulty >= 75:
        narrative_parts.append(
            "Dataset appears well-suited for automated model benchmarking."
        )
    elif difficulty < 50:
        narrative_parts.append(
            "Expect moderate challenge — consider more data or feature engineering."
        )

    return {
        "top_correlations": correlations,
        "class_balance": class_balance,
        "target_stats": target_stats,
        "quality_warnings": warnings,
        "estimated_difficulty": difficulty,
        "narrative": " ".join(narrative_parts),
        "preprocessing_summary": f"{len(preprocessing_steps)} transformation steps applied.",
    }
