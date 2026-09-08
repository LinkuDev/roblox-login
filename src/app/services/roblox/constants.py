"""Tap trung selector / URL / key cua Roblox vao 1 cho.

Khi Roblox doi giao dien, chi sua file nay - khong dung vao logic step.
Cac gia tri duoi day la diem khoi dau, can xac nhan lai bang DevTools thuc te.
"""

from __future__ import annotations

from app.core.enums import CaptchaType

BASE_URL = "https://www.roblox.com"
LOGIN_URL = f"{BASE_URL}/login"
HOME_URL = f"{BASE_URL}/home"
# Sau login co the bi chuyen sang man "Account locked" (xac nhan human bang Arkose).
NOT_APPROVED_PATH = "/not-approved"

# Login = trai nghiem DESKTOP; toi man /not-approved moi chuyen sang MOBILE.
DESKTOP_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/152.0.0.0 Safari/537.36"
)
MOBILE_USER_AGENT = (
    "Mozilla/5.0 (Linux; Android 14; Pixel 7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/152.0.0.0 Mobile Safari/537.36"
)
DESKTOP_VIEWPORT = (1280, 800)   # (width, height)
MOBILE_VIEWPORT = (390, 844)

# Kich thuoc CUA SO OS that: login = rong (desktop, form hien day du, layout PC);
# /not-approved = hep (Chrome min-width ~500 nen khong the < ~500).
DESKTOP_WINDOW = (900, 760)
MOBILE_WINDOW = (500, 860)

# Client Hints (Sec-CH-UA-*) + navigator.platform de "y het PC / dien thoai" -
# khong chi UA string. Khop Chrome 152 cua Chrome for Testing.
_CHROME_MAJOR = "152"
_CHROME_FULL = "152.0.7977.82"
_BRANDS = [("Chromium", _CHROME_MAJOR), ("Google Chrome", _CHROME_MAJOR), ("Not?A_Brand", "99")]
DESKTOP_CLIENT_HINTS = {
    "platform": "Windows",
    "platform_version": "15.0.0",
    "architecture": "x86",
    "model": "",
    "mobile": False,
    "bitness": "64",
    "brands": _BRANDS,
    "full_version": _CHROME_FULL,
    "nav_platform": "Win32",
}
MOBILE_CLIENT_HINTS = {
    "platform": "Android",
    "platform_version": "14.0.0",
    "architecture": "",
    "model": "Pixel 7",
    "mobile": True,
    "bitness": "",
    "brands": _BRANDS,
    "full_version": _CHROME_FULL,
    "nav_platform": "Linux armv8l",
}

# Man APP-PROMO ("Explore Roblox in our mobile app" - Continue in App/browser) hien
# o route "/" SAU KHI giai/dang nhap xong (do dung mobile UA) -> tin hieu THANH CONG.
# Khac han man /not-approved doi QUET QR (do la fail). Bat rong cac text de chac.
APP_PROMO_TEXTS = (
    "continue in browser",
    "continue in app",
    "explore roblox in our mobile app",
    "roblox for ios",
    "roblox for android",
)

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
