from src.services.company_service import CompanyService


def test_has_company_false(session):
    svc = CompanyService(session)
    assert svc.has_company() is False


def test_create_company(session):
    svc = CompanyService(session)
    c = svc.create_company(name="Test ERP", gstin="27AAAAA0000A1Z5")
    assert c.name == "Test ERP"
    assert svc.has_company() is True


def test_get_company(session):
    svc = CompanyService(session)
    svc.create_company(name="My Co")
    c = svc.get_company()
    assert c is not None
    assert c.name == "My Co"


def test_update_company(session):
    svc = CompanyService(session)
    c = svc.create_company(name="Old")
    svc.update_company(c.id, name="New", phone="12345")
    updated = svc.get_company()
    assert updated.name == "New"
    assert updated.phone == "12345"
