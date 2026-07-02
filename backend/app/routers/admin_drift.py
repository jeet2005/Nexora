import json

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel

from app.config import settings
from app.middleware.admin_auth_guard import require_admin
from app.services.audit_service import log_admin_action

router = APIRouter(prefix="/api/admin/drift", tags=["admin", "drift"], dependencies=[Depends(require_admin)])

RESOLVED_FILE = settings.upload_dir / ".drift_resolved.json"


def _load_resolved() -> set[str]:
    if not RESOLVED_FILE.exists():
        return set()
    try:
        with open(RESOLVED_FILE, encoding="utf-8") as f:
            return set(json.load(f))
    except Exception:
        return set()


def _save_resolved(keys: set[str]) -> None:
    with open(RESOLVED_FILE, "w", encoding="utf-8") as f:
        json.dump(sorted(keys), f)


def _alert_key(alert: dict) -> str:
    return f"{alert.get('dataset_id')}:{alert.get('batch_id')}:{alert.get('feature')}"


def _scan_alerts() -> list[dict]:
    alerts = []
    resolved = _load_resolved()
    for batch_dir in settings.upload_dir.glob("*.batches"):
        dataset_id = batch_dir.name.replace(".batches", "")
        for batch_file in batch_dir.glob("*.json"):
            try:
                with open(batch_file, encoding="utf-8") as f:
                    data = json.load(f)
                drift_info = data.get("drift", {})
                if not drift_info or not drift_info.get("drift_detected", False):
                    continue
                features = drift_info.get("features", {})
                for feature, details in features.items():
                    if details.get("is_drifting", False):
                        alert = {
                            "dataset_id": dataset_id,
                            "batch_id": data.get("batch_id"),
                            "created_at": data.get("created_at"),
                            "feature": feature,
                            "score": details.get("score"),
                            "severity": "high" if details.get("score", 0) > 0.5 else "medium",
                            "status": "open",
                        }
                        key = _alert_key(alert)
                        if key in resolved:
                            alert["status"] = "resolved"
                        alerts.append(alert)
            except Exception:
                continue
    alerts.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    return alerts


@router.get("")
def get_all_drift_alerts(
    severity: str | None = None,
    status: str | None = None,
    since: str | None = None,
):
    alerts = _scan_alerts()
    if severity:
        alerts = [a for a in alerts if a.get("severity") == severity]
    if status:
        alerts = [a for a in alerts if a.get("status") == status]
    if since:
        alerts = [a for a in alerts if (a.get("created_at") or "") >= since]
    return alerts


class ResolveDriftRequest(BaseModel):
    dataset_id: str
    batch_id: str
    feature: str


@router.post("/resolve")
def resolve_drift_alert(body: ResolveDriftRequest, request: Request, admin: dict = Depends(require_admin)):
    key = f"{body.dataset_id}:{body.batch_id}:{body.feature}"
    resolved = _load_resolved()
    resolved.add(key)
    _save_resolved(resolved)
    log_admin_action(
        admin["email"],
        "resolve_drift",
        key,
        request.client.host if request.client else None,
    )
    return {"success": True, "key": key}
