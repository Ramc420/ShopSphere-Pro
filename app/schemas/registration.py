import re
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, field_validator


class CustomerRegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, description="Must include upper, lower, number, special char")
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    phone: str = Field(..., description="Valid international phone number, e.g. +14155552671")
    marketing_opt_in: bool = False

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        clean = re.sub(r"[\s\-\(\)]", "", v)
        if not re.match(r"^\+?[1-9]\d{7,14}$", clean):
            raise ValueError("Phone number must be valid international format with 8 to 15 digits (e.g., +14155552671)")
        return clean


class VerifyEmailRequest(BaseModel):
    token: str = Field(..., min_length=1)


class ResendVerificationRequest(BaseModel):
    email: EmailStr


class RegistrationResponse(BaseModel):
    user_id: int
    email: str
    first_name: str
    last_name: str
    registration_status: str
    verification_token: Optional[str] = None
    verification_link: Optional[str] = None
    message: str

