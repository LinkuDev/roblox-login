from __future__ import annotations

from app.automation.context import ExecutionContext
from app.automation.result import StepResult
from app.automation.step import Step
from app.services.roblox import constants as C


class OpenLoginPageStep(Step):
    name = "open_login"
    max_retries = 2   # loi mang -> thu lai

    def run(self, ctx: ExecutionContext) -> StepResult:
        # Trang login = trai nghiem DESKTOP, y het PC:
        # - MAXIMIZE cua so -> fullwidth nhu mo tren may tinh (form hien day du).
        #   (Grid tiling chi ap dung khi chuyen sang MOBILE o man /not-approved.)
        # - set UA + Client Hints desktop (KHONG ep viewport -> viewport = cua so that).
        ctx.browser.maximize_window()
        ctx.browser.emulate(
            0, 0, mobile=False,
            user_agent=C.DESKTOP_USER_AGENT,
            client_hints=C.DESKTOP_CLIENT_HINTS,
            set_metrics=False,
        )
        ctx.browser.goto(C.LOGIN_URL, wait=3)
        # da dang nhap san (profile cu)? Kiem tra bang COOKIE session that, KHONG
        # dua vao navbar - .rbx-navbar co mat ca khi CHUA dang nhap -> de bao nham.
        if C.COOKIE_SESSION in ctx.browser.cookies():
            ctx.set("already_logged_in", True)
            return StepResult.ok(self.name, "da co phien dang nhap san")
        ctx.browser.wait_for(C.SEL_USERNAME)
        return StepResult.ok(self.name, "trang login da san sang")
