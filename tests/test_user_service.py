from src.services.user_service import UserService


def test_create_user(session):
    svc = UserService(session)
    u = svc.create_user(username="operator1", password="pass123", display_name="Operator 1", role="operator")
    assert u.username == "operator1"
    assert u.role == "operator"


def test_authenticate_valid(session):
    svc = UserService(session)
    svc.create_user(username="test", password="secret", display_name="Test", role="admin")
    user = svc.authenticate("test", "secret")
    assert user is not None
    assert user.username == "test"


def test_authenticate_wrong_password(session):
    svc = UserService(session)
    svc.create_user(username="test", password="correct", display_name="Test", role="admin")
    assert svc.authenticate("test", "wrong") is None


def test_authenticate_unknown_user(session):
    svc = UserService(session)
    assert svc.authenticate("nobody", "pass") is None


def test_update_user_password(session):
    svc = UserService(session)
    u = svc.create_user(username="u1", password="oldpass", display_name="U1", role="operator")
    svc.update_user(u.id, password="newpass")
    assert svc.authenticate("u1", "newpass") is not None
    assert svc.authenticate("u1", "oldpass") is None


def test_get_all_users(session):
    svc = UserService(session)
    svc.create_user(username="a", password="p", display_name="A", role="admin")
    svc.create_user(username="b", password="p", display_name="B", role="operator")
    assert len(svc.get_all_users()) == 2
