"""Cau hinh tap trung. Moi thu doc tu env -> khong hardcode o bat ky tang nao khac."""

from __future__ import annotations

import sys
from functools import lru_cache
from pathlib import Path
from typing import Any

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT_DIR = Path(__file__).resolve().parents[3]


def bundle_dir() -> Path:
    """Thu muc goc tai nguyen di kem.

    - Dong goi PyInstaller: sys._MEIPASS (onefile) hoac thu muc chua exe (onedir).
    - Dev: repo root.
    """
    if getattr(sys, "frozen", False):
        return Path(getattr(sys, "_MEIPASS", None) or Path(sys.executable).resolve().parent)
    return ROOT_DIR


def _browser_dir() -> Path:
    # bundle: <base>/browser ; dev: <root>/data/browser
    if getattr(sys, "frozen", False):
        return bundle_dir() / "browser"
    return ROOT_DIR / "data" / "browser"


def default_chrome_path() -> Path:
    """Duong dan binary Chrome for Testing di kem (da nen tang)."""
    base = _browser_dir()
    binname = "chrome.exe" if sys.platform.startswith("win") else "chrome"
    for sub in ("chrome", "chrome-linux64", "chrome-win64", "chrome-mac-x64", "chrome-mac-arm64"):
        p = base / sub / binname
        if p.exists():
            return p
    return base / "chrome-linux64" / binname  # dev default (co the chua ton tai)


def default_extension_dir() -> Path:
    """Thu muc template extension YesCaptcha (unpacked) di kem."""
    return _browser_dir() / "yescaptcha-ext"


class AppSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="APP_", env_file=".env", extra="ignore")

    env: str = "dev"
    debug: bool = True
    secret_key: str = "change-me"
    log_level: str = "INFO"
    log_json: bool = False
    access_token_ttl_minutes: int = 60 * 24
    # Email duoc cap quyen ADMIN tu dong luc register (ngan cach dau phay). Admin ->
    # topup diem + tao API key cho node claim pool. Vd: APP_ADMIN_EMAILS=op@x.co
    admin_emails: str = ""
    # Origin FE (Next.js) duoc phep goi API qua CORS (ngan cach dau phay). "*" = tat ca.
    # Vd: APP_CORS_ORIGINS=http://localhost:3000,https://app.mysaas.com
    cors_origins: str = "*"

    def is_admin_email(self, email: str) -> bool:
        allow = {e.strip().lower() for e in self.admin_emails.split(",") if e.strip()}
        return email.strip().lower() in allow

    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()] or ["*"]

    @property
    def is_prod(self) -> bool:
        return self.env.lower() in {"prod", "production"}


class CaptchaSettings(BaseSettings):
    """Chon nha cung cap giai captcha. Doi provider = doi 1 dong env."""

    model_config = SettingsConfigDict(env_prefix="CAPTCHA_", env_file=".env", extra="ignore")

    provider: str = "twocaptcha"
    timeout: int = 180
    poll_interval: float = 5.0
    max_retries: int = 2


class ProviderKeys(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    twocaptcha_api_key: str = ""
    capsolver_api_key: str = ""
    anticaptcha_api_key: str = ""
    yescaptcha_api_key: str = ""


class BrowserSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="BROWSER_", env_file=".env", extra="ignore")

    provider: str = "botasaurus"
    headless: bool = True
    # Kich thuoc = 1 dien thoai that (Pixel 7), khong dung width desktop.
    window_size: str = "412,915"
    timeout: int = 45
    profile_dir: Path = ROOT_DIR / "data" / "profiles"
    # Mobile UA khop Chrome engine (CfT) de Roblox tra layout mobile ma khong lech.
    user_agent: str | None = (
        "Mozilla/5.0 (Linux; Android 14; Pixel 7) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/152.0.0.0 Mobile Safari/537.36"
    )
    # Nhan = Chrome for Testing (khong dung Chrome goc). None -> chrome he thong.
    # default_factory -> tu tim trong bundle (khi dong goi) hoac data/browser (dev).
    chrome_executable_path: Path | None = Field(default_factory=default_chrome_path)
    # Extension YesCaptcha (unpacked, TEMPLATE) tu giai captcha in-page thay cho API.
    captcha_extension_dir: Path | None = Field(default_factory=default_extension_dir)
    # clientKey bom vao config.js cua ban copy luc launch (nguon: config app/node UI).
    # None -> giu nguyen key co san trong template.
    captcha_client_key: str | None = None
    # Override cac field trong config.js cua extension (merge sau, ho tro long nhau).
    # Vd: FunCaptcha giai fail -> nhan "Try again". Node/app co the ghi de field nay.
    captcha_config_overrides: dict[str, Any] = Field(
        default_factory=lambda: {
            "autorun": True,
            # So lan giai toi da truoc khi extension dung (mac dinh config.js la 20).
            "isOpenEndTimes": True,
            "endTimes": "60",
            "funcaptchaConfig": {
                "isOpen": True,
                "isAutoClickPrePage": True,
                "actionAfterRecFail": "tryAgain",
                "actionAfterOneRecFail": "restart",
            },
        }
    )

    @property
    def window(self) -> tuple[int, int]:
        w, _, h = self.window_size.partition(",")
        return int(w), int(h)


class ProxySettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="PROXY_", env_file=".env", extra="ignore")

    provider: str = "none"
    list_file: Path = ROOT_DIR / "data" / "proxies.txt"


class DatabaseSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = f"sqlite:///{ROOT_DIR / 'data' / 'app.db'}"
    sql_echo: bool = False


class QueueSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    queue_backend: str = "memory"
    redis_url: str = "redis://localhost:6379/0"
    worker_concurrency: int = 2


class BillingSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    point_signup_bonus: int = 0


class CryptoSettings(BaseSettings):
    """Nap diem tu dong qua crypto. Doi cong thanh toan = doi 1 dong `provider`.

    - provider: `manual` (dev/mac dinh - admin tao dia chi vi + confirm tay hoac qua
      webhook noi bo) hoac `nowpayments` (goi HTTP that, xac thuc IPN bang HMAC).
    - points_per_usd: 1 USD (stablecoin) = bao nhieu diem. total_usd = points/rate.
    - min_points: nạp toi thieu.
    - deposit_ttl_minutes: het han thi lenh nap chuyen EXPIRED.
    """

    model_config = SettingsConfigDict(env_prefix="CRYPTO_", env_file=".env", extra="ignore")

    provider: str = "manual"
    enabled: bool = True
    points_per_usd: int = 1000
    min_points: int = 1000
    deposit_ttl_minutes: int = 60
    # currency (stablecoin/coin) cho phep. FE chon 1 trong list nay.
    currencies: str = "USDT,USDC,BTC,ETH"
    # `manual`: dia chi vi nhan tien (hien cho user). Co the map theo currency sau.
    wallet_address: str = ""
    # `nowpayments`: khoa API + IPN secret (xac thuc webhook). Trong env, khong hardcode.
    api_key: str = ""
    ipn_secret: str = ""
    api_base: str = "https://api.nowpayments.io/v1"
    # URL callback provider goi ve (public URL cua SaaS). Vd https://api.mysaas.com
    callback_base: str = ""

    def currency_list(self) -> list[str]:
        return [c.strip().upper() for c in self.currencies.split(",") if c.strip()]


class Settings(BaseSettings):
    """Root settings - inject cai nay di khap noi thay vi doc env truc tiep."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app: AppSettings = Field(default_factory=AppSettings)
    captcha: CaptchaSettings = Field(default_factory=CaptchaSettings)
    keys: ProviderKeys = Field(default_factory=ProviderKeys)
    browser: BrowserSettings = Field(default_factory=BrowserSettings)
    proxy: ProxySettings = Field(default_factory=ProxySettings)
    db: DatabaseSettings = Field(default_factory=DatabaseSettings)
    queue: QueueSettings = Field(default_factory=QueueSettings)
    billing: BillingSettings = Field(default_factory=BillingSettings)
    crypto: CryptoSettings = Field(default_factory=CryptoSettings)

    root_dir: Path = ROOT_DIR


@lru_cache
def get_settings() -> Settings:
    return Settings()
