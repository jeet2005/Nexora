import random
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Request

from app.middleware.user_auth_guard import get_current_user
from app.models.user import (
    ActivityResponse,
    LoginEvent,
    UserCreate,
    UserResponse,
    UserUpdate,
)
from app.services.email_service import _is_configured as email_enabled
from app.services.email_service import send_email
from app.services.link_validator import validate_link
from app.services.persistence_service import collection

router = APIRouter(prefix="/api/users", tags=["users"])

VALID_AVATARS = {f"/avatars/users/u{i}.png" for i in range(1, 21)}
MAX_LOGIN_HISTORY = 20


def _sanitize_user(doc: dict) -> dict:
    if doc.get("links"):
        doc["links"] = {
            k: v
            for k, v in doc["links"].items()
            if isinstance(v, dict) and v.get("is_visible", True)
        }
    return doc


def _auth_providers_from_token(token: dict) -> list[str]:
    providers = []
    sign_in = token.get("firebase", {}).get("sign_in_provider")
    if sign_in:
        mapping = {
            "password": "email",
            "google.com": "google",
            "github.com": "github",
            "phone": "phone",
            "anonymous": "anonymous",
        }
        providers.append(mapping.get(sign_in, sign_in))
    return providers


def _record_login(users_col, user_id: str, token: dict, request: Request) -> None:
    now = datetime.utcnow()
    providers = _auth_providers_from_token(token)
    event = {
        "at": now,
        "method": providers[0] if providers else "unknown",
        "user_agent": request.headers.get("user-agent"),
        "ip": request.client.host if request.client else None,
    }
    users_col.update_one(
        {"user_id": user_id},
        {
            "$set": {"last_login": now},
            "$push": {
                "login_history": {
                    "$each": [event],
                    "$position": 0,
                    "$slice": MAX_LOGIN_HISTORY,
                }
            },
        },
    )
    if providers:
        users_col.update_one(
            {"user_id": user_id},
            {"$addToSet": {"auth_providers": {"$each": providers}}},
        )


def _mark_github_verified(users_col, user_id: str, token: dict) -> None:
    sign_in = token.get("firebase", {}).get("sign_in_provider")
    if sign_in != "github.com":
        return
    user = users_col.find_one({"user_id": user_id})
    if not user:
        return
    links = user.get("links") or {}
    github = links.get("github") or {}
    if github.get("url"):
        github["verified"] = True
        links["github"] = github
        users_col.update_one({"user_id": user_id}, {"$set": {"links": links}})


@router.post("/register", response_model=UserResponse)
async def register_user(
    user_data: UserCreate,
    request: Request,
    token: dict = Depends(get_current_user),
):
    if token.get("uid") != user_data.user_id:
        raise HTTPException(
            status_code=403, detail="Not authorized to create this user"
        )

    users_col = collection("users")
    if users_col is None:
        raise HTTPException(status_code=500, detail="Database not available")

    existing = users_col.find_one({"user_id": user_data.user_id})
    if existing:
        _record_login(users_col, user_data.user_id, token, request)
        _mark_github_verified(users_col, user_data.user_id, token)
        return existing

    if not user_data.avatar_url or user_data.avatar_url not in VALID_AVATARS:
        user_data.avatar_url = f"/avatars/users/u{random.randint(1, 20)}.png"

    providers = _auth_providers_from_token(token)
    new_user = user_data.dict()
    new_user["created_at"] = datetime.utcnow()
    new_user["auth_providers"] = providers
    new_user["last_login"] = datetime.utcnow()
    new_user["login_history"] = [
        {
            "at": datetime.utcnow(),
            "method": providers[0] if providers else "unknown",
            "user_agent": request.headers.get("user-agent"),
            "ip": request.client.host if request.client else None,
        }
    ]
    users_col.insert_one(new_user)
    _mark_github_verified(users_col, user_data.user_id, token)
    return new_user


@router.get("/me", response_model=UserResponse)
async def get_my_profile(token: dict = Depends(get_current_user)):
    users_col = collection("users")
    if users_col is None:
        raise HTTPException(status_code=500, detail="Database not available")

    user_id = token.get("uid")
    user = users_col.find_one({"user_id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return user


@router.put("/me", response_model=UserResponse)
async def update_my_profile(
    update_data: UserUpdate, token: dict = Depends(get_current_user)
):
    users_col = collection("users")
    if users_col is None:
        raise HTTPException(status_code=500, detail="Database not available")

    user_id = token.get("uid")

    if update_data.username:
        existing = users_col.find_one(
            {"username": update_data.username, "user_id": {"$ne": user_id}}
        )
        if existing:
            raise HTTPException(status_code=400, detail="Username already taken")

    if update_data.avatar_url and update_data.avatar_url not in VALID_AVATARS:
        raise HTTPException(status_code=400, detail="Invalid avatar selection")

    if update_data.links:
        for platform, link in update_data.links.items():
            if link and link.url:
                err = validate_link(platform, link.url)
                if err:
                    raise HTTPException(status_code=400, detail=err)

    update_dict = {k: v for k, v in update_data.dict().items() if v is not None}

    if not update_dict:
        user = users_col.find_one({"user_id": user_id})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return user

    users_col.update_one({"user_id": user_id}, {"$set": update_dict})
    return users_col.find_one({"user_id": user_id})


@router.get("/me/activity", response_model=ActivityResponse)
async def get_my_activity(token: dict = Depends(get_current_user)):
    users_col = collection("users")
    if users_col is None:
        raise HTTPException(status_code=500, detail="Database not available")

    user_id = token.get("uid")
    user = users_col.find_one({"user_id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    history = user.get("login_history") or []
    return ActivityResponse(
        last_login=user.get("last_login"),
        login_history=[
            LoginEvent(**h) if isinstance(h, dict) else h
            for h in history[:MAX_LOGIN_HISTORY]
        ],
        email_verified=bool(token.get("email_verified")),
        auth_providers=user.get("auth_providers") or _auth_providers_from_token(token),
    )


@router.post("/me/sessions/revoke-all")
async def revoke_all_sessions(token: dict = Depends(get_current_user)):
    user_id = token.get("uid")
    try:
        from firebase_admin import auth as firebase_auth

        firebase_auth.revoke_refresh_tokens(user_id)
    except Exception as exc:
        raise HTTPException(
            status_code=500, detail=f"Failed to revoke sessions: {exc}"
        ) from exc
    return {
        "status": "success",
        "message": "All sessions revoked. Sign in again on this device.",
    }


@router.post("/me/notify/password-changed")
async def notify_password_changed(token: dict = Depends(get_current_user)):
    email = token.get("email")
    if not email:
        raise HTTPException(status_code=400, detail="No email on account")
    if not email_enabled():
        return {"status": "skipped", "message": "Email notifications not configured"}
    sent = send_email(
        email,
        "Nexora — Password changed",
        "<p>Your Nexora account password was changed. If this wasn't you, reset your password immediately.</p>",
        "Your Nexora account password was changed.",
    )
    return {"status": "sent" if sent else "failed"}


@router.post("/me/notify/new-login")
async def notify_new_login(request: Request, token: dict = Depends(get_current_user)):
    email = token.get("email")
    if not email or not email_enabled():
        return {"status": "skipped"}
    ua = request.headers.get("user-agent", "Unknown device")
    ip = request.client.host if request.client else "Unknown"
    sent = send_email(
        email,
        "Nexora — New sign-in detected",
        f"<p>A new sign-in to your Nexora account was detected.</p><p>Device: {ua}</p><p>IP: {ip}</p>",
        f"New sign-in detected. Device: {ua}, IP: {ip}",
    )
    return {"status": "sent" if sent else "failed"}


@router.get("/profile/{username}", response_model=UserResponse)
async def get_public_profile(username: str):
    users_col = collection("users")
    if users_col is None:
        raise HTTPException(status_code=500, detail="Database not available")

    user = users_col.find_one({"username": username})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if not user.get("is_public", True):
        raise HTTPException(status_code=403, detail="This profile is private")

    if user.get("links"):
        user["links"] = {
            k: v for k, v in user["links"].items() if v.get("is_visible", True)
        }

    return _sanitize_user(user)


@router.get("/me/datasets")
async def get_my_datasets(token: dict = Depends(get_current_user)):
    user_id = token.get("uid")
    datasets_col = collection("datasets")
    if datasets_col is None:
        return {"datasets": []}
    docs = list(
        datasets_col.find({"user_id": user_id}, {"_id": 0})
        .sort("updated_at", -1)
        .limit(50)
    )
    return {"datasets": docs}


@router.get("/me/export")
async def export_my_data(token: dict = Depends(get_current_user)):
    user_id = token.get("uid")
    users_col = collection("users")
    datasets_col = collection("datasets")
    if users_col is None:
        raise HTTPException(status_code=500, detail="Database not available")
    user = users_col.find_one({"user_id": user_id}, {"_id": 0, "password_hash": 0})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    datasets = []
    if datasets_col is not None:
        datasets = list(datasets_col.find({"user_id": user_id}, {"_id": 0}))
    return {
        "exported_at": datetime.utcnow().isoformat(),
        "profile": user,
        "datasets": datasets,
    }


@router.delete("/me")
async def delete_my_account(token: dict = Depends(get_current_user)):
    users_col = collection("users")
    if users_col is None:
        raise HTTPException(status_code=500, detail="Database not available")

    user_id = token.get("uid")
    users_col.delete_one({"user_id": user_id})
    return {"status": "success", "message": "User account deleted successfully"}
