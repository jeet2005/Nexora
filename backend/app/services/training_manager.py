"""Background training jobs with WebSocket broadcast."""

from __future__ import annotations

import asyncio
import threading
from pathlib import Path
from typing import Any

from app.config import settings
from app.models.schemas import ModelResult, TrainingResult
from app.services.experiment_service import create_experiment
from app.services.session_store import load_processed_df, load_session, save_session
from app.services.training_engine import run_training

_jobs: dict[str, dict[str, Any]] = {}
_subscribers: dict[str, list[asyncio.Queue]] = {}
_lock = threading.Lock()


def _training_path(dataset_id: str) -> Path:
    return settings.upload_dir / f"{dataset_id}.training.json"


def save_training_result(dataset_id: str, result: TrainingResult) -> None:
    _training_path(dataset_id).write_text(
        result.model_dump_json(indent=2), encoding="utf-8"
    )


def load_training_result(dataset_id: str) -> TrainingResult | None:
    path = _training_path(dataset_id)
    if not path.exists():
        return None
    return TrainingResult.model_validate_json(path.read_text(encoding="utf-8"))


def get_job(dataset_id: str) -> dict[str, Any] | None:
    with _lock:
        return _jobs.get(dataset_id)


def subscribe(dataset_id: str) -> asyncio.Queue:
    q: asyncio.Queue = asyncio.Queue()
    _subscribers.setdefault(dataset_id, []).append(q)
    return q


def unsubscribe(dataset_id: str, q: asyncio.Queue) -> None:
    subs = _subscribers.get(dataset_id, [])
    if q in subs:
        subs.remove(q)


def _broadcast_sync(dataset_id: str, event: dict[str, Any]) -> None:
    subs = _subscribers.get(dataset_id, [])
    for q in subs:
        try:
            q.put_nowait(event)
        except Exception:
            pass


def _progress_handler(dataset_id: str):
    def handler(event: dict[str, Any]):
        with _lock:
            job = _jobs.get(dataset_id)
            if job:
                job["last_event"] = event
                if event.get("event") == "model_completed":
                    job["completed"] = event.get("index", 0)
                if event.get("event") == "training_started":
                    job["total"] = event.get("total_models", 0)
        _broadcast_sync(dataset_id, event)

    return handler


def start_training(
    dataset_id: str,
    max_models: int | None = None,
    test_split: float | None = None,
    cv_folds: int | None = None,
    timeout_sec: int | None = None,
    seed: int | None = None,
) -> dict[str, Any]:
    with _lock:
        if dataset_id in _jobs and _jobs[dataset_id].get("status") == "running":
            return {"status": "already_running", "job": _jobs[dataset_id]}

    session = load_session(dataset_id)
    if not session or session.status != "preprocessed" or not session.target_column:
        raise ValueError(
            "Dataset must be preprocessed with a target column before training."
        )

    df = load_processed_df(dataset_id)
    if df is None:
        raise ValueError("Processed dataset not found.")

    problem_type = session.problem_type or "classification"
    if problem_type not in ("classification", "regression"):
        problem_type = "classification"

    _jobs[dataset_id] = {
        "dataset_id": dataset_id,
        "status": "running",
        "completed": 0,
        "total": 0,
        "started_at": __import__("time").time(),
    }

    def _run():
        try:
            summary = run_training(
                df,
                session.target_column,
                problem_type,
                on_progress=_progress_handler(dataset_id),
                max_models=max_models,
                test_split=test_split,
                cv_folds=cv_folds,
                timeout_sec=timeout_sec,
                seed=seed,
            )

            best = summary.get("best_model")
            training_result = TrainingResult(
                dataset_id=dataset_id,
                problem_type=problem_type,
                primary_metric=summary["primary_metric"],
                total_attempted=summary["total_attempted"],
                total_completed=summary["total_completed"],
                total_failed=summary["total_failed"],
                registry_available=summary["registry_available"],
                best_model=ModelResult(**best) if best else None,
                leaderboard=[ModelResult(**r) for r in summary["leaderboard"]],
            )

            save_training_result(dataset_id, training_result)
            create_experiment(
                dataset_id=dataset_id,
                kind="benchmark",
                problem_type=problem_type,
                target_column=session.target_column,
                config=summary.get("config", {}),
                metrics={
                    "total_attempted": summary["total_attempted"],
                    "total_completed": summary["total_completed"],
                    "total_failed": summary["total_failed"],
                    "primary_metric": summary["primary_metric"],
                },
                models=summary.get("leaderboard", []),
                best_model=best,
                artifact_refs={"training_result": str(
                    _training_path(dataset_id))},
            )

            sess = load_session(dataset_id)
            if sess:
                sess.training_result = training_result
                sess.status = "trained"
                save_session(sess)

            with _lock:
                _jobs[dataset_id]["status"] = "completed"
                _jobs[dataset_id]["summary"] = summary

            _broadcast_sync(
                dataset_id, {"event": "training_complete", "summary": summary}
            )
        except Exception as e:
            with _lock:
                _jobs[dataset_id]["status"] = "failed"
                _jobs[dataset_id]["error"] = str(e)
            _broadcast_sync(
                dataset_id, {"event": "training_failed", "error": str(e)})

    thread = threading.Thread(target=_run, daemon=True)
    thread.start()

    return {"status": "started", "dataset_id": dataset_id}
