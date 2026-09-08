from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from app.core.enums import StepOutcome


@dataclass(slots=True)
class StepResult:
    step: str
    outcome: StepOutcome
    message: str = ""
    duration: float = 0.0
    data: dict[str, Any] = field(default_factory=dict)
    error_code: str | None = None

    @classmethod
    def ok(cls, step: str, message: str = "", **data) -> StepResult:
        return cls(step, StepOutcome.OK, message, data=data)

    @classmethod
    def skipped(cls, step: str, message: str = "") -> StepResult:
        return cls(step, StepOutcome.SKIPPED, message)

    @classmethod
    def retry(cls, step: str, message: str = "") -> StepResult:
        return cls(step, StepOutcome.RETRY, message)

    @classmethod
    def failed(cls, step: str, message: str, error_code: str | None = None) -> StepResult:
        return cls(step, StepOutcome.FAILED, message, error_code=error_code)

    def to_dict(self) -> dict:
        return {
            "step": self.step,
            "outcome": str(self.outcome),
            "message": self.message,
            "duration": round(self.duration, 3),
            "error_code": self.error_code,
            "data": self.data,
        }


@dataclass(slots=True)
class RunResult:
    """Ket qua 1 lan chay service - day chinh la thu tra ve cho order/API."""

    service: str
    success: bool
    data: dict[str, Any] = field(default_factory=dict)
    error_code: str | None = None
    error_message: str = ""
    steps: list[StepResult] = field(default_factory=list)
    artifacts: list[str] = field(default_factory=list)
    cost: dict[str, float] = field(default_factory=dict)   # vd {"captcha": 0.0029}
    started_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    finished_at: datetime | None = None

    @property
    def duration(self) -> float:
        end = self.finished_at or datetime.now(timezone.utc)
        return (end - self.started_at).total_seconds()

    def to_dict(self) -> dict:
        return {
            "service": self.service,
            "success": self.success,
            "data": self.data,
            "error": {"code": self.error_code, "message": self.error_message}
            if not self.success
            else None,
            "steps": [s.to_dict() for s in self.steps],
            "artifacts": self.artifacts,
            "cost": self.cost,
            "duration": round(self.duration, 2),
            "started_at": self.started_at.isoformat(),
            "finished_at": self.finished_at.isoformat() if self.finished_at else None,
        }
