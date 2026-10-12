# 💼 Automated Payroll & Salary Slip Dispatcher

An end-to-end automation system that generates PDF salary slips and automatically emails them to employees whenever their salary is credited.

---

## 🌟 Key Features

1. **Intelligent Payment Detection**:
   - Automatically filters and dispatches pay slips **only to employees whose salary status is `Credited`**, preventing premature emails for pending payments.
2. **Professional PDF Salary Slips**:
   - Generates corporate A4 salary slips using `reportlab`.
   - Includes company header, employee details, masked bank account numbers, earnings breakdown, statutory deductions (PF, PT, TDS), Net Salary in numbers and currency words (e.g., _"Rupees Seventy-Seven Thousand Only"_), and digital validity notices.
3. **Automated Gmail / Google Workspace Delivery**:
   - Connects securely via TLS with your Gmail / Google Workspace App Password.
   - Sends a responsive, beautifully styled HTML email notification with the generated PDF attached.
   - Built-in rate limiting to prevent spam flagging.
4. **Dual Modes**:
   - **Interactive Web UI (Streamlit)**: Upload payroll sheets, preview individual employee slips, test SMTP connection, track real-time dispatch progress, and download audit reports.
   - **Headless CLI / Scheduled Runner**: Can be triggered on a schedule (e.g., Windows Task Scheduler or Cron) or run on-demand.
5. **Audit Trails**:
   - Automatically logs timestamped dispatch results (Sent / Failed / Simulated) with CSV export for accounting compliance.

---

## 📁 Project Structure

```
payroll_salary_automation/
├── app.py                     # Streamlit Interactive Web Dashboard
├── pdf_generator.py           # ReportLab PDF salary slip generator
├── email_service.py           # Gmail / SMTP email composer & dispatcher
├── payroll_data.py            # Data validation, normalization & sample generator
├── cli_runner.py              # Headless CLI / Scheduled automation runner
├── sample_payroll.xlsx        # Pre-generated sample payroll dataset
├── requirements.txt           # Python dependencies
├── .env.example               # Environment variables template
└── README.md                  # Documentation
```

---

## 🚀 Quick Start Guide

### 1. Requirements & Dependencies
Ensure Python 3.10+ is installed, then install dependencies:
```bash
pip install -r requirements.txt
```

### 2. Configure Gmail SMTP (App Password)
For security, Google requires an **App Password** for automated email sending:
1. Log in to your Google Account and ensure **2-Step Verification** is turned ON.
2. Go to: [https://myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords)
3. Under **App Name**, enter `Payroll Automation` and click **Create**.
4. Google will display a 16-character password (e.g., `abcd efgh ijkl mnop`).
5. Copy this password into `.env` or input it in the Web UI sidebar.

*(Optional)* Create a `.env` file by copying `.env.example`:
```bash
copy .env.example .env
```

---

## 🖥️ Running the Interactive Web Dashboard

To launch the Streamlit dashboard:

```bash
python -m streamlit run app.py
```

The web dashboard will open in your browser (usually `http://localhost:8501`):
- **Tab 1: Payroll Data & Filtering** — Upload your `.xlsx` or `.csv` payroll file, or click **"Load Demo Payroll Data"** to test with pre-built data.
- **Tab 2: Salary Slip Preview** — Select any employee from the dropdown to review their earnings, deductions, and download/inspect the generated PDF.
- **Tab 3: Automated Email Dispatch** — Toggle Dry Run mode or launch the live automated dispatch with live progress tracking and CSV audit logs.

---

## ⚡ Running Headless via Command Line (CLI / Cron / Windows Task Scheduler)

You can run the automation headlessly without opening the browser:

### 1. Test Run (Dry Run / Simulation)
Test the entire workflow without sending real emails:
```bash
python cli_runner.py --file sample_payroll.xlsx --dry-run
```

### 2. Live Dispatch (Only Credited Employees)
Dispatches emails to all employees marked as `Credited`:
```bash
python cli_runner.py --file sample_payroll.xlsx
```

### 3. Send All Test Slips to a Single Test Email
Verify formatting in your own inbox before sending to staff:
```bash
python cli_runner.py --file sample_payroll.xlsx --test-email your-personal-email@gmail.com
```

---

## 📊 Expected Spreadsheet Format

The Excel (`.xlsx`) or `.csv` file should contain the following columns:

| Column Name | Description | Example |
| :--- | :--- | :--- |
| `employee_id` | Unique ID of employee | `EMP-1001` |
| `employee_name` | Full Name | `Aditi Sharma` |
| `employee_email` | Destination email | `aditi@example.com` |
| `designation` | Job Role | `Senior Software Engineer` |
| `department` | Department | `Engineering` |
| `bank_name` | Employee's Bank | `HDFC Bank` |
| `account_number` | Bank Account Number | `501004928172` (Auto-masked in PDF) |
| `basic_salary` | Basic Pay | `55000` |
| `hra` | House Rent Allowance | `22000` |
| `special_allowance`| Special Allowance | `18000` |
| `provident_fund` | PF deduction | `6600` |
| `professional_tax`| PT deduction | `200` |
| `income_tax_tds` | TDS deduction | `5200` |
| `payment_status` | **`Credited`** or **`Pending`** | `Credited` |
| `payment_date` | Date of credit | `2026-10-05` |
| `utr_ref_number` | Bank reference / UTR | `HDFC261005019842` |

> 💡 **Tip:** You can download a pre-formatted template with all columns and formulas directly from the Web UI!

---

## 🌐 Deployment Options

### Method 1: Streamlit Community Cloud (Easiest & Free)

1. **Initialize Git & Push to a Private GitHub Repo**:
   ```bash
   git init
   git add .
   git commit -m "Dexlabs AI Payroll Automation"
   git branch -M main
   git remote add origin https://github.com/<your-username>/dexlabs-payroll.git
   git push -u origin main
   ```
2. Go to **[share.streamlit.io](https://share.streamlit.io/)** and sign in with GitHub.
3. Click **"New app"**, select your repository, branch `main`, and main file path `app.py`.
4. In **Advanced Settings > Secrets**, paste your environment variables:
   ```toml
   COMPANY_NAME = "Dexlabs AI Private Limited"
   COMPANY_ADDRESS = "Dexlabs AI Private Limited Campus, Tech Center"
   SMTP_SERVER = "smtp.gmail.com"
   SMTP_PORT = 587
   SENDER_NAME = "Dexlabs AI Private Limited Payroll"
   SENDER_EMAIL = "dexlabsaieducation@gmail.com"
   SENDER_PASSWORD = "vutwzodagpztxywv"
   ```
5. Click **Deploy!** Your app will be live on a secure HTTPS URL.

---

### Method 2: Docker / On-Premise / VPS (Recommended for Payroll Privacy)

Since payroll contains sensitive employee financial data, running it inside your own private server or cloud VPS (AWS EC2, DigitalOcean, Azure VM, or Local Office Server) ensures total privacy:

1. Clone or copy this directory to your server.
2. Ensure Docker and Docker Compose are installed.
3. Start the container:
   ```bash
   docker compose up -d --build
   ```
4. Access your dashboard at:
   `http://<your-server-ip>:8501`

---

### Method 3: Cloud PaaS (Render / Railway)

1. Push your repository to GitHub.
2. In **Render.com** or **Railway.app**, click **New Web Service** and connect your GitHub repo.
3. Configuration:
   - **Environment:** Docker (uses the included `Dockerfile`) OR Python 3.11.
   - **Start Command:** `streamlit run app.py --server.port=$PORT --server.address=0.0.0.0`
4. Add the environment variables from your `.env` file under the service's **Environment** tab.
5. Deploy!

