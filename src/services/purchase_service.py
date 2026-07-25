from datetime import date

from sqlalchemy import select, func
from sqlalchemy.orm import Session

from src.database.models.purchase import PurchaseBill, PurchaseBillItem
from src.database.models.party import Party
from src.database.models.company import Company
from src.services.stock_service import StockService
from src.utils.gst_utils import calculate_gst


class PurchaseService:
    def __init__(self, session: Session):
        self.session = session
        self.stock_service = StockService(session)

    def _next_bill_no(self) -> str:
        year = date.today().year % 100
        result = self.session.execute(
            select(func.max(PurchaseBill.bill_no)).where(
                PurchaseBill.bill_no.like(f"PUR-{year}%")
            )
        ).scalar()
        if result is None:
            return f"PUR-{year}-0001"
        last_num = int(result.split("-")[-1])
        return f"PUR-{year}-{last_num + 1:04d}"

    def create_purchase_bill(
        self,
        party_id: int,
        godown_id: int,
        items: list[dict],
        bill_date: str | None = None,
        discount_amount: float = 0.0,
        notes: str | None = None,
        created_by: int | None = None,
    ) -> PurchaseBill:
        if bill_date is None:
            bill_date = date.today().isoformat()

        party = self.session.get(Party, party_id)
        company = self.session.scalar(select(Company))

        bill_no = self._next_bill_no()
        bill = PurchaseBill(
            bill_no=bill_no,
            bill_date=bill_date,
            party_id=party_id,
            godown_id=godown_id,
            discount_amount=discount_amount,
            notes=notes,
            status="confirmed",
        )
        self.session.add(bill)
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
            gross += amount

            item_total = amount
            discount = item_data.get("discount", 0.0)
            item_taxable = round(item_total - discount, 2)
            taxable += item_taxable

            tax = calculate_gst(
                item_taxable, gst_rate,
                company.state_code if company else None,
                party.state_code if party else None,
            )
            cgst_total += tax["cgst"]
            sgst_total += tax["sgst"]
            igst_total += tax["igst"]

            item = PurchaseBillItem(
                bill_id=bill.id,
                item_id=item_data["item_id"],
                quantity=qty,
                rate=rate,
                amount=item_total,
                gst_rate=gst_rate,
                cgst=tax["cgst"],
                sgst=tax["sgst"],
                igst=tax["igst"],
            )
            self.session.add(item)

            self.stock_service.record_transaction(
                transaction_type="purchase",
                item_id=item_data["item_id"],
                godown_id=godown_id,
                quantity=qty,
                rate=rate,
                amount=item_total,
                transaction_date=bill_date,
                party_id=party_id,
                reference_type="purchase_bill",
                reference_id=bill.id,
                created_by=created_by,
            )

        bill.gross_amount = round(gross, 2)
        bill.taxable_amount = round(taxable, 2)
        bill.cgst_total = round(cgst_total, 2)
        bill.sgst_total = round(sgst_total, 2)
        bill.igst_total = round(igst_total, 2)
        bill.grand_total = round(taxable + cgst_total + sgst_total + igst_total, 2)

        self.session.commit()
        return bill

    def get_all_bills(self) -> list[PurchaseBill]:
        return list(
            self.session.scalars(
                select(PurchaseBill).order_by(PurchaseBill.id.desc())
            ).all()
        )

    def get_bill_by_id(self, bill_id: int) -> PurchaseBill | None:
        return self.session.get(PurchaseBill, bill_id)
