from src.services.item_service import ItemService


def test_create_item(session):
    svc = ItemService(session)
    it = svc.create_item(name="Cotton Yarn", unit="kg", gst_rate=5, hsn_code="5205")
    assert it.code == "ITM001"
    assert it.name == "Cotton Yarn"
    assert it.gst_rate == 5


def test_get_all_items(session):
    svc = ItemService(session)
    svc.create_item(name="Item A", unit="kg")
    svc.create_item(name="Item B", unit="meter")
    assert len(svc.get_all_items()) == 2


def test_update_item(session):
    svc = ItemService(session)
    it = svc.create_item(name="Old", unit="kg")
    svc.update_item(it.id, name="New", gst_rate=12)
    updated = svc.get_item_by_id(it.id)
    assert updated.name == "New"
    assert updated.gst_rate == 12


def test_delete_item(session):
    svc = ItemService(session)
    it = svc.create_item(name="ToDelete", unit="kg")
    assert svc.delete_item(it.id) is True
    assert svc.get_item_by_id(it.id) is None
