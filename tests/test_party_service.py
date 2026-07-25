from src.services.party_service import PartyService


def test_create_customer(session):
    svc = PartyService(session)
    p = svc.create_party(name="Test Customer", party_type="customer")
    assert p.code.startswith("C")
    assert p.name == "Test Customer"
    assert p.is_active is True


def test_create_vendor(session):
    svc = PartyService(session)
    p = svc.create_party(name="Test Vendor", party_type="vendor")
    assert p.code.startswith("V")
    assert p.name == "Test Vendor"


def test_get_all_parties(session):
    svc = PartyService(session)
    svc.create_party(name="A", party_type="customer")
    svc.create_party(name="B", party_type="vendor")
    assert len(svc.get_all_parties()) == 2


def test_get_parties_by_type(session):
    svc = PartyService(session)
    svc.create_party(name="Cust", party_type="customer")
    svc.create_party(name="Vend", party_type="vendor")
    custs = svc.get_all_parties("customer")
    assert all(p.party_type in ("customer", "both") for p in custs)
    assert len(custs) == 1


def test_update_party(session):
    svc = PartyService(session)
    p = svc.create_party(name="Old", party_type="customer")
    svc.update_party(p.id, name="Updated")
    assert svc.get_party_by_id(p.id).name == "Updated"


def test_delete_party(session):
    svc = PartyService(session)
    p = svc.create_party(name="ToDelete", party_type="customer")
    assert svc.delete_party(p.id) is True
    assert svc.get_party_by_id(p.id) is None
