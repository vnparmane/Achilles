from src.services.payment_service import PaymentService


def test_record_receipt(session, customer):
    svc = PaymentService(session)
    p = svc.record_payment(
        payment_type="receipt",
        party_id=customer.id,
        amount=5000,
        payment_date="2026-07-25",
        mode="cash",
    )
    assert p.payment_type == "receipt"
    assert p.amount == 5000
    assert p.id is not None


def test_record_payment(session, vendor):
    svc = PaymentService(session)
    p = svc.record_payment(
        payment_type="payment",
        party_id=vendor.id,
        amount=3000,
        payment_date="2026-07-25",
        mode="bank",
    )
    assert p.payment_type == "payment"
    assert p.amount == 3000


def test_get_all_payments(session, customer, vendor):
    svc = PaymentService(session)
    svc.record_payment("receipt", customer.id, 1000, "2026-07-25", "cash")
    svc.record_payment("payment", vendor.id, 500, "2026-07-25", "upi")
    assert len(svc.get_all_payments()) == 2


def test_get_party_outstanding(session, customer):
    svc = PaymentService(session)
    assert svc.get_party_outstanding(customer.id) == 0.0


def test_get_payment_by_id(session, customer):
    svc = PaymentService(session)
    p = svc.record_payment("receipt", customer.id, 1000, "2026-07-25", "cash")
    assert svc.get_payment_by_id(p.id) is not None
