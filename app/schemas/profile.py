from datetime import date, datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict, EmailStr, Field


class CustomerProfileUpdate(BaseModel):
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    phone: Optional[str] = Field(None, max_length=32)
    secondary_email: Optional[EmailStr] = None
    date_of_birth: Optional[date] = None
    gender: Optional[str] = Field(None, max_length=30)
    avatar_url: Optional[str] = Field(None, max_length=500)
    marketing_opt_in: Optional[bool] = None
    notes: Optional[str] = None


class CustomerProfileResponse(BaseModel):
    id: int
    user_id: int
    first_name: str
    last_name: str
    email: str
    phone: Optional[str] = None
    secondary_email: Optional[str] = None
    date_of_birth: Optional[date] = None
    gender: Optional[str] = None
    avatar_url: Optional[str] = None
    marketing_opt_in: bool
    notes: Optional[str] = None
    deactivation_requested: bool
    deactivation_reason: Optional[str] = None
    deactivation_status: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DeactivationRequestCreate(BaseModel):
    reason: str = Field(..., min_length=5, max_length=500, description="Reason for requesting account deactivation")


class DeactivationReviewRequest(BaseModel):
    decision: str = Field(..., description="APPROVED or REJECTED")
    admin_notes: Optional[str] = None


class ProfileChangeHistoryResponse(BaseModel):
    id: int
    user_id: int
    changed_by_user_id: Optional[int]
    field_name: str
    old_value: Optional[str]
    new_value: Optional[str]
    changed_at: datetime

    model_config = ConfigDict(from_attributes=True)
