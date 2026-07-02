from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from app.config import settings


def firebase_enabled() -> bool:
    return bool(
        settings.firebase_project_id
        or settings.firebase_credentials_json
        or settings.firebase_credentials_file
    )


def _load_credentials_dict() -> dict | None:
    if settings.firebase_credentials_json:
        return json.loads(settings.firebase_credentials_json)
    if settings.firebase_credentials_file:
        path = Path(settings.firebase_credentials_file)
        if not path.is_absolute():
            path = Path(__file__).resolve().parent.parent.parent / path
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
    return None


@lru_cache(maxsize=1)
def _firebase_app():
    if not firebase_enabled():
        return None
    try:
        import firebase_admin
        from firebase_admin import credentials
    except ImportError:
        return None

    if firebase_admin._apps:
        return firebase_admin.get_app()

    if settings.firebase_credentials_json or settings.firebase_credentials_file:
        info = _load_credentials_dict()
        if info is None:
            return None
        cred = credentials.Certificate(info)
        return firebase_admin.initialize_app(cred)

    return firebase_admin.initialize_app(
        options={"projectId": settings.firebase_project_id}
    )


def verify_bearer_token(authorization: str | None) -> dict[str, Any] | None:
    if not authorization or not authorization.lower().startswith("bearer "):
        return None
    app = _firebase_app()
    if app is None:
        return None
    token = authorization.split(" ", 1)[1].strip()
    try:
        from firebase_admin import auth

        return auth.verify_id_token(token, app=app)
    except Exception:
        return None
