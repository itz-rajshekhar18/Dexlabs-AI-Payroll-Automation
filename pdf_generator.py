"""
pdf_generator.py - Generates clean, professional PDF salary slips using ReportLab.
"""
import io
import os
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable, Image as RLImage
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch


def mask_account_number(acc: str) -> str:
    acc_str = str(acc).strip()
    if len(acc_str) <= 4:
        return acc_str
    return "X" * (len(acc_str) - 4) + acc_str[-4:]


def format_currency(val) -> str:
    try:
        val_float = float(val)
        return f"{val_float:,.2f}"
    except (ValueError, TypeError):
        return "0.00"


def generate_salary_slip_pdf(
    record: dict,
    company_name: str = "Dexlabs AI Private Limited",
    company_address: str = "Dexlabs AI Private Limited Campus, Tech Center",
    logo_path: str = None
) -> bytes:
    """
    Generates a PDF salary slip for a given employee record dictionary and returns bytes.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    # Auto-detect local logo.png if not provided
    if not logo_path:
        default_logo = os.path.join(os.path.dirname(__file__), "logo.png")
        if os.path.exists(default_logo):
            logo_path = default_logo

    styles = getSampleStyleSheet()

    # Custom typography styles
    company_style = ParagraphStyle(
        'CompanyHeader',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=18,
        leading=22,
        textColor=colors.HexColor('#1E293B'),
        alignment=1  # Center
    )

    sub_header_style = ParagraphStyle(
        'CompanySub',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=12,
        textColor=colors.HexColor('#64748B'),
        alignment=1  # Center
    )

    title_style = ParagraphStyle(
        'SlipTitle',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=13,
        leading=16,
        textColor=colors.HexColor('#2563EB'),
        alignment=1  # Center
    )

    cell_label_style = ParagraphStyle(
        'CellLabel',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8.5,
        leading=11,
        textColor=colors.HexColor('#475569')
    )

    cell_value_style = ParagraphStyle(
        'CellValue',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=11,
        textColor=colors.HexColor('#0F172A')
    )

    table_header_style = ParagraphStyle(
        'TableHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9,
        leading=12,
        textColor=colors.white,
        alignment=0
    )

    table_header_right_style = ParagraphStyle(
        'TableHeaderRight',
        parent=table_header_style,
        alignment=2
    )

    number_cell_style = ParagraphStyle(
        'NumberCell',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=11,
        alignment=2,
        textColor=colors.HexColor('#0F172A')
    )

    bold_number_cell_style = ParagraphStyle(
        'BoldNumberCell',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9,
        leading=12,
        alignment=2,
        textColor=colors.HexColor('#0F172A')
    )

    footer_style = ParagraphStyle(
        'FooterNotice',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=7.5,
        leading=10,
        textColor=colors.HexColor('#94A3B8'),
        alignment=1
    )

    elements = []
    pay_period = str(record.get('pay_period') or 'Current Month')

    # 1. Company Header (With Logo if available)
    if logo_path and os.path.exists(logo_path):
        logo_img = RLImage(logo_path, width=50, height=50)
        
        comp_title_style = ParagraphStyle(
            'CompanyTitleWithLogo',
            parent=styles['Heading1'],
            fontName='Helvetica-Bold',
            fontSize=15,
            leading=18,
            textColor=colors.HexColor('#1E293B')
        )
        comp_addr_style = ParagraphStyle(
            'CompanyAddrWithLogo',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=8,
            leading=11,
            textColor=colors.HexColor('#64748B')
        )
        badge_style = ParagraphStyle(
            'HeaderBadgeWithLogo',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=11,
            leading=14,
            textColor=colors.HexColor('#4338CA'),
            alignment=2
        )

        header_data = [
            [
                logo_img,
                [
                    Paragraph(company_name.upper(), comp_title_style),
                    Spacer(1, 2),
                    Paragraph(company_address, comp_addr_style)
                ],
                Paragraph(f"PAYSLIP<br/><font color='#64748B' size='8'>{pay_period.upper()}</font>", badge_style)
            ]
        ]
        header_table = Table(header_data, colWidths=[56, 330, 137])
        header_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
            ('TOPPADDING', (0, 0), (-1, -1), 0),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
        ]))
        elements.append(header_table)
        elements.append(Spacer(1, 6))
    else:
        elements.append(Paragraph(company_name.upper(), company_style))
        if company_address:
            elements.append(Spacer(1, 2))
            elements.append(Paragraph(company_address, sub_header_style))
        elements.append(Spacer(1, 6))
        elements.append(Paragraph(f"PAYSLIP FOR {pay_period.upper()}", title_style))
        elements.append(Spacer(1, 6))

    elements.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#E2E8F0'), spaceAfter=10))

    # 2. Employee Details Grid (2 columns: left employee profile, right bank/compliance details)
    masked_acc = mask_account_number(record.get('account_number', ''))
    paid_days = record.get('paid_days', 30)
    lop_days = record.get('lop_days', 0)

    emp_info_data = [
        [
            Paragraph("Employee ID", cell_label_style),
            Paragraph(f": {record.get('employee_id', '-')}", cell_value_style),
            Paragraph("Bank Name", cell_label_style),
            Paragraph(f": {record.get('bank_name', '-')}", cell_value_style),
        ],
        [
            Paragraph("Employee Name", cell_label_style),
            Paragraph(f": {record.get('employee_name', '-')}", cell_value_style),
            Paragraph("Account No.", cell_label_style),
            Paragraph(f": {masked_acc}", cell_value_style),
        ],
        [
            Paragraph("Designation", cell_label_style),
            Paragraph(f": {record.get('designation', '-')}", cell_value_style),
            Paragraph("PAN Number", cell_label_style),
            Paragraph(f": {record.get('pan_number', '-')}", cell_value_style),
        ],
        [
            Paragraph("Department", cell_label_style),
            Paragraph(f": {record.get('department', '-')}", cell_value_style),
            Paragraph("UAN / PF No.", cell_label_style),
            Paragraph(f": {record.get('uan_number', '-')}", cell_value_style),
        ],
        [
            Paragraph("Date of Joining", cell_label_style),
            Paragraph(f": {record.get('joining_date', '-')}", cell_value_style),
            Paragraph("Paid / LOP Days", cell_label_style),
            Paragraph(f": {paid_days} Days / {lop_days} LOP", cell_value_style),
        ]
    ]

    emp_table = Table(emp_info_data, colWidths=[100, 160, 100, 160])
    emp_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#F8FAFC')),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#E2E8F0')),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#F1F5F9'))
    ]))
    elements.append(emp_table)
    elements.append(Spacer(1, 14))

    # 3. Earnings & Deductions Breakdown Table
    basic = float(record.get('basic_salary') or 0.0)
    hra = float(record.get('hra') or 0.0)
    conveyance = float(record.get('conveyance_allowance') or 0.0)
    special = float(record.get('special_allowance') or 0.0)
    bonus = float(record.get('bonus_incentives') or 0.0)
    gross_earnings = basic + hra + conveyance + special + bonus

    pf = float(record.get('provident_fund') or 0.0)
    pt = float(record.get('professional_tax') or 0.0)
    tds = float(record.get('income_tax_tds') or 0.0)
    other_ded = float(record.get('other_deductions') or 0.0)
    total_deductions = pf + pt + tds + other_ded

    net_salary = gross_earnings - total_deductions

    salary_data = [
        # Table Header
        [
            Paragraph("EARNINGS", table_header_style),
            Paragraph("AMOUNT (INR)", table_header_right_style),
            Paragraph("DEDUCTIONS", table_header_style),
            Paragraph("AMOUNT (INR)", table_header_right_style),
        ],
        # Line 1
        [
            Paragraph("Basic Salary", cell_value_style),
            Paragraph(format_currency(basic), number_cell_style),
            Paragraph("Provident Fund (EPF)", cell_value_style),
            Paragraph(format_currency(pf), number_cell_style),
        ],
        # Line 2
        [
            Paragraph("House Rent Allowance (HRA)", cell_value_style),
            Paragraph(format_currency(hra), number_cell_style),
            Paragraph("Professional Tax (PT)", cell_value_style),
            Paragraph(format_currency(pt), number_cell_style),
        ],
        # Line 3
        [
            Paragraph("Conveyance Allowance", cell_value_style),
            Paragraph(format_currency(conveyance), number_cell_style),
            Paragraph("TDS / Income Tax", cell_value_style),
            Paragraph(format_currency(tds), number_cell_style),
        ],
        # Line 4
        [
            Paragraph("Special Allowance", cell_value_style),
            Paragraph(format_currency(special), number_cell_style),
            Paragraph("Other Deductions", cell_value_style),
            Paragraph(format_currency(other_ded), number_cell_style),
        ],
        # Line 5
        [
            Paragraph("Bonus & Incentives", cell_value_style),
            Paragraph(format_currency(bonus), number_cell_style),
            Paragraph("", cell_value_style),
            Paragraph("", number_cell_style),
        ],
        # Total Row
        [
            Paragraph("Gross Earnings", cell_label_style),
            Paragraph(format_currency(gross_earnings), bold_number_cell_style),
            Paragraph("Total Deductions", cell_label_style),
            Paragraph(format_currency(total_deductions), bold_number_cell_style),
        ]
    ]

    salary_table = Table(salary_data, colWidths=[160, 100, 160, 100])
    salary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1E293B')),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#F1F5F9')),
        ('LINEBELOW', (0, 0), (-1, 0), 1.5, colors.HexColor('#0F172A')),
        ('LINEABOVE', (0, -1), (-1, -1), 1, colors.HexColor('#CBD5E1')),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#CBD5E1')),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2E8F0')),
    ]))
    elements.append(salary_table)
    elements.append(Spacer(1, 14))

    # 4. Net Salary & Payment Confirmation Callout
    net_in_words = record.get('net_salary_words') or ''
    payment_status = record.get('payment_status', 'Pending').capitalize()
    payment_date = record.get('payment_date', '-')
    utr_no = record.get('utr_ref_number', '-')

    net_pay_style = ParagraphStyle(
        'NetPayTitle',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=16,
        textColor=colors.HexColor('#065F46')
    )

    net_words_style = ParagraphStyle(
        'NetPayWords',
        parent=styles['Normal'],
        fontName='Helvetica-Oblique',
        fontSize=8.5,
        leading=11,
        textColor=colors.HexColor('#047857')
    )

    credit_info_style = ParagraphStyle(
        'CreditInfo',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=11,
        textColor=colors.HexColor('#1E293B'),
        alignment=2
    )

    status_badge = f"<font color='#047857'><b>CREDITED</b></font>" if payment_status.lower() == 'credited' else f"<font color='#D97706'><b>{payment_status.upper()}</b></font>"

    net_summary_data = [
        [
            Paragraph(f"NET PAYABLE AMOUNT: Rs. {format_currency(net_salary)}", net_pay_style),
            Paragraph(f"Status: {status_badge}", credit_info_style)
        ],
        [
            Paragraph(f"Amount in Words: {net_in_words}", net_words_style),
            Paragraph(f"Payment Date: {payment_date} | UTR: {utr_no}", credit_info_style)
        ]
    ]

    net_summary_table = Table(net_summary_data, colWidths=[320, 200])
    net_summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#ECFDF5')),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#A7F3D0')),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
    ]))
    elements.append(net_summary_table)
    elements.append(Spacer(1, 24))

    # 5. Signatory & Security Disclaimer
    auth_style = ParagraphStyle(
        'AuthSign',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8.5,
        leading=11,
        textColor=colors.HexColor('#334155'),
        alignment=2
    )

    signatory_data = [
        [
            Paragraph("", cell_value_style),
            Paragraph("For " + company_name, auth_style)
        ],
        [
            Paragraph("", cell_value_style),
            Paragraph("<br/><br/><b>Authorized Signatory</b><br/>Human Resources & Finance", auth_style)
        ]
    ]
    signatory_table = Table(signatory_data, colWidths=[320, 200])
    signatory_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'BOTTOM'),
        ('TOPPADDING', (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
    ]))
    elements.append(signatory_table)
    elements.append(Spacer(1, 20))

    elements.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor('#CBD5E1'), spaceAfter=6))
    elements.append(Paragraph(
        "<i>Note: This is a system-generated document and does not require a physical signature.<br/>"
        "Confidentiality Notice: This document contains confidential payroll information intended solely for the designated employee.</i>",
        footer_style
    ))

    # Build PDF
    doc.build(elements)
    buffer.seek(0)
    return buffer.getvalue()
