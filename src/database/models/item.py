from sqlalchemy import Boolean, Float, String
from sqlalchemy.orm import Mapped, mapped_column

from src.database.models.base import Base


class Item(Base):
    __tablename__ = "items"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    unit: Mapped[str] = mapped_column(String(20), nullable=False)
    opening_balance: Mapped[float] = mapped_column(Float, default=0.0)
    gst_rate: Mapped[float] = mapped_column(Float, default=0.0)
    hsn_code: Mapped[str | None] = mapped_column(String(10))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
