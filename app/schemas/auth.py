from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=1, description="Account password")


class TokenUserData(BaseModel):
    id: int
    email: str
    first_name: str
    last_name: str
    role: str
    status: str
    is_verified: bool
    permissions: List[str]


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "Bearer"
    expires_in: int
    user: TokenUserData


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class PasswordChangeRequest(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=8)
    confirm_password: str = Field(..., min_length=8)


class LogoutRequest(BaseModel):
    refresh_token: Optional[str] = None

