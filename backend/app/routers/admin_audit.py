from fastapi import APIRouter, Depends

from app.middleware.admin_auth_guard import require_admin
from app.services.persistence_service import collection

router = APIRouter(
    prefix="/api/admin/audit",
    tags=["admin", "audit"],
    dependencies=[Depends(require_admin)],
)


@router.get("")
def get_audit_log(limit: int = 100):
    col = collection("audit_log")
    if col is None:
        return []

    docs = list(col.find({}, {"_id": 0}).sort("timestamp", -1).limit(limit))
    return docs
