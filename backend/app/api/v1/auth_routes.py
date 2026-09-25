"""
PayPilot Global — Auth API Routes

Owner: Person 1 (Backend Core — Auth & Employees)

Endpoints:
    POST /auth/login            (public)  Exchange email+password for a JWT
    GET  /auth/me               (auth)    Who am I?
    POST /auth/refresh          (auth)    Get a fresh token before the old expires
    POST /auth/logout           (auth)    Revoke the current token
    POST /auth/change-password  (auth)    Change your own password
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models import User
from app.schemas import (
    LoginRequest,
    LoginResponse,
    UserResponse,
    RefreshResponse,
    LogoutResponse,
    ChangePasswordRequest,
    ChangePasswordResponse,
)
from app.api.auth import (
    verify_password,
    hash_password,
    create_access_token,
    get_current_user,
    get_token_payload,
    revoke_token,
)

router = APIRouter(prefix="/auth", tags=["Authentication"])

# How long a freshly issued token lasts, in seconds. The frontend uses this to
# schedule a refresh before expiry instead of guessing.
TOKEN_TTL_SECONDS = settings.jwt_expiration_hours * 3600

# Minimum acceptable password length for self-service password changes.
MIN_PASSWORD_LENGTH = 8


# ─── Login ────────────────────────────────────────────────────────────────────

@router.post("/login", response_model=LoginResponse)
def login(req: LoginRequest, db: Session = Depends(get_db)):
    """Authenticate with email/password and return a JWT.

    Returns 401 for both "unknown email" and "wrong password" on purpose —
    telling an attacker which emails exist is an account-enumeration leak.
    """
    email = (req.email or "").strip().lower()

    user = db.query(User).filter(User.email == email).first()

    if not user or not verify_password(req.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )

    # Separate message: the credentials were right, the account is just disabled.
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This account has been deactivated. Contact your administrator.",
        )

    token = create_access_token(user.id, user.employer_id, user.role)
    return LoginResponse(
        access_token=token,
        expires_in=TOKEN_TTL_SECONDS,
        user=UserResponse.model_validate(user),
    )


# ─── Who am I ─────────────────────────────────────────────────────────────────

@router.get("/me", response_model=UserResponse)
def get_me(user: User = Depends(get_current_user)):
    """Return the currently authenticated user.

    The frontend calls this on page load to restore the session from a stored
    token, and to decide which UI controls to show based on `role`.
    """
    return UserResponse.model_validate(user)


# ─── Refresh ──────────────────────────────────────────────────────────────────

@router.post("/refresh", response_model=RefreshResponse)
def refresh_token(
    payload: dict = Depends(get_token_payload),
    db: Session = Depends(get_db),
):
    """Exchange a still-valid token for a new one with a fresh expiry.

    The frontend should call this a few minutes before `expires_in` runs out so
    the user is never kicked out mid-task. The old token is revoked so a single
    token can't be refreshed forever from two places.
    """
    user = db.query(User).filter(
        User.id == payload.get("sub"),
        User.is_active == True,
    ).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )

    # Burn the old token so it can't be reused.
    revoke_token(payload.get("jti"))

    new_token = create_access_token(user.id, user.employer_id, user.role)
    return RefreshResponse(access_token=new_token, expires_in=TOKEN_TTL_SECONDS)


# ─── Logout ───────────────────────────────────────────────────────────────────

@router.post("/logout", response_model=LogoutResponse)
def logout(payload: dict = Depends(get_token_payload)):
    """Revoke the caller's current token.

    A JWT is stateless, so we can't "delete" it — instead we remember its unique
    `jti` in a denylist and reject it from then on. The frontend should also drop
    its stored copy of the token.
    """
    revoke_token(payload.get("jti"))
    return LogoutResponse()


# ─── Change password ──────────────────────────────────────────────────────────

@router.post("/change-password", response_model=ChangePasswordResponse)
def change_password(
    req: ChangePasswordRequest,
    payload: dict = Depends(get_token_payload),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Change your own password.

    Requires the current password even though you are already logged in — this
    stops someone who grabbed an unlocked laptop from locking the real owner out.
    """
    if not verify_password(req.current_password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Current password is incorrect.",
        )

    new_password = req.new_password or ""

    if len(new_password) < MIN_PASSWORD_LENGTH:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"New password must be at least {MIN_PASSWORD_LENGTH} characters.",
        )

    if new_password == req.current_password:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="New password must be different from the current password.",
        )

    user.hashed_password = hash_password(new_password)
    db.commit()

    # Force a re-login: the old token was issued before the password changed.
    revoke_token(payload.get("jti"))

    return ChangePasswordResponse()
