from typing import Generator, List, Optional
from fastapi import Depends, HTTPException, Request, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy.orm import Session

from app.config import settings
from app.core.permissions import UserRole, UserStatus, get_role_permissions
from app.core.security import decode_token
from app.database import get_db
from app.models.token_blacklist import TokenBlacklist
from app.models.user import User

security_scheme = HTTPBearer(auto_error=False)


def get_client_ip(request: Request) -> str:
    """Extract client IP address from headers or connection."""
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def get_current_user_and_jti(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(security_scheme),
    db: Session = Depends(get_db)
) -> tuple[User, str]:
    """Verify JWT access token, check blacklist, and return current user and token JTI."""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication credentials were not provided",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    token = credentials.credentials
    try:
        payload = decode_token(token)
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Could not validate credentials: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    token_type = payload.get("type")
    if token_type != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type: access token expected",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    jti = payload.get("jti")
    if not jti:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token structure (missing jti)",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    # Check if token is blacklisted (Module 1: Logout and token revocation)
    blacklisted = db.query(TokenBlacklist).filter(TokenBlacklist.jti == jti).first()
    if blacklisted:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has been revoked or invalidated. Please log in again.",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token subject missing",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User associated with token was not found",
        )
        
    if user.status == UserStatus.DEACTIVATED.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account has been deactivated. Please contact support.",
        )
        
    if user.status == UserStatus.SUSPENDED.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account has been suspended due to policy violations.",
        )
        
    if user.status != UserStatus.ACTIVE.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Account is inactive (current status: {user.status}).",
        )
        
    return user, jti


def get_current_user(
    current_data: tuple[User, str] = Depends(get_current_user_and_jti)
) -> User:
    """Return authenticated active user."""
    return current_data[0]


def get_current_active_user(user: User = Depends(get_current_user)) -> User:
    return user


def get_optional_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(security_scheme),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """Optional user resolution for endpoints that support anonymous + authenticated calls."""
    if not credentials:
        return None
    try:
        user, _ = get_current_user_and_jti(credentials, db)
        return user
    except HTTPException:
        return None


def require_roles(*roles: str):
    """Enforce role-based access control (RBAC)."""
    def role_checker(user: User = Depends(get_current_user)) -> User:
        if user.role == UserRole.SUPER_ADMIN.value:
            return user
        if user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied: Requires one of roles: {', '.join(roles)}",
            )
        return user
    return role_checker


def require_permissions(*permissions: str):
    """Enforce granular permission-based access control."""
    def permission_checker(user: User = Depends(get_current_user)) -> User:
        if user.role == UserRole.SUPER_ADMIN.value:
            return user
        user_perms = set(get_role_permissions(user.role))
        missing = [p for p in permissions if p not in user_perms]
        if missing:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied: Missing required permission(s): {', '.join(missing)}",
            )
        return user
    return permission_checker


def mask_sensitive_data(val: Optional[str], kind: str = "phone") -> Optional[str]:
    """Mask phone or email for privacy restriction (Module 4)."""
    if not val:
        return val
    if kind == "phone":
        clean = val.strip()
        if len(clean) > 4:
            return "*" * (len(clean) - 4) + clean[-4:]
        return "****"
    if kind == "email":
        parts = val.split("@")
        if len(parts) == 2:
            name, domain = parts
            masked_name = name[0] + "*" * max(1, len(name) - 2) + (name[-1] if len(name) > 1 else "")
            return f"{masked_name}@{domain}"
    return val
