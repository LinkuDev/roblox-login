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

# Nut unlock co text CHINH XAC "Continue" (KHONG phai "Continue in App"/
# "Continue in browser" cua man app-promo -> tranh bam nham mo app store).
_HAS_CONTINUE = (
    "return [...document.querySelectorAll('button,[role=button]')]"
    ".some(x=>(x.innerText||'').trim().toLowerCase()==='continue');"
)
_CLICK_CONTINUE = (
    "const b=[...document.querySelectorAll('button,[role=button]')]"
    ".find(x=>(x.innerText||'').trim().toLowerCase()==='continue');"
    "if(b){b.scrollIntoView({block:'center'});b.click();return true;}return false;"
)


class HandleAccountLockedStep(Step):
    name = "handle_account_locked"
    optional = True          # khong phai acc nao cung bi khoa
    max_attempts = 3         # so lan bam Continue toi da

    def should_run(self, ctx: ExecutionContext) -> bool:
        return C.NOT_APPROVED_PATH in ctx.browser.current_url()

    def run(self, ctx: ExecutionContext) -> StepResult:
        # Toi man /not-approved -> CHUYEN sang MOBILE: thu nho CUA SO OS + emulate
        # viewport dien thoai + UA/CH mobile, roi reload de trang render lai mobile.
        ctx.browser.resize_window(*C.MOBILE_WINDOW)
        mw, mh = C.MOBILE_VIEWPORT
        ctx.browser.emulate(
            mw, mh, mobile=True,
            user_agent=C.MOBILE_USER_AGENT,
            client_hints=C.MOBILE_CLIENT_HINTS,
            scale_factor=3.0,
        )
        ctx.browser.reload()
        time.sleep(3)  # cho reload xong

        # Man doi APP MOBILE (quet QR, khong co Continue) -> bo tay, detect_result danh dau.
        if not ctx.browser.run_js(_HAS_CONTINUE):
            return StepResult.skipped(self.name, "khong co Continue - detect_result xu ly")

        s = ctx.settings.captcha
        for attempt in range(1, self.max_attempts + 1):
            clicked = bool(ctx.browser.run_js(_CLICK_CONTINUE))
            ctx.log.info("account_locked_continue", attempt=attempt, clicked=clicked)
            if not clicked:
                break  # khong con nut Continue -> co the da qua man khoa

            # cho extension giai Arkose sau khi bam Continue
            deadline = time.time() + s.timeout
            while time.time() < deadline:
                body = self._body(ctx)
                if C.NOT_APPROVED_PATH not in ctx.browser.current_url():
                    return StepResult.ok(self.name, "da mo khoa", attempts=attempt)
                if "continue in browser" in body:
                    # man app-promo xuat hien = da giai xong -> coi la mo khoa
                    return StepResult.ok(self.name, "da mo khoa (app-promo)", attempts=attempt)
                if any(k in body for k in ("scan this qr", "qr code")):
                    # doi APP MOBILE (quet QR) -> bo tay, de detect_result danh dau
                    ctx.log.info("account_locked_need_app", attempt=attempt)
                    return StepResult.skipped(self.name, "doi app mobile - detect_result xu ly")
                if any(k in body for k in ("try unlocking again", "weren't able to unlock")):
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
