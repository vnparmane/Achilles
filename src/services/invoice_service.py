from datetime import date

from sqlalchemy import select, func
from sqlalchemy.orm import Session

from src.database.models.invoice import SalesInvoice, SalesInvoiceItem
from src.database.models.party import Party
from src.database.models.company import Company
from src.services.stock_service import StockService
from src.utils.gst_utils import calculate_gst


class InvoiceService:
    def __init__(self, session: Session):
        self.session = session
        self.stock_service = StockService(session)

    def _next_invoice_no(self) -> str:
        year = date.today().year % 100
        result = self.session.execute(
            select(func.max(SalesInvoice.invoice_no)).where(
                SalesInvoice.invoice_no.like(f"INV-{year}%")
            )
        ).scalar()
        if result is None:
            return f"INV-{year}-0001"
        last_num = int(result.split("-")[-1])
        return f"INV-{year}-{last_num + 1:04d}"

    def create_invoice(
        self,
        party_id: int,
        godown_id: int,
        items: list[dict],
        invoice_date: str | None = None,
        discount_amount: float = 0.0,
        transport: str | None = None,
        notes: str | None = None,
        created_by: int | None = None,
    ) -> SalesInvoice:
        if invoice_date is None:
            invoice_date = date.today().isoformat()

        party = self.session.get(Party, party_id)
        company = self.session.scalar(select(Company))

        invoice_no = self._next_invoice_no()
        invoice = SalesInvoice(
            invoice_no=invoice_no,
            invoice_date=invoice_date,
            party_id=party_id,
            godown_id=godown_id,
            transport=transport,
            discount_amount=discount_amount,
            notes=notes,
            status="confirmed",
        )
        self.session.add(invoice)
        self.session.flush()

        gross = 0.0
        taxable = 0.0
        cgst_total = 0.0
        sgst_total = 0.0
        igst_total = 0.0

        for item_data in items:
            qty = item_data["quantity"]
            rate = item_data["rate"]
            gst_rate = item_data["gst_rate"]
            amount = round(qty * rate, 2)
            discount = item_data.get("discount", 0.0)
            item_taxable = round(amount - discount, 2)
            gross += amount
            taxable += item_taxable

            tax = calculate_gst(
                item_taxable, gst_rate,
                company.state_code if company else None,
                party.state_code if party else None,
            )
            cgst_total += tax["cgst"]
            sgst_total += tax["sgst"]
            igst_total += tax["igst"]

            item = SalesInvoiceItem(
                invoice_id=invoice.id,
                item_id=item_data["item_id"],
                hsn_code=item_data.get("hsn_code"),
                quantity=qty,
                rate=rate,
                discount=discount,
                taxable=item_taxable,
                gst_rate=gst_rate,
                cgst=tax["cgst"],
                sgst=tax["sgst"],
                igst=tax["igst"],
                cess=item_data.get("cess", 0.0),
                total=round(item_taxable + tax["cgst"] + tax["sgst"] + tax["igst"], 2),
            )
            self.session.add(item)

            self.stock_service.record_transaction(
                transaction_type="sales",
                item_id=item_data["item_id"],
                godown_id=godown_id,
                quantity=-qty,
                rate=rate,
                amount=amount,
                transaction_date=invoice_date,
                party_id=party_id,
                reference_type="sales_invoice",
                reference_id=invoice.id,
                created_by=created_by,
            )

        invoice.gross_amount = round(gross, 2)
        invoice.taxable_amount = round(taxable, 2)
        invoice.cgst_total = round(cgst_total, 2)
        invoice.sgst_total = round(sgst_total, 2)
        invoice.igst_total = round(igst_total, 2)
        invoice.grand_total = round(taxable + cgst_total + sgst_total + igst_total, 2)

        self.session.commit()
        return invoice

    def get_all_invoices(self) -> list[SalesInvoice]:
        return list(
            self.session.scalars(
                select(SalesInvoice).order_by(SalesInvoice.id.desc())
            ).all()
        )

    def get_invoice_by_id(self, invoice_id: int) -> SalesInvoice | None:
        return self.session.get(SalesInvoice, invoice_id)
