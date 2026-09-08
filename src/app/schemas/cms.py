from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from app.core.enums import CmsKind


class CmsView(BaseModel):
    """Ban rut gon cho FE render (public)."""

    id: str
    kind: str
    placement: str
    title: str
    body: str
    image_url: str
    link_url: str
    cta_label: str
    level: str
    priority: int
    dismissible: bool


class CmsCreateRequest(BaseModel):
    kind: CmsKind = CmsKind.BANNER
    placement: str = "global"
    title: str = ""
    body: str = ""
    image_url: str = ""
    link_url: str = ""
    cta_label: str = ""
    level: str = "info"
    priority: int = 0
    dismissible: bool = True
    is_active: bool = True
    starts_at: datetime | None = None
    ends_at: datetime | None = None


class CmsUpdateRequest(BaseModel):
    kind: CmsKind | None = None
    placement: str | None = None
    title: str | None = None
    body: str | None = None
    image_url: str | None = None
    link_url: str | None = None
    cta_label: str | None = None
    level: str | None = None
    priority: int | None = None
    dismissible: bool | None = None
    is_active: bool | None = None
    starts_at: datetime | None = None
    ends_at: datetime | None = None
