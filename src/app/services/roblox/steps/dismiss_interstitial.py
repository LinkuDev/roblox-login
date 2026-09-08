"""Man app-promo mobile: "Explore Roblox in our mobile app!" voi 2 nut
"Continue in App" / "Continue in browser".

Xuat hien SAU khi giai/dang nhap thanh cong (do dung mobile UA). Bam
"Continue in browser" de vao trang that -> coi nhu da thanh cong (detect_result
se thay cookie). KHAC voi man /not-approved doi QUET QR (do la fail need_mobile_app).
"""

from __future__ import annotations

import time

from app.automation.context import ExecutionContext
from app.automation.result import StepResult
from app.automation.step import Step

_HAS_BROWSER_CONTINUE = (
    "return [...document.querySelectorAll('a,button,[role=button]')]"
    ".some(x=>/continue in browser/i.test(x.innerText||''));"
)
_CLICK_BROWSER_CONTINUE = (
    "const b=[...document.querySelectorAll('a,button,[role=button]')]"
    ".find(x=>/continue in browser/i.test(x.innerText||''));"
    "if(b){b.click();return true;}return false;"
)


class DismissMobileInterstitialStep(Step):
    name = "dismiss_mobile_interstitial"
    optional = True

    def should_run(self, ctx: ExecutionContext) -> bool:
        return bool(ctx.browser.run_js(_HAS_BROWSER_CONTINUE))

    def run(self, ctx: ExecutionContext) -> StepResult:
        clicked = bool(ctx.browser.run_js(_CLICK_BROWSER_CONTINUE))
        time.sleep(3)  # cho chuyen sang trang that (home)
        return StepResult.ok(
            self.name, "bo qua man app-promo (Continue in browser)", clicked=clicked
        )
