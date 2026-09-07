from __future__ import annotations

from app.core.registry import Registry
from app.domain.ports import BrowserProvider

browser_registry: Registry[BrowserProvider] = Registry("browser provider")
