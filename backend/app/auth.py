import hashlib
import os
import re
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from pydantic import BaseModel

from app.database import (
    get_db,
    get_user_by_id,
    get_user_by_username,
    create_login_history as db_create_login_history,
    get_login_history as db_get_login_history,
    get_user_sessions as db_get_user_sessions,
    create_session as db_create_session,
    get_session_by_refresh_hash,
    deactivate_session as db_deactivate_session,
    deactivate_all_user_sessions as db_deactivate_all_sessions,
    update_user as db_update_user,
)
from app.models import AuthUser, LoginHistoryEntry, UserSession, UserRole

SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "15"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("JWT_REFRESH_EXPIRE_DAYS", "7"))
MAX_FAILED_LOGIN_ATTEMPTS = 5
LOCKOUT_DURATION_MINUTES = 15

security = HTTPBearer(auto_error=False)

# ── Password Helpers ────────────────────────────────────────

def _hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    h = hashlib.sha256((salt + password).encode()).hexdigest()
    return f"{salt}:{h}"


def _verify_password(password: str, hashed: str) -> bool:
    try:
        salt, h = hashed.split(":", 1)
        return hashlib.sha256((salt + password).encode()).hexdigest() == h
    except ValueError:
        return False


PASSWORD_POLICY = re.compile(r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[!@#$%^&*()_+\-=\[\]{};':\"\\|,.<>\/?]).{8,128}$")


def validate_password(password: str) -> Optional[str]:
    if len(password) < 8:
        return "Password must be at least 8 characters"
    if len(password) > 128:
        return "Password must be at most 128 characters"
    if not re.search(r"[a-z]", password):
        return "Password must contain a lowercase letter"
    if not re.search(r"[A-Z]", password):
        return "Password must contain an uppercase letter"
    if not re.search(r"\d", password):
        return "Password must contain a digit"
    if not re.search(r"[!@#$%^&*()_+\-=\[\]{};':\"\\|,.<>\/?]", password):
        return "Password must contain a special character"
    return None


# ── Token Helpers ───────────────────────────────────────────

def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def create_refresh_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def verify_token(token: str, expected_type: str = "access") -> Optional[dict]:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != expected_type:
            return None
        return payload
    except JWTError:
        return None


# ── Auth Dependencies ───────────────────────────────────────

async def get_optional_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> Optional[dict]:
    if credentials is None:
        return None
    payload = verify_token(credentials.credentials, "access")
    if payload is None:
        return None
    return payload


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict:
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    payload = verify_token(credentials.credentials, "access")
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired access token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    with get_db() as conn:
        user = get_user_by_id(conn, payload.get("sub"))
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )
    if user.disabled:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is disabled",
        )
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "role": user.role.value,
        "email_verified": user.email_verified,
        "twofa_enabled": user.twofa_enabled,
    }


class RoleChecker:
    def __init__(self, required_role: UserRole):
        self.required_role = required_role
        self._role_order = {UserRole.admin: 2, UserRole.user: 1}

    async def __call__(self, current_user: dict = Depends(get_current_user)) -> dict:
        if self._role_order.get(UserRole(current_user["role"]), 0) < self._role_order[self.required_role]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires {self.required_role.value} role or higher",
            )
        return current_user


require_role = RoleChecker


# ── 2FA Simulation ──────────────────────────────────────────

def generate_2fa_secret() -> str:
    return secrets.token_hex(16)


def verify_2fa_code(secret: str, code: str) -> bool:
    expected = hashlib.sha256(secret.encode()).hexdigest()[:6]
    return code == expected


def generate_2fa_code(secret: str) -> str:
    return hashlib.sha256(secret.encode()).hexdigest()[:6]


# ── Account Lockout ─────────────────────────────────────────

def is_account_locked(user: AuthUser) -> bool:
    if user.locked_until is None:
        return False
    try:
        lock_until = datetime.fromisoformat(user.locked_until)
        if datetime.now() < lock_until:
            return True
        return False
    except (ValueError, TypeError):
        return False


def lock_account(user: AuthUser) -> AuthUser:
    now = datetime.now()
    user.locked_until = (now + timedelta(minutes=LOCKOUT_DURATION_MINUTES)).isoformat()
    return user


# ── Login Logic ─────────────────────────────────────────────

async def perform_login(
    username: str,
    password: str,
    request: Request,
    twofa_code: Optional[str] = None,
    device_info: Optional[str] = None,
) -> dict:
    ip = request.client.host if request.client else "0.0.0.0"
    device = device_info or request.headers.get("User-Agent", "Unknown")[:128]

    with get_db() as conn:
        user = get_user_by_username(conn, username)
        if user is None:
            db_create_login_history(conn, LoginHistoryEntry(
                id=str(uuid.uuid4())[:8], user_id="unknown",
                ip_address=ip, device_info=device,
                success=False, fail_reason="User not found",
                timestamp=datetime.now().isoformat(),
            ))
            raise HTTPException(status_code=401, detail="Invalid username or password")

        if user.disabled:
            raise HTTPException(status_code=403, detail="Account is disabled")

        if is_account_locked(user):
            db_create_login_history(conn, LoginHistoryEntry(
                id=str(uuid.uuid4())[:8], user_id=user.id,
                ip_address=ip, device_info=device,
                success=False, fail_reason="Account locked",
                timestamp=datetime.now().isoformat(),
            ))
            raise HTTPException(
                status_code=423,
                detail=f"Account locked due to too many failed attempts. Try again after {LOCKOUT_DURATION_MINUTES} minutes.",
            )

        if not _verify_password(password, user.hashed_password):
            user.failed_login_attempts += 1
            if user.failed_login_attempts >= MAX_FAILED_LOGIN_ATTEMPTS:
                user = lock_account(user)
            db_update_user(conn, user)
            db_create_login_history(conn, LoginHistoryEntry(
                id=str(uuid.uuid4())[:8], user_id=user.id,
                ip_address=ip, device_info=device,
                success=False, fail_reason="Wrong password",
                timestamp=datetime.now().isoformat(),
            ))
            remaining = MAX_FAILED_LOGIN_ATTEMPTS - user.failed_login_attempts
            detail = "Invalid username or password"
            if remaining > 0 and user.failed_login_attempts < MAX_FAILED_LOGIN_ATTEMPTS:
                detail = f"Invalid username or password ({remaining} attempt{'s' if remaining != 1 else ''} remaining)"
            raise HTTPException(status_code=401, detail=detail)

        if user.twofa_enabled:
            if not twofa_code:
                db_create_login_history(conn, LoginHistoryEntry(
                    id=str(uuid.uuid4())[:8], user_id=user.id,
                    ip_address=ip, device_info=device,
                    success=False, fail_reason="2FA code required",
                    timestamp=datetime.now().isoformat(),
                ))
                raise HTTPException(
                    status_code=428,
                    detail="2FA code required",
                    headers={"X-2FA-Required": "true"},
                )
            if not verify_2fa_code(user.twofa_secret or "", twofa_code):
                db_create_login_history(conn, LoginHistoryEntry(
                    id=str(uuid.uuid4())[:8], user_id=user.id,
                    ip_address=ip, device_info=device,
                    success=False, fail_reason="Invalid 2FA code",
                    timestamp=datetime.now().isoformat(),
                ))
                raise HTTPException(status_code=401, detail="Invalid 2FA code")

        user.failed_login_attempts = 0
        user.locked_until = None
        user.last_login = datetime.now().isoformat()
        db_update_user(conn, user)

        access_token = create_access_token(data={"sub": user.id, "username": user.username, "role": user.role.value})
        refresh_token = create_refresh_token(data={"sub": user.id})

        refresh_hash = _hash_token(refresh_token)
        session = UserSession(
            id=str(uuid.uuid4())[:8],
            user_id=user.id,
            refresh_token_hash=refresh_hash,
            device_info=device,
            ip_address=ip,
            created_at=datetime.now().isoformat(),
            last_activity=datetime.now().isoformat(),
        )
        db_create_session(conn, session)

        db_create_login_history(conn, LoginHistoryEntry(
            id=str(uuid.uuid4())[:8], user_id=user.id,
            ip_address=ip, device_info=device,
            success=True, timestamp=datetime.now().isoformat(),
        ))

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "role": user.role.value,
            "email_verified": user.email_verified,
            "twofa_enabled": user.twofa_enabled,
        },
    }


async def refresh_access_token(refresh_token: str) -> dict:
    payload = verify_token(refresh_token, "refresh")
    if payload is None:
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")

    user_id = payload.get("sub")
    token_hash = _hash_token(refresh_token)

    with get_db() as conn:
        session = get_session_by_refresh_hash(conn, token_hash)
        if session is None:
            raise HTTPException(status_code=401, detail="Session not found or expired")

        user = get_user_by_id(conn, user_id)
        if user is None or user.disabled:
            raise HTTPException(status_code=401, detail="User not found or disabled")

        new_access = create_access_token(data={"sub": user.id, "username": user.username, "role": user.role.value})
        new_refresh = create_refresh_token(data={"sub": user.id})
        new_hash = _hash_token(new_refresh)

        db_deactivate_session(conn, session.id)

        new_session = UserSession(
            id=str(uuid.uuid4())[:8],
            user_id=user.id,
            refresh_token_hash=new_hash,
            device_info=session.device_info,
            ip_address=session.ip_address,
            created_at=datetime.now().isoformat(),
            last_activity=datetime.now().isoformat(),
        )
        db_create_session(conn, new_session)

    return {
        "access_token": new_access,
        "refresh_token": new_refresh,
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "role": user.role.value,
            "email_verified": user.email_verified,
            "twofa_enabled": user.twofa_enabled,
        },
    }


# ── Seed Default Users ──────────────────────────────────────

def seed_users():
    from app.database import create_user
    default_users = [
        ("admin", "admin@shoporch.com", "Admin@123", UserRole.admin),
        ("user1", "user1@shoporch.com", "User@1234", UserRole.user),
    ]
    with get_db() as conn:
        for username, email, password, role in default_users:
            if get_user_by_username(conn, username) is None:
                user = AuthUser(
                    id=str(uuid.uuid4())[:8],
                    username=username,
                    email=email,
                    hashed_password=_hash_password(password),
                    role=role,
                    email_verified=True,
                    created_at=datetime.now().isoformat(),
                )
                create_user(conn, user)
