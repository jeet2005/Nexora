from datetime import datetime

from pydantic import BaseModel


class ExternalLink(BaseModel):
    url: str
    is_visible: bool = True
    verified: bool = False

class LoginEvent(BaseModel):
    at: datetime
    method: str
    user_agent: str | None = None
    ip: str | None = None

class UserBase(BaseModel):
    user_id: str
    email: str
    name: str | None = None
    username: str | None = None
    bio: str | None = None
    avatar_url: str | None = None
    role: str = "user" # user, contributor, admin
    is_public: bool = True
    requires_2fa: bool = False
    links: dict[str, ExternalLink] | None = None # Keys: github, linkedin, orcid, portfolio
    auth_providers: list[str] | None = None
    last_login: datetime | None = None
    login_history: list[LoginEvent] | None = None

class UserUpdate(BaseModel):
    name: str | None = None
    username: str | None = None
    bio: str | None = None
    avatar_url: str | None = None
    is_public: bool | None = None
    requires_2fa: bool | None = None
    links: dict[str, ExternalLink] | None = None

class UserCreate(UserBase):
    pass

class UserResponse(UserBase):
    created_at: datetime
    
    class Config:
        from_attributes = True

class ActivityResponse(BaseModel):
    last_login: datetime | None = None
    login_history: list[LoginEvent] = []
    email_verified: bool = False
    auth_providers: list[str] = []
