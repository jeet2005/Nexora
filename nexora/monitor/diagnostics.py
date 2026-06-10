"""Model diagnostic plotting and performance visualization."""

from __future__ import annotations

import warnings
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from sklearn.calibration import CalibrationDisplay
from sklearn.metrics import (
    ConfusionMatrixDisplay,
    PrecisionRecallDisplay,
    RocCurveDisplay,
    classification_report,
)
from sklearn.model_selection import learning_curve


def plot_residuals(y_true: pd.Series | np.ndarray, y_pred: pd.Series | np.ndarray) -> plt.Figure:
    """Plot residuals scatter and distribution for regression.
    
    Args:
        y_true: Actual target values.
        y_pred: Predicted target values.
        
    Returns:
        Matplotlib figure containing the plots.
    """
    y_true = np.asarray(y_true)
    y_pred = np.asarray(y_pred)
    residuals = y_true - y_pred

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
    
    # Scatter plot
    sns.scatterplot(x=y_pred, y=residuals, ax=ax1, alpha=0.5)
    ax1.axhline(y=0, color="r", linestyle="--")
    ax1.set_xlabel("Predicted Values")
    ax1.set_ylabel("Residuals (True - Predicted)")
    ax1.set_title("Residuals vs Predicted")
    
    # Distribution
    sns.histplot(residuals, kde=True, ax=ax2)
    ax2.set_xlabel("Residual Error")
    ax2.set_title("Residual Distribution")
    
    plt.tight_layout()
    return fig


def plot_confusion_matrix(y_true: pd.Series | np.ndarray, y_pred: pd.Series | np.ndarray, labels: list[str] | None = None) -> plt.Figure:
    """Plot confusion matrix and print classification report.
    
    Args:
        y_true: True class labels.
        y_pred: Predicted class labels.
        labels: Optional list of class names.
        
    Returns:
        Matplotlib figure.
    """
    fig, ax = plt.subplots(figsize=(8, 6))
    ConfusionMatrixDisplay.from_predictions(y_true, y_pred, display_labels=labels, cmap="Blues", ax=ax)
    ax.set_title("Confusion Matrix")
    
    # Also print the classification report to standard output
    print(classification_report(y_true, y_pred, target_names=labels))
    
    return fig


def plot_roc_curve(y_true: pd.Series | np.ndarray, y_prob: pd.DataFrame | np.ndarray, labels: list[str] | None = None) -> plt.Figure:
    """Plot multi-class or binary ROC curve.
    
    Args:
        y_true: True class labels.
        y_prob: Predicted probabilities.
        labels: Optional list of class names.
        
    Returns:
        Matplotlib figure.
    """
    fig, ax = plt.subplots(figsize=(8, 6))
    y_true = np.asarray(y_true)
    y_prob = np.asarray(y_prob)
    
    if len(y_prob.shape) == 1 or y_prob.shape[1] <= 2:
        # Binary classification
        prob = y_prob if len(y_prob.shape) == 1 else y_prob[:, 1]
        RocCurveDisplay.from_predictions(y_true, prob, name="Positive Class", ax=ax)
    else:
        # Multi-class (One-vs-Rest)
        from sklearn.preprocessing import label_binarize
        classes = np.unique(y_true)
        y_true_bin = label_binarize(y_true, classes=classes)
        for i, cls in enumerate(classes):
            name = labels[i] if labels and i < len(labels) else f"Class {cls}"
            RocCurveDisplay.from_predictions(y_true_bin[:, i], y_prob[:, i], name=name, ax=ax)
            
    ax.plot([0, 1], [0, 1], "k--", label="Chance")
    ax.set_title("Receiver Operating Characteristic (ROC)")
    ax.legend()
    return fig


def plot_pr_curve(y_true: pd.Series | np.ndarray, y_prob: pd.DataFrame | np.ndarray, labels: list[str] | None = None) -> plt.Figure:
    """Plot multi-class or binary Precision-Recall curve.
    
    Args:
        y_true: True class labels.
        y_prob: Predicted probabilities.
        labels: Optional list of class names.
        
    Returns:
        Matplotlib figure.
    """
    fig, ax = plt.subplots(figsize=(8, 6))
    y_true = np.asarray(y_true)
    y_prob = np.asarray(y_prob)
    
    if len(y_prob.shape) == 1 or y_prob.shape[1] <= 2:
        prob = y_prob if len(y_prob.shape) == 1 else y_prob[:, 1]
        PrecisionRecallDisplay.from_predictions(y_true, prob, name="Positive Class", ax=ax)
    else:
        from sklearn.preprocessing import label_binarize
        classes = np.unique(y_true)
        y_true_bin = label_binarize(y_true, classes=classes)
        for i, cls in enumerate(classes):
            name = labels[i] if labels and i < len(labels) else f"Class {cls}"
            PrecisionRecallDisplay.from_predictions(y_true_bin[:, i], y_prob[:, i], name=name, ax=ax)
            
    ax.set_title("Precision-Recall Curve")
    return fig


def plot_learning_curve(estimator: Any, X: pd.DataFrame | np.ndarray, y: pd.Series | np.ndarray, cv: int = 5) -> plt.Figure:
    """Plot bias-variance learning curve.
    
    Args:
        estimator: Sklearn-compatible model/pipeline.
        X: Training features.
        y: Training target.
        cv: Cross-validation splits.
        
    Returns:
        Matplotlib figure.
    """
    fig, ax = plt.subplots(figsize=(8, 6))
    
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        train_sizes, train_scores, test_scores = learning_curve(
            estimator, X, y, cv=cv, n_jobs=-1,
            train_sizes=np.linspace(0.1, 1.0, 5)
        )
        
    train_scores_mean = np.mean(train_scores, axis=1)
    train_scores_std = np.std(train_scores, axis=1)
    test_scores_mean = np.mean(test_scores, axis=1)
    test_scores_std = np.std(test_scores, axis=1)
    
    ax.fill_between(train_sizes, train_scores_mean - train_scores_std, train_scores_mean + train_scores_std, alpha=0.1, color="r")
    ax.fill_between(train_sizes, test_scores_mean - test_scores_std, test_scores_mean + test_scores_std, alpha=0.1, color="g")
    ax.plot(train_sizes, train_scores_mean, "o-", color="r", label="Training score")
    ax.plot(train_sizes, test_scores_mean, "o-", color="g", label="Cross-validation score")
    
    ax.set_xlabel("Training examples")
    ax.set_ylabel("Score")
    ax.set_title("Learning Curve")
    ax.legend(loc="best")
    return fig


def plot_calibration_curve(y_true: pd.Series | np.ndarray, y_prob: pd.DataFrame | np.ndarray) -> plt.Figure:
    """Plot probability calibration curve (reliability diagram).
    
    Args:
        y_true: True class labels.
        y_prob: Predicted probabilities.
        
    Returns:
        Matplotlib figure.
    """
    fig, ax = plt.subplots(figsize=(8, 6))
    y_true = np.asarray(y_true)
    y_prob = np.asarray(y_prob)
    
    if len(y_prob.shape) == 1 or y_prob.shape[1] <= 2:
        prob = y_prob if len(y_prob.shape) == 1 else y_prob[:, 1]
        CalibrationDisplay.from_predictions(y_true, prob, n_bins=10, ax=ax, name="Model")
    else:
        # For multi-class, we plot the calibration curve of the highest probability prediction
        # vs whether it was correct (confidence calibration).
        y_pred = np.argmax(y_prob, axis=1)
        max_prob = np.max(y_prob, axis=1)
        correct = (y_pred == y_true).astype(int)
        CalibrationDisplay.from_predictions(correct, max_prob, n_bins=10, ax=ax, name="Top-1 Confidence")
        
    ax.set_title("Probability Calibration Curve")
    return fig
