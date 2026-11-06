from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    phone: Optional[str] = Field(None, max_length=32)
    role: str = Field(default="CUSTOMER", description="SUPER_ADMIN, ADMIN, EMPLOYEE, CUSTOMER")
    department: Optional[str] = None
    is_verified: bool = True


class UserUpdate(BaseModel):
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    phone: Optional[str] = Field(None, max_length=32)
    department: Optional[str] = None


class UserStatusUpdate(BaseModel):
    status: str = Field(..., description="ACTIVE, INACTIVE, SUSPENDED, DEACTIVATED")
    reason: Optional[str] = None


class UserRoleAssign(BaseModel):
    role: str = Field(..., description="SUPER_ADMIN, ADMIN, EMPLOYEE, CUSTOMER")


class UserResponse(BaseModel):
    id: int
    email: str
    first_name: str
    last_name: str
    phone: Optional[str] = None
    role: str
    status: str
    is_verified: bool
    registration_status: str
    department: Optional[str] = None
    permissions: List[str] = []
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserActivityLogResponse(BaseModel):
    id: int
    user_id: Optional[int]
    actor_id: Optional[int]
    action: str
    ip_address: Optional[str]
    user_agent: Optional[str]
    details: Optional[str]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
