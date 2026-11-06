from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class CouponCreate(BaseModel):
    code: str = Field(..., min_length=3, max_length=50)
    description: Optional[str] = None
    discount_type: str = Field("PERCENTAGE", description="PERCENTAGE or FIXED_AMOUNT")
    discount_value: float = Field(..., gt=0)
    min_purchase_amount: float = Field(0.0, ge=0)
    max_discount_amount: Optional[float] = None
    usage_limit: Optional[int] = None
    valid_from: Optional[datetime] = None
    valid_until: Optional[datetime] = None
    is_active: bool = True


class CouponUpdate(BaseModel):
    description: Optional[str] = None
    discount_value: Optional[float] = None
    min_purchase_amount: Optional[float] = None
    max_discount_amount: Optional[float] = None
    usage_limit: Optional[int] = None
    valid_from: Optional[datetime] = None
    valid_until: Optional[datetime] = None
    is_active: Optional[bool] = None


class CouponResponse(BaseModel):
    id: int
    code: str
    description: Optional[str] = None
    discount_type: str
    discount_value: float
    min_purchase_amount: float
    max_discount_amount: Optional[float] = None
    usage_limit: Optional[int] = None
    used_count: int
    valid_from: Optional[datetime] = None
    valid_until: Optional[datetime] = None
    is_active: bool
    is_valid_now: bool = True
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CouponValidateRequest(BaseModel):
    code: str
    cart_subtotal: float = Field(..., ge=0)


class CouponValidateResponse(BaseModel):
    is_valid: bool
    code: str
    discount_type: str
    discount_value: float
    calculated_discount: float
    message: str

