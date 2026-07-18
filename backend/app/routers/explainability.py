"""Phase 4 API routes: Explainability, PDF reports, advanced visualizations."""

import asyncio

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from app.config import settings
from app.services.dataset_store import load_analysis
from app.services.session_store import load_processed_df, load_session
from app.services.training_manager import load_training_result

router = APIRouter(prefix="/api/datasets", tags=["explainability"])


@router.post("/{dataset_id}/explain")
async def run_explainability(dataset_id: str, model_id: str | None = None):
    """Run SHAP explainability on the best (or specified) model."""
    session = load_session(dataset_id)
    if not session or session.status != "trained":
        raise HTTPException(
            status_code=400, detail="Model training must be completed first."
        )

    training_result = load_training_result(dataset_id)
    if not training_result or not training_result.best_model:
        raise HTTPException(status_code=400, detail="No training results available.")

    df = load_processed_df(dataset_id)
    if df is None:
        raise HTTPException(status_code=404, detail="Processed dataset not found.")

    target_model_id = model_id or training_result.best_model.model_id
    problem_type = session.problem_type or "classification"

    if not session.target_column:
        raise HTTPException(status_code=400, detail="Target column must be specified.")

    # Run in a thread to avoid blocking the event loop
    from app.services.explainability_engine import run_explainability as _run_explain

    loop = asyncio.get_event_loop()
    try:
        result = await loop.run_in_executor(
            None,
            lambda: _run_explain(
                df, session.target_column, problem_type, target_model_id
            ),
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Explainability failed: {str(e)[:300]}"
        ) from e

    return result


@router.post("/{dataset_id}/report/generate")
async def generate_report(dataset_id: str, include_shap: bool = True):
    """Generate a comprehensive PDF report for the dataset."""
    session = load_session(dataset_id)
    if not session or session.status != "trained":
        raise HTTPException(
            status_code=400, detail="Complete training before generating a report."
        )

    analysis = load_analysis(dataset_id)
    if not analysis:
        raise HTTPException(status_code=404, detail="Dataset analysis not found.")

    training_result = load_training_result(dataset_id)
    if not training_result:
        raise HTTPException(status_code=400, detail="No training results available.")

    # Build dataset info
    dataset_info = {
        "filename": analysis.filename,
        "rows": analysis.rows,
        "columns": analysis.columns,
        "duplicate_rows": analysis.duplicate_rows,
        "memory_mb": analysis.memory_mb,
        "target_column": session.target_column,
        "problem_type": session.problem_type,
    }

    training_dict = training_result.model_dump()

    # Get insights if available
    insights_dict = None
    if session.preprocess_result and session.preprocess_result.insights:
        insights_dict = session.preprocess_result.insights.model_dump()

    # Optionally run SHAP
    explainability_dict = None
    if include_shap and training_result.best_model and session.target_column:
        df = load_processed_df(dataset_id)
        if df is not None:
            from app.services.explainability_engine import (
                run_explainability as _run_explain,
            )

            loop = asyncio.get_event_loop()
            try:
                explainability_dict = await loop.run_in_executor(
                    None,
                    lambda: _run_explain(
                        df,
                        session.target_column,
                        session.problem_type or "classification",
                        training_result.best_model.model_id,
                    ),
                )
            except Exception:
                pass  # Report will be generated without SHAP section

    # Generate PDF
    from app.services.report_generator import generate_pdf_report, save_pdf_report

    loop = asyncio.get_event_loop()
    try:
        _ = await loop.run_in_executor(
            None,
            lambda: save_pdf_report(
                dataset_id,
                dataset_info,
                training_dict,
                explainability_dict,
                insights_dict,
            ),
        )
        pdf_b64 = await loop.run_in_executor(
            None,
            lambda: generate_pdf_report(
                dataset_info,
                training_dict,
                explainability_dict,
                insights_dict,
            ),
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Report generation failed: {str(e)[:300]}"
        ) from e

    return {
        "status": "ok",
        "pdf_base64": pdf_b64,
        "filename": f"{dataset_id}_report.pdf",
    }


@router.get("/{dataset_id}/report/download")
async def download_report(dataset_id: str):
    """Download the generated PDF report."""
    path = settings.upload_dir / f"{dataset_id}_report.pdf"
    if not path.exists():
        raise HTTPException(
            status_code=404, detail="Report not found. Generate it first."
        )

    analysis = load_analysis(dataset_id)
    filename = analysis.filename.rsplit(".", 1)[0] if analysis else "report"

    return FileResponse(
        path=str(path),
        media_type="application/pdf",
        filename=f"nexora_{filename}_report.pdf",
    )
