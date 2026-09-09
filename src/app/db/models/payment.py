from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.enums import DepositStatus
from app.db.base import Base, TimestampMixin, UUIDPk


class Deposit(Base, UUIDPk, TimestampMixin):
    """Lenh nap diem qua crypto.

    User yeu cau nap `amount_points` -> he thong tinh so crypto phai tra (theo ty gia
    luc tao) + dia chi/nvoice tu payment provider. User chuyen tien -> provider goi
    webhook (hoac admin confirm tay) -> cong diem 1 LAN DUY NHAT (idempotent theo
    trang thai CONFIRMED + billing ref_id=deposit.id).
    """

    __tablename__ = "deposits"

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    provider: Mapped[str] = mapped_column(String(30), default="manual")
    status: Mapped[str] = mapped_column(String(20), default=DepositStatus.PENDING, index=True)

    amount_points: Mapped[int] = mapped_column(Integer)             # diem se cong
    currency: Mapped[str] = mapped_column(String(20), default="USDT")
    amount_crypto: Mapped[float] = mapped_column(Numeric(24, 8), default=0)  # so tien phai tra
    usd_per_point: Mapped[float] = mapped_column(Numeric(12, 6), default=0)  # gia diem da chot

    # thong tin thanh toan tra ve tu provider
    pay_address: Mapped[str] = mapped_column(String(200), default="")
    pay_url: Mapped[str] = mapped_column(String(500), default="")
    external_id: Mapped[str | None] = mapped_column(String(120), nullable=True, index=True)
    tx_hash: Mapped[str] = mapped_column(String(200), default="")

    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    confirmed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    raw_json: Mapped[str] = mapped_column(Text, default="")        # payload provider (debug)

    user = relationship("User")
