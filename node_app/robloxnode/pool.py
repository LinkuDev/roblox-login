"""PoolClient - noi agent lay record va tra ket qua.

Trc mat: LocalPool (in-memory) de test vong lap ngay tren may, chua can SaaS/WSS.
Sau nay them WsPool (claim/report qua WSS) implement cung interface - agent khong doi.
"""

from __future__ import annotations

import threading
from collections import deque
from dataclasses import dataclass
from typing import Protocol


@dataclass(slots=True)
class Record:
    id: str
    username: str
    password: str


class PoolClient(Protocol):
    def has_work(self) -> bool: ...
    def claim(self) -> Record | None: ...
    def report(self, record_id: str, result: dict) -> None: ...
    def pending_count(self) -> int: ...


class LocalPool:
    """Pool local: hang doi record trong RAM. Dung de demo/test agent."""

    def __init__(self) -> None:
        self._q: deque[Record] = deque()
        self._lock = threading.Lock()
        self.reported: list[tuple[str, dict]] = []

    def seed_demo(self, n: int = 500) -> None:
        with self._lock:
            for i in range(1, n + 1):
                rid = f"demo-{i:04d}"
                self._q.append(Record(rid, f"user{i:04d}", "pass"))

    def add_lines(self, text: str) -> int:
        added = 0
        with self._lock:
            for idx, raw in enumerate(text.splitlines(), 1):
                line = raw.strip()
                if not line or line.startswith("#") or ":" not in line:
                    continue
                u, _, p = line.partition(":")
                if u.strip() and p.strip():
                    self._q.append(Record(f"line-{idx}", u.strip(), p.strip()))
                    added += 1
        return added

    def has_work(self) -> bool:
        with self._lock:
            return bool(self._q)

    def claim(self) -> Record | None:
        with self._lock:
            return self._q.popleft() if self._q else None

    def report(self, record_id: str, result: dict) -> None:
        with self._lock:
            self.reported.append((record_id, result))

    def pending_count(self) -> int:
        with self._lock:
            return len(self._q)
