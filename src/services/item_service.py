from sqlalchemy import select
from sqlalchemy.orm import Session

from src.database.models.item import Item


class ItemService:
    def __init__(self, session: Session):
        self.session = session

    def _next_code(self) -> str:
        result = self.session.execute(
            select(Item.code).order_by(Item.code.desc())
        ).first()
        if result is None:
            return "ITM001"
        last_code = result[0]
        last_num = int(last_code[3:]) if last_code[3:].isdigit() else 0
        return f"ITM{last_num + 1:03d}"

    def create_item(
        self,
        name: str,
        unit: str,
        gst_rate: float = 0.0,
        hsn_code: str | None = None,
        opening_balance: float = 0.0,
    ) -> Item:
        code = self._next_code()
        item = Item(
            code=code,
            name=name,
            unit=unit,
            gst_rate=gst_rate,
            hsn_code=hsn_code,
            opening_balance=opening_balance,
        )
        self.session.add(item)
        self.session.commit()
        return item

    def get_all_items(self) -> list[Item]:
        return list(self.session.scalars(select(Item).order_by(Item.name)).all())

    def get_item_by_id(self, item_id: int) -> Item | None:
        return self.session.get(Item, item_id)

    def update_item(self, item_id: int, **kwargs) -> Item | None:
        item = self.session.get(Item, item_id)
        if item is None:
            return None
        for key, value in kwargs.items():
            setattr(item, key, value)
        self.session.commit()
        return item

    def search_items(self, query: str) -> list[Item]:
        stmt = select(Item).where(
            Item.name.ilike(f"%{query}%") | Item.code.ilike(f"%{query}%")
        ).order_by(Item.name)
        return list(self.session.scalars(stmt).all())
