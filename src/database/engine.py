from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from src.utils.constants import DB_FILENAME


def get_db_path() -> Path:
    return Path(__file__).resolve().parent.parent.parent / DB_FILENAME


def create_db_engine(db_path: str | None = None):
    path = db_path or str(get_db_path())
    engine = create_engine(f"sqlite:///{path}", echo=False)
    return engine


def create_session_factory(engine):
    return sessionmaker(bind=engine)


def get_session(session_factory) -> Session:
    return session_factory()
