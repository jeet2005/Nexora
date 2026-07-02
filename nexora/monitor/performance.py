"""Performance monitoring and error analysis."""

from __future__ import annotations

import numpy as np
import pandas as pd


def error_analysis(
    y_true: pd.Series | np.ndarray,
    y_pred: pd.Series | np.ndarray,
    features: pd.DataFrame,
    task_type: str = "regression",
) -> pd.DataFrame:
    """Find specific segments where the model has highest error.

    Args:
        y_true: Actual target values.
        y_pred: Predicted target values.
        features: The feature DataFrame corresponding to the predictions.
        task_type: Task type, e.g., 'regression' or 'classification'.

    Returns:
        DataFrame of feature segments with their average error.
    """
    y_true = np.asarray(y_true)
    y_pred = np.asarray(y_pred)

    # Calculate error per row
    if task_type == "regression":
        errors = np.abs(y_true - y_pred)
    else:
        # 1 for incorrect, 0 for correct
        errors = (y_true != y_pred).astype(float)

    df_eval = features.copy()
    df_eval["_nexora_error"] = errors

    segments = []

    # Simple heuristic: for categorical columns, what is the error rate per category?
    # For numeric columns, bin them into quartiles and calculate error rate.
    for col in features.columns:
        if (
            pd.api.types.is_numeric_dtype(features[col])
            and features[col].nunique() > 10
        ):
            # Numeric: bin into quartiles
            try:
                binned = pd.qcut(df_eval[col], q=4, duplicates="drop")
                grouped = df_eval.groupby(binned)["_nexora_error"].agg(
                    ["mean", "count"]
                )
            except Exception:
                continue
        else:
            # Categorical or low-cardinality numeric
            grouped = df_eval.groupby(col)["_nexora_error"].agg(["mean", "count"])

        # Filter for segments with decent size (e.g. > 5% of data)
        min_size = len(df_eval) * 0.05
        grouped = grouped[grouped["count"] >= min_size]

        for idx, row in grouped.iterrows():
            segments.append(
                {
                    "feature": col,
                    "segment": str(idx),
                    "error_rate": float(row["mean"]),
                    "sample_size": int(row["count"]),
                }
            )

    res_df = pd.DataFrame(segments)
    if res_df.empty:
        return res_df

    # Sort by error rate descending
    return res_df.sort_values(by="error_rate", ascending=False).reset_index(drop=True)
