"""
app.py - Streamlit Web Dashboard for Payroll Salary Slip Automation with Bank Credit Receipts Processing.
"""
import streamlit as st
import pandas as pd
import os
import io
from dotenv import load_dotenv

from payroll_data import (
    create_sample_payroll_dataframe,
    normalize_payroll_df,
    validate_payroll_df,
    export_template_to_bytes
)
from pdf_generator import generate_salary_slip_pdf
from email_service import (
    verify_smtp_credentials,
    send_salary_slip_email,
    DEFAULT_HTML_TEMPLATE
)
from receipt_processor import (
    match_bank_disbursal_sheet,
    map_individual_receipt_files,
    create_sample_bank_disbursal_dataframe
)

# Load environment variables
load_dotenv()

st.set_page_config(
    page_title="DexLabs Payroll & Salary Slip Automation",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Polished UI styles
st.markdown("""
<style>
    .main-header {
        font-size: 26px;
        font-weight: 700;
        color: #1E293B;
        margin-bottom: 4px;
    }
    .sub-header {
        font-size: 14px;
        color: #64748B;
        margin-bottom: 20px;
    }
    .metric-card {
        background-color: #F8FAFC;
        border-radius: 8px;
        padding: 14px 18px;
        border: 1px solid #E2E8F0;
    }
    .metric-val {
        font-size: 22px;
        font-weight: 700;
        color: #0F172A;
    }
    .metric-lbl {
        font-size: 12px;
        color: #64748B;
        text-transform: uppercase;
        font-weight: 600;
    }
    .stButton>button {
        border-radius: 6px;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

# ---------------- SIDEBAR CONFIGURATION ----------------
with st.sidebar:
    if os.path.exists("logo.png"):
        st.image("logo.png", width=72)
    st.header("⚙️ Configuration")
    
    with st.expander("🏢 Company Information", expanded=True):
        company_name = st.text_input("Company Name", value=os.getenv("COMPANY_NAME", "Dexlabs AI Private Limited"))
        company_address = st.text_input(
            "Company Address / Campus",
            value=os.getenv("COMPANY_ADDRESS", "Dexlabs AI Private Limited Campus, Tech Center")
        )

    with st.expander("✉️ Gmail / SMTP Settings", expanded=True):
        st.caption("Send payslips directly via your Gmail or Google Workspace account.")
        smtp_server = st.text_input("SMTP Server", value="smtp.gmail.com")
        smtp_port = st.number_input("SMTP Port", value=587, min_value=1, max_value=65535)
        sender_name = st.text_input("Sender Display Name", value=os.getenv("SENDER_NAME", "Dexlabs AI Private Limited Payroll"))
        sender_email = st.text_input(
            "Sender Email (Gmail)",
            value=os.getenv("SENDER_EMAIL", "dexlabsaieducation@gmail.com")
        )
        sender_password = st.text_input(
            "Gmail App Password",
            value=os.getenv("SENDER_PASSWORD", ""),
            type="password",
            help="16-character Google App Password (not your regular Gmail password)."
        )

        st.markdown("""
        <small style='color: #64748B;'>
        💡 <b>How to get a Gmail App Password:</b><br/>
        1. Ensure 2-Step Verification is ON in Google Account.<br/>
        2. Visit <a href="https://myaccount.google.com/apppasswords" target="_blank">Google App Passwords</a>.<br/>
        3. Create an app password named 'Payroll' & paste here.
        </small>
        """, unsafe_allow_html=True)

        if st.button("🔌 Test SMTP Handshake", use_container_width=True):
            if not sender_email or not sender_password:
                st.warning("Please enter your sender email and 16-character App Password.")
            else:
                with st.spinner("Verifying SMTP handshake with Google..."):
                    success, msg = verify_smtp_credentials(smtp_server, int(smtp_port), sender_email, sender_password)
                    if success:
                        st.success(f"✅ {msg}")
                    else:
                        st.error(f"❌ {msg}")

    with st.expander("📝 Email Template Customization", expanded=False):
        subject_template = st.text_input(
            "Subject Line Template",
            value="Salary Slip for {pay_period} - {company_name}"
        )
        st.caption("Placeholders: `{employee_name}`, `{employee_id}`, `{pay_period}`, `{net_salary}`, `{company_name}`")
        custom_body = st.text_area(
            "HTML Body Template",
            value=DEFAULT_HTML_TEMPLATE,
            height=200,
            help="Leave as default or customize HTML with placeholder variables."
        )


# ---------------- SESSION STATE ----------------
if "payroll_df" not in st.session_state:
    st.session_state.payroll_df = None
if "receipt_map" not in st.session_state:
    st.session_state.receipt_map = {}
if "bank_match_stats" not in st.session_state:
    st.session_state.bank_match_stats = None


# ---------------- MAIN CONTENT ----------------
col_head_logo, col_head_txt = st.columns([1, 11])
with col_head_logo:
    if os.path.exists("logo.png"):
        st.image("logo.png", width=62)
with col_head_txt:
    st.markdown(f"<div class='main-header'>💼 {company_name} - Payroll Automation</div>", unsafe_allow_html=True)
    st.markdown("<div class='sub-header'>Upload payroll sheets, match salary credit receipts / bank transfer reports, and automatically dispatch PDF salary slips.</div>", unsafe_allow_html=True)

tab1, tab2, tab3, tab4 = st.tabs([
    "1. 📊 Payroll Master Data",
    "2. 🏦 Bank Credit Receipts (Trigger)",
    "3. 📄 Salary Slip Preview",
    "4. 🚀 Automated Email Dispatch"
])


# ==================== TAB 1: PAYROLL MASTER DATA ====================
with tab1:
    col_upload, col_actions = st.columns([2, 1])

    with col_upload:
        uploaded_file = st.file_uploader(
            "Upload Employee Payroll / Salary Breakdown Sheet (.xlsx, .csv)",
            type=["xlsx", "xls", "csv"],
            key="payroll_uploader"
        )

    with col_actions:
        st.write("**Quick Actions:**")
        template_bytes = export_template_to_bytes()
        st.download_button(
            label="📥 Download Sample Payroll Excel",
            data=template_bytes,
            file_name="payroll_sample_template.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )

        if st.button("🧪 Load Demo Payroll Data", use_container_width=True):
            st.session_state.payroll_df = normalize_payroll_df(create_sample_payroll_dataframe())
            st.success("Loaded 4 employee records with Indian salary structure!")

    if uploaded_file is not None:
        try:
            if uploaded_file.name.endswith(".csv"):
                raw_df = pd.read_csv(uploaded_file)
            else:
                raw_df = pd.read_excel(uploaded_file)

            is_valid, validation_errors = validate_payroll_df(raw_df)
            if not is_valid:
                for err in validation_errors:
                    st.error(f"Validation Warning: {err}")
            
            st.session_state.payroll_df = normalize_payroll_df(raw_df)
            st.success(f"Successfully loaded '{uploaded_file.name}' with {len(st.session_state.payroll_df)} employee records!")
        except Exception as e:
            st.error(f"Error parsing file: {e}")

    if st.session_state.payroll_df is not None:
        df = st.session_state.payroll_df
        credited_mask = df["payment_status"].str.strip().str.lower() == "credited"
        
        m1, m2, m3, m4 = st.columns(4)
        with m1:
            st.markdown(f"<div class='metric-card'><div class='metric-lbl'>Total Employees</div><div class='metric-val'>{len(df)}</div></div>", unsafe_allow_html=True)
        with m2:
            st.markdown(f"<div class='metric-card'><div class='metric-lbl'>Status: Credited</div><div class='metric-val' style='color:#16a34a;'>{int(credited_mask.sum())}</div></div>", unsafe_allow_html=True)
        with m3:
            st.markdown(f"<div class='metric-card'><div class='metric-lbl'>Status: Pending</div><div class='metric-val' style='color:#d97706;'>{len(df) - int(credited_mask.sum())}</div></div>", unsafe_allow_html=True)
        with m4:
            st.markdown(f"<div class='metric-card'><div class='metric-lbl'>Total Net Payout</div><div class='metric-val'>Rs. {df['net_salary'].sum():,.2f}</div></div>", unsafe_allow_html=True)

        st.markdown("### 📋 Employee Master Records")
        display_columns = [
            "employee_id", "employee_name", "employee_email", "designation",
            "department", "bank_name", "account_number", "gross_earnings", "total_deductions",
            "net_salary", "payment_status", "payment_date", "utr_ref_number"
        ]
        available_cols = [c for c in display_columns if c in df.columns]
        st.dataframe(df[available_cols], use_container_width=True, height=260)
    else:
        st.info("👋 Upload your payroll sheet above or click 'Load Demo Payroll Data' to begin.")


# ==================== TAB 2: BANK CREDIT RECEIPTS (TRIGGER) ====================
with tab2:
    st.markdown("### 🏦 Upload Salary Credited Receipts & Bank Transfer Confirmation")
    st.markdown(
        "Upload your corporate bank credit reports or individual payment receipts. "
        "The system will automatically match each transfer, update the payment status to **`Credited`**, "
        "and record the **Bank UTR Number & Date**."
    )

    if st.session_state.payroll_df is None:
        st.warning("Please upload or load payroll data in Tab 1 first.")
    else:
        r_type = st.radio(
            "Select Receipt Input Type:",
            [
                "Option A: Corporate Banking Disbursal / Settlement Sheet (.xlsx or .csv)",
                "Option B: Individual Transfer Receipts / Screenshots / PDFs (multiple files)"
            ],
            index=0
        )

        # OPTION A: BANK BULK DISBURSAL SHEET
        if "Option A" in r_type:
            col_b1, col_b2 = st.columns([2, 1])
            with col_b1:
                bank_file = st.file_uploader(
                    "Upload Bank Disbursal / Transfer Report",
                    type=["xlsx", "xls", "csv"],
                    key="bank_file_uploader",
                    help="Upload report downloaded from netbanking (containing Account Number, UTR, and Status)."
                )
            with col_b2:
                st.write("**Testing Utility:**")
                sample_bank_df = create_sample_bank_disbursal_dataframe()
                buf = io.BytesIO()
                sample_bank_df.to_excel(buf, index=False)
                st.download_button(
                    label="📥 Download Sample Bank Report",
                    data=buf.getvalue(),
                    file_name="sample_bank_disbursal_report.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )
                if st.button("⚡ Simulate Bank Disbursal Report", use_container_width=True):
                    up_df, stats = match_bank_disbursal_sheet(st.session_state.payroll_df, sample_bank_df)
                    st.session_state.payroll_df = up_df
                    st.session_state.bank_match_stats = stats
                    st.success(f"Matched {stats['matched_count']} employees with bank credit receipts!")

            if bank_file is not None:
                try:
                    if bank_file.name.endswith(".csv"):
                        b_raw_df = pd.read_csv(bank_file)
                    else:
                        b_raw_df = pd.read_excel(bank_file)

                    up_df, stats = match_bank_disbursal_sheet(st.session_state.payroll_df, b_raw_df)
                    st.session_state.payroll_df = up_df
                    st.session_state.bank_match_stats = stats
                    st.success(f"Matched & Verified {stats['matched_count']} employees out of {stats['total_employees']}!")
                except Exception as e:
                    st.error(f"Error parsing bank file: {e}")

        # OPTION B: INDIVIDUAL FILES
        else:
            multi_receipts = st.file_uploader(
                "Upload Transfer Receipts (PDFs, Images, Screenshots)",
                type=["pdf", "png", "jpg", "jpeg"],
                accept_multiple_files=True,
                key="multi_receipts_uploader",
                help="Files named after Employee ID (e.g. EMP-1001_receipt.pdf) or Name/Account will be auto-matched!"
            )
            if multi_receipts:
                receipt_map, unmatched_fnames = map_individual_receipt_files(st.session_state.payroll_df, multi_receipts)
                st.session_state.receipt_map = receipt_map
                
                # Mark matched employees as Credited
                df = st.session_state.payroll_df.copy()
                for emp_id in receipt_map:
                    mask = df["employee_id"] == emp_id
                    df.loc[mask, "payment_status"] = "Credited"
                    if not df.loc[mask, "payment_date"].values[0]:
                        df.loc[mask, "payment_date"] = pd.Timestamp.now().strftime("%Y-%m-%d")
                    if not df.loc[mask, "utr_ref_number"].values[0]:
                        df.loc[mask, "utr_ref_number"] = f"RECEIPT-{emp_id}"
                st.session_state.payroll_df = df

                st.success(f"Successfully matched {len(receipt_map)} receipt file(s) to employees!")
                if unmatched_fnames:
                    st.warning(f"Unmatched receipt files (naming did not match any employee): {', '.join(unmatched_fnames)}")

        # Verification Status Card
        if st.session_state.bank_match_stats or st.session_state.receipt_map:
            st.markdown("#### ✅ Verification & Credit Status Summary")
            df = st.session_state.payroll_df
            matched_view = df[["employee_id", "employee_name", "account_number", "payment_status", "payment_date", "utr_ref_number"]]
            st.dataframe(matched_view, use_container_width=True)


# ==================== TAB 3: SALARY SLIP PREVIEW ====================
with tab3:
    st.markdown("### 📄 Preview Employee Salary Slip with Credit Confirmation")
    if st.session_state.payroll_df is None or len(st.session_state.payroll_df) == 0:
        st.warning("Please upload payroll data in Tab 1 first.")
    else:
        df = st.session_state.payroll_df
        emp_options = df.apply(lambda r: f"{r['employee_id']} - {r['employee_name']} [{r['payment_status']}]", axis=1).tolist()
        
        selected_emp_label = st.selectbox("Select Employee to Preview:", emp_options)
        selected_idx = emp_options.index(selected_emp_label)
        record = df.iloc[selected_idx].to_dict()

        col_details, col_pdf = st.columns([1, 1])
        with col_details:
            st.markdown(f"#### 👤 {record.get('employee_name')} (`{record.get('employee_id')}`)")
            st.write(f"**Email:** `{record.get('employee_email')}`")
            st.write(f"**Designation:** {record.get('designation')} | **Dept:** {record.get('department')}")
            st.write(f"**Bank:** {record.get('bank_name')} | **Account:** `{record.get('account_number')}`")
            st.write(f"**Pay Period:** {record.get('pay_period')}")
            
            p_status = str(record.get('payment_status', 'Pending'))
            status_color = "green" if p_status.lower() == "credited" else "orange"
            st.markdown(f"**Payment Status:** :{status_color}[**{p_status.upper()}**]")
            if p_status.lower() == "credited":
                st.write(f"**Payment Date:** {record.get('payment_date')} | **UTR:** `{record.get('utr_ref_number')}`")

            # Check if receipt attached
            emp_id = record.get('employee_id')
            if emp_id in st.session_state.receipt_map:
                st.info(f"📎 Bank Receipt Attached: `{st.session_state.receipt_map[emp_id]['filename']}`")

            st.divider()
            c1, c2 = st.columns(2)
            with c1:
                st.write("**Earnings:**")
                st.write(f"- Basic: Rs. {float(record.get('basic_salary', 0)):,.2f}")
                st.write(f"- HRA: Rs. {float(record.get('hra', 0)):,.2f}")
                st.write(f"- Special: Rs. {float(record.get('special_allowance', 0)):,.2f}")
                st.write(f"- Bonus: Rs. {float(record.get('bonus_incentives', 0)):,.2f}")
                st.markdown(f"**Gross: Rs. {float(record.get('gross_earnings', 0)):,.2f}**")
            with c2:
                st.write("**Deductions:**")
                st.write(f"- PF: Rs. {float(record.get('provident_fund', 0)):,.2f}")
                st.write(f"- PT: Rs. {float(record.get('professional_tax', 0)):,.2f}")
                st.write(f"- TDS: Rs. {float(record.get('income_tax_tds', 0)):,.2f}")
                st.markdown(f"**Total Ded: Rs. {float(record.get('total_deductions', 0)):,.2f}**")

            st.success(f"**Net Payable:** Rs. {float(record.get('net_salary', 0)):,.2f}")
            st.caption(f"_{record.get('net_salary_words')}_")

        with col_pdf:
            pdf_bytes = generate_salary_slip_pdf(record, company_name=company_name, company_address=company_address)
            st.markdown("#### 📑 Generated PDF Salary Slip")
            st.download_button(
                label=f"💾 Download Pay Slip ({record.get('employee_id')}.pdf)",
                data=pdf_bytes,
                file_name=f"Salary_Slip_{record.get('employee_id')}.pdf",
                mime="application/pdf",
                use_container_width=True
            )
            st.caption("PDF size: " + f"{len(pdf_bytes):,} bytes" + " | Standard A4 corporate layout.")


# ==================== TAB 4: AUTOMATED EMAIL DISPATCH ====================
with tab4:
    st.markdown("### 🚀 Automated Email Dispatch Engine")
    if st.session_state.payroll_df is None or len(st.session_state.payroll_df) == 0:
        st.warning("Please upload payroll data in Tab 1 before launching automation.")
    else:
        df = st.session_state.payroll_df
        credited_df = df[df["payment_status"].str.strip().str.lower() == "credited"]
        
        st.write("Configure the criteria for salary slip dispatch:")
        
        send_scope = st.radio(
            "Select Target Recipients:",
            [
                "Only employees with verified 'Credited' status (Recommended - skips uncredited/pending)",
                "All employees in sheet (including Pending)",
                "Send Test Email to a specific address"
            ],
            index=0
        )

        test_override_email = None
        if "Test Email to a specific address" in send_scope:
            test_override_email = st.text_input("Enter recipient email for testing:", value=sender_email)

        attach_receipts = st.checkbox(
            "Also attach uploaded Bank Credit Receipts in email (if available)",
            value=True if len(st.session_state.receipt_map) > 0 else False
        )

        is_dry_run = st.checkbox(
            "Dry Run Mode (Simulate dispatch without sending real emails)",
            value=False,
            help="Generates PDFs and validates records without contacting Gmail SMTP server."
        )

        if "Only employees with verified 'Credited'" in send_scope:
            target_df = credited_df
        elif "Test Email" in send_scope:
            target_df = df.head(1).copy()
            if test_override_email:
                target_df["employee_email"] = test_override_email
        else:
            target_df = df

        st.info(f"Target count: **{len(target_df)} employee(s)** queued for salary slip delivery.")

        if st.button("🚀 Start Email Automation Now", type="primary", use_container_width=True):
            if not is_dry_run and (not sender_email or not sender_password):
                st.error("Please configure your Gmail sender email and App Password in the sidebar first.")
            elif len(target_df) == 0:
                st.warning("No employees match the selected criteria (make sure salary status is 'Credited').")
            else:
                smtp_config = {
                    "smtp_server": smtp_server,
                    "smtp_port": smtp_port,
                    "sender_name": sender_name,
                    "sender_email": sender_email,
                    "sender_password": sender_password
                }

                progress_bar = st.progress(0)
                status_text = st.empty()
                results = []
                total = len(target_df)

                for idx, (_, row) in enumerate(target_df.iterrows()):
                    rec = row.to_dict()
                    emp_name = rec.get("employee_name", "Employee")
                    emp_id = rec.get("employee_id", "EMP")
                    emp_email = rec.get("employee_email", "")

                    status_text.text(f"Processing ({idx+1}/{total}): Generating pay slip and emailing {emp_name} ({emp_email})...")
                    
                    try:
                        # 1. Generate PDF
                        pdf_data = generate_salary_slip_pdf(
                            rec,
                            company_name=company_name,
                            company_address=company_address
                        )

                        # 2. Check for attached receipt
                        receipt_attach = None
                        if attach_receipts and emp_id in st.session_state.receipt_map:
                            receipt_attach = st.session_state.receipt_map[emp_id]

                        # 3. Dispatch Email
                        if is_dry_run:
                            res = {
                                "success": True,
                                "error": "Dry run (simulated)",
                                "employee_id": emp_id,
                                "employee_name": emp_name,
                                "email": emp_email,
                                "receipt_attached": receipt_attach is not None
                            }
                        else:
                            res = send_salary_slip_email(
                                smtp_config=smtp_config,
                                employee_record=rec,
                                pdf_bytes=pdf_data,
                                company_name=company_name,
                                custom_subject=subject_template,
                                custom_body_html=custom_body,
                                receipt_attachment=receipt_attach
                            )
                            res["receipt_attached"] = receipt_attach is not None
                        results.append(res)
                    except Exception as exc:
                        results.append({
                            "success": False,
                            "error": str(exc),
                            "employee_id": emp_id,
                            "employee_name": emp_name,
                            "email": emp_email,
                            "receipt_attached": False
                        })

                    progress_bar.progress((idx + 1) / total)

                status_text.text("Dispatch Completed!")
                
                # Report summary
                report_df = pd.DataFrame(results)
                success_count = (report_df["success"] == True).sum()
                fail_count = len(report_df) - success_count

                if fail_count == 0:
                    st.success(f"🎉 All {success_count} salary slips were processed and sent successfully!")
                else:
                    st.warning(f"Completed: {success_count} sent, {fail_count} failed.")

                st.markdown("#### 📜 Dispatch Audit Log")
                st.dataframe(report_df, use_container_width=True)

                csv_bytes = report_df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="📥 Download Dispatch Report (CSV)",
                    data=csv_bytes,
                    file_name="payroll_dispatch_report.csv",
                    mime="text/csv"
                )
