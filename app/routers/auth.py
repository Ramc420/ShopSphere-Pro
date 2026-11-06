from datetime import datetime, timezone
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, Request, status
from jose import JWTError
from sqlalchemy.orm import Session

from app.config import settings
from app.core.audit import log_user_activity
from app.core.dependencies import (
    get_client_ip,
    get_current_user,
    get_current_user_and_jti,
    security_scheme,
)
from app.core.permissions import UserStatus, get_role_permissions
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    validate_password_strength,
    verify_password,
)
from app.database import get_db
from app.models.token_blacklist import TokenBlacklist
from app.models.user import User
from app.schemas.auth import (
    LoginRequest,
    LogoutRequest,
    PasswordChangeRequest,
    RefreshTokenRequest,
    TokenResponse,
    TokenUserData,
)
from app.schemas.common import MessageResponse

router = APIRouter(prefix="/auth", tags=["Module 1: Authentication & Authorization"])


@router.post("/login", response_model=TokenResponse)
def login(
    payload: LoginRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Authenticate customer or employee credentials, verify password hash,
    and issue JWT access and refresh tokens.
    """
    email_clean = payload.email.strip().lower()
    user = db.query(User).filter(User.email == email_clean).first()
    
    if not user or not verify_password(payload.password, user.hashed_password):
        # Log failed attempt
        if user:
            log_user_activity(
                db,
                action="LOGIN_FAILED",
                user_id=user.id,
                ip_address=get_client_ip(request),
                user_agent=request.headers.get("user-agent"),
                details={"reason": "Invalid password"}
            )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check user account status
    if user.status == UserStatus.DEACTIVATED.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account has been deactivated. Please contact customer support.",
        )
    if user.status == UserStatus.SUSPENDED.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is currently suspended.",
        )
    if user.status != UserStatus.ACTIVE.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Account is not active (current status: {user.status}).",
        )

    # Generate Access & Refresh tokens
    token_claims = {
        "sub": str(user.id),
        "email": user.email,
        "role": user.role,
        "name": f"{user.first_name} {user.last_name}"
    }
    
    access_token_data = create_access_token(token_claims)
    refresh_token_data = create_refresh_token(token_claims)

    # Audit log successful login
    log_user_activity(
        db,
        action="LOGIN_SUCCESS",
        user_id=user.id,
        ip_address=get_client_ip(request),
        user_agent=request.headers.get("user-agent"),
        details={"role": user.role}
    )

    permissions = get_role_permissions(user.role)
    
    return TokenResponse(
        access_token=access_token_data["token"],
        refresh_token=refresh_token_data["token"],
        token_type="Bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=TokenUserData(
            id=user.id,
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            role=user.role,
            status=user.status,
            is_verified=user.is_verified,
            permissions=permissions
        )
    )


@router.post("/refresh", response_model=TokenResponse)
def refresh_token(
    payload: RefreshTokenRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Exchange a valid refresh token for a fresh access token and rotated refresh token.
    Implements token rotation and invalidates the previous refresh token.
    """
    try:
        token_payload = decode_token(payload.refresh_token)
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid or expired refresh token: {str(e)}",
        )

    if token_payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token type must be 'refresh'",
        )

    jti = token_payload.get("jti")
    if not jti:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing token identifier",
        )

    # Verify if refresh token was already revoked
    is_revoked = db.query(TokenBlacklist).filter(TokenBlacklist.jti == jti).first()
    if is_revoked:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token has been revoked. Please log in again.",
        )

    user_id = token_payload.get("sub")
    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user or user.status != UserStatus.ACTIVE.value:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User associated with token is not active or not found",
        )

    # Invalidate previous refresh token (Rotation security)
    exp_timestamp = token_payload.get("exp")
    expires_at = datetime.fromtimestamp(exp_timestamp, tz=timezone.utc) if exp_timestamp else None
    
    revoked_old = TokenBlacklist(
        jti=jti,
        user_id=user.id,
        token_type="refresh",
        expires_at=expires_at
    )
    db.add(revoked_old)
    db.commit()

    # Issue new pair
    token_claims = {
        "sub": str(user.id),
        "email": user.email,
        "role": user.role,
        "name": f"{user.first_name} {user.last_name}"
    }
    new_access = create_access_token(token_claims)
    new_refresh = create_refresh_token(token_claims)

    log_user_activity(
        db,
        action="TOKEN_REFRESH",
        user_id=user.id,
        ip_address=get_client_ip(request),
        user_agent=request.headers.get("user-agent"),
    )

    permissions = get_role_permissions(user.role)

    return TokenResponse(
        access_token=new_access["token"],
        refresh_token=new_refresh["token"],
        token_type="Bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=TokenUserData(
            id=user.id,
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            role=user.role,
            status=user.status,
            is_verified=user.is_verified,
            permissions=permissions
        )
    )


@router.post("/logout", response_model=MessageResponse)
def logout(
    payload: LogoutRequest = LogoutRequest(),
    current_data: tuple[User, str] = Depends(get_current_user_and_jti),
    request: Request = None,
    db: Session = Depends(get_db)
):
    """
    Log out customer or employee and revoke the current access token and optional refresh token.
    """
    user, jti = current_data
    
    # Revoke access token
    revoked_access = TokenBlacklist(
        jti=jti,
        user_id=user.id,
        token_type="access"
    )
    db.add(revoked_access)

    # If client supplied refresh token, revoke it too
    if payload.refresh_token:
        try:
            r_payload = decode_token(payload.refresh_token)
            r_jti = r_payload.get("jti")
            if r_jti:
                revoked_refresh = TokenBlacklist(
                    jti=r_jti,
                    user_id=user.id,
                    token_type="refresh"
                )
                db.add(revoked_refresh)
        except Exception:
            pass

    db.commit()

    log_user_activity(
        db,
        action="LOGOUT",
        user_id=user.id,
        ip_address=get_client_ip(request) if request else None,
        user_agent=request.headers.get("user-agent") if request else None
    )

    return MessageResponse(
        success=True,
        message="Successfully logged out. Tokens have been revoked."
    )


@router.post("/change-password", response_model=MessageResponse)
def change_password(
    payload: PasswordChangeRequest,
    current_user: User = Depends(get_current_user),
    request: Request = None,
    db: Session = Depends(get_db)
):
    """
    Verify current password, validate strong password complexity,
    and update password hash.
    """
    if not verify_password(payload.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password verification failed",
        )

    if payload.new_password != payload.confirm_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password and confirmation password do not match",
        )

    if not validate_password_strength(payload.new_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 8 characters long and contain uppercase, lowercase, numeric, and special characters",
        )

    current_user.hashed_password = hash_password(payload.new_password)
    db.commit()

    log_user_activity(
        db,
        action="PASSWORD_CHANGE",
        user_id=current_user.id,
        ip_address=get_client_ip(request) if request else None,
        user_agent=request.headers.get("user-agent") if request else None
    )

    return MessageResponse(
        success=True,
        message="Password has been successfully changed"
    )


@router.get("/me", response_model=TokenUserData)
def get_me(current_user: User = Depends(get_current_user)):
    """
    Get profile information and permissions for the currently authenticated user.
    """
    return TokenUserData(
        id=current_user.id,
        email=current_user.email,
        first_name=current_user.first_name,
        last_name=current_user.last_name,
        role=current_user.role,
        status=current_user.status,
        is_verified=current_user.is_verified,
        permissions=get_role_permissions(current_user.role)
    )

