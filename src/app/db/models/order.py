from __future__ import annotations

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.enums import OrderStatus
from app.db.base import Base, TimestampMixin, UUIDPk


class Order(Base, UUIDPk, TimestampMixin):
    """Don hang: 1 user mua 1 service voi N record (N account).

    Diem duoc tru NGAY khi tao order (quantity * unit_price). Tung record chay
    doc lap sau do; hien khong hoan diem khi record fail (refund lam sau).
    """

    __tablename__ = "orders"

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    service_id: Mapped[str] = mapped_column(String(50), index=True)
    status: Mapped[str] = mapped_column(String(20), default=OrderStatus.DRAFT, index=True)
    quantity: Mapped[int] = mapped_column(Integer, default=1)
    unit_price: Mapped[int] = mapped_column(Integer, default=0)   # diem / record
    total_price: Mapped[int] = mapped_column(Integer, default=0)  # da tru luc tao
    completed_count: Mapped[int] = mapped_column(Integer, default=0)
    failed_count: Mapped[int] = mapped_column(Integer, default=0)
    note: Mapped[str] = mapped_column(Text, default="")

    user = relationship("User", back_populates="orders")
    records = relationship("Record", back_populates="order", cascade="all, delete-orphan")
