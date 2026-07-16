"""Train and benchmark models with live progress callbacks."""

from __future__ import annotations

import time
import warnings
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as FuturesTimeout
from typing import Any

import numpy as np
import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    mean_absolute_error,
    mean_squared_error,
    r2_score,
    roc_auc_score,
)
from sklearn.model_selection import cross_val_score, train_test_split

from app.config import settings
from app.services.model_registry import ModelSpec, filter_models, get_models_for_problem
from app.services.timing_estimator import estimate_model_seconds

warnings.filterwarnings("ignore")

ProgressCallback = Callable[[dict[str, Any]], None]


def _prepare_xy(
    df: pd.DataFrame, target: str
) -> tuple[np.ndarray, np.ndarray, list[str]]:
    if target not in df.columns:
        raise ValueError(f"Target '{target}' not in dataframe.")
    feature_cols = [c for c in df.columns if c != target]
    X = df[feature_cols].values
    y = df[target].values
    return X, y, feature_cols


def _metric_label(problem_type: str) -> str:
    return "accuracy" if problem_type == "classification" else "r2"


def _score_model(
    model,
    X_train,
    X_test,
    y_train,
    y_test,
    problem_type: str,
) -> dict[str, float]:
    model.fit(X_train, y_train)
    pred = model.predict(X_test)

    if problem_type == "classification":
        acc = accuracy_score(y_test, pred)
        f1 = f1_score(y_test, pred, average="weighted", zero_division=0)
        metrics = {"accuracy": round(float(acc), 4), "f1": round(float(f1), 4)}
        try:
            if hasattr(model, "predict_proba") and len(np.unique(y_test)) == 2:
                proba = model.predict_proba(X_test)[:, 1]
                metrics["roc_auc"] = round(
                    float(roc_auc_score(y_test, proba)), 4)
        except Exception:
            pass
        metrics["primary"] = metrics["accuracy"]
        return metrics

    mae = mean_absolute_error(y_test, pred)
    rmse = float(np.sqrt(mean_squared_error(y_test, pred)))
    r2 = r2_score(y_test, pred)
    metrics = {
        "mae": round(float(mae), 4),
        "rmse": round(rmse, 4),
        "r2": round(float(r2), 4),
    }
    metrics["primary"] = metrics["r2"]
    return metrics


def _train_one(
    spec: ModelSpec,
    X: np.ndarray,
    y: np.ndarray,
    problem_type: str,
    use_cv: bool,
    test_split: float,
    cv_folds: int,
    seed: int,
) -> dict[str, Any]:
    t0 = time.perf_counter()
    try:
        model = spec.factory()

        if use_cv and len(y) >= 30:
            scoring = "accuracy" if problem_type == "classification" else "r2"
            scores = cross_val_score(
                model, X, y, cv=min(cv_folds, 5), scoring=scoring, n_jobs=1
            )
            primary = float(np.mean(scores))
            metrics = {scoring: round(primary, 4),
                       "primary": round(primary, 4)}
            if problem_type == "classification":
                metrics["accuracy"] = metrics["primary"]
            else:
                metrics["r2"] = metrics["primary"]
        else:
            X_train, X_test, y_train, y_test = train_test_split(
                X,
                y,
                test_size=test_split,
                random_state=seed,
            )
            metrics = _score_model(
                model, X_train, X_test, y_train, y_test, problem_type
            )

        elapsed = round(time.perf_counter() - t0, 3)
        speed_label = "fast" if elapsed < 2 else (
            "medium" if elapsed < 10 else "slow")

        return {
            "model_id": spec.id,
            "model_name": spec.name,
            "family": spec.family,
            "status": "completed",
            "metrics": metrics,
            "primary_score": metrics["primary"],
            "train_time_sec": elapsed,
            "speed": speed_label,
            "error": None,
        }
    except Exception as e:
        elapsed = round(time.perf_counter() - t0, 3)
        return {
            "model_id": spec.id,
            "model_name": spec.name,
            "family": spec.family,
            "status": "failed",
            "metrics": {},
            "primary_score": -1.0,
            "train_time_sec": elapsed,
            "speed": spec.speed,
            "error": str(e)[:200],
        }


def run_training(
    df: pd.DataFrame,
    target_column: str,
    problem_type: str,
    on_progress: ProgressCallback | None = None,
    max_models: int | None = None,
    test_split: float | None = None,
    cv_folds: int | None = None,
    timeout_sec: int | None = None,
    seed: int | None = None,
) -> dict[str, Any]:
    X, y, feature_cols = _prepare_xy(df, target_column)
    n = len(y)

    all_specs = get_models_for_problem(problem_type)
    skip_slow = n > 10_000
    specs = filter_models(all_specs, n, skip_slow=skip_slow)

    if max_models and len(specs) > max_models:
        # Prioritize fast/medium, diverse families
        fast = [s for s in specs if s.speed == "fast"]
        medium = [s for s in specs if s.speed == "medium"]
        slow = [s for s in specs if s.speed == "slow"]
        specs = fast + medium + \
            slow[: max(0, max_models - len(fast) - len(medium))]
        specs = specs[:max_models]

    use_cv = n < 5000
    results: list[dict] = []
    total = len(specs)
    per_model_estimates = [
        estimate_model_seconds(spec, n, len(feature_cols), use_cv) for spec in specs
    ]
    expected_total_sec = max(5, int(round(sum(per_model_estimates))))
    training_started_at = time.perf_counter()
    test_split = test_split if test_split is not None else settings.train_test_split
    cv_folds = cv_folds if cv_folds is not None else settings.cv_folds
    timeout_sec = timeout_sec if timeout_sec is not None else settings.model_timeout_sec
    seed = seed if seed is not None else settings.random_seed

    if on_progress:
        on_progress(
            {
                "event": "training_started",
                "total_models": total,
                "registry_total": len(all_specs),
                "problem_type": problem_type,
                "expected_total_sec": expected_total_sec,
                "expected_per_model_sec": round(expected_total_sec / max(total, 1), 1),
                "config": {
                    "test_split": test_split,
                    "cv_folds": cv_folds,
                    "timeout_sec": timeout_sec,
                    "seed": seed,
                },
            }
        )

    for i, spec in enumerate(specs):
        if on_progress:
            on_progress(
                {
                    "event": "model_started",
                    "index": i + 1,
                    "total": total,
                    "model_id": spec.id,
                    "model_name": spec.name,
                    "family": spec.family,
                }
            )

        with ThreadPoolExecutor(max_workers=1) as ex:
            future = ex.submit(
                _train_one, spec, X, y, problem_type, use_cv, test_split, cv_folds, seed
            )
            try:
                result = future.result(timeout=timeout_sec)
            except FuturesTimeout:
                result = {
                    "model_id": spec.id,
                    "model_name": spec.name,
                    "family": spec.family,
                    "status": "timeout",
                    "metrics": {},
                    "primary_score": -1.0,
                    "train_time_sec": timeout_sec,
                    "speed": spec.speed,
                    "error": "Training timeout",
                }

        results.append(result)

        completed = [r for r in results if r["status"] == "completed"]
        leaderboard = sorted(completed, key=lambda r: r["primary_score"], reverse=True)[
            :20
        ]

        if on_progress:
            elapsed = round(time.perf_counter() - training_started_at, 2)
            completed_count = i + 1
            avg_per_model = elapsed / max(completed_count, 1)
            remaining = max(
                0, int(round(avg_per_model * (total - completed_count))))
            on_progress(
                {
                    "event": "model_completed",
                    "index": i + 1,
                    "total": total,
                    "result": result,
                    "leaderboard": leaderboard,
                    "completed_count": len(completed),
                    "failed_count": sum(
                        1 for r in results if r["status"] != "completed"
                    ),
                    "elapsed_sec": elapsed,
                    "estimated_remaining_sec": remaining,
                    "expected_total_sec": expected_total_sec,
                }
            )

    completed = [r for r in results if r["status"] == "completed"]
    failed = [r for r in results if r["status"] != "completed"]
    leaderboard = sorted(
        completed, key=lambda r: r["primary_score"], reverse=True)

    summary = {
        "total_attempted": total,
        "total_completed": len(completed),
        "total_failed": len(failed),
        "registry_available": len(all_specs),
        "primary_metric": _metric_label(problem_type),
        "best_model": leaderboard[0] if leaderboard else None,
        "leaderboard": leaderboard[:50],
        "all_results": results,
        "feature_count": len(feature_cols),
        "sample_count": n,
        "config": {
            "test_split": test_split,
            "cv_folds": cv_folds,
            "timeout_sec": timeout_sec,
            "seed": seed,
            "use_cv": use_cv,
            "max_models": max_models,
        },
    }

    if on_progress:
        on_progress({"event": "training_complete", "summary": summary})

    return summary
