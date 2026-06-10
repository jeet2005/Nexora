"""pytest-nexora: Pytest plugin for asserting ML invariants."""

import pandas as pd
from nexora.report import NexoraReport


def assert_no_drift(report: NexoraReport, new_df: pd.DataFrame, threshold: float = 0.1):
    """Assert that the new dataset does not drift significantly from the training dataset.
    
    Args:
        report: Fitted NexoraReport.
        new_df: New data to check.
        threshold: Alert threshold.
    """
    alert = report.drift(new_df, threshold=threshold)
    if alert.severity == "High":
        raise AssertionError(f"High data drift detected in features: {alert.drifted_features}")


def assert_accuracy_above(report: NexoraReport, min_accuracy: float):
    """Assert that the primary metric is above the specified minimum.
    
    Args:
        report: Fitted NexoraReport.
        min_accuracy: Minimum acceptable score.
    """
    if report.best_score < min_accuracy:
        raise AssertionError(f"Model score {report.best_score:.4f} is below minimum {min_accuracy}")
