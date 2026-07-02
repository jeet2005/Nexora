from datetime import datetime
from typing import Any

from pydantic import BaseModel, EmailStr, Field


class AdminUser(BaseModel):
    email: EmailStr
    password_hash: str
    name: str | None = None
    avatar_url: str | None = None
    created_at: datetime
    last_login: datetime | None = None


class AdminProfileUpdate(BaseModel):
    name: str | None = None
    avatar_url: str | None = None


class AdminPasswordChange(BaseModel):
    current_password: str
    new_password: str


class AdminForgotPasswordRequest(BaseModel):
    email: EmailStr


class AdminResetPasswordRequest(BaseModel):
    token: str
    new_password: str


class AdminOtpRequest(BaseModel):
    email: EmailStr


class AdminOtpLoginRequest(BaseModel):
    email: EmailStr
    code: str


class AdminLoginRequest(BaseModel):
    email: EmailStr
    password: str


class AdminLoginResponse(BaseModel):
    success: bool
    email: EmailStr
    message: str


class AuditLogEntry(BaseModel):
    admin_email: str
    action: str
    target: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    ip_address: str | None = None


class SiteContent(BaseModel):
    key: str
    value: Any
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    updated_by: str
