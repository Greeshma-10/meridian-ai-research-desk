"""
JWT-based authentication and role-based authorization for api-gateway.

Design note: user credentials are hardcoded here for demo purposes —
a real system would store hashed passwords in a database (DynamoDB,
Postgres, etc.), not in code. Flagged explicitly as a simplification,
not an oversight.
"""
import os
import logging
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
from fastapi import HTTPException, Header

logger = logging.getLogger(__name__)

# In production, this MUST come from a secret manager (AWS Secrets Manager),
# never hardcoded or committed. For this project, it's read from an
# environment variable — set it as a Codespaces secret, same pattern as
# your AWS/Neo4j credentials.
JWT_SECRET = os.environ.get("JWT_SECRET", "dev-only-insecure-secret-change-me")
JWT_ALGORITHM = "HS256"
TOKEN_EXPIRY_HOURS = 24


def _hash_password(password: str) -> bytes:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())


def _verify_password(password: str, hashed: bytes) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), hashed)


# Demo user store — hardcoded on purpose, see docstring above.
# Password for "analyst" is "meridian123", for "admin" is "adminpass456"
# (hashed below, never stored in plaintext).
_DEMO_USERS = {
    "analyst": {
        "password_hash": _hash_password("meridian123"),
        "role": "user",
    },
    "admin": {
        "password_hash": _hash_password("adminpass456"),
        "role": "admin",
    },
}


def authenticate_user(username: str, password: str) -> dict | None:
    user = _DEMO_USERS.get(username)
    if not user or not _verify_password(password, user["password_hash"]):
        return None
    return {"username": username, "role": user["role"]}


def create_access_token(username: str, role: str) -> str:
    payload = {
        "sub": username,
        "role": role,
        "exp": datetime.now(timezone.utc) + timedelta(hours=TOKEN_EXPIRY_HOURS),
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def verify_token(authorization: str = Header(None)) -> dict:
    """
        FastAPI dependency — extracts and validates the JWT from the
        Authorization header. Raises 401 for any invalid/missing/expired token.
        """
    if authorization is None:
        raise HTTPException(status_code=401, detail="Missing Authorization header")
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or malformed Authorization header")

    token = authorization.removeprefix("Bearer ")
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return {"username": payload["sub"], "role": payload["role"]}
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


def require_admin(user: dict) -> dict:
    """Additional check for admin-only endpoints — stacks on top of verify_token."""
    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return user