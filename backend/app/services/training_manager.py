"""Training job orchestration: validates requests and enqueues Celery jobs.

This used to spin up a `threading.Thread` per job and track progress in
module-level Python dicts (`_jobs`, `_subscribers`) — see git history for
the old version. That doesn't scale past a single process and loses all
job state on restart.

Now `start_training` does the same upfront validation as before, but then
just enqueues `app.tasks.training_tasks.run_benchmark_task` on Celery and
returns immediately. The actual training work, progress broadcasting, and
result persistence all happen inside the Celery task; job status and
progress events live in Redis (see `app.services.job_events`) instead of
in-process memory, so they're visible to whichever process the WebSocket
happens to be connected to.
"""

from __future__ import annotations

import time
import uuid
from pathlib import Path
from typing import Any

from fastapi import BackgroundTasks

from app.config import settings
from app.models.schemas import TrainingResult
from app.services import job_events
from app.services.session_store import load_processed_df, load_session


def training_artifact_path(dataset_id: str) -> Path:
    return settings.upload_dir / f"{dataset_id}.training.json"


def save_training_result(dataset_id: str, result: TrainingResult) -> None:
    training_artifact_path(dataset_id).write_text(
        result.model_dump_json(indent=2), encoding="utf-8"
    )


def load_training_result(dataset_id: str) -> TrainingResult | None:
    path = training_artifact_path(dataset_id)
    if not path.exists():
        return None
    return TrainingResult.model_validate_json(path.read_text(encoding="utf-8"))


def get_job(dataset_id: str) -> dict[str, Any] | None:
    return job_events.get_job(dataset_id)


def start_training(
    dataset_id: str,
    background_tasks: BackgroundTasks,
    max_models: int | None = None,
    test_split: float | None = None,
    cv_folds: int | None = None,
    timeout_sec: int | None = None,
    seed: int | None = None,
) -> dict[str, Any]:
    existing = job_events.get_job(dataset_id)
    if existing and existing.get("status") == "running":
        return {"status": "already_running", "job": existing}

    # Same validation as before, done synchronously in the request handler
    # so bad requests still fail fast with a clear error instead of
    # silently failing inside a worker a moment later.
    session = load_session(dataset_id)
    if not session or session.status != "preprocessed" or not session.target_column:
        raise ValueError(
            "Dataset must be preprocessed with a target column before training."
        )

    if load_processed_df(dataset_id) is None:
        raise ValueError("Processed dataset not found.")

    job_events.set_job(
        dataset_id,
        {
            "dataset_id": dataset_id,
            "status": "running",
            "completed": 0,
            "total": 0,
            "started_at": time.time(),
        },
    )

    # Imported lazily to avoid a circular import: training_tasks imports
    # save_training_result/training_artifact_path from this module.
    from app.tasks.training_tasks import run_benchmark_task

    task_id = str(uuid.uuid4())

    background_tasks.add_task(
        run_benchmark_task,
        dataset_id=dataset_id,
        max_models=max_models,
        test_split=test_split,
        cv_folds=cv_folds,
        timeout_sec=timeout_sec,
        seed=seed,
    )

    job_events.update_job(dataset_id, task_id=task_id)

    return {"status": "started", "dataset_id": dataset_id, "task_id": task_id}
