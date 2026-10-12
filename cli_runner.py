"""
cli_runner.py - Headless CLI / Scheduled runner for Salary Slip Automation.
Use this script for automated cron jobs or Windows Task Scheduler execution.
"""
import argparse
import os
import sys
import datetime
import pandas as pd
from dotenv import load_dotenv

# Ensure stdout handles UTF-8 on Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from payroll_data import normalize_payroll_df, validate_payroll_df, create_sample_payroll_dataframe
from pdf_generator import generate_salary_slip_pdf
from email_service import send_salary_slip_email, verify_smtp_credentials


def main():
    load_dotenv()

    parser = argparse.ArgumentParser(description="Automated Payroll Salary Slip Dispatcher CLI")
    parser.add_argument("--file", "-f", type=str, default="sample_payroll.xlsx", help="Path to payroll spreadsheet (.xlsx or .csv)")
    parser.add_argument("--all-status", action="store_true", help="Send to all employees regardless of payment status (default: credited only)")
    parser.add_argument("--dry-run", action="store_true", help="Simulate PDF generation and logging without sending actual emails")
    parser.add_argument("--company", type=str, default=os.getenv("COMPANY_NAME", "Dexlabs AI Private Limited"))
    parser.add_argument("--test-email", type=str, default=None, help="Redirect all slips to this test email address")

    args = parser.parse_args()

    print("==================================================")
    print("Payroll Salary Slip Automation Runner")
    print(f"Time: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"File: {args.file}")
    print(f"Dry Run: {args.dry_run}")
    print("==================================================")

    # 1. Load Data
    if not os.path.exists(args.file):
        print(f"Warning: File '{args.file}' not found. Generating sample file for run...")
        df_sample = create_sample_payroll_dataframe()
        df_sample.to_excel(args.file, index=False)
        raw_df = df_sample
    else:
        if args.file.endswith(".csv"):
            raw_df = pd.read_csv(args.file)
        else:
            raw_df = pd.read_excel(args.file)

    is_valid, errors = validate_payroll_df(raw_df)
    if not is_valid:
        print("Validation errors encountered:")
        for err in errors:
            print(f"  [ERROR] {err}")
        sys.exit(1)

    df = normalize_payroll_df(raw_df)

    # Filter targets
    if not args.all_status:
        target_df = df[df["payment_status"].str.strip().str.lower() == "credited"]
        print(f"Filtered records: {len(target_df)} / {len(df)} marked as 'Credited'")
    else:
        target_df = df
        print(f"Selected all {len(target_df)} records in file.")

    if target_df.empty:
        print("No employee records to process. Exiting.")
        sys.exit(0)

    # 2. SMTP Verification (if not dry run)
    smtp_config = {
        "smtp_server": os.getenv("SMTP_SERVER", "smtp.gmail.com"),
        "smtp_port": int(os.getenv("SMTP_PORT", 587)),
        "sender_name": os.getenv("SENDER_NAME", args.company),
        "sender_email": os.getenv("SENDER_EMAIL", ""),
        "sender_password": os.getenv("SENDER_PASSWORD", "")
    }

    if not args.dry_run:
        if not smtp_config["sender_email"] or not smtp_config["sender_password"]:
            print("[ERROR] SENDER_EMAIL or SENDER_PASSWORD is not set in environment or .env file.")
            print("Please configure .env or pass credentials.")
            sys.exit(1)

        ok, msg = verify_smtp_credentials(
            smtp_config["smtp_server"],
            smtp_config["smtp_port"],
            smtp_config["sender_email"],
            smtp_config["sender_password"]
        )
        if not ok:
            print(f"[ERROR] SMTP connection failed: {msg}")
            sys.exit(1)
        print("[OK] SMTP credentials verified successfully.")

    # 3. Processing & Dispatch
    results = []
    total = len(target_df)
    print(f"\nBeginning dispatch for {total} employee(s)...")

    for i, (_, row) in enumerate(target_df.iterrows(), start=1):
        rec = row.to_dict()
        if args.test_email:
            rec["employee_email"] = args.test_email

        emp_id = rec.get("employee_id")
        emp_name = rec.get("employee_name")
        emp_email = rec.get("employee_email")

        print(f"[{i}/{total}] Processing {emp_id} - {emp_name} ({emp_email})...", end=" ")

        try:
            pdf_bytes = generate_salary_slip_pdf(rec, company_name=args.company)
            if args.dry_run:
                results.append({
                    "employee_id": emp_id,
                    "employee_name": emp_name,
                    "email": emp_email,
                    "status": "Simulated (Dry Run)",
                    "error": None
                })
                print("[SIMULATED OK]")
            else:
                res = send_salary_slip_email(
                    smtp_config=smtp_config,
                    employee_record=rec,
                    pdf_bytes=pdf_bytes,
                    company_name=args.company
                )
                if res["success"]:
                    results.append({
                        "employee_id": emp_id,
                        "employee_name": emp_name,
                        "email": emp_email,
                        "status": "Sent",
                        "error": None
                    })
                    print("[SENT OK]")
                else:
                    results.append({
                        "employee_id": emp_id,
                        "employee_name": emp_name,
                        "email": emp_email,
                        "status": "Failed",
                        "error": res["error"]
                    })
                    print(f"[FAILED] ({res['error']})")
        except Exception as e:
            results.append({
                "employee_id": emp_id,
                "employee_name": emp_name,
                "email": emp_email,
                "status": "Error",
                "error": str(e)
            })
            print(f"[ERROR] ({e})")

    # 4. Summary & Log
    log_df = pd.DataFrame(results)
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    log_filename = f"dispatch_log_{timestamp}.csv"
    log_df.to_csv(log_filename, index=False)
    success_ct = len(log_df[log_df['status'] == 'Sent']) if not args.dry_run else len(log_df)
    print(f"\nSummary: {success_ct} successful out of {total}.")
    print(f"Detailed audit log saved to: {log_filename}")


if __name__ == "__main__":
    main()
