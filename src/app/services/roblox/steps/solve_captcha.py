"""Step giai captcha.

2 che do:
- EXTENSION (uu tien): extension YesCaptcha nap trong browser tu giai Arkose
  in-page. Step chi CHO toi khi khung captcha bien mat / co cookie (khong goi API).
- API (cu): goi solver qua PORT roi inject token. Phan lay blob/inject con TODO
  vi phu thuoc runtime Roblox.
"""

from __future__ import annotations

import time
from pathlib import Path

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
        # chi chay khi phat hien khung captcha (Arkose co the load cham hon 5s)
        return ctx.browser.exists(C.SEL_CAPTCHA_FRAME, timeout=10)

    def run(self, ctx: ExecutionContext) -> StepResult:
        if self._extension_mode(ctx):
            return self._wait_for_extension(ctx)
        return self._solve_via_api(ctx)

    # --- che do EXTENSION ---------------------------------------------------
    def _extension_mode(self, ctx: ExecutionContext) -> bool:
        d = ctx.settings.browser.captcha_extension_dir
        return bool(d and Path(d).exists())

    def _wait_for_extension(self, ctx: ExecutionContext) -> StepResult:
        """Cho extension YesCaptcha tu giai captcha in-page.

        Ket thuc som khi: co cookie session (da qua), hoac khung captcha bien mat.
        Het thoi gian -> fail (optional -> khong lam sap flow, detect_result quyet).
        """
        s = ctx.settings.captcha
        deadline = time.time() + s.timeout
        ctx.log.info("captcha_wait_extension", timeout=s.timeout)
        while time.time() < deadline:
            if C.COOKIE_SESSION in ctx.browser.cookies():
                return StepResult.ok(self.name, "extension giai xong (co cookie session)")
            if not ctx.browser.exists(C.SEL_CAPTCHA_FRAME, timeout=0):
                return StepResult.ok(self.name, "khung captcha da bien mat (extension xu ly)")
            time.sleep(s.poll_interval)
        ctx.snapshot("captcha_timeout")
        return StepResult.failed(self.name, "extension khong giai kip captcha", "captcha_timeout")

    # --- che do API (cu) ----------------------------------------------------
    def _solve_via_api(self, ctx: ExecutionContext) -> StepResult:
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
