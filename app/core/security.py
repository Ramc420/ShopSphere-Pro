import re
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional, Union
from jose import JWTError, jwt
from passlib.context import CryptContext
from app.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=4)


def hash_password(password: str) -> str:
    """Hash password using bcrypt."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify plain password against hashed password."""
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception:
        return False


def validate_password_strength(password: str) -> bool:
    """
    Ensure password has at least:
    - 8 characters
    - 1 uppercase letter
    - 1 lowercase letter
    - 1 number
    - 1 special character
    """
    if len(password) < 8:
        return False
    if not re.search(r"[A-Z]", password):
        return False
    if not re.search(r"[a-z]", password):
        return False
    if not re.search(r"\d", password):
        return False
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>\-_]", password):
        return False
    return True


def create_token(
    data: Dict[str, Any],
    expires_delta: Optional[timedelta] = None,
    token_type: str = "access"
) -> Dict[str, Any]:
    """Create a signed JWT token with unique JTI."""
    to_encode = data.copy()
    now = datetime.now(timezone.utc)
    
    if expires_delta:
        expire = now + expires_delta
    else:
        if token_type == "access":
            expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        else:
            expire = now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
            
    token_id = str(uuid.uuid4())
    to_encode.update({
        "exp": expire,
        "iat": now,
        "nbf": now,
        "jti": token_id,
        "type": token_type
    })
    
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return {
        "token": encoded_jwt,
        "jti": token_id,
        "expires_at": expire
    }


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> Dict[str, Any]:
    return create_token(data, expires_delta=expires_delta, token_type="access")


def create_refresh_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> Dict[str, Any]:
    return create_token(data, expires_delta=expires_delta, token_type="refresh")


def decode_token(token: str) -> Dict[str, Any]:
    """Decode and validate JWT token."""
    return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
