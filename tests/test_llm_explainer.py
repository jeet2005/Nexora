from unittest.mock import MagicMock, patch

import pytest

from nexora.config import config
from nexora.explainer.llm_explainer import ask_question, generate_explanation, what_if


@pytest.fixture
def dummy_context():
    return {
        "model_type": "XGBRegressor",
        "metric_name": "r2",
        "metric_value": 0.95,
        "task_type": "regression",
        "n_rows": 1000,
        "n_features": 10,
        "target_col": "price",
        "top_features": [{"name": "age", "shap_importance": 0.5}],
        "data_profile": {"health_score": 90, "missing_count": 0},
    }


def test_generate_explanation_fallback(dummy_context):
    config.set(llm_provider="invalid_provider")

    result = generate_explanation(dummy_context, "Fallback Text")
    assert result == "Fallback Text"


@patch("nexora.explainer.llm_explainer.requests.post")
def test_generate_explanation_ollama(mock_post, dummy_context):
    config.set(llm_provider="ollama")

    mock_response = MagicMock()
    mock_response.json.return_value = {
        "message": {"content": "This is a mocked explanation."}
    }
    mock_response.raise_for_status.return_value = None
    mock_post.return_value = mock_response

    result = generate_explanation(dummy_context, "Fallback Text")
    assert result == "This is a mocked explanation."


@patch("nexora.explainer.llm_explainer.requests.post")
def test_ask_question_ollama(mock_post, dummy_context):
    config.set(llm_provider="ollama")

    mock_response = MagicMock()
    mock_response.json.return_value = {
        "message": {"content": "It means age is important."}
    }
    mock_response.raise_for_status.return_value = None
    mock_post.return_value = mock_response

    result = ask_question(dummy_context, "What does this mean?")
    assert result == "It means age is important."


def test_ask_question_fallback(dummy_context):
    config.set(llm_provider="invalid_provider")

    result = ask_question(dummy_context, "What does this mean?")
    assert "LLM error" in result


@patch("nexora.explainer.llm_explainer.requests.post")
def test_what_if_ollama(mock_post, dummy_context):
    config.set(llm_provider="ollama")

    mock_response = MagicMock()
    mock_response.json.return_value = {
        "message": {"content": "Prediction changes because age increased."}
    }
    mock_response.raise_for_status.return_value = None
    mock_post.return_value = mock_response

    result = what_if(dummy_context, "age", 50, {"age": 25}, 100.0)
    assert result == "Prediction changes because age increased."
