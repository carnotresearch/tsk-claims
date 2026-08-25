"""
Auth endpoints:
  POST /api/v1/auth/login    — OAuth2 form → access + refresh tokens
  POST /api/v1/auth/refresh  — refresh token → new token pair
  GET  /api/v1/auth/me       — current user info
"""
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from jose import JWTError
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    verify_password,
)
from app.database import get_db
from app.models.user import User
from app.schemas.auth import RefreshRequest, TokenResponse, UserMeResponse

router = APIRouter(prefix="/auth", tags=["auth"])


def _token_data(user: User) -> dict:
    return {"sub": str(user.id), "role": user.role, "hospital_id": user.hospital_id}


@router.post("/login", response_model=TokenResponse)
async def login(
    form: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(User).where(User.email == form.username, User.is_active.is_(True))
    )
    user = result.scalar_one_or_none()
    if not user or not verify_password(form.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    await db.execute(
        update(User)
        .where(User.id == user.id)
        .values(last_login=datetime.now(tz=timezone.utc))
    )
    await db.commit()

    td = _token_data(user)
    return TokenResponse(
        access_token=create_access_token(td),
        refresh_token=create_refresh_token(td),
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh(body: RefreshRequest, db: AsyncSession = Depends(get_db)):
    try:
        payload = decode_token(body.refresh_token)
        if payload.get("type") != "refresh":
            raise ValueError("not a refresh token")
    except (JWTError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )

    result = await db.execute(
        select(User).where(User.id == int(payload["sub"]), User.is_active.is_(True))
    )
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    td = _token_data(user)
    return TokenResponse(
        access_token=create_access_token(td),
        refresh_token=create_refresh_token(td),
    )


@router.get("/me", response_model=UserMeResponse)
async def me(current_user: User = Depends(get_current_user)):
    return current_user
