"""Partial Dependence Plot explainer module.

Provides a lightweight implementation of partial dependence without relying on scikit‑learn's ``partial_dependence`` function.
It creates a grid of values for the specified feature, replaces the column with each grid value, and averages the model predictions.
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def get_partial_dependence(
    model, X: pd.DataFrame, feature: str
) -> dict[str, list[float]]:
    """Calculate partial dependence for ``feature``.

    Args:
        model: Trained model with a ``predict`` method (or ``predict_proba`` for classifiers).
        X: DataFrame containing the features.
        feature: Column name to evaluate.

    Returns:
        A dictionary with two keys:
        * "values" – the grid values used for the feature.
        * "average" – the average model prediction for each grid value.
    """
    if feature not in X.columns:
        raise ValueError(f"Feature '{feature}' not found in the dataset.")

    col = X[feature]
    # Determine grid of values
    if pd.api.types.is_numeric_dtype(col):
        grid = np.linspace(col.min(), col.max(), num=50)
    else:
        grid = np.asarray(col.unique())

    averages: list[float] = []
    for val in grid:
        X_tmp = X.copy()
        X_tmp[feature] = val
        if hasattr(model, "predict_proba"):
            preds = model.predict_proba(X_tmp)
            if preds.ndim == 2 and preds.shape[1] == 2:
                preds = preds[:, 1]
        else:
            preds = model.predict(X_tmp)
        preds = np.ravel(preds)
        averages.append(float(np.mean(preds)))

    return {"values": list(map(float, grid)), "average": averages}
