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
    from app.models.schemas import DatasetSession, FeatureSelection, ProblemDetection
    from app.services.dataset_store import load_dataframe
    from app.services.preprocessing_engine import PreprocessingConfig, preprocess
    from app.services.problem_detector import (
        detect_problem_type,
        suggest_feature_columns,
    )
    from app.services.session_store import save_processed_df, save_session

    df = load_dataframe(dataset_id)
    if df is None:
        raise ValueError("Dataset not found.")

    if not session or not session.target_column:
        target_col = df.columns[-1]
        detection_raw = detect_problem_type(df, target_col)
        problem_type = detection_raw.get("problem_type", "classification")
        if problem_type not in ("classification", "regression"):
            problem_type = "classification"
        features_raw = suggest_feature_columns(df, target_col)
        feature_cols = [c for c in features_raw["feature_columns"]]
        session = DatasetSession(
            dataset_id=dataset_id,
            target_column=target_col,
            problem_type=problem_type,
            problem_detection=ProblemDetection(**detection_raw),
            feature_selection=FeatureSelection(
                feature_columns=feature_cols,
                excluded_id_columns=features_raw.get("excluded_id_columns", []),
                excluded_datetime_columns=features_raw.get(
                    "excluded_datetime_columns", []
                ),
            ),
            status="configured",
        )
        save_session(session)

    if load_processed_df(dataset_id) is None or session.status != "preprocessed":
        config = PreprocessingConfig()
        processed, steps_raw, meta_raw = preprocess(
            df,
            session.target_column,
            session.problem_type or "classification",
            config,
        )
        save_processed_df(dataset_id, processed)
        session.status = "preprocessed"
        save_session(session)

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
