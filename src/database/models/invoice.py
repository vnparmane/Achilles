from sqlalchemy import Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database.models.base import Base


class SalesInvoice(Base):
    __tablename__ = "sales_invoices"

    id: Mapped[int] = mapped_column(primary_key=True)
    invoice_no: Mapped[str] = mapped_column(String(50), nullable=False)
    invoice_date: Mapped[str] = mapped_column(String(10), nullable=False)
    party_id: Mapped[int] = mapped_column(ForeignKey("parties.id"), nullable=False)
    godown_id: Mapped[int] = mapped_column(ForeignKey("godowns.id"), nullable=False)
    transport: Mapped[str | None] = mapped_column(String(200))
    gross_amount: Mapped[float] = mapped_column(Float, default=0.0)
    discount_amount: Mapped[float] = mapped_column(Float, default=0.0)
    taxable_amount: Mapped[float] = mapped_column(Float, default=0.0)
    cgst_total: Mapped[float] = mapped_column(Float, default=0.0)
    sgst_total: Mapped[float] = mapped_column(Float, default=0.0)
    igst_total: Mapped[float] = mapped_column(Float, default=0.0)
    grand_total: Mapped[float] = mapped_column(Float, default=0.0)
    amount_in_words: Mapped[str | None] = mapped_column(String(500))
    notes: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(20), default="confirmed")

    party = relationship("Party")
    godown = relationship("Godown")
    items: Mapped[list[SalesInvoiceItem]] = relationship(back_populates="invoice", cascade="all, delete-orphan")


class SalesInvoiceItem(Base):
    __tablename__ = "sales_invoice_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    invoice_id: Mapped[int] = mapped_column(ForeignKey("sales_invoices.id"), nullable=False)
    item_id: Mapped[int] = mapped_column(ForeignKey("items.id"), nullable=False)
    hsn_code: Mapped[str | None] = mapped_column(String(10))
    quantity: Mapped[float] = mapped_column(Float, nullable=False)
    rate: Mapped[float] = mapped_column(Float, nullable=False)
    discount: Mapped[float] = mapped_column(Float, default=0.0)
    taxable: Mapped[float] = mapped_column(Float, default=0.0)
    gst_rate: Mapped[float] = mapped_column(Float, default=0.0)
    cgst: Mapped[float] = mapped_column(Float, default=0.0)
    sgst: Mapped[float] = mapped_column(Float, default=0.0)
    igst: Mapped[float] = mapped_column(Float, default=0.0)
    cess: Mapped[float] = mapped_column(Float, default=0.0)
    total: Mapped[float] = mapped_column(Float, default=0.0)

    invoice: Mapped[SalesInvoice] = relationship(back_populates="items")
    item = relationship("Item")
