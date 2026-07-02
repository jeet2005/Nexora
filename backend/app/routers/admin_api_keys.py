import json

from fastapi import APIRouter, Depends

from app.config import settings
from app.middleware.admin_auth_guard import require_admin

router = APIRouter(
    prefix="/api/admin/api-keys",
    tags=["admin", "api_keys"],
    dependencies=[Depends(require_admin)],
)


@router.get("")
def list_all_api_keys():
    deployments = []
    for file_path in settings.upload_dir.glob("*.deployments.json"):
        dataset_id = file_path.name.split(".")[0]
        try:
            with open(file_path, encoding="utf-8") as f:
                data = json.load(f)
                for item in data:
                    item["dataset_id"] = dataset_id
                    deployments.append(item)
        except Exception:
            continue
    # Sort by created_at descending
    deployments.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    return deployments


@router.post("/{dataset_id}/{deployment_id}/revoke")
def revoke_api_key(dataset_id: str, deployment_id: str):
    from app.services.deployed_model_service import _deployments_path

    path = _deployments_path(dataset_id)
    if not path.exists():
        return {"success": False, "detail": "Deployments file not found"}

    try:
        with open(path, encoding="utf-8") as f:
            deps = json.load(f)

        updated = False
        for dep in deps:
            if dep["id"] == deployment_id:
                dep["active"] = False
                updated = True

        if updated:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(deps, f, indent=2)
            return {"success": True, "detail": "Deployment deactivated"}
        return {"success": False, "detail": "Deployment not found"}
    except Exception as e:
        return {"success": False, "detail": str(e)}
