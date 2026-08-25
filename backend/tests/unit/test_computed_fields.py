"""
Unit tests for all formula-replication helpers in excel_parser.py.

No database, no file I/O — pure function tests.
Each function maps directly to a formula in the Excel workbook.
"""
import pytest
from datetime import date, datetime
from decimal import Decimal

from app.sync.excel_parser import (
    _tat,
    _compute_deduction,
    _compute_outstanding,
    _compute_ageing_days,
    _compute_ageing_bucket,
    _compute_month_label,
    _compute_hsk_ref_id,
    _to_date,
    _to_decimal,
    _to_int,
    _to_bool,
    _to_str,
    _row_hash,
)

pytestmark = pytest.mark.unit


# ── _tat (TAT = turnaround time in days) ─────────────────────────────────────
class TestTat:
    def test_normal(self):
        assert _tat(date(2026, 4, 1), date(2026, 4, 3)) == 2

    def test_same_day(self):
        assert _tat(date(2026, 4, 1), date(2026, 4, 1)) == 0

    def test_start_none(self):
        assert _tat(None, date(2026, 4, 3)) is None

    def test_end_none(self):
        assert _tat(date(2026, 4, 1), None) is None

    def test_both_none(self):
        assert _tat(None, None) is None

    def test_end_before_start_returns_none(self):
        # Discharge before admission = data error → return None
        assert _tat(date(2026, 4, 5), date(2026, 4, 1)) is None

    def test_cross_month(self):
        assert _tat(date(2026, 3, 28), date(2026, 4, 5)) == 8

    def test_los_zero_day_stay(self):
        # Day surgery — admitted and discharged same day
        assert _tat(date(2026, 4, 5), date(2026, 4, 5)) == 0


# ── _compute_deduction ────────────────────────────────────────────────────────
# Excel: =MAX(AJ-(BI+BJ),0)  → max(approved - (settled + tds), 0)
class TestComputeDeduction:
    def test_no_deduction_when_settled_equals_approved(self):
        # settled + tds == approved → deduction = 0
        assert _compute_deduction(
            approved=Decimal("67743"),
            settled=Decimal("60969"),
            tds=Decimal("6774"),
        ) == Decimal("0")

    def test_positive_deduction(self):
        # approved=100, settled=80, tds=10 → deduction = max(100-90, 0) = 10
        result = _compute_deduction(
            approved=Decimal("100"),
            settled=Decimal("80"),
            tds=Decimal("10"),
        )
        assert result == Decimal("10")

    def test_no_negative_deduction(self):
        # settled+tds > approved (e.g. rounding) → clamped to 0
        result = _compute_deduction(
            approved=Decimal("100"),
            settled=Decimal("95"),
            tds=Decimal("10"),
        )
        assert result == Decimal("0")

    def test_none_tds_treated_as_zero(self):
        result = _compute_deduction(
            approved=Decimal("100"),
            settled=Decimal("85"),
            tds=None,
        )
        assert result == Decimal("15")

    def test_none_approved_returns_none(self):
        assert _compute_deduction(None, Decimal("80"), Decimal("10")) is None

    def test_none_settled_returns_none(self):
        assert _compute_deduction(Decimal("100"), None, Decimal("10")) is None

    def test_all_none_returns_none(self):
        assert _compute_deduction(None, None, None) is None

    def test_real_claim_row1(self):
        """Row 1: approved=67743, settled=60969, tds=6774 → deduction=0"""
        result = _compute_deduction(
            approved=Decimal("67743"),
            settled=Decimal("60969"),
            tds=Decimal("6774"),
        )
        assert result == Decimal("0")


# ── _compute_outstanding ──────────────────────────────────────────────────────
# Excel: if settled: max(settled - payment, 0)  else: max(approved - (payment+tds), 0)
class TestComputeOutstanding:
    def test_fully_paid_zero_outstanding(self):
        # settled=60969, payment=60969 → outstanding=0
        result = _compute_outstanding(
            approved=Decimal("67743"),
            settled=Decimal("60969"),
            tds=Decimal("6774"),
            payment_received=Decimal("60969"),
        )
        assert result == Decimal("0")

    def test_partial_payment_outstanding(self):
        # settled=100000, payment=60000 → outstanding=40000
        result = _compute_outstanding(
            approved=Decimal("150000"),
            settled=Decimal("100000"),
            tds=Decimal("10000"),
            payment_received=Decimal("60000"),
        )
        assert result == Decimal("40000")

    def test_no_settlement_uses_approved(self):
        # No settled_amt yet → outstanding = approved - (payment + tds)
        result = _compute_outstanding(
            approved=Decimal("100000"),
            settled=None,
            tds=Decimal("10000"),
            payment_received=Decimal("50000"),
        )
        assert result == Decimal("40000")  # 100000 - (50000 + 10000)

    def test_no_payment_and_no_settlement(self):
        result = _compute_outstanding(
            approved=Decimal("100000"),
            settled=None,
            tds=None,
            payment_received=None,
        )
        assert result == Decimal("100000")

    def test_no_approved_no_settled_returns_none(self):
        assert _compute_outstanding(None, None, None, None) is None

    def test_no_negative_outstanding(self):
        # overpayment edge case → clamped to 0
        result = _compute_outstanding(
            approved=Decimal("100"),
            settled=Decimal("90"),
            tds=Decimal("10"),
            payment_received=Decimal("95"),
        )
        assert result == Decimal("0")


# ── _compute_ageing_days ──────────────────────────────────────────────────────
# Excel: =IF(AND(ISNUMBER(BS),BS>0),TODAY()-AH,"")
class TestComputeAgeingDays:
    def test_zero_outstanding_no_ageing(self):
        assert _compute_ageing_days(Decimal("0"), date(2026, 4, 1)) is None

    def test_none_outstanding_no_ageing(self):
        assert _compute_ageing_days(None, date(2026, 4, 1)) is None

    def test_none_approval_date_no_ageing(self):
        assert _compute_ageing_days(Decimal("1000"), None) is None

    def test_positive_outstanding_returns_days(self):
        from datetime import date as dt
        approval_date = dt(2026, 4, 1)
        days = _compute_ageing_days(Decimal("50000"), approval_date)
        # Must be a non-negative integer (today - approval_date)
        assert isinstance(days, int)
        assert days >= 0

    def test_ageing_days_increases_with_older_date(self):
        old_date = date(2025, 1, 1)
        recent_date = date(2026, 6, 1)
        old_days = _compute_ageing_days(Decimal("1000"), old_date)
        recent_days = _compute_ageing_days(Decimal("1000"), recent_date)
        assert old_days > recent_days


# ── _compute_ageing_bucket ────────────────────────────────────────────────────
class TestComputeAgeingBucket:
    @pytest.mark.parametrize("days,expected", [
        (0,   "0-30"),
        (1,   "0-30"),
        (30,  "0-30"),
        (31,  "31-60"),
        (60,  "31-60"),
        (61,  "61-90"),
        (90,  "61-90"),
        (91,  "90+"),
        (200, "90+"),
        (365, "90+"),
    ])
    def test_bucket_boundaries(self, days, expected):
        assert _compute_ageing_bucket(days) == expected

    def test_none_returns_none(self):
        assert _compute_ageing_bucket(None) is None


# ── _compute_month_label ──────────────────────────────────────────────────────
class TestComputeMonthLabel:
    def test_uses_discharge_date(self):
        assert _compute_month_label(date(2026, 4, 15), date(2026, 3, 1)) == "Apr-26"

    def test_falls_back_to_admission_if_no_discharge(self):
        assert _compute_month_label(None, date(2026, 5, 10)) == "May-26"

    def test_both_none_returns_none(self):
        assert _compute_month_label(None, None) is None

    @pytest.mark.parametrize("month,expected", [
        (1, "Jan-26"), (2, "Feb-26"), (3, "Mar-26"), (4, "Apr-26"),
        (5, "May-26"), (6, "Jun-26"), (7, "Jul-26"), (8, "Aug-26"),
        (9, "Sep-26"), (10, "Oct-26"), (11, "Nov-26"), (12, "Dec-26"),
    ])
    def test_all_months(self, month, expected):
        assert _compute_month_label(date(2026, month, 15), None) == expected


# ── _compute_hsk_ref_id ───────────────────────────────────────────────────────
class TestComputeHskRefId:
    def test_generates_padded_ref(self):
        assert _compute_hsk_ref_id(1, "John") == "TANCL-0001"
        assert _compute_hsk_ref_id(20, "Jane") == "TANCL-0020"
        assert _compute_hsk_ref_id(100, "X") == "TANCL-0100"

    def test_none_patient_returns_none(self):
        assert _compute_hsk_ref_id(1, None) is None

    def test_empty_patient_returns_none(self):
        assert _compute_hsk_ref_id(1, "") is None


# ── Type coercion helpers ─────────────────────────────────────────────────────
class TestToDate:
    def test_datetime_object(self):
        dt = datetime(2026, 4, 5, 0, 0)
        assert _to_date(dt) == date(2026, 4, 5)

    def test_date_object(self):
        assert _to_date(date(2026, 4, 5)) == date(2026, 4, 5)

    def test_string_iso(self):
        assert _to_date("2026-04-05") == date(2026, 4, 5)

    def test_formula_string_returns_none(self):
        assert _to_date("=IF(AND(ISNUMBER(N4),ISNUMBER(O4)),O4-N4,\"\")") is None

    def test_none_returns_none(self):
        assert _to_date(None) is None

    def test_empty_string_returns_none(self):
        assert _to_date("") is None


class TestToDecimal:
    def test_integer(self):
        assert _to_decimal(71961) == Decimal("71961")

    def test_float(self):
        assert _to_decimal(1234.56) == Decimal("1234.56")

    def test_string_number(self):
        assert _to_decimal("71961") == Decimal("71961")

    def test_string_with_rupee_sign(self):
        assert _to_decimal("₹1,373,099") == Decimal("1373099")

    def test_string_with_comma(self):
        assert _to_decimal("1,373,099") == Decimal("1373099")

    def test_formula_string_returns_none(self):
        assert _to_decimal("=SUM(BI4:BI23)") is None

    def test_dash_returns_none(self):
        assert _to_decimal("-") is None

    def test_none_returns_none(self):
        assert _to_decimal(None) is None

    def test_empty_string_returns_none(self):
        assert _to_decimal("") is None

    def test_zero(self):
        assert _to_decimal(0) == Decimal("0")


class TestToBool:
    @pytest.mark.parametrize("val,expected", [
        ("Y", True), ("y", True), ("YES", True), ("yes", True),
        ("N", False), ("n", False), ("NO", False), ("no", False),
        (True, True), (False, False),
        ("TRUE", True), ("FALSE", False),
        ("1", True), ("0", False),
    ])
    def test_valid_values(self, val, expected):
        assert _to_bool(val) == expected

    def test_none_returns_none(self):
        assert _to_bool(None) is None

    def test_unknown_string_returns_none(self):
        assert _to_bool("maybe") is None


class TestToStr:
    def test_normal_string(self):
        assert _to_str("MediAssist TPA") == "MediAssist TPA"

    def test_strips_whitespace(self):
        assert _to_str("  Hassan  ") == "Hassan"

    def test_formula_string_returns_none(self):
        assert _to_str("=IF(I4=\"\",\"\",\"TANCL-\"&TEXT(ROW()-3,\"0000\"))") is None

    def test_none_returns_none(self):
        assert _to_str(None) is None

    def test_empty_string_returns_none(self):
        assert _to_str("") is None

    def test_whitespace_only_returns_none(self):
        assert _to_str("   ") is None

    def test_converts_non_string(self):
        assert _to_str(12345) == "12345"


# ── _row_hash ─────────────────────────────────────────────────────────────────
class TestRowHash:
    def test_same_row_same_hash(self):
        row = ("A", 1, date(2026, 4, 1), None)
        assert _row_hash(row) == _row_hash(row)

    def test_different_row_different_hash(self):
        row1 = ("A", 1, date(2026, 4, 1), None)
        row2 = ("A", 2, date(2026, 4, 1), None)
        assert _row_hash(row1) != _row_hash(row2)

    def test_hash_is_32_char_hex(self):
        row = ("test",)
        h = _row_hash(row)
        assert len(h) == 32
        assert all(c in "0123456789abcdef" for c in h)

    def test_none_vs_empty_string_different(self):
        assert _row_hash((None,)) != _row_hash(("",))
