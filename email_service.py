"""
email_service.py - Handles SMTP email composition, PDF attachment, and delivery via Gmail/Google Workspace.
"""
import smtplib
import ssl
import time
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from typing import Dict, Any, Tuple


DEFAULT_HTML_TEMPLATE = """<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <style>
    body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; color: #1e293b; line-height: 1.6; margin: 0; padding: 20px; background-color: #f8fafc; }
    .card { max-width: 600px; margin: 0 auto; background: #ffffff; border-radius: 8px; border: 1px solid #e2e8f0; overflow: hidden; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05); }
    .header { background: #1e293b; color: #ffffff; padding: 24px; text-align: center; }
    .header h1 { margin: 0 0 6px 0; font-size: 20px; font-weight: 600; }
    .header p { margin: 0; font-size: 13px; color: #94a3b8; }
    .content { padding: 28px 24px; }
    .greeting { font-size: 16px; font-weight: 600; color: #0f172a; margin-bottom: 12px; }
    .box { background: #f0fdf4; border: 1px solid #bbf7d0; border-radius: 6px; padding: 16px; margin: 20px 0; }
    .box-title { font-size: 12px; text-transform: uppercase; color: #166534; font-weight: 700; margin-bottom: 6px; }
    .box-amount { font-size: 22px; font-weight: 700; color: #15803d; }
    .meta-table { width: 100%; border-collapse: collapse; margin-top: 10px; font-size: 13px; }
    .meta-table td { padding: 4px 0; }
    .meta-label { color: #64748b; width: 140px; }
    .meta-val { font-weight: 600; color: #1e293b; }
    .footer { padding: 18px 24px; background: #f1f5f9; text-align: center; font-size: 12px; color: #64748b; border-top: 1px solid #e2e8f0; }
  </style>
</head>
<body>
  <div class="card">
    <div class="header">
      <h1>{company_name}</h1>
      <p>Salary Disbursal & Payslip Notification</p>
    </div>
    <div class="content">
      <div class="greeting">Dear {employee_name},</div>
      <p>We are pleased to inform you that your salary for <strong>{pay_period}</strong> has been credited to your registered bank account.</p>
      
      <div class="box">
        <div class="box-title">Net Salary Credited</div>
        <div class="box-amount">₹ {net_salary}</div>
        <table class="meta-table">
          <tr><td class="meta-label">Payment Status:</td><td class="meta-val" style="color: #16a34a;">Credited</td></tr>
          <tr><td class="meta-label">Payment Date:</td><td class="meta-val">{payment_date}</td></tr>
          <tr><td class="meta-label">Bank & Account:</td><td class="meta-val">{bank_name} ({account_number})</td></tr>
          <tr><td class="meta-label">Transaction / UTR:</td><td class="meta-val">{utr_ref_number}</td></tr>
        </table>
      </div>

      <p>Your detailed salary slip is attached to this email as a PDF document for your records and income tax filings.</p>
      
      <p style="margin-top: 24px; font-size: 13px; color: #475569;">
        If you have any queries regarding your pay computation, allowances, or deductions, please reach out to the HR / Finance team.
      </p>

      <p style="margin-top: 20px; font-size: 13px; color: #334155;">
        Warm regards,<br/>
        <strong>Human Resources & Payroll Team</strong><br/>
        {company_name}
      </p>
    </div>
    <div class="footer">
      This is an automated system email. Please do not reply directly to this message.
    </div>
  </div>
</body>
</html>
"""


def verify_smtp_credentials(smtp_server: str, smtp_port: int, sender_email: str, sender_password: str) -> Tuple[bool, str]:
    """
    Tests SMTP connection and authentication.
    Returns (success: bool, message: str).
    """
    if not sender_email or not sender_password:
        return False, "Sender email and password/app password cannot be empty."

    sender_email = sender_email.strip()
    sender_password = sender_password.strip().replace(" ", "")

    try:
        context = ssl.create_default_context()
        if int(smtp_port) == 465:
            server = smtplib.SMTP_SSL(smtp_server, smtp_port, context=context, timeout=15)
        else:
            server = smtplib.SMTP(smtp_server, smtp_port, timeout=15)
            server.ehlo()
            server.starttls(context=context)
            server.ehlo()

        server.login(sender_email, sender_password)
        server.quit()
        return True, "SMTP connection and authentication successful!"
    except smtplib.SMTPAuthenticationError as auth_err:
        err_str = str(auth_err)
        return False, (
            "Authentication failed: Google/Gmail requires an 'App Password' instead of your regular password.\n"
            "Steps to generate:\n"
            "1. Go to https://myaccount.google.com/apppasswords\n"
            "2. Ensure 2-Step Verification is turned ON.\n"
            "3. Under 'App name', enter 'Payroll Automation' and click 'Create'.\n"
            "4. Copy the 16-character code generated by Google (e.g., abcd efgh ijkl mnop) and use it as your password."
        )
    except smtplib.SMTPServerDisconnected as disc_err:
        if "gmail.com" in smtp_server.lower():
            return False, (
                "Google SMTP server disconnected: Gmail rejected the regular password. "
                "Google requires a 16-character 'App Password' for automated applications.\n"
                "To get one:\n"
                "1. Go to https://myaccount.google.com/apppasswords (log into dexlabsaieducation@gmail.com)\n"
                "2. Create an App Password named 'Payroll'\n"
                "3. Use the 16-character password provided by Google."
            )
        return False, f"Server disconnected unexpectedly: {disc_err}"
    except smtplib.SMTPConnectError as conn_err:
        return False, f"Could not connect to {smtp_server}:{smtp_port} - {conn_err}"
    except Exception as e:
        return False, f"SMTP Connection error: {str(e)}"


def send_salary_slip_email(
    smtp_config: dict,
    employee_record: dict,
    pdf_bytes: bytes,
    company_name: str = "Acme Technologies Pvt. Ltd.",
    custom_subject: str = None,
    custom_body_html: str = None,
    receipt_attachment: dict = None
) -> Dict[str, Any]:
    """
    Dispatches a single salary slip email with PDF attachment.
    """
    emp_email = str(employee_record.get("employee_email", "")).strip()
    emp_name = str(employee_record.get("employee_name", "Employee")).strip()
    emp_id = str(employee_record.get("employee_id", "EMP")).strip()
    pay_period = str(employee_record.get("pay_period", "Current Month")).strip()
    net_val = employee_record.get("net_salary", 0.0)
    net_formatted = f"{float(net_val):,.2f}" if net_val else "0.00"

    if not emp_email or "@" not in emp_email:
        return {
            "success": False,
            "error": f"Invalid recipient email: '{emp_email}'",
            "employee_id": emp_id,
            "employee_name": emp_name,
            "email": emp_email
        }

    # Email body and subject replacements
    masked_acc = str(employee_record.get("account_number", ""))
    if len(masked_acc) > 4:
        masked_acc = "•••• " + masked_acc[-4:]

    replacements = {
        "{company_name}": str(company_name),
        "{employee_name}": str(emp_name),
        "{employee_id}": str(emp_id),
        "{pay_period}": str(pay_period),
        "{net_salary}": str(net_formatted),
        "{payment_date}": str(employee_record.get("payment_date") or "N/A"),
        "{bank_name}": str(employee_record.get("bank_name") or "Bank"),
        "{account_number}": str(masked_acc),
        "{utr_ref_number}": str(employee_record.get("utr_ref_number") or "N/A")
    }

    # Subject line
    if custom_subject:
        subject = custom_subject
        for k, v in replacements.items():
            subject = subject.replace(k, v)
    else:
        subject = f"Salary Slip for {pay_period} - {company_name}"

    template = custom_body_html if custom_body_html else DEFAULT_HTML_TEMPLATE
    body_html = template
    for k, v in replacements.items():
        body_html = body_html.replace(k, v)

    msg = MIMEMultipart("mixed")
    msg["From"] = f"{smtp_config.get('sender_name', company_name)} <{smtp_config['sender_email']}>"
    msg["To"] = emp_email
    msg["Subject"] = subject

    # Body part
    body_part = MIMEText(body_html, "html", "utf-8")
    msg.attach(body_part)

    # Attach Generated Salary Slip PDF
    safe_period = pay_period.replace(" ", "_").replace("/", "-")
    pdf_filename = f"Salary_Slip_{emp_id}_{safe_period}.pdf"
    attachment = MIMEApplication(pdf_bytes, _subtype="pdf")
    attachment.add_header("Content-Disposition", "attachment", filename=pdf_filename)
    msg.attach(attachment)

    # Optional: Attach Uploaded Bank Salary Credit Receipt if present
    if receipt_attachment and "content" in receipt_attachment:
        r_fname = receipt_attachment.get("filename", f"Bank_Receipt_{emp_id}.pdf")
        r_content = receipt_attachment["content"]
        r_attach = MIMEApplication(r_content)
        r_attach.add_header("Content-Disposition", "attachment", filename=r_fname)
        msg.attach(r_attach)

    try:
        context = ssl.create_default_context()
        smtp_port = int(smtp_config.get("smtp_port", 587))
        smtp_server = smtp_config.get("smtp_server", "smtp.gmail.com")
        sender_email = smtp_config.get("sender_email")
        sender_password = smtp_config.get("sender_password").replace(" ", "")

        if smtp_port == 465:
            server = smtplib.SMTP_SSL(smtp_server, smtp_port, context=context, timeout=20)
        else:
            server = smtplib.SMTP(smtp_server, smtp_port, timeout=20)
            server.ehlo()
            server.starttls(context=context)
            server.ehlo()

        server.login(sender_email, sender_password)
        server.send_message(msg)
        server.quit()

        # Slight pause to avoid aggressive throttling
        time.sleep(0.5)

        return {
            "success": True,
            "error": None,
            "employee_id": emp_id,
            "employee_name": emp_name,
            "email": emp_email
        }
    except (smtplib.SMTPAuthenticationError, smtplib.SMTPServerDisconnected) as e:
        err_msg = "Google requires a 16-character App Password (https://myaccount.google.com/apppasswords)." if "gmail" in smtp_server.lower() else str(e)
        return {
            "success": False,
            "error": f"Authentication failed: {err_msg}",
            "employee_id": emp_id,
            "employee_name": emp_name,
            "email": emp_email
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "employee_id": emp_id,
            "employee_name": emp_name,
            "email": emp_email
        }
