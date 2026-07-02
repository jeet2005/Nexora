import random
import secrets
from datetime import datetime, timedelta

import bcrypt
import jwt
from fastapi import APIRouter, Depends, HTTPException, Request, Response

from app.config import settings
from app.middleware.admin_auth_guard import require_admin
from app.models.admin import (
    AdminForgotPasswordRequest,
    AdminLoginRequest,
    AdminLoginResponse,
    AdminOtpLoginRequest,
    AdminOtpRequest,
    AdminPasswordChange,
    AdminProfileUpdate,
    AdminResetPasswordRequest,
)
from app.services.email_service import _is_configured as email_enabled
from app.services.email_service import send_email
from app.services.persistence_service import collection

router = APIRouter(prefix="/api/admin", tags=["admin"])

RATE_LIMIT_MINUTES = 15
MAX_ATTEMPTS = 5
PASSWORD_RESET_EXPIRY_MINUTES = 15
OTP_EXPIRY_MINUTES = 10
login_attempts = {}


def _hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def _verify_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))


def _generate_token() -> str:
    return secrets.token_urlsafe(32)


def _generate_otp_code() -> str:
    return f"{random.randint(0, 999999):06d}"


def _admin_collection():
    return collection("admins")


def _reset_collection():
    return collection("admin_password_resets")


def _otp_collection():
    return collection("admin_otp_codes")


def _issue_token(response: Response, email: str) -> None:
    now = datetime.utcnow()
    token_exp = now + timedelta(hours=8)
    payload = {"sub": email, "exp": token_exp}
    token = jwt.encode(payload, settings.admin_jwt_secret, algorithm=settings.admin_jwt_algorithm)
    response.set_cookie(
        key="admin_token",
        value=token,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=8 * 60 * 60,
    )


def _admin_login_response(email: str) -> AdminLoginResponse:
    return AdminLoginResponse(success=True, email=email, message="Logged in successfully")


@router.post("/login", response_model=AdminLoginResponse)
async def login(request: Request, response: Response, login_data: AdminLoginRequest):
    client_ip = request.client.host
    now = datetime.utcnow()

    if client_ip in login_attempts:
        attempts, last_attempt = login_attempts[client_ip]
        if (now - last_attempt).total_seconds() < RATE_LIMIT_MINUTES * 60:
            if attempts >= MAX_ATTEMPTS:
                raise HTTPException(status_code=429, detail="Too many login attempts")
            login_attempts[client_ip] = (attempts + 1, now)
        else:
            login_attempts[client_ip] = (1, now)
    else:
        login_attempts[client_ip] = (1, now)

    if settings.persistence_backend != "mongodb":
        raise HTTPException(status_code=500, detail="MongoDB is required for Admin Panel")

    admins_coll = _admin_collection()
    if admins_coll is None:
        raise HTTPException(status_code=500, detail="Database connection failed")

    admin_doc = admins_coll.find_one({"email": login_data.email})
    if not admin_doc or not _verify_password(login_data.password, admin_doc["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if client_ip in login_attempts:
        del login_attempts[client_ip]

    admins_coll.update_one({"_id": admin_doc["_id"]}, {"$set": {"last_login": now}})
    _issue_token(response, login_data.email)
    return _admin_login_response(login_data.email)


@router.post("/request-otp")
async def request_otp(request_data: AdminOtpRequest):
    if settings.persistence_backend != "mongodb":
        raise HTTPException(status_code=500, detail="MongoDB is required for Admin Panel")

    admins_coll = _admin_collection()
    if admins_coll is None:
        raise HTTPException(status_code=500, detail="Database connection failed")

    admin_doc = admins_coll.find_one({"email": request_data.email})
    if admin_doc:
        otp_code = _generate_otp_code()
        otp_coll = _otp_collection()
        if otp_coll is not None:
            otp_coll.update_one(
                {"email": request_data.email},
                {
                    "$set": {
                        "code_hash": bcrypt.hashpw(otp_code.encode("utf-8"), bcrypt.gensalt()).decode("utf-8"),
                        "expires_at": datetime.utcnow() + timedelta(minutes=OTP_EXPIRY_MINUTES),
                        "used": False,
                    }
                },
                upsert=True,
            )
            if email_enabled():
                send_email(
                    request_data.email,
                    "Nexora Admin OTP Code",
                    f"<p>Your Nexora admin login code is <strong>{otp_code}</strong>.</p><p>It expires in {OTP_EXPIRY_MINUTES} minutes.</p>",
                    f"Your Nexora admin login code is {otp_code}.",
                )

    return {"success": True, "message": "If the account exists, an OTP has been sent to the registered email address."}


@router.post("/login-otp", response_model=AdminLoginResponse)
async def login_otp(request: Request, response: Response, request_data: AdminOtpLoginRequest):
    if settings.persistence_backend != "mongodb":
        raise HTTPException(status_code=500, detail="MongoDB is required for Admin Panel")

    otp_coll = _otp_collection()
    admins_coll = _admin_collection()
    if otp_coll is None or admins_coll is None:
        raise HTTPException(status_code=500, detail="Database connection failed")

    otp_doc = otp_coll.find_one({"email": request_data.email, "used": False})
    if (
        not otp_doc
        or otp_doc.get("expires_at") is None
        or otp_doc["expires_at"] < datetime.utcnow()
        or not bcrypt.checkpw(request_data.code.encode("utf-8"), otp_doc["code_hash"].encode("utf-8"))
    ):
        raise HTTPException(status_code=401, detail="Invalid OTP code")

    admin_doc = admins_coll.find_one({"email": request_data.email})
    if not admin_doc:
        raise HTTPException(status_code=401, detail="Invalid OTP code")

    otp_coll.update_one({"email": request_data.email}, {"$set": {"used": True}})
    admins_coll.update_one({"_id": admin_doc["_id"]}, {"$set": {"last_login": datetime.utcnow()}})
    _issue_token(response, request_data.email)
    return _admin_login_response(request_data.email)


@router.post("/forgot-password")
async def forgot_password(request_data: AdminForgotPasswordRequest):
    if settings.persistence_backend != "mongodb":
        raise HTTPException(status_code=500, detail="MongoDB is required for Admin Panel")

    admins_coll = _admin_collection()
    reset_coll = _reset_collection()
    if admins_coll is None or reset_coll is None:
        raise HTTPException(status_code=500, detail="Database connection failed")

    admin_doc = admins_coll.find_one({"email": request_data.email})
    if admin_doc:
        token = _generate_token()
        expires_at = datetime.utcnow() + timedelta(minutes=PASSWORD_RESET_EXPIRY_MINUTES)
        reset_coll.update_one(
            {"email": request_data.email},
            {
                "$set": {
                    "token": token,
                    "expires_at": expires_at,
                    "used": False,
                }
            },
            upsert=True,
        )
        if email_enabled():
            reset_link = f"{settings.public_app_url.rstrip('/')}/admin/reset-password?token={token}"
            send_email(
                request_data.email,
                "Nexora Admin Password Reset",
                f"<p>A password reset was requested for your Nexora admin account.</p><p>Click the link below to reset your password:</p><p><a href=\"{reset_link}\">Reset my password</a></p><p>This link expires in {PASSWORD_RESET_EXPIRY_MINUTES} minutes.</p>",
                f"Use this link to reset your admin password: {reset_link}",
            )

    return {"success": True, "message": "If the account exists, a password reset link has been sent to the registered email address."}


@router.post("/reset-password")
async def reset_password(request_data: AdminResetPasswordRequest):
    if settings.persistence_backend != "mongodb":
        raise HTTPException(status_code=500, detail="MongoDB is required for Admin Panel")

    admins_coll = _admin_collection()
    reset_coll = _reset_collection()
    if admins_coll is None or reset_coll is None:
        raise HTTPException(status_code=500, detail="Database connection failed")

    reset_doc = reset_coll.find_one({"token": request_data.token, "used": False})
    if not reset_doc or reset_doc.get("expires_at") is None or reset_doc["expires_at"] < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")

    updated = admins_coll.update_one(
        {"email": reset_doc["email"]},
        {"$set": {"password_hash": _hash_password(request_data.new_password)}},
    )
    if updated.matched_count == 0:
        raise HTTPException(status_code=404, detail="Admin user not found")

    reset_coll.update_one({"token": request_data.token}, {"$set": {"used": True}})
    return {"success": True, "message": "Password reset successfully."}


@router.post("/logout")
async def logout(response: Response):
    response.delete_cookie(key="admin_token")
    return {"success": True, "message": "Logged out"}


@router.get("/me")
async def get_me(admin: dict = Depends(require_admin)):
    admins_coll = _admin_collection()
    if admins_coll is None:
        return {"email": admin["email"], "name": admin["email"].split("@")[0], "avatar_url": "/avatars/admins/a1.png"}
    doc = admins_coll.find_one({"email": admin["email"]}, {"_id": 0, "password_hash": 0})
    if not doc:
        return {"email": admin["email"], "name": admin["email"].split("@")[0], "avatar_url": "/avatars/admins/a1.png"}
    return {
        "email": doc["email"],
        "name": doc.get("name") or doc["email"].split("@")[0],
        "avatar_url": doc.get("avatar_url") or "/avatars/admins/a1.png",
        "created_at": doc.get("created_at"),
        "last_login": doc.get("last_login"),
    }


@router.put("/me")
async def update_profile(update: AdminProfileUpdate, admin: dict = Depends(require_admin)):
    admins_coll = _admin_collection()
    if admins_coll is None:
        raise HTTPException(status_code=500, detail="Database connection failed")
    update_dict = {k: v for k, v in update.dict().items() if v is not None}
    if update_dict:
        admins_coll.update_one({"email": admin["email"]}, {"$set": update_dict})
    return await get_me(admin)


@router.put("/me/password")
async def change_password(data: AdminPasswordChange, admin: dict = Depends(require_admin)):
    admins_coll = _admin_collection()
    if admins_coll is None:
        raise HTTPException(status_code=500, detail="Database connection failed")

    admin_doc = admins_coll.find_one({"email": admin["email"]})
    if not admin_doc or not _verify_password(data.current_password, admin_doc["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid current password")

    admins_coll.update_one({"email": admin["email"]}, {"$set": {"password_hash": _hash_password(data.new_password)}})
    return {"success": True, "message": "Password updated successfully."}
