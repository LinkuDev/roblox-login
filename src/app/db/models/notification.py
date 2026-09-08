from __future__ import annotations

from sqlalchemy import ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.enums import NotificationLevel
from app.db.base import Base, TimestampMixin, UUIDPk


class Notification(Base, UUIDPk, TimestampMixin):
    """Thong bao trong app.

    - user_id = NULL  -> broadcast (moi user deu thay).
    - user_id != NULL -> rieng 1 user (vd: don xong, nap thanh cong).

    Trang thai "da doc" KHONG luu o day (broadcast dung chung 1 dong) ma o
    `NotificationRead` theo tung user -> broadcast van danh dau doc rieng le duoc.
    """

    __tablename__ = "notifications"

    user_id: Mapped[str | None] = mapped_column(
        ForeignKey("users.id"), nullable=True, index=True
    )
    level: Mapped[str] = mapped_column(String(20), default=NotificationLevel.INFO)
    title: Mapped[str] = mapped_column(String(200))
    body: Mapped[str] = mapped_column(Text, default="")
    link_url: Mapped[str] = mapped_column(String(500), default="")
    ref_type: Mapped[str] = mapped_column(String(30), default="")   # vd "order","deposit"
    ref_id: Mapped[str] = mapped_column(String(32), default="")


class NotificationRead(Base, UUIDPk, TimestampMixin):
    """Danh dau 1 user da doc 1 notification (ho tro ca broadcast)."""

    __tablename__ = "notification_reads"
    __table_args__ = (UniqueConstraint("user_id", "notification_id", name="uq_notif_read"),)

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    notification_id: Mapped[str] = mapped_column(
        ForeignKey("notifications.id"), index=True
    )
