from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.models.schemas import ChatRequest, ChatResponse
from app.services.dataset_store import load_analysis
from app.services.ollama_service import (
    chat_with_dataset,
    check_ollama_status,
    explain_error_with_ollama,
)

router = APIRouter(prefix="/api", tags=["chat"])


class ExplainErrorRequest(BaseModel):
    error_message: str
    dataset_id: str | None = None
    context_info: str | None = None


@router.get("/datasets/{dataset_id}/chat/status")
async def chat_status(dataset_id: str):
    if not load_analysis(dataset_id):
        raise HTTPException(status_code=404, detail="Dataset not found.")
    return await check_ollama_status()


@router.post("/datasets/{dataset_id}/chat", response_model=ChatResponse)
async def dataset_chat(dataset_id: str, body: ChatRequest):
    if not load_analysis(dataset_id):
        raise HTTPException(status_code=404, detail="Dataset not found.")

    history = [{"role": m.role, "content": m.content} for m in body.history]
    result = await chat_with_dataset(dataset_id, body.message, history)
    return ChatResponse(**result)


@router.post("/explain-error")
async def explain_error_global(body: ExplainErrorRequest):
    return await explain_error_with_ollama(
        error_message=body.error_message,
        dataset_id=body.dataset_id,
        context_info=body.context_info,
    )


@router.post("/datasets/{dataset_id}/explain-error")
async def explain_error_dataset(dataset_id: str, body: ExplainErrorRequest):
    return await explain_error_with_ollama(
        error_message=body.error_message,
        dataset_id=dataset_id,
        context_info=body.context_info,
    )
