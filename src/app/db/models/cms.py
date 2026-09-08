from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.enums import CmsKind
from app.db.base import Base, TimestampMixin, UUIDPk


class CmsContent(Base, UUIDPk, TimestampMixin):
    """Noi dung do admin bat/tat khong can deploy: banner, modal popup, thong bao.

    Hien theo `placement` (vi tri FE render) + cua so thoi gian [starts_at, ends_at].
    `priority` cao hien truoc. `dismissible` -> user tat duoc (luu o CmsDismissal).
    """

    __tablename__ = "cms_contents"

    kind: Mapped[str] = mapped_column(String(20), default=CmsKind.BANNER, index=True)
    placement: Mapped[str] = mapped_column(String(50), default="global", index=True)
    title: Mapped[str] = mapped_column(String(200), default="")
    body: Mapped[str] = mapped_column(Text, default="")          # text/markdown/html
    image_url: Mapped[str] = mapped_column(String(500), default="")
    link_url: Mapped[str] = mapped_column(String(500), default="")
    cta_label: Mapped[str] = mapped_column(String(100), default="")
    level: Mapped[str] = mapped_column(String(20), default="info")  # mau sac FE
    priority: Mapped[int] = mapped_column(Integer, default=0)
    dismissible: Mapped[bool] = mapped_column(Boolean, default=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    starts_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    ends_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_by: Mapped[str | None] = mapped_column(ForeignKey("users.id"), nullable=True)


class CmsDismissal(Base, UUIDPk, TimestampMixin):
    """User da tat 1 CMS content -> khong hien lai cho user do."""

    __tablename__ = "cms_dismissals"
    __table_args__ = (UniqueConstraint("user_id", "content_id", name="uq_cms_dismiss"),)

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    content_id: Mapped[str] = mapped_column(ForeignKey("cms_contents.id"), index=True)
