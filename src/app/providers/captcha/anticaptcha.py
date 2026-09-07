"""Anti-Captcha.com."""

from __future__ import annotations

from typing import Any

from app.core.enums import CaptchaType
from app.domain.models import CaptchaTask
from app.providers.captcha.base import HttpTaskSolver, captcha_registry


@captcha_registry.register("anticaptcha")
class AntiCaptchaSolver(HttpTaskSolver):
    name = "anticaptcha"
    base_url = "https://api.anti-captcha.com"
    report_bad_path = "/reportIncorrectRecaptcha"
    supported = frozenset(
        {CaptchaType.FUNCAPTCHA, CaptchaType.RECAPTCHA_V2, CaptchaType.RECAPTCHA_V3}
    )

    _TASK_TYPES = {
        CaptchaType.FUNCAPTCHA: "FunCaptchaTaskProxyless",
        CaptchaType.RECAPTCHA_V2: "RecaptchaV2TaskProxyless",
        CaptchaType.RECAPTCHA_V3: "RecaptchaV3TaskProxyless",
    }

    def build_task(self, task: CaptchaTask) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "type": self._TASK_TYPES[task.type],
            "websiteURL": task.website_url,
        }
        if task.type is CaptchaType.FUNCAPTCHA:
            payload["websitePublicKey"] = task.website_key
            if task.api_subdomain:
                payload["funcaptchaApiJSSubdomain"] = task.api_subdomain
            if task.blob:
                payload["data"] = task.blob
        else:
            payload["websiteKey"] = task.website_key
        payload.update(task.extra)
        return payload
