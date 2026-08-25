from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel


class ClaimSummary(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    hospital_id: int
    hsk_ref_id: str | None
    month_label: str | None
    patient_name: str | None
    date_admission: date | None
    date_discharge: date | None
    los_days: int | None
    payer_type: str | None
    insurer_name: str | None
    final_claimed_amt: Decimal | None
    final_bill_approved_amt: Decimal | None
    payment_received_amt: Decimal | None
    outstanding_amt: Decimal | None
    ageing_bucket: str | None
    final_claim_status: str | None


class ClaimDetail(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    hospital_id: int
    hsk_ref_id: str | None
    month_label: str | None
    ihx_ref_id: str | None
    uhid: str | None
    ip_number: str | None

    patient_name: str | None
    patient_contact: str | None
    insured_name: str | None
    employee_code: str | None
    corporate_name: str | None

    date_admission: date | None
    date_discharge: date | None
    los_days: int | None
    procedure_name: str | None
    diagnosis: str | None

    payer_type: str | None
    tpa_name: str | None
    insurer_name: str | None
    policy_no: str | None
    policy_type: str | None

    preauth_no: str | None
    preauth_request_date: date | None
    preauth_approval_date: date | None
    preauth_requested_amt: Decimal | None
    preauth_approved_amt: Decimal | None
    preauth_copay: Decimal | None
    preauth_status: str | None
    preauth_tat: int | None

    final_bill_request_date: date | None
    final_bill_approval_date: date | None
    final_claimed_amt: Decimal | None
    final_bill_approved_amt: Decimal | None
    hospital_discount: Decimal | None
    patient_paid_amt: Decimal | None
    discharge_status: str | None
    discharge_tat: int | None

    submission_type: str | None
    submission_date: date | None
    submission_tat: int | None
    submission_status: str | None

    query_raised: bool | None
    query_raised_date: date | None
    query_reason: str | None
    query_response_date: date | None
    query_resolution_tat: int | None

    settlement_date: date | None
    settled_amt: Decimal | None
    tds_amt: Decimal | None
    deduction_amt: Decimal | None
    utr_no: str | None
    payment_received_date: date | None
    payment_received_amt: Decimal | None
    payment_mode: str | None
    payment_tat: int | None

    outstanding_amt: Decimal | None
    ageing_days: int | None
    ageing_bucket: str | None

    final_claim_status: str | None
    denial_reason: str | None
    insurer_comments: str | None
    hospital_remarks: str | None

    created_at: datetime
    updated_at: datetime


class ClaimListResponse(BaseModel):
    items: list[ClaimSummary]
    total: int
    page: int
    page_size: int
    pages: int
