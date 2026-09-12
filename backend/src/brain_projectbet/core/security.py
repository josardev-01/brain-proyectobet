from __future__ import annotations

from datetime import UTC, datetime, timedelta

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerifyMismatchError
from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from brain_projectbet.core.settings import get_settings
from brain_projectbet.database.models import UserRecord
from brain_projectbet.database.session import get_db


password_hasher = PasswordHasher()
_dummy_password_hash = password_hasher.hash("projectbet-dummy-password-never-used")
bearer = HTTPBearer(auto_error=False)


def hash_password(password: str) -> str:
    return password_hasher.hash(password)


def verify_password(password: str, password_hash: str | None) -> bool:
    candidate_hash = password_hash or _dummy_password_hash
    try:
        verified = password_hasher.verify(candidate_hash, password)
        return bool(password_hash) and verified
    except (VerifyMismatchError, InvalidHashError):
        return False


def create_access_token(user_id: int) -> tuple[str, int]:
    settings = get_settings()
    expires_in = settings.access_token_minutes * 60
    now = datetime.now(UTC)
    token = jwt.encode(
        {"sub": str(user_id), "iat": now, "exp": now + timedelta(seconds=expires_in)},
        settings.jwt_secret,
        algorithm="HS256",
    )
    return token, expires_in


def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
    session: Session = Depends(get_db),
) -> UserRecord:
    unauthorized = HTTPException(status_code=401, detail="autenticación requerida")
    token = credentials.credentials if credentials is not None else request.cookies.get("projectbet_session")
    if token is None:
        raise unauthorized
    try:
        payload = jwt.decode(token, get_settings().jwt_secret, algorithms=["HS256"])
        user_id = int(payload["sub"])
    except (jwt.PyJWTError, KeyError, TypeError, ValueError):
        raise unauthorized
    user = session.get(UserRecord, user_id)
    if user is None or not user.active or user.approval_status != "APPROVED":
        raise unauthorized
    return user


def require_admin(user: UserRecord = Depends(get_current_user)) -> UserRecord:
    if user.role != "ADMIN":
        raise HTTPException(status_code=403, detail="se requiere rol de administrador")
    return user
