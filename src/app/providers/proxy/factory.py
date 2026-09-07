from __future__ import annotations

from app.core.config import Settings, get_settings
from app.domain.ports import ProxyProvider
from app.providers.proxy.base import proxy_registry


def build_proxy_provider(name: str | None = None, settings: Settings | None = None) -> ProxyProvider:
    settings = settings or get_settings()
    cls = proxy_registry.get(name or settings.proxy.provider)
    return cls(settings.proxy)  # type: ignore[call-arg]


def available_proxy_providers() -> list[str]:
    return proxy_registry.names()
