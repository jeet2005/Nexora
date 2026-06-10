"""Sensitivity analysis explainer module."""

from __future__ import annotations

import numpy as np
import pandas as pd


def sensitivity(model, X: pd.DataFrame, feature: str, stdev_multiplier: float = 1.0) -> dict[str, float]:
    """Calculate sensitivity of predictions to a feature by perturbing it.
    
    Args:
        model: Trained model with a `predict` method.
        X: The dataset to perturb.
        feature: The column name to perturb.
        stdev_multiplier: The amount of standard deviation to shift the feature by.
        
    Returns:
        Dictionary containing the mean absolute change in predictions.
        
    Example:
        `result = sensitivity(model, df, "age")`
    """
    if feature not in X.columns:
        raise ValueError(f"Feature '{feature}' not found in the dataset.")
        
    if not pd.api.types.is_numeric_dtype(X[feature]):
        raise ValueError(f"Sensitivity analysis currently only supports numeric features. '{feature}' is not numeric.")
        
    baseline_preds = np.array(model.predict(X))
    
    std_dev = X[feature].std()
    shift_amount = std_dev * stdev_multiplier
    
    X_perturbed = X.copy()
    X_perturbed[feature] += shift_amount
    
    perturbed_preds = np.array(model.predict(X_perturbed))
    
    mean_abs_change = np.mean(np.abs(perturbed_preds - baseline_preds))
    mean_pct_change = np.mean(np.abs((perturbed_preds - baseline_preds) / (np.abs(baseline_preds) + 1e-9))) * 100
    
    return {
        "shift_amount": float(shift_amount),
        "mean_absolute_change": float(mean_abs_change),
        "mean_percentage_change": float(mean_pct_change)
    }
