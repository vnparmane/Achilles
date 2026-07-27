from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    HRFlowable,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)
from sqlalchemy import select

from src.database.models.company import Company
from src.database.models.invoice import SalesInvoice

NUMBER_WORDS = {
    0: "Zero", 1: "One", 2: "Two", 3: "Three", 4: "Four",
    5: "Five", 6: "Six", 7: "Seven", 8: "Eight", 9: "Nine",
    10: "Ten", 11: "Eleven", 12: "Twelve", 13: "Thirteen",
    14: "Fourteen", 15: "Fifteen", 16: "Sixteen", 17: "Seventeen",
    18: "Eighteen", 19: "Nineteen", 20: "Twenty", 30: "Thirty",
    40: "Forty", 50: "Fifty", 60: "Sixty", 70: "Seventy",
    80: "Eighty", 90: "Ninety",
}


def _num_to_words(n: float) -> str:
    if n == 0:
        return "Zero Rupees Only"
    whole = int(n)
    frac = round((n - whole) * 100)

    def _convert(num: int) -> str:
        if num < 20:
            return NUMBER_WORDS.get(num, "")
        if num < 100:
            tens = num // 10 * 10
            rem = num % 10
            return NUMBER_WORDS[tens] + (" " + NUMBER_WORDS[rem] if rem else "")
        if num < 1000:
            h = num // 100
            rem = num % 100
            return NUMBER_WORDS[h] + " Hundred" + (" " + _convert(rem) if rem else "")
        if num < 100000:
            t = num // 1000
            rem = num % 1000
            return _convert(t) + " Thousand" + (" " + _convert(rem) if rem else "")
        if num < 10000000:
            lk = num // 100000
            rem = num % 100000
            return _convert(lk) + " Lakh" + (" " + _convert(rem) if rem else "")
        c = num // 10000000
        rem = num % 10000000
        return _convert(c) + " Crore" + (" " + _convert(rem) if rem else "")

    result = _convert(whole) + " Rupees"
    if frac > 0:
        result += " and " + _convert(frac) + " Paise"
    result += " Only"
    return result


def _build_company_header(company, style_center):
    rows = [
        [Paragraph(f"<b>{company.name}</b>", ParagraphStyle("co_name", fontSize=16, alignment=TA_CENTER, spaceAfter=2))],
        [Paragraph(f"GSTIN: {company.gstin or 'N/A'} | {company.address or ''}", style_center)],
        [Paragraph(f"Phone: {company.phone or ''} | Email: {company.email or ''}", style_center)],
    ]
    if company.bank_name:
        rows.append([Paragraph(
            f"Bank: {company.bank_name}, {company.bank_branch} | A/c: {company.bank_account_no} | IFSC: {company.bank_ifsc}",
            style_center,
        )])
    tbl = Table(rows, colWidths=[170*mm])
    tbl.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 0.5, colors.black),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    return [tbl, Spacer(1, 4*mm)]


def _build_info_section(invoice, customer, style_normal, style_right):
    rows = [
        [
            Paragraph(f"<b>Invoice No:</b> {invoice.invoice_no}", style_normal),
            Paragraph(f"<b>Date:</b> {invoice.invoice_date}", style_right),
        ],
        [
            Paragraph(f"<b>Customer:</b> {customer.name}", style_normal),
            Paragraph(f"<b>GSTIN:</b> {customer.gstin or 'N/A'}", style_right),
        ],
        [
            Paragraph(f"<b>Address:</b> {customer.address or ''}", style_normal),
            Paragraph(f"<b>State:</b> {customer.state or ''} ({customer.state_code or ''})", style_right),
        ],
    ]
    if invoice.transport:
        rows.append([
            Paragraph(f"<b>Transport:</b> {invoice.transport}", style_normal),
            Paragraph("", style_normal),
        ])
    tbl = Table(rows, colWidths=[100*mm, 70*mm])
    tbl.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 0.5, colors.black),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
        ("TOPPADDING", (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
    ]))
    return [tbl, Spacer(1, 4*mm)]


def _build_items_table(invoice):
    header = ["#", "Item (HSN)", "Qty", "Rate", "Taxable", "CGST", "SGST", "IGST", "Total"]
    data = [header]
    for idx, item in enumerate(invoice.items, 1):
        data.append([
            str(idx),
            f"{item.item.name if item.item else ''}\n({item.hsn_code or ''})",
            f"{item.quantity:.3f}",
            f"{item.rate:.2f}",
            f"{item.taxable:.2f}",
            f"{item.cgst:.2f}" if item.cgst else "-",
            f"{item.sgst:.2f}" if item.sgst else "-",
            f"{item.igst:.2f}" if item.igst else "-",
            f"{item.total:.2f}",
        ])
    data.append(["", "", "", "", f"{invoice.taxable_amount:.2f}", f"{invoice.cgst_total:.2f}", f"{invoice.sgst_total:.2f}", f"{invoice.igst_total:.2f}", f"{invoice.grand_total:.2f}"])
    col_widths = [8*mm, 50*mm, 20*mm, 20*mm, 22*mm, 18*mm, 18*mm, 18*mm, 22*mm]
    tbl = Table(data, colWidths=col_widths)
    tbl.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 0.5, colors.black),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2c3e50")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 8),
        ("FONTSIZE", (0, 1), (-1, -1), 8),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("ALIGN", (1, 0), (1, -1), "LEFT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#f0f0f0")),
        ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
    ]))
    return [tbl, Spacer(1, 3*mm)]


def _build_tax_summary(invoice):
    header = ["Tax Summary", "Rate", "Taxable", "CGST", "SGST", "IGST", "Total Tax"]
    rows = [header]
    for item in invoice.items:
        rows.append([
            f"{item.gst_rate}%",
            f"{item.gst_rate}%",
            f"{item.taxable:.2f}",
            f"{item.cgst:.2f}" if item.cgst else "-",
            f"{item.sgst:.2f}" if item.sgst else "-",
            f"{item.igst:.2f}" if item.igst else "-",
            f"{item.cgst + item.sgst + item.igst:.2f}",
        ])
    rows.append([
        "Total", "", f"{invoice.taxable_amount:.2f}",
        f"{invoice.cgst_total:.2f}", f"{invoice.sgst_total:.2f}",
        f"{invoice.igst_total:.2f}",
        f"{invoice.cgst_total + invoice.sgst_total + invoice.igst_total:.2f}",
    ])
    tbl = Table(rows, colWidths=[30*mm, 20*mm, 25*mm, 20*mm, 20*mm, 20*mm, 25*mm])
    tbl.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 0.5, colors.black),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2c3e50")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("TOPPADDING", (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#f0f0f0")),
        ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
    ]))
    return [tbl, Spacer(1, 6*mm)]


def _build_bank_details(company, style_normal, style_bold):
    if not company.bank_name:
        return []
    rows = [
        [Paragraph("<b>Bank Details:</b>", style_bold)],
        [Paragraph(
            f"{company.bank_name}, {company.bank_branch or ''} | "
            f"A/c: {company.bank_account_no or ''} | IFSC: {company.bank_ifsc or ''}",
            style_normal,
        )],
    ]
    tbl = Table(rows, colWidths=[170*mm])
    tbl.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 0.5, colors.black),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
    ]))
    return [tbl, Spacer(1, 4*mm)]


def _build_footer():
    terms_sig = Table([
        [
            Paragraph("<b>Terms & Conditions:</b><br/>1. Goods once sold will not be taken back.<br/>2. Interest @ 18% p.a. on overdue payments.", ParagraphStyle("terms", fontSize=8)),
            Paragraph("<br/><br/><br/>Authorised Signatory<br/>________________", ParagraphStyle("sig", fontSize=9, alignment=TA_RIGHT)),
        ]
    ], colWidths=[100*mm, 70*mm])
    terms_sig.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 0.5, colors.black),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
    ]))
    hr = HRFlowable(width="100%", color=colors.grey)
    gen_by = Paragraph(
        f"Generated by TextileERP on {datetime.now().date().isoformat()}",
        ParagraphStyle("footer", fontSize=7, alignment=TA_CENTER, textColor=colors.grey),
    )
    return [terms_sig, Spacer(1, 4*mm), hr, gen_by]


def generate_invoice_pdf(
    session,
    invoice_id: int,
    output_path: str,
):
    invoice = session.get(SalesInvoice, invoice_id)
    if invoice is None:
        raise ValueError(f"Invoice {invoice_id} not found")

    company = session.scalar(select(Company))
    if company is None:
        company = Company(name="Your Company")

    customer = invoice.party

    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        topMargin=15*mm,
        bottomMargin=15*mm,
        leftMargin=12*mm,
        rightMargin=12*mm,
    )

    styles = getSampleStyleSheet()
    style_normal = styles["Normal"]
    style_right = ParagraphStyle("right", parent=style_normal, alignment=TA_RIGHT)
    style_center = ParagraphStyle("center", parent=style_normal, alignment=TA_CENTER)
    style_bold = ParagraphStyle("bold", parent=style_normal, fontName="Helvetica-Bold")

    elements = []
    elements.extend(_build_company_header(company, style_center))
    elements.append(Paragraph("<b>TAX INVOICE</b>", ParagraphStyle("inv_title", fontSize=14, alignment=TA_CENTER, spaceAfter=6)))
    elements.append(Spacer(1, 2*mm))
    elements.extend(_build_info_section(invoice, customer, style_normal, style_right))
    elements.extend(_build_items_table(invoice))
    elements.append(Paragraph(f"<b>Amount in Words:</b> {_num_to_words(invoice.grand_total)}", ParagraphStyle("words", fontSize=9, spaceAfter=6)))
    elements.extend(_build_tax_summary(invoice))
    elements.extend(_build_bank_details(company, style_normal, style_bold))
    elements.extend(_build_footer())

    doc.build(elements)
    return output_path
