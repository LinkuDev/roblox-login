from __future__ import annotations

from pydantic import BaseModel, Field

from app.core.enums import NotificationLevel


class NotificationView(BaseModel):
    id: str
    level: str
    title: str
    body: str
    link_url: str
    ref_type: str
    ref_id: str
    is_broadcast: bool
    unread: bool
    created_at: str


class UnreadCountResponse(BaseModel):
    unread: int


class BroadcastRequest(BaseModel):
    """Admin gui thong bao. user_id=None -> broadcast toan bo."""

    title: str = Field(min_length=1, max_length=200)
    body: str = ""
    level: NotificationLevel = NotificationLevel.INFO
    user_id: str | None = None
    link_url: str = ""
