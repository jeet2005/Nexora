"""Fast SHAP-style feature importance with graceful fallback."""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.inspection import permutation_importance


def explain_report(report, *, plot: bool = False) -> pd.DataFrame:
    """Explain a report's best model with ranked feature importance.

    Args:
        report: NexoraReport instance.
        plot: When True, also render a simple matplotlib bar chart.

    Returns:
        DataFrame with feature, importance, and percentage columns.

    Example:
        `report.explain()`
    """

    pipeline = report.pipeline
    model = pipeline.named_steps["model"]
    preprocessor = pipeline.named_steps["preprocess"]
    X_raw = report.training_frame[report.schema.feature_columns]
    y = report.training_frame[report.target]
    feature_names = report.schema.transformed_feature_names

    try:
        transformed = preprocessor.transform(X_raw)
    except Exception:
        transformed = None

    raw = _native_importance(model)
    if raw is None and transformed is not None:
        raw = _permutation_importance(pipeline, X_raw, y, len(feature_names))
    if raw is None:
        raw = np.zeros(len(feature_names), dtype=float)

    if len(feature_names) != len(raw):
        feature_names = [f"feature_{index}" for index in range(len(raw))]

    frame = _importance_frame(feature_names, raw)
    if plot and not frame.empty:
        ax = frame.head(15).sort_values("importance").plot.barh(
            x="feature", y="importance", legend=False, title="Nexora Feature Importance"
        )
        ax.set_xlabel("Importance")
    return frame


def _native_importance(model) -> np.ndarray | None:
    if hasattr(model, "feature_importances_"):
        return np.asarray(model.feature_importances_, dtype=float)
    if hasattr(model, "coef_"):
        coef = np.asarray(model.coef_, dtype=float)
        if coef.ndim > 1:
            coef = np.mean(np.abs(coef), axis=0)
        return np.abs(coef)
    return None


def _permutation_importance(pipeline, X_raw, y, feature_count: int) -> np.ndarray | None:
    try:
        result = permutation_importance(
            pipeline,
            X_raw,
            y,
            n_repeats=3,
            random_state=42,
            n_jobs=1,
        )
        raw = np.maximum(result.importances_mean, 0)
        if len(raw) == feature_count:
            return raw
        return np.resize(raw, feature_count)
    except Exception:
        return None


def _importance_frame(feature_names: list[str], raw: np.ndarray) -> pd.DataFrame:
    values = np.abs(np.asarray(raw, dtype=float))
    total = float(values.sum()) or 1.0
    rows = [
        {
            "feature": feature,
            "importance": round(float(value), 8),
            "percentage": round(float(value) / total * 100, 2),
        }
        for feature, value in zip(feature_names, values)
    ]
    return pd.DataFrame(rows).sort_values("importance", ascending=False).reset_index(drop=True)
