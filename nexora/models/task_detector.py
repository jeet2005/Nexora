"""Task type detection for supervised MVP runs."""

from __future__ import annotations

import pandas as pd

from nexora.profiler.dataset_profile import infer_datetime
from nexora.types import TaskType


def detect_task_type(df: pd.DataFrame, target: str) -> TaskType:
    """Detect whether a supervised target is regression or classification.

    Args:
        df: Training dataframe.
        target: Target column name.

    Returns:
        `"regression"` for continuous numeric targets, otherwise `"classification"`.

    Example:
        `task = detect_task_type(df, "price")`
    """

    if target not in df.columns:
        raise ValueError(f"Target column '{target}' not found.")

    y = df[target].dropna()
    if y.empty:
        raise ValueError(f"Target column '{target}' has no non-null values.")

    unique = y.nunique(dropna=True)
    is_numeric = pd.api.types.is_numeric_dtype(y) and not infer_datetime(y)
    if is_numeric and unique > max(20, len(y) * 0.05):
        return "regression"
    # Float targets with non-integer values are continuous even with few unique values
    if is_numeric and pd.api.types.is_float_dtype(y) and not (y == y.astype(int)).all():
        return "regression"
    return "classification"
