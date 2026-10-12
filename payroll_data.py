"""
payroll_data.py - Payroll data loading, validation, and sample data generator.
"""
import io
import pandas as pd
from typing import Tuple, List, Dict, Any

# Standard expected columns
REQUIRED_COLUMNS = [
    "employee_id",
    "employee_name",
    "employee_email",
    "designation",
    "department",
    "bank_name",
    "account_number",
    "basic_salary",
    "payment_status"
]

OPTIONAL_COLUMNS = [
    "joining_date",
    "pan_number",
    "uan_number",
    "pay_period",
    "paid_days",
    "lop_days",
    "hra",
    "conveyance_allowance",
    "special_allowance",
    "bonus_incentives",
    "provident_fund",
    "professional_tax",
    "income_tax_tds",
    "other_deductions",
    "payment_date",
    "utr_ref_number"
]


def number_to_words(number: int or float) -> str:
    """
    Converts a number to Indian numbering system words (Lakhs, Thousands, Hundreds).
    """
    try:
        n = int(round(float(number)))
    except (ValueError, TypeError):
        return ""

    if n == 0:
        return "Zero Rupees Only"

    units = ["", "One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine",
             "Ten", "Eleven", "Twelve", "Thirteen", "Fourteen", "Fifteen", "Sixteen",
             "Seventeen", "Eighteen", "Nineteen"]
    tens = ["", "", "Twenty", "Thirty", "Forty", "Fifty", "Sixty", "Seventy", "Eighty", "Ninety"]

    def convert_two_digits(val: int) -> str:
        if val < 20:
            return units[val]
        else:
            return tens[val // 10] + (" " + units[val % 10] if val % 10 != 0 else "")

    def convert_three_digits(val: int) -> str:
        hundred = val // 100
        rest = val % 100
        res = ""
        if hundred > 0:
            res += units[hundred] + " Hundred"
            if rest > 0:
                res += " and "
        if rest > 0:
            res += convert_two_digits(rest)
        return res

    parts = []
    crores = n // 10000000
    n %= 10000000

    lakhs = n // 100000
    n %= 100000

    thousands = n // 1000
    n %= 1000

    if crores > 0:
        parts.append(convert_two_digits(crores) + " Crore")
    if lakhs > 0:
        parts.append(convert_two_digits(lakhs) + " Lakh")
    if thousands > 0:
        parts.append(convert_two_digits(thousands) + " Thousand")
    if n > 0:
        parts.append(convert_three_digits(n))

    result = " ".join(parts).strip()
    return f"Rupees {result} Only" if result else "Zero Rupees Only"


def create_sample_payroll_dataframe() -> pd.DataFrame:
    """
    Creates a realistic mock payroll DataFrame with Indian corporate structure.
    """
    sample_records = [
        {
            "employee_id": "EMP-1001",
            "employee_name": "Aditi Sharma",
            "employee_email": "aditi.sharma.test@gmail.com",
            "designation": "Senior Software Engineer",
            "department": "Engineering",
            "joining_date": "2022-03-15",
            "bank_name": "HDFC Bank",
            "account_number": "50100492817263",
            "pan_number": "ABCPS1234D",
            "uan_number": "101928374650",
            "pay_period": "October 2026",
            "paid_days": 30,
            "lop_days": 0,
            "basic_salary": 55000.0,
            "hra": 22000.0,
            "conveyance_allowance": 3000.0,
            "special_allowance": 18000.0,
            "bonus_incentives": 5000.0,
            "provident_fund": 6600.0,
            "professional_tax": 200.0,
            "income_tax_tds": 5200.0,
            "other_deductions": 0.0,
            "payment_status": "Credited",
            "payment_date": "2026-10-05",
            "utr_ref_number": "HDFC261005019842"
        },
        {
            "employee_id": "EMP-1002",
            "employee_name": "Rahul Verma",
            "employee_email": "rahul.verma.test@gmail.com",
            "designation": "Product Manager",
            "department": "Product",
            "joining_date": "2021-07-01",
            "bank_name": "ICICI Bank",
            "account_number": "002901582914",
            "pan_number": "BTYPV9876E",
            "uan_number": "101837462910",
            "pay_period": "October 2026",
            "paid_days": 29,
            "lop_days": 1,
            "basic_salary": 65000.0,
            "hra": 26000.0,
            "conveyance_allowance": 3000.0,
            "special_allowance": 21000.0,
            "bonus_incentives": 0.0,
            "provident_fund": 7800.0,
            "professional_tax": 200.0,
            "income_tax_tds": 7500.0,
            "other_deductions": 500.0,
            "payment_status": "Credited",
            "payment_date": "2026-10-05",
            "utr_ref_number": "ICIC261005084921"
        },
        {
            "employee_id": "EMP-1003",
            "employee_name": "Priya Nair",
            "employee_email": "priya.nair.test@gmail.com",
            "designation": "UX Designer",
            "department": "Design",
            "joining_date": "2023-01-10",
            "bank_name": "State Bank of India",
            "account_number": "38291049281",
            "pan_number": "CFRPN4567G",
            "uan_number": "101746291038",
            "pay_period": "October 2026",
            "paid_days": 30,
            "lop_days": 0,
            "basic_salary": 45000.0,
            "hra": 18000.0,
            "conveyance_allowance": 2500.0,
            "special_allowance": 12000.0,
            "bonus_incentives": 2000.0,
            "provident_fund": 5400.0,
            "professional_tax": 200.0,
            "income_tax_tds": 3200.0,
            "other_deductions": 0.0,
            "payment_status": "Credited",
            "payment_date": "2026-10-05",
            "utr_ref_number": "SBIN261005118492"
        },
        {
            "employee_id": "EMP-1004",
            "employee_name": "Karan Mehta",
            "employee_email": "karan.mehta.test@gmail.com",
            "designation": "QA Automation Engineer",
            "department": "Quality Assurance",
            "joining_date": "2023-09-20",
            "bank_name": "Axis Bank",
            "account_number": "91801004829104",
            "pan_number": "DMOPK8765H",
            "uan_number": "101948271039",
            "pay_period": "October 2026",
            "paid_days": 30,
            "lop_days": 0,
            "basic_salary": 40000.0,
            "hra": 16000.0,
            "conveyance_allowance": 2000.0,
            "special_allowance": 10000.0,
            "bonus_incentives": 0.0,
            "provident_fund": 4800.0,
            "professional_tax": 200.0,
            "income_tax_tds": 2500.0,
            "other_deductions": 0.0,
            "payment_status": "Pending",  # Notice: Pending payment
            "payment_date": "",
            "utr_ref_number": ""
        }
    ]
    return pd.DataFrame(sample_records)


def normalize_payroll_df(df: pd.DataFrame) -> pd.DataFrame:
    """
    Cleans column headers and fills defaults for missing optional columns.
    """
    df = df.copy()
    # Normalize column names: lowercase, strip, replace spaces/dashes with underscores
    df.columns = [str(c).strip().lower().replace(" ", "_").replace("-", "_") for c in df.columns]

    # Numeric columns to ensure float
    num_cols = [
        "basic_salary", "hra", "conveyance_allowance", "special_allowance",
        "bonus_incentives", "provident_fund", "professional_tax",
        "income_tax_tds", "other_deductions"
    ]
    for col in num_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0)
        else:
            df[col] = 0.0

    # Ensure string columns
    str_cols = [
        "employee_id", "employee_name", "employee_email", "designation",
        "department", "bank_name", "account_number", "pan_number",
        "uan_number", "pay_period", "payment_status", "payment_date",
        "utr_ref_number", "joining_date"
    ]
    for col in str_cols:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip().replace("nan", "")
        else:
            df[col] = ""

    # Day count defaults
    if "paid_days" in df.columns:
        df["paid_days"] = pd.to_numeric(df["paid_days"], errors="coerce").fillna(30).astype(int)
    else:
        df["paid_days"] = 30

    if "lop_days" in df.columns:
        df["lop_days"] = pd.to_numeric(df["lop_days"], errors="coerce").fillna(0).astype(int)
    else:
        df["lop_days"] = 0

    # Computed fields
    df["gross_earnings"] = (
        df["basic_salary"] + df["hra"] + df["conveyance_allowance"] +
        df["special_allowance"] + df["bonus_incentives"]
    )
    df["total_deductions"] = (
        df["provident_fund"] + df["professional_tax"] +
        df["income_tax_tds"] + df["other_deductions"]
    )
    df["net_salary"] = df["gross_earnings"] - df["total_deductions"]

    # Net in words
    df["net_salary_words"] = df["net_salary"].apply(number_to_words)

    return df


def validate_payroll_df(df: pd.DataFrame) -> Tuple[bool, List[str]]:
    """
    Validates that necessary columns exist and email values are present.
    Returns (is_valid, list_of_error_messages).
    """
    errors = []
    normalized_cols = [str(c).strip().lower().replace(" ", "_").replace("-", "_") for c in df.columns]

    missing = [col for col in REQUIRED_COLUMNS if col not in normalized_cols]
    if missing:
        errors.append(f"Missing required columns in uploaded file: {', '.join(missing)}")

    # Check for empty emails if column exists
    if "employee_email" in normalized_cols:
        email_idx = normalized_cols.index("employee_email")
        orig_col = df.columns[email_idx]
        invalid_emails = df[df[orig_col].isna() | (df[orig_col].astype(str).str.strip() == "")]
        if not invalid_emails.empty:
            errors.append(f"Found {len(invalid_emails)} row(s) with missing or empty employee email addresses.")

    return (len(errors) == 0, errors)


def export_template_to_bytes() -> bytes:
    """
    Returns an Excel file as bytes with sample records and headers.
    """
    df = create_sample_payroll_dataframe()
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Payroll_Data")
    return output.getvalue()
