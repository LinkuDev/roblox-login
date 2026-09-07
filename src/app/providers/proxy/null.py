from __future__ import annotations

from app.domain.models import Proxy
from app.domain.ports import ProxyProvider
from app.providers.proxy.base import proxy_registry


@proxy_registry.register("none")
class NullProxyProvider(ProxyProvider):
    """Chay khong proxy - mac dinh khi dev."""

    name = "none"

    def __init__(self, settings=None):
        pass

    def acquire(self, key: str | None = None) -> Proxy | None:
        return None
