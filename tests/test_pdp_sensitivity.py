import pandas as pd
import pytest
from sklearn.linear_model import LinearRegression

from nexora.explainer.pdp import get_partial_dependence
from nexora.explainer.sensitivity import sensitivity


@pytest.fixture
def mock_data_model():
    df = pd.DataFrame(
        {
            "age": [20, 30, 40, 50, 60],
            "income": [30000, 40000, 50000, 60000, 70000],
            "target": [0, 1, 0, 1, 1],
        }
    )

    model = LinearRegression()
    model.fit(df[["age", "income"]], df["target"])

    return model, df[["age", "income"]]


def test_get_partial_dependence(mock_data_model):
    model, X = mock_data_model

    pdp = get_partial_dependence(model, X, "age")

    assert "values" in pdp
    assert "average" in pdp
    assert len(pdp["values"]) > 0
    assert len(pdp["average"]) > 0


def test_get_partial_dependence_missing_feature(mock_data_model):
    model, X = mock_data_model

    with pytest.raises(ValueError, match="Feature 'height' not found"):
        get_partial_dependence(model, X, "height")


def test_sensitivity(mock_data_model):
    model, X = mock_data_model

    res = sensitivity(model, X, "income")

    assert "shift_amount" in res
    assert "mean_absolute_change" in res
    assert "mean_percentage_change" in res


def test_sensitivity_missing_feature(mock_data_model):
    model, X = mock_data_model

    with pytest.raises(ValueError, match="Feature 'height' not found"):
        sensitivity(model, X, "height")
