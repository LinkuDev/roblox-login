from __future__ import annotations

import hashlib

from sqlalchemy.orm import Session

from app.core.enums import PointTxType
from app.core.errors import AuthError, BusinessError
from app.core.security import (
    create_access_token,
    generate_api_key,
    hash_password,
    verify_password,
)
from app.db.models import ApiKey, User
from app.db.repositories import ApiKeyRepository, UserRepository
from app.modules.billing import BillingService


def _hash_key(raw: str) -> str:
    return hashlib.sha256(raw.encode()).hexdigest()


class AuthService:
    def __init__(self, session: Session):
        self.session = session
        self.users = UserRepository(session)
        self.api_keys = ApiKeyRepository(session)
        self.billing = BillingService(session)

    def register(self, email: str, password: str) -> User:
        if self.users.by_email(email):
            raise BusinessError("email da ton tai")

        from app.core.config import get_settings
        from app.core.enums import UserRole

        role = UserRole.ADMIN if get_settings().app.is_admin_email(email) else UserRole.USER
        user = self.users.add(
            User(email=email, password_hash=hash_password(password), role=role)
        )
        self.billing.ensure_wallet(user.id)

        bonus = get_settings().billing.point_signup_bonus
        if bonus > 0:
            self.billing.topup(user.id, bonus, note="signup bonus", tx_type=PointTxType.BONUS)
        return user

    def authenticate(self, email: str, password: str) -> str:
        user = self.users.by_email(email)
        if not user or not verify_password(password, user.password_hash):
            raise AuthError("sai email hoac mat khau")
        if not user.is_active:
            raise AuthError("tai khoan bi khoa")
        return create_access_token(user.id, {"role": user.role})

    def issue_api_key(self, user_id: str, label: str = "") -> str:
        raw = generate_api_key()
        self.api_keys.add(ApiKey(user_id=user_id, key_hash=_hash_key(raw), label=label))
        return raw   # chi tra 1 lan, khong luu ban ro

    def user_from_api_key(self, raw_key: str) -> User:
        record = self.api_keys.by_hash(_hash_key(raw_key))
        if not record:
            raise AuthError("API key khong hop le")
        user = self.users.get(record.user_id)
        if not user or not user.is_active:
            raise AuthError("tai khoan khong hop le")
        return user
