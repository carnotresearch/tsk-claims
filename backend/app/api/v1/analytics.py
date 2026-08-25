"""
Analytics endpoints (all hospital-scoped):
  GET /api/v1/analytics/kpis
  GET /api/v1/analytics/tat
  GET /api/v1/analytics/ageing
  GET /api/v1/analytics/payer-performance
  GET /api/v1/analytics/monthly
  GET /api/v1/analytics/status-breakdown
"""
from __future__ import annotations

from decimal import Decimal

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select, case
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, hospital_scope
from app.database import get_db
from app.models.claim import Claim
from app.models.user import User
from app.schemas.analytics import (
    AgeingBucket,
    KPIs,
    MonthlyTrend,
    PayerPerformance,
    StatusBreakdown,
    TATStats,
)

router = APIRouter(prefix="/analytics", tags=["analytics"])

_ZERO = Decimal("0")


def _scope_filter(q, scope: int | None, hospital_id: int | None = None):
    if scope is not None:
        return q.where(Claim.hospital_id == scope)
    if hospital_id is not None:
        return q.where(Claim.hospital_id == hospital_id)
    return q


# ── KPIs ─────────────────────────────────────────────────────────────────────

@router.get("/kpis", response_model=KPIs)
async def kpis(
    hospital_id: int | None = Query(None),
    scope: int | None = Depends(hospital_scope),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    q = select(
        func.count().label("total_claims"),
        func.coalesce(func.sum(Claim.final_claimed_amt), 0).label("total_billed"),
        func.coalesce(func.sum(Claim.final_bill_approved_amt), 0).label("total_approved"),
        func.coalesce(func.sum(Claim.payment_received_amt), 0).label("total_paid"),
        func.coalesce(func.sum(Claim.outstanding_amt), 0).label("total_outstanding"),
        func.coalesce(func.sum(Claim.settled_amt), 0).label("total_settled"),
        func.coalesce(func.sum(Claim.tds_amt), 0).label("total_tds"),
    )
    q = _scope_filter(q, scope, hospital_id)
    row = (await db.execute(q)).one()

    billed = Decimal(str(row.total_billed))
    approved = Decimal(str(row.total_approved))
    rate = float(approved / billed * 100) if billed else 0.0

    return KPIs(
        total_claims=row.total_claims,
        total_billed=billed,
        total_approved=approved,
        total_paid=Decimal(str(row.total_paid)),
        total_outstanding=Decimal(str(row.total_outstanding)),
        total_settled=Decimal(str(row.total_settled)),
        total_tds=Decimal(str(row.total_tds)),
        approval_rate=round(rate, 2),
    )


# ── TAT ──────────────────────────────────────────────────────────────────────

@router.get("/tat", response_model=TATStats)
async def tat_stats(
    hospital_id: int | None = Query(None),
    scope: int | None = Depends(hospital_scope),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    q = select(
        func.avg(Claim.preauth_tat).label("preauth_avg"),
        func.avg(Claim.discharge_tat).label("discharge_avg"),
        func.avg(Claim.submission_tat).label("submission_avg"),
        func.avg(Claim.payment_tat).label("payment_avg"),
        func.avg(Claim.query_resolution_tat).label("query_avg"),
    )
    q = _scope_filter(q, scope, hospital_id)
    row = (await db.execute(q)).one()

    def _f(v) -> float | None:
        return round(float(v), 1) if v is not None else None

    return TATStats(
        preauth_avg_days=_f(row.preauth_avg),
        discharge_avg_days=_f(row.discharge_avg),
        submission_avg_days=_f(row.submission_avg),
        payment_avg_days=_f(row.payment_avg),
        query_resolution_avg_days=_f(row.query_avg),
    )


# ── Ageing ────────────────────────────────────────────────────────────────────

@router.get("/ageing", response_model=list[AgeingBucket])
async def ageing(
    hospital_id: int | None = Query(None),
    scope: int | None = Depends(hospital_scope),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    q = (
        select(
            Claim.ageing_bucket.label("bucket"),
            func.count().label("claim_count"),
            func.coalesce(func.sum(Claim.outstanding_amt), 0).label("outstanding_amt"),
        )
        .where(Claim.ageing_bucket.isnot(None))
        .group_by(Claim.ageing_bucket)
        .order_by(Claim.ageing_bucket)
    )
    q = _scope_filter(q, scope, hospital_id)
    rows = (await db.execute(q)).all()
    return [
        AgeingBucket(
            bucket=r.bucket,
            claim_count=r.claim_count,
            outstanding_amt=Decimal(str(r.outstanding_amt)),
        )
        for r in rows
    ]


# ── Payer Performance ─────────────────────────────────────────────────────────

@router.get("/payer-performance", response_model=list[PayerPerformance])
async def payer_performance(
    hospital_id: int | None = Query(None),
    scope: int | None = Depends(hospital_scope),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    q = (
        select(
            Claim.payer_type,
            func.count().label("claim_count"),
            func.coalesce(func.sum(Claim.final_claimed_amt), 0).label("total_billed"),
            func.coalesce(func.sum(Claim.final_bill_approved_amt), 0).label("total_approved"),
            func.coalesce(func.sum(Claim.payment_received_amt), 0).label("total_paid"),
        )
        .where(Claim.payer_type.isnot(None))
        .group_by(Claim.payer_type)
        .order_by(func.count().desc())
    )
    q = _scope_filter(q, scope, hospital_id)
    rows = (await db.execute(q)).all()

    result = []
    for r in rows:
        billed = Decimal(str(r.total_billed))
        approved = Decimal(str(r.total_approved))
        rate = float(approved / billed * 100) if billed else 0.0
        result.append(
            PayerPerformance(
                payer_type=r.payer_type,
                claim_count=r.claim_count,
                total_billed=billed,
                total_approved=approved,
                total_paid=Decimal(str(r.total_paid)),
                approval_rate=round(rate, 2),
            )
        )
    return result


# ── Monthly Trend ─────────────────────────────────────────────────────────────

@router.get("/monthly", response_model=list[MonthlyTrend])
async def monthly_trend(
    hospital_id: int | None = Query(None),
    scope: int | None = Depends(hospital_scope),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    q = (
        select(
            Claim.month_label.label("month"),
            func.count().label("claim_count"),
            func.coalesce(func.sum(Claim.final_claimed_amt), 0).label("total_billed"),
            func.coalesce(func.sum(Claim.final_bill_approved_amt), 0).label("total_approved"),
            func.coalesce(func.sum(Claim.payment_received_amt), 0).label("total_paid"),
        )
        .where(Claim.month_label.isnot(None))
        .group_by(Claim.month_label)
        .order_by(Claim.month_label)
    )
    q = _scope_filter(q, scope, hospital_id)
    rows = (await db.execute(q)).all()
    return [
        MonthlyTrend(
            month=r.month,
            claim_count=r.claim_count,
            total_billed=Decimal(str(r.total_billed)),
            total_approved=Decimal(str(r.total_approved)),
            total_paid=Decimal(str(r.total_paid)),
        )
        for r in rows
    ]


# ── Status Breakdown ──────────────────────────────────────────────────────────

@router.get("/status-breakdown", response_model=list[StatusBreakdown])
async def status_breakdown(
    hospital_id: int | None = Query(None),
    scope: int | None = Depends(hospital_scope),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    q = (
        select(
            Claim.final_claim_status.label("status"),
            func.count().label("count"),
        )
        .where(Claim.final_claim_status.isnot(None))
        .group_by(Claim.final_claim_status)
        .order_by(func.count().desc())
    )
    q = _scope_filter(q, scope, hospital_id)
    rows = (await db.execute(q)).all()
    return [StatusBreakdown(status=r.status, count=r.count) for r in rows]
