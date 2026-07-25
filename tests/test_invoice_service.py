from src.services.invoice_service import InvoiceService
from src.services.stock_service import StockService


def test_create_invoice(session, company, customer, item, godown, admin_user):
    # First add stock
    StockService(session).record_transaction(
        "purchase", item.id, godown.id, 100, 50, 5000, "2026-07-25",
    )
    session.commit()

    svc = InvoiceService(session)
    inv = svc.create_invoice(
        party_id=customer.id, godown_id=godown.id,
        items=[{"item_id": item.id, "quantity": 10, "rate": 200, "gst_rate": 12}],
        created_by=admin_user.id,
    )
    assert inv.invoice_no.startswith("INV-")
    assert inv.gross_amount == 2000.0
    assert inv.taxable_amount == 2000.0
    assert inv.igst_total == 240.0
    assert inv.grand_total == 2240.0


def test_stock_decreases(session, company, customer, item, godown, admin_user):
    StockService(session).record_transaction(
        "purchase", item.id, godown.id, 100, 50, 5000, "2026-07-25",
    )
    session.commit()

    svc = InvoiceService(session)
    svc.create_invoice(
        party_id=customer.id, godown_id=godown.id,
        items=[{"item_id": item.id, "quantity": 25, "rate": 200, "gst_rate": 12}],
        created_by=admin_user.id,
    )
    ssvc = StockService(session)
    assert ssvc.get_stock_balance(item.id) == 75.0
