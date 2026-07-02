"""Tests for monitoring and diagnostics."""

import matplotlib

matplotlib.use("Agg")

import numpy as np
import pandas as pd
import pytest

from nexora.core import Nexora
from nexora.monitor.drift import detect_drift


@pytest.fixture
def regression_data():
    np.random.seed(42)
    X = pd.DataFrame(
        {
            "num1": np.random.normal(0, 1, 100),
            "num2": np.random.uniform(0, 10, 100),
            "cat1": np.random.choice(["A", "B", "C"], 100),
        }
    )
    y = X["num1"] * 2 + X["num2"] * 0.5 + np.random.normal(0, 0.1, 100)

    # Drifted data
    X_new = X.copy()
    X_new["num1"] = X_new["num1"] + 5  # Mean shift
    X_new["cat1"] = np.random.choice(["A", "C"], 100)  # Distribution change

    return X, y, X_new


def test_drift_detection(regression_data):
    X, y, X_new = regression_data

    alert = detect_drift(X, X_new)

    assert "num1" in alert.drifted_features
    assert "num2" not in alert.drifted_features
    assert alert.severity in ["Medium", "High"]

    # Test through report interface
    df = X.copy()
    df["target"] = y
    nx = Nexora(df, target="target")
    report = nx.quick()

    # Test proxy method
    alert2 = report.drift(X_new)
    assert "num1" in alert2.drifted_features


def test_diagnostics_regression(regression_data):
    X, y, _ = regression_data
    df = X.copy()
    df["target"] = y

    nx = Nexora(df, target="target")
    report = nx.quick()

    # Check that methods return Matplotlib figures (or run without error)
    fig_res = report.residuals()
    assert fig_res is not None

    fig_lc = report.learning_curve(cv=2)
    assert fig_lc is not None

    err_df = report.error_analysis()
    assert isinstance(err_df, pd.DataFrame)

    with pytest.raises(ValueError, match="only available for classification"):
        report.confusion_matrix()


def test_diagnostics_classification():
    np.random.seed(42)
    X = pd.DataFrame({"num": np.random.normal(0, 1, 100)})
    y = (X["num"] > 0).astype(int)
    df = X.copy()
    df["target"] = y

    nx = Nexora(df, target="target")
    report = nx.quick()

    fig_cm = report.confusion_matrix()
    assert fig_cm is not None

    fig_roc = report.roc_curve()
    assert fig_roc is not None

    fig_pr = report.pr_curve()
    assert fig_pr is not None

    fig_cal = report.calibration_curve()
    assert fig_cal is not None

    with pytest.raises(ValueError, match="only available for regression"):
        report.residuals()
