"""Local experiment tracking for terminal and Jupyter package runs."""

from __future__ import annotations

import json
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class ExperimentRecord:
    """A persistent local training/production/clustering/forecast run."""

    run_id: str
    kind: str
    created_at: str
    source_name: str
    target_column: str | None
    problem_type: str
    config: dict[str, Any] = field(default_factory=dict)
    metrics: dict[str, Any] = field(default_factory=dict)
    models: list[dict[str, Any]] = field(default_factory=list)
    best_model: dict[str, Any] | None = None
    artifact_refs: dict[str, str] = field(default_factory=dict)


def experiment_store(path: str | Path | None = None) -> Path:
    """Return the JSONL path used for local experiments."""

    if path is not None:
        return Path(path).expanduser().resolve()
    return (Path.cwd() / ".nexora" / "experiments.jsonl").resolve()


def save_experiment(record: ExperimentRecord, path: str | Path | None = None) -> Path:
    """Append an experiment record and return the store path."""

    store = experiment_store(path)
    store.parent.mkdir(parents=True, exist_ok=True)
    with store.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(asdict(record), default=str) + "\n")
    return store


def list_experiments(path: str | Path | None = None) -> list[ExperimentRecord]:
    """Read local experiment records."""

    store = experiment_store(path)
    if not store.exists():
        return []
    records: list[ExperimentRecord] = []
    for line in store.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            records.append(ExperimentRecord(**json.loads(line)))
        except (TypeError, ValueError, json.JSONDecodeError):
            continue
    return records


def create_training_experiment(
    report, *, path: str | Path | None = None
) -> ExperimentRecord:
    """Create and persist an experiment record from a NexoraReport."""

    best = report.best_result
    record = ExperimentRecord(
        run_id=str(uuid.uuid4()),
        kind="benchmark",
        created_at=datetime.now(timezone.utc).isoformat(),
        source_name=report.source_name,
        target_column=report.target,
        problem_type=report.task_type,
        config={
            "test_size": report.training_settings.test_size,
            "cv_folds": report.training_settings.cv_folds,
            "max_models": report.training_settings.max_models,
            "timeout_sec": report.training_settings.timeout_sec,
            "random_state": report.training_settings.random_state,
            "early_stopping": report.training_settings.early_stopping,
        },
        metrics={
            "primary_metric": report.best_score_label,
            "best_primary_score": report.best_score,
            "model_count": len(
                [item for item in report.results if item.status == "completed"]
            ),
        },
        models=[
            {
                "model_id": item.model_id,
                "model_name": item.model_name,
                "family": item.family,
                "status": item.status,
                "primary_score": item.primary_score,
                "metrics": item.metrics,
                "train_time_sec": item.train_time_sec,
            }
            for item in report.results
        ],
        best_model=None
        if best is None
        else {
            "model_id": best.model_id,
            "model_name": best.model_name,
            "family": best.family,
            "primary_score": best.primary_score,
            "metrics": best.metrics,
        },
    )
    save_experiment(record, path)
    return record
