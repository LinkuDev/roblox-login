from __future__ import annotations

from app.core.registry import Registry
from app.domain.ports import ProxyProvider

proxy_registry: Registry[ProxyProvider] = Registry("proxy provider")
