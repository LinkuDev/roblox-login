"""Flow engine: chay danh sach Step theo thu tu, xu ly retry / optional / loi."""

from __future__ import annotations

import time

from app.automation.context import ExecutionContext
from app.automation.result import RunResult, StepResult
from app.automation.step import Step
from app.core.enums import StepOutcome
from app.core.errors import AppError, AutomationError, StepFailed


class Flow:
    def __init__(self, name: str, steps: list[Step]):
        self.name = name
        self.steps = steps

    def run(self, ctx: ExecutionContext) -> RunResult:
        result = RunResult(service=self.name, success=False)
        ctx.log.info("flow_start", flow=self.name, steps=len(self.steps))

        for step in self.steps:
            if not step.should_run(ctx):
                result.steps.append(StepResult.skipped(step.name, "dieu kien khong thoa"))
                continue

            step_result = self._run_step(step, ctx)
            step_result.duration = step_result.duration
            result.steps.append(step_result)

            if step_result.outcome is StepOutcome.FAILED and not step.optional:
                result.error_code = step_result.error_code or "step_failed"
                result.error_message = step_result.message
                self._finalize(ctx, result)
                ctx.log.warning(
                    "flow_failed", flow=self.name, step=step.name, error=result.error_message
                )
                return result

        result.success = True
        self._finalize(ctx, result)
        ctx.log.info("flow_success", flow=self.name, duration=result.duration)
        return result

    # ------------------------------------------------------------------
    def _run_step(self, step: Step, ctx: ExecutionContext) -> StepResult:
        attempts = step.max_retries + 1
        last: StepResult | None = None

        for attempt in range(1, attempts + 1):
            started = time.perf_counter()
            log = ctx.log.bind(step=step.name, attempt=attempt)
            try:
                log.debug("step_start")
                res = step.run(ctx)
                res.duration = time.perf_counter() - started

                if res.outcome is StepOutcome.RETRY and attempt < attempts:
                    log.info("step_retry", reason=res.message)
                    last = res
                    time.sleep(step.retry_delay)
                    continue

                if res.outcome is StepOutcome.RETRY:
                    res = StepResult.failed(step.name, res.message or "het luot retry", "retry_exhausted")
                    res.duration = time.perf_counter() - started

                log.info("step_done", outcome=str(res.outcome), duration=round(res.duration, 2))
                return res

            except AutomationError as exc:
                # loi nghiep vu (sai mat khau, 2FA...) -> khong retry
                step.on_error(ctx, exc)
                if step.snapshot_on_error:
                    ctx.snapshot(f"{step.name}_error")
                log.warning("step_error", code=exc.code, error=exc.message)
                res = StepResult.failed(step.name, exc.message, exc.code)
                res.duration = time.perf_counter() - started
                res.data = exc.context
                return res

            except (AppError, Exception) as exc:  # noqa: B014 - loi ha tang -> co the retry
                step.on_error(ctx, exc)
                code = getattr(exc, "code", exc.__class__.__name__)
                log.warning("step_exception", code=code, error=str(exc))
                last = StepResult.failed(step.name, str(exc), code)
                last.duration = time.perf_counter() - started
                if attempt < attempts:
                    time.sleep(step.retry_delay)
                    continue
                if step.snapshot_on_error:
                    ctx.snapshot(f"{step.name}_error")
                return last

        return last or StepResult.failed(step.name, "khong chay duoc", "unknown")

    def _finalize(self, ctx: ExecutionContext, result: RunResult) -> None:
        from datetime import UTC, datetime

        result.finished_at = datetime.now(UTC)
        result.artifacts = list(ctx.artifacts)
        result.cost = dict(ctx.cost)


__all__ = ["Flow", "StepFailed"]
