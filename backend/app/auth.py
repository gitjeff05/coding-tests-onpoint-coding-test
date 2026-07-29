import base64
import binascii
import logging
import os
import secrets
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import APIRouter, HTTPException, Request

from . import schemas

logger = logging.getLogger(__name__)

# Demo credential store + JWT signing secret. In a real deployment these
# would not exist at all — see the README's "Authentication" section for
# how a managed identity provider replaces this.
AUTH_USERNAME = os.environ.get("AUTH_USERNAME", "admin")
AUTH_PASSWORD = os.environ.get("AUTH_PASSWORD", "admin123")
JWT_SECRET = os.environ.get("JWT_SECRET", "dev-secret-change-me-32-bytes-min")
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_MINUTES = 30

router = APIRouter(prefix="/auth", tags=["auth"])


def _valid_credentials(username: str, password: str) -> bool:
    return secrets.compare_digest(username, AUTH_USERNAME) and secrets.compare_digest(
        password, AUTH_PASSWORD
    )


def create_access_token(username: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=JWT_EXPIRE_MINUTES)
    return jwt.encode({"sub": username, "exp": expire}, JWT_SECRET, algorithm=JWT_ALGORITHM)


def _unauthorized(reason: str) -> HTTPException:
    logger.warning("auth rejected: %s", reason)
    return HTTPException(status_code=401, detail="not authenticated", headers={"WWW-Authenticate": "Basic"})


def require_auth(request: Request) -> str:
    """Accept either an HTTP Basic Authorization header or a Bearer JWT."""
    authorization = request.headers.get("Authorization")
    if not authorization:
        raise _unauthorized("missing Authorization header")

    scheme, _, value = authorization.partition(" ")
    scheme = scheme.lower()

    if scheme == "basic":
        try:
            decoded = base64.b64decode(value).decode("utf-8")
        except (binascii.Error, UnicodeDecodeError):
            raise _unauthorized("malformed basic auth header")
        username, _, password = decoded.partition(":")
        if not _valid_credentials(username, password):
            raise _unauthorized("invalid basic auth credentials")
        return username

    if scheme == "bearer":
        try:
            payload = jwt.decode(value, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        except jwt.PyJWTError as e:
            raise _unauthorized(f"invalid bearer token ({e})")
        return payload["sub"]

    raise _unauthorized(f"unsupported authorization scheme {scheme!r}")


@router.post("/login", response_model=schemas.Token)
def login(credentials: schemas.LoginRequest):
    if not _valid_credentials(credentials.username, credentials.password):
        logger.warning("login rejected for user %r", credentials.username)
        raise HTTPException(status_code=401, detail="invalid username or password")
    logger.info("login succeeded for user %r", credentials.username)
    return schemas.Token(access_token=create_access_token(credentials.username))
