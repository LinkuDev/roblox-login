"""Cau hinh tap trung. Moi thu doc tu env -> khong hardcode o bat ky tang nao khac."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT_DIR = Path(__file__).resolve().parents[3]


class AppSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="APP_", env_file=".env", extra="ignore")

    env: str = "dev"
    debug: bool = True
    secret_key: str = "change-me"
    log_level: str = "INFO"
    log_json: bool = False
    access_token_ttl_minutes: int = 60 * 24

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
    chrome_executable_path: Path | None = (
        ROOT_DIR / "data" / "browser" / "chrome-linux64" / "chrome"
    )
    # Extension YesCaptcha (unpacked, TEMPLATE) tu giai captcha in-page thay cho API.
    captcha_extension_dir: Path | None = ROOT_DIR / "data" / "browser" / "yescaptcha-ext"
    # clientKey bom vao config.js cua ban copy luc launch (nguon: config app/node UI).
    # None -> giu nguyen key co san trong template.
    captcha_client_key: str | None = None
    # Override cac field trong config.js cua extension (merge sau, ho tro long nhau).
    # Vd: FunCaptcha giai fail -> nhan "Try again". Node/app co the ghi de field nay.
    captcha_config_overrides: dict[str, Any] = Field(
        default_factory=lambda: {
            "autorun": True,
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

    root_dir: Path = ROOT_DIR


@lru_cache
def get_settings() -> Settings:
    return Settings()
