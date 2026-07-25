from src.services.godown_service import GodownService


def test_create_godown(session):
    svc = GodownService(session)
    g = svc.create_godown(code="WH1", name="Warehouse 1", address="Main St")
    assert g.code == "WH1"
    assert g.name == "Warehouse 1"
    assert g.address == "Main St"


def test_get_all_godowns(session):
    svc = GodownService(session)
    svc.create_godown(code="A", name="A")
    svc.create_godown(code="B", name="B")
    assert len(svc.get_all_godowns()) == 2


def test_update_godown(session):
    svc = GodownService(session)
    g = svc.create_godown(code="OLD", name="Old Name")
    svc.update_godown(g.id, name="New Name")
    assert svc.get_godown_by_id(g.id).name == "New Name"


def test_delete_godown(session):
    svc = GodownService(session)
    g = svc.create_godown(code="DEL", name="ToDelete")
    assert svc.delete_godown(g.id) is True
    assert svc.get_godown_by_id(g.id) is None
