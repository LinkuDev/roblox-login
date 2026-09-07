from __future__ import annotations

from sqlalchemy import select

from app.db.models import ApiKey, User
from app.db.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    model = User

    def by_email(self, email: str) -> User | None:
        return self.session.scalar(select(User).where(User.email == email))


class ApiKeyRepository(BaseRepository[ApiKey]):
    model = ApiKey

    def by_hash(self, key_hash: str) -> ApiKey | None:
        return self.session.scalar(
            select(ApiKey).where(ApiKey.key_hash == key_hash, ApiKey.is_active.is_(True))
        )
