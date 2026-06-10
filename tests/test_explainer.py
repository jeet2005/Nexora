from __future__ import annotations

from nexora import Nexora


def test_explain_returns_ranked_feature_importance(regression_csv):
    path, _ = regression_csv
    report = Nexora(path, target="revenue").run(max_models=3)

    explanation = report.explain()

    assert not explanation.empty
    assert list(explanation.columns) == ["feature", "importance", "percentage"]
    assert explanation["importance"].iloc[0] >= explanation["importance"].iloc[-1]
