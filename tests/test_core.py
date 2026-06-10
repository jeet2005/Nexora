from __future__ import annotations

import pandas as pd
import pytest

from nexora import Nexora, NexoraReport
from nexora.models.task_detector import detect_task_type


def test_csv_constructor_profile_and_task_detection(regression_csv):
    path, _ = regression_csv

    nx = Nexora(path, target="revenue")
    profile = nx.profile()

    assert profile.source_name == "sales.csv"
    assert profile.rows == 80
    assert profile.health_score > 0
    assert "customer_id" in profile.columns["name"].tolist()
    assert detect_task_type(nx.df, "revenue") == "regression"


def test_constructor_rejects_unknown_target(regression_csv):
    path, _ = regression_csv

    with pytest.raises(ValueError, match="Target column"):
        Nexora(path, target="missing_target")


def test_run_returns_report_and_leaderboard(regression_csv):
    path, _ = regression_csv

    report = Nexora(path, target="revenue").run(max_models=3)

    assert isinstance(report, NexoraReport)
    assert report.best_model
    assert isinstance(report.best_score, float)
    assert report.best_score_label == "r2"
    assert not report.leaderboard.empty
    assert {"model_name", "primary_score", "status"}.issubset(report.leaderboard.columns)
    assert report.profile.health_score > 0


def test_predict_and_session_load(regression_csv, tmp_path):
    path, df = regression_csv
    report = Nexora(path, target="revenue").run(max_models=2)

    predictions = report.predict(df.drop(columns=["revenue"]).head(5))
    assert list(predictions.columns) == ["revenue_predicted", "confidence", "model_used"]
    assert len(predictions) == 5

    session = report.save(tmp_path / "session.nx")
    loaded = Nexora.load(session)
    loaded_predictions = loaded.predict(df.drop(columns=["revenue"]).head(3))

    assert isinstance(loaded, NexoraReport)
    assert loaded.best_model == report.best_model
    assert len(loaded_predictions) == 3


def test_classification_run_predicts_confidence(classification_csv):
    path, df = classification_csv
    report = Nexora(path, target="churn").run(max_models=3)

    assert report.task_type == "classification"
    assert report.best_score_label == "accuracy"

    predictions = report.predict(df.drop(columns=["churn"]).head(4))
    # Note: predictions could be 0/1 or "yes"/"no" depending on whether
    # inverse_transform is implemented on the pipeline outputs.
    assert predictions["churn_predicted"].isin(["yes", "no", 0, 1]).all()
    assert predictions["confidence"].notna().all()
