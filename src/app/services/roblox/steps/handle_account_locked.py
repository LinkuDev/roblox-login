"""Man "Account locked" hau dang nhap (/not-approved).

Sau khi login co cookie, Roblox co the chuyen sang /not-approved ("We've detected
suspicious activity... confirm you're a human"). Nut Continue nam trong DOM -> bam
bang automation -> Arkose hien -> extension YesCaptcha tu giai. Neu that bai hien
"Try unlocking again" -> bam Continue lai (toi da max_attempts lan).
"""

from __future__ import annotations

import time

from app.automation.context import ExecutionContext
from app.automation.result import StepResult
from app.automation.step import Step
from app.services.roblox import constants as C

# tim nut Continue theo text (con trong DOM)
_HAS_CONTINUE = (
    "return [...document.querySelectorAll('button,[role=button]')]"
    ".some(x=>/continue/i.test(x.innerText||''));"
)
# tim nut Continue va bam
_CLICK_CONTINUE = (
    "const b=[...document.querySelectorAll('button,[role=button]')]"
    ".find(x=>/continue/i.test(x.innerText||''));"
    "if(b){b.scrollIntoView({block:'center'});b.click();return true;}return false;"
)


class HandleAccountLockedStep(Step):
    name = "handle_account_locked"
    optional = True          # khong phai acc nao cung bi khoa
    max_attempts = 3         # so lan bam Continue toi da

    def should_run(self, ctx: ExecutionContext) -> bool:
        # Chi chay khi o /not-approved VA co nut Continue de bam. Neu la bien the
        # doi APP MOBILE (quet QR, khong co Continue) -> bo qua, detect_result se
        # danh dau need_mobile_app.
        if C.NOT_APPROVED_PATH not in ctx.browser.current_url():
            return False
        return bool(ctx.browser.run_js(_HAS_CONTINUE))

    def run(self, ctx: ExecutionContext) -> StepResult:
        s = ctx.settings.captcha
        for attempt in range(1, self.max_attempts + 1):
            clicked = bool(ctx.browser.run_js(_CLICK_CONTINUE))
            ctx.log.info("account_locked_continue", attempt=attempt, clicked=clicked)
            if not clicked:
                break  # khong con nut Continue -> co the da qua man khoa

            # cho extension giai Arkose sau khi bam Continue
            deadline = time.time() + s.timeout
            while time.time() < deadline:
                if C.NOT_APPROVED_PATH not in ctx.browser.current_url():
                    return StepResult.ok(self.name, "da mo khoa", attempts=attempt)
                if self._needs_app(ctx):
                    # doi APP MOBILE (quet QR) -> bo tay, de detect_result danh dau
                    ctx.log.info("account_locked_need_app", attempt=attempt)
                    return StepResult.skipped(self.name, "doi app mobile - detect_result xu ly")
                if self._needs_retry(ctx):
                    ctx.log.info("account_locked_retry_prompt", attempt=attempt)
                    break  # thoat vong cho -> bam Continue lai
                time.sleep(s.poll_interval)

        if C.NOT_APPROVED_PATH not in ctx.browser.current_url():
            return StepResult.ok(self.name, "da mo khoa")
        ctx.snapshot("account_locked")
        return StepResult.failed(
            self.name, "khong mo khoa duoc (Arkose chua giai)", "account_locked"
        )

    def _body(self, ctx: ExecutionContext) -> str:
        return ctx.browser.text_of("body").lower()

    def _needs_retry(self, ctx: ExecutionContext) -> bool:
        """Man 'Try unlocking again' = lan giai vua roi that bai -> can bam lai."""
        txt = self._body(ctx)
        return any(k in txt for k in ("try unlocking again", "weren't able to unlock", "try again"))

    def _needs_app(self, ctx: ExecutionContext) -> bool:
        """Bien the doi xac thuc bang app mobile (quet QR)."""
        txt = self._body(ctx)
        return any(k in txt for k in ("mobile app", "qr code", "scan this qr"))
