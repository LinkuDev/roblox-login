from __future__ import annotations

from abc import ABC, abstractmethod

from app.domain.models import Proxy


class ProxyProvider(ABC):
    name: str = "base"

    @abstractmethod
    def acquire(self, key: str | None = None) -> Proxy | None:
        """Lay 1 proxy. `key` de sticky theo account neu provider ho tro."""

    def release(self, proxy: Proxy, *, healthy: bool = True) -> None:
        """Tra proxy ve pool, danh dau chet neu healthy=False."""
