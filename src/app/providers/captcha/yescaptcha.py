"""YesCaptcha - API tuong thich anti-captcha (createTask / getTaskResult / getBalance).

Token FunCaptcha qua `FunCaptchaTaskProxyless` (co proxy thi `FunCaptchaTask`).
Dung cho Roblox Arkose: truyen `websitePublicKey`, `funcaptchaApiJSSubdomain`,
va `data` = blob (dataExchangeBlob duoi dang chuoi).
"""

from __future__ import annotations

from typing import Any

from app.core.enums import CaptchaType
from app.domain.models import CaptchaTask
from app.providers.captcha.base import PROXYLESS_SUPPORT, HttpTaskSolver, captcha_registry


@captcha_registry.register("yescaptcha")
class YesCaptchaSolver(HttpTaskSolver):
    name = "yescaptcha"
    base_url = "https://api.yescaptcha.com"
    supported = PROXYLESS_SUPPORT

    _TASK_TYPES = {
        CaptchaType.FUNCAPTCHA: "FunCaptchaTask",
        CaptchaType.RECAPTCHA_V2: "NoCaptchaTask",
        CaptchaType.RECAPTCHA_V3: "RecaptchaV3TaskProxyless",
        CaptchaType.HCAPTCHA: "HCaptchaTask",
        CaptchaType.TURNSTILE: "TurnstileTaskProxyless",
    }

    def build_task(self, task: CaptchaTask) -> dict[str, Any]:
        base = self._TASK_TYPES[task.type]
        use_proxy = task.proxy is not None and not base.endswith("Proxyless")
        task_type = base if use_proxy else (base if base.endswith("Proxyless") else base + "Proxyless")

        payload: dict[str, Any] = {"type": task_type, "websiteURL": task.website_url}

        if task.type is CaptchaType.FUNCAPTCHA:
            payload["websitePublicKey"] = task.website_key
            if task.api_subdomain:
                payload["funcaptchaApiJSSubdomain"] = task.api_subdomain
            if task.blob:
                # blob = dataExchangeBlob (chuoi). YesCaptcha nhan qua `data`.
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
