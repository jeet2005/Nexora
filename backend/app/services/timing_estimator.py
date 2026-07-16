"""Estimate expected runtime for Nexora pipeline operations."""

from __future__ import annotations

from typing import Any

import pandas as pd

from app.services.model_registry import ModelSpec, filter_models, get_models_for_problem

_SPEED_BASE_SEC = {"fast": 0.8, "medium": 3.5, "slow": 12.0}


def _dataset_scale_factor(n_rows: int, n_cols: int) -> float:
    factor = 1.0
    if n_rows > 2_000:
        factor += 1.5
    if n_rows > 10_000:
        factor += 4.0
    if n_cols > 30:
        factor += 1.0
    if n_cols > 100:
        factor += 3.0
    return factor


def estimate_model_seconds(
    spec: ModelSpec, n_rows: int, n_cols: int, use_cv: bool
) -> float:
    base = _SPEED_BASE_SEC.get(spec.speed, 3.5)
    scaled = base * _dataset_scale_factor(n_rows, n_cols)
    if use_cv and n_rows >= 30:
        scaled *= 1.8
    return max(0.5, scaled)


def _select_specs(
    df: pd.DataFrame,
    problem_type: str,
    max_models: int | None,
) -> list[ModelSpec]:
    n = len(df)
    all_specs = get_models_for_problem(problem_type)
    skip_slow = n > 10_000
    specs = filter_models(all_specs, n, skip_slow=skip_slow)
    if max_models and len(specs) > max_models:
        fast = [s for s in specs if s.speed == "fast"]
        medium = [s for s in specs if s.speed == "medium"]
        slow = [s for s in specs if s.speed == "slow"]
        specs = fast + medium + \
            slow[: max(0, max_models - len(fast) - len(medium))]
        specs = specs[:max_models]
    return specs


def estimate_benchmark_seconds(
    df: pd.DataFrame,
    problem_type: str,
    max_models: int | None = None,
) -> dict[str, Any]:
    n_rows, n_cols = len(df), len(df.columns)
    use_cv = n_rows < 5000
    specs = _select_specs(df, problem_type, max_models)
    per_model = [estimate_model_seconds(
        s, n_rows, n_cols, use_cv) for s in specs]
    total = sum(per_model)
    return {
        "seconds": max(5, int(round(total))),
        "model_count": len(specs),
        "per_model_avg_sec": round(total / max(len(specs), 1), 1),
    }


def estimate_preprocess_seconds(df: pd.DataFrame) -> int:
    n_rows, n_cols = len(df), len(df.columns)
    base = 1.0 + (n_rows / 5000) + (n_cols / 40)
    return max(2, int(round(base)))


def estimate_production_train_seconds(
    df: pd.DataFrame,
    model_count: int,
    speeds: list[str] | None = None,
) -> int:
    n_rows, n_cols = len(df), len(df.columns)
    factor = _dataset_scale_factor(n_rows, n_cols)
    if speeds:
        per = sum(_SPEED_BASE_SEC.get(s, 3.5) for s in speeds) * factor
    else:
        per = model_count * 2.5 * factor
    return max(3, int(round(per)))


def estimate_time_series_seconds(n_rows: int) -> int:
    return max(1, int(round(0.5 + n_rows / 2000)))


def estimate_clustering_seconds(n_rows: int, n_cols: int, n_clusters: int = 3) -> int:
    base = 1.0 + (n_rows * n_cols) / 50_000 + n_clusters * 0.3
    return max(2, int(round(base)))


def estimate_all(
    df: pd.DataFrame,
    problem_type: str = "classification",
    max_models: int | None = None,
    production_model_count: int = 2,
) -> dict[str, Any]:
    benchmark = estimate_benchmark_seconds(df, problem_type, max_models)
    return {
        "preprocess_sec": estimate_preprocess_seconds(df),
        "benchmark_sec": benchmark["seconds"],
        "benchmark_model_count": benchmark["model_count"],
        "benchmark_per_model_avg_sec": benchmark["per_model_avg_sec"],
        "production_train_sec": estimate_production_train_seconds(
            df, production_model_count
        ),
        "time_series_sec": estimate_time_series_seconds(len(df)),
        "clustering_sec": estimate_clustering_seconds(len(df), len(df.columns)),
    }
