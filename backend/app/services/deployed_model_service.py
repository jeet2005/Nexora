"""Train and serve selected, persisted prediction models from user-facing inputs."""

from __future__ import annotations

import hashlib
import json
import secrets
import time
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    mean_absolute_error,
    mean_squared_error,
    r2_score,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from app.config import settings
from app.models.schemas import (
    DeployableModelOption,
    DeployedModel,
    ModelDeployment,
    PredictionContribution,
    PredictionExplainResponse,
    PredictionInputField,
    PredictionOutput,
    PredictionReceipt,
    ProductionStatus,
)
from app.services.dataset_analyzer import _infer_datetime, _is_id_like
from app.services.dataset_store import load_dataframe
from app.services.dataset_validator import load_dataframe as parse_dataframe
from app.services.experiment_service import create_experiment
from app.services.model_registry import ModelSpec, get_models_for_problem
from app.services.session_store import load_session

RECOMMENDED_IDS = {
    "classification": [
        "lr_l2_c1.0",
        "rf_100_d10",
        "gb_100_lr0.1",
        "xgb_100_d5_lr0.1",
        "lgbm_100_d5_lr0.1",
        "catboost_200_d6",
    ],
    "regression": [
        "linear_regression",
        "rfr_100_d10",
        "gbr_100_lr0.1",
        "xgbr_100_d5_lr0.1",
        "lgbmr_100_d5",
        "catboost_reg_200_d6",
    ],
}


def _models_dir(dataset_id: str) -> Path:
    path = settings.upload_dir / f"{dataset_id}.models"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _status_path(dataset_id: str) -> Path:
    return settings.upload_dir / f"{dataset_id}.production.json"


def _artifact_path(dataset_id: str, model_id: str) -> Path:
    return _models_dir(dataset_id) / f"{model_id}.joblib"


def model_artifact_path(dataset_id: str, model_id: str) -> Path:
    path = _artifact_path(dataset_id, model_id)
    if not path.exists():
        raise ValueError("Model artifact not found.")
    return path


def _batches_dir(dataset_id: str) -> Path:
    path = settings.upload_dir / f"{dataset_id}.batches"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _batch_meta_path(dataset_id: str, batch_id: str) -> Path:
    return _batches_dir(dataset_id) / f"{batch_id}.json"


def _batch_output_path(dataset_id: str, batch_id: str) -> Path:
    return _batches_dir(dataset_id) / f"{batch_id}.predictions.csv"


def _deployments_path(dataset_id: str) -> Path:
    return settings.upload_dir / f"{dataset_id}.deployments.json"


def _require_prediction_context(dataset_id: str) -> tuple[pd.DataFrame, str, str]:
    session = load_session(dataset_id)
    if not session or not session.target_column:
        raise ValueError("Select a prediction target first.")
    problem_type = session.problem_type or "classification"
    if problem_type not in ("classification", "regression"):
        raise ValueError(
            "Prediction Studio currently supports classification and regression targets."
        )

    df = load_dataframe(dataset_id)
    if df is None:
        raise ValueError("Dataset not found.")
    return df, session.target_column, problem_type


def list_deployable_models(dataset_id: str) -> dict[str, Any]:
    df, target, problem_type = _require_prediction_context(dataset_id)
    recommended = set(RECOMMENDED_IDS[problem_type])
    specs = get_models_for_problem(problem_type)
    options = [
        DeployableModelOption(
            model_id=spec.id,
            model_name=spec.name,
            family=spec.family,
            speed=spec.speed,
            recommended=spec.id in recommended,
        )
        for spec in specs
        if spec.speed != "slow" or spec.id in recommended
    ]
    options.sort(
        key=lambda model: (
            not model.recommended,
            model.speed != "fast",
            model.family,
            model.model_name,
        )
    )
    deployed = load_production_status(dataset_id)
    if deployed and (
        deployed.target_column != target or deployed.problem_type != problem_type
    ):
        deployed = None
    raw_features = _usable_feature_columns(df, target)
    excluded_ids = [
        str(column)
        for column in df.columns
        if column != target and _is_id_like(df[column])
    ]
    limitations = [
        "Time-series forecasting runs in Exploration Modes; date columns here become calendar features for supervised models.",
        "Clustering runs in Exploration Modes and does not produce saved prediction receipts.",
    ]
    if excluded_ids:
        limitations.insert(
            0,
            f"Identifier-like columns are excluded from training: {', '.join(excluded_ids[:4])}.",
        )
    return {
        "dataset_id": dataset_id,
        "target_column": target,
        "problem_type": problem_type,
        "available_models": options,
        "eligibility_reason": (
            f"{len(options)} {problem_type} models can train on `{target}` using "
            f"{len(raw_features)} usable input column{'s' if len(raw_features) != 1 else ''}."
        ),
        "limitations": limitations,
        "deployed": deployed,
    }


def load_production_status(dataset_id: str) -> ProductionStatus | None:
    path = _status_path(dataset_id)
    if not path.exists():
        return None
    return ProductionStatus.model_validate_json(path.read_text(encoding="utf-8"))


def train_selected_models(dataset_id: str, model_ids: list[str]) -> ProductionStatus:
    df, target, problem_type = _require_prediction_context(dataset_id)
    if not model_ids:
        raise ValueError("Select at least one model.")
    if len(model_ids) > 5:
        raise ValueError("Select up to five models for Prediction Studio.")

    all_specs = {
        spec.id: spec for spec in get_models_for_problem(problem_type)}
    unknown = [model_id for model_id in model_ids if model_id not in all_specs]
    if unknown:
        raise ValueError(f"Unknown model selection: {', '.join(unknown)}")

    raw_features = _usable_feature_columns(df, target)
    if not raw_features:
        raise ValueError("No usable input features remain for prediction.")

    input_fields = _input_fields(df, raw_features)
    datetime_features = [
        column for column in raw_features if _infer_datetime(df[column])
    ]
    X = _feature_frame(df, raw_features, datetime_features)
    y = df[target]
    usable = y.notna()
    X = X.loc[usable].reset_index(drop=True)
    y = y.loc[usable].reset_index(drop=True)
    if len(y) < 10:
        raise ValueError(
            "At least 10 rows with a target value are required for model training."
        )
    if problem_type == "classification" and y.nunique(dropna=True) < 2:
        raise ValueError(
            "The selected target must contain at least two classes.")

    if len(X) > 50_000:
        sampled = X.sample(50_000, random_state=42).index
        X = X.loc[sampled].reset_index(drop=True)
        y = y.loc[sampled].reset_index(drop=True)

    trained: list[DeployedModel] = []
    errors: list[str] = []
    for model_id in model_ids:
        spec = all_specs[model_id]
        try:
            descriptor, artifact = _train_one_selected(
                spec, X, y, problem_type, raw_features, datetime_features, input_fields
            )
            joblib.dump(artifact, _artifact_path(dataset_id, model_id))
            trained.append(descriptor)
        except Exception as exc:
            errors.append(f"{spec.name}: {str(exc)[:120]}")

    if not trained:
        raise ValueError(
            "Selected models could not be trained. " + " ".join(errors))

    status = ProductionStatus(
        dataset_id=dataset_id,
        target_column=target,
        problem_type=problem_type,
        input_fields=input_fields,
        models=trained,
        trained_at=datetime.now(UTC).isoformat(),
    )
    _status_path(dataset_id).write_text(
        status.model_dump_json(indent=2), encoding="utf-8"
    )
    create_experiment(
        dataset_id=dataset_id,
        kind="production",
        problem_type=problem_type,
        target_column=target,
        config={
            "model_ids": model_ids,
            "test_split": settings.train_test_split,
            "seed": settings.random_seed,
            "input_field_count": len(input_fields),
        },
        metrics={
            "model_count": len(trained),
            "best_primary_score": max(model.primary_score for model in trained),
        },
        models=[model.model_dump() for model in trained],
        best_model=max(
            trained, key=lambda model: model.primary_score).model_dump(),
        artifact_refs={
            model.model_id: str(_artifact_path(dataset_id, model.model_id))
            for model in trained
        },
    )
    return status


def run_saved_prediction(
    dataset_id: str,
    inputs: dict[str, Any],
    model_ids: list[str] | None = None,
) -> PredictionReceipt:
    _, target, problem_type = _require_prediction_context(dataset_id)
    status = load_production_status(dataset_id)
    if not status or not status.models:
        raise ValueError(
            "Train at least one selected model in Prediction Studio first."
        )
    if status.target_column != target or status.problem_type != problem_type:
        raise ValueError(
            "The target changed after these models were trained. Train selected models again."
        )

    selected = set(model_ids or [model.model_id for model in status.models])
    models = [model for model in status.models if model.model_id in selected]
    if not models:
        raise ValueError(
            "None of the requested models are trained and available.")

    submitted, assumed, warnings = _prepare_input_values(
        inputs, status.input_fields)
    raw_row = {**assumed, **submitted}
    raw_df = pd.DataFrame([raw_row])

    # Convert numeric fields to numeric dtype to avoid pandas object dtypes when None is present
    for field in status.input_fields:
        if field.name in raw_df.columns and field.kind == "number":
            raw_df[field.name] = pd.to_numeric(
                raw_df[field.name], errors="coerce")

    outputs: list[PredictionOutput] = []
    for descriptor in models:
        artifact = joblib.load(_artifact_path(dataset_id, descriptor.model_id))
        row = _feature_frame(
            raw_df, artifact["raw_features"], artifact.get(
                "datetime_features", [])
        )
        pipeline: Pipeline = artifact["pipeline"]
        value = pipeline.predict(row)[0]
        probabilities: dict[str, float] = {}
        confidence: float | None = None
        if status.problem_type == "classification" and hasattr(
            pipeline, "predict_proba"
        ):
            prob_values = pipeline.predict_proba(row)[0]
            labels = pipeline.classes_
            probabilities = {
                str(label): round(float(prob), 4)
                for label, prob in zip(labels, prob_values)
            }
            confidence = round(float(max(prob_values)), 4)

        outputs.append(
            PredictionOutput(
                model_id=descriptor.model_id,
                model_name=descriptor.model_name,
                family=descriptor.family,
                prediction=_json_value(value),
                metrics=descriptor.metrics,
                confidence=confidence,
                probabilities=probabilities,
            )
        )

    consensus, consensus_label = _consensus(outputs, status.problem_type)
    return PredictionReceipt(
        dataset_id=dataset_id,
        target_column=status.target_column,
        problem_type=status.problem_type,
        submitted_inputs=submitted,
        assumed_inputs=assumed,
        warnings=warnings,
        predictions=outputs,
        consensus=consensus,
        consensus_label=consensus_label,
        created_at=datetime.now(UTC).isoformat(),
    )


def run_batch_prediction(
    dataset_id: str,
    content: bytes,
    filename: str,
    model_ids: list[str] | None = None,
) -> dict[str, Any]:
    df = parse_dataframe(content, filename)
    _, target, problem_type = _require_prediction_context(dataset_id)
    status = load_production_status(dataset_id)
    if not status or not status.models:
        raise ValueError(
            "Train selected models before running batch predictions.")

    selected = set(model_ids or [model.model_id for model in status.models])
    models = [model for model in status.models if model.model_id in selected]
    if not models:
        raise ValueError(
            "None of the requested models are trained and available.")

    raw_batch, warnings = _prepare_batch_frame(df, status.input_fields)
    output = df.copy()
    prediction_columns: list[str] = []
    for descriptor in models:
        artifact = joblib.load(_artifact_path(dataset_id, descriptor.model_id))
        features = _feature_frame(
            raw_batch, artifact["raw_features"], artifact.get(
                "datetime_features", [])
        )
        pipeline: Pipeline = artifact["pipeline"]
        preds = pipeline.predict(features)
        column = f"prediction_{descriptor.model_id}"
        output[column] = [_json_value(value) for value in preds]
        prediction_columns.append(column)
        if problem_type == "classification" and hasattr(pipeline, "predict_proba"):
            probas = pipeline.predict_proba(features)
            output[f"confidence_{descriptor.model_id}"] = [
                round(float(max(row)), 4) for row in probas
            ]

    if problem_type == "regression":
        output["nexora_consensus"] = output[prediction_columns].apply(
            lambda row: round(
                float(pd.to_numeric(row, errors="coerce").mean()), 6),
            axis=1,
        )
    else:
        output["nexora_consensus"] = output[prediction_columns].mode(axis=1)[0]

    drift = calculate_drift(dataset_id, raw_batch, status.input_fields)
    batch_id = str(uuid.uuid4())
    output_path = _batch_output_path(dataset_id, batch_id)
    output.to_csv(output_path, index=False)
    meta = {
        "batch_id": batch_id,
        "dataset_id": dataset_id,
        "filename": filename,
        "rows": len(df),
        "model_ids": [model.model_id for model in models],
        "created_at": datetime.now(UTC).isoformat(),
        "download_url": f"/api/datasets/{dataset_id}/production/batches/{batch_id}/download",
        "drift": drift,
        "warnings": warnings,
        "target_column": target,
    }
    _batch_meta_path(dataset_id, batch_id).write_text(
        json.dumps(meta, indent=2), encoding="utf-8"
    )
    return meta


def list_batches(dataset_id: str) -> list[dict[str, Any]]:
    directory = _batches_dir(dataset_id)
    batches: list[dict[str, Any]] = []
    for path in sorted(
        directory.glob("*.json"), key=lambda item: item.stat().st_mtime, reverse=True
    ):
        try:
            batches.append(json.loads(path.read_text(encoding="utf-8")))
        except (OSError, ValueError):
            continue
    return batches


def batch_output_path(dataset_id: str, batch_id: str) -> Path:
    path = _batch_output_path(dataset_id, batch_id)
    if not path.exists():
        raise ValueError("Batch prediction output not found.")
    return path


def explain_saved_prediction(
    dataset_id: str,
    inputs: dict[str, Any],
    model_id: str | None = None,
) -> PredictionExplainResponse:
    status = load_production_status(dataset_id)
    if not status or not status.models:
        raise ValueError(
            "Train selected models before explaining predictions.")
    descriptor = next(
        (model for model in status.models if model.model_id == model_id),
        status.models[0],
    )
    artifact = joblib.load(_artifact_path(dataset_id, descriptor.model_id))

    submitted, assumed, warnings = _prepare_input_values(
        inputs, status.input_fields)
    raw_row = {**assumed, **submitted}
    baseline_row = {field.name: field.default for field in status.input_fields}
    raw_df = pd.DataFrame([raw_row])
    baseline_df = pd.DataFrame([baseline_row])
    for field in status.input_fields:
        if field.kind == "number":
            raw_df[field.name] = pd.to_numeric(
                raw_df[field.name], errors="coerce")
            baseline_df[field.name] = pd.to_numeric(
                baseline_df[field.name], errors="coerce"
            )

    pipeline: Pipeline = artifact["pipeline"]
    pred_value, pred_score = _prediction_score(
        pipeline,
        _feature_frame(
            raw_df, artifact["raw_features"], artifact.get(
                "datetime_features", [])
        ),
        status.problem_type,
    )
    base_value, base_score = _prediction_score(
        pipeline,
        _feature_frame(
            baseline_df, artifact["raw_features"], artifact.get(
                "datetime_features", [])
        ),
        status.problem_type,
        target_label=pred_value,
    )

    contributions: list[PredictionContribution] = []
    for field in status.input_fields:
        if field.name not in raw_row:
            continue
        replaced = dict(raw_row)
        replaced[field.name] = baseline_row.get(field.name)
        replaced_df = pd.DataFrame([replaced])
        if field.kind == "number":
            replaced_df[field.name] = pd.to_numeric(
                replaced_df[field.name], errors="coerce"
            )
        _, score = _prediction_score(
            pipeline,
            _feature_frame(
                replaced_df,
                artifact["raw_features"],
                artifact.get("datetime_features", []),
            ),
            status.problem_type,
            target_label=pred_value,
        )
        contribution = round(float(pred_score - score), 6)
        direction = "neutral"
        if contribution > 0:
            direction = "increases"
        elif contribution < 0:
            direction = "decreases"
        contributions.append(
            PredictionContribution(
                feature=field.name,
                submitted_value=raw_row.get(field.name),
                baseline_value=baseline_row.get(field.name),
                contribution=contribution,
                direction=direction,  # type: ignore[arg-type]
            )
        )

    contributions.sort(key=lambda item: abs(item.contribution), reverse=True)
    return PredictionExplainResponse(
        dataset_id=dataset_id,
        model_id=descriptor.model_id,
        model_name=descriptor.model_name,
        prediction=_json_value(pred_value),
        baseline_prediction=_json_value(base_value),
        score_delta=round(float(pred_score - base_score), 6),
        method="single-row perturbation against typical training values",
        contributions=contributions[:12],
        warnings=warnings,
    )


def calculate_drift(
    dataset_id: str,
    batch_df: pd.DataFrame,
    fields: list[PredictionInputField],
) -> dict[str, Any]:
    train_df = load_dataframe(dataset_id)
    if train_df is None:
        return {
            "overall_score": 0,
            "features": [],
            "summary": "Training dataset not found.",
        }

    features: list[dict[str, Any]] = []
    scores: list[float] = []
    for field in fields:
        if field.name not in train_df.columns or field.name not in batch_df.columns:
            continue
        train = train_df[field.name]
        batch = batch_df[field.name]
        if field.kind == "number":
            train_num = pd.to_numeric(train, errors="coerce").dropna()
            batch_num = pd.to_numeric(batch, errors="coerce").dropna()
            if len(train_num) == 0 or len(batch_num) == 0:
                continue
            std = float(train_num.std()) or 1.0
            mean_shift = abs(float(batch_num.mean()) -
                             float(train_num.mean())) / std
            below = batch_num < float(train_num.min())
            above = batch_num > float(train_num.max())
            out_range = float((below | above).mean()
                              ) if len(batch_num) else 0.0
            score = min(1.0, mean_shift / 3 + out_range)
            features.append(
                {
                    "feature": field.name,
                    "kind": field.kind,
                    "score": round(score, 4),
                    "training_mean": round(float(train_num.mean()), 4),
                    "batch_mean": round(float(batch_num.mean()), 4),
                    "out_of_range_pct": round(out_range * 100, 2),
                }
            )
            scores.append(score)
        elif field.kind == "category" and field.options:
            known = set(map(str, field.options))
            values = batch.dropna().astype(str)
            unseen = float((~values.isin(known)).mean()
                           ) if len(values) else 0.0
            features.append(
                {
                    "feature": field.name,
                    "kind": field.kind,
                    "score": round(unseen, 4),
                    "unseen_category_pct": round(unseen * 100, 2),
                }
            )
            scores.append(unseen)

    overall = round(float(np.mean(scores)) if scores else 0.0, 4)
    return {
        "overall_score": overall,
        "severity": "high"
        if overall >= 0.35
        else ("medium" if overall >= 0.15 else "low"),
        "features": sorted(
            features, key=lambda item: item.get("score", 0), reverse=True
        )[:20],
        "summary": "Batch distribution compared against the original training dataset.",
    }


def list_deployments(dataset_id: str) -> list[ModelDeployment]:
    path = _deployments_path(dataset_id)
    if not path.exists():
        return []
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []
    return [_deployment_public(item) for item in raw]


def create_deployment(
    dataset_id: str, name: str, model_ids: list[str] | None = None
) -> tuple[ModelDeployment, str]:
    status = load_production_status(dataset_id)
    if not status or not status.models:
        raise ValueError(
            "Train selected models before creating a deployment endpoint.")
    selected = model_ids or [model.model_id for model in status.models]
    trained = {model.model_id for model in status.models}
    missing = [model_id for model_id in selected if model_id not in trained]
    if missing:
        raise ValueError(
            f"Models are not trained for deployment: {', '.join(missing)}")

    api_key = f"nx_{secrets.token_urlsafe(32)}"
    raw = _load_deployment_records(dataset_id)
    record = {
        "deployment_id": str(uuid.uuid4()),
        "dataset_id": dataset_id,
        "name": name,
        "model_ids": selected,
        "active": True,
        "created_at": datetime.now(UTC).isoformat(),
        "last_used_at": None,
        "api_key_hash": _hash_key(api_key),
        "api_key_preview": f"{api_key[:8]}...{api_key[-4:]}",
    }
    raw.append(record)
    _save_deployment_records(dataset_id, raw)
    return _deployment_public(record), api_key


def set_deployment_active(
    dataset_id: str, deployment_id: str, active: bool
) -> ModelDeployment:
    records = _load_deployment_records(dataset_id)
    for record in records:
        if record["deployment_id"] == deployment_id:
            record["active"] = active
            _save_deployment_records(dataset_id, records)
            return _deployment_public(record)
    raise ValueError("Deployment not found.")


def predict_deployment(
    deployment_id: str,
    api_key: str,
    inputs: dict[str, Any],
    model_ids: list[str] | None = None,
) -> PredictionReceipt:
    for path in settings.upload_dir.glob("*.deployments.json"):
        dataset_id = path.name.replace(".deployments.json", "")
        records = _load_deployment_records(dataset_id)
        for record in records:
            if record.get("deployment_id") != deployment_id:
                continue
            if not record.get("active"):
                raise ValueError("Deployment is inactive.")
            if record.get("api_key_hash") != _hash_key(api_key):
                raise PermissionError("Invalid deployment API key.")
            selected = model_ids or record.get("model_ids", [])
            record["last_used_at"] = datetime.now(UTC).isoformat()
            _save_deployment_records(dataset_id, records)
            return run_saved_prediction(dataset_id, inputs, selected)
    raise ValueError("Deployment not found.")


def _train_one_selected(
    spec: ModelSpec,
    X: pd.DataFrame,
    y: pd.Series,
    problem_type: str,
    raw_features: list[str],
    datetime_features: list[str],
    fields: list[PredictionInputField],
) -> tuple[DeployedModel, dict[str, Any]]:
    t0 = time.perf_counter()
    pipeline = _pipeline_for_spec(spec, X)
    stratify = (
        y if problem_type == "classification" and y.value_counts().min() >= 2 else None
    )
    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=settings.train_test_split,
        random_state=42,
        stratify=stratify,
    )
    pipeline.fit(X_train, y_train)
    pred = pipeline.predict(X_test)
    metrics = _metrics(problem_type, y_test, pred)
    pipeline.fit(X, y)
    elapsed = round(time.perf_counter() - t0, 3)
    descriptor = DeployedModel(
        model_id=spec.id,
        model_name=spec.name,
        family=spec.family,
        problem_type=problem_type,
        metrics=metrics,
        primary_score=metrics["accuracy"]
        if problem_type == "classification"
        else metrics["r2"],
        train_time_sec=elapsed,
    )
    artifact = {
        "pipeline": pipeline,
        "raw_features": raw_features,
        "datetime_features": datetime_features,
        "input_fields": [field.model_dump() for field in fields],
        "problem_type": problem_type,
    }
    return descriptor, artifact


def _pipeline_for_spec(spec: ModelSpec, X: pd.DataFrame) -> Pipeline:
    numeric = X.select_dtypes(include=[np.number]).columns.tolist()
    categorical = [column for column in X.columns if column not in numeric]
    preprocess = ColumnTransformer(
        [
            (
                "number",
                Pipeline(
                    [
                        ("impute", SimpleImputer(strategy="median")),
                        ("scale", StandardScaler()),
                    ]
                ),
                numeric,
            ),
            (
                "category",
                Pipeline(
                    [
                        ("impute", SimpleImputer(strategy="most_frequent")),
                        ("encode", OneHotEncoder(handle_unknown="ignore")),
                    ]
                ),
                categorical,
            ),
        ],
        remainder="drop",
    )
    return Pipeline([("preprocess", preprocess), ("model", spec.factory())])


def _usable_feature_columns(df: pd.DataFrame, target: str) -> list[str]:
    return [
        str(column)
        for column in df.columns
        if column != target
        and not _is_id_like(df[column])
        and df[column].nunique(dropna=True) > 1
    ]


def _input_fields(df: pd.DataFrame, columns: list[str]) -> list[PredictionInputField]:
    fields: list[PredictionInputField] = []
    for column in columns:
        series = df[column]
        if _infer_datetime(series):
            parsed = pd.to_datetime(
                series, errors="coerce", format="mixed").dropna()
            fields.append(
                PredictionInputField(
                    name=column,
                    kind="date",
                    default=parsed.median().date().isoformat() if len(parsed) else None,
                    options=[],
                )
            )
        elif pd.api.types.is_numeric_dtype(series):
            numbers = pd.to_numeric(series, errors="coerce").dropna()
            fields.append(
                PredictionInputField(
                    name=column,
                    kind="number",
                    default=round(float(numbers.median()),
                                  4) if len(numbers) else None,
                    min_value=round(float(numbers.min()), 4) if len(
                        numbers) else None,
                    max_value=round(float(numbers.max()), 4) if len(
                        numbers) else None,
                )
            )
        elif series.nunique(dropna=True) <= 40:
            options = [
                str(value)
                for value in series.dropna().astype(str).value_counts().index.tolist()
            ]
            fields.append(
                PredictionInputField(
                    name=column,
                    kind="category",
                    default=options[0] if options else None,
                    options=options,
                )
            )
        else:
            mode = series.dropna().astype(str).mode()
            fields.append(
                PredictionInputField(
                    name=column,
                    kind="text",
                    default=str(mode.iloc[0]) if len(mode) else None,
                )
            )
    return fields


def _feature_frame(
    df: pd.DataFrame,
    raw_features: list[str],
    datetime_features: list[str],
) -> pd.DataFrame:
    prepared = pd.DataFrame(index=df.index)
    for column in raw_features:
        source = (
            df[column]
            if column in df.columns
            else pd.Series([None] * len(df), index=df.index)
        )
        if column in datetime_features:
            parsed = pd.to_datetime(source, errors="coerce", format="mixed")
            prepared[f"{column}__year"] = parsed.dt.year
            prepared[f"{column}__month"] = parsed.dt.month
            prepared[f"{column}__day"] = parsed.dt.day
            prepared[f"{column}__ordinal"] = parsed.map(
                lambda value: value.toordinal() if pd.notna(value) else np.nan
            )
        else:
            prepared[column] = source
    return prepared


def _prepare_input_values(
    inputs: dict[str, Any],
    fields: list[PredictionInputField],
) -> tuple[dict[str, Any], dict[str, Any], list[str]]:
    submitted: dict[str, Any] = {}
    assumed: dict[str, Any] = {}
    warnings: list[str] = []
    for field in fields:
        raw = inputs.get(field.name)
        if raw in (None, ""):
            assumed[field.name] = field.default
            continue

        if field.kind == "number":
            try:
                value: Any = float(raw)
            except (TypeError, ValueError) as exc:
                raise ValueError(f"`{field.name}` must be a number.") from exc
            if field.min_value is not None and value < field.min_value:
                warnings.append(
                    f"{field.name} is below the range seen during training."
                )
            if field.max_value is not None and value > field.max_value:
                warnings.append(
                    f"{field.name} is above the range seen during training."
                )
        elif field.kind == "date":
            parsed = pd.to_datetime(raw, errors="coerce", format="mixed")
            if pd.isna(parsed):
                raise ValueError(f"`{field.name}` must be a valid date.")
            value = parsed.date().isoformat()
        else:
            value = str(raw)
            if (
                field.kind == "category"
                and field.options
                and value not in field.options
            ):
                warnings.append(
                    f"{field.name} value was not present in the training dataset."
                )
        submitted[field.name] = value
    return submitted, assumed, warnings


def _prepare_batch_frame(
    df: pd.DataFrame,
    fields: list[PredictionInputField],
) -> tuple[pd.DataFrame, list[str]]:
    prepared = pd.DataFrame(index=df.index)
    warnings: list[str] = []
    for field in fields:
        if field.name in df.columns:
            values = df[field.name]
        else:
            values = pd.Series([field.default] * len(df), index=df.index)
            warnings.append(
                f"Missing column `{field.name}` was filled with typical training values."
            )

        if field.kind == "number":
            prepared[field.name] = pd.to_numeric(values, errors="coerce").fillna(
                field.default
            )
            if field.min_value is not None:
                below = prepared[field.name] < field.min_value
                if bool(below.any()):
                    warnings.append(
                        f"{field.name}: {int(below.sum())} rows below training range."
                    )
            if field.max_value is not None:
                above = prepared[field.name] > field.max_value
                if bool(above.any()):
                    warnings.append(
                        f"{field.name}: {int(above.sum())} rows above training range."
                    )
        elif field.kind == "date":
            parsed = pd.to_datetime(values, errors="coerce", format="mixed")
            prepared[field.name] = parsed.dt.date.astype("string").fillna(
                str(field.default)
            )
        else:
            prepared[field.name] = values.astype("string").fillna(
                str(field.default or "")
            )
            if field.kind == "category" and field.options:
                unseen = ~prepared[field.name].isin(field.options)
                if bool(unseen.any()):
                    warnings.append(
                        f"{field.name}: {int(unseen.sum())} rows contain unseen categories."
                    )
    return prepared, warnings[:20]


def _metrics(
    problem_type: str, y_test: pd.Series, pred: np.ndarray
) -> dict[str, float]:
    if problem_type == "classification":
        return {
            "accuracy": round(float(accuracy_score(y_test, pred)), 4),
            "f1": round(
                float(f1_score(y_test, pred, average="weighted", zero_division=0)), 4
            ),
        }
    return {
        "r2": round(float(r2_score(y_test, pred)), 4),
        "mae": round(float(mean_absolute_error(y_test, pred)), 4),
        "rmse": round(float(np.sqrt(mean_squared_error(y_test, pred))), 4),
    }


def _prediction_score(
    pipeline: Pipeline,
    row: pd.DataFrame,
    problem_type: str,
    target_label: Any = None,
) -> tuple[Any, float]:
    prediction = pipeline.predict(row)[0]
    if problem_type == "classification" and hasattr(pipeline, "predict_proba"):
        probabilities = pipeline.predict_proba(row)[0]
        labels = list(pipeline.classes_)
        label = target_label if target_label is not None else prediction
        try:
            score = float(probabilities[labels.index(label)])
        except ValueError:
            score = float(max(probabilities))
        return prediction, score
    return prediction, float(prediction) if isinstance(
        prediction, (int, float, np.integer, np.floating)
    ) else 0.0


def _consensus(outputs: list[PredictionOutput], problem_type: str) -> tuple[Any, str]:
    if problem_type == "regression":
        values = [float(output.prediction) for output in outputs]
        return round(float(np.mean(values)), 4), "Average of selected trained models"

    votes: dict[str, int] = {}
    for output in outputs:
        key = str(output.prediction)
        votes[key] = votes.get(key, 0) + 1
    winner = max(votes.items(), key=lambda item: item[1])
    return winner[0], f"Majority vote ({winner[1]}/{len(outputs)} models)"


def _hash_key(api_key: str) -> str:
    return hashlib.sha256(api_key.encode("utf-8")).hexdigest()


def _load_deployment_records(dataset_id: str) -> list[dict[str, Any]]:
    path = _deployments_path(dataset_id)
    if not path.exists():
        return []
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []


def _save_deployment_records(dataset_id: str, records: list[dict[str, Any]]) -> None:
    _deployments_path(dataset_id).write_text(
        json.dumps(records, indent=2), encoding="utf-8"
    )


def _deployment_public(record: dict[str, Any]) -> ModelDeployment:
    deployment_id = record["deployment_id"]
    return ModelDeployment(
        deployment_id=deployment_id,
        dataset_id=record["dataset_id"],
        name=record.get("name", "Production endpoint"),
        model_ids=record.get("model_ids", []),
        active=bool(record.get("active", True)),
        created_at=record["created_at"],
        last_used_at=record.get("last_used_at"),
        predict_url=f"{settings.public_api_url.rstrip('/')}/api/predict/{deployment_id}",
        api_key_preview=record.get("api_key_preview"),
    )


def _json_value(value: Any) -> Any:
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        return round(float(value), 6)
    return value
