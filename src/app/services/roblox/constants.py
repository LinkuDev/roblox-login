"""Tap trung selector / URL / key cua Roblox vao 1 cho.

Khi Roblox doi giao dien, chi sua file nay - khong dung vao logic step.
Cac gia tri duoi day la diem khoi dau, can xac nhan lai bang DevTools thuc te.
"""

from __future__ import annotations

from app.core.enums import CaptchaType

BASE_URL = "https://www.roblox.com"
LOGIN_URL = f"{BASE_URL}/login"
HOME_URL = f"{BASE_URL}/home"

# Roblox dung Arkose Labs FunCaptcha
CAPTCHA_TYPE = CaptchaType.FUNCAPTCHA
# Public key Arkose cua Roblox (login). CAN kiem tra lai - Roblox co the doi.
FUNCAPTCHA_PUBLIC_KEY = "476068BF-9607-4799-B53D-966BE98E2B81"
FUNCAPTCHA_API_SUBDOMAIN = "roblox-api.arkoselabs.com"

# --- selectors (xac nhan lai bang DevTools) ---
SEL_USERNAME = "#login-username"
SEL_PASSWORD = "#login-password"
SEL_SUBMIT = "#login-button"
SEL_ERROR = ".login-error, .text-error, [class*='error']"
SEL_LOGGED_IN = "#navbar-robux, .rbx-navbar, [data-testid='home-page']"
SEL_2FA_INPUT = "#two-step-verification-code-input, input[name='code']"
SEL_2FA_SUBMIT = ".two-step-verification-code-submit, button[type='submit']"
SEL_CAPTCHA_FRAME = "iframe[src*='arkoselabs'], #arkose-iframe, iframe[title*='verification']"

# URL API doc thong tin sau khi dang nhap
API_AUTHENTICATED = "https://users.roblox.com/v1/users/authenticated"
COOKIE_SESSION = ".ROBLOSECURITY"
