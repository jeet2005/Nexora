import logging
import uuid

from fastapi import APIRouter, File, HTTPException, Query, UploadFile

from app.config import settings
from app.models.schemas import (
    ArchiveDatasetRequest,
    ArchiveDatasetResponse,
    DatasetAnalysis,
    DatasetHistoryResponse,
    ErrorResponse,
    UploadResponse,
)
from app.services.dataset_analyzer import analyze_dataset
from app.services.dataset_store import load_analysis, save_dataset
from app.services.dataset_validator import DatasetValidationError, load_dataframe
from app.services.history_service import delete_dataset, list_history, set_archived

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/datasets", tags=["datasets"])


@router.get("", response_model=DatasetHistoryResponse)
async def get_dataset_history(include_archived: bool = Query(False)):
    return DatasetHistoryResponse(
        datasets=list_history(include_archived=include_archived)
    )


@router.post(
    "/upload",
    response_model=UploadResponse,
    responses={400: {"model": ErrorResponse}},
)
async def upload_dataset(file: UploadFile = File(...)):
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided.")

    try:
        content = await file.read()
    except Exception as e:
        logger.error(f"Failed to read file: {e}", exc_info=True)
        raise HTTPException(
            status_code=400, detail=f"Failed to read file: {str(e)}"
        ) from e

    max_bytes = settings.max_upload_mb * 1024 * 1024
    if len(content) > max_bytes:
        raise HTTPException(
            status_code=400,
            detail=f"File exceeds {settings.max_upload_mb}MB limit.",
        )

    try:
        df = load_dataframe(content, file.filename)
    except DatasetValidationError as e:
        logger.warning(f"Dataset validation error: {e.message}")
        raise HTTPException(status_code=400, detail=e.message) from e
    except Exception as e:
        logger.error(f"Error processing file: {e}", exc_info=True)
        raise HTTPException(
            status_code=400, detail=f"Error processing file: {str(e)}"
        ) from e

    try:
        dataset_id = str(uuid.uuid4())
        logger.info(f"Analyzing dataset {dataset_id}...")
        analysis = analyze_dataset(df, file.filename, dataset_id)
        logger.info(f"Saving dataset {dataset_id}...")
        save_dataset(df, file.filename, analysis)
        logger.info(f"Successfully processed dataset {dataset_id}")
    except Exception as e:
        logger.error(f"Error analyzing or saving dataset: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}") from e

    return UploadResponse(
        dataset_id=dataset_id,
        filename=file.filename,
        message="Dataset uploaded and analyzed successfully.",
        analysis=analysis,
    )


@router.get("/{dataset_id}", response_model=DatasetAnalysis)
async def get_dataset(dataset_id: str):
    analysis = load_analysis(dataset_id)
    if not analysis:
        raise HTTPException(status_code=404, detail="Dataset not found.")
    return analysis


@router.post("/{dataset_id}/archive", response_model=ArchiveDatasetResponse)
async def archive_dataset(dataset_id: str, body: ArchiveDatasetRequest):
    try:
        set_archived(dataset_id, body.archived)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    return ArchiveDatasetResponse(dataset_id=dataset_id, archived=body.archived)


@router.delete("/{dataset_id}")
async def remove_dataset(dataset_id: str):
    try:
        delete_dataset(dataset_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    return {"status": "deleted", "dataset_id": dataset_id}


@router.get("/{dataset_id}/preview")
async def get_preview(dataset_id: str, limit: int = 50):
    analysis = load_analysis(dataset_id)
    if not analysis:
        raise HTTPException(status_code=404, detail="Dataset not found.")
    return {"rows": analysis.preview[:limit], "total_rows": analysis.rows}
