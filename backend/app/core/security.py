from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import jwt
from passlib.context import CryptContext

from app.core.config import get_settings

# Use pbkdf2_sha256 for stable local/product bootstrap without external bcrypt backend issues.
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")
settings = get_settings()


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return pwd_context.verify(password, password_hash)


def create_access_token(*, subject: str, user_id: int) -> str:
    expires_at = datetime.now(UTC) + timedelta(minutes=settings.access_token_expire_minutes)
    payload = {
        "sub": subject,
        "user_id": user_id,
        "type": "access",
        "exp": expires_at,
        "iat": datetime.now(UTC),
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm="HS256")


def create_refresh_token(*, subject: str, user_id: int) -> tuple[str, str, datetime]:
    token_id = str(uuid4())
    expires_at = datetime.now(UTC) + timedelta(days=settings.refresh_token_expire_days)
    payload = {
        "sub": subject,
        "user_id": user_id,
        "type": "refresh",
        "jti": token_id,
        "exp": expires_at,
        "iat": datetime.now(UTC),
    }
    token = jwt.encode(payload, settings.jwt_refresh_secret_key, algorithm="HS256")
    return token, token_id, expires_at


def decode_access_token(token: str) -> dict:
    return jwt.decode(token, settings.jwt_secret_key, algorithms=["HS256"])


def decode_refresh_token(token: str) -> dict:
    return jwt.decode(token, settings.jwt_refresh_secret_key, algorithms=["HS256"])
