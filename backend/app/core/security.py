"""
Password hashing (bcrypt via passlib) and JWT issuance/verification.

Kept deliberately separate from routes so auth logic is unit-testable
without spinning up FastAPI, and so the same functions serve both the
HTTP dependency (routes_auth.py) and the WebSocket auth check.
"""
from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain_password: str) -> str:
    return _pwd_context.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return _pwd_context.verify(plain_password, hashed_password)


def create_access_token(subject: str, expires_minutes: int | None = None) -> str:
    minutes = settings.ACCESS_TOKEN_EXPIRE_MINUTES if expires_minutes is None else expires_minutes
    expire = datetime.now(timezone.utc) + timedelta(minutes=minutes)
    payload = {"sub": subject, "type": "access", "exp": expire}
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_refresh_token(subject: str, expires_days: int | None = None) -> str:
    """Refresh tokens live much longer and carry a 'type' claim so an access
    token can never be replayed as a refresh token even if it leaks."""
    days = settings.REFRESH_TOKEN_EXPIRE_DAYS if expires_days is None else expires_days
    expire = datetime.now(timezone.utc) + timedelta(days=days)
    payload = {"sub": subject, "type": "refresh", "exp": expire}
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def _decode_token(token: str, expected_type: str) -> str | None:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
    except JWTError:
        return None
    if payload.get("type") != expected_type:
        return None
    return payload.get("sub")


def decode_access_token(token: str) -> str | None:
    """Returns the subject (user id string) if the token is a valid, non-expired
    access token, else None. Rejects refresh tokens even if otherwise valid."""
    return _decode_token(token, expected_type="access")


def decode_refresh_token(token: str) -> str | None:
    """Returns the subject (user id string) if the token is a valid, non-expired
    refresh token, else None. Rejects access tokens even if otherwise valid."""
    return _decode_token(token, expected_type="refresh")
