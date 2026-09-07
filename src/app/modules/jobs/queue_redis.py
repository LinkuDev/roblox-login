from __future__ import annotations

import json
from typing import Any

from app.core.config import get_settings
from app.domain.ports import JobQueue

_QUEUE_KEY = "rlx:jobs"


class RedisQueue(JobQueue):
    """Hang doi Redis - dung khi scale nhieu worker."""

    name = "redis"

    def __init__(self, settings=None):
        import redis  # optional dependency

        url = (settings or get_settings().queue).redis_url
        self._r = redis.Redis.from_url(url)

    def enqueue(self, job_id: str, payload: dict[str, Any]) -> str:
        self._r.rpush(_QUEUE_KEY, json.dumps({"job_id": job_id, "payload": payload}))
        return job_id

    def dequeue(self, timeout: int = 5) -> tuple[str, dict[str, Any]] | None:
        item = self._r.blpop(_QUEUE_KEY, timeout=timeout)
        if not item:
            return None
        data = json.loads(item[1])
        return data["job_id"], data["payload"]

    def size(self) -> int:
        return int(self._r.llen(_QUEUE_KEY))
