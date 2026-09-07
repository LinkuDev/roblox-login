from __future__ import annotations

from functools import lru_cache

from app.core.config import get_settings
from app.domain.ports import JobQueue


@lru_cache
def build_queue(backend: str | None = None) -> JobQueue:
    settings = get_settings()
    backend = (backend or settings.queue.queue_backend).lower()
    if backend == "redis":
        from app.modules.jobs.queue_redis import RedisQueue

        return RedisQueue(settings.queue)
    from app.modules.jobs.queue_memory import MemoryQueue

    return MemoryQueue(settings.queue)
