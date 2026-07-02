from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.services.auth_service import firebase_enabled, verify_bearer_token

security = HTTPBearer()
optional_security = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    if not firebase_enabled():
        raise HTTPException(
            status_code=503,
            detail=(
                "Firebase auth is not configured on the backend. Set "
                "FIREBASE_PROJECT_ID and either FIREBASE_CREDENTIALS_JSON or "
                "FIREBASE_CREDENTIALS_FILE in the deployed environment."
            ),
        )

    decoded = verify_bearer_token(f"Bearer {credentials.credentials}")
    if not decoded:
        raise HTTPException(
            status_code=401,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return decoded


async def get_optional_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(optional_security),
):
    if not credentials or not firebase_enabled():
        return None
    return verify_bearer_token(f"Bearer {credentials.credentials}")
