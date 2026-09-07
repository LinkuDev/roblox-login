from unittest.mock import MagicMock

from app.automation.context import ExecutionContext
from app.automation.flow import Flow
from app.automation.result import StepResult
from app.automation.step import Step
from app.core.enums import StepOutcome
from app.domain.models import Credential


def _ctx():
    return ExecutionContext(
        credential=Credential("u", "p"),
        browser=MagicMock(),
        solver=MagicMock(),
    )


class OkStep(Step):
    name = "ok"

    def run(self, ctx):
        return StepResult.ok(self.name)


class FailStep(Step):
    name = "fail"

    def run(self, ctx):
        return StepResult.failed(self.name, "boom", "boom_code")


class FlakyStep(Step):
    name = "flaky"
    max_retries = 2

    def __init__(self):
        self.calls = 0

    def run(self, ctx):
        self.calls += 1
        if self.calls < 3:
            raise RuntimeError("transient")
        return StepResult.ok(self.name)


def test_flow_success():
    result = Flow("t", [OkStep(), OkStep()]).run(_ctx())
    assert result.success
    assert len(result.steps) == 2


def test_flow_stops_on_required_failure():
    result = Flow("t", [OkStep(), FailStep(), OkStep()]).run(_ctx())
    assert not result.success
    assert result.error_code == "boom_code"
    assert len(result.steps) == 2  # step sau khong chay


def test_optional_step_does_not_break_flow():
    fail = FailStep()
    fail.optional = True
    result = Flow("t", [fail, OkStep()]).run(_ctx())
    assert result.success


def test_step_retry_recovers():
    flaky = FlakyStep()
    flaky.retry_delay = 0
    result = Flow("t", [flaky]).run(_ctx())
    assert result.success
    assert flaky.calls == 3


def test_skipped_step():
    class Cond(OkStep):
        name = "cond"

        def should_run(self, ctx):
            return False

    result = Flow("t", [Cond()]).run(_ctx())
    assert result.steps[0].outcome is StepOutcome.SKIPPED
