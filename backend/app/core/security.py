"""
JWT utilities and password hashing.
All crypto primitives live here; deps.py builds FastAPI dependencies on top.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

import bcrypt
from jose import jwt

from app.config import get_settings

settings = get_settings()


# ── Password ──────────────────────────────────────────────────────────────────

def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())


# ── JWT ───────────────────────────────────────────────────────────────────────

def _now() -> datetime:
    return datetime.now(tz=timezone.utc)


def create_access_token(data: dict[str, Any]) -> str:
    expire = _now() + timedelta(minutes=settings.access_token_expire_minutes)
    return jwt.encode(
        {**data, "exp": expire, "type": "access"},
        settings.secret_key,
        algorithm=settings.algorithm,
    )


def create_refresh_token(data: dict[str, Any]) -> str:
    expire = _now() + timedelta(days=settings.refresh_token_expire_days)
    return jwt.encode(
        {**data, "exp": expire, "type": "refresh"},
        settings.secret_key,
        algorithm=settings.algorithm,
    )


def decode_token(token: str) -> dict[str, Any]:
    """Raises jose.JWTError on invalid/expired tokens."""
    return jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
