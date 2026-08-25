"""
Upsert logic — takes parsed data and writes it to the database.

Strategy:
  - Hospitals: upsert by name (auto-create on first encounter)
  - Claims: upsert by hsk_ref_id; skip if raw_row_hash unchanged (no-op)
  - QueryDenials: delete-and-reinsert per hsk_ref_id (simple, avoids drift)
  - Lookups: upsert by (category, value)

All operations go through a single AsyncSession passed in from the pipeline.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Hospital, Claim, QueryDenial, Lookup
from app.sync.excel_parser import ParsedWorkbook, ParsedClaim, ParsedQueryDenial, ParsedHospital

logger = logging.getLogger(__name__)


@dataclass
class UpsertStats:
    hospitals_created: int = 0
    claims_inserted: int = 0
    claims_updated: int = 0
    claims_skipped: int = 0
    claims_errored: int = 0
    query_denials_inserted: int = 0
    lookups_inserted: int = 0
    errors: list[str] = field(default_factory=list)


async def upsert_workbook(db: AsyncSession, parsed: ParsedWorkbook) -> UpsertStats:
    """
    Persist all parsed data into the database.
    Returns per-entity counts for the sync log.
    """
    stats = UpsertStats()

    # 1. Hospitals
    hospital_map = await _upsert_hospitals(db, parsed.hospitals, stats)

    # 2. Lookups
    await _upsert_lookups(db, parsed.lookups, stats)

    # 3. Claims — build existing claim map for O(1) lookups
    existing = await _load_existing_claims(db)
    for parsed_claim in parsed.claims:
        await _upsert_claim(db, parsed_claim, hospital_map, existing, stats)

    # 4. Query denials — rebuild from parsed data
    if parsed.query_denials:
        await _upsert_query_denials(db, parsed.query_denials, existing, stats)

    await db.flush()
    logger.info(
        "Upsert complete: hospitals=%d, claims_inserted=%d, claims_updated=%d, "
        "claims_skipped=%d, claims_errored=%d, query_denials=%d",
        stats.hospitals_created,
        stats.claims_inserted,
        stats.claims_updated,
        stats.claims_skipped,
        stats.claims_errored,
        stats.query_denials_inserted,
    )
    return stats


async def _upsert_hospitals(
    db: AsyncSession,
    hospitals: list[ParsedHospital],
    stats: UpsertStats,
) -> dict[str, int]:
    """Return {hospital_name: hospital_id} map."""
    hospital_map: dict[str, int] = {}

    for ph in hospitals:
        result = await db.execute(select(Hospital).where(Hospital.name == ph.name))
        existing = result.scalar_one_or_none()

        if existing:
            hospital_map[ph.name] = existing.id
            # Update location/rohini_id if they were previously null
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


async def _load_existing_claims(db: AsyncSession) -> dict[str, Claim]:
    """Load all existing claims keyed by hsk_ref_id for fast lookup."""
    result = await db.execute(select(Claim))
    return {c.hsk_ref_id: c for c in result.scalars().all() if c.hsk_ref_id}


async def _upsert_claim(
    db: AsyncSession,
    pc: ParsedClaim,
    hospital_map: dict[str, int],
    existing: dict[str, Claim],
    stats: UpsertStats,
) -> None:
    hospital_id = hospital_map.get(pc.hospital_name)
    if not hospital_id:
        msg = f"Hospital not found for claim {pc.hsk_ref_id!r}: {pc.hospital_name!r}"
        stats.errors.append(msg)
        stats.claims_errored += 1
        logger.warning(msg)
        return

    try:
        if pc.hsk_ref_id and pc.hsk_ref_id in existing:
            claim = existing[pc.hsk_ref_id]
            # Skip if data hasn't changed
            if claim.raw_row_hash == pc.raw_row_hash:
                stats.claims_skipped += 1
                return
            # Update all fields
            _apply_claim_fields(claim, pc, hospital_id)
            stats.claims_updated += 1
        else:
            claim = Claim(hospital_id=hospital_id)
            _apply_claim_fields(claim, pc, hospital_id)
            db.add(claim)
            stats.claims_inserted += 1
    except Exception as exc:
        msg = f"Error upserting claim {pc.hsk_ref_id!r}: {exc}"
        stats.errors.append(msg)
        stats.claims_errored += 1
        logger.error(msg, exc_info=True)


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


async def _upsert_query_denials(
    db: AsyncSession,
    query_denials: list[ParsedQueryDenial],
    existing_claims: dict[str, Claim],
    stats: UpsertStats,
) -> None:
    """
    Simple rebuild strategy: delete existing QueryDenial rows for affected
    hsk_ref_ids, then reinsert fresh from parsed data.
    """
    affected_refs = {qd.hsk_ref_id for qd in query_denials if qd.hsk_ref_id}
    if affected_refs:
        await db.execute(
            delete(QueryDenial).where(QueryDenial.hsk_ref_id.in_(affected_refs))
        )

    for pqd in query_denials:
        claim = existing_claims.get(pqd.hsk_ref_id) if pqd.hsk_ref_id else None
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


async def _upsert_lookups(
    db: AsyncSession,
    lookups: dict[str, list[str]],
    stats: UpsertStats,
) -> None:
    for category, values in lookups.items():
        for value in values:
            result = await db.execute(
                select(Lookup).where(Lookup.category == category, Lookup.value == value)
            )
            if not result.scalar_one_or_none():
                db.add(Lookup(category=category, value=value))
                stats.lookups_inserted += 1
