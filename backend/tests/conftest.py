"""
Shared fixtures for all test tiers.

DB lifecycle:
  - A sync session-scoped fixture creates/drops tables once per run via
    asyncio.run(), avoiding event-loop conflicts with pytest-asyncio 0.24+.
  - function-scoped db_session creates its own engine per test so that
    every async test runs with an asyncpg pool bound to its own event loop.
  - TRUNCATE after every test so each test starts with a clean slate.
"""
from __future__ import annotations

import os
import asyncio
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    create_async_engine,
    async_sessionmaker,
)

# ── Override env vars BEFORE importing any app modules ────────────────────────
os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://hsk:hsk_dev_password@localhost:5432/hsk_claims_test")
os.environ.setdefault("DATABASE_URL_SYNC", "postgresql+psycopg://hsk:hsk_dev_password@localhost:5432/hsk_claims_test")
os.environ.setdefault("SECRET_KEY", "test_secret_key_for_testing_only_32b")
os.environ["ENVIRONMENT"] = "test"
os.environ["LOG_LEVEL"] = "WARNING"
os.environ.setdefault("UPLOAD_DIR", "/tmp/hsk_test_uploads")

# ── Import app after env override ─────────────────────────────────────────────
from app.config import get_settings
from app.database import Base, get_db
from app.main import app

get_settings.cache_clear()
settings = get_settings()

# ── Path to the real Excel file ───────────────────────────────────────────────
REAL_EXCEL_PATH = os.environ.get(
    "HSK_EXCEL_PATH",
    os.path.normpath(
        os.path.join(os.path.dirname(__file__), "..", "..", "..",
                     "HSK - CASHLESS CLAIMS TRACKER-FINALIZE.xlsx")
    ),
)

# Tables to truncate between tests (order matters for FK constraints)
_TRUNCATE_TABLES = [
    "chat_messages", "chat_sessions",
    "query_denials", "claims",
    "excel_sync_log", "lookups",
    "users", "hospitals",
]


# ── Schema setup: sync + session-scoped (avoids cross-loop issues) ────────────
@pytest.fixture(scope="session", autouse=True)
def _create_test_schema():
    """Drop and recreate all tables once per pytest session."""

    async def _setup():
        engine = create_async_engine(settings.database_url, echo=False)
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            await conn.run_sync(Base.metadata.create_all)
        await engine.dispose()

    async def _teardown():
        engine = create_async_engine(settings.database_url, echo=False)
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        await engine.dispose()

    asyncio.run(_setup())
    yield
    asyncio.run(_teardown())


# ── Per-test DB session ───────────────────────────────────────────────────────
@pytest_asyncio.fixture()
async def db_session(_create_test_schema) -> AsyncGenerator[AsyncSession, None]:
    """
    Create a fresh engine + session for each test.

    A per-test engine is bound to the test function's event loop, which
    prevents the 'Future attached to a different loop' error that occurs
    when a session-scoped asyncpg engine is reused across pytest-asyncio
    0.24+ function-scoped tests.

    Tables are truncated in the finally block so the next test starts clean.
    """
    engine = create_async_engine(settings.database_url, echo=False)
    Session = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
        autocommit=False,
    )
    async with Session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            async with engine.begin() as conn:
                for table in _TRUNCATE_TABLES:
                    await conn.execute(
                        text(f'TRUNCATE TABLE "{table}" RESTART IDENTITY CASCADE')
                    )
    await engine.dispose()


# ── HTTP client wired to the test DB session ──────────────────────────────────
@pytest_asyncio.fixture()
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """
    Async HTTP client pointing at the FastAPI app.
    DB dependency is overridden so API calls use the same test session.
    """
    async def _override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac
    app.dependency_overrides.clear()


# ── Excel file fixtures ───────────────────────────────────────────────────────
@pytest.fixture(scope="session")
def excel_path() -> str:
    path = REAL_EXCEL_PATH
    if not os.path.exists(path):
        pytest.skip(
            f"Real Excel file not found at {path!r}. "
            "Set HSK_EXCEL_PATH env var to the workbook location."
        )
    return path


@pytest.fixture(scope="session")
def excel_bytes(excel_path: str) -> bytes:
    with open(excel_path, "rb") as fh:
        return fh.read()


@pytest.fixture(scope="session")
def parsed_workbook(excel_bytes):
    import io
    from app.sync.excel_parser import parse_workbook
    return parse_workbook(io.BytesIO(excel_bytes))
