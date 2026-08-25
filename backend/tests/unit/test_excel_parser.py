"""
Unit tests for the Excel parser against the real workbook.

Golden values are taken directly from the Excel DashBoard sheet and verified
by eye. If these numbers change, either the source file changed or the parser
has a regression.

All tests are session-scoped via the `parsed_workbook` fixture — the file is
opened only once per pytest run.
"""
import io
import pytest
from decimal import Decimal
from datetime import date

from app.sync.excel_parser import parse_workbook, ParsedWorkbook

pytestmark = pytest.mark.unit


# ─────────────────────────────────────────────────────────────────────────────
# Structural / count tests
# ─────────────────────────────────────────────────────────────────────────────

class TestWorkbookStructure:
    def test_no_parse_errors(self, parsed_workbook: ParsedWorkbook):
        assert parsed_workbook.parse_errors == [], (
            f"Parser raised errors: {parsed_workbook.parse_errors}"
        )

    def test_correct_number_of_claims(self, parsed_workbook: ParsedWorkbook):
        assert len(parsed_workbook.claims) == 20

    def test_hospitals_detected(self, parsed_workbook: ParsedWorkbook):
        names = [h.name for h in parsed_workbook.hospitals]
        assert "Tanya Speciality Hospital" in names

    def test_single_hospital_in_file(self, parsed_workbook: ParsedWorkbook):
        assert len(parsed_workbook.hospitals) == 1

    def test_hospital_location(self, parsed_workbook: ParsedWorkbook):
        hospital = parsed_workbook.hospitals[0]
        assert "Hassan" in hospital.location

    def test_hospital_rohini_id(self, parsed_workbook: ParsedWorkbook):
        hospital = parsed_workbook.hospitals[0]
        assert hospital.rohini_id == "8900080409743"

    def test_query_denials_loaded(self, parsed_workbook: ParsedWorkbook):
        assert len(parsed_workbook.query_denials) == 3

    def test_lookups_categories_present(self, parsed_workbook: ParsedWorkbook):
        expected_categories = {
            "payer_type", "tpa_names", "insurance_companies",
            "preauth_status", "discharge_status", "submission_status",
            "claim_status", "payment_mode", "policy_type",
            "query_reasons", "disallowed_reasons", "submission_type",
        }
        assert expected_categories.issubset(set(parsed_workbook.lookups.keys()))

    def test_lookups_payer_types(self, parsed_workbook: ParsedWorkbook):
        payer_types = parsed_workbook.lookups.get("payer_type", [])
        assert "TPA" in payer_types
        assert "Insurer" in payer_types

    def test_lookups_payment_modes(self, parsed_workbook: ParsedWorkbook):
        modes = parsed_workbook.lookups.get("payment_mode", [])
        assert "NEFT" in modes
        assert "RTGS" in modes


# ─────────────────────────────────────────────────────────────────────────────
# KPI golden values — must match Excel DashBoard sheet exactly
# ─────────────────────────────────────────────────────────────────────────────

class TestKpiGoldenValues:
    """
    These exact numbers appear in the Excel DashBoard section 1 (Headline KPIs).
    Any change here = either source data changed or parser regressed.
    """

    def test_total_claims(self, parsed_workbook: ParsedWorkbook):
        assert len(parsed_workbook.claims) == 20

    def test_total_billed(self, parsed_workbook: ParsedWorkbook):
        total = sum(c.final_claimed_amt or Decimal(0) for c in parsed_workbook.claims)
        assert total == Decimal("1373099"), f"Expected ₹13,73,099 got ₹{total}"

    def test_total_approved(self, parsed_workbook: ParsedWorkbook):
        total = sum(c.final_bill_approved_amt or Decimal(0) for c in parsed_workbook.claims)
        assert total == Decimal("1060316"), f"Expected ₹10,60,316 got ₹{total}"

    def test_total_paid(self, parsed_workbook: ParsedWorkbook):
        # "Total Paid" = SUM(payment_received_amt) = ₹9,74,198
        total = sum(c.payment_received_amt or Decimal(0) for c in parsed_workbook.claims)
        assert total == Decimal("974198"), f"Expected ₹9,74,198 got ₹{total}"

    def test_total_settled_gross(self, parsed_workbook: ParsedWorkbook):
        # "Total Settled" on dashboard = settled + tds = ₹10,56,551
        total = sum(
            (c.settled_amt or Decimal(0)) + (c.tds_amt or Decimal(0))
            for c in parsed_workbook.claims
        )
        assert total == Decimal("1056551"), f"Expected ₹10,56,551 got ₹{total}"

    def test_total_tds(self, parsed_workbook: ParsedWorkbook):
        # "Total Deductions" on dashboard = ₹82,353 (TDS sum)
        total = sum(c.tds_amt or Decimal(0) for c in parsed_workbook.claims)
        assert total == Decimal("82353"), f"Expected ₹82,353 got ₹{total}"

    def test_approval_rate(self, parsed_workbook: ParsedWorkbook):
        total_claimed = sum(c.final_claimed_amt or Decimal(0) for c in parsed_workbook.claims)
        total_approved = sum(c.final_bill_approved_amt or Decimal(0) for c in parsed_workbook.claims)
        rate = round(100 * total_approved / total_claimed, 1)
        assert rate == 77.2, f"Expected 77.2% approval rate, got {rate}%"

    def test_all_claims_same_hospital(self, parsed_workbook: ParsedWorkbook):
        hospitals = {c.hospital_name for c in parsed_workbook.claims}
        assert hospitals == {"Tanya Speciality Hospital"}

    def test_all_claims_in_april_2026(self, parsed_workbook: ParsedWorkbook):
        """All 20 claims in this file are from April 2026."""
        for claim in parsed_workbook.claims:
            assert claim.month_label == "Apr-26", (
                f"Claim {claim.hsk_ref_id} has unexpected month: {claim.month_label}"
            )


# ─────────────────────────────────────────────────────────────────────────────
# Field mapping — spot-check first claim (Teja K R)
# ─────────────────────────────────────────────────────────────────────────────

class TestFirstClaimMapping:
    @pytest.fixture(autouse=True)
    def first_claim(self, parsed_workbook: ParsedWorkbook):
        self.c = parsed_workbook.claims[0]

    def test_hsk_ref_id(self):
        assert self.c.hsk_ref_id == "TANCL-0001"

    def test_ihx_ref_id(self):
        assert self.c.ihx_ref_id == "17450123"

    def test_patient_name(self):
        assert self.c.patient_name == "Teja K R"

    def test_hospital_name(self):
        assert self.c.hospital_name == "Tanya Speciality Hospital"

    def test_insurer_name(self):
        assert self.c.insurer_name == "Aditya Birla Health"

    def test_tpa_name(self):
        assert self.c.tpa_name == "MediAssist TPA"

    def test_payer_type(self):
        assert self.c.payer_type == "Insurer"

    def test_date_admission(self):
        assert self.c.date_admission == date(2026, 4, 5)

    def test_date_discharge(self):
        assert self.c.date_discharge == date(2026, 4, 5)

    def test_los_days_computed(self):
        # Same-day discharge → LOS = 0
        assert self.c.los_days == 0

    def test_preauth_status(self):
        assert self.c.preauth_status == "Preauth Approved"

    def test_preauth_tat_computed(self):
        # Preauth requested 4-Apr, approved 4-Apr → TAT = 0
        assert self.c.preauth_tat == 0

    def test_final_claimed_amt(self):
        assert self.c.final_claimed_amt == Decimal("71961")

    def test_final_bill_approved_amt(self):
        assert self.c.final_bill_approved_amt == Decimal("67743")

    def test_settled_amt(self):
        assert self.c.settled_amt == Decimal("60969")

    def test_tds_amt(self):
        assert self.c.tds_amt == Decimal("6774")

    def test_deduction_computed_zero(self):
        # 67743 - (60969 + 6774) = 0
        assert self.c.deduction_amt == Decimal("0")

    def test_payment_received_amt(self):
        assert self.c.payment_received_amt == Decimal("60969")

    def test_outstanding_computed_zero(self):
        # Fully paid → outstanding = 0
        assert self.c.outstanding_amt == Decimal("0")

    def test_ageing_days_none_when_no_outstanding(self):
        assert self.c.ageing_days is None

    def test_ageing_bucket_none_when_no_outstanding(self):
        assert self.c.ageing_bucket is None

    def test_final_claim_status(self):
        assert self.c.final_claim_status == "Settled-Paid"

    def test_query_raised_false(self):
        assert self.c.query_raised is False

    def test_payment_mode(self):
        assert self.c.payment_mode == "NEFT"

    def test_submission_type(self):
        assert self.c.submission_type == "Hard Copy"

    def test_row_hash_is_set(self):
        assert self.c.raw_row_hash is not None
        assert len(self.c.raw_row_hash) == 32


# ─────────────────────────────────────────────────────────────────────────────
# Specific rows — spot checks across the dataset
# ─────────────────────────────────────────────────────────────────────────────

class TestSpecificRowChecks:
    def test_second_claim_patient(self, parsed_workbook):
        c = parsed_workbook.claims[1]
        assert c.patient_name == "baby of nikitha"
        assert c.los_days == 2   # admitted Apr 3, discharged Apr 5

    def test_third_claim_courier_awb(self, parsed_workbook):
        """Row 3 (priyanka H K) has a courier AWB number."""
        c = parsed_workbook.claims[2]
        assert c.courier_awb == "HSN6321482"

    def test_fifth_claim_settled_payment_pending(self, parsed_workbook):
        """Row 5 (Megha M H) is Settled-Payment Pending (not Settled-Paid)."""
        c = parsed_workbook.claims[4]
        assert c.final_claim_status == "Settled-Payment Pending"

    def test_last_claim_patient(self, parsed_workbook):
        c = parsed_workbook.claims[19]
        assert c.patient_name == "MOHAK"

    def test_last_claim_insurer(self, parsed_workbook):
        c = parsed_workbook.claims[19]
        assert c.insurer_name == "United India Insurance"

    def test_all_hsk_ref_ids_unique(self, parsed_workbook):
        ids = [c.hsk_ref_id for c in parsed_workbook.claims if c.hsk_ref_id]
        assert len(ids) == len(set(ids)), "Duplicate hsk_ref_ids found"

    def test_all_hsk_ref_ids_follow_pattern(self, parsed_workbook):
        import re
        pattern = re.compile(r"^TANCL-\d{4}$")
        for c in parsed_workbook.claims:
            assert pattern.match(c.hsk_ref_id), (
                f"Unexpected hsk_ref_id format: {c.hsk_ref_id!r}"
            )

    def test_all_row_hashes_unique(self, parsed_workbook):
        hashes = [c.raw_row_hash for c in parsed_workbook.claims]
        assert len(hashes) == len(set(hashes)), "Duplicate row hashes found (identical rows?)"


# ─────────────────────────────────────────────────────────────────────────────
# Query denials
# ─────────────────────────────────────────────────────────────────────────────

class TestQueryDenials:
    def test_three_query_denial_records(self, parsed_workbook):
        assert len(parsed_workbook.query_denials) == 3

    def test_first_denial_hsk_ref(self, parsed_workbook):
        qd = parsed_workbook.query_denials[0]
        assert qd.hsk_ref_id == "TANCL1003"

    def test_first_denial_stage(self, parsed_workbook):
        qd = parsed_workbook.query_denials[0]
        assert qd.stage == "Submission"

    def test_second_denial_appeal_filed(self, parsed_workbook):
        qd = parsed_workbook.query_denials[1]
        assert qd.appeal_filed is True

    def test_third_denial_status(self, parsed_workbook):
        qd = parsed_workbook.query_denials[2]
        assert qd.status == "Query Raised"

    def test_denial_resolution_tat_computed(self, parsed_workbook):
        """First QD: raised 1-Feb, response 5-Feb → TAT = 4 days."""
        qd = parsed_workbook.query_denials[0]
        assert qd.resolution_tat == 4


# ─────────────────────────────────────────────────────────────────────────────
# Formula string rejection
# ─────────────────────────────────────────────────────────────────────────────

class TestFormulaCellRejection:
    def test_parse_bytes_with_formula_only_cells(self):
        """
        Feed a minimal synthetic workbook where computed columns have raw formula
        strings (as they appear when data_only=False). The parser must not crash
        and must produce None for formula-only cells.
        """
        import openpyxl
        from io import BytesIO
        from app.sync.excel_parser import _to_str, _to_date, _to_decimal

        formula_strings = [
            '=IF(AND(ISNUMBER(N4),ISNUMBER(O4)),O4-N4,"")',
            '=IF(A4="","",IF(ISNUMBER(BI4),MAX((BI4+BJ4)-IF(ISNUMBER(BO4+BJ4),(BO4+BJ4),0),0),""))',
            '=TEXT(O4,"MMM-YY")',
        ]
        for formula in formula_strings:
            assert _to_str(formula) is None, f"Formula not rejected: {formula!r}"
            assert _to_date(formula) is None
            assert _to_decimal(formula) is None


# ─────────────────────────────────────────────────────────────────────────────
# Parser robustness
# ─────────────────────────────────────────────────────────────────────────────

class TestParserRobustness:
    def test_parse_empty_bytes_returns_error(self):
        result = parse_workbook(io.BytesIO(b"not an excel file"))
        assert result.parse_errors, "Expected parse error for invalid file"
        assert result.claims == []

    def test_parse_real_file_twice_same_result(self, excel_bytes):
        """Parser must be deterministic — same file → same output."""
        wb1 = parse_workbook(io.BytesIO(excel_bytes))
        wb2 = parse_workbook(io.BytesIO(excel_bytes))
        assert len(wb1.claims) == len(wb2.claims)
        hashes1 = sorted(c.raw_row_hash for c in wb1.claims)
        hashes2 = sorted(c.raw_row_hash for c in wb2.claims)
        assert hashes1 == hashes2
