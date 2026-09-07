from __future__ import annotations

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.enums import OrderStatus
from app.db.base import Base, TimestampMixin, UUIDPk


class Order(Base, UUIDPk, TimestampMixin):
    """Don hang: 1 user mua 1 service voi N item (N account chang han)."""

    __tablename__ = "orders"

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    service_id: Mapped[str] = mapped_column(String(50), index=True)
    status: Mapped[str] = mapped_column(String(20), default=OrderStatus.DRAFT, index=True)
    quantity: Mapped[int] = mapped_column(Integer, default=1)
    unit_price: Mapped[int] = mapped_column(Integer, default=0)   # diem / item
    total_price: Mapped[int] = mapped_column(Integer, default=0)
    completed_count: Mapped[int] = mapped_column(Integer, default=0)
    failed_count: Mapped[int] = mapped_column(Integer, default=0)
    note: Mapped[str] = mapped_column(Text, default="")

    user = relationship("User", back_populates="orders")
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")


class OrderItem(Base, UUIDPk, TimestampMixin):
    """Mot don vi cong viec trong don - map 1-1 voi 1 Job khi chay."""

    __tablename__ = "order_items"

    order_id: Mapped[str] = mapped_column(ForeignKey("orders.id"), index=True)
    # input duoc luu dang JSON string (tk/mk...) - can ma hoa o prod
    input_ref: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(20), default="pending", index=True)
    result_ref: Mapped[str] = mapped_column(Text, default="")

    order = relationship("Order", back_populates="items")
