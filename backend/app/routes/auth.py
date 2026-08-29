import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.auth import (
    AuthUser,
    UserRole,
    RoleChecker,
    _hash_password,
    generate_2fa_secret,
    get_current_user,
    perform_login,
    refresh_access_token,
    validate_password,
    verify_2fa_code,
)
from app.database import (
    get_db,
    create_user as db_create_user,
    get_user_by_username,
    get_user_by_email,
    get_user_by_id,
    update_user as db_update_user,
    get_login_history as db_get_login_history,
    get_user_sessions as db_get_user_sessions,
    deactivate_session as db_deactivate_session,
    deactivate_all_user_sessions as db_deactivate_all_sessions,
)
from app.models import (
    RegisterRequest,
    LoginRequest,
    RefreshRequest,
    ChangePasswordRequest,
    TokenResponse,
)

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", status_code=201)
async def register(body: RegisterRequest):
    pw_error = validate_password(body.password)
    if pw_error:
        raise HTTPException(status_code=400, detail=pw_error)

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
        db_create_user(conn, user)

    return {
        "message": "Registration successful. Please log in.",
        "user_id": user.id,
        "username": user.username,
    }


@router.post("/login")
async def login(body: LoginRequest, request: Request):
    result = await perform_login(
        username=body.username,
        password=body.password,
        request=request,
        twofa_code=body.twofa_code,
        device_info=body.device_info,
    )
    return TokenResponse(**result)


@router.post("/refresh")
async def refresh(body: RefreshRequest):
    result = await refresh_access_token(body.refresh_token)
    return TokenResponse(**result)


@router.post("/logout")
async def logout(current_user: dict = Depends(get_current_user)):
    with get_db() as conn:
        db_deactivate_all_sessions(conn, current_user["id"])
    return {"message": "Logged out from all sessions"}


@router.get("/me")
async def get_me(current_user: dict = Depends(get_current_user)):
    return current_user


@router.post("/change-password")
async def change_password(body: ChangePasswordRequest, current_user: dict = Depends(get_current_user)):
    pw_error = validate_password(body.new_password)
    if pw_error:
        raise HTTPException(status_code=400, detail=pw_error)

    with get_db() as conn:
        user = get_user_by_id(conn, current_user["id"])
        if user is None:
            raise HTTPException(status_code=404, detail="User not found")

        from app.auth import _verify_password
        if not _verify_password(body.current_password, user.hashed_password):
            raise HTTPException(status_code=400, detail="Current password is incorrect")

        user.hashed_password = _hash_password(body.new_password)
        db_update_user(conn, user)
        db_deactivate_all_sessions(conn, user.id)

    return {"message": "Password changed successfully. Please log in again."}


@router.post("/verify-email/resend")
async def resend_verification(current_user: dict = Depends(get_current_user)):
    return {
        "message": f"Verification email sent to {current_user['email']}",
        "note": "In this demo, accounts are auto-verified on seed. Use /api/auth/verify-email/confirm to simulate.",
    }


@router.post("/verify-email/confirm")
async def confirm_email(current_user: dict = Depends(get_current_user)):
    with get_db() as conn:
        user = get_user_by_id(conn, current_user["id"])
        if user is None:
            raise HTTPException(status_code=404, detail="User not found")
        user.email_verified = True
        db_update_user(conn, user)
    return {"message": "Email verified successfully"}


@router.post("/2fa/enable")
async def enable_2fa(current_user: dict = Depends(get_current_user)):
    secret = generate_2fa_secret()
    with get_db() as conn:
        user = get_user_by_id(conn, current_user["id"])
        if user is None:
            raise HTTPException(status_code=404, detail="User not found")
        user.twofa_secret = secret
        user.twofa_enabled = True
        db_update_user(conn, user)
    return {
        "message": "2FA enabled. Add this setup key to your authenticator app.",
        "secret": secret,
        "otpauth_uri": f"otpauth://totp/ShopOrch:{user.username}?secret={secret}&issuer=ShopOrch",
    }


@router.post("/2fa/disable")
async def disable_2fa(current_user: dict = Depends(get_current_user)):
    with get_db() as conn:
        user = get_user_by_id(conn, current_user["id"])
        if user is None:
            raise HTTPException(status_code=404, detail="User not found")
        user.twofa_secret = None
        user.twofa_enabled = False
        db_update_user(conn, user)
    return {"message": "2FA disabled"}


@router.post("/2fa/verify")
async def verify_2fa(body: dict, current_user: dict = Depends(get_current_user)):
    code = body.get("code", "")
    with get_db() as conn:
        user = get_user_by_id(conn, current_user["id"])
        if user is None or not user.twofa_secret:
            raise HTTPException(status_code=400, detail="2FA not configured")
        if not verify_2fa_code(user.twofa_secret, code):
            raise HTTPException(status_code=400, detail="Invalid code")
    return {"message": "2FA code verified", "valid": True}


@router.get("/history")
async def get_history(current_user: dict = Depends(get_current_user)):
    with get_db() as conn:
        entries = db_get_login_history(conn, current_user["id"])
    return {"entries": [e.model_dump() for e in entries], "total": len(entries)}


@router.get("/sessions")
async def get_sessions(current_user: dict = Depends(get_current_user)):
    with get_db() as conn:
        sessions = db_get_user_sessions(conn, current_user["id"])
    return {"sessions": [s.model_dump() for s in sessions], "total": len(sessions)}


@router.delete("/sessions/{session_id}")
async def revoke_session(session_id: str, current_user: dict = Depends(get_current_user)):
    with get_db() as conn:
        owned_ids = {s.id for s in db_get_user_sessions(conn, current_user["id"])}
        if session_id not in owned_ids:
            raise HTTPException(status_code=404, detail="Session not found")
        if not db_deactivate_session(conn, session_id):
            raise HTTPException(status_code=404, detail="Session not found")
    return {"message": "Session revoked"}


@router.get("/users", dependencies=[Depends(RoleChecker(UserRole.admin))])
async def list_users(current_user: dict = Depends(get_current_user)):
    from app.database import list_users as db_list_users
    with get_db() as conn:
        users = db_list_users(conn)
    return {
        "users": [
            {"id": u.id, "username": u.username, "email": u.email, "role": u.role.value, "disabled": u.disabled, "created_at": u.created_at, "last_login": u.last_login}
            for u in users
        ],
        "total": len(users),
    }
