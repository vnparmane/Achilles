from sqlalchemy import Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database.models.base import Base


class PurchaseBill(Base):
    __tablename__ = "purchase_bills"

    id: Mapped[int] = mapped_column(primary_key=True)
    bill_no: Mapped[str] = mapped_column(String(50), nullable=False)
    bill_date: Mapped[str] = mapped_column(String(10), nullable=False)
    party_id: Mapped[int] = mapped_column(ForeignKey("parties.id"), nullable=False)
    godown_id: Mapped[int] = mapped_column(ForeignKey("godowns.id"), nullable=False)
    gross_amount: Mapped[float] = mapped_column(Float, default=0.0)
    discount_amount: Mapped[float] = mapped_column(Float, default=0.0)
    taxable_amount: Mapped[float] = mapped_column(Float, default=0.0)
    cgst_total: Mapped[float] = mapped_column(Float, default=0.0)
    sgst_total: Mapped[float] = mapped_column(Float, default=0.0)
    igst_total: Mapped[float] = mapped_column(Float, default=0.0)
    grand_total: Mapped[float] = mapped_column(Float, default=0.0)
    notes: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(20), default="confirmed")

    party = relationship("Party")
    godown = relationship("Godown")
    items: Mapped[list[PurchaseBillItem]] = relationship(back_populates="bill", cascade="all, delete-orphan")


class PurchaseBillItem(Base):
    __tablename__ = "purchase_bill_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    bill_id: Mapped[int] = mapped_column(ForeignKey("purchase_bills.id"), nullable=False)
    item_id: Mapped[int] = mapped_column(ForeignKey("items.id"), nullable=False)
    quantity: Mapped[float] = mapped_column(Float, nullable=False)
    rate: Mapped[float] = mapped_column(Float, nullable=False)
    amount: Mapped[float] = mapped_column(Float, default=0.0)
    gst_rate: Mapped[float] = mapped_column(Float, default=0.0)
    cgst: Mapped[float] = mapped_column(Float, default=0.0)
    sgst: Mapped[float] = mapped_column(Float, default=0.0)
    igst: Mapped[float] = mapped_column(Float, default=0.0)

    bill: Mapped[PurchaseBill] = relationship(back_populates="items")
    item = relationship("Item")
