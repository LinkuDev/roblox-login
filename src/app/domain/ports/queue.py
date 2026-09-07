from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class JobQueue(ABC):
    """Hang doi job. memory (dev) -> redis/rq -> celery ma khong sua caller."""

    name: str = "base"

    @abstractmethod
    def enqueue(self, job_id: str, payload: dict[str, Any]) -> str: ...

    @abstractmethod
    def dequeue(self, timeout: int = 5) -> tuple[str, dict[str, Any]] | None: ...

    @abstractmethod
    def size(self) -> int: ...
