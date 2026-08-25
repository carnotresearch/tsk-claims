"""
Generate a multi-hospital demo Excel workbook compatible with the HSK Claims Tracker parser.

Usage:
    python scripts/generate_demo_excel.py --out uploads/latest.xlsx

The generated file contains:
  - 3 hospitals, ~8 claims each (24 rows total)
  - Mix of TPA, Insurance, Govt payer types
  - Mix of statuses (Paid, Pending, Query, Denied)
"""
from __future__ import annotations

import argparse
import os
import sys
from datetime import date, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import openpyxl
from openpyxl import Workbook


# ── Hospitals ─────────────────────────────────────────────────────────────────
HOSPITALS = [
    {"name": "Tanya Speciality Hospital", "location": "Hassan", "rohini_id": "RHN-10001"},
    {"name": "Apex Multi Speciality Hospital", "location": "Bengaluru", "rohini_id": "RHN-10002"},
    {"name": "Grace Medical Centre", "location": "Mysuru", "rohini_id": "RHN-10003"},
]

# ── Column headers (row 3) ────────────────────────────────────────────────────
HEADERS = [
    "HSK Ref ID", "Month", "IHX Ref ID", "Hospital Name", "Location", "Rohini ID",
    "UHID", "IP Number", "Patient Name", "Patient Contact", "Insured Name",
    "Employee Code", "Corporate Name", "Date of Admission", "Date of Discharge",
    "LOS Days", "Procedure Name", "Diagnosis", "Payer Type", "TPA Name",
    "Insurer Name", "Policy No", "Policy Type", "Preauth No", "Initial Claim No",
    "Preauth Request Date", "Preauth Approval Date", "Preauth Requested Amt",
    "Preauth Approved Amt", "Preauth Copay", "Preauth Status", "Preauth TAT",
    "Final Bill Request Date", "Final Bill Approval Date", "Final Claimed Amt",
    "Final Bill Approved Amt", "Hospital Discount", "Patient Paid Amt",
    "Discharge Status", "Discharge TAT", "Submission Type", "Submission Date",
    "Submission TAT", "Submission Status", "Courier Agency", "Courier Destination",
    "Courier Dispatch Date", "Courier AWB", "Hospital Invoice No",
    "Query Raised", "Query Raised Date", "Query Reason", "Query Response Date",
    "Query Resolution TAT", "Resubmission Date", "Disallowed Amt", "Denial Reason",
    "Appeal Filed", "Appeal Date", "Settlement Date", "Settled Amt", "TDS Amt",
    "Deduction Amt", "UTR No", "UTR Date", "Payment Received Date",
    "Payment Received Amt", "Payment Mode", "Hospital Receipt No", "Payment TAT",
    "Outstanding Amt", "Ageing Days", "Ageing Bucket", "Final Claim Status",
    "Insurer Comments", "Hospital Remarks", "Updated By", "Last Updated Date",
    "Variance",
]

_d = date  # shorthand


def _dt(base: date, delta: int) -> date:
    return base + timedelta(days=delta)


# ── Per-hospital claim templates ───────────────────────────────────────────────

def _claims_for(h: dict, start_idx: int) -> list[list]:
    """Return 8 rows of demo claims for one hospital."""
    hn = h["name"]
    loc = h["location"]
    rid = h["rohini_id"]

    base = date(2025, 1, 15)  # anchor date for claim 1

    rows = []

    # Claim 1 — TPA, Paid
    adm = _dt(base, 0)
    dis = _dt(base, 5)
    rows.append([
        f"TANCL-{start_idx:04d}", adm.strftime("%b-%y"), f"IHX{start_idx:05d}",
        hn, loc, rid, f"UHID{start_idx:04d}", f"IP{start_idx:04d}",
        "Ramesh Kumar", "9876543210", "Ramesh Kumar", None, None,
        adm, dis, None, "Appendectomy", "Appendicitis",
        "TPA", "Medi Assist", "Star Health Insurance", f"POL{start_idx:06d}", "Individual",
        f"PA{start_idx:05d}", None, _dt(adm, -2), _dt(adm, -1), 85000, 78000, 0, "Approved", None,
        dis, _dt(dis, 1), 92000, 78000, 5000, 9000, "Paid", None,
        "Physical", _dt(dis, 3), None, "Submitted", "BlueDart", loc, _dt(dis, 3), f"AWB{start_idx:07d}", f"INV{start_idx:04d}",
        "N", None, None, None, None, None, None, None, None, None,
        _dt(dis, 30), 78000, 390, None, f"UTR{start_idx:08d}", _dt(dis, 30),
        _dt(dis, 30), 78000, "NEFT", f"REC{start_idx:04d}", None,
        None, None, None, "Paid", None, None, "Admin", _dt(dis, 31),
        None,
    ])

    # Claim 2 — Insurance, Pending settlement
    adm = _dt(base, 20)
    dis = _dt(base, 25)
    rows.append([
        f"TANCL-{start_idx+1:04d}", adm.strftime("%b-%y"), f"IHX{start_idx+1:05d}",
        hn, loc, rid, f"UHID{start_idx+1:04d}", f"IP{start_idx+1:04d}",
        "Surekha Devi", "9845001122", "Surekha Devi", None, None,
        adm, dis, None, "Knee Replacement", "Osteoarthritis",
        "Insurance", None, "HDFC ERGO", f"POL{start_idx+1:06d}", "Individual",
        f"PA{start_idx+1:05d}", None, _dt(adm, -3), _dt(adm, -1), 150000, 135000, 0, "Approved", None,
        dis, _dt(dis, 2), 162000, 135000, 8000, 11000, "Paid", None,
        "Physical", _dt(dis, 5), None, "Submitted", "DTDC", loc, _dt(dis, 5), f"AWB{start_idx+1:07d}", f"INV{start_idx+1:04d}",
        "N", None, None, None, None, None, None, None, None, None,
        None, None, None, None, None, None,
        None, None, None, None, None,
        None, None, None, "Pending Settlement", None, "Awaiting settlement", "Admin", date(2025, 3, 10),
        None,
    ])

    # Claim 3 — Government scheme, Query raised
    adm = _dt(base, 40)
    dis = _dt(base, 43)
    rows.append([
        f"TANCL-{start_idx+2:04d}", adm.strftime("%b-%y"), f"IHX{start_idx+2:05d}",
        hn, loc, rid, f"UHID{start_idx+2:04d}", f"IP{start_idx+2:04d}",
        "Manju Patil", "9900112233", "Manju Patil", None, None,
        adm, dis, None, "Cataract Surgery", "Cataract",
        "Govt Scheme", None, "Ayushman Bharat", None, "Government",
        f"PA{start_idx+2:05d}", None, _dt(adm, -1), _dt(adm, 0), 45000, 40000, 0, "Approved", None,
        dis, _dt(dis, 1), 48000, 40000, 0, 0, "Paid", None,
        "Online", _dt(dis, 2), None, "Submitted", None, None, None, None, f"INV{start_idx+2:04d}",
        "Y", _dt(dis, 15), "Missing documents", None, None, None, None, None, None, None,
        None, None, None, None, None, None,
        None, None, None, None, None,
        None, None, None, "Query", "Awaiting patient records", None, "Admin", date(2025, 4, 1),
        None,
    ])

    # Claim 4 — Corporate, Paid
    adm = _dt(base, 60)
    dis = _dt(base, 63)
    rows.append([
        f"TANCL-{start_idx+3:04d}", adm.strftime("%b-%y"), f"IHX{start_idx+3:05d}",
        hn, loc, rid, f"UHID{start_idx+3:04d}", f"IP{start_idx+3:04d}",
        "Anil Nayak", "9811223344", "Anil Nayak", "EMP12345", "Infosys Ltd",
        adm, dis, None, "Hernia Repair", "Inguinal Hernia",
        "Corporate", "Vipul MedCorp", "New India Assurance", f"POL{start_idx+3:06d}", "Group",
        f"PA{start_idx+3:05d}", None, _dt(adm, -2), _dt(adm, -1), 55000, 52000, 0, "Approved", None,
        dis, _dt(dis, 1), 58000, 52000, 3000, 6000, "Paid", None,
        "Online", _dt(dis, 3), None, "Submitted", None, None, None, None, f"INV{start_idx+3:04d}",
        "N", None, None, None, None, None, None, None, None, None,
        _dt(dis, 28), 52000, 260, None, f"UTR{start_idx+3:08d}", _dt(dis, 28),
        _dt(dis, 28), 52000, "NEFT", f"REC{start_idx+3:04d}", None,
        None, None, None, "Paid", None, None, "Admin", _dt(dis, 29),
        None,
    ])

    # Claim 5 — TPA, Denied
    adm = _dt(base, 80)
    dis = _dt(base, 82)
    rows.append([
        f"TANCL-{start_idx+4:04d}", adm.strftime("%b-%y"), f"IHX{start_idx+4:05d}",
        hn, loc, rid, f"UHID{start_idx+4:04d}", f"IP{start_idx+4:04d}",
        "Priya Sharma", "9822334455", "Priya Sharma", None, None,
        adm, dis, None, "LSCS", "Pregnancy",
        "TPA", "Paramount", "United India Insurance", f"POL{start_idx+4:06d}", "Individual",
        f"PA{start_idx+4:05d}", None, _dt(adm, -1), _dt(adm, 0), 70000, 65000, 0, "Approved", None,
        dis, _dt(dis, 1), 72000, 65000, 0, 0, "Paid", None,
        "Physical", _dt(dis, 4), None, "Submitted", "Delhivery", loc, _dt(dis, 4), f"AWB{start_idx+4:07d}", f"INV{start_idx+4:04d}",
        "Y", _dt(dis, 20), "Pre-existing condition not covered", _dt(dis, 35), None, None, 65000, "Pre-existing exclusion", "N", None,
        None, None, None, None, None, None,
        None, None, None, None, None,
        None, None, None, "Denied", "Pre-existing exclusion applied", "Will appeal", "Admin", date(2025, 5, 15),
        None,
    ])

    # Claim 6 — Insurance, Pending Submission
    adm = _dt(base, 100)
    dis = _dt(base, 105)
    rows.append([
        f"TANCL-{start_idx+5:04d}", adm.strftime("%b-%y"), f"IHX{start_idx+5:05d}",
        hn, loc, rid, f"UHID{start_idx+5:04d}", f"IP{start_idx+5:04d}",
        "Deepak Rao", "9833445566", "Deepak Rao", None, None,
        adm, dis, None, "CABG", "Coronary Artery Disease",
        "Insurance", None, "Bajaj Allianz", f"POL{start_idx+5:06d}", "Individual",
        f"PA{start_idx+5:05d}", None, _dt(adm, -5), _dt(adm, -3), 250000, 230000, 0, "Approved", None,
        dis, _dt(dis, 2), 265000, 230000, 10000, 20000, "Paid", None,
        "Physical", None, None, "Pending Submission", None, None, None, None, f"INV{start_idx+5:04d}",
        "N", None, None, None, None, None, None, None, None, None,
        None, None, None, None, None, None,
        None, None, None, None, None,
        None, None, None, "Pending Submission", None, None, "Admin", date(2025, 6, 5),
        None,
    ])

    # Claim 7 — Govt, Paid with partial deduction
    adm = _dt(base, 120)
    dis = _dt(base, 122)
    rows.append([
        f"TANCL-{start_idx+6:04d}", adm.strftime("%b-%y"), f"IHX{start_idx+6:05d}",
        hn, loc, rid, f"UHID{start_idx+6:04d}", f"IP{start_idx+6:04d}",
        "Kavitha Murthy", "9844556677", "Kavitha Murthy", None, None,
        adm, dis, None, "Hysterectomy", "Uterine Fibroids",
        "Govt Scheme", None, "Karnataka Arogya Bhagya", None, "Government",
        f"PA{start_idx+6:05d}", None, _dt(adm, -2), _dt(adm, -1), 60000, 55000, 0, "Approved", None,
        dis, _dt(dis, 1), 62000, 55000, 0, 0, "Paid", None,
        "Online", _dt(dis, 3), None, "Submitted", None, None, None, None, f"INV{start_idx+6:04d}",
        "N", None, None, None, None, None, None, None, None, None,
        _dt(dis, 35), 50000, 250, 5000, f"UTR{start_idx+6:08d}", _dt(dis, 35),
        _dt(dis, 35), 50000, "RTGS", f"REC{start_idx+6:04d}", None,
        None, None, None, "Paid", "₹5000 deducted - inadmissible charges", None, "Admin", _dt(dis, 36),
        None,
    ])

    # Claim 8 — Corporate, Under Query
    adm = _dt(base, 140)
    dis = _dt(base, 147)
    rows.append([
        f"TANCL-{start_idx+7:04d}", adm.strftime("%b-%y"), f"IHX{start_idx+7:05d}",
        hn, loc, rid, f"UHID{start_idx+7:04d}", f"IP{start_idx+7:04d}",
        "Sanjay Hegde", "9855667788", "Sanjay Hegde", "EMP67890", "TCS Ltd",
        adm, dis, None, "Spinal Fusion", "Lumbar Disc Disease",
        "Corporate", "Health India TPA", "Reliance General", f"POL{start_idx+7:06d}", "Group",
        f"PA{start_idx+7:05d}", None, _dt(adm, -4), _dt(adm, -2), 320000, 295000, 0, "Approved", None,
        dis, _dt(dis, 2), 335000, 295000, 15000, 20000, "Paid", None,
        "Online", _dt(dis, 5), None, "Submitted", None, None, None, None, f"INV{start_idx+7:04d}",
        "Y", _dt(dis, 18), "Implant invoice required", None, None, None, None, None, None, None,
        None, None, None, None, None, None,
        None, None, None, None, None,
        None, None, None, "Query", "Awaiting implant invoice", None, "Admin", date(2025, 7, 20),
        None,
    ])

    return rows


def generate_workbook(out_path: str) -> None:
    wb = Workbook()
    ws = wb.active
    ws.title = "ClaimsMaster"

    # Row 1: section headers (placeholder)
    ws.append(["HSK Cashless Claims Tracker"] + [""] * (len(HEADERS) - 1))
    # Row 2: totals row (blank)
    ws.append([""] * len(HEADERS))
    # Row 3: column headers
    ws.append(HEADERS)

    # Data rows (rows 4+)
    row_start_idx = 1
    for h in HOSPITALS:
        for row in _claims_for(h, row_start_idx):
            ws.append(row)
        row_start_idx += 8

    # Add Lookups sheet (minimal — parser tolerates missing values)
    lk = wb.create_sheet("Lookups")
    lk.append(["Payer Type", "TPA Names", "Insurance Companies", "Insurer Code",
                "Govt Schemes", "Corporate Sources", "Preauth Status", "Discharge Status",
                "Submission Status", "Claim Status", "Payment Mode", "Ageing Buckets",
                "Yes/No", "Policy Type", "Query Reasons", "Disallowed Reasons",
                "Submission Type", "Users"])
    lk.append([""] * 18)  # spacer
    lookups = [
        ["TPA", "Medi Assist", "Star Health Insurance", "STAR", "Ayushman Bharat", "Infosys Ltd",
         "Approved", "Paid", "Submitted", "Paid", "NEFT", "0-30", "Y", "Individual",
         "Missing documents", "Pre-existing exclusion", "Physical", "admin"],
        ["Insurance", "Paramount", "HDFC ERGO", "HDFC", "Karnataka Arogya Bhagya", "TCS Ltd",
         "Pending", "Pending", "Pending Submission", "Pending Settlement", "RTGS", "31-60", "N", "Group",
         "Implant invoice required", "Inadmissible charges", "Online", ""],
        ["Corporate", "Vipul MedCorp", "New India Assurance", "NIA", "", "",
         "Rejected", "Discharged", "Query", "Query", "Cash", "61-90", "", "",
         "Pre-existing condition not covered", "Policy lapsed", "", ""],
        ["Govt Scheme", "Health India TPA", "United India Insurance", "UII", "", "",
         "", "", "Denied", "Denied", "Cheque", "90+", "", "",
         "TDS query", "Document mismatch", "", ""],
        ["", "Vidal Health", "Bajaj Allianz", "BAJA", "", "",
         "", "", "", "", "DD", "", "", "",
         "Amount mismatch", "Treatment not covered", "", ""],
        ["", "", "Reliance General", "RGI", "", "", "", "", "", "", "", "", "", "", "", "", "", ""],
    ]
    for lk_row in lookups:
        lk.append(lk_row)

    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    wb.save(out_path)
    print(f"Demo Excel saved → {out_path}  ({len(HOSPITALS) * 8} rows, {len(HOSPITALS)} hospitals)")


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate demo HSK Excel workbook")
    parser.add_argument("--out", default="uploads/latest.xlsx", help="Output path for .xlsx file")
    args = parser.parse_args()
    generate_workbook(args.out)


if __name__ == "__main__":
    main()
