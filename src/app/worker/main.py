"""Worker: keo job tu queue va chay. Chay nhieu instance de scale.

  python -m app.worker.main
"""

from __future__ import annotations

import signal

from app.core.logging import get_logger, setup_logging
from app.modules.jobs import build_queue, process_record

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
        record_id, _payload = item
        log.info("record_picked", record_id=record_id)
        try:
            result = process_record(record_id)
            log.info("record_finished", record_id=record_id, **result)
        except Exception as exc:  # worker khong duoc chet vi 1 record loi
            log.error("record_crashed", record_id=record_id, error=str(exc))


if __name__ == "__main__":
    main()
