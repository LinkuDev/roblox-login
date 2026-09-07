from __future__ import annotations

from app.core.config import Settings, get_settings
from app.domain.ports import BrowserProvider
from app.providers.browser.base import browser_registry


def build_browser(name: str | None = None, settings: Settings | None = None) -> BrowserProvider:
    settings = settings or get_settings()
    cls = browser_registry.get(name or settings.browser.provider)
    return cls(settings.browser)  # type: ignore[call-arg]


def available_browsers() -> list[str]:
    return browser_registry.names()
