"""
Demo seed script.

Creates:
  1. Demo Excel workbook (3 hospitals × 8 claims = 24 rows)
  2. Imports all claims via the sync pipeline
  3. Admin user  (admin@hsk.local / admin123)
  4. One hospital_user per hospital  (<slug>@hsk.local / hospital123)

Usage (from backend/ with venv active):
    python scripts/seed_demo.py

Inside Docker:
    docker compose exec backend python scripts/seed_demo.py
"""
from __future__ import annotations

import asyncio
import io
import logging
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import bcrypt
from sqlalchemy import select

from app.database import AsyncSessionLocal, engine, Base
from app.models.hospital import Hospital
from app.models.user import User
from app.sync.pipeline import run_sync
from app.sync.sources.upload import UploadSource

logging.basicConfig(level=logging.INFO, format="%(levelname)s — %(message)s")
log = logging.getLogger(__name__)

# ── Demo user credentials ─────────────────────────────────────────────────────
ADMIN_EMAIL = "admin@hsk.local"
ADMIN_PASSWORD = "admin123"
ADMIN_NAME = "HSK Admin"

HOSPITAL_USER_PASSWORD = "hospital123"


def _hash(pw: str) -> str:
    return bcrypt.hashpw(pw.encode(), bcrypt.gensalt()).decode()


def _slug(name: str) -> str:
    """Turn 'Tanya Speciality Hospital' → 'tanya'."""
    return name.split()[0].lower()


# ── Step 1: generate demo Excel in-memory ─────────────────────────────────────

def _build_excel_bytes() -> bytes:
    """Import generate_demo_excel and produce the workbook as bytes."""
    import importlib.util
    import pathlib
    import tempfile

    script_dir = pathlib.Path(__file__).resolve().parent
    spec = importlib.util.spec_from_file_location(
        "generate_demo_excel",
        script_dir / "generate_demo_excel.py",
    )
    mod = importlib.util.module_from_spec(spec)  # type: ignore[arg-type]
    spec.loader.exec_module(mod)  # type: ignore[union-attr]

    with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp:
        tmp_path = tmp.name
    try:
        mod.generate_workbook(tmp_path)
        with open(tmp_path, "rb") as fh:
            return fh.read()
    finally:
        os.unlink(tmp_path)


# ── Step 2: ensure tables exist ───────────────────────────────────────────────

async def _ensure_tables() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    log.info("Tables ready.")


# ── Step 3: run Excel sync ────────────────────────────────────────────────────

async def _sync_excel(excel_bytes: bytes) -> None:
    source = UploadSource(file_bytes=excel_bytes, filename="demo.xlsx")
    async with AsyncSessionLocal() as db:
        result = await run_sync(db, source, triggered_by="seed_demo")
        await db.commit()
    log.info(
        "Sync done — processed=%d inserted=%d updated=%d skipped=%d errored=%d",
        result.rows_processed, result.rows_inserted, result.rows_updated,
        result.rows_skipped, result.rows_errored,
    )
    if result.errors:
        for e in result.errors[:5]:
            log.warning("  Sync error: %s", e)


# ── Step 4: create users ──────────────────────────────────────────────────────

async def _create_users() -> None:
    async with AsyncSessionLocal() as db:
        # Admin
        existing = (await db.execute(select(User).where(User.email == ADMIN_EMAIL))).scalar_one_or_none()
        if not existing:
            db.add(User(
                email=ADMIN_EMAIL,
                password_hash=_hash(ADMIN_PASSWORD),
                full_name=ADMIN_NAME,
                role="admin",
                hospital_id=None,
                is_active=True,
            ))
            log.info("Created admin: %s / %s", ADMIN_EMAIL, ADMIN_PASSWORD)
        else:
            log.info("Admin already exists: %s", ADMIN_EMAIL)

        # Hospital users
        hospitals = (await db.execute(select(Hospital))).scalars().all()
        for h in hospitals:
            slug = _slug(h.name)
            email = f"{slug}@hsk.local"
            exists = (await db.execute(select(User).where(User.email == email))).scalar_one_or_none()
            if not exists:
                db.add(User(
                    email=email,
                    password_hash=_hash(HOSPITAL_USER_PASSWORD),
                    full_name=f"{h.name} User",
                    role="hospital_user",
                    hospital_id=h.id,
                    is_active=True,
                ))
                log.info("Created hospital user: %s / %s  (hospital_id=%d)", email, HOSPITAL_USER_PASSWORD, h.id)
            else:
                log.info("Hospital user already exists: %s", email)

        await db.commit()


# ── Main ──────────────────────────────────────────────────────────────────────

async def _main() -> None:
    log.info("=== HSK Demo Seed ===")

    log.info("Step 1/4 — Building demo Excel…")
    excel_bytes = _build_excel_bytes()
    log.info("  Excel built (%d bytes, 24 rows, 3 hospitals)", len(excel_bytes))

    log.info("Step 2/4 — Ensuring database tables…")
    await _ensure_tables()

    log.info("Step 3/4 — Syncing Excel into database…")
    await _sync_excel(excel_bytes)

    log.info("Step 4/4 — Creating demo users…")
    await _create_users()

    log.info("")
    log.info("=== Seed Complete ===")
    log.info("")
    log.info("Demo login credentials:")
    log.info("  Admin       : %s / %s", ADMIN_EMAIL, ADMIN_PASSWORD)
    log.info("  Hospital 1  : tanya@hsk.local / %s", HOSPITAL_USER_PASSWORD)
    log.info("  Hospital 2  : apex@hsk.local / %s", HOSPITAL_USER_PASSWORD)
    log.info("  Hospital 3  : grace@hsk.local / %s", HOSPITAL_USER_PASSWORD)


if __name__ == "__main__":
    asyncio.run(_main())
