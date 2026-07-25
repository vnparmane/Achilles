from sqlalchemy import Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database.models.base import Base


class PaymentTransaction(Base):
    __tablename__ = "payment_transactions"

    id: Mapped[int] = mapped_column(primary_key=True)
    payment_type: Mapped[str] = mapped_column(String(20), nullable=False)
    party_id: Mapped[int] = mapped_column(ForeignKey("parties.id"), nullable=False)
    invoice_id: Mapped[int | None] = mapped_column(ForeignKey("sales_invoices.id"))
    purchase_bill_id: Mapped[int | None] = mapped_column(ForeignKey("purchase_bills.id"))
    payment_date: Mapped[str] = mapped_column(String(10), nullable=False)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    mode: Mapped[str] = mapped_column(String(20), default="cash")
    reference_no: Mapped[str | None] = mapped_column(String(50))
    notes: Mapped[str | None] = mapped_column(String(200))

    party = relationship("Party")
