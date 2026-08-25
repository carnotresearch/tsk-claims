from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user
from app.database import get_db
from app.models.hospital import Hospital
from app.models.user import User

router = APIRouter(prefix="/hospitals", tags=["hospitals"])


@router.get("", summary="List all hospitals")
async def list_hospitals(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Return id + name for every hospital. Used to populate dropdowns."""
    result = await db.execute(select(Hospital.id, Hospital.name).order_by(Hospital.name))
    rows = result.all()
    return [{"id": row.id, "name": row.name} for row in rows]
