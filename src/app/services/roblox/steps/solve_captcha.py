"""Step giai captcha - day la vi du cach step goi solver qua PORT.

Luong that te voi Arkose FunCaptcha co the phuc tap hon (lay blob tu
enforcement, inject token vao callback). Phan lay blob/inject de TODO ro rang
vi phu thuoc vao chi tiet runtime cua Roblox tai thoi diem chay.
"""

from __future__ import annotations

from app.automation.context import ExecutionContext
from app.automation.result import StepResult
from app.automation.step import Step
from app.core.errors import CaptchaError
from app.domain.models import CaptchaTask
from app.services.roblox import constants as C


class SolveCaptchaStep(Step):
    name = "solve_captcha"
    optional = True          # khong phai lan login nao cung dinh captcha
    max_retries = 1          # giai truot thi thu lai 1 lan

    def should_run(self, ctx: ExecutionContext) -> bool:
        if ctx.get("already_logged_in"):
            return False
        # chi chay khi phat hien khung captcha
        return ctx.browser.exists(C.SEL_CAPTCHA_FRAME, timeout=5)

    def run(self, ctx: ExecutionContext) -> StepResult:
        blob = self._extract_blob(ctx)

        task = CaptchaTask(
            type=C.CAPTCHA_TYPE,
            website_url=C.LOGIN_URL,
            website_key=C.FUNCAPTCHA_PUBLIC_KEY,
            api_subdomain=C.FUNCAPTCHA_API_SUBDOMAIN,
            blob=blob,
            proxy=ctx.proxy,
            user_agent=ctx.browser.user_agent() or None,
        )

        solution = ctx.solver.solve(task)          # <-- goi PORT, khong biet provider nao
        ctx.add_cost("captcha", solution.cost)
        ctx.set("captcha_token", solution.token)
        ctx.set("captcha_solution", solution)

        if not self._inject_token(ctx, solution.token):
            raise CaptchaError("khong inject duoc token vao trang")

        return StepResult.ok(
            self.name,
            f"giai captcha xong ({solution.provider})",
            provider=solution.provider,
            seconds=solution.solve_seconds,
        )

    # --- cac phan phu thuoc runtime Roblox: khoanh vung ro rang -----------
    def _extract_blob(self, ctx: ExecutionContext) -> str | None:
        """Lay dataExchangeBlob tu enforcement cua Arkose.

        TODO(flow): dien khi ban da xem duoc luong that. Thuong doc tu bien
        toan cuc/JS event cua Arkose. Tra None neu khong can blob.
        """
        try:
            return ctx.browser.run_js(
                "return window.__ARKOSE_BLOB__ || null;"
            )
        except Exception:
            return None

    def _inject_token(self, ctx: ExecutionContext, token: str) -> bool:
        """Bom token da giai vao callback cua Arkose de Roblox chap nhan.

        TODO(flow): dien callback that. Placeholder tra True de flow chay thong
        khi test voi manual solver.
        """
        ctx.log.debug("inject_token_placeholder", token_len=len(token))
        return True
