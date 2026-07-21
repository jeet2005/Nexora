"""Ollama integration for dataset-aware chat."""

from __future__ import annotations

import json
import re
from typing import Any

import httpx
import pandas as pd

from app.config import settings
from app.services.dataset_store import load_analysis, load_dataframe
from app.services.deployed_model_service import (
    list_deployable_models,
    load_production_status,
)
from app.services.session_store import load_session


def _build_dataset_context(dataset_id: str) -> str:
    """Build comprehensive context for Ollama with full dataset details."""
    analysis = load_analysis(dataset_id)
    if not analysis:
        return "No dataset loaded."

    session = load_session(dataset_id)
    df = load_dataframe(dataset_id)

    lines = [
        f"Dataset: {analysis.filename}",
        f"Rows: {analysis.rows:,} | Columns: {analysis.columns}",
        f"Summary: {analysis.semantic_summary}",
        "",
        "Columns:",
    ]

    for p in analysis.column_profiles[:20]:
        tags = []
        if p.is_numeric:
            tags.append("numeric")
        if p.is_categorical:
            tags.append("categorical")
        if p.is_id_like:
            tags.append("id")
        tag_str = f" [{', '.join(tags)}]" if tags else ""
        lines.append(
            f"  - {p.name}: {p.dtype}, {p.missing_pct}% missing, "
            f"{p.unique_count} unique{tag_str}"
        )

    if analysis.prediction_suggestions:
        lines.append("\nPrediction suggestions:")
        for s in analysis.prediction_suggestions[:5]:
            lines.append(f"  - {s.target_column} ({s.problem_type}): {s.description}")

    if analysis.model_eligibility:
        lines.append("\nModel readiness:")
        for finding in analysis.model_eligibility:
            state = "eligible" if finding.eligible else "not eligible"
            lines.append(f"  - {finding.task}: {state}. {finding.reason}")

    if session and session.target_column:
        lines.append(
            f"\nConfigured target: {session.target_column} ({session.problem_type})"
        )

    if session and session.preprocess_result:
        pr = session.preprocess_result
        lines.append(
            f"Preprocessed: {pr.meta.rows_after} rows, {pr.meta.feature_count} features. "
            f"{pr.insights.narrative}"
        )

    if session and session.training_result:
        tr = session.training_result
        if tr.best_model:
            bm = tr.best_model
            lines.append(
                f"\nBest model: {bm.model_name} "
                f"({tr.primary_metric}={bm.primary_score})"
            )
        lines.append(f"Models trained: {tr.total_completed}/{tr.total_attempted}")

    deployed = load_production_status(dataset_id)
    if deployed and deployed.models:
        lines.append("\nPrediction Studio models:")
        for model in deployed.models:
            lines.append(
                f"  - {model.model_name} ({model.family}), score={model.primary_score}"
            )
        fields = ", ".join(field.name for field in deployed.input_fields)
        lines.append(f"Prediction Studio input fields: {fields}")

    if df is not None and len(df) > 0:
        sample = df.head(3).to_dict(orient="records")
        lines.append("\nSample rows (first 3):")
        lines.append(json.dumps(sample, default=str, indent=2)[:1200])

    lines.append(f"\nHealth score: {analysis.health.overall}/100")
    return "\n".join(lines)


def _is_detail_request(message: str) -> bool:
    """
    Intelligently detect if user wants detailed explanation.
    Uses multiple signals: explicit requests, message length, punctuation, and context.
    """
    lower = message.lower().strip()

    # Explicit detail request keywords (highest confidence)
    explicit_detail_phrases = (
        "explain in detail",
        "detailed explanation",
        "comprehensive analysis",
        "detailed analysis",
        "walk me through",
        "step by step",
        "in depth",
        "full details",
        "thorough explanation",
        "elaborate",
        "dive deep",
        "explain thoroughly",
        "tell me more",
        "go deeper",
        "why and how",
    )

    # Quick detection for explicit requests (highest priority)
    if any(phrase in lower for phrase in explicit_detail_phrases):
        return True

    # Context signals that suggest user wants details
    detail_signals = (
        "?" * 2 in lower,  # Multiple question marks (urgency/emphasis)
        "!" * 2 in lower,  # Multiple exclamation marks (emphasis)
        len(message) > 100,  # Longer messages often have more context
        "because" in lower,  # User asking for reasons
        "how does" in lower,
        "why is" in lower,
        "what about" in lower,
        "help me understand" in lower,
        "explain how" in lower,
        "teach me" in lower,
        "what's the difference" in lower,
    )

    # Check for multiple signals
    signal_count = sum(
        1 for signal in detail_signals if isinstance(signal, bool) and signal
    )

    # If 2+ signals are true, likely a detail request
    if signal_count >= 2:
        return True

    # Check if message seems exploratory (contains multiple topics)
    question_marks = lower.count("?")
    if question_marks >= 2:
        return True

    return False


SYSTEM_PROMPT = """You are Nexora AI, an educational data science assistant embedded in a predictive analytics platform.
You help users understand datasets, select prediction targets and models, interpret preprocessing, and learn from model results.
You are not the prediction engine. Never invent or calculate a requested prediction value in chat.
If a user asks for a new prediction, tell them which target and input fields are relevant and direct them to Prediction Studio, where Nexora's saved backend models calculate the result.
Be concise, accurate, and actionable. Reference specific column names and statistics from the dataset context provided.
If asked about something not in the context, say what you would need. Never invent statistics not present in the context."""


async def chat_with_dataset(
    dataset_id: str,
    message: str,
    history: list[dict[str, str]] | None = None,
) -> dict[str, Any]:
    if _is_prediction_request(message):
        return {
            "reply": _prediction_studio_guidance(dataset_id),
            "model": "nexora-guidance",
            "ok": True,
        }

    grounded = _grounded_reply(dataset_id, message)
    if grounded:
        return {"reply": grounded, "model": "nexora-grounded", "ok": True}

    context = _build_dataset_context(dataset_id)
    history = history or []

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": f"=== CURRENT DATASET CONTEXT ===\n{context}\n=== END CONTEXT ===",
        },
        {
            "role": "assistant",
            "content": "I have reviewed your dataset context. How can I help you analyze or predict with this data?",
        },
    ]

    for h in history[-10:]:
        if h.get("role") in ("user", "assistant") and h.get("content"):
            messages.append({"role": h["role"], "content": h["content"]})

    messages.append({"role": "user", "content": message})

    url = f"{settings.ollama_base_url.rstrip('/')}/api/chat"

    # Determine token budget based on request type
    is_detail = _is_detail_request(message)
    max_tokens = (
        512 if is_detail else settings.ollama_max_tokens
    )  # 512 for detail requests, 256 for normal

    payload = {
        "model": settings.ollama_model,
        "messages": messages,
        "stream": False,
        "keep_alive": "10m",  # Full 10 minutes to keep context loaded
        "options": {
            "temperature": 0.8,  # Natural, thoughtful responses
            "num_predict": max_tokens,
            "num_ctx": 2048,  # Full context window
            "repeat_penalty": 1.1,
        },
    }

    try:
        async with httpx.AsyncClient(timeout=settings.ollama_timeout) as client:
            resp = await client.post(url, json=payload)
            resp.raise_for_status()
            data = resp.json()
            reply = data.get("message", {}).get("content", "").strip()
            if not reply:
                reply = "I could not generate a response. Please ensure Ollama is running with the configured model."
            return {"reply": reply, "model": settings.ollama_model, "ok": True}
    except httpx.ConnectError:
        return {
            "reply": (
                "Nexora-Helper (Ollama) is not fully available in the online stage. "
                "To use the advanced open-ended chat assistant, please run Nexora locally with Ollama and pull the model:\n"
                f"  ollama pull {settings.ollama_model}\n"
                f"Local Ollama server is expected at {settings.ollama_base_url}"
            ),
            "model": settings.ollama_model,
            "ok": False,
        }
    except httpx.HTTPStatusError as e:
        return {
            "reply": f"Ollama error ({e.response.status_code}): {e.response.text[:300]}",
            "model": settings.ollama_model,
            "ok": False,
        }
    except httpx.TimeoutException:
        return {
            "reply": (
                f"The local Ollama model took longer than {settings.ollama_timeout:.0f} seconds, so I stopped waiting. "
                "Questions about rows, columns, missing values, model eligibility, and numeric summaries are answered "
                "instantly from your CSV; open-ended explanations depend on your local Ollama speed.\n\n"
                "Tips to speed up Ollama:\n"
                "  • Ensure Ollama is running: curl http://127.0.0.1:11434/api/tags\n"
                "  • Check system resources (GPU/CPU/RAM available)\n"
                "  • Consider using GPU if available\n"
                "  • Try restarting Ollama if it's been idle"
            ),
            "model": "nexora-helper-timeout",
            "ok": False,
        }
    except Exception as e:
        return {
            "reply": f"AI service error: {str(e)[:300]}",
            "model": settings.ollama_model,
            "ok": False,
        }


def _is_prediction_request(message: str) -> bool:
    lower = message.lower()
    if any(
        text in lower
        for text in (
            "what can i predict",
            "what should i predict",
            "teach me",
            "explain",
        )
    ):
        return False
    return any(
        text in lower
        for text in (
            "predict ",
            "forecast ",
            "estimate ",
            "what will ",
            "how much will ",
        )
    )


def _grounded_reply(dataset_id: str, message: str) -> str | None:
    lower = message.lower().strip()
    analysis = load_analysis(dataset_id)
    if not analysis:
        return None
    df = load_dataframe(dataset_id)

    if lower in {"hi", "hello", "hey", "hii", "hello ai", "hi ai"}:
        return (
            f"Hi. I have the analyzed facts for `{analysis.filename}` ready: "
            f"{analysis.rows:,} rows and {analysis.columns} columns. Ask what you can predict, "
            "which models are eligible, or about missing values."
        )

    if any(
        phrase in lower
        for phrase in (
            "can you access",
            "can ollama access",
            "read my csv",
            "access my csv",
        )
    ):
        return (
            "Nexora's backend reads your uploaded CSV and gives chat grounded facts such as columns, "
            "quality, model eligibility, and calculated summaries. Ollama receives a compact analyzed "
            "context for explanations, not permission to invent values or calculate predictions."
        )

    if any(
        phrase in lower
        for phrase in (
            "what can i predict",
            "what should i predict",
            "prediction target",
        )
    ):
        if not analysis.prediction_suggestions:
            return (
                "No strong target was detected automatically. Open Target and select the column you want "
                "to predict; Nexora will then explain which supervised models can train on it."
            )
        items = [
            f"`{item.target_column}` ({item.problem_type}, {round(item.confidence * 100)}% match)"
            for item in analysis.prediction_suggestions[:5]
        ]
        return "Suggested prediction targets from your CSV: " + ", ".join(items) + "."

    if any(
        token in lower
        for token in (
            "eligible model",
            "eligible for",
            "which model",
            "models can",
            "model should",
        )
    ):
        session = load_session(dataset_id)
        if (
            session
            and session.target_column
            and session.problem_type in ("classification", "regression")
        ):
            choices = list_deployable_models(dataset_id)
            recommended = [
                model.model_name
                for model in choices["available_models"]
                if model.recommended
            ][:5]
            return (
                f"For target `{choices['target_column']}`, {choices['eligibility_reason']} "
                f"Suggested starting models: {', '.join(recommended)}. "
                f"Time-series forecasting and clustering run in Exploration Modes on the Overview tab."
            )
        states = []
        for finding in analysis.model_eligibility:
            state = "eligible" if finding.eligible else "not eligible"
            states.append(f"{finding.task}: {state} ({finding.reason})")
        return "Model readiness before target selection: " + " ".join(states)

    if "missing" in lower or "null" in lower:
        missing = [
            f"`{profile.name}` {profile.missing_pct}%"
            for profile in analysis.column_profiles
            if profile.missing_count > 0
        ]
        return (
            "No missing values were detected in this CSV."
            if not missing
            else "Columns with missing values: " + ", ".join(missing[:12]) + "."
        )

    if any(
        phrase in lower
        for phrase in ("how many rows", "row count", "rows and columns", "dataset size")
    ):
        return f"`{analysis.filename}` has {analysis.rows:,} rows and {analysis.columns} columns."

    if any(
        phrase in lower for phrase in ("what columns", "list columns", "column names")
    ):
        columns = ", ".join(
            f"`{profile.name}`" for profile in analysis.column_profiles[:30]
        )
        suffix = " ..." if len(analysis.column_profiles) > 30 else ""
        return f"Columns in this CSV: {columns}{suffix}"

    if "accuracy vs r2" in lower or "accuracy vs r²" in lower:
        return (
            "Accuracy measures how often a classification label is correct. R2 measures how much "
            "variation a regression model explains; 1 is strong, 0 is no better than predicting the average, "
            "and negative means worse."
        )

    aggregate = _aggregate_reply(df, message) if df is not None else None
    if aggregate:
        return aggregate
    return None


def _aggregate_reply(df: pd.DataFrame, message: str) -> str | None:
    lower = message.lower()
    operation = next(
        (
            name
            for name in (
                "average",
                "mean",
                "median",
                "minimum",
                "min",
                "maximum",
                "max",
                "sum",
                "total",
            )
            if re.search(rf"\b{name}\b", lower)
        ),
        None,
    )
    if not operation:
        return None

    column = _mentioned_column(message, [str(column) for column in df.columns])
    if not column:
        return None
    values = pd.to_numeric(df[column], errors="coerce").dropna()
    if values.empty:
        return f"`{column}` is not numeric, so I cannot calculate a numeric {operation} for it."
    calculation = {
        "average": values.mean,
        "mean": values.mean,
        "median": values.median,
        "minimum": values.min,
        "min": values.min,
        "maximum": values.max,
        "max": values.max,
        "sum": values.sum,
        "total": values.sum,
    }[operation]
    label = {"mean": "average", "min": "minimum", "max": "maximum", "total": "sum"}.get(
        operation, operation
    )
    return f"The {label} of `{column}` is {float(calculation()):,.4f}, calculated directly from {len(values):,} non-empty CSV rows."


def _mentioned_column(message: str, columns: list[str]) -> str | None:
    normalized_message = re.sub(r"[^a-z0-9]", "", message.lower())
    for column in sorted(columns, key=len, reverse=True):
        if re.sub(r"[^a-z0-9]", "", column.lower()) in normalized_message:
            return column
    return None


def _prediction_studio_guidance(dataset_id: str) -> str:
    session = load_session(dataset_id)
    if not session or not session.target_column:
        return (
            "I can help you prepare a prediction, but Nexora needs a target first. "
            "Choose what to predict in the Target step, then train one or more models in Prediction Studio. "
            "The backend will calculate the real model output."
        )

    deployed = load_production_status(dataset_id)
    if not deployed or not deployed.models:
        return (
            f"Your target is `{session.target_column}`. Open Prediction Studio and select one or more models "
            "to train first. Once they are saved, provide input values there and Nexora's backend will produce "
            "the prediction; I can then help explain what it means."
        )

    fields = ", ".join(f"`{field.name}`" for field in deployed.input_fields[:10])
    models = ", ".join(model.model_name for model in deployed.models)
    return (
        f"I recognized a request to predict `{deployed.target_column}`. Your saved models are {models}. "
        f"Enter the known values in Prediction Studio ({fields}) and press Run Prediction. "
        "The prediction is calculated by those trained backend models, not by chat."
    )


async def check_ollama_status() -> dict[str, Any]:
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(f"{settings.ollama_base_url.rstrip('/')}/api/tags")
            resp.raise_for_status()
            models = [m.get("name") for m in resp.json().get("models", [])]
            return {
                "available": True,
                "models": models,
                "configured_model": settings.ollama_model,
                "model_ready": settings.ollama_model in models
                or any(settings.ollama_model in m for m in models),
            }
    except Exception:
        return {
            "available": False,
            "models": [],
            "configured_model": settings.ollama_model,
            "model_ready": False,
        }


async def explain_error_with_ollama(
    error_message: str, dataset_id: str | None = None, context_info: str | None = None
) -> dict[str, Any]:
    status = await check_ollama_status()
    dataset_ctx = ""
    if dataset_id:
        try:
            dataset_ctx = _build_dataset_context(dataset_id)
        except Exception:
            dataset_ctx = ""

    if not status.get("available"):
        return {
            "explanation": (
                "### 🔍 Diagnostic Summary\n\n"
                f"**Error Details:**\n```\n{error_message[:300]}\n```\n\n"
                "### 🛠️ Actionable Tips:\n"
                "1. **Check Target Column:** Ensure a valid target column is selected in Preprocess settings.\n"
                "2. **Inspect CSV Structure:** Verify your CSV has valid headers and non-empty rows.\n"
                "3. **Local Engine:** Local Python backend will auto-clean and format categorical variables.\n"
            ),
            "available": False,
        }

    prompt = f"""You are Nexora's Senior AI Debugging Expert.
An error occurred during dataset processing, machine learning training, or data cleaning.

ERROR MESSAGE:
{error_message}

CONTEXT LOCATION:
{context_info or "General Nexora Platform Operation"}

DATASET SUMMARY:
{dataset_ctx[:1000] if dataset_ctx else "No active dataset context"}

Explain this error to the user in 3 short, clear sections:
1. 💡 **What went wrong** (in simple plain English)
2. 🛠️ **How to fix it** (step-by-step actionable advice)
3. ⚡ **Quick Tip** (how to prevent this error next time)

Keep the response friendly, actionable, and formatted in clean Markdown.
"""

    try:
        async with httpx.AsyncClient(timeout=25.0) as client:
            resp = await client.post(
                f"{settings.ollama_base_url.rstrip('/')}/api/generate",
                json={
                    "model": settings.ollama_model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {"max_tokens": 450, "temperature": 0.3},
                },
            )
            if resp.status_code == 200:
                explanation = resp.json().get("response", "").strip()
                return {"explanation": explanation, "available": True}
    except Exception:
        pass

    return {
        "explanation": (
            "### 🔍 AI Diagnostic Summary\n\n"
            f"**Recorded Exception:** `{error_message[:200]}`\n\n"
            "### 🛠️ Recommended Action:\n"
            "• Verify dataset headers and data types.\n"
            "• Auto-preprocessing will automatically drop high-cardinality noise columns.\n"
        ),
        "available": False,
    }
