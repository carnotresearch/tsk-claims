from __future__ import annotations

from decimal import Decimal

from pydantic import BaseModel


class KPIs(BaseModel):
    total_claims: int
    total_billed: Decimal
    total_approved: Decimal
    total_paid: Decimal
    total_outstanding: Decimal
    total_settled: Decimal
    total_tds: Decimal
    approval_rate: float  # percentage 0–100


class TATStats(BaseModel):
    preauth_avg_days: float | None
    discharge_avg_days: float | None
    submission_avg_days: float | None
    payment_avg_days: float | None
    query_resolution_avg_days: float | None


class AgeingBucket(BaseModel):
    bucket: str
    claim_count: int
    outstanding_amt: Decimal


class PayerPerformance(BaseModel):
    payer_type: str
    claim_count: int
    total_billed: Decimal
    total_approved: Decimal
    total_paid: Decimal
    approval_rate: float


class MonthlyTrend(BaseModel):
    month: str
    claim_count: int
    total_billed: Decimal
    total_approved: Decimal
    total_paid: Decimal


class StatusBreakdown(BaseModel):
    status: str
    count: int
