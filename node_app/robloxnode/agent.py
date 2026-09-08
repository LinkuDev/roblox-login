"""NodeAgent: vong lap always-on.

start() -> lang nghe pool, claim khi con headroom (RAM < diem tran & slot < max),
moi record chay 1 flow trong 1 LUONG rieng (thread) song song, spawn browser vao 1
o luoi trong (khong de nhau), xong thi report + persist DB + tra o cho record sau.
stop()  -> ngung claim moi; slot dang chay xong thi thoi (drain).

Doc lap voi:
  - pool     : PoolClient (LocalPool hom nay, WsPool sau)
  - run_flow : callable(Record, placement|None) -> dict
  - store    : ResultStore | None (ghi ket qua ca success lan failed)
  - layout   : SlotAllocator | None (chia o cua so; None -> khong dat vi tri)
"""

from __future__ import annotations

import os
import threading
import time
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from contextlib import suppress

import psutil

from robloxnode.layout import SlotAllocator
from robloxnode.pool import PoolClient, Record
from robloxnode.store import ResultStore


def _default_max_concurrent() -> int:
    return max(2, os.cpu_count() or 4)


class NodeAgent:
    def __init__(
        self,
        pool: PoolClient,
        run_flow: Callable[[Record, dict | None], dict],
        get_overflow_percent: Callable[[], int],
        *,
        get_max_concurrent: Callable[[], int] | None = None,
        get_layout: Callable[[], SlotAllocator | None] | None = None,
        store: ResultStore | None = None,
        poll_interval: float = 1.0,
        settle_delay: float = 1.2,
    ) -> None:
        self.pool = pool
        self.run_flow = run_flow
        self.get_overflow_percent = get_overflow_percent
        self.get_max_concurrent = get_max_concurrent or _default_max_concurrent
        self.get_layout = get_layout
        self.store = store
        self.poll = poll_interval
        self.settle = settle_delay

        self._lock = threading.Lock()
        self._running = False
        self._sup: threading.Thread | None = None
        self._exec: ThreadPoolExecutor | None = None
        self._layout: SlotAllocator | None = None
        self.hard_cap = self.get_max_concurrent()
        self._active: dict[str, dict] = {}   # record_id -> {username, since, slot}
        self._claimed = 0
        self._done = 0
        self._failed = 0

    # --- dieu khien ---------------------------------------------------------
    def start(self) -> None:
        with self._lock:
            if self._running:
                return
            self._running = True
            self.hard_cap = max(1, self.get_max_concurrent())
            self._layout = self.get_layout() if self.get_layout else None
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
            layout = self._layout
            slot = layout.acquire() if layout else None
            placement = layout.placement(slot) if (layout and slot is not None) else None
            self._active[record.id] = {
                "username": record.username, "since": time.time(), "slot": slot,
            }
            self._claimed += 1
            ex = self._exec
        if ex is not None:
            ex.submit(self._run_one, record, slot, placement)

    def _run_one(self, record: Record, slot: int | None, placement: dict | None) -> None:
        result: dict = {"success": False, "error": "unknown", "reason": ""}
        try:
            result = self.run_flow(record, placement)
        except Exception as exc:  # 1 slot loi khong duoc lam chet agent
            result = {"success": False, "error": "exception", "reason": repr(exc)}
        finally:
            # doi trang thai DB (pool) + persist ket qua: CA success lan failed,
            # ke ca khi exception. Loi ghi khong duoc lam chet slot.
            with suppress(Exception):
                self.pool.report(record.id, result)
            if self.store is not None:
                with suppress(Exception):
                    self.store.save(record, result)
            with self._lock:
                if result.get("success"):
                    self._done += 1
                else:
                    self._failed += 1
                self._active.pop(record.id, None)
                if self._layout and slot is not None:
                    self._layout.release(slot)   # tra o cho record sau lap vao

    # --- trang thai cho UI --------------------------------------------------
    def status(self) -> dict:
        ram = psutil.virtual_memory().percent
        overflow = self.get_overflow_percent()
        now = time.time()
        with self._lock:
            slots = [
                {
                    "username": v["username"],
                    "elapsed": round(now - v["since"], 1),
                    "slot": v["slot"],
                }
                for v in self._active.values()
            ]
            claimed, done, failed = self._claimed, self._done, self._failed
            active = len(self._active)
        db_status = self.pool.statuses() if hasattr(self.pool, "statuses") else {}
        return {
            "listening": self._running,
            "active_slots": active,
            "hard_cap": self.hard_cap,
            "claimed": claimed,
            "done": done,
            "failed": failed,
            "db_status": db_status,
            "pending": self.pool.pending_count(),
            "ram_percent": round(ram, 1),
            "overflow_at": overflow,
            "full": ram >= overflow,
            "slots": slots,
        }
