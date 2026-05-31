from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel

from app.auth import (
    Token,
    User,
    _hash_password,
    authenticate_user,
    create_access_token,
    get_current_active_user,
    mock_users_db,
)

router = APIRouter(prefix="/api/auth", tags=["auth"])


class RegisterRequest(BaseModel):
    username: str
    password: str


@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"sub": user.username})
    return Token(access_token=access_token, token_type="bearer")


@router.post("/register", response_model=Token)
async def register(body: RegisterRequest):
    if not body.username or not body.password:
        raise HTTPException(status_code=400, detail="Username and password required")
    if body.username in mock_users_db:
        raise HTTPException(status_code=400, detail="Username already registered")
    user = User(
        username=body.username,
        hashed_password=_hash_password(body.password),
        disabled=False,
    )
    mock_users_db[body.username] = user
    access_token = create_access_token(data={"sub": user.username})
    return Token(access_token=access_token, token_type="bearer")


@router.get("/me")
async def read_users_me(current_user: dict = Depends(get_current_active_user)):
    return current_user
