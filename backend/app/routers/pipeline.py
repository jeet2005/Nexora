import numpy as np
from fastapi import APIRouter, HTTPException

from app.models.schemas import (
    ConfigureTargetRequest,
    ConfigureTargetResponse,
    CorrelationInsight,
    DatasetInsights,
    DatasetSession,
    FeatureSelection,
    PreprocessMeta,
    PreprocessRequest,
    PreprocessResponse,
    PreprocessResult,
    PreprocessStep,
    ProblemDetection,
    TimingEstimatesResponse,
)
from app.services.dataset_store import load_analysis, load_dataframe
from app.services.insights_engine import generate_insights
from app.services.preprocessing_engine import PreprocessingConfig, preprocess
from app.services.problem_detector import detect_problem_type, suggest_feature_columns
from app.services.session_store import (
    load_processed_df,
    load_session,
    save_processed_df,
    save_session,
    update_session_preprocess,
)
from app.services.timing_estimator import estimate_all

router = APIRouter(prefix="/api/datasets", tags=["pipeline"])


def _require_dataset(dataset_id: str):
    analysis = load_analysis(dataset_id)
    df = load_dataframe(dataset_id)
    if not analysis or df is None:
        raise HTTPException(status_code=404, detail="Dataset not found.")
    return analysis, df


@router.get("/{dataset_id}/timing-estimates", response_model=TimingEstimatesResponse)
async def get_timing_estimates(
    dataset_id: str,
    max_models: int | None = None,
    production_model_count: int = 2,
):
    _, df = _require_dataset(dataset_id)
    session = load_session(dataset_id)
    problem_type = (session.problem_type if session else None) or "classification"
    if problem_type not in ("classification", "regression"):
        problem_type = "classification"
    return TimingEstimatesResponse(
        **estimate_all(
            df,
            problem_type=problem_type,
            max_models=max_models,
            production_model_count=production_model_count,
        )
    )


@router.get("/{dataset_id}/session")
async def get_session(dataset_id: str):
    session = load_session(dataset_id)
    if not session:
        return DatasetSession(dataset_id=dataset_id, status="analyzed")
    return session


@router.post("/{dataset_id}/configure", response_model=ConfigureTargetResponse)
async def configure_target(dataset_id: str, body: ConfigureTargetRequest):
    analysis, df = _require_dataset(dataset_id)

    if body.target_column not in df.columns:
        raise HTTPException(
            status_code=400, detail=f"Column '{body.target_column}' not found."
        )

    detection_raw = detect_problem_type(df, body.target_column)
    problem_type = body.problem_type or detection_raw["problem_type"]
    if problem_type not in ("classification", "regression"):
        detail = (
            "Time-series forecasting runs in Exploration Modes on the Overview tab. "
            "Select a numeric or categorical prediction target here for supervised models."
            if problem_type == "time_series"
            else "Clustering runs in Exploration Modes. Select a classification or regression target for Prediction Studio."
        )
        raise HTTPException(status_code=400, detail=detail)
    detection_raw["problem_type"] = problem_type

    features_raw = suggest_feature_columns(df, body.target_column)
    feature_cols = [
        c for c in features_raw["feature_columns"] if c not in body.exclude_columns
    ]

    detection = ProblemDetection(**detection_raw)
    feature_selection = FeatureSelection(
        feature_columns=feature_cols,
        excluded_id_columns=features_raw["excluded_id_columns"],
        excluded_datetime_columns=features_raw["excluded_datetime_columns"],
    )

    session = DatasetSession(
        dataset_id=dataset_id,
        target_column=body.target_column,
        problem_type=problem_type,
        problem_detection=detection,
        feature_selection=feature_selection,
        status="configured",
    )
    save_session(session)

    return ConfigureTargetResponse(
        session=session,
        problem_detection=detection,
        feature_selection=feature_selection,
    )


@router.post("/{dataset_id}/preprocess", response_model=PreprocessResponse)
async def run_preprocess(dataset_id: str, body: PreprocessRequest | None = None):
    body = body or PreprocessRequest()
    analysis, df = _require_dataset(dataset_id)
    session = load_session(dataset_id)

    if not session or not session.target_column:
        raise HTTPException(
            status_code=400,
            detail="Configure a target column before preprocessing.",
        )

    config = PreprocessingConfig(
        missing_strategy=body.missing_strategy,
        outlier_method=body.outlier_method,
        scaling=body.scaling,
        encode_categorical=body.encode_categorical,
        remove_duplicates=body.remove_duplicates,
        remove_constant=body.remove_constant,
        drop_id_columns=body.drop_id_columns,
    )

    processed, steps_raw, meta_raw = preprocess(
        df,
        session.target_column,
        session.problem_type or "classification",
        config,
    )

    save_processed_df(dataset_id, processed)

    feature_cols = [c for c in processed.columns if c != session.target_column]
    raw_features = (
        session.feature_selection.feature_columns
        if session.feature_selection
        else [c for c in df.columns if c != session.target_column]
    )
    insights_raw = generate_insights(
        processed,
        df,
        session.target_column,
        session.problem_type or "classification",
        feature_cols,
        steps_raw,
        raw_feature_columns=raw_features,
    )

    preview = processed.head(30).replace({np.nan: None}).to_dict(orient="records")

    result = PreprocessResult(
        steps=[PreprocessStep(**s) for s in steps_raw],
        meta=PreprocessMeta(**meta_raw),
        insights=DatasetInsights(
            top_correlations=[
                CorrelationInsight(**c) for c in insights_raw["top_correlations"]
            ],
            class_balance=insights_raw["class_balance"],
            target_stats=insights_raw["target_stats"],
            quality_warnings=insights_raw["quality_warnings"],
            estimated_difficulty=insights_raw["estimated_difficulty"],
            narrative=insights_raw["narrative"],
            preprocessing_summary=insights_raw["preprocessing_summary"],
        ),
        preview=preview,
        feature_columns=feature_cols,
    )

    session = update_session_preprocess(dataset_id, result)

    return PreprocessResponse(session=session, result=result)


@router.get("/{dataset_id}/processed-preview")
async def processed_preview(dataset_id: str, limit: int = 30):
    session = load_session(dataset_id)
    if not session or session.status != "preprocessed":
        raise HTTPException(
            status_code=400, detail="Dataset has not been preprocessed yet."
        )

    df = load_processed_df(dataset_id)
    if df is None:
        raise HTTPException(status_code=404, detail="Processed data not found.")

    rows = df.head(limit).replace({np.nan: None}).to_dict(orient="records")
    return {"rows": rows, "total_rows": len(df), "columns": list(df.columns)}
