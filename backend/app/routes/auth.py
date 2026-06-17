import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from app.auth import (
    get_current_user,
    perform_login,
    refresh_access_token,
    seed_users,
    validate_password,
    _hash_password,
)
from app.database import (
    get_db,
    create_user,
    get_user_by_username,
    get_user_by_email,
    get_login_history,
    get_user_sessions,
    deactivate_session,
    deactivate_all_user_sessions,
    list_users,
    update_user,
    get_user_by_id,
)
from app.models import (
    AuthUser,
    UserRole,
    RegisterRequest,
    LoginRequest,
    TokenResponse,
    RefreshRequest,
    ChangePasswordRequest,
)

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register")
async def register(body: RegisterRequest, request: Request):
    pwd_error = validate_password(body.password)
    if pwd_error:
        raise HTTPException(status_code=400, detail=pwd_error)

    if len(body.username) < 3 or len(body.username) > 32:
        raise HTTPException(status_code=400, detail="Username must be 3-32 characters")

    with get_db() as conn:
        if get_user_by_username(conn, body.username):
            raise HTTPException(status_code=409, detail="Username already taken")
        if get_user_by_email(conn, body.email):
            raise HTTPException(status_code=409, detail="Email already registered")

        user = AuthUser(
            id=str(uuid.uuid4())[:8],
            username=body.username,
            email=body.email,
            hashed_password=_hash_password(body.password),
            role=UserRole.user,
            created_at=datetime.now().isoformat(),
        )
        create_user(conn, user)

    return {"message": "User registered successfully", "user_id": user.id, "username": user.username}


@router.post("/login")
async def login(body: LoginRequest, request: Request):
    result = await perform_login(
        username=body.username,
        password=body.password,
        request=request,
        twofa_code=body.twofa_code,
        device_info=body.device_info,
    )
    return result


@router.post("/refresh")
async def refresh(body: RefreshRequest):
    return await refresh_access_token(body.refresh_token)


@router.post("/logout")
async def logout(current_user: dict = Depends(get_current_user)):
    with get_db() as conn:
        deactivate_all_user_sessions(conn, current_user["id"])
    return {"message": "Logged out successfully"}


@router.get("/me")
async def me(current_user: dict = Depends(get_current_user)):
    return current_user


@router.post("/change-password")
async def change_password(body: ChangePasswordRequest, current_user: dict = Depends(get_current_user)):
    from app.auth import _verify_password
    pwd_error = validate_password(body.new_password)
    if pwd_error:
        raise HTTPException(status_code=400, detail=pwd_error)

    with get_db() as conn:
        user = get_user_by_id(conn, current_user["id"])
        if not _verify_password(body.current_password, user.hashed_password):
            raise HTTPException(status_code=400, detail="Current password is incorrect")
        user.hashed_password = _hash_password(body.new_password)
        update_user(conn, user)
        deactivate_all_user_sessions(conn, user.id)

    return {"message": "Password changed successfully"}


@router.get("/history")
async def login_history(current_user: dict = Depends(get_current_user)):
    with get_db() as conn:
        entries = get_login_history(conn, current_user["id"])
    return {"entries": entries, "total": len(entries)}


@router.get("/sessions")
async def sessions(current_user: dict = Depends(get_current_user)):
    with get_db() as conn:
        sess = get_user_sessions(conn, current_user["id"])
    return {"sessions": sess, "total": len(sess)}


@router.delete("/sessions/{session_id}")
async def revoke_session(session_id: str, current_user: dict = Depends(get_current_user)):
    with get_db() as conn:
        deactivate_session(conn, session_id)
    return {"message": "Session revoked"}


@router.get("/users")
async def list_all_users(current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    with get_db() as conn:
        users = list_users(conn)
    return {"users": users, "total": len(users)}
