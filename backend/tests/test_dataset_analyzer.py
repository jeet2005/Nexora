import pandas as pd

from app.services.dataset_analyzer import analyze_dataset


def test_analyze_dataset_handles_boolean_numeric_stats():
    df = pd.DataFrame(
        {
            "flag": [True, False, True, False, True],
            "score": [1, 2, 3, 4, 5],
        }
    )

    analysis = analyze_dataset(df, "flags.csv", "bool-dataset")

    assert analysis.stats.mean["flag"] == 0.6
    assert analysis.stats.outlier_counts["flag"] == 0
