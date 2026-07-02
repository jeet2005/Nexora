"""Data drift monitoring using Evidently AI."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pandas as pd


@dataclass
class DriftAlert:
    """Alert object containing details of detected data drift."""

    drifted_features: list[str]
    severity: str
    recommendation: str
    details: dict[str, Any]

    def __repr__(self) -> str:
        return f"DriftAlert(severity='{self.severity}', features={len(self.drifted_features)})"


def _run_evidently(training_df: pd.DataFrame, new_df: pd.DataFrame) -> Any:
    """Run Evidently Data Drift preset."""
    try:
        from evidently.metric_preset import DataDriftPreset
        from evidently.report import Report
    except ImportError as e:
        raise ImportError(
            "Evidently is required for drift detection. Run `pip install evidently`."
        ) from e

    report = Report(metrics=[DataDriftPreset()])
    report.run(reference_data=training_df, current_data=new_df)
    return report


def detect_drift(
    training_df: pd.DataFrame, new_df: pd.DataFrame, threshold: float = 0.1
) -> DriftAlert:
    """Detect drift between two DataFrames.

    A lightweight fallback that works without the *evidently* library.
    For numeric columns we flag drift when the absolute difference in means
    exceeds ``threshold`` (default 0.1). For categorical columns we flag
    drift when the most‑common value proportion changes by more than ``threshold``.
    The function returns a :class:`DriftAlert` compatible with the original API.
    """
    # Simple numeric drift detection
    drifted = []
    details = {}
    for col in training_df.columns:
        if col not in new_df.columns:
            continue
        if pd.api.types.is_numeric_dtype(training_df[col]):
            mean_train = training_df[col].mean()
            mean_new = new_df[col].mean()
            diff = abs(mean_new - mean_train)
            drifted_flag = diff > threshold
            if drifted_flag:
                drifted.append(col)
            details[col] = {
                "type": "numeric",
                "mean_train": float(mean_train),
                "mean_new": float(mean_new),
                "diff": float(diff),
                "drifted": drifted_flag,
            }
        else:
            # Categorical / object
            train_counts = training_df[col].value_counts(normalize=True, dropna=False)
            new_counts = new_df[col].value_counts(normalize=True, dropna=False)
            # Compare proportion of the most common category
            top_train = train_counts.iloc[0] if not train_counts.empty else 0.0
            top_new = new_counts.iloc[0] if not new_counts.empty else 0.0
            diff = abs(top_new - top_train)
            drifted_flag = diff > threshold
            if drifted_flag:
                drifted.append(col)
            details[col] = {
                "type": "categorical",
                "top_train": float(top_train),
                "top_new": float(top_new),
                "diff": float(diff),
                "drifted": drifted_flag,
            }
    # Determine severity based on share of drifted columns
    share = len(drifted) / max(len(training_df.columns), 1)
    if share > 0.5:
        severity = "High"
    elif share > 0:
        severity = "Medium"
    else:
        severity = "Low"
    recommendation = (
        "Significant drift detected. Retraining the model is highly recommended."
        if severity == "High"
        else "Monitor model performance closely. Consider retraining if accuracy drops."
        if severity == "Medium"
        else "No action needed."
    )
    return DriftAlert(
        drifted_features=drifted,
        severity=severity,
        recommendation=recommendation,
        details=details,
    )


def full_monitoring_report(
    training_df: pd.DataFrame, new_df: pd.DataFrame
) -> pd.DataFrame:
    """Generate a tabular monitoring report of drift using Evidently.

    Args:
        training_df: Original dataset.
        new_df: New dataset.

    Returns:
        DataFrame summarizing drift metrics per column.
    """
    alert = detect_drift(training_df, new_df)

    rows = []
    for col, data in alert.details.items():
        rows.append({"feature": col, **data})
    return pd.DataFrame(rows)
