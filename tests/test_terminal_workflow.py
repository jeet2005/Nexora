from __future__ import annotations

import pandas as pd

from nexora import Nexora
from nexora.types import PreprocessingConfig


def test_intelligence_suggests_targets_and_pipeline_plan(regression_csv):
    path, _ = regression_csv
    nx = Nexora(path)

    intelligence = nx.intelligence()
    targets = nx.suggest_targets()
    plan = nx.pipeline_plan(target="revenue")

    assert intelligence.profile.health_score > 0
    assert intelligence.preview
    assert any(item["target_column"] == "revenue" for item in targets)
    assert plan["problem_detector"]["problem_type"] == "regression"
    assert plan["preprocessing"]["fill_missing"] is True


def test_prediction_receipt_uses_selected_models(regression_csv):
    path, df = regression_csv
    report = Nexora(path, target="revenue").run(max_models=3)
    suggested = report.suggest_models(max_models=2)
    model_ids = [item["model_id"] for item in suggested]
    row = df.drop(columns=["revenue"]).iloc[0].to_dict()

    receipt = report.prediction_receipt(row, models=model_ids)
    batch = report.predict_with_models(pd.DataFrame([row]), models=model_ids)

    assert len(receipt.predictions) == 2
    assert receipt.consensus_label
    assert receipt.why
    assert not batch.empty
    assert "nexora_consensus" in batch.columns


def test_pipeline_controls_charts_experiments_and_advanced_tracks(
    regression_csv, tmp_path
):
    path, df = regression_csv
    config = PreprocessingConfig(
        scaling="minmax",
        drop_id_columns=True,
        remove_duplicates=True,
        fill_missing=True,
        outlier_cap=True,
        encode_categorical=True,
    )

    nx = Nexora(path, target="revenue")
    plan = nx.pipeline_plan(target="revenue", preprocessing_config=config)
    report = nx.run(target="revenue", max_models=2, preprocessing_config=config)
    charts = report.save_charts(tmp_path / "charts")
    clusters = nx.cluster(n_clusters=3)
    forecast = nx.forecast(
        date_column="signup_date",
        target_column="revenue",
        periods=3,
        frequency="D",
    )

    assert plan["preprocessing"]["feature_scaling"] == "MinMaxScaler"
    assert report.experiment_record is not None
    assert Nexora.experiments()
    assert charts
    assert all(path.exists() for path in charts)
    assert clusters["clusters"]
    assert len(forecast["forecast"]) == 3


def test_outlier_capping_skips_boolean_features():
    df = pd.DataFrame(
        {
            "flag": [True, False] * 8,
            "amount": [10, 11, 10, 12, 11, 10, 500, 9] * 2,
            "target": [1, 0] * 8,
        }
    )

    report = Nexora(df, target="target").run(
        max_models=1,
        preprocessing_config=PreprocessingConfig(remove_duplicates=False),
    )

    assert report.best_model
