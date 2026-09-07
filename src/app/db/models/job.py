from __future__ import annotations

from sqlalchemy import Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.enums import JobStatus
from app.db.base import Base, TimestampMixin, UUIDPk


class Job(Base, UUIDPk, TimestampMixin):
    """Mot lan chay automation cho 1 order item. Worker cap nhat trang thai o day."""

    __tablename__ = "jobs"

    order_item_id: Mapped[str] = mapped_column(ForeignKey("order_items.id"), index=True)
    service_id: Mapped[str] = mapped_column(String(50), index=True)
    status: Mapped[str] = mapped_column(String(20), default=JobStatus.PENDING, index=True)
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    result_json: Mapped[str] = mapped_column(Text, default="")   # RunResult.to_dict()
    error_code: Mapped[str] = mapped_column(String(50), default="")
    cost_points: Mapped[int] = mapped_column(Integer, default=0)
    duration: Mapped[float] = mapped_column(Float, default=0.0)
