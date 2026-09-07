from app.core.enums import CaptchaType
from app.domain.models import CaptchaTask
from app.providers.captcha import available_solvers
from app.providers.captcha.twocaptcha import TwoCaptchaSolver


def test_solvers_registered():
    names = available_solvers()
    assert {"twocaptcha", "capsolver", "anticaptcha", "manual"} <= set(names)


def test_twocaptcha_builds_funcaptcha_task():
    solver = TwoCaptchaSolver(api_key="dummy")
    task = CaptchaTask(
        type=CaptchaType.FUNCAPTCHA,
        website_url="https://roblox.com/login",
        website_key="KEY",
        api_subdomain="roblox-api.arkoselabs.com",
    )
    payload = solver.build_task(task)
    assert payload["type"] == "FunCaptchaTaskProxyless"
    assert payload["websitePublicKey"] == "KEY"
    assert payload["funcaptchaApiJSSubdomain"] == "roblox-api.arkoselabs.com"
    solver.close()
