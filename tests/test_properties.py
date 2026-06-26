"""Property-based tests for Nexora using Hypothesis."""

import pandas as pd
import numpy as np
import pytest
from hypothesis import given, settings, assume, HealthCheck
from hypothesis.extra.pandas import data_frames, column, range_indexes
import hypothesis.strategies as st

from nexora.core import Nexora


# Strategy for generating a small valid dataframe for regression
regression_df_strategy = data_frames(
    index=range_indexes(min_size=30, max_size=50),
    columns=[
        column("feature_num", elements=st.floats(min_value=-100, max_value=100, allow_nan=False, allow_infinity=False)),
        column("feature_cat", elements=st.sampled_from(["A", "B", "C"])),
        column("target", elements=st.floats(min_value=-1000, max_value=1000, allow_nan=False, allow_infinity=False)),
    ],
)


@settings(max_examples=5, deadline=None, suppress_health_check=[HealthCheck.too_slow])
@given(regression_df_strategy)
def test_nexora_regression_properties(df):
    """Property: Nexora should successfully profile and train on any valid regression DataFrame."""
    # Skip degenerate datasets where the target has too few unique values
    assume(df["target"].nunique() >= 5)
    # Ensure enough variance in features
    assume(df["feature_num"].std() > 0)
    assume(len(df.drop_duplicates()) >= 10)

    nx = Nexora(df, target="target")
    assert nx.profile() is not None
    assert nx.profile().num_rows == len(df)

    # Fast test training
    report = nx.run(max_models=1)
    assert report is not None
    assert report.best_model is not None


# Strategy for generating a valid dataframe for classification
classification_df_strategy = data_frames(
    index=range_indexes(min_size=30, max_size=50),
    columns=[
        column("feature_num", elements=st.floats(min_value=-100, max_value=100, allow_nan=False, allow_infinity=False)),
        column("feature_cat", elements=st.sampled_from(["A", "B", "C"])),
        column("target", elements=st.sampled_from([0, 1])),
    ],
)


@settings(max_examples=5, deadline=None, suppress_health_check=[HealthCheck.too_slow, HealthCheck.filter_too_much])
@given(classification_df_strategy)
def test_nexora_classification_properties(df):
    """Property: Nexora should successfully profile and train on any valid classification DataFrame."""
    # Ensure both classes have enough samples for train/test split with stratification
    assume((df["target"] == 0).sum() >= 5 and (df["target"] == 1).sum() >= 5)
    # Ensure enough variance in features
    assume(df["feature_num"].std() > 0)
    assume(len(df.drop_duplicates()) >= 10)

    nx = Nexora(df, target="target")

    report = nx.run(max_models=1)
    assert report is not None
    assert report.best_model is not None
