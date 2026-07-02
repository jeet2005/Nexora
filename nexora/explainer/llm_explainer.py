"""LLM Explainer module for Nexora. Converts SHAP values to natural language."""

from __future__ import annotations

import json
from typing import Any

import requests

from nexora.config import config


def _get_llm_response(system_prompt: str, user_prompt: str) -> str:
    """Helper to query the configured LLM provider."""
    provider = config.get("llm_provider")

    if provider == "ollama":
        try:
            base_url = config.get("ollama_base_url").rstrip("/")
            model = config.get("llm_model")

            payload = {
                "model": model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                "stream": False,
            }

            response = requests.post(f"{base_url}/api/chat", json=payload, timeout=10)
            response.raise_for_status()
            return response.json()["message"]["content"]
        except Exception as e:
            raise RuntimeError(f"Ollama error: {e}") from e

    elif provider == "openai":
        try:
            import openai

            api_key = config.get("openai_api_key")
            if not api_key:
                raise ValueError("OPENAI_API_KEY is not set.")

            client = openai.OpenAI(api_key=api_key)
            model = config.get("llm_model")

            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.0,
            )
            return response.choices[0].message.content
        except Exception as e:
            raise RuntimeError(f"OpenAI error: {e}") from e

    else:
        raise ValueError(f"Unknown LLM provider: {provider}")


def _build_context_str(context: dict[str, Any]) -> str:
    return json.dumps(context, indent=2)


def generate_explanation(context: dict[str, Any], fallback_text: str) -> str:
    """Generate a natural language explanation of the model's feature importance.

    Args:
        context: Dictionary containing model and dataset metadata.
        fallback_text: The text to return if the LLM call fails.

    Returns:
        A natural language string explaining the model.

    Example:
        `text = generate_explanation(context, fallback_text)`
    """
    system_prompt = (
        "You are a data science assistant. Answer ONLY based on the statistics provided.\n"
        "Do not hallucinate numbers not present in the context. Be specific and concrete.\n"
        "Keep answers under 150 words unless the user explicitly asks for detail."
    )

    user_prompt = f"Please explain the following model's feature importance in plain English:\n{_build_context_str(context)}"

    try:
        return _get_llm_response(system_prompt, user_prompt)
    except Exception as e:
        print(f"LLM explanation failed ({e}). Falling back to standard text.")
        return fallback_text


def ask_question(context: dict[str, Any], question: str) -> str:
    """Ask a free-form question grounded in model stats.

    Args:
        context: Dictionary containing model and dataset metadata.
        question: The user's question.

    Returns:
        A natural language string answering the question.

    Example:
        `ans = ask_question(context, "Which features matter most?")`
    """
    system_prompt = (
        "You are a data science assistant. Answer ONLY based on the statistics provided.\n"
        "Do not hallucinate numbers not present in the context. Be specific and concrete.\n"
        "Keep answers under 150 words unless the user explicitly asks for detail."
    )

    user_prompt = f"Context:\n{_build_context_str(context)}\n\nQuestion: {question}"

    try:
        return _get_llm_response(system_prompt, user_prompt)
    except Exception as e:
        return f"Could not answer question due to LLM error: {e}"


def what_if(
    context: dict[str, Any],
    feature: str,
    value: Any,
    row_data: dict[str, Any],
    new_prediction: Any,
) -> str:
    """Explain the impact of changing one feature value.

    Args:
        context: Dictionary containing model and dataset metadata.
        feature: The feature that was changed.
        value: The new value of the feature.
        row_data: The original row data.
        new_prediction: The predicted value after the change.

    Returns:
        A natural language string explaining the prediction change.

    Example:
        `ans = what_if(context, "age", 35, {"age": 25, "income": 50000}, 0.8)`
    """
    system_prompt = (
        "You are a data science assistant. Answer ONLY based on the statistics provided.\n"
        "Do not hallucinate numbers not present in the context. Be specific and concrete.\n"
        "Keep answers under 150 words unless the user explicitly asks for detail."
    )

    user_prompt = (
        f"Context:\n{_build_context_str(context)}\n\n"
        f"Original Data: {json.dumps(row_data)}\n"
        f"Change: Feature '{feature}' was changed to {value}.\n"
        f"New Prediction Result: {new_prediction}\n\n"
        "Explain what this means in plain English."
    )

    try:
        return _get_llm_response(system_prompt, user_prompt)
    except Exception as e:
        return f"Could not explain 'what if' due to LLM error: {e}"
