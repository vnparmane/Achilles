from sqlalchemy import Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database.models.base import Base


class StockTransaction(Base):
    __tablename__ = "stock_transactions"

    id: Mapped[int] = mapped_column(primary_key=True)
    transaction_type: Mapped[str] = mapped_column(String(30), nullable=False)
    item_id: Mapped[int] = mapped_column(ForeignKey("items.id"), nullable=False)
    godown_id: Mapped[int] = mapped_column(ForeignKey("godowns.id"), nullable=False)
    quantity: Mapped[float] = mapped_column(Float, nullable=False)
    rate: Mapped[float] = mapped_column(Float, default=0.0)
    amount: Mapped[float] = mapped_column(Float, default=0.0)
    party_id: Mapped[int | None] = mapped_column(ForeignKey("parties.id"))
    reference_type: Mapped[str | None] = mapped_column(String(30))
    reference_id: Mapped[int | None]
    notes: Mapped[str | None] = mapped_column(Text)
    transaction_date: Mapped[str] = mapped_column(String(10), nullable=False)
    created_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"))

    item = relationship("Item")
    godown = relationship("Godown")
    party = relationship("Party")
