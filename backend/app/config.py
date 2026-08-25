from functools import lru_cache
from urllib.parse import quote_plus

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
    # Accept individual components (preferred — handles special chars in password)
    # OR full URLs as fallback (DATABASE_URL / DATABASE_URL_SYNC env vars)
    postgres_user: str = "hsk"
    postgres_password: str = ""
    postgres_host: str = "db"
    postgres_port: int = 5432
    postgres_db: str = "hsk_claims"

    # Full URL overrides (used in dev/test where DATABASE_URL is set directly)
    database_url: str = ""
    database_url_sync: str = ""

    @property
    def db_url(self) -> str:
        if self.database_url:
            return self.database_url
        pw = quote_plus(self.postgres_password)
        return f"postgresql+asyncpg://{self.postgres_user}:{pw}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"

    @property
    def db_url_sync(self) -> str:
        if self.database_url_sync:
            return self.database_url_sync
        pw = quote_plus(self.postgres_password)
        return f"postgresql+psycopg://{self.postgres_user}:{pw}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"

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
