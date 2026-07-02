import jwt
from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyCookie

from app.config import settings

cookie_sec = APIKeyCookie(name="admin_token", auto_error=False)


def require_admin(token: str | None = Security(cookie_sec)):
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated"
        )
    try:
        payload = jwt.decode(
            token, settings.admin_jwt_secret, algorithms=[settings.admin_jwt_algorithm]
        )
        subject = payload.get("sub")
        if not isinstance(subject, str):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
            )
        return {"email": subject}
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token"
        )
