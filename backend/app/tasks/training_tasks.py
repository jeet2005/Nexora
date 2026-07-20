"""Celery task for running the model benchmark training job.

This is a direct port of the body of the old `training_manager._run()`
thread function — same validation, same call into `run_training`, same
`TrainingResult`/experiment/session bookkeeping — just running inside a
Celery worker instead of a `threading.Thread`, and reporting progress and
job status through `app.services.job_events` (Redis) instead of
module-level dicts.
"""

from __future__ import annotations

from typing import Any

from app.models.schemas import ModelResult, TrainingResult
from app.services import job_events
from app.services.experiment_service import create_experiment
from app.services.session_store import load_processed_df, load_session, save_session
from app.services.training_engine import run_training
from app.services.training_manager import save_training_result, training_artifact_path


def run_benchmark_task(
    dataset_id: str,
    max_models: int | None = None,
    test_split: float | None = None,
    cv_folds: int | None = None,
    timeout_sec: int | None = None,
    seed: int | None = None,
) -> dict[str, Any]:
    session = load_session(dataset_id)
    if not session or session.status != "preprocessed" or not session.target_column:
        error = "Dataset must be preprocessed with a target column before training."
        job_events.update_job(dataset_id, status="failed", error=error)
        job_events.publish_event(dataset_id, {"event": "training_failed", "error": error})
        return {"status": "failed", "error": error}

    df = load_processed_df(dataset_id)
    if df is None:
        error = "Processed dataset not found."
        job_events.update_job(dataset_id, status="failed", error=error)
        job_events.publish_event(dataset_id, {"event": "training_failed", "error": error})
        return {"status": "failed", "error": error}

    problem_type = session.problem_type or "classification"
    if problem_type not in ("classification", "regression"):
        problem_type = "classification"

    def on_progress(event: dict[str, Any]) -> None:
        if event.get("event") == "model_completed":
            job_events.update_job(dataset_id, completed=event.get("index", 0))
        if event.get("event") == "training_started":
            job_events.update_job(dataset_id, total=event.get("total_models", 0))
        job_events.publish_event(dataset_id, event)

    try:
        summary = run_training(
            df,
            session.target_column,
            problem_type,
            on_progress=on_progress,
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
            artifact_refs={"training_result": str(training_artifact_path(dataset_id))},
        )

        sess = load_session(dataset_id)
        if sess:
            sess.training_result = training_result
            sess.status = "trained"
            save_session(sess)

        job_events.update_job(dataset_id, status="completed", summary=summary)
        job_events.publish_event(
            dataset_id, {"event": "training_complete", "summary": summary}
        )
        return {"status": "completed"}
    except Exception as e:
        job_events.update_job(dataset_id, status="failed", error=str(e))
        job_events.publish_event(dataset_id, {"event": "training_failed", "error": str(e)})
        # BackgroundTask will just finish.
        raise
