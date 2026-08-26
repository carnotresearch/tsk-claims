"""
Upsert logic — takes parsed data and writes it to the database.

Strategy:
  - Hospitals: upsert by name (auto-create on first encounter, never deleted)
  - Claims: wipe all existing rows, insert fresh from Excel
  - QueryDenials: wipe all existing rows, insert fresh (claims flushed first for FK links)
  - Lookups: wipe all existing rows, insert fresh

Users are never touched. Hospital records are preserved so that hospital-scoped
users continue to exist and simply see 0 claims if their hospital has no rows
in the new Excel.

All operations go through a single AsyncSession passed in from the pipeline.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Hospital, Claim, QueryDenial, Lookup
from app.sync.excel_parser import ParsedWorkbook, ParsedClaim, ParsedQueryDenial, ParsedHospital

logger = logging.getLogger(__name__)


@dataclass
class UpsertStats:
    hospitals_created: int = 0
    claims_inserted: int = 0
    claims_updated: int = 0   # always 0 under wipe-then-insert strategy
    claims_skipped: int = 0   # always 0 under wipe-then-insert strategy
    claims_errored: int = 0
    query_denials_inserted: int = 0
    lookups_inserted: int = 0
    errors: list[str] = field(default_factory=list)


async def upsert_workbook(db: AsyncSession, parsed: ParsedWorkbook) -> UpsertStats:
    """
    Persist all parsed data into the database using a wipe-then-insert strategy.

    Existing claims, query denials, and lookups are deleted first so that the
    database always reflects exactly what is in the uploaded Excel file.
    Hospitals and users are never deleted.

    Returns per-entity counts for the sync log.
    """
    stats = UpsertStats()

    # 1. Hospitals — upsert by name (preserve existing, create new)
    #    Must run before the wipe so hospital_map is available for FK assignment.
    hospital_map = await _upsert_hospitals(db, parsed.hospitals, stats)

    # 2. Wipe transactional data in FK-safe order
    #    (query_denials → claims → lookups; hospitals and users are untouched)
    await db.execute(delete(QueryDenial))
    await db.execute(delete(Claim))
    await db.execute(delete(Lookup))

    # 3. Insert all claims fresh; collect ORM objects for later FK linking
    added_claims: list[Claim] = []
    for parsed_claim in parsed.claims:
        claim_obj = _insert_claim(db, parsed_claim, hospital_map, stats)
        if claim_obj is not None:
            added_claims.append(claim_obj)

    # 4. Flush to let Postgres assign PKs on all newly inserted Claim rows
    await db.flush()

    # 5. Build hsk_ref_id → Claim map (ids are now populated post-flush)
    new_claims: dict[str, Claim] = {
        c.hsk_ref_id: c for c in added_claims if c.hsk_ref_id
    }

    # 6. Insert query denials with correct FK links to the new claims
    if parsed.query_denials:
        _insert_query_denials(db, parsed.query_denials, new_claims, stats)

    # 7. Insert lookups fresh
    _insert_lookups(db, parsed.lookups, stats)

    await db.flush()
    logger.info(
        "Sync complete (wipe-then-insert): hospitals=%d, claims_inserted=%d, "
        "claims_errored=%d, query_denials=%d, lookups=%d",
        stats.hospitals_created,
        stats.claims_inserted,
        stats.claims_errored,
        stats.query_denials_inserted,
        stats.lookups_inserted,
    )
    return stats


async def _upsert_hospitals(
    db: AsyncSession,
    hospitals: list[ParsedHospital],
    stats: UpsertStats,
) -> dict[str, int]:
    """Return {hospital_name: hospital_id} map. Creates new hospitals; never deletes."""
    hospital_map: dict[str, int] = {}

    for ph in hospitals:
        result = await db.execute(select(Hospital).where(Hospital.name == ph.name))
        existing = result.scalar_one_or_none()

        if existing:
            hospital_map[ph.name] = existing.id
            # Backfill location/rohini_id if they were previously null
            if ph.location and not existing.location:
                existing.location = ph.location
            if ph.rohini_id and not existing.rohini_id:
                existing.rohini_id = ph.rohini_id
        else:
            new_hospital = Hospital(
                name=ph.name,
                location=ph.location,
                rohini_id=ph.rohini_id,
            )
            db.add(new_hospital)
            await db.flush()  # get the generated id
            hospital_map[ph.name] = new_hospital.id
            stats.hospitals_created += 1
            logger.info("Created hospital: %r (id=%d)", ph.name, new_hospital.id)

    return hospital_map


def _insert_claim(
    db: AsyncSession,
    pc: ParsedClaim,
    hospital_map: dict[str, int],
    stats: UpsertStats,
) -> Claim | None:
    """
    Insert a single claim. Returns the ORM object on success, None on error.

    Partial claims (missing settlement, null amounts, in-progress status) are
    inserted as-is — every row with a hospital_name and patient_name is a valid
    claim regardless of how many fields are filled.
    """
    hospital_id = hospital_map.get(pc.hospital_name)
    if not hospital_id:
        msg = f"Hospital not found for claim {pc.hsk_ref_id!r}: {pc.hospital_name!r}"
        stats.errors.append(msg)
        stats.claims_errored += 1
        logger.warning(msg)
        return None

    try:
        claim = Claim(hospital_id=hospital_id)
        _apply_claim_fields(claim, pc, hospital_id)
        db.add(claim)
        stats.claims_inserted += 1
        return claim
    except Exception as exc:
        msg = f"Error inserting claim {pc.hsk_ref_id!r}: {exc}"
        stats.errors.append(msg)
        stats.claims_errored += 1
        logger.error(msg, exc_info=True)
        return None


def _insert_query_denials(
    db: AsyncSession,
    query_denials: list[ParsedQueryDenial],
    new_claims: dict[str, Claim],
    stats: UpsertStats,
) -> None:
    """Insert query denial rows, linking to newly inserted claims by hsk_ref_id."""
    for pqd in query_denials:
        claim = new_claims.get(pqd.hsk_ref_id) if pqd.hsk_ref_id else None
        qd = QueryDenial(
            claim_id=claim.id if claim else None,
            hsk_ref_id=pqd.hsk_ref_id,
            stage=pqd.stage,
            query_raised_date=pqd.query_raised_date,
            query_reason_category=pqd.query_reason_category,
            query_reason_desc=pqd.query_reason_desc,
            action_required=pqd.action_required,
            responsible_person=pqd.responsible_person,
            target_response_date=pqd.target_response_date,
            response_date=pqd.response_date,
            resolution_tat=pqd.resolution_tat,
            resubmission_date=pqd.resubmission_date,
            disallowed_amt=pqd.disallowed_amt,
            disallowed_reason=pqd.disallowed_reason,
            appeal_filed=pqd.appeal_filed,
            appeal_date=pqd.appeal_date,
            appeal_outcome=pqd.appeal_outcome,
            final_recovery=pqd.final_recovery,
            net_loss=pqd.net_loss,
            status=pqd.status,
            remarks=pqd.remarks,
        )
        db.add(qd)
        stats.query_denials_inserted += 1


def _insert_lookups(
    db: AsyncSession,
    lookups: dict[str, list[str]],
    stats: UpsertStats,
) -> None:
    """Insert all lookup values fresh (table was already wiped)."""
    for category, values in lookups.items():
        for value in values:
            db.add(Lookup(category=category, value=value))
            stats.lookups_inserted += 1


def _apply_claim_fields(claim: Claim, pc: ParsedClaim, hospital_id: int) -> None:
    """Copy all fields from ParsedClaim onto a Claim ORM object."""
    claim.hospital_id = hospital_id
    claim.hsk_ref_id = pc.hsk_ref_id
    claim.month_label = pc.month_label
    claim.ihx_ref_id = pc.ihx_ref_id
    claim.uhid = pc.uhid
    claim.ip_number = pc.ip_number
    claim.patient_name = pc.patient_name
    claim.patient_contact = pc.patient_contact
    claim.insured_name = pc.insured_name
    claim.employee_code = pc.employee_code
    claim.corporate_name = pc.corporate_name
    claim.date_admission = pc.date_admission
    claim.date_discharge = pc.date_discharge
    claim.los_days = pc.los_days
    claim.procedure_name = pc.procedure_name
    claim.diagnosis = pc.diagnosis
    claim.payer_type = pc.payer_type
    claim.tpa_name = pc.tpa_name
    claim.insurer_name = pc.insurer_name
    claim.policy_no = pc.policy_no
    claim.policy_type = pc.policy_type
    claim.preauth_no = pc.preauth_no
    claim.initial_claim_no = pc.initial_claim_no
    claim.preauth_request_date = pc.preauth_request_date
    claim.preauth_approval_date = pc.preauth_approval_date
    claim.preauth_requested_amt = pc.preauth_requested_amt
    claim.preauth_approved_amt = pc.preauth_approved_amt
    claim.preauth_copay = pc.preauth_copay
    claim.preauth_status = pc.preauth_status
    claim.preauth_tat = pc.preauth_tat
    claim.final_bill_request_date = pc.final_bill_request_date
    claim.final_bill_approval_date = pc.final_bill_approval_date
    claim.final_claimed_amt = pc.final_claimed_amt
    claim.final_bill_approved_amt = pc.final_bill_approved_amt
    claim.hospital_discount = pc.hospital_discount
    claim.patient_paid_amt = pc.patient_paid_amt
    claim.discharge_status = pc.discharge_status
    claim.discharge_tat = pc.discharge_tat
    claim.submission_type = pc.submission_type
    claim.submission_date = pc.submission_date
    claim.submission_tat = pc.submission_tat
    claim.submission_status = pc.submission_status
    claim.courier_agency = pc.courier_agency
    claim.courier_destination = pc.courier_destination
    claim.courier_dispatch_date = pc.courier_dispatch_date
    claim.courier_awb = pc.courier_awb
    claim.hospital_invoice_no = pc.hospital_invoice_no
    claim.query_raised = pc.query_raised
    claim.query_raised_date = pc.query_raised_date
    claim.query_reason = pc.query_reason
    claim.query_response_date = pc.query_response_date
    claim.query_resolution_tat = pc.query_resolution_tat
    claim.resubmission_date = pc.resubmission_date
    claim.disallowed_amt = pc.disallowed_amt
    claim.denial_reason = pc.denial_reason
    claim.appeal_filed = pc.appeal_filed
    claim.appeal_date = pc.appeal_date
    claim.settlement_date = pc.settlement_date
    claim.settled_amt = pc.settled_amt
    claim.tds_amt = pc.tds_amt
    claim.deduction_amt = pc.deduction_amt
    claim.utr_no = pc.utr_no
    claim.utr_date = pc.utr_date
    claim.payment_received_date = pc.payment_received_date
    claim.payment_received_amt = pc.payment_received_amt
    claim.payment_mode = pc.payment_mode
    claim.hospital_receipt_no = pc.hospital_receipt_no
    claim.payment_tat = pc.payment_tat
    claim.outstanding_amt = pc.outstanding_amt
    claim.ageing_days = pc.ageing_days
    claim.ageing_bucket = pc.ageing_bucket
    claim.final_claim_status = pc.final_claim_status
    claim.insurer_comments = pc.insurer_comments
    claim.hospital_remarks = pc.hospital_remarks
    claim.updated_by = pc.updated_by
    claim.last_updated_date = pc.last_updated_date
    claim.raw_row_hash = pc.raw_row_hash
