# HSK Cashless Claims Dashboard

A full-stack web application for managing hospital cashless insurance claims. Replaces a manual Excel-based workflow with a live, multi-user, role-scoped dashboard featuring AI-powered natural language querying.

---

## Table of Contents

- [Architecture](#architecture)
- [Project Structure](#project-structure)
- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Environment Variables](#environment-variables)
- [Database & Migrations](#database--migrations)
- [Seeding Data](#seeding-data)
- [API Reference](#api-reference)
- [Excel Sync Pipeline](#excel-sync-pipeline)
- [AI Chat (Text-to-SQL)](#ai-chat-text-to-sql)
- [Role-Based Access Control](#role-based-access-control)
- [Running Tests](#running-tests)
- [Development Workflow](#development-workflow)

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Browser                              │
└───────────────────────┬─────────────────────────────────────┘
                        │ HTTP :80
                        ▼
┌─────────────────────────────────────────────────────────────┐
│                    nginx (reverse proxy)                     │
│  /api/*  ──► backend:8000   │   /*  ──► frontend:80/5173   │
└───────────┬─────────────────────────────────────────────────┘
            │                               │
            ▼                               ▼
┌───────────────────────┐     ┌─────────────────────────────┐
│   FastAPI (backend)   │     │    React + Vite (frontend)  │
│   Python 3.12         │     │    TypeScript + Tailwind     │
│   SQLAlchemy 2 async  │     │    Recharts + TanStack Query │
│   asyncpg + alembic   │     └─────────────────────────────┘
└───────────┬───────────┘
            │
            ▼
┌───────────────────────┐     ┌─────────────────────────────┐
│   PostgreSQL 16        │     │    Google Gemini API        │
│   (pgdata volume)      │     │    (text-to-SQL for chat)   │
└───────────────────────┘     └─────────────────────────────┘
```

**Services (Docker Compose):**

| Service    | Image / Build         | Port   | Purpose                              |
|------------|-----------------------|--------|--------------------------------------|
| `db`       | postgres:16-alpine    | 5432   | Primary database                     |
| `backend`  | ./backend (Python)    | 8000   | FastAPI REST API                     |
| `frontend` | node:20-alpine        | 5173   | Vite dev server (React SPA)          |
| `nginx`    | nginx:1.27-alpine     | 80     | Reverse proxy (API + frontend)       |

---

## Project Structure

```
hsk-claims/
├── docker-compose.yml
├── .env                          # local secrets (never commit)
├── .env.example                  # template
├── nginx/
│   └── nginx.conf                # reverse proxy config
├── frontend/                     # React + TypeScript SPA
│   ├── Dockerfile                # multi-stage prod build
│   ├── vite.config.ts
│   └── src/
│       ├── api/                  # typed axios wrappers per domain
│       ├── components/           # layout + UI primitives
│       ├── pages/                # Login, Dashboard, Claims, Chat, Users, Sync
│       ├── store/auth.ts         # Zustand persisted auth store
│       ├── types/index.ts        # shared TypeScript interfaces
│       └── lib/format.ts         # INR currency / date formatters
└── backend/                      # FastAPI Python application
    ├── Dockerfile
    ├── requirements.txt
    ├── requirements-test.txt
    ├── pytest.ini
    ├── alembic/                  # database migrations
    │   └── versions/
    │       ├── 001_initial_schema.py
    │       └── 002_chat_message_result_rows_jsonb.py
    ├── scripts/
    │   ├── seed.py               # seed claims from Excel file
    │   └── seed_admin.py         # create initial admin user
    └── app/
        ├── main.py               # FastAPI app + router registration
        ├── config.py             # pydantic-settings (env vars)
        ├── database.py           # async engine + get_db dependency
        ├── core/
        │   ├── security.py       # JWT encode/decode, bcrypt
        │   └── deps.py           # get_current_user, require_admin, hospital_scope
        ├── models/               # SQLAlchemy ORM models
        │   ├── hospital.py
        │   ├── user.py
        │   ├── claim.py          # 80-column claims table
        │   ├── query_denial.py
        │   ├── lookup.py
        │   ├── sync_log.py
        │   └── chat.py
        ├── schemas/              # Pydantic request/response models
        ├── api/v1/               # route handlers
        │   ├── auth.py           # POST /login, POST /refresh, GET /me
        │   ├── claims.py         # GET /claims, GET /claims/{id}
        │   ├── analytics.py      # KPIs, TAT, ageing, payer perf, monthly
        │   ├── users.py          # admin CRUD for users
        │   ├── chat.py           # chat sessions + messages
        │   └── sync.py           # Excel upload + sync logs
        ├── services/
        │   ├── chat_service.py   # LLM → SQL → execute → persist
        │   └── llm/
        │       ├── base.py       # abstract LLMProvider
        │       └── gemini.py     # Google Gemini implementation
        └── sync/
            ├── base.py           # ExcelSource ABC + SyncResult
            ├── excel_parser.py   # openpyxl parser, all computed fields
            ├── upsert.py         # upsert logic (MD5 hash change detection)
            ├── pipeline.py       # run_sync orchestrator
            └── sources/
                ├── upload.py     # from uploaded bytes
                ├── local_file.py # from filesystem path
                ├── google_drive.py  # stub (future)
                └── network_share.py # stub (future)
```

---

## Prerequisites

- **Docker** 24+ and **Docker Compose** v2
- **Google Gemini API key** (for AI chat feature — get one free at [aistudio.google.com](https://aistudio.google.com))
- The Excel source file: `HSK - CASHLESS CLAIMS TRACKER-FINALIZE.xlsx`

---

## Quick Start

### 1. Clone and configure

```bash
git clone <repo-url>
cd hsk-claims
cp .env.example .env
```

Edit `.env` and fill in the required values:

```bash
POSTGRES_PASSWORD=your_strong_db_password
SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")
GEMINI_API_KEY=AIza...          # from Google AI Studio
ADMIN_PASSWORD=your_admin_pass
```

### 2. Start all services

```bash
docker compose up -d
```

Wait ~15 seconds for the frontend Vite dev server to boot, then open:

- **Dashboard:** http://localhost
- **API docs:** http://localhost/api/docs

### 3. Run database migrations

```bash
docker compose exec backend alembic upgrade head
```

### 4. Create the admin user

```bash
docker compose exec backend python scripts/seed_admin.py
```

### 5. (Optional) Seed claims from Excel

```bash
# Copy the Excel file into the container and seed
docker compose cp "HSK - CASHLESS CLAIMS TRACKER-FINALIZE.xlsx" backend:/tmp/tracker.xlsx
docker compose exec backend python scripts/seed.py --file /tmp/tracker.xlsx
```

### 6. Log in

Open http://localhost and sign in with the admin credentials set in `.env`.

---

## Environment Variables

All variables are loaded from the `.env` file at the project root.

| Variable             | Required | Default                  | Description                                      |
|----------------------|----------|--------------------------|--------------------------------------------------|
| `POSTGRES_DB`        | No       | `hsk_claims`             | Database name                                    |
| `POSTGRES_USER`      | No       | `hsk`                    | Database user                                    |
| `POSTGRES_PASSWORD`  | **Yes**  | —                        | Database password                                |
| `SECRET_KEY`         | **Yes**  | —                        | JWT signing key (32+ random bytes)               |
| `GEMINI_API_KEY`     | No       | `""`                     | Google Gemini API key (required for chat)        |
| `GEMINI_MODEL`       | No       | `gemini-1.5-flash`       | Gemini model to use                              |
| `LLM_PROVIDER`       | No       | `gemini`                 | LLM backend: `gemini` (extensible)               |
| `SYNC_SOURCE`        | No       | `upload`                 | `upload` \| `local_file` \| `google_drive`       |
| `EXCEL_FILE_PATH`    | No       | `/app/uploads/latest.xlsx` | Path when `SYNC_SOURCE=local_file`             |
| `ADMIN_EMAIL`        | No       | `admin@hsk.local`        | Seed admin email                                 |
| `ADMIN_PASSWORD`     | No       | `changeme`               | Seed admin password                              |
| `LOG_LEVEL`          | No       | `INFO`                   | Python log level                                 |
| `ENVIRONMENT`        | No       | `development`            | `development` \| `production`                    |

---

## Database & Migrations

The project uses **Alembic** for schema migrations with a synchronous `psycopg` driver (separate from the async `asyncpg` runtime driver).

```bash
# Apply all pending migrations
docker compose exec backend alembic upgrade head

# Check current revision
docker compose exec backend alembic current

# Create a new migration (after changing models)
docker compose exec backend alembic revision --autogenerate -m "describe the change"

# Rollback one revision
docker compose exec backend alembic downgrade -1
```

### Schema overview

| Table              | Purpose                                              |
|--------------------|------------------------------------------------------|
| `hospitals`        | Hospital master (name, location, rohini_id)          |
| `users`            | Auth users with role and optional hospital scope     |
| `claims`           | 80-column claims table (all raw + computed fields)   |
| `query_denials`    | Per-claim query/denial detail rows                   |
| `lookups`          | Reference data (payer types, statuses, etc.)         |
| `excel_sync_log`   | Audit trail for every sync run                       |
| `chat_sessions`    | Named AI chat threads per user                       |
| `chat_messages`    | Individual messages with generated SQL + results     |

---

## Seeding Data

### Admin user

```bash
docker compose exec backend python scripts/seed_admin.py
```

Reads `ADMIN_EMAIL`, `ADMIN_PASSWORD`, `ADMIN_FULL_NAME` from environment. Skips if the email already exists.

### Claims from Excel

```bash
docker compose exec backend python scripts/seed.py --file /path/to/workbook.xlsx
```

Or via the web UI: go to **Sync** page and drag-and-drop the `.xlsx` file.

---

## API Reference

Interactive docs are available at **http://localhost/api/docs** (Swagger UI).

### Auth

| Method | Endpoint               | Description                              |
|--------|------------------------|------------------------------------------|
| POST   | `/api/v1/auth/login`   | Login (form: `username`, `password`) → tokens |
| POST   | `/api/v1/auth/refresh` | Refresh access token                     |
| GET    | `/api/v1/auth/me`      | Current user info                        |

### Claims

| Method | Endpoint               | Description                                         |
|--------|------------------------|-----------------------------------------------------|
| GET    | `/api/v1/claims`       | Paginated list (filters: status, payer, date, search) |
| GET    | `/api/v1/claims/{id}`  | Full claim detail (80 fields)                       |

### Analytics

| Method | Endpoint                             | Description                      |
|--------|--------------------------------------|----------------------------------|
| GET    | `/api/v1/analytics/kpis`             | Headline KPIs                    |
| GET    | `/api/v1/analytics/tat`              | Average turnaround times         |
| GET    | `/api/v1/analytics/ageing`           | Outstanding ageing buckets       |
| GET    | `/api/v1/analytics/payer-performance`| Per-payer claims/amounts         |
| GET    | `/api/v1/analytics/monthly`          | Month-wise trend                 |
| GET    | `/api/v1/analytics/status-breakdown` | Claims by final status           |

All analytics endpoints accept an optional `?hospital_id=` query parameter (admin only). Hospital users are automatically scoped to their hospital.

### Users (admin only)

| Method | Endpoint               | Description              |
|--------|------------------------|--------------------------|
| GET    | `/api/v1/users`        | List all users           |
| POST   | `/api/v1/users`        | Create user              |
| GET    | `/api/v1/users/{id}`   | Get user                 |
| PATCH  | `/api/v1/users/{id}`   | Update user              |
| DELETE | `/api/v1/users/{id}`   | Deactivate user          |

### Chat

| Method | Endpoint                                   | Description                         |
|--------|--------------------------------------------|-------------------------------------|
| POST   | `/api/v1/chat/sessions`                    | Create chat session                 |
| GET    | `/api/v1/chat/sessions`                    | List user's sessions                |
| GET    | `/api/v1/chat/sessions/{id}/messages`      | Message history                     |
| POST   | `/api/v1/chat/sessions/{id}/messages`      | Send message → SQL → results        |

### Sync

| Method | Endpoint               | Description                              |
|--------|------------------------|------------------------------------------|
| POST   | `/api/v1/sync/upload`  | Upload `.xlsx`/`.xlsm` → sync pipeline  |
| GET    | `/api/v1/sync/logs`    | Recent sync log entries                  |

---

## Excel Sync Pipeline

The sync pipeline is built around a swappable **source abstraction**, making it easy to add new data sources without touching business logic.

```
ExcelSource (abstract)
  ├── UploadSource       — bytes from HTTP multipart upload
  ├── LocalFileSource    — reads from container filesystem path
  ├── GoogleDriveSource  — stub (implement with google-api-python-client)
  └── NetworkShareSource — stub (implement with smb/cifs mounting)
```

**Flow for each sync run:**

```
Source.get_file()
    └──► excel_parser.parse_workbook()     # openpyxl, data_only=True
             └──► upsert.upsert_workbook() # MD5 hash change detection
                      └──► ExcelSyncLog    # audit trail
                      └──► SyncResult      # returned to caller
```

**Change detection:** Every row is fingerprinted with an MD5 hash of its raw values. On re-import, rows with unchanged hashes are skipped — only changed or new rows are written.

**Computed fields** (recalculated server-side, never read from Excel formulas):
- `los_days` — discharge − admission date
- `preauth_tat`, `discharge_tat`, `submission_tat`, `payment_tat`, `query_resolution_tat`
- `deduction_amt`, `outstanding_amt`
- `ageing_days`, `ageing_bucket` (0-30 / 31-60 / 61-90 / 90+)
- `month_label` (e.g. "Apr-26")

### Adding a new sync source

1. Create `backend/app/sync/sources/my_source.py` extending `ExcelSource`
2. Implement `get_file()`, `source_type()`, `source_path()`
3. Add a new branch in `LLM_PROVIDER`-style factory (or wire it into the scheduler)

---

## AI Chat (Text-to-SQL)

The chat feature converts natural language questions into PostgreSQL `SELECT` statements using a pluggable LLM backend.

**How it works:**

1. User types a question (e.g. "Which insurer has the highest approval rate?")
2. Gemini receives the DB schema as a system prompt + conversation history
3. Gemini returns a `SELECT` statement
4. The backend validates it (must start with `SELECT`), then executes it
5. Results (up to 500 rows) are returned alongside the generated SQL
6. The frontend renders the SQL in a collapsible block and the results as a table

**Hospital scoping in chat:** The system prompt automatically includes `WHERE hospital_id = X` instructions for hospital users, so they cannot accidentally query other hospitals' data.

**Swapping the LLM provider:**

The `LLMProvider` abstract base class (`app/services/llm/base.py`) defines a single method:

```python
async def generate_sql(system_prompt, conversation, user_message) -> str
```

To add a new provider:

1. Create `app/services/llm/openai.py` implementing `LLMProvider`
2. Add a branch to `app/services/llm/__init__.py`
3. Set `LLM_PROVIDER=openai` in `.env`

---

## Role-Based Access Control

| Role             | Claims   | Analytics | Users    | Chat              |
|------------------|----------|-----------|----------|-------------------|
| `admin`          | All      | All       | CRUD     | All hospitals     |
| `hospital_user`  | Own only | Own only  | Denied   | Own hospital only |

- **Admins** can optionally filter by `?hospital_id=` on analytics endpoints
- **Hospital users** are automatically filtered — the `hospital_scope` FastAPI dependency injects the restriction transparently
- All protected endpoints require a valid JWT access token (`Authorization: Bearer <token>`)
- Tokens expire after 30 minutes; use `POST /api/v1/auth/refresh` with the refresh token (7-day expiry) to get a new pair

---

## Running Tests

Tests run against a dedicated `hsk_claims_test` PostgreSQL database.

```bash
# Run the full test suite inside Docker (recommended)
docker compose run --rm \
  -e DATABASE_URL="postgresql+asyncpg://hsk:hsk_dev_password@db:5432/hsk_claims_test" \
  -e DATABASE_URL_SYNC="postgresql+psycopg://hsk:hsk_dev_password@db:5432/hsk_claims_test" \
  -e HSK_EXCEL_PATH="/tmp/tracker.xlsx" \
  -v "/path/to/HSK - CASHLESS CLAIMS TRACKER-FINALIZE.xlsx:/tmp/tracker.xlsx:ro" \
  backend bash -c "pip install -r requirements-test.txt && pytest"
```

**Test structure:**

```
tests/
├── conftest.py              # session fixtures: schema setup, db_session, client
├── unit/
│   ├── test_computed_fields.py   # pure unit tests for parser helpers
│   └── test_excel_parser.py      # parser against the real Excel file
├── integration/
│   ├── test_upsert.py            # DB upsert logic
│   └── test_pipeline.py          # full run_sync pipeline
└── api/
    ├── test_health.py            # GET /api/health
    └── test_sync.py              # POST /sync/upload, GET /sync/logs
```

**Markers:**

| Marker        | Requires           |
|---------------|--------------------|
| `unit`        | Nothing (pure)     |
| `integration` | Running PostgreSQL  |
| `api`         | Full FastAPI + DB   |

```bash
# Run only unit tests (no DB needed)
pytest -m unit

# Run with coverage report
pytest --cov=app --cov-report=html
```

---

## Development Workflow

### Backend (FastAPI with hot reload)

The backend container mounts `./backend` as `/app` and runs `uvicorn --reload`, so code changes are reflected immediately.

```bash
# View backend logs
docker compose logs -f backend

# Run a one-off management command
docker compose exec backend python scripts/seed_admin.py

# Open a Python shell with app context
docker compose exec backend python -c "from app.config import get_settings; print(get_settings())"
```

### Frontend (Vite HMR)

The frontend container mounts `./frontend` as `/app` with a named volume for `node_modules`. Vite's Hot Module Replacement means UI changes appear instantly in the browser.

```bash
# View frontend logs
docker compose logs -f frontend

# Install a new npm package
docker compose exec frontend npm install <package>
```

### Database access

```bash
# psql shell
docker compose exec db psql -U hsk -d hsk_claims

# Quick query
docker compose exec db psql -U hsk -d hsk_claims -c "SELECT COUNT(*) FROM claims;"
```

### Production build (frontend)

```bash
cd frontend
npm run build          # outputs to dist/
# The Dockerfile multi-stage build does this automatically for prod deployments
```
