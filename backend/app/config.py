from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── App ───────────────────────────────────────────────────
    environment: str = "development"
    log_level: str = "INFO"

    # ── Database ──────────────────────────────────────────────
    database_url: str
    database_url_sync: str

    # ── Auth ──────────────────────────────────────────────────
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    # ── LLM (modular — swap provider via LLM_PROVIDER env var) ───────────────
    llm_provider: str = "gemini"          # gemini | openai | anthropic
    gemini_api_key: str = ""
    gemini_model: str = "gemini-1.5-flash"

    # ── Sync pipeline ─────────────────────────────────────────
    sync_source: str = "upload"
    excel_file_path: str = "/app/uploads/latest.xlsx"
    sync_schedule: str = "0 */6 * * *"

    # ── Upload storage ────────────────────────────────────────
    upload_dir: str = "/app/uploads"
    max_upload_size_mb: int = 50

    # ── Admin seed ────────────────────────────────────────────
    admin_email: str = "admin@hsk.local"
    admin_password: str = "changeme"
    admin_full_name: str = "HSK Admin"


@lru_cache
def get_settings() -> Settings:
    return Settings()
