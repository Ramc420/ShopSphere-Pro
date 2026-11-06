from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class ShippingMethodCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    code: str = Field(..., min_length=2, max_length=50)
    description: Optional[str] = None
    base_charge: float = Field(0.0, ge=0)
    free_shipping_threshold: Optional[float] = Field(None, ge=0)
    estimated_days_min: int = Field(3, ge=1)
    estimated_days_max: int = Field(5, ge=1)
    is_active: bool = True


class ShippingMethodResponse(BaseModel):
    id: int
    name: str
    code: str
    description: Optional[str] = None
    base_charge: float
    free_shipping_threshold: Optional[float] = None
    estimated_days_min: int
    estimated_days_max: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ShippingEstimateRequest(BaseModel):
    subtotal: float = Field(..., ge=0)
    country: str = "USA"
    state_province: Optional[str] = None


class ShippingEstimateOption(BaseModel):
    code: str
    name: str
    estimated_days: str
    charge: float
    is_free: bool


class ShippingEstimateResponse(BaseModel):
    options: List[ShippingEstimateOption]

