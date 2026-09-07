from __future__ import annotations

from app.automation.context import ExecutionContext
from app.automation.result import StepResult
from app.automation.step import Step
from app.services.roblox import constants as C


class SubmitLoginStep(Step):
    name = "submit_login"

    def should_run(self, ctx: ExecutionContext) -> bool:
        return not ctx.get("already_logged_in")

    def run(self, ctx: ExecutionContext) -> StepResult:
        ctx.browser.click(C.SEL_SUBMIT)
        # cho phan hoi: hoac captcha hien ra, hoac vao home, hoac bao loi
        return StepResult.ok(self.name, "da bam dang nhap")
