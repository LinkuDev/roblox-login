from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import current_user, db_session
from app.db.models import User
from app.modules.auth import AuthService
from app.schemas.auth import (
    ApiKeyResponse,
    LoginRequest,
    RegisterRequest,
    TokenResponse,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse)
def register(body: RegisterRequest, session: Session = Depends(db_session)):
    auth = AuthService(session)
    auth.register(body.email, body.password)
    return TokenResponse(access_token=auth.authenticate(body.email, body.password))


@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest, session: Session = Depends(db_session)):
    token = AuthService(session).authenticate(body.email, body.password)
    return TokenResponse(access_token=token)


@router.post("/api-keys", response_model=ApiKeyResponse)
def create_api_key(
    label: str = "",
    user: User = Depends(current_user),
    session: Session = Depends(db_session),
):
    raw = AuthService(session).issue_api_key(user.id, label)
    return ApiKeyResponse(api_key=raw, label=label)
