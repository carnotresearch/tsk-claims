"""
Analytics endpoints (all hospital-scoped):
  GET /api/v1/analytics/kpis
  GET /api/v1/analytics/tat
  GET /api/v1/analytics/tat-detailed
  GET /api/v1/analytics/ageing
  GET /api/v1/analytics/ageing-by-payer
  GET /api/v1/analytics/top-disallowances
  GET /api/v1/analytics/status-snapshot
  GET /api/v1/analytics/payer-performance
  GET /api/v1/analytics/monthly
  GET /api/v1/analytics/monthly-detailed
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
from app.models.query_denial import QueryDenial
from app.models.user import User
from app.schemas.analytics import (
    AgeingBucket,
    AgeingByPayerRow,
    DisallowanceReasonRow,
    KPIs,
    MonthlyDetailedStats,
    MonthlyTrend,
    OperationalTATRow,
    PayerPerformance,
    StatusBreakdown,
    StatusSnapshotItem,
    StatusSnapshotResponse,
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


# ── 1. HEADLINE KPIs ──────────────────────────────────────────────────────────

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
        func.coalesce(func.sum(Claim.settled_amt), 0).label("total_settled"),
        func.coalesce(func.sum(Claim.payment_received_amt), 0).label("total_paid"),
        func.coalesce(func.sum(Claim.outstanding_amt), 0).label("total_outstanding"),
        func.coalesce(func.sum(Claim.deduction_amt), 0).label("total_deductions"),
        func.coalesce(func.sum(Claim.tds_amt), 0).label("total_tds"),
    )
    q = _scope_filter(q, scope, hospital_id)
    row = (await db.execute(q)).one()

    billed = Decimal(str(row.total_billed))
    approved = Decimal(str(row.total_approved))
    paid = Decimal(str(row.total_paid))
    settled = Decimal(str(row.total_settled))
    outstanding = Decimal(str(row.total_outstanding))
    deductions = Decimal(str(row.total_deductions))
    tds = Decimal(str(row.total_tds))

    apprv_rate = float(approved / billed * 100) if billed else 0.0
    col_rate = float(paid / approved * 100) if approved else 0.0

    return KPIs(
        total_claims=row.total_claims,
        total_billed=billed,
        total_approved=approved,
        total_settled=settled,
        total_paid=paid,
        total_outstanding=outstanding,
        total_deductions=deductions,
        total_tds=tds,
        approval_rate=round(apprv_rate, 2),
        collection_rate=round(col_rate, 2),
    )


# ── 2. OPERATIONAL TAT (Days) ─────────────────────────────────────────────────

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


@router.get("/tat-detailed", response_model=list[OperationalTATRow])
async def tat_detailed(
    hospital_id: int | None = Query(None),
    scope: int | None = Depends(hospital_scope),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    q = select(
        func.coalesce(func.avg(Claim.preauth_tat), 0).label("preauth_avg"),
        func.coalesce(func.min(Claim.preauth_tat), 0).label("preauth_min"),
        func.coalesce(func.max(Claim.preauth_tat), 0).label("preauth_max"),

        func.coalesce(func.avg(Claim.discharge_tat), 0).label("discharge_avg"),
        func.coalesce(func.min(Claim.discharge_tat), 0).label("discharge_min"),
        func.coalesce(func.max(Claim.discharge_tat), 0).label("discharge_max"),

        func.coalesce(func.avg(Claim.submission_tat), 0).label("submission_avg"),
        func.coalesce(func.min(Claim.submission_tat), 0).label("submission_min"),
        func.coalesce(func.max(Claim.submission_tat), 0).label("submission_max"),

        func.coalesce(func.avg(Claim.query_resolution_tat), 0).label("query_avg"),
        func.coalesce(func.min(Claim.query_resolution_tat), 0).label("query_min"),
        func.coalesce(func.max(Claim.query_resolution_tat), 0).label("query_max"),

        func.coalesce(func.avg(Claim.payment_tat), 0).label("payment_avg"),
        func.coalesce(func.min(Claim.payment_tat), 0).label("payment_min"),
        func.coalesce(func.max(Claim.payment_tat), 0).label("payment_max"),
    )
    q = _scope_filter(q, scope, hospital_id)
    r = (await db.execute(q)).one()

    def _make_row(metric: str, stage: str, avg_v, min_v, max_v, target: float) -> OperationalTATRow:
        avg_f = round(float(avg_v), 1)
        min_f = round(float(min_v), 1)
        max_f = round(float(max_v), 1)
        status = "Above Target" if avg_f > target else "On Target"
        return OperationalTATRow(
            metric=metric,
            stage=stage,
            average=avg_f,
            fastest=min_f,
            slowest=max_f,
            target=target,
            status=status,
        )

    return [
        _make_row("Preauth TAT", "preauth", r.preauth_avg, r.preauth_min, r.preauth_max, 2.0),
        _make_row("Discharge TAT", "discharge", r.discharge_avg, r.discharge_min, r.discharge_max, 2.0),
        _make_row("Submission TAT", "submission", r.submission_avg, r.submission_min, r.submission_max, 7.0),
        _make_row("Query Resoln.", "query", r.query_avg, r.query_min, r.query_max, 5.0),
        _make_row("Payment TAT", "payment", r.payment_avg, r.payment_min, r.payment_max, 30.0),
    ]


# ── 3. OUTSTANDING AGEING BY PAYER TYPE ───────────────────────────────────────

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


@router.get("/ageing-by-payer", response_model=list[AgeingByPayerRow])
async def ageing_by_payer(
    hospital_id: int | None = Query(None),
    scope: int | None = Depends(hospital_scope),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    q = (
        select(
            Claim.payer_type,
            func.coalesce(func.sum(case((Claim.ageing_bucket == "0-30", Claim.outstanding_amt), else_=0)), 0).label("b_0_30"),
            func.coalesce(func.sum(case((Claim.ageing_bucket == "31-60", Claim.outstanding_amt), else_=0)), 0).label("b_31_60"),
            func.coalesce(func.sum(case((Claim.ageing_bucket == "61-90", Claim.outstanding_amt), else_=0)), 0).label("b_61_90"),
            func.coalesce(func.sum(case((Claim.ageing_bucket == "90+", Claim.outstanding_amt), else_=0)), 0).label("b_90_plus"),
            func.coalesce(func.sum(Claim.outstanding_amt), 0).label("total_outstanding"),
        )
        .where(Claim.payer_type.isnot(None))
        .group_by(Claim.payer_type)
        .order_by(Claim.payer_type)
    )
    q = _scope_filter(q, scope, hospital_id)
    rows = (await db.execute(q)).all()

    STANDARD_PAYERS = ["TPA", "Insurer", "Govt Scheme", "Self-funded"]
    payer_map = {r.payer_type: r for r in rows}

    result = []
    tot_0_30 = Decimal("0")
    tot_31_60 = Decimal("0")
    tot_61_90 = Decimal("0")
    tot_90 = Decimal("0")
    tot_out = Decimal("0")

    for p in STANDARD_PAYERS:
        r = payer_map.get(p)
        b0 = Decimal(str(r.b_0_30)) if r else Decimal("0")
        b31 = Decimal(str(r.b_31_60)) if r else Decimal("0")
        b61 = Decimal(str(r.b_61_90)) if r else Decimal("0")
        b90 = Decimal(str(r.b_90_plus)) if r else Decimal("0")
        total = Decimal(str(r.total_outstanding)) if r else Decimal("0")

        tot_0_30 += b0
        tot_31_60 += b31
        tot_61_90 += b61
        tot_90 += b90
        tot_out += total

        display_name = "Govt. Scheme" if p == "Govt Scheme" else p
        result.append(
            AgeingByPayerRow(
                payer_type=display_name,
                bucket_0_30=b0,
                bucket_31_60=b31,
                bucket_61_90=b61,
                bucket_90_plus=b90,
                total_outstanding=total,
            )
        )

    # Grand total
    result.append(
        AgeingByPayerRow(
            payer_type="GRAND TOTAL",
            bucket_0_30=tot_0_30,
            bucket_31_60=tot_31_60,
            bucket_61_90=tot_61_90,
            bucket_90_plus=tot_90,
            total_outstanding=tot_out,
        )
    )
    return result


# ── 4. TOP DISALLOWANCES ──────────────────────────────────────────────────────

@router.get("/top-disallowances", response_model=list[DisallowanceReasonRow])
async def top_disallowances(
    hospital_id: int | None = Query(None),
    scope: int | None = Depends(hospital_scope),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    # Query from query_denials table first
    q_denials = select(
        QueryDenial.disallowed_reason.label("reason"),
        func.count().label("cases_count"),
        func.coalesce(func.sum(QueryDenial.disallowed_amt), 0).label("disallowed_amt"),
    ).where(QueryDenial.disallowed_reason.isnot(None)).group_by(QueryDenial.disallowed_reason)

    rows = (await db.execute(q_denials)).all()
    reason_map = {r.reason: r for r in rows}

    STANDARD_REASONS = [
        "Non-Medicals",
        "Room Rent Diff",
        "Sub-Limit",
        "Co-Pay",
        "PED Exclusion",
        "Tariff Mismatch",
        "Consumables",
        "Pharmacy Outside",
        "Document Issue",
        "Billing Error",
        "Admission NA",
        "Investigation NA",
        "Others",
    ]

    result = []
    for reason in STANDARD_REASONS:
        # Match against database rows
        match = None
        for k, v in reason_map.items():
            if reason.lower() in k.lower() or k.lower() in reason.lower():
                match = v
                break

        cnt = match.cases_count if match else 0
        amt = Decimal(str(match.disallowed_amt)) if match else Decimal("0")
        result.append(
            DisallowanceReasonRow(
                reason=reason,
                cases_count=cnt,
                disallowed_amt=amt,
            )
        )

    return result


# ── 5. STATUS SNAPSHOT ────────────────────────────────────────────────────────

@router.get("/status-snapshot", response_model=StatusSnapshotResponse)
async def status_snapshot(
    hospital_id: int | None = Query(None),
    scope: int | None = Depends(hospital_scope),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    # Preauth counts
    q_pre = select(Claim.preauth_status, func.count()).where(Claim.preauth_status.isnot(None)).group_by(Claim.preauth_status)
    q_pre = _scope_filter(q_pre, scope, hospital_id)
    pre_rows = {r[0]: r[1] for r in (await db.execute(q_pre)).all()}

    # Discharge counts
    q_dis = select(Claim.discharge_status, func.count()).where(Claim.discharge_status.isnot(None)).group_by(Claim.discharge_status)
    q_dis = _scope_filter(q_dis, scope, hospital_id)
    dis_rows = {r[0]: r[1] for r in (await db.execute(q_dis)).all()}

    # Submission counts
    q_sub = select(Claim.submission_status, func.count()).where(Claim.submission_status.isnot(None)).group_by(Claim.submission_status)
    q_sub = _scope_filter(q_sub, scope, hospital_id)
    sub_rows = {r[0]: r[1] for r in (await db.execute(q_sub)).all()}

    PRE_KEYS = ["Requested", "Preauth Approved", "Partial Approved", "Enhancement", "Query Raised", "Denied", "Not opted"]
    DIS_KEYS = ["Approved", "Partial Approved", "Query Raised", "Denied", "Pending"]
    SUB_KEYS = ["Submitted", "Not Submitted", "Re-submitted", "NA"]

    def _get_val(source_dict, key):
        # 1. Exact match
        if key in source_dict:
            return source_dict[key]
        for k, v in source_dict.items():
            if k.lower().strip() == key.lower().strip():
                return v
        # 2. Specific alias match
        for k, v in source_dict.items():
            k_lower = k.lower().strip()
            key_lower = key.lower().strip()
            if key_lower == "enhancement" and "enhancement" in k_lower:
                return v
            if key_lower == "not opted" and "not opted" in k_lower:
                return v
            if key_lower == "denied" and ("denied" in k_lower or "rejected" in k_lower):
                return v
            if key_lower == "approved" and k_lower == "approved":
                return v
            if key_lower == "submitted" and k_lower == "submitted":
                return v
        return 0

    return StatusSnapshotResponse(
        preauth_statuses=[StatusSnapshotItem(status=k, count=_get_val(pre_rows, k)) for k in PRE_KEYS],
        discharge_statuses=[StatusSnapshotItem(status=k, count=_get_val(dis_rows, k)) for k in DIS_KEYS],
        submission_statuses=[StatusSnapshotItem(status=k, count=_get_val(sub_rows, k)) for k in SUB_KEYS],
    )


# ── 6. PAYER-WISE PERFORMANCE ─────────────────────────────────────────────────

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
            func.coalesce(func.sum(Claim.settled_amt), 0).label("total_settled"),
            func.coalesce(func.sum(Claim.payment_received_amt), 0).label("total_paid"),
            func.coalesce(func.sum(Claim.outstanding_amt), 0).label("total_outstanding"),
            func.coalesce(func.sum(Claim.deduction_amt), 0).label("total_deductions"),
        )
        .where(Claim.payer_type.isnot(None))
        .group_by(Claim.payer_type)
        .order_by(Claim.payer_type)
    )
    q = _scope_filter(q, scope, hospital_id)
    rows = (await db.execute(q)).all()

    STANDARD_PAYERS = ["TPA", "Insurer", "Government", "Self-funded"]
    row_map = {r.payer_type: r for r in rows}

    result = []
    grand_cases = 0
    grand_billed = Decimal("0")
    grand_approved = Decimal("0")
    grand_settled = Decimal("0")
    grand_paid = Decimal("0")
    grand_outstanding = Decimal("0")
    grand_deductions = Decimal("0")

    for p in STANDARD_PAYERS:
        # Match Govt / Government
        r = row_map.get(p)
        if not r and p == "Government":
            r = row_map.get("Govt Scheme") or row_map.get("Govt")

        cnt = r.claim_count if r else 0
        billed = Decimal(str(r.total_billed)) if r else Decimal("0")
        approved = Decimal(str(r.total_approved)) if r else Decimal("0")
        settled = Decimal(str(r.total_settled)) if r else Decimal("0")
        paid = Decimal(str(r.total_paid)) if r else Decimal("0")
        outstanding = Decimal(str(r.total_outstanding)) if r else Decimal("0")
        deductions = Decimal(str(r.total_deductions)) if r else Decimal("0")

        apprv_pct = float(approved / billed * 100) if billed else 0.0
        ded_pct = float(deductions / billed * 100) if billed else 0.0
        col_pct = float(paid / approved * 100) if approved else 0.0

        grand_cases += cnt
        grand_billed += billed
        grand_approved += approved
        grand_settled += settled
        grand_paid += paid
        grand_outstanding += outstanding
        grand_deductions += deductions

        result.append(
            PayerPerformance(
                payer_type=p,
                claim_count=cnt,
                total_billed=billed,
                total_approved=approved,
                total_settled=settled,
                total_paid=paid,
                total_outstanding=outstanding,
                approval_rate=round(apprv_pct, 1),
                deduction_rate=round(ded_pct, 1),
                collection_rate=round(col_pct, 1),
            )
        )

    # Grand total row
    g_apprv_pct = float(grand_approved / grand_billed * 100) if grand_billed else 0.0
    g_ded_pct = float(grand_deductions / grand_billed * 100) if grand_billed else 0.0
    g_col_pct = float(grand_paid / grand_approved * 100) if grand_approved else 0.0

    result.append(
        PayerPerformance(
            payer_type="GRAND TOTAL",
            claim_count=grand_cases,
            total_billed=grand_billed,
            total_approved=grand_approved,
            total_settled=grand_settled,
            total_paid=grand_paid,
            total_outstanding=grand_outstanding,
            approval_rate=round(g_apprv_pct, 1),
            deduction_rate=round(g_ded_pct, 1),
            collection_rate=round(g_col_pct, 1),
        )
    )

    return result


# ── 7. 12-MONTH STATISTICS ────────────────────────────────────────────────────

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


@router.get("/monthly-detailed", response_model=list[MonthlyDetailedStats])
async def monthly_detailed(
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
            func.coalesce(func.sum(Claim.tds_amt), 0).label("total_tds"),
            func.coalesce(func.sum(Claim.outstanding_amt), 0).label("total_outstanding"),
            func.coalesce(func.sum(Claim.patient_paid_amt), 0).label("patient_paid"),
            func.coalesce(func.sum(Claim.deduction_amt), 0).label("total_deductions"),
        )
        .where(Claim.month_label.isnot(None))
        .group_by(Claim.month_label)
        .order_by(Claim.month_label)
    )
    q = _scope_filter(q, scope, hospital_id)
    rows = (await db.execute(q)).all()

    result = []
    for r in rows:
        billed = Decimal(str(r.total_billed))
        approved = Decimal(str(r.total_approved))
        paid = Decimal(str(r.total_paid))
        tds = Decimal(str(r.total_tds))
        outstanding = Decimal(str(r.total_outstanding))
        patient_paid = Decimal(str(r.patient_paid))
        deductions = Decimal(str(r.total_deductions))

        apprv_pct = float(approved / billed * 100) if billed else 0.0
        paid_pct = float(paid / approved * 100) if approved else 0.0
        net_col_pct = float((paid + tds) / approved * 100) if approved else 0.0
        tds_pct = float(tds / approved * 100) if approved else 0.0
        variance = approved - (paid + tds + outstanding)

        result.append(
            MonthlyDetailedStats(
                month=r.month,
                claim_count=r.claim_count,
                total_billed=billed,
                total_approved=approved,
                total_paid=paid,
                total_tds=tds,
                total_outstanding=outstanding,
                patient_paid=patient_paid,
                approval_rate=round(apprv_pct, 1),
                paid_rate=round(paid_pct, 1),
                net_collected_rate=round(net_col_pct, 1),
                tds_rate=round(tds_pct, 1),
                variance=variance,
            )
        )

    return result


# ── STATUS BREAKDOWN ──────────────────────────────────────────────────────────

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
