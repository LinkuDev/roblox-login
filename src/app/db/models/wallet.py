from __future__ import annotations

from sqlalchemy import BigInteger, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPk


class Wallet(Base, UUIDPk, TimestampMixin):
    """Vi diem cua user. Chay he thong bang POINT truoc, thanh toan tu dong sau."""

    __tablename__ = "wallets"

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), unique=True, index=True)
    balance: Mapped[int] = mapped_column(BigInteger, default=0)

    user = relationship("User", back_populates="wallet")
    transactions = relationship("PointTransaction", back_populates="wallet")


class PointTransaction(Base, UUIDPk, TimestampMixin):
    """So cai: moi thay doi diem la 1 dong -> audit duoc, khong sua balance tay."""

    __tablename__ = "point_transactions"

    wallet_id: Mapped[str] = mapped_column(ForeignKey("wallets.id"), index=True)
    type: Mapped[str] = mapped_column(String(20))          # PointTxType
    amount: Mapped[int] = mapped_column(Integer)           # + hoac -
    balance_after: Mapped[int] = mapped_column(BigInteger)
    ref_type: Mapped[str] = mapped_column(String(30), default="")   # vd "order"
    ref_id: Mapped[str] = mapped_column(String(32), default="")
    note: Mapped[str] = mapped_column(Text, default="")

    wallet = relationship("Wallet", back_populates="transactions")
