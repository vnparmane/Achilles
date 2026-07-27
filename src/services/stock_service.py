from sqlalchemy import func, select
from sqlalchemy.orm import Session

from src.database.models.item import Item
from src.database.models.stock import StockTransaction


class StockService:
    def __init__(self, session: Session):
        self.session = session

    def record_transaction(
        self,
        transaction_type: str,
        item_id: int,
        godown_id: int,
        quantity: float,
        rate: float,
        amount: float,
        transaction_date: str,
        party_id: int | None = None,
        reference_type: str | None = None,
        reference_id: int | None = None,
        notes: str | None = None,
        created_by: int | None = None,
    ) -> StockTransaction:
        txn = StockTransaction(
            transaction_type=transaction_type,
            item_id=item_id,
            godown_id=godown_id,
            quantity=quantity,
            rate=rate,
            amount=amount,
            party_id=party_id,
            reference_type=reference_type,
            reference_id=reference_id,
            notes=notes,
            transaction_date=transaction_date,
            created_by=created_by,
        )
        self.session.add(txn)
        return txn

    def get_stock_balance(self, item_id: int) -> float:
        result = self.session.execute(
            select(func.sum(StockTransaction.quantity)).where(
                StockTransaction.item_id == item_id
            )
        ).scalar()
        return result or 0.0

    def get_all_balances(self) -> list[dict]:
        rows = self.session.execute(
            select(
                Item.id,
                Item.code,
                Item.name,
                Item.unit,
                func.coalesce(func.sum(StockTransaction.quantity), 0).label("balance"),
            )
            .outerjoin(StockTransaction, Item.id == StockTransaction.item_id)
            .group_by(Item.id)
            .order_by(Item.name)
        ).all()
        return [
            {"id": r.id, "code": r.code, "name": r.name, "unit": r.unit, "balance": float(r.balance)}
            for r in rows
        ]
