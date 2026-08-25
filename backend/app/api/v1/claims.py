"""
Claims endpoints:
  GET /api/v1/claims        — paginated list with filters
  GET /api/v1/claims/{id}   — full claim detail

Hospital scoping is enforced automatically: hospital_users only see their hospital.
"""
from __future__ import annotations

import math

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, hospital_scope
from app.database import get_db
from app.models.claim import Claim
from app.models.user import User
from app.schemas.claim import ClaimDetail, ClaimListResponse, ClaimSummary

router = APIRouter(prefix="/claims", tags=["claims"])


def _apply_scope(q, scope: int | None):
    if scope is not None:
        q = q.where(Claim.hospital_id == scope)
    return q


@router.get("", response_model=ClaimListResponse)
async def list_claims(
    # Filters
    hospital_id: int | None = Query(None, description="Admin only: filter by hospital"),
    status_filter: str | None = Query(None, alias="status"),
    preauth_status: str | None = Query(None),
    discharge_status: str | None = Query(None),
    submission_status: str | None = Query(None),
    disallowed_reason: str | None = Query(None),
    has_disallowed: bool | None = Query(None),
    insurer: str | None = Query(None),
    payer_type: str | None = Query(None),
    month_label: str | None = Query(None, description="Month label e.g. Apr-25"),
    has_outstanding: bool | None = Query(None, description="Filter claims with outstanding amount > 0"),
    has_paid: bool | None = Query(None, description="Filter claims with payment received > 0"),
    has_approved: bool | None = Query(None, description="Filter claims with approved amount > 0"),
    has_billed: bool | None = Query(None, description="Filter claims with billed amount > 0"),
    tat_stage: str | None = Query(None, description="Filter claims with valid TAT (preauth|discharge|submission|payment|query)"),
    date_from: str | None = Query(None, description="Admission date from (YYYY-MM-DD)"),
    date_to: str | None = Query(None, description="Admission date to (YYYY-MM-DD)"),
    search: str | None = Query(None, description="Search patient name or HSK ref ID"),
    ageing_bucket: str | None = Query(None),
    # Pagination
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
    # Auth
    current_user: User = Depends(get_current_user),
    scope: int | None = Depends(hospital_scope),
    db: AsyncSession = Depends(get_db),
):
    q = select(Claim)

    # Hospital scoping
    if scope is not None:
        q = q.where(Claim.hospital_id == scope)
    elif hospital_id is not None:
        # Admin filtering by specific hospital
        q = q.where(Claim.hospital_id == hospital_id)

    # Optional filters
    if status_filter:
        q = q.where(
            or_(
                Claim.final_claim_status == status_filter,
                Claim.final_claim_status.ilike(f"%{status_filter}%"),
            )
        )
    if preauth_status:
        q = q.where(
            or_(
                Claim.preauth_status == preauth_status,
                Claim.preauth_status.ilike(f"%{preauth_status}%"),
            )
        )
    if discharge_status:
        q = q.where(
            or_(
                Claim.discharge_status == discharge_status,
                Claim.discharge_status.ilike(f"%{discharge_status}%"),
            )
        )
    if submission_status:
        q = q.where(
            or_(
                Claim.submission_status == submission_status,
                Claim.submission_status.ilike(f"%{submission_status}%"),
            )
        )
    if disallowed_reason:
        q = q.where(Claim.denial_reason.ilike(f"%{disallowed_reason}%"))
    if has_disallowed:
        q = q.where(or_(Claim.disallowed_amt > 0, Claim.deduction_amt > 0))
    if insurer:
        q = q.where(Claim.insurer_name.ilike(f"%{insurer}%"))
    if payer_type:
        if payer_type.lower() in ("govt scheme", "govt", "government"):
            q = q.where(or_(Claim.payer_type == "Govt Scheme", Claim.payer_type.ilike("%govt%")))
        else:
            q = q.where(Claim.payer_type.ilike(f"%{payer_type}%"))
    if month_label:
        q = q.where(Claim.month_label.ilike(f"%{month_label}%"))
    if has_outstanding:
        q = q.where(Claim.outstanding_amt > 0)
    if has_paid:
        q = q.where(Claim.payment_received_amt > 0)
    if has_approved:
        q = q.where(Claim.final_bill_approved_amt > 0)
    if has_billed:
        q = q.where(Claim.final_claimed_amt > 0)
    if tat_stage:
        if tat_stage == "preauth":
            q = q.where(Claim.preauth_tat.isnot(None))
        elif tat_stage == "discharge":
            q = q.where(Claim.discharge_tat.isnot(None))
        elif tat_stage == "submission":
            q = q.where(Claim.submission_tat.isnot(None))
        elif tat_stage == "payment":
            q = q.where(Claim.payment_tat.isnot(None))
        elif tat_stage == "query":
            q = q.where(Claim.query_resolution_tat.isnot(None))
    if date_from:
        q = q.where(Claim.date_admission >= date_from)
    if date_to:
        q = q.where(Claim.date_admission <= date_to)
    if ageing_bucket:
        q = q.where(Claim.ageing_bucket == ageing_bucket)
    if search:
        q = q.where(
            or_(
                Claim.patient_name.ilike(f"%{search}%"),
                Claim.hsk_ref_id.ilike(f"%{search}%"),
            )
        )

    # Count total
    count_q = select(func.count()).select_from(q.subquery())
    total = (await db.execute(count_q)).scalar_one()

    # Paginate
    offset = (page - 1) * page_size
    q = q.order_by(Claim.id.desc()).offset(offset).limit(page_size)
    items = (await db.execute(q)).scalars().all()

    return ClaimListResponse(
        items=[ClaimSummary.model_validate(c) for c in items],
        total=total,
        page=page,
        page_size=page_size,
        pages=math.ceil(total / page_size) if total else 0,
    )


@router.get("/{claim_id}", response_model=ClaimDetail)
async def get_claim(
    claim_id: int,
    scope: int | None = Depends(hospital_scope),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    q = select(Claim).where(Claim.id == claim_id)
    if scope is not None:
        q = q.where(Claim.hospital_id == scope)

    claim = (await db.execute(q)).scalar_one_or_none()
    if claim is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Claim not found")
    return ClaimDetail.model_validate(claim)
