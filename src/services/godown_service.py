from sqlalchemy import select
from sqlalchemy.orm import Session

from src.database.models.godown import Godown


class GodownService:
    def __init__(self, session: Session):
        self.session = session

    def create_godown(self, code: str, name: str, address: str | None = None) -> Godown:
        godown = Godown(code=code, name=name, address=address)
        self.session.add(godown)
        self.session.commit()
        return godown

    def get_all_godowns(self) -> list[Godown]:
        return list(self.session.scalars(select(Godown).order_by(Godown.name)).all())

    def get_godown_by_id(self, godown_id: int) -> Godown | None:
        return self.session.get(Godown, godown_id)

    def update_godown(self, godown_id: int, **kwargs) -> Godown | None:
        godown = self.session.get(Godown, godown_id)
        if godown is None:
            return None
        for key, value in kwargs.items():
            if hasattr(godown, key):
                setattr(godown, key, value)
        self.session.commit()
        return godown
