from __future__ import annotations

import queue
from typing import Any

from app.domain.ports import JobQueue


class MemoryQueue(JobQueue):
    """Hang doi in-process cho dev/test. Prod dung Redis."""

    name = "memory"

    def __init__(self, settings=None):
        self._q: queue.Queue[tuple[str, dict]] = queue.Queue()

    def enqueue(self, job_id: str, payload: dict[str, Any]) -> str:
        self._q.put((job_id, payload))
        return job_id

    def dequeue(self, timeout: int = 5) -> tuple[str, dict[str, Any]] | None:
        try:
            return self._q.get(timeout=timeout)
        except queue.Empty:
            return None

    def size(self) -> int:
        return self._q.qsize()
