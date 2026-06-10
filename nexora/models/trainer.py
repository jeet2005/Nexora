"""Model training and leaderboard construction."""

from __future__ import annotations

import time

import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    mean_absolute_error,
    mean_squared_error,
    r2_score,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline

from nexora.models.registry import get_models_for_task
from nexora.types import (
    ModelResult,
    ModelSpec,
    PreprocessingBundle,
    TaskType,
    TrainingArtifacts,
)


def train_models(
    df: pd.DataFrame,
    target: str,
    task_type: TaskType,
    preprocessing: PreprocessingBundle,
    *,
    max_models: int | None = 6,
    model_names: list[str] | None = None,
    test_size: float = 0.2,
    random_state: int = 42,
) -> TrainingArtifacts:
    """Train eligible models and return ranked artifacts.

    Args:
        df: Original training dataframe.
        target: Target column name.
        task_type: Supervised task type.
        preprocessing: Preprocessing bundle from `build_preprocessing`.
        max_models: Optional cap on model count.
        model_names: Optional model names to train.
        test_size: Holdout split ratio.
        random_state: Reproducible random seed.

    Returns:
        TrainingArtifacts containing leaderboard rows and fitted best pipeline.

    Example:
        `artifacts = train_models(df, "price", "regression", bundle)`
    """

    frame = preprocessing.training_frame
    feature_cols = preprocessing.schema.feature_columns
    X = frame[feature_cols]
    y = frame[target]
    specs = _select_specs(
        get_models_for_task(task_type),
        len(frame),
        max_models=max_models,
        model_names=model_names,
    )
    if not specs:
        raise ValueError("No eligible models were selected for training.")

    primary_metric = "accuracy" if task_type == "classification" else "r2"

    # Handle single-class targets gracefully by using a dummy model.
    if y.nunique() == 1:
        # Choose appropriate dummy model based on task type.
        if task_type == "classification":
            from sklearn.dummy import DummyClassifier
            dummy_model = DummyClassifier(strategy="most_frequent")
        else:
            from sklearn.dummy import DummyRegressor
            dummy_model = DummyRegressor()
        pipeline = Pipeline([
            ("preprocess", clone(preprocessing.transformer)),
            ("model", dummy_model),
        ])
        pipeline.fit(X, y)
        pred = pipeline.predict(X)
        metrics = _score_predictions(pipeline, X, y, pred, task_type)
        best_result = ModelResult(
            model_id="dummy",
            model_name="DummyModel",
            family="dummy",
            status="completed",
            primary_metric=primary_metric,
            primary_score=metrics[primary_metric] if primary_metric in metrics else 0.0,
            metrics=metrics,
            train_time_sec=0.0,
            speed="fast",
        )
        results = [best_result]
        best_pipeline = pipeline
        preprocessing.schema.transformed_feature_names = _feature_names(best_pipeline)
        return TrainingArtifacts(
            task_type=task_type,
            target=target,
            primary_metric=primary_metric,
            results=results,
            best_result=best_result,
            best_pipeline=best_pipeline,
            model_specs={"dummy": ModelSpec(model_id="dummy", model_name="DummyModel", family="dummy", task_type=task_type, import_path="sklearn.dummy", class_name="DummyClassifier" if task_type == "classification" else "DummyRegressor", params={}, speed="fast")},
            preprocessing=preprocessing,
        )

    stratify = _stratify_target(y, task_type)
    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=test_size,
        random_state=random_state,
        stratify=stratify,
    )

    results: list[ModelResult] = []
    best_pipeline: Pipeline | None = None
    best_result: ModelResult | None = None
    # primary_metric already set above

    mlflow_available = False
    try:
        import mlflow
        mlflow_available = True
        mlflow.autolog(silent=True, disable=False)
        mlflow.start_run(run_name=f"nexora_session_{int(time.time())}")
    except ImportError:
        pass

    try:
        for spec in specs:
            start = time.perf_counter()
            
            if mlflow_available:
                mlflow.start_run(run_name=spec.model_name, nested=True)
                
            try:
                pipeline = Pipeline(
                    steps=[
                        ("preprocess", clone(preprocessing.transformer)),
                        ("model", spec.factory()),
                    ]
                )
                pipeline.fit(X_train, y_train)
                pred = pipeline.predict(X_test)
                metrics = _score_predictions(pipeline, X_test, y_test, pred, task_type)
                elapsed = round(time.perf_counter() - start, 3)
                result = ModelResult(
                    model_id=spec.model_id,
                    model_name=spec.model_name,
                    family=spec.family,
                    status="completed",
                    primary_metric=primary_metric,
                    primary_score=metrics[primary_metric],
                    metrics=metrics,
                    train_time_sec=elapsed,
                    speed=spec.speed,
                )
                
                if mlflow_available:
                    mlflow.log_metrics(metrics)
                    
                if best_result is None or result.primary_score > best_result.primary_score:
                    best_result = result
                    best_pipeline = pipeline
            except Exception as exc:
                result = ModelResult(
                    model_id=spec.model_id,
                    model_name=spec.model_name,
                    family=spec.family,
                    status="failed",
                    primary_metric=primary_metric,
                    primary_score=float("-inf"),
                    metrics={},
                    train_time_sec=round(time.perf_counter() - start, 3),
                    speed=spec.speed,
                    error=str(exc)[:300],
                )
            finally:
                if mlflow_available:
                    mlflow.end_run()
                    
            results.append(result)

        if best_pipeline is None or best_result is None:
            errors = "; ".join(
                f"{result.model_name}: {result.error}" for result in results if result.error
            )
            raise RuntimeError(f"All models failed during training. {errors}")
            
    finally:
        if mlflow_available:
            mlflow.end_run()

    results = sorted(
        results,
        key=lambda result: (
            result.status == "completed",
            result.primary_score,
        ),
        reverse=True,
    )
    preprocessing.schema.transformed_feature_names = _feature_names(best_pipeline)
    return TrainingArtifacts(
        task_type=task_type,
        target=target,
        primary_metric=primary_metric,
        results=results,
        best_result=best_result,
        best_pipeline=best_pipeline,
        model_specs={spec.model_id: spec for spec in specs},
        preprocessing=preprocessing,
    )


def _select_specs(
    specs: list[ModelSpec],
    n_samples: int,
    *,
    max_models: int | None,
    model_names: list[str] | None,
) -> list[ModelSpec]:
    selected = [
        spec
        for spec in specs
        if n_samples >= spec.min_samples
        and (spec.max_samples is None or n_samples <= spec.max_samples)
    ]
    if model_names:
        requested = []
        for name in model_names:
            match = next((spec for spec in selected if spec.matches(name)), None)
            if match is None:
                raise ValueError(f"Model is not in the {selected[0].task_type} registry: {name}")
            requested.append(match)
        selected = requested
    if max_models is not None:
        selected = selected[:max_models]
    return selected


def _stratify_target(y: pd.Series, task_type: TaskType) -> pd.Series | None:
    if task_type != "classification":
        return None
    counts = y.value_counts(dropna=False)
    if counts.empty or counts.min() < 2:
        return None
    return y


def _score_predictions(
    pipeline: Pipeline,
    X_test: pd.DataFrame,
    y_test: pd.Series,
    pred: np.ndarray,
    task_type: TaskType,
) -> dict[str, float]:
    if task_type == "classification":
        metrics = {
            "accuracy": round(float(accuracy_score(y_test, pred)), 4),
            "f1": round(float(f1_score(y_test, pred, average="weighted", zero_division=0)), 4),
        }
        try:
            model = pipeline.named_steps["model"]
            if hasattr(model, "predict_proba") and y_test.nunique(dropna=False) == 2:
                proba = pipeline.predict_proba(X_test)[:, 1]
                metrics["roc_auc"] = round(float(roc_auc_score(y_test, proba)), 4)
        except Exception:
            pass
        return metrics

    mae = mean_absolute_error(y_test, pred)
    rmse = np.sqrt(mean_squared_error(y_test, pred))
    r2 = r2_score(y_test, pred)
    return {
        "mae": round(float(mae), 4),
        "rmse": round(float(rmse), 4),
        "r2": round(float(r2), 4),
    }


def _feature_names(pipeline: Pipeline) -> list[str]:
    preprocessor = pipeline.named_steps["preprocess"]
    try:
        return [str(name) for name in preprocessor.get_feature_names_out()]
    except Exception:
        return []
