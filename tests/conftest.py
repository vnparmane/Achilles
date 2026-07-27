import pytest

from src.database.engine import create_db_engine, create_session_factory
from src.database.models import Company, Godown, Item, Party, User
from src.database.models.base import Base


@pytest.fixture
def session():
    engine = create_db_engine(":memory:")
    Base.metadata.create_all(engine)
    factory = create_session_factory(engine)
    s = factory()
    yield s
    s.close()


@pytest.fixture
def company(session):
    c = Company(name="Test Co", gstin="27AAAAA0000A1Z5", state_code="27")
    session.add(c)
    session.commit()
    return c


@pytest.fixture
def vendor(session):
    v = Party(code="V001", name="Test Vendor", party_type="vendor", state_code="27")
    session.add(v)
    session.commit()
    return v


@pytest.fixture
def customer(session):
    c = Party(code="C001", name="Test Customer", party_type="customer", state_code="09")
    session.add(c)
    session.commit()
    return c


@pytest.fixture
def item(session):
    i = Item(code="ITM001", name="Test Item", unit="kg", gst_rate=12, hsn_code="5208")
    session.add(i)
    session.commit()
    return i


@pytest.fixture
def godown(session):
    g = Godown(code="GDN", name="Main")
    session.add(g)
    session.commit()
    return g


@pytest.fixture
def admin_user(session):
    u = User(username="admin", password_hash="abc", display_name="Admin", role="admin")
    session.add(u)
    session.commit()
    return u
