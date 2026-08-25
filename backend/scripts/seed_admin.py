"""
Create the initial admin user.

Usage:
    python scripts/seed_admin.py
    # or override via env:
    ADMIN_EMAIL=me@example.com ADMIN_PASSWORD=secret python scripts/seed_admin.py
"""
import asyncio
import logging
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select
from app.config import get_settings
from app.database import AsyncSessionLocal, engine, Base
from app.models.user import User

logging.basicConfig(level=logging.INFO, format="%(levelname)s — %(message)s")
logger = logging.getLogger(__name__)

settings = get_settings()


def _hash_password(password: str) -> str:
    import bcrypt
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


async def create_admin() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as db:
        result = await db.execute(select(User).where(User.email == settings.admin_email))
        existing = result.scalar_one_or_none()

        if existing:
            logger.info("Admin already exists: %s", settings.admin_email)
            return

        admin = User(
            email=settings.admin_email,
            password_hash=_hash_password(settings.admin_password),
            full_name=settings.admin_full_name,
            role="admin",
            hospital_id=None,
            is_active=True,
        )
        db.add(admin)
        await db.commit()
        logger.info("Admin created: %s", settings.admin_email)


if __name__ == "__main__":
    asyncio.run(create_admin())
