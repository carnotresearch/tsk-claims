from __future__ import annotations

from decimal import Decimal
from pydantic import BaseModel


class KPIs(BaseModel):
    total_claims: int
    total_billed: Decimal
    total_approved: Decimal
    total_settled: Decimal
    total_paid: Decimal
    total_outstanding: Decimal
    total_deductions: Decimal
    total_tds: Decimal
    approval_rate: float     # percentage 0–100 (Approved / Billed)
    collection_rate: float   # percentage 0–100 (Paid / Approved)


class TATStats(BaseModel):
    preauth_avg_days: float | None
    discharge_avg_days: float | None
    submission_avg_days: float | None
    payment_avg_days: float | None
    query_resolution_avg_days: float | None


class OperationalTATRow(BaseModel):
    metric: str
    stage: str
    average: float
    fastest: float
    slowest: float
    target: float
    status: str             # "On Target" | "Above Target"


class AgeingBucket(BaseModel):
    bucket: str
    claim_count: int
    outstanding_amt: Decimal


class AgeingByPayerRow(BaseModel):
    payer_type: str
    bucket_0_30: Decimal
    bucket_31_60: Decimal
    bucket_61_90: Decimal
    bucket_90_plus: Decimal
    total_outstanding: Decimal


class DisallowanceReasonRow(BaseModel):
    reason: str
    cases_count: int
    disallowed_amt: Decimal


class StatusSnapshotItem(BaseModel):
    status: str
    count: int


class StatusSnapshotResponse(BaseModel):
    preauth_statuses: list[StatusSnapshotItem]
    discharge_statuses: list[StatusSnapshotItem]
    submission_statuses: list[StatusSnapshotItem]


class PayerPerformance(BaseModel):
    payer_type: str
    claim_count: int
    total_billed: Decimal
    total_approved: Decimal
    total_settled: Decimal
    total_paid: Decimal
    total_outstanding: Decimal
    approval_rate: float      # Approved / Billed %
    deduction_rate: float     # Deductions / Billed %
    collection_rate: float    # Paid / Approved %


class MonthlyTrend(BaseModel):
    month: str
    claim_count: int
    total_billed: Decimal
    total_approved: Decimal
    total_paid: Decimal


class MonthlyDetailedStats(BaseModel):
    month: str
    claim_count: int
    total_billed: Decimal
    total_approved: Decimal
    total_paid: Decimal
    total_tds: Decimal
    total_outstanding: Decimal
    patient_paid: Decimal
    approval_rate: float
    paid_rate: float
    net_collected_rate: float
    tds_rate: float
    variance: Decimal


class StatusBreakdown(BaseModel):
    status: str
    count: int
