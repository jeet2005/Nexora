from fastapi import APIRouter

from app.services.persistence_service import collection

router = APIRouter(prefix="/api/content", tags=["content"])


@router.get("")
def get_public_content():
    col = collection("site_content")
    if col is None:
        return []
    return list(col.find({}, {"_id": 0}))


@router.get("/{key}")
def get_public_content_by_key(key: str):
    col = collection("site_content")
    if col is None:
        return {"key": key, "value": None}
    doc = col.find_one({"key": key}, {"_id": 0})
    if doc:
        return doc
    return {"key": key, "value": None}
