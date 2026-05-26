import secrets

from fastapi import APIRouter, Depends, HTTPException, status

from app.auth import create_access_token
from app.config import settings
from app.deps import get_current_user
from app.schemas import LoginRequest, TokenResponse, UserResponse

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
def login(data: LoginRequest):
    user_ok = secrets.compare_digest(data.username, settings.admin_username)
    pass_ok = secrets.compare_digest(data.password, settings.admin_password)
    if not user_ok or not pass_ok:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario o contraseña incorrectos",
        )
    token = create_access_token(settings.admin_username)
    return TokenResponse(access_token=token)


@router.get("/me", response_model=UserResponse)
def me(username: str = Depends(get_current_user)):
    return UserResponse(username=username)
