from src.services.company_service import CompanyService
from src.services.godown_service import GodownService
from src.services.invoice_service import InvoiceService
from src.services.item_service import ItemService
from src.services.party_service import PartyService
from src.services.payment_service import PaymentService
from src.services.purchase_service import PurchaseService
from src.services.report_service import ReportService
from src.services.stock_service import StockService
from src.services.user_service import UserService


def test_e2e_full_workflow(session):
    svc_u = UserService(session)
    svc_c = CompanyService(session)
    svc_g = GodownService(session)
    svc_i = ItemService(session)
    svc_p = PartyService(session)
    svc_pur = PurchaseService(session)
    svc_inv = InvoiceService(session)
    svc_pay = PaymentService(session)
    svc_stk = StockService(session)
    svc_rpt = ReportService(session)

    # ── 1. User Management ──────────────────────────────────────────────
    user = svc_u.create_user("admin", "secret123", "Admin User", "admin")
    assert user.id is not None
    assert user.role == "admin"

    auth = svc_u.authenticate("admin", "secret123")
    assert auth is not None
    assert auth.id == user.id

    auth_wrong = svc_u.authenticate("admin", "wrongpass")
    assert auth_wrong is None

    auth_unknown = svc_u.authenticate("nobody", "x")
    assert auth_unknown is None

    # ── 2. Master Data Setup ────────────────────────────────────────────
    company = svc_c.create_company(
        name="My Textile Co",
        gstin="27AAAAA0000A1Z5",
        state_code="27",
        state="Maharashtra",
    )
    assert company.id is not None
    assert company.state_code == "27"

    godown = svc_g.create_godown(code="WH01", name="Warehouse 1")
    assert godown.id is not None

    godowns = svc_g.get_all_godowns()
    assert len(godowns) == 1

    item1 = svc_i.create_item(
        name="Cotton Fabric", unit="mtr",
        gst_rate=12, hsn_code="5208",
    )
    item2 = svc_i.create_item(
        name="Cotton Yarn", unit="kg",
        gst_rate=5, hsn_code="5205",
    )
    assert item1.id is not None
    assert item2.id is not None

    # Same-state vendor (Maharashtra = 27)
    vendor = svc_p.create_party(
        name="Mumbai Mills", party_type="vendor",
        state_code="27", state="Maharashtra", gstin="27BBBBB0000B1Z5",
    )
    assert vendor.id is not None
    assert vendor.party_type == "vendor"

    # Different-state customer (Gujarat = 24)
    customer = svc_p.create_party(
        name="Surat Textiles", party_type="customer",
        state_code="24", state="Gujarat", gstin="24CCCCC0000C1Z5",
    )
    assert customer.id is not None
    assert customer.party_type == "customer"

    # Same-state customer (Maharashtra = 27, for CGST/SGST test)
    local_customer = svc_p.create_party(
        name="Pune Garments", party_type="customer",
        state_code="27", state="Maharashtra", gstin="27DDDDD0000D1Z5",
    )
    assert local_customer.id is not None

    parties = svc_p.get_all_parties()
    assert len(parties) == 3

    # ── 3. Purchase Flow ────────────────────────────────────────────────
    bill = svc_pur.create_purchase_bill(
        party_id=vendor.id,
        godown_id=godown.id,
        items=[
            {"item_id": item1.id, "quantity": 100, "rate": 50, "gst_rate": 12},
            {"item_id": item2.id, "quantity": 200, "rate": 30, "gst_rate": 5},
        ],
        bill_date="2026-07-01",
        created_by=user.id,
    )
    assert bill.bill_no.startswith("PUR-")
    assert bill.gross_amount == 100 * 50 + 200 * 30  # 5000 + 6000 = 11000
    assert bill.taxable_amount == 11000.0
    assert bill.cgst_total > 0
    assert bill.sgst_total > 0
    assert bill.igst_total == 0.0
    assert bill.grand_total == 11000 + bill.cgst_total + bill.sgst_total

    # Same-state -> CGST = SGST
    assert bill.cgst_total == bill.sgst_total
    cgst_12 = round(5000 * 0.06, 2)
    sgst_12 = round(5000 * 0.06, 2)
    cgst_5 = round(6000 * 0.025, 2)
    sgst_5 = round(6000 * 0.025, 2)
    assert bill.cgst_total == round(cgst_12 + cgst_5, 2)
    assert bill.sgst_total == round(sgst_12 + sgst_5, 2)

    # Stock increased
    assert svc_stk.get_stock_balance(item1.id) == 100.0
    assert svc_stk.get_stock_balance(item2.id) == 200.0

    # ── 4. Sales Flow (Cross-State → IGST) ──────────────────────────────
    invoice1 = svc_inv.create_invoice(
        party_id=customer.id,
        godown_id=godown.id,
        items=[
            {"item_id": item1.id, "quantity": 30, "rate": 80, "gst_rate": 12},
        ],
        invoice_date="2026-07-15",
        created_by=user.id,
    )
    assert invoice1.invoice_no.startswith("INV-")
    assert invoice1.gross_amount == 30 * 80  # 2400
    assert invoice1.taxable_amount == 2400.0
    assert invoice1.cgst_total == 0.0
    assert invoice1.sgst_total == 0.0
    assert invoice1.igst_total > 0
    assert invoice1.igst_total == round(2400 * 0.12, 2)  # 288.0
    assert invoice1.grand_total == 2400 + 288.0

    # Stock decreased
    assert svc_stk.get_stock_balance(item1.id) == 70.0  # 100 - 30

    # ── 5. Sales Flow (Same-State → CGST + SGST) ────────────────────────
    invoice2 = svc_inv.create_invoice(
        party_id=local_customer.id,
        godown_id=godown.id,
        items=[
            {"item_id": item1.id, "quantity": 10, "rate": 80, "gst_rate": 12},
            {"item_id": item2.id, "quantity": 50, "rate": 55, "gst_rate": 5},
        ],
        invoice_date="2026-07-20",
        created_by=user.id,
    )
    assert invoice2.cgst_total > 0
    assert invoice2.sgst_total > 0
    assert invoice2.cgst_total == invoice2.sgst_total
    assert invoice2.igst_total == 0.0

    expected_cgst = round(800 * 0.06 + 2750 * 0.025, 2)
    assert invoice2.cgst_total == expected_cgst
    assert invoice2.grand_total == (800 + 2750) + invoice2.cgst_total + invoice2.sgst_total

    assert svc_stk.get_stock_balance(item1.id) == 60.0  # 100 - 30 - 10
    assert svc_stk.get_stock_balance(item2.id) == 150.0  # 200 - 50

    # ── 6. Payment Flow ─────────────────────────────────────────────────
    receipt = svc_pay.record_payment(
        payment_type="receipt", party_id=customer.id,
        amount=2000, payment_date="2026-07-25", mode="bank",
        reference_no="CHQ001",
    )
    assert receipt.payment_type == "receipt"
    assert receipt.amount == 2000.0
    assert receipt.id is not None

    payment = svc_pay.record_payment(
        payment_type="payment", party_id=vendor.id,
        amount=5000, payment_date="2026-07-26", mode="cash",
    )
    assert payment.payment_type == "payment"
    assert payment.amount == 5000.0

    all_payments = svc_pay.get_all_payments()
    assert len(all_payments) == 2

    # Outstanding calculations
    # Customer: invoiced 2688, received 2000, outstanding = 688
    cust_outstanding = svc_pay.get_party_outstanding(customer.id)
    expected_cust = invoice1.grand_total - 2000
    assert cust_outstanding == expected_cust

    # Vendor: bill was 12320 (approx), paid 5000, outstanding = ~7320
    vend_outstanding = svc_pay.get_party_outstanding(vendor.id)
    expected_vend = bill.grand_total - 5000
    assert vend_outstanding == expected_vend

    # ── 7. Reports ──────────────────────────────────────────────────────
    # Stock Balance
    balances = svc_rpt.stock_balance()
    assert len(balances) == 2
    b1 = {b["name"]: b["balance"] for b in balances}
    assert b1["Cotton Fabric"] == 60.0
    assert b1["Cotton Yarn"] == 150.0

    # Stock Movement
    movements = svc_rpt.stock_movement()
    assert len(movements) >= 4  # 1 purchase + 3 sales (2 invoices, but invoice2 has 2 items)

    movements_item1 = svc_rpt.stock_movement(item_id=item1.id)
    assert len(movements_item1) == 3  # purchase + 2 sales

    # Party Ledger
    cust_ledger = svc_rpt.party_ledger(customer.id)
    assert len(cust_ledger) >= 2  # invoice + receipt
    assert cust_ledger[-1]["balance"] == cust_outstanding

    vend_ledger = svc_rpt.party_ledger(vendor.id)
    assert len(vend_ledger) >= 2  # bill + payment

    # GST Summary
    gst = svc_rpt.gst_summary()
    assert len(gst) == 2  # 12% and 5% slabs
    rates = {g["rate"]: g for g in gst}
    assert 12 in rates
    assert 5 in rates

    # Sales Register
    sales = svc_rpt.sales_register()
    assert len(sales) == 2

    # Purchase Register
    purchases = svc_rpt.purchase_register()
    assert len(purchases) == 1

    # Dashboard Summary
    dash = svc_rpt.dashboard_summary()
    assert dash["today_sales"] >= 0
    assert dash["today_purchases"] >= 0
    assert dash["total_receivables"] >= 0
    assert dash["total_payables"] >= 0
    assert len(dash["recent_activity"]) >= 1

    # ── 8. Edge Cases ───────────────────────────────────────────────────
    # Zero-stock item
    item3 = svc_i.create_item(
        name="Chemicals", unit="ltr",
        gst_rate=18, hsn_code="3808",
    )
    assert svc_stk.get_stock_balance(item3.id) == 0.0

    # Delete unused godown
    godown2 = svc_g.create_godown(code="WH02", name="Warehouse 2")
    svc_g.delete_godown(godown2.id)

    # Update item
    updated = svc_i.update_item(item3.id, name="Industrial Chemicals")
    assert updated.name == "Industrial Chemicals"

    # Update party
    updated_p = svc_p.update_party(vendor.id, phone="9876543210")
    assert updated_p.phone == "9876543210"

    # Update user password
    svc_u.update_user(user.id, password="newsecret456")
    assert svc_u.authenticate("admin", "newsecret456") is not None
    assert svc_u.authenticate("admin", "secret123") is None

    # Update company
    svc_c.update_company(company.id, name="My Textile Co Pvt Ltd")
    assert svc_c.get_company().name == "My Textile Co Pvt Ltd"

    # Delete unused party/item (no FK references)
    unused_party = svc_p.create_party(name="Temp", party_type="customer")
    assert svc_p.delete_party(unused_party.id) is True
    assert svc_u.get_all_users() is not None
