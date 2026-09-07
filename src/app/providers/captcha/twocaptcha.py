"""2captcha (rucaptcha) - API v2."""

from __future__ import annotations

from typing import Any

from app.core.enums import CaptchaType
from app.domain.models import CaptchaTask
from app.providers.captcha.base import PROXYLESS_SUPPORT, HttpTaskSolver, captcha_registry


@captcha_registry.register("twocaptcha")
class TwoCaptchaSolver(HttpTaskSolver):
    name = "twocaptcha"
    base_url = "https://api.2captcha.com"
    report_bad_path = "/reportIncorrect"
    supported = PROXYLESS_SUPPORT

    _TASK_TYPES = {
        CaptchaType.FUNCAPTCHA: "FunCaptchaTask",
        CaptchaType.RECAPTCHA_V2: "RecaptchaV2Task",
        CaptchaType.RECAPTCHA_V3: "RecaptchaV3TaskProxyless",
        CaptchaType.HCAPTCHA: "HCaptchaTask",
        CaptchaType.TURNSTILE: "TurnstileTask",
    }

    def build_task(self, task: CaptchaTask) -> dict[str, Any]:
        base = self._TASK_TYPES[task.type]
        # RecaptchaV3 chi co ban Proxyless; cac loai khac them hau to khi khong co proxy
        use_proxy = task.proxy is not None and not base.endswith("Proxyless")
        task_type = base if use_proxy else (base if base.endswith("Proxyless") else base + "Proxyless")

        payload: dict[str, Any] = {
            "type": task_type,
            "websiteURL": task.website_url,
        }

        if task.type is CaptchaType.FUNCAPTCHA:
            payload["websitePublicKey"] = task.website_key
            if task.api_subdomain:
                payload["funcaptchaApiJSSubdomain"] = task.api_subdomain
            if task.blob:
                # blob phai la chuoi JSON, vd: {"blob":"<dataExchangeBlob>"}
                payload["data"] = task.blob
        else:
            payload["websiteKey"] = task.website_key
            if task.action:
                payload["pageAction"] = task.action

        if use_proxy and task.proxy:
            payload.update(
                {
                    "proxyType": task.proxy.scheme,
                    "proxyAddress": task.proxy.host,
                    "proxyPort": task.proxy.port,
                }
            )
            if task.proxy.username:
                payload["proxyLogin"] = task.proxy.username
                payload["proxyPassword"] = task.proxy.password
        if task.user_agent:
            payload["userAgent"] = task.user_agent

        payload.update(task.extra)
        return payload
