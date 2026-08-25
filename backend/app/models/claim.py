from datetime import datetime, date
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    String, Text, Boolean, Date, DateTime, Numeric, Integer,
    ForeignKey, func, Index
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.hospital import Hospital
    from app.models.query_denial import QueryDenial


class Claim(Base):
    """
    Central claims table — mirrors ClaimsMaster sheet columns.
    All formula-derived fields are recomputed server-side on import.
    """
    __tablename__ = "claims"
    __table_args__ = (
        Index("ix_claims_hospital_status", "hospital_id", "final_claim_status"),
        Index("ix_claims_hospital_admission", "hospital_id", "date_admission"),
        Index("ix_claims_insurer", "insurer_name"),
        Index("ix_claims_payer_type", "payer_type"),
        Index("ix_claims_submission_date", "submission_date"),
        Index("ix_claims_settlement_date", "settlement_date"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    hospital_id: Mapped[int] = mapped_column(ForeignKey("hospitals.id"), nullable=False)

    # ── REFERENCE & IDs ───────────────────────────────────────
    hsk_ref_id: Mapped[str | None] = mapped_column(String(50), unique=True, index=True)
    month_label: Mapped[str | None] = mapped_column(String(20))   # "Apr-26"
    ihx_ref_id: Mapped[str | None] = mapped_column(String(100), index=True)
    uhid: Mapped[str | None] = mapped_column(String(100))
    ip_number: Mapped[str | None] = mapped_column(String(100))

    # ── PATIENT DETAILS ───────────────────────────────────────
    patient_name: Mapped[str | None] = mapped_column(String(255))
    patient_contact: Mapped[str | None] = mapped_column(String(50))
    insured_name: Mapped[str | None] = mapped_column(String(255))
    employee_code: Mapped[str | None] = mapped_column(String(100))
    corporate_name: Mapped[str | None] = mapped_column(String(255))

    # ── ADMISSION & STAY ──────────────────────────────────────
    date_admission: Mapped[date | None] = mapped_column(Date)
    date_discharge: Mapped[date | None] = mapped_column(Date)
    los_days: Mapped[int | None] = mapped_column(Integer)         # computed
    procedure_name: Mapped[str | None] = mapped_column(String(255))
    diagnosis: Mapped[str | None] = mapped_column(Text)

    # ── PAYOR & POLICY ────────────────────────────────────────
    payer_type: Mapped[str | None] = mapped_column(String(100))   # TPA / Insurer / Govt / Self-funded
    tpa_name: Mapped[str | None] = mapped_column(String(255))
    insurer_name: Mapped[str | None] = mapped_column(String(255))
    policy_no: Mapped[str | None] = mapped_column(String(255))
    policy_type: Mapped[str | None] = mapped_column(String(100))  # GMC/GHI / Individual / Top-up

    # ── PREAUTH ───────────────────────────────────────────────
    preauth_no: Mapped[str | None] = mapped_column(String(255))
    initial_claim_no: Mapped[str | None] = mapped_column(String(255))
    preauth_request_date: Mapped[date | None] = mapped_column(Date)
    preauth_approval_date: Mapped[date | None] = mapped_column(Date)
    preauth_requested_amt: Mapped[Decimal | None] = mapped_column(Numeric(14, 2))
    preauth_approved_amt: Mapped[Decimal | None] = mapped_column(Numeric(14, 2))
    preauth_copay: Mapped[Decimal | None] = mapped_column(Numeric(14, 2))
    preauth_status: Mapped[str | None] = mapped_column(String(100))
    preauth_tat: Mapped[int | None] = mapped_column(Integer)      # computed

    # ── DISCHARGE / FINAL BILL ────────────────────────────────
    final_bill_request_date: Mapped[date | None] = mapped_column(Date)
    final_bill_approval_date: Mapped[date | None] = mapped_column(Date)
    final_claimed_amt: Mapped[Decimal | None] = mapped_column(Numeric(14, 2))
    final_bill_approved_amt: Mapped[Decimal | None] = mapped_column(Numeric(14, 2))
    hospital_discount: Mapped[Decimal | None] = mapped_column(Numeric(14, 2))
    patient_paid_amt: Mapped[Decimal | None] = mapped_column(Numeric(14, 2))
    discharge_status: Mapped[str | None] = mapped_column(String(100))
    discharge_tat: Mapped[int | None] = mapped_column(Integer)    # computed

    # ── CLAIM SUBMISSION ──────────────────────────────────────
    submission_type: Mapped[str | None] = mapped_column(String(100))   # Hard Copy / Scan Copy
    submission_date: Mapped[date | None] = mapped_column(Date)
    submission_tat: Mapped[int | None] = mapped_column(Integer)   # computed
    submission_status: Mapped[str | None] = mapped_column(String(100))
    courier_agency: Mapped[str | None] = mapped_column(String(255))
    courier_destination: Mapped[str | None] = mapped_column(String(255))
    courier_dispatch_date: Mapped[date | None] = mapped_column(Date)
    courier_awb: Mapped[str | None] = mapped_column(String(255))
    hospital_invoice_no: Mapped[str | None] = mapped_column(String(100))

    # ── QUERY & DENIAL ────────────────────────────────────────
    query_raised: Mapped[bool | None] = mapped_column(Boolean)
    query_raised_date: Mapped[date | None] = mapped_column(Date)
    query_reason: Mapped[str | None] = mapped_column(Text)
    query_response_date: Mapped[date | None] = mapped_column(Date)
    query_resolution_tat: Mapped[int | None] = mapped_column(Integer)  # computed
    resubmission_date: Mapped[date | None] = mapped_column(Date)
    disallowed_amt: Mapped[Decimal | None] = mapped_column(Numeric(14, 2))
    denial_reason: Mapped[str | None] = mapped_column(Text)
    appeal_filed: Mapped[bool | None] = mapped_column(Boolean)
    appeal_date: Mapped[date | None] = mapped_column(Date)

    # ── SETTLEMENT & PAYMENT ──────────────────────────────────
    settlement_date: Mapped[date | None] = mapped_column(Date)
    settled_amt: Mapped[Decimal | None] = mapped_column(Numeric(14, 2))
    tds_amt: Mapped[Decimal | None] = mapped_column(Numeric(14, 2))
    deduction_amt: Mapped[Decimal | None] = mapped_column(Numeric(14, 2))  # computed
    utr_no: Mapped[str | None] = mapped_column(String(255))
    utr_date: Mapped[date | None] = mapped_column(Date)
    payment_received_date: Mapped[date | None] = mapped_column(Date)
    payment_received_amt: Mapped[Decimal | None] = mapped_column(Numeric(14, 2))
    payment_mode: Mapped[str | None] = mapped_column(String(100))   # NEFT / RTGS / Cheque / UPI
    hospital_receipt_no: Mapped[str | None] = mapped_column(String(100))
    payment_tat: Mapped[int | None] = mapped_column(Integer)        # computed

    # ── OUTSTANDING & AGEING ──────────────────────────────────
    outstanding_amt: Mapped[Decimal | None] = mapped_column(Numeric(14, 2))  # computed
    ageing_days: Mapped[int | None] = mapped_column(Integer)                 # computed (TODAY-based)
    ageing_bucket: Mapped[str | None] = mapped_column(String(20))            # 0-30 / 31-60 / 61-90 / 90+

    # ── STATUS & NOTES ────────────────────────────────────────
    final_claim_status: Mapped[str | None] = mapped_column(String(100), index=True)
    insurer_comments: Mapped[str | None] = mapped_column(Text)
    hospital_remarks: Mapped[str | None] = mapped_column(Text)
    updated_by: Mapped[str | None] = mapped_column(String(100))
    last_updated_date: Mapped[date | None] = mapped_column(Date)

    # ── METADATA ──────────────────────────────────────────────
    # MD5 of the raw row tuple — used for change detection on re-import
    raw_row_hash: Mapped[str | None] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # ── Relationships ─────────────────────────────────────────
    hospital: Mapped["Hospital"] = relationship("Hospital", back_populates="claims")
    query_denials: Mapped[list["QueryDenial"]] = relationship("QueryDenial", back_populates="claim")

    def __repr__(self) -> str:
        return f"<Claim id={self.id} hsk_ref={self.hsk_ref_id!r} patient={self.patient_name!r}>"
