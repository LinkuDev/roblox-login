"""Pool proxy doc tu file text, round-robin + sticky theo key, danh dau proxy chet."""

from __future__ import annotations

import itertools
import threading
from pathlib import Path

from app.core.logging import get_logger
from app.domain.models import Proxy
from app.domain.ports import ProxyProvider
from app.providers.proxy.base import proxy_registry


@proxy_registry.register("static")
class FilePoolProxyProvider(ProxyProvider):
    name = "static"

    def __init__(self, settings=None):
        from app.core.config import get_settings

        self._settings = settings or get_settings().proxy
        self._lock = threading.Lock()
        self._log = get_logger("proxy", provider=self.name)
        self._pool: list[Proxy] = self._load(Path(self._settings.list_file))
        self._dead: set[str] = set()
        self._sticky: dict[str, Proxy] = {}
        self._cycle = itertools.cycle(self._pool) if self._pool else None

    def _load(self, path: Path) -> list[Proxy]:
        if not path.exists():
            self._log.warning("proxy_file_missing", path=str(path))
            return []
        out: list[Proxy] = []
        for line in path.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            try:
                out.append(Proxy.parse(line))
            except ValueError:
                self._log.warning("proxy_parse_failed", line=line)
        self._log.info("proxy_pool_loaded", count=len(out))
        return out

    def acquire(self, key: str | None = None) -> Proxy | None:
        if not self._cycle:
            return None
        with self._lock:
            if key and key in self._sticky:
                return self._sticky[key]
            for _ in range(len(self._pool)):
                proxy = next(self._cycle)
                if proxy.url not in self._dead:
                    if key:
                        self._sticky[key] = proxy
                    return proxy
            self._log.error("proxy_pool_exhausted")
            return None

    def release(self, proxy: Proxy, *, healthy: bool = True) -> None:
        if healthy:
            return
        with self._lock:
            self._dead.add(proxy.url)
            self._sticky = {k: v for k, v in self._sticky.items() if v.url != proxy.url}
            self._log.warning("proxy_marked_dead", proxy=f"{proxy.host}:{proxy.port}")
