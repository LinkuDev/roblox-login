from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.errors import NotFoundError
from app.db.models import User
from app.db.repositories import UserRepository
from app.modules.billing import BillingService


class UserService:
    def __init__(self, session: Session):
        self.session = session
        self.users = UserRepository(session)
        self.billing = BillingService(session)

    def get(self, user_id: str) -> User:
        user = self.users.get(user_id)
        if not user:
            raise NotFoundError("khong tim thay user")
        return user

    def profile(self, user_id: str) -> dict:
        user = self.get(user_id)
        return {
            "id": user.id,
            "email": user.email,
            "role": user.role,
            "balance": self.billing.balance(user_id),
            "created_at": user.created_at.isoformat(),
        }
