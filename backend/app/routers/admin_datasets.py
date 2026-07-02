from fastapi import APIRouter, Depends

from app.middleware.admin_auth_guard import require_admin
from app.services.history_service import delete_dataset, list_history
from app.services.persistence_service import collection

router = APIRouter(prefix="/api/admin/datasets", tags=["admin", "datasets"], dependencies=[Depends(require_admin)])

@router.get("")
def get_all_datasets():
    return list_history(include_archived=True)

@router.delete("/{dataset_id}")
def delete_dataset_admin(dataset_id: str):
    try:
        delete_dataset(dataset_id)
        # Also remove from MongoDB if configured
        col = collection("datasets")
        if col is not None:
            col.delete_one({"dataset_id": dataset_id})
        return {"success": True}
    except Exception as e:
        return {"success": False, "detail": str(e)}
