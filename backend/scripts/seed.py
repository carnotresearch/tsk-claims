"""
Seed script — import the real Excel file into the database.

Usage (from backend/ directory with venv active):
    python scripts/seed.py --file /path/to/HSK\ -\ CASHLESS\ CLAIMS\ TRACKER-FINALIZE.xlsx

Or inside Docker:
    docker compose exec backend python scripts/seed.py --file /app/uploads/latest.xlsx
"""
import asyncio
import argparse
import logging
import sys
import os

# Make sure app package is importable when running from scripts/
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.ext.asyncio import AsyncSession
from app.database import AsyncSessionLocal, engine, Base
from app.sync.pipeline import run_sync
from app.sync.sources.local_file import LocalFileSource

logging.basicConfig(level=logging.INFO, format="%(levelname)s — %(message)s")
logger = logging.getLogger(__name__)


async def create_tables() -> None:
    """Create all tables if they don't exist (dev convenience; use Alembic in prod)."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Tables ensured.")


async def seed(excel_path: str) -> None:
    await create_tables()

    source = LocalFileSource(path=excel_path)
    async with AsyncSessionLocal() as db:
        result = await run_sync(db, source, triggered_by="seed_script")
        await db.commit()

    print("\n─── Seed Result ───────────────────────────────")
    print(f"  Status         : {result.status}")
    print(f"  Source         : {result.source_path}")
    print(f"  Rows processed : {result.rows_processed}")
    print(f"  Inserted       : {result.rows_inserted}")
    print(f"  Updated        : {result.rows_updated}")
    print(f"  Skipped        : {result.rows_skipped}")
    print(f"  Errored        : {result.rows_errored}")
    if result.errors:
        print(f"  Errors         :")
        for err in result.errors:
            print(f"    • {err}")
    print("───────────────────────────────────────────────\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed database from HSK Excel file")
    parser.add_argument(
        "--file",
        required=True,
        help="Path to the Excel workbook (.xlsx)",
    )
    args = parser.parse_args()

    if not os.path.exists(args.file):
        logger.error("File not found: %s", args.file)
        sys.exit(1)

    asyncio.run(seed(args.file))


if __name__ == "__main__":
    main()
