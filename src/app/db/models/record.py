from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.enums import JobStatus
from app.db.base import Base, TimestampMixin, UUIDPk


class Record(Base, UUIDPk, TimestampMixin):
    """Mot dong trong pool = 1 account can xu ly.

    1 order sinh N record. Node claim record -> chay flow -> ghi lai status +
    cookies + reason ngay tren dong nay. Day la don vi ma node keo ve tu pool
    (Phase 2: claim bang SELECT ... FOR UPDATE SKIP LOCKED tren bang nay).
    """

    __tablename__ = "records"

    order_id: Mapped[str] = mapped_column(ForeignKey("orders.id"), index=True)
    service_id: Mapped[str] = mapped_column(String(50), index=True)

    # --- input (TODO: ma hoa o prod) ---
    username: Mapped[str] = mapped_column(String(255), index=True)
    password: Mapped[str] = mapped_column(String(255))
    totp_secret: Mapped[str | None] = mapped_column(String(64), nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # --- trang thai ---
    status: Mapped[str] = mapped_column(String(20), default=JobStatus.QUEUED, index=True)
    attempt: Mapped[int] = mapped_column(Integer, default=0)

    # --- ket qua "co gia tri" ---
    cookies: Mapped[str] = mapped_column(Text, default="")       # JSON cookie/session
    result_json: Mapped[str] = mapped_column(Text, default="")   # RunResult.to_dict()
    error_code: Mapped[str] = mapped_column(String(50), default="")
    reason: Mapped[str] = mapped_column(Text, default="")        # ly do fail cho nguoi doc
    cost_points: Mapped[int] = mapped_column(Integer, default=0)
    duration: Mapped[float] = mapped_column(Float, default=0.0)

    # --- claim (Phase 2 - de san, nullable) ---
    node_id: Mapped[str] = mapped_column(String(64), default="")
    claim_expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    order = relationship("Order", back_populates="records")
