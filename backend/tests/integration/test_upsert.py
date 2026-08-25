"""
Integration tests for the upsert layer.

These tests hit a real PostgreSQL database (hsk_claims_test).
Each test runs inside a transaction that is rolled back on teardown,
so tests are isolated without dropping/recreating tables.
"""
import io
from decimal import Decimal

import pytest
from sqlalchemy import select, func

from app.models import Claim, Hospital, Lookup, QueryDenial
from app.sync.upsert import upsert_workbook

pytestmark = pytest.mark.integration


# ─────────────────────────────────────────────────────────────────────────────
# Hospital upsert
# ─────────────────────────────────────────────────────────────────────────────

class TestHospitalUpsert:
    async def test_hospitals_created_from_parsed_data(self, db_session, parsed_workbook):
        stats = await upsert_workbook(db_session, parsed_workbook)
        await db_session.flush()

        result = await db_session.execute(select(Hospital))
        hospitals = result.scalars().all()
        assert len(hospitals) == 1
        assert hospitals[0].name == "Tanya Speciality Hospital"

    async def test_hospital_location_stored(self, db_session, parsed_workbook):
        await upsert_workbook(db_session, parsed_workbook)
        result = await db_session.execute(select(Hospital))
        h = result.scalar_one()
        assert "Hassan" in h.location

    async def test_hospital_rohini_id_stored(self, db_session, parsed_workbook):
        await upsert_workbook(db_session, parsed_workbook)
        result = await db_session.execute(select(Hospital))
        h = result.scalar_one()
        assert h.rohini_id == "8900080409743"

    async def test_hospital_not_duplicated_on_rerun(self, db_session, parsed_workbook):
        await upsert_workbook(db_session, parsed_workbook)
        await upsert_workbook(db_session, parsed_workbook)
        result = await db_session.execute(select(func.count()).select_from(Hospital))
        assert result.scalar_one() == 1

    async def test_hospitals_created_count_in_stats(self, db_session, parsed_workbook):
        stats = await upsert_workbook(db_session, parsed_workbook)
        assert stats.hospitals_created == 1


# ─────────────────────────────────────────────────────────────────────────────
# Claims upsert — insert
# ─────────────────────────────────────────────────────────────────────────────

class TestClaimsInsert:
    async def test_all_20_claims_inserted(self, db_session, parsed_workbook):
        stats = await upsert_workbook(db_session, parsed_workbook)
        assert stats.claims_inserted == 20
        assert stats.claims_errored == 0

    async def test_claims_count_in_db(self, db_session, parsed_workbook):
        await upsert_workbook(db_session, parsed_workbook)
        result = await db_session.execute(select(func.count()).select_from(Claim))
        assert result.scalar_one() == 20

    async def test_first_claim_fields_stored_correctly(self, db_session, parsed_workbook):
        await upsert_workbook(db_session, parsed_workbook)
        result = await db_session.execute(
            select(Claim).where(Claim.hsk_ref_id == "TANCL-0001")
        )
        claim = result.scalar_one()

        assert claim.patient_name == "Teja K R"
        assert claim.insurer_name == "Aditya Birla Health"
        assert claim.final_claimed_amt == Decimal("71961")
        assert claim.final_bill_approved_amt == Decimal("67743")
        assert claim.settled_amt == Decimal("60969")
        assert claim.tds_amt == Decimal("6774")
        assert claim.payment_received_amt == Decimal("60969")
        assert claim.final_claim_status == "Settled-Paid"

    async def test_computed_fields_stored(self, db_session, parsed_workbook):
        await upsert_workbook(db_session, parsed_workbook)
        result = await db_session.execute(
            select(Claim).where(Claim.hsk_ref_id == "TANCL-0001")
        )
        claim = result.scalar_one()

        assert claim.los_days == 0
        assert claim.preauth_tat == 0
        assert claim.deduction_amt == Decimal("0")
        assert claim.outstanding_amt == Decimal("0")
        assert claim.ageing_days is None
        assert claim.ageing_bucket is None

    async def test_hospital_fk_set(self, db_session, parsed_workbook):
        await upsert_workbook(db_session, parsed_workbook)
        hospital_result = await db_session.execute(select(Hospital))
        hospital = hospital_result.scalar_one()

        claim_result = await db_session.execute(
            select(Claim).where(Claim.hsk_ref_id == "TANCL-0001")
        )
        claim = claim_result.scalar_one()
        assert claim.hospital_id == hospital.id

    async def test_zero_errors_on_clean_insert(self, db_session, parsed_workbook):
        stats = await upsert_workbook(db_session, parsed_workbook)
        assert stats.claims_errored == 0
        assert stats.errors == []


# ─────────────────────────────────────────────────────────────────────────────
# Claims upsert — skip (no change)
# ─────────────────────────────────────────────────────────────────────────────

class TestClaimsSkip:
    async def test_rerun_skips_all_unchanged(self, db_session, parsed_workbook):
        await upsert_workbook(db_session, parsed_workbook)
        stats2 = await upsert_workbook(db_session, parsed_workbook)

        assert stats2.claims_inserted == 0
        assert stats2.claims_updated == 0
        assert stats2.claims_skipped == 20

    async def test_row_count_unchanged_after_rerun(self, db_session, parsed_workbook):
        await upsert_workbook(db_session, parsed_workbook)
        await upsert_workbook(db_session, parsed_workbook)
        result = await db_session.execute(select(func.count()).select_from(Claim))
        assert result.scalar_one() == 20


# ─────────────────────────────────────────────────────────────────────────────
# Claims upsert — update (row changed)
# ─────────────────────────────────────────────────────────────────────────────

class TestClaimsUpdate:
    async def test_changed_field_triggers_update(self, db_session, parsed_workbook):
        """Modify one claim in the parsed result — should trigger 1 update."""
        await upsert_workbook(db_session, parsed_workbook)

        # Mutate one claim
        import copy, hashlib
        modified = copy.deepcopy(parsed_workbook)
        target = modified.claims[0]
        target.hospital_remarks = "Updated remark for test"
        # Must also change the hash so upsert detects the change
        target.raw_row_hash = hashlib.md5(b"changed").hexdigest()

        stats = await upsert_workbook(db_session, modified)
        assert stats.claims_updated == 1
        assert stats.claims_skipped == 19
        assert stats.claims_inserted == 0

    async def test_updated_field_persisted(self, db_session, parsed_workbook):
        await upsert_workbook(db_session, parsed_workbook)

        import copy, hashlib
        modified = copy.deepcopy(parsed_workbook)
        target = modified.claims[0]
        target.hospital_remarks = "Test update persisted"
        target.raw_row_hash = hashlib.md5(b"new_hash").hexdigest()

        await upsert_workbook(db_session, modified)

        result = await db_session.execute(
            select(Claim).where(Claim.hsk_ref_id == "TANCL-0001")
        )
        claim = result.scalar_one()
        assert claim.hospital_remarks == "Test update persisted"


# ─────────────────────────────────────────────────────────────────────────────
# Lookups
# ─────────────────────────────────────────────────────────────────────────────

class TestLookupsUpsert:
    async def test_lookups_inserted(self, db_session, parsed_workbook):
        stats = await upsert_workbook(db_session, parsed_workbook)
        assert stats.lookups_inserted > 0

    async def test_payer_type_values_stored(self, db_session, parsed_workbook):
        await upsert_workbook(db_session, parsed_workbook)
        result = await db_session.execute(
            select(Lookup).where(Lookup.category == "payer_type")
        )
        values = {row.value for row in result.scalars().all()}
        assert "TPA" in values
        assert "Insurer" in values

    async def test_lookups_not_duplicated_on_rerun(self, db_session, parsed_workbook):
        await upsert_workbook(db_session, parsed_workbook)
        count_before = (await db_session.execute(
            select(func.count()).select_from(Lookup)
        )).scalar_one()

        await upsert_workbook(db_session, parsed_workbook)
        count_after = (await db_session.execute(
            select(func.count()).select_from(Lookup)
        )).scalar_one()

        assert count_before == count_after


# ─────────────────────────────────────────────────────────────────────────────
# Query denials
# ─────────────────────────────────────────────────────────────────────────────

class TestQueryDenialsUpsert:
    async def test_three_query_denials_inserted(self, db_session, parsed_workbook):
        stats = await upsert_workbook(db_session, parsed_workbook)
        assert stats.query_denials_inserted == 3

    async def test_query_denials_in_db(self, db_session, parsed_workbook):
        await upsert_workbook(db_session, parsed_workbook)
        result = await db_session.execute(select(func.count()).select_from(QueryDenial))
        assert result.scalar_one() == 3

    async def test_query_denials_rebuilt_on_rerun(self, db_session, parsed_workbook):
        """Re-running should delete old QDs for the same refs and reinsert."""
        await upsert_workbook(db_session, parsed_workbook)
        await upsert_workbook(db_session, parsed_workbook)
        result = await db_session.execute(select(func.count()).select_from(QueryDenial))
        # Still exactly 3 — no duplicates
        assert result.scalar_one() == 3

    async def test_first_query_denial_fields(self, db_session, parsed_workbook):
        await upsert_workbook(db_session, parsed_workbook)
        result = await db_session.execute(
            select(QueryDenial).where(QueryDenial.hsk_ref_id == "TANCL1003")
        )
        qd = result.scalar_one()
        assert qd.stage == "Submission"
        assert qd.resolution_tat == 4
        assert qd.disallowed_amt == Decimal("39516")
