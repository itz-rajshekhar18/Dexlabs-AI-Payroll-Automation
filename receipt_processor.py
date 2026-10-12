"""
receipt_processor.py - Matches and verifies salary credit receipts (bank reports & individual receipt files).
"""
import os
import re
import pandas as pd
from typing import List, Dict, Any, Tuple, Optional


def clean_acc(val: Any) -> str:
    """Standardizes account number for comparison (digits only)."""
    s = str(val or "").strip()
    digits = re.sub(r"\D", "", s)
    return digits


def clean_str(val: Any) -> str:
    """Standardizes strings (lowercase, alphanumeric)."""
    s = str(val or "").lower().strip()
    return re.sub(r"[^a-z0-9]", "", s)


def match_bank_disbursal_sheet(
    payroll_df: pd.DataFrame,
    bank_df: pd.DataFrame
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Matches corporate banking disbursal report against payroll DataFrame.
    Matches primarily on Account Number, then Employee ID, then Employee Name.
    Updates payment_status to 'Credited', utr_ref_number, and payment_date.
    """
    updated_df = payroll_df.copy()
    
    # Normalize bank columns
    bank_cols_clean = {c: str(c).strip().lower().replace(" ", "_").replace("-", "_") for c in bank_df.columns}
    b_df = bank_df.rename(columns=bank_cols_clean).copy()

    # Identify bank columns
    acc_col = next((c for c in b_df.columns if any(k in c for k in ["account", "ac_no", "acc_no", "beneficiary_acc", "credit_acc"])), None)
    utr_col = next((c for c in b_df.columns if any(k in c for k in ["utr", "ref", "rrn", "txn_id", "transaction_id", "journal_no", "cheque_no"])), None)
    date_col = next((c for c in b_df.columns if any(k in c for k in ["date", "txn_date", "value_date", "credit_date"])), None)
    status_col = next((c for c in b_df.columns if any(k in c for k in ["status", "txn_status", "result"])), None)
    name_col = next((c for c in b_df.columns if any(k in c for k in ["name", "beneficiary_name", "emp_name"])), None)
    id_col = next((c for c in b_df.columns if any(k in c for k in ["emp_id", "employee_id", "emp_code"])), None)

    matched_records = []
    unmatched_records = []

    # Build lookup dicts from bank dataframe
    bank_records = b_df.to_dict(orient="records")

    for idx, row in updated_df.iterrows():
        emp_acc = clean_acc(row.get("account_number", ""))
        emp_id = clean_str(row.get("employee_id", ""))
        emp_name = clean_str(row.get("employee_name", ""))

        matched_bank_entry = None

        for b_entry in bank_records:
            # 1. Match by account number (most reliable)
            if acc_col and emp_acc:
                b_acc = clean_acc(b_entry.get(acc_col, ""))
                if b_acc and (emp_acc == b_acc or emp_acc.endswith(b_acc) or b_acc.endswith(emp_acc)):
                    matched_bank_entry = b_entry
                    break

            # 2. Match by Employee ID
            if id_col and emp_id:
                b_id = clean_str(b_entry.get(id_col, ""))
                if b_id and emp_id == b_id:
                    matched_bank_entry = b_entry
                    break

            # 3. Match by Employee Name
            if name_col and emp_name:
                b_name = clean_str(b_entry.get(name_col, ""))
                if b_name and (emp_name in b_name or b_name in emp_name):
                    matched_bank_entry = b_entry
                    break

        if matched_bank_entry:
            # Extract UTR
            utr_val = str(matched_bank_entry.get(utr_col, "")).strip() if utr_col else ""
            if not utr_val or utr_val.lower() == "nan":
                utr_val = "BANK-CONFIRMED"

            # Extract Date
            dt_val = str(matched_bank_entry.get(date_col, "")).strip() if date_col else ""
            if not dt_val or dt_val.lower() == "nan":
                dt_val = pd.Timestamp.now().strftime("%Y-%m-%d")

            # Check status if bank has a status column
            is_success = True
            if status_col:
                b_stat = str(matched_bank_entry.get(status_col, "")).strip().lower()
                if any(neg in b_stat for neg in ["fail", "reject", "reverse", "pending"]):
                    is_success = False

            if is_success:
                updated_df.at[idx, "payment_status"] = "Credited"
                updated_df.at[idx, "utr_ref_number"] = utr_val
                updated_df.at[idx, "payment_date"] = dt_val
                matched_records.append({
                    "employee_id": row.get("employee_id"),
                    "employee_name": row.get("employee_name"),
                    "utr_ref_number": utr_val,
                    "payment_date": dt_val
                })
        else:
            unmatched_records.append({
                "employee_id": row.get("employee_id"),
                "employee_name": row.get("employee_name")
            })

    stats = {
        "total_employees": len(updated_df),
        "matched_count": len(matched_records),
        "unmatched_count": len(unmatched_records),
        "matched_records": matched_records,
        "unmatched_records": unmatched_records
    }
    return updated_df, stats


def map_individual_receipt_files(
    payroll_df: pd.DataFrame,
    uploaded_files: List[Any]
) -> Tuple[Dict[str, Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Maps uploaded receipt files (PDF/PNG/JPG) to employees by inspecting file names.
    Recognizes patterns such as:
      - EMP1001_receipt.pdf
      - Aditi_Sharma_credit.png
      - 50100492817263_transfer.pdf
    Returns (receipt_map: {emp_id: file_dict}, unmatched_files: list).
    """
    receipt_map = {}
    matched_file_names = set()

    for idx, row in payroll_df.iterrows():
        emp_id = str(row.get("employee_id", "")).strip()
        emp_name = str(row.get("employee_name", "")).strip()
        emp_acc = clean_acc(row.get("account_number", ""))

        clean_id = clean_str(emp_id)
        clean_nm = clean_str(emp_name)

        for f in uploaded_files:
            fname = f.name
            fname_clean = clean_str(fname)

            matched = False
            # Check match against ID
            if clean_id and clean_id in fname_clean:
                matched = True
            # Check match against Name
            elif clean_nm and clean_nm in fname_clean:
                matched = True
            # Check match against Account number
            elif emp_acc and emp_acc in fname_clean:
                matched = True

            if matched:
                receipt_map[emp_id] = {
                    "filename": fname,
                    "content": f.getvalue() if hasattr(f, "getvalue") else f.read(),
                    "mime_type": "application/pdf" if fname.lower().endswith(".pdf") else "image/png"
                }
                matched_file_names.add(fname)
                break

    unmatched_files = [f.name for f in uploaded_files if f.name not in matched_file_names]
    return receipt_map, unmatched_files


def create_sample_bank_disbursal_dataframe() -> pd.DataFrame:
    """
    Generates a realistic sample bank credit disbursal file from corporate netbanking.
    """
    return pd.DataFrame([
        {
            "beneficiary_account": "50100492817263",
            "beneficiary_name": "Aditi Sharma",
            "emp_id": "EMP-1001",
            "amount_credited": 91000.0,
            "utr_number": "CMS261012901842",
            "value_date": "2026-10-12",
            "transfer_status": "Success"
        },
        {
            "beneficiary_account": "002901582914",
            "beneficiary_name": "Rahul Verma",
            "emp_id": "EMP-1002",
            "amount_credited": 97000.0,
            "utr_number": "CMS261012901843",
            "value_date": "2026-10-12",
            "transfer_status": "Success"
        },
        {
            "beneficiary_account": "38291049281",
            "beneficiary_name": "Priya Nair",
            "emp_id": "EMP-1003",
            "amount_credited": 68900.0,
            "utr_number": "CMS261012901844",
            "value_date": "2026-10-12",
            "transfer_status": "Success"
        }
    ])
