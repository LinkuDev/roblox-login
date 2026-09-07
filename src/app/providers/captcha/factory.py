from __future__ import annotations

from app.core.config import Settings, get_settings
from app.core.errors import CaptchaError
from app.domain.ports import CaptchaSolver
from app.providers.captcha.base import captcha_registry


def _api_key_for(name: str, settings: Settings) -> str:
    return {
        "twocaptcha": settings.keys.twocaptcha_api_key,
        "capsolver": settings.keys.capsolver_api_key,
        "anticaptcha": settings.keys.anticaptcha_api_key,
        "yescaptcha": settings.keys.yescaptcha_api_key,
        "manual": "",
    }.get(name.lower(), "")


def build_solver(name: str | None = None, settings: Settings | None = None) -> CaptchaSolver:
    """Diem duy nhat tao solver. Doi provider = doi env CAPTCHA_PROVIDER."""
    settings = settings or get_settings()
    name = (name or settings.captcha.provider).lower()
    cls = captcha_registry.get(name)
    try:
        return cls(api_key=_api_key_for(name, settings), config=settings.captcha)  # type: ignore[call-arg]
    except TypeError as exc:
        raise CaptchaError(f"khong khoi tao duoc solver '{name}': {exc}") from exc


def available_solvers() -> list[str]:
    return captcha_registry.names()
