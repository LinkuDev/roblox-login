from __future__ import annotations

from collections.abc import Iterator

from fastapi import Depends, Header, HTTPException
from sqlalchemy.orm import Session

from app.core.errors import AuthError
from app.core.security import decode_access_token
from app.db.models import User
from app.db.session import get_session
from app.modules.auth import AuthService


def db_session() -> Iterator[Session]:
    yield from get_session()


def current_user(
    authorization: str | None = Header(default=None),
    x_api_key: str | None = Header(default=None),
    session: Session = Depends(db_session),
) -> User:
    """Chap nhan Bearer JWT hoac X-API-Key."""
    auth = AuthService(session)
    try:
        if x_api_key:
            return auth.user_from_api_key(x_api_key)
        if authorization and authorization.lower().startswith("bearer "):
            payload = decode_access_token(authorization.split(" ", 1)[1])
            user = auth.users.get(payload["sub"])
            if not user:
                raise AuthError("user khong ton tai")
            return user
    except AuthError as exc:
        raise HTTPException(status_code=401, detail=exc.message) from exc
    raise HTTPException(status_code=401, detail="thieu thong tin xac thuc")


def require_admin(user: User = Depends(current_user)) -> User:
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="can quyen admin")
    return user
