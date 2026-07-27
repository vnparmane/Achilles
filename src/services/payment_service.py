from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from src.database.models.invoice import SalesInvoice
from src.database.models.party import Party
from src.database.models.payment import PaymentTransaction
from src.database.models.purchase import PurchaseBill


class PaymentService:
    def __init__(self, session: Session):
        self.session = session

    def record_payment(
        self,
        payment_type: str,
        party_id: int,
        amount: float,
        payment_date: str | None = None,
        invoice_id: int | None = None,
        purchase_bill_id: int | None = None,
        mode: str = "cash",
        reference_no: str | None = None,
        notes: str | None = None,
    ) -> PaymentTransaction:
        if payment_date is None:
            payment_date = datetime.now().date().isoformat()
        txn = PaymentTransaction(
            payment_type=payment_type,
            party_id=party_id,
            invoice_id=invoice_id,
            purchase_bill_id=purchase_bill_id,
            payment_date=payment_date,
            amount=amount,
            mode=mode,
            reference_no=reference_no,
            notes=notes,
        )
        self.session.add(txn)
        self.session.commit()
        return txn

    def get_all_payments(self) -> list[PaymentTransaction]:
        return list(
            self.session.scalars(
                select(PaymentTransaction).order_by(PaymentTransaction.id.desc())
            ).all()
        )

    def get_payment_by_id(self, payment_id: int) -> PaymentTransaction | None:
        return self.session.get(PaymentTransaction, payment_id)

    def get_party_outstanding(self, party_id: int) -> float:
        total_billed = 0.0
        party = self.session.get(Party, party_id)
        if party is None:
            return 0.0

        if party.party_type in ("customer", "both"):
            result = self.session.execute(
                select(func.coalesce(func.sum(SalesInvoice.grand_total), 0)).where(
                    SalesInvoice.party_id == party_id,
                    SalesInvoice.status == "confirmed",
                )
            ).scalar()
            total_billed += result or 0.0

        if party.party_type in ("vendor", "both"):
            result = self.session.execute(
                select(func.coalesce(func.sum(PurchaseBill.grand_total), 0)).where(
                    PurchaseBill.party_id == party_id,
                    PurchaseBill.status == "confirmed",
                )
            ).scalar()
            total_billed += result or 0.0

        result = self.session.execute(
            select(func.coalesce(func.sum(PaymentTransaction.amount), 0)).where(
                PaymentTransaction.party_id == party_id
            )
        ).scalar()
        total_paid = result or 0.0

        return round(total_billed - total_paid, 2)

    def get_outstanding_invoices(self, party_id: int) -> list[dict]:
        party = self.session.get(Party, party_id)
        if party is None:
            return []
        results: list[dict] = []

        if party.party_type in ("customer", "both"):
            invoices = self.session.scalars(
                select(SalesInvoice).where(
                    SalesInvoice.party_id == party_id,
                    SalesInvoice.status == "confirmed",
                ).order_by(SalesInvoice.invoice_date)
            ).all()
            for inv in invoices:
                paid = self.session.execute(
                    select(func.coalesce(func.sum(PaymentTransaction.amount), 0)).where(
                        PaymentTransaction.invoice_id == inv.id
                    )
                ).scalar() or 0.0
                outstanding = round(inv.grand_total - paid, 2)
                if outstanding > 0:
                    results.append({
                        "type": "invoice",
                        "ref_id": inv.id,
                        "ref_no": inv.invoice_no,
                        "date": inv.invoice_date,
                        "total": inv.grand_total,
                        "paid": round(paid, 2),
                        "outstanding": outstanding,
                    })

        if party.party_type in ("vendor", "both"):
            bills = self.session.scalars(
                select(PurchaseBill).where(
                    PurchaseBill.party_id == party_id,
                    PurchaseBill.status == "confirmed",
                ).order_by(PurchaseBill.bill_date)
            ).all()
            for bill in bills:
                paid = self.session.execute(
                    select(func.coalesce(func.sum(PaymentTransaction.amount), 0)).where(
                        PaymentTransaction.purchase_bill_id == bill.id
                    )
                ).scalar() or 0.0
                outstanding = round(bill.grand_total - paid, 2)
                if outstanding > 0:
                    results.append({
                        "type": "purchase_bill",
                        "ref_id": bill.id,
                        "ref_no": bill.bill_no,
                        "date": bill.bill_date,
                        "total": bill.grand_total,
                        "paid": round(paid, 2),
                        "outstanding": outstanding,
                    })

        return results
