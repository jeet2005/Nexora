import asyncio

from fastapi import (
    APIRouter,
    File,
    Form,
    Header,
    HTTPException,
    UploadFile,
    WebSocket,
    WebSocketDisconnect,
)
from fastapi.responses import FileResponse

from app.models.schemas import (
    BatchPredictionListResponse,
    BatchPredictionSummary,
    CreateDeploymentRequest,
    CreateDeploymentResponse,
    DeploymentListResponse,
    ExperimentCompareResponse,
    ExperimentsResponse,
    PredictionExplainRequest,
    PredictionExplainResponse,
    PredictionReceipt,
    PredictionRunRequest,
    ProductionModelsResponse,
    ProductionStatus,
    ProductionTrainRequest,
    RegistryStatsResponse,
    TrainingStartRequest,
)
from app.services.deployed_model_service import (
    batch_output_path,
    create_deployment,
    explain_saved_prediction,
    list_batches,
    list_deployable_models,
    list_deployments,
    load_production_status,
    model_artifact_path,
    predict_deployment,
    run_batch_prediction,
    run_saved_prediction,
    set_deployment_active,
    train_selected_models,
)
from app.services.experiment_service import compare_experiments, list_experiments
from app.services.model_registry import registry_stats
from app.services.session_store import load_session
from app.services.training_manager import (
    get_job,
    load_training_result,
    start_training,
    subscribe,
    unsubscribe,
)

router = APIRouter(prefix="/api", tags=["training"])
public_router = APIRouter(tags=["public-prediction"])


@router.get("/models/registry", response_model=RegistryStatsResponse)
async def get_registry_stats():
    return RegistryStatsResponse(**registry_stats())


@router.get(
    "/datasets/{dataset_id}/production/models", response_model=ProductionModelsResponse
)
async def get_deployable_models(dataset_id: str):
    try:
        return ProductionModelsResponse(**list_deployable_models(dataset_id))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.get(
    "/datasets/{dataset_id}/production/status", response_model=ProductionStatus | None
)
async def get_production_status(dataset_id: str):
    return load_production_status(dataset_id)


@router.post("/datasets/{dataset_id}/production/train", response_model=ProductionStatus)
async def train_production_models(dataset_id: str, body: ProductionTrainRequest):
    try:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(
            None,
            lambda: train_selected_models(dataset_id, body.model_ids),
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.post(
    "/datasets/{dataset_id}/production/predict", response_model=PredictionReceipt
)
async def predict_from_trained_models(dataset_id: str, body: PredictionRunRequest):
    try:
        return run_saved_prediction(dataset_id, body.inputs, body.model_ids)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.post(
    "/datasets/{dataset_id}/production/batch-predict",
    response_model=BatchPredictionSummary,
)
async def batch_predict(
    dataset_id: str,
    file: UploadFile = File(...),
    model_ids: str = Form(""),
):
    try:
        content = await file.read()
        selected = [item.strip() for item in model_ids.split(",") if item.strip()]
        return BatchPredictionSummary(
            **run_batch_prediction(
                dataset_id, content, file.filename or "batch.csv", selected or None
            )
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.get(
    "/datasets/{dataset_id}/production/batches",
    response_model=BatchPredictionListResponse,
)
async def get_batches(dataset_id: str):
    return BatchPredictionListResponse(
        batches=[BatchPredictionSummary(**item) for item in list_batches(dataset_id)]
    )


@router.get("/datasets/{dataset_id}/production/batches/{batch_id}/download")
async def download_batch_predictions(dataset_id: str, batch_id: str):
    try:
        path = batch_output_path(dataset_id, batch_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    return FileResponse(
        path=str(path),
        media_type="text/csv",
        filename=f"nexora_batch_{batch_id}.csv",
    )


@router.get("/datasets/{dataset_id}/production/models/{model_id}/download")
async def download_trained_model(dataset_id: str, model_id: str):
    try:
        path = model_artifact_path(dataset_id, model_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    return FileResponse(
        path=str(path),
        media_type="application/octet-stream",
        filename=f"{model_id}.joblib",
    )


@router.post(
    "/datasets/{dataset_id}/production/explain-prediction",
    response_model=PredictionExplainResponse,
)
async def explain_prediction(dataset_id: str, body: PredictionExplainRequest):
    try:
        return explain_saved_prediction(dataset_id, body.inputs, body.model_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.get("/datasets/{dataset_id}/deployments", response_model=DeploymentListResponse)
async def get_deployments(dataset_id: str):
    return DeploymentListResponse(deployments=list_deployments(dataset_id))


@router.post(
    "/datasets/{dataset_id}/deployments", response_model=CreateDeploymentResponse
)
async def create_prediction_deployment(dataset_id: str, body: CreateDeploymentRequest):
    try:
        deployment, api_key = create_deployment(dataset_id, body.name, body.model_ids)
        return CreateDeploymentResponse(deployment=deployment, api_key=api_key)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.post("/datasets/{dataset_id}/deployments/{deployment_id}/deactivate")
async def deactivate_prediction_deployment(dataset_id: str, deployment_id: str):
    try:
        return set_deployment_active(dataset_id, deployment_id, False)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e


@router.post(
    "/predict/{deployment_id}",
    response_model=PredictionReceipt,
    tags=["public-prediction"],
)
async def public_prediction(
    deployment_id: str,
    body: PredictionRunRequest,
    x_nexora_key: str | None = Header(default=None, alias="X-Nexora-Key"),
):
    if not x_nexora_key:
        raise HTTPException(status_code=401, detail="X-Nexora-Key header is required.")
    try:
        return predict_deployment(
            deployment_id, x_nexora_key, body.inputs, body.model_ids
        )
    except PermissionError as e:
        raise HTTPException(status_code=401, detail=str(e)) from e
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e


@public_router.post("/predict/{deployment_id}", response_model=PredictionReceipt)
async def public_prediction_root(
    deployment_id: str,
    body: PredictionRunRequest,
    x_nexora_key: str | None = Header(default=None, alias="X-Nexora-Key"),
):
    if not x_nexora_key:
        raise HTTPException(status_code=401, detail="X-Nexora-Key header is required.")
    try:
        return predict_deployment(
            deployment_id, x_nexora_key, body.inputs, body.model_ids
        )
    except PermissionError as e:
        raise HTTPException(status_code=401, detail=str(e)) from e
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e


@router.get("/datasets/{dataset_id}/experiments", response_model=ExperimentsResponse)
async def get_experiments(dataset_id: str):
    return ExperimentsResponse(experiments=list_experiments(dataset_id))


@router.get(
    "/datasets/{dataset_id}/experiments/compare",
    response_model=ExperimentCompareResponse,
)
async def compare_dataset_experiments(dataset_id: str):
    return ExperimentCompareResponse(**compare_experiments(dataset_id))


@router.get("/datasets/{dataset_id}/training")
async def get_training(dataset_id: str):
    result = load_training_result(dataset_id)
    job = get_job(dataset_id)
    return {
        "result": result,
        "job": job,
    }


@router.post("/datasets/{dataset_id}/training/start")
async def start_training_job(dataset_id: str, body: TrainingStartRequest | None = None):
    body = body or TrainingStartRequest()
    try:
        out = start_training(
            dataset_id,
            max_models=body.max_models,
            test_split=body.test_split,
            cv_folds=body.cv_folds,
            timeout_sec=body.timeout_sec,
            seed=body.seed,
        )
        return out
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.websocket("/ws/training/{dataset_id}")
async def training_websocket(websocket: WebSocket, dataset_id: str):
    await websocket.accept()
    queue = subscribe(dataset_id)

    session = load_session(dataset_id)
    if session and session.training_result:
        await websocket.send_json(
            {
                "event": "snapshot",
                "leaderboard": [
                    r.model_dump() for r in session.training_result.leaderboard
                ],
                "summary": session.training_result.model_dump(),
            }
        )

    job = get_job(dataset_id)
    if job:
        await websocket.send_json({"event": "job_status", "job": job})

    try:
        while True:
            try:
                event = await asyncio.wait_for(queue.get(), timeout=1.0)
                await websocket.send_json(event)
            except TimeoutError:
                try:
                    await asyncio.wait_for(websocket.receive_text(), timeout=0.01)
                except TimeoutError:
                    continue
    except WebSocketDisconnect:
        pass
    finally:
        unsubscribe(dataset_id, queue)
