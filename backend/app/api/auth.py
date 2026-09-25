"""
PayPilot Global — Auth dependencies and utilities.
"""
from __future__ import annotations

import hashlib
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional, Set

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models import User

# auto_error=False is deliberate.
#
# By default HTTPBearer raises 403 "Not authenticated" when the Authorization
# header is missing, which is semantically wrong: 403 means "I know who you are
# and you may not do this", but here we do not know who you are at all.
# The frontend relies on 401 to trigger a refresh/redirect-to-login and on 403
# to show a permission message, so returning 403 for a missing token would send
# logged-out users to a "permission denied" screen instead of the login page.
#
# We turn the automatic error off and raise our own 401 in get_token_payload().
security = HTTPBearer(auto_error=False)

# ─── Roles ────────────────────────────────────────────────────────────────────
# Stored uppercase on User.role. Keep these constants as the single source of
# truth so a typo like "Admin" can never silently grant/deny access.
ROLE_ADMIN = "ADMIN"
ROLE_FINANCE = "FINANCE"
ROLE_VIEWER = "VIEWER"
ALL_ROLES = (ROLE_ADMIN, ROLE_FINANCE, ROLE_VIEWER)

# ─── Password hashing ─────────────────────────────────────────────────────────
# PBKDF2-SHA256 (no bcrypt dependency issues).
_HASH_ITERATIONS = 100000
_SALT_BYTES = 16


def hash_password(password: str) -> str:
    """Hash a password with a cryptographically random per-password salt.

    Format: "<salt_hex>$<hash_hex>"
    """
    salt = secrets.token_hex(_SALT_BYTES)
    hashed = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), _HASH_ITERATIONS)
    return f"{salt}${hashed.hex()}"


def verify_password(plain: str, hashed: str) -> bool:
    """Verify a password against a stored hash, in constant time."""
    try:
        salt, stored_hash = hashed.split("$", 1)
        computed = hashlib.pbkdf2_hmac("sha256", plain.encode(), salt.encode(), _HASH_ITERATIONS)
        # compare_digest prevents timing attacks
        return secrets.compare_digest(computed.hex(), stored_hash)
    except (ValueError, AttributeError):
        return False


# ─── Token denylist (logout support) ──────────────────────────────────────────
# JWTs are stateless, so "logging out" means remembering which token IDs (jti)
# have been revoked until they expire on their own.
# NOTE: in-memory only — cleared on server restart. Move to Redis in production.
_REVOKED_JTIS: Set[str] = set()


def revoke_token(jti: str) -> None:
    """Add a token's unique id to the denylist so it can no longer be used."""
    if jti:
        _REVOKED_JTIS.add(jti)


def is_token_revoked(jti: Optional[str]) -> bool:
    return bool(jti) and jti in _REVOKED_JTIS


def create_access_token(user_id: str, employer_id: str, role: str = ROLE_VIEWER) -> str:
    """Issue a signed JWT carrying the user's identity, tenant and role."""
    now = datetime.now(timezone.utc)
    expire = now + timedelta(hours=settings.jwt_expiration_hours)
    payload = {
        "sub": user_id,
        "employer_id": employer_id,
        "role": role,
        "iat": now,
        "exp": expire,
        "jti": str(uuid.uuid4()),  # unique token id, needed for logout
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_token(token: str) -> dict:
    """Decode and validate a JWT, raising 401 on any problem."""
    try:
        return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )


def get_token_payload(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> dict:
    """Return the decoded JWT payload, rejecting missing or revoked tokens."""
    # No Authorization header at all, or a non-Bearer scheme.
    if credentials is None or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated. Provide an 'Authorization: Bearer <token>' header.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = decode_token(credentials.credentials)
    if is_token_revoked(payload.get("jti")):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has been revoked. Please log in again.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return payload


def get_current_user(
    payload: dict = Depends(get_token_payload),
    db: Session = Depends(get_db),
) -> User:
    """Extract and validate the current user from the JWT token."""
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token: missing subject",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = db.query(User).filter(User.id == user_id, User.is_active == True).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


def require_role(*roles: str):
    """Dependency factory: require the user to have one of the specified roles.

    Usage:
        @router.delete("/{id}")
        def delete_thing(user: User = Depends(require_role(ROLE_ADMIN))):
            ...
    """
    allowed = tuple(r.upper() for r in roles)

    def checker(user: User = Depends(get_current_user)) -> User:
        if (user.role or "").upper() not in allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    f"Your role '{user.role}' cannot perform this action. "
                    f"Required role: {' or '.join(allowed)}."
                ),
            )
        return user

    return checker


# ─── Ready-made role dependencies ─────────────────────────────────────────────
# Use these instead of calling require_role() inline, so the permission model
# lives in ONE place and is easy to audit.

#: Full control — manage users, delete records, change settings.
require_admin = require_role(ROLE_ADMIN)

#: Can create and modify payroll/employee data, but not delete or manage users.
require_finance = require_role(ROLE_ADMIN, ROLE_FINANCE)

#: Any authenticated, active user — read-only access is enough.
require_viewer = require_role(*ALL_ROLES)


def get_employer_id(user: User = Depends(get_current_user)) -> str:
    """Extract employer_id from the authenticated user — never trust the frontend."""
    return user.employer_id

