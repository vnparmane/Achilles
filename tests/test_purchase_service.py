from src.services.purchase_service import PurchaseService
from src.services.stock_service import StockService


def test_create_purchase_bill(session, company, vendor, item, godown, admin_user):
    svc = PurchaseService(session)
    bill = svc.create_purchase_bill(
        party_id=vendor.id, godown_id=godown.id,
        items=[{"item_id": item.id, "quantity": 100, "rate": 50, "gst_rate": 12}],
        created_by=admin_user.id,
    )
    assert bill.bill_no.startswith("PUR-")
    assert bill.gross_amount == 5000.0
    assert bill.taxable_amount == 5000.0
    assert bill.grand_total == 5600.0


def test_stock_increases(session, company, vendor, item, godown, admin_user):
    psvc = PurchaseService(session)
    psvc.create_purchase_bill(
        party_id=vendor.id, godown_id=godown.id,
        items=[{"item_id": item.id, "quantity": 50, "rate": 100, "gst_rate": 12}],
        created_by=admin_user.id,
    )
    ssvc = StockService(session)
    assert ssvc.get_stock_balance(item.id) == 50.0
