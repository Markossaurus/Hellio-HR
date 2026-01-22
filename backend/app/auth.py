import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Iterable

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import AuthToken, User

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
bearer_scheme = HTTPBearer(auto_error=False)


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def create_token(user_id, db: Session, expires_in: timedelta | None = None) -> str:
    token = secrets.token_urlsafe(32)
    token_hash = _hash_token(token)
    expires_at = datetime.now(timezone.utc) + (expires_in or timedelta(days=7))
    db_token = AuthToken(user_id=user_id, token_hash=token_hash, expires_at=expires_at)
    db.add(db_token)
    db.commit()
    db.refresh(db_token)
    return token


def verify_token(token: str, db: Session) -> User | None:
    token_hash = _hash_token(token)
    now = datetime.now(timezone.utc)
    stmt = select(AuthToken).where(
        AuthToken.token_hash == token_hash,
        AuthToken.revoked_at.is_(None),
        AuthToken.expires_at > now,
    )
    auth_token = db.execute(stmt).scalar_one_or_none()
    if not auth_token:
        return None
    return auth_token.user


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    if not credentials or not credentials.credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing token")
    user = verify_token(credentials.credentials, db)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    return user


def require_roles(required_roles: Iterable[str]):
    required = {role.lower() for role in required_roles}

    def _require_roles(user: User = Depends(get_current_user)) -> User:
        user_roles = {role.name.lower() for role in user.roles}
        if not required.intersection(user_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions"
            )
        return user

    return _require_roles
