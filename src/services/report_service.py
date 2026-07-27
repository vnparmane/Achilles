from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from src.database.models.invoice import SalesInvoice, SalesInvoiceItem
from src.database.models.item import Item
from src.database.models.party import Party
from src.database.models.payment import PaymentTransaction
from src.database.models.purchase import PurchaseBill
from src.database.models.stock import StockTransaction


class ReportService:
    def __init__(self, session: Session):
        self.session = session

    def stock_balance(self) -> list[dict]:
        rows = self.session.execute(
            select(
                Item.code, Item.name, Item.unit, Item.opening_balance,
                func.coalesce(func.sum(StockTransaction.quantity), 0).label("balance"),
            )
            .outerjoin(StockTransaction, Item.id == StockTransaction.item_id)
            .group_by(Item.id)
            .order_by(Item.name)
        ).all()
        return [
            {
                "code": r.code, "name": r.name, "unit": r.unit,
                "opening": r.opening_balance,
                "balance": float(r.balance),
            }
            for r in rows
        ]

    def stock_movement(self, item_id: int | None = None) -> list[dict]:
        query = (
            select(StockTransaction)
            .order_by(StockTransaction.transaction_date.desc(), StockTransaction.id.desc())
        )
        if item_id is not None:
            query = query.where(StockTransaction.item_id == item_id)
        txns = self.session.scalars(query).all()
        return [
            {
                "date": t.transaction_date,
                "type": t.transaction_type,
                "item": t.item.name if t.item else "",
                "godown": t.godown.name if t.godown else "",
                "qty": t.quantity,
                "rate": t.rate,
                "amount": t.amount,
                "party": t.party.name if t.party else "",
                "ref": f"{t.reference_type or ''} #{t.reference_id or ''}",
            }
            for t in txns
        ]

    def party_ledger(self, party_id: int, date_from: str | None = None, date_to: str | None = None) -> list[dict]:
        entries: list[dict] = []
        inv_q = select(SalesInvoice).where(
            SalesInvoice.party_id == party_id,
            SalesInvoice.status == "confirmed",
        )
        if date_from:
            inv_q = inv_q.where(SalesInvoice.invoice_date >= date_from)
        if date_to:
            inv_q = inv_q.where(SalesInvoice.invoice_date <= date_to)
        invoices = self.session.scalars(inv_q.order_by(SalesInvoice.invoice_date)).all()
        for inv in invoices:
            entries.append({
                "date": inv.invoice_date,
                "description": f"Sales Invoice {inv.invoice_no}",
                "debit": inv.grand_total,
                "credit": 0.0,
            })

        bill_q = select(PurchaseBill).where(
            PurchaseBill.party_id == party_id,
            PurchaseBill.status == "confirmed",
        )
        if date_from:
            bill_q = bill_q.where(PurchaseBill.bill_date >= date_from)
        if date_to:
            bill_q = bill_q.where(PurchaseBill.bill_date <= date_to)
        bills = self.session.scalars(bill_q.order_by(PurchaseBill.bill_date)).all()
        for b in bills:
            entries.append({
                "date": b.bill_date,
                "description": f"Purchase Bill {b.bill_no}",
                "debit": 0.0,
                "credit": b.grand_total,
            })

        pay_q = select(PaymentTransaction).where(
            PaymentTransaction.party_id == party_id,
        )
        if date_from:
            pay_q = pay_q.where(PaymentTransaction.payment_date >= date_from)
        if date_to:
            pay_q = pay_q.where(PaymentTransaction.payment_date <= date_to)
        payments = self.session.scalars(pay_q.order_by(PaymentTransaction.payment_date)).all()
        for p in payments:
            desc = f"Payment ({p.mode})"
            if p.reference_no:
                desc += f" - {p.reference_no}"
            if p.payment_type == "receipt":
                entries.append({
                    "date": p.payment_date,
                    "description": desc,
                    "debit": 0.0,
                    "credit": p.amount,
                })
            else:
                entries.append({
                    "date": p.payment_date,
                    "description": desc,
                    "debit": p.amount,
                    "credit": 0.0,
                })

        entries.sort(key=lambda e: e["date"])
        balance = 0.0
        for e in entries:
            balance += e["debit"] - e["credit"]
            e["balance"] = round(balance, 2)
        return entries

    def gst_summary(self, date_from: str | None = None, date_to: str | None = None) -> list[dict]:
        q = select(SalesInvoiceItem).join(SalesInvoice).where(
            SalesInvoice.status == "confirmed"
        )
        if date_from:
            q = q.where(SalesInvoice.invoice_date >= date_from)
        if date_to:
            q = q.where(SalesInvoice.invoice_date <= date_to)
        invoices = self.session.scalars(q).all()
        summary: dict[float, dict] = {}
        for item in invoices:
            rate = item.gst_rate
            if rate not in summary:
                summary[rate] = {"rate": rate, "taxable": 0, "cgst": 0, "sgst": 0, "igst": 0}
            summary[rate]["taxable"] += item.taxable
            summary[rate]["cgst"] += item.cgst
            summary[rate]["sgst"] += item.sgst
            summary[rate]["igst"] += item.igst
        return [
            {"rate": v["rate"], "taxable": round(v["taxable"], 2),
             "cgst": round(v["cgst"], 2), "sgst": round(v["sgst"], 2),
             "igst": round(v["igst"], 2)}
            for v in summary.values()
        ]

    def purchase_register(self, date_from: str | None = None, date_to: str | None = None) -> list[dict]:
        q = select(PurchaseBill).where(PurchaseBill.status == "confirmed")
        if date_from:
            q = q.where(PurchaseBill.bill_date >= date_from)
        if date_to:
            q = q.where(PurchaseBill.bill_date <= date_to)
        bills = self.session.scalars(q.order_by(PurchaseBill.bill_date.desc())).all()
        return [
            {
                "bill_no": b.bill_no, "date": b.bill_date,
                "party": b.party.name if b.party else "",
                "gross": b.gross_amount, "taxable": b.taxable_amount,
                "gst": b.cgst_total + b.sgst_total + b.igst_total,
                "grand": b.grand_total,
            }
            for b in bills
        ]

    def dashboard_summary(self) -> dict:
        today = datetime.now().date().isoformat()
        result = {
            "today_sales": 0.0,
            "total_receivables": 0.0,
            "total_payables": 0.0,
            "low_stock_items": [],
        }

        today_sales = self.session.execute(
            select(func.coalesce(func.sum(SalesInvoice.grand_total), 0)).where(
                SalesInvoice.invoice_date == today,
                SalesInvoice.status == "confirmed",
            )
        ).scalar()
        result["today_sales"] = round(today_sales or 0.0, 2)

        from src.services.payment_service import PaymentService
        ps = PaymentService(self.session)

        customers = self.session.scalars(
            select(Party).where(Party.party_type.in_(["customer", "both"]), Party.is_active)
        ).all()
        for c in customers:
            result["total_receivables"] += ps.get_party_outstanding(c.id)

        vendors = self.session.scalars(
            select(Party).where(Party.party_type.in_(["vendor", "both"]), Party.is_active)
        ).all()
        for v in vendors:
            result["total_payables"] += ps.get_party_outstanding(v.id)

        result["total_receivables"] = round(result["total_receivables"], 2)
        result["total_payables"] = round(result["total_payables"], 2)

        low_stock = self.session.execute(
            select(Item.code, Item.name, Item.unit,
                   func.coalesce(func.sum(StockTransaction.quantity), 0).label("balance"))
            .outerjoin(StockTransaction, Item.id == StockTransaction.item_id)
            .group_by(Item.id)
            .having(func.coalesce(func.sum(StockTransaction.quantity), 0) < 10)
            .order_by(Item.name)
        ).all()
        result["low_stock_items"] = [
            {"code": r.code, "name": r.name, "unit": r.unit, "balance": float(r.balance)}
            for r in low_stock
        ]
        return result

    def sales_register(self, date_from: str | None = None, date_to: str | None = None) -> list[dict]:
        q = select(SalesInvoice).where(SalesInvoice.status == "confirmed")
        if date_from:
            q = q.where(SalesInvoice.invoice_date >= date_from)
        if date_to:
            q = q.where(SalesInvoice.invoice_date <= date_to)
        invoices = self.session.scalars(q.order_by(SalesInvoice.invoice_date.desc())).all()
        return [
            {
                "invoice_no": inv.invoice_no, "date": inv.invoice_date,
                "party": inv.party.name if inv.party else "",
                "gross": inv.gross_amount, "taxable": inv.taxable_amount,
                "gst": inv.cgst_total + inv.sgst_total + inv.igst_total,
                "grand": inv.grand_total,
            }
            for inv in invoices
        ]
