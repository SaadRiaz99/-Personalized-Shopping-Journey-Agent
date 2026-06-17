from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.auth import verify_token
from app.database import get_db, get_user_by_id

security = HTTPBearer(auto_error=False)


async def get_optional_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> Optional[dict]:
    if credentials is None:
        return None
    payload = verify_token(credentials.credentials, "access")
    if payload is None:
        return None
    user_id = payload.get("sub")
    if user_id is None:
        return None
    with get_db() as conn:
        user = get_user_by_id(conn, user_id)
    if user is None:
        return None
    return {"id": user.id, "username": user.username, "disabled": user.disabled}


async def require_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict:
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )
    payload = verify_token(credentials.credentials, "access")
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )
    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )
    with get_db() as conn:
        user = get_user_by_id(conn, user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )
    return {"id": user.id, "username": user.username, "disabled": user.disabled, "role": user.role.value if hasattr(user, 'role') else 'user'}
