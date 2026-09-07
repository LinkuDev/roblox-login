from __future__ import annotations

from abc import ABC, abstractmethod

from app.automation.context import ExecutionContext
from app.automation.result import StepResult


class Step(ABC):
    """Mot buoc trong flow.

    Quy uoc:
      - `name`      : id cua buoc, dung de log/trace.
      - `optional`  : buoc that bai khong lam hong ca flow (vd: 2FA khi tk khong bat).
      - `max_retries`: so lan thu lai rieng cua buoc (vd captcha giai truot).
      - `should_run`: dieu kien chay, doc tu ctx.
    """

    name: str = "step"
    optional: bool = False
    max_retries: int = 0
    retry_delay: float = 2.0
    snapshot_on_error: bool = True

    def should_run(self, ctx: ExecutionContext) -> bool:
        return True

    @abstractmethod
    def run(self, ctx: ExecutionContext) -> StepResult:
        """Thuc thi buoc. Tra StepResult, hoac raise AutomationError."""

    def on_error(self, ctx: ExecutionContext, exc: Exception) -> None:
        """Hook don dep khi buoc loi."""

    def __repr__(self) -> str:
        return f"<Step {self.name}>"
