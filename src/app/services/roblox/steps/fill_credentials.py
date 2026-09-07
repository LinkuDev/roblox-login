from __future__ import annotations

from app.automation.context import ExecutionContext
from app.automation.result import StepResult
from app.automation.step import Step
from app.services.roblox import constants as C


class FillCredentialsStep(Step):
    name = "fill_credentials"

    def should_run(self, ctx: ExecutionContext) -> bool:
        return not ctx.get("already_logged_in")

    def run(self, ctx: ExecutionContext) -> StepResult:
        cred = ctx.credential
        ctx.browser.type(C.SEL_USERNAME, cred.username, human=True)
        ctx.browser.type(C.SEL_PASSWORD, cred.password, human=True)
        return StepResult.ok(self.name, "da dien tk/mk")
