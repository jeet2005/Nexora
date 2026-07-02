from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel

from app.middleware.admin_auth_guard import require_admin
from app.services.audit_service import log_admin_action
from app.services.email_service import notify_users_announcement
from app.services.persistence_service import collection

router = APIRouter(
    prefix="/api/admin/content",
    tags=["admin", "content"],
    dependencies=[Depends(require_admin)],
)


class SiteContentUpdate(BaseModel):
    value: Any
    notify_users: bool = False


@router.get("")
def get_all_content():
    col = collection("site_content")
    if col is None:
        return []

    docs = list(col.find({}, {"_id": 0}))
    return docs


@router.get("/{key}")
def get_content(key: str):
    col = collection("site_content")
    if col is None:
        return {"key": key, "value": None}

    doc = col.find_one({"key": key}, {"_id": 0})
    if doc:
        return doc
    return {"key": key, "value": None}


def _admin_display(admin: dict) -> dict:
    admins_col = collection("admins")
    if admins_col is None:
        return {"name": admin["email"], "avatar_url": "/avatars/admins/a1.png"}
    doc = admins_col.find_one({"email": admin["email"]}, {"_id": 0, "password_hash": 0})
    if not doc:
        return {"name": admin["email"], "avatar_url": "/avatars/admins/a1.png"}
    return {
        "name": doc.get("name") or admin["email"].split("@")[0],
        "avatar_url": doc.get("avatar_url") or "/avatars/admins/a1.png",
    }


@router.put("/{key}")
def update_content(
    key: str,
    data: SiteContentUpdate,
    request: Request,
    admin: dict = Depends(require_admin),
):
    col = collection("site_content")
    if col is None:
        return {"success": False, "detail": "Database connection failed"}

    profile = _admin_display(admin)
    now = datetime.utcnow()
    col.update_one(
        {"key": key},
        {
            "$set": {
                "value": data.value,
                "updated_at": now,
                "updated_by": admin["email"],
                "updated_by_name": profile["name"],
                "updated_by_avatar": profile["avatar_url"],
            }
        },
        upsert=True,
    )

    log_admin_action(
        admin["email"],
        f"update_content:{key}",
        str(data.value)[:200],
        request.client.host if request.client else None,
    )

    emails_sent = 0
    if key == "announcement_banner" and data.notify_users and data.value:
        users_col = collection("users")
        if users_col is not None:
            recipients = [
                u["email"] for u in users_col.find({}, {"email": 1}) if u.get("email")
            ]
            emails_sent = notify_users_announcement(
                recipients, str(data.value), profile["name"]
            )

    return {
        "success": True,
        "key": key,
        "value": data.value,
        "updated_by_name": profile["name"],
        "updated_by_avatar": profile["avatar_url"],
        "emails_sent": emails_sent,
    }
