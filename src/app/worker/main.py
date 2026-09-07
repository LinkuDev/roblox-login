"""Worker: keo job tu queue va chay. Chay nhieu instance de scale.

  python -m app.worker.main
"""

from __future__ import annotations

import signal

from app.core.logging import get_logger, setup_logging
from app.modules.jobs import build_queue, execute_job

log = get_logger("worker")
_running = True


def _stop(*_):
    global _running
    _running = False
    log.info("worker_stopping")


def main() -> None:
    setup_logging()
    signal.signal(signal.SIGINT, _stop)
    signal.signal(signal.SIGTERM, _stop)

    queue = build_queue()
    log.info("worker_started", backend=queue.name)

    while _running:
        item = queue.dequeue(timeout=5)
        if item is None:
            continue
        job_id, _payload = item
        log.info("job_picked", job_id=job_id)
        try:
            result = execute_job(job_id)
            log.info("job_finished", job_id=job_id, **result)
        except Exception as exc:  # worker khong duoc chet vi 1 job loi
            log.error("job_crashed", job_id=job_id, error=str(exc))


if __name__ == "__main__":
    main()
