"""
FastAPI application entrypoint — Phase 2.
"""
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.api.v1 import sync as sync_router
from app.api.v1 import auth as auth_router
from app.api.v1 import claims as claims_router
from app.api.v1 import analytics as analytics_router
from app.api.v1 import users as users_router
from app.api.v1 import chat as chat_router
from app.api.v1 import hospitals as hospitals_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(name)s — %(message)s",
)

settings = get_settings()

app = FastAPI(
    title="HSK Claims Dashboard API",
    version="0.2.0",
    description="Hospital Cashless Claims Tracker — backend API",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

# ── CORS ──────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.environment in ("development", "test") else [],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(sync_router.router, prefix="/api/v1")
app.include_router(auth_router.router, prefix="/api/v1")
app.include_router(claims_router.router, prefix="/api/v1")
app.include_router(analytics_router.router, prefix="/api/v1")
app.include_router(users_router.router, prefix="/api/v1")
app.include_router(chat_router.router, prefix="/api/v1")
app.include_router(hospitals_router.router, prefix="/api/v1")


@app.get("/api/health", tags=["health"])
async def health_check():
    return {"status": "ok", "version": app.version, "environment": settings.environment}
