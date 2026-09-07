from __future__ import annotations

from app.automation.context import ExecutionContext
from app.automation.result import StepResult
from app.automation.step import Step
from app.services.roblox import constants as C


class OpenLoginPageStep(Step):
    name = "open_login"
    max_retries = 2   # loi mang -> thu lai

    def run(self, ctx: ExecutionContext) -> StepResult:
        ctx.browser.goto(C.LOGIN_URL, wait=3)
        # da dang nhap san (profile cu)?
        if ctx.browser.exists(C.SEL_LOGGED_IN, timeout=2):
            ctx.set("already_logged_in", True)
            return StepResult.ok(self.name, "da co phien dang nhap san")
        ctx.browser.wait_for(C.SEL_USERNAME)
        return StepResult.ok(self.name, "trang login da san sang")
