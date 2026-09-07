"""Value object thuan Python - khong phu thuoc DB, khong phu thuoc framework."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from app.core.enums import CaptchaType
from app.core.logging import mask


@dataclass(slots=True)
class Credential:
    """Dau vao co ban cua moi service: tk + mk (+ 2FA neu co)."""

    username: str
    password: str
    totp_secret: str | None = None
    email: str | None = None
    email_password: str | None = None
    meta: dict[str, Any] = field(default_factory=dict)

    def __repr__(self) -> str:  # tranh lo password vao log/traceback
        return f"Credential(username={self.username!r}, password={mask(self.password)!r})"

    @classmethod
    def parse(cls, line: str, sep: str = ":") -> Credential:
        """Parse dong dang `user:pass` hoac `user:pass:totp`."""
        parts = [p.strip() for p in line.strip().split(sep)]
        if len(parts) < 2:
            raise ValueError(f"dong credential khong hop le: {line!r}")
        return cls(username=parts[0], password=parts[1], totp_secret=parts[2] if len(parts) > 2 else None)


@dataclass(slots=True, frozen=True)
class Proxy:
    host: str
    port: int
    username: str | None = None
    password: str | None = None
    scheme: str = "http"

    @classmethod
    def parse(cls, raw: str) -> Proxy:
        """host:port | host:port:user:pass | scheme://user:pass@host:port"""
        raw = raw.strip()
        scheme = "http"
        if "://" in raw:
            scheme, _, raw = raw.partition("://")
        if "@" in raw:
            auth, _, hostport = raw.rpartition("@")
            user, _, pwd = auth.partition(":")
            host, _, port = hostport.partition(":")
            return cls(host, int(port), user or None, pwd or None, scheme)
        parts = raw.split(":")
        if len(parts) == 2:
            return cls(parts[0], int(parts[1]), scheme=scheme)
        if len(parts) == 4:
            return cls(parts[0], int(parts[1]), parts[2], parts[3], scheme)
        raise ValueError(f"proxy khong hop le: {raw!r}")

    @property
    def url(self) -> str:
        auth = f"{self.username}:{self.password}@" if self.username else ""
        return f"{self.scheme}://{auth}{self.host}:{self.port}"

    def as_2captcha(self) -> dict:
        return {
            "proxyType": self.scheme,
            "proxyAddress": self.host,
            "proxyPort": self.port,
            "proxyLogin": self.username,
            "proxyPassword": self.password,
        }


@dataclass(slots=True)
class CaptchaTask:
    """Mo ta 1 captcha can giai - provider-agnostic."""

    type: CaptchaType
    website_url: str
    website_key: str
    # FunCaptcha: blob tu dataExchangeBlob; reCAPTCHA: rieng cac field khac
    blob: str | None = None
    api_subdomain: str | None = None
    action: str | None = None
    proxy: Proxy | None = None
    user_agent: str | None = None
    cookies: dict[str, str] | None = None
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class CaptchaSolution:
    token: str
    provider: str
    task_id: str | None = None
    cost: float | None = None
    solve_seconds: float | None = None
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class SessionArtifact:
    """Ket qua "co gia tri" thu duoc sau khi login thanh cong."""

    cookies: dict[str, str] = field(default_factory=dict)
    tokens: dict[str, str] = field(default_factory=dict)
    user_agent: str | None = None
    profile: dict[str, Any] = field(default_factory=dict)
    captured_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def to_dict(self) -> dict:
        return {
            "cookies": self.cookies,
            "tokens": self.tokens,
            "user_agent": self.user_agent,
            "profile": self.profile,
            "captured_at": self.captured_at.isoformat(),
        }
