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
    totp_secret: str | None = None   # tu SaaS claim -> can cho acc 2FA
    email: str | None = None


class PoolClient(Protocol):
    def has_work(self) -> bool: ...
    def claim(self) -> Record | None: ...
    def report(self, record_id: str, result: dict) -> None: ...
    def pending_count(self) -> int: ...
    def heartbeat(self, record_id: str) -> bool: ...   # gia han lease; local -> no-op


class LocalPool:
    """Pool local: hang doi record trong RAM. Dung de demo/test agent."""

    def __init__(self) -> None:
        self._q: deque[Record] = deque()
        self._lock = threading.Lock()
        self.reported: list[tuple[str, dict]] = []
        # trang thai vong doi tung record: pending -> running -> success|failed
        self._status: dict[str, str] = {}

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
                # format "user:pass" hoac "user:pass:cookie" (cookie chua ':' ->
                # chi tach 2 ':' dau, bo phan cookie vi login chi can user/pass).
                parts = line.split(":", 2)
                u, p = parts[0].strip(), parts[1].strip()
                if u and p:
                    rid = f"line-{idx}"
                    self._q.append(Record(rid, u, p))
                    self._status[rid] = "pending"
                    added += 1
        return added

    def has_work(self) -> bool:
        with self._lock:
            return bool(self._q)

    def claim(self) -> Record | None:
        with self._lock:
            if not self._q:
                return None
            rec = self._q.popleft()
            self._status[rec.id] = "running"   # doi trang thai khi spawn
            return rec

    def report(self, record_id: str, result: dict) -> None:
        with self._lock:
            self.reported.append((record_id, result))
            # doi trang thai DB khi flow xong: success (da giai + dang nhap) / failed
            self._status[record_id] = "success" if result.get("success") else "failed"

    def statuses(self) -> dict[str, int]:
        """Dem record theo trang thai (cho UI/kiem tra)."""
        out: dict[str, int] = {}
        with self._lock:
            for s in self._status.values():
                out[s] = out.get(s, 0) + 1
        return out

    def pending_count(self) -> int:
        with self._lock:
            return len(self._q)

    def heartbeat(self, record_id: str) -> bool:  # noqa: ARG002 - local khong co lease
        return True
