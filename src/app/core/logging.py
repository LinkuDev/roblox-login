"""structlog: log co cau truc, bind duoc job_id/username -> de trace tung don."""

from __future__ import annotations

import logging
import sys

import structlog

from app.core.config import get_settings

_configured = False


def setup_logging(level: str | None = None, json_output: bool | None = None) -> None:
    global _configured
    if _configured:
        return

    s = get_settings().app
    level = level or s.log_level
    json_output = s.log_json if json_output is None else json_output

    logging.basicConfig(format="%(message)s", stream=sys.stdout, level=level.upper())

    processors = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]
    processors.append(
        structlog.processors.JSONRenderer()
        if json_output
        else structlog.dev.ConsoleRenderer(colors=True)
    )

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(
            logging.getLevelNamesMapping()[level.upper()]
        ),
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )
    _configured = True


def get_logger(name: str = "app", **initial):
    setup_logging()
    return structlog.get_logger(name).bind(**initial)


def mask(value: str, keep: int = 2) -> str:
    """Che password/token khi log."""
    if not value:
        return ""
    if len(value) <= keep * 2:
        return "*" * len(value)
    return f"{value[:keep]}{'*' * (len(value) - keep * 2)}{value[-keep:]}"
