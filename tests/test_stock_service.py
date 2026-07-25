from src.services.stock_service import StockService


def test_record_and_balance(session, item, godown):
    svc = StockService(session)
    svc.record_transaction(
        transaction_type="purchase", item_id=item.id,
        godown_id=godown.id, quantity=100, rate=50, amount=5000,
        transaction_date="2026-07-25",
    )
    session.commit()
    assert svc.get_stock_balance(item.id) == 100.0


def test_multiple_transactions(session, item, godown):
    svc = StockService(session)
    svc.record_transaction("purchase", item.id, godown.id, 100, 10, 1000, "2026-07-25")
    svc.record_transaction("sales", item.id, godown.id, -30, 20, 600, "2026-07-26")
    svc.record_transaction("purchase", item.id, godown.id, 50, 12, 600, "2026-07-27")
    session.commit()
    assert svc.get_stock_balance(item.id) == 120.0


def test_zero_balance_item(session, item, godown):
    svc = StockService(session)
    assert svc.get_stock_balance(item.id) == 0.0
