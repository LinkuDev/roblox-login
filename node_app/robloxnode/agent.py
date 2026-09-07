"""NodeAgent: vong lap always-on.

start() -> lang nghe pool, claim khi con headroom (RAM < diem tran & slot < tran cung),
moi record chay 1 flow trong 1 slot (thread) song song, xong thi report.
stop()  -> ngung lang nghe (khong claim moi), slot dang chay xong thi thoi (drain).

Agent doc lap voi:
  - pool     : PoolClient (LocalPool hom nay, WsPool sau)
  - run_flow : callable(Record) -> dict (stub hom nay, run_service that sau)
"""

from __future__ import annotations

import os
import threading
import time
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor

import psutil

from robloxnode.pool import PoolClient, Record


def _default_hard_cap() -> int:
    return max(2, min(8, (os.cpu_count() or 2)))


class NodeAgent:
    def __init__(
        self,
        pool: PoolClient,
        run_flow: Callable[[Record], dict],
        get_overflow_percent: Callable[[], int],
        *,
        hard_cap: int | None = None,
        poll_interval: float = 1.0,
        settle_delay: float = 1.2,
    ) -> None:
        self.pool = pool
        self.run_flow = run_flow
        self.get_overflow_percent = get_overflow_percent
        self.hard_cap = hard_cap or _default_hard_cap()
        self.poll = poll_interval
        self.settle = settle_delay

        self._lock = threading.Lock()
        self._running = False
        self._sup: threading.Thread | None = None
        self._exec: ThreadPoolExecutor | None = None
        self._active: dict[str, dict] = {}   # record_id -> {username, since}
        self._claimed = 0
        self._done = 0
        self._failed = 0

    # --- dieu khien ---------------------------------------------------------
    def start(self) -> None:
        with self._lock:
            if self._running:
                return
            self._running = True
            self._exec = ThreadPoolExecutor(max_workers=self.hard_cap)
        self._sup = threading.Thread(target=self._supervise, name="node-supervisor", daemon=True)
        self._sup.start()

    def stop(self) -> None:
        with self._lock:
            self._running = False
            ex = self._exec
            self._exec = None
        if ex:
            ex.shutdown(wait=False)   # slot dang chay xong thi thoi, khong nhan moi

    # --- vong lap -----------------------------------------------------------
    def _supervise(self) -> None:
        while self._running:
            if self._can_claim():
                record = self.pool.claim()
                if record is None:
                    time.sleep(self.poll)
                    continue
                self._start_slot(record)
                time.sleep(self.settle)   # hysteresis: cho slot moi on dinh RAM
            else:
                time.sleep(self.poll)

    def _can_claim(self) -> bool:
        if not self._running:
            return False
        ram = psutil.virtual_memory().percent
        with self._lock:
            n_active = len(self._active)
        return (
            ram < self.get_overflow_percent()
            and n_active < self.hard_cap
            and self.pool.has_work()
        )

    def _start_slot(self, record: Record) -> None:
        with self._lock:
            self._active[record.id] = {"username": record.username, "since": time.time()}
            self._claimed += 1
            ex = self._exec
        if ex is not None:
            ex.submit(self._run_one, record)

    def _run_one(self, record: Record) -> None:
        try:
            result = self.run_flow(record)
            self.pool.report(record.id, result)
            with self._lock:
                if result.get("success"):
                    self._done += 1
                else:
                    self._failed += 1
        except Exception:  # 1 slot loi khong duoc lam chet agent
            with self._lock:
                self._failed += 1
        finally:
            with self._lock:
                self._active.pop(record.id, None)

    # --- trang thai cho UI --------------------------------------------------
    def status(self) -> dict:
        ram = psutil.virtual_memory().percent
        overflow = self.get_overflow_percent()
        now = time.time()
        with self._lock:
            slots = [
                {"username": v["username"], "elapsed": round(now - v["since"], 1)}
                for v in self._active.values()
            ]
            claimed, done, failed = self._claimed, self._done, self._failed
            active = len(self._active)
        return {
            "listening": self._running,
            "active_slots": active,
            "hard_cap": self.hard_cap,
            "claimed": claimed,
            "done": done,
            "failed": failed,
            "pending": self.pool.pending_count(),
            "ram_percent": round(ram, 1),
            "overflow_at": overflow,
            "full": ram >= overflow,
            "slots": slots,
        }
