from __future__ import annotations

import secrets
from datetime import UTC, datetime, timedelta

import bcrypt
from jose import JWTError, jwt

from app.core.config import get_settings
from app.core.errors import AuthError

ALGORITHM = "HS256"
_BCRYPT_MAX = 72   # bcrypt chi doc 72 byte dau


def hash_password(raw: str) -> str:
    data = raw.encode("utf-8")[:_BCRYPT_MAX]
    return bcrypt.hashpw(data, bcrypt.gensalt()).decode("utf-8")


def verify_password(raw: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(raw.encode("utf-8")[:_BCRYPT_MAX], hashed.encode("utf-8"))
    except (ValueError, TypeError):
        return False


def create_access_token(subject: str, extra: dict | None = None) -> str:
    s = get_settings().app
    now = datetime.now(UTC)
    payload = {
        "sub": subject,
        "iat": now,
        "exp": now + timedelta(minutes=s.access_token_ttl_minutes),
        **(extra or {}),
    }
    return jwt.encode(payload, s.secret_key, algorithm=ALGORITHM)


def decode_access_token(token: str) -> dict:
    try:
        return jwt.decode(token, get_settings().app.secret_key, algorithms=[ALGORITHM])
    except JWTError as exc:
        raise AuthError("token khong hop le hoac het han") from exc


def generate_api_key(prefix: str = "rlx") -> str:
    return f"{prefix}_{secrets.token_urlsafe(32)}"
