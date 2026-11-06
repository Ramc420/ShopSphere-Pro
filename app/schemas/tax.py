from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class TaxRateCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    country: str = Field("USA", max_length=3)
    state_province: str = Field("*", max_length=64)
    postal_code: Optional[str] = None
    rate_percentage: float = Field(..., ge=0, le=100, description="Tax rate percentage e.g. 8.25 for 8.25%")
    category_id: Optional[int] = None
    is_active: bool = True


class TaxRateUpdate(BaseModel):
    name: Optional[str] = None
    rate_percentage: Optional[float] = Field(None, ge=0, le=100)
    is_active: Optional[bool] = None
    change_reason: Optional[str] = "Tax rate update"


class TaxRateResponse(BaseModel):
    id: int
    name: str
    country: str
    state_province: str
    postal_code: Optional[str] = None
    rate_percentage: float
    category_id: Optional[int] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TaxHistoryResponse(BaseModel):
    id: int
    tax_rate_id: int
    old_rate: float
    new_rate: float
    change_reason: Optional[str] = None
    changed_by_user_id: Optional[int] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TaxCalculationRequest(BaseModel):
    country: str = "USA"
    state_province: str = "*"
    amount: float = Field(..., ge=0)
    category_id: Optional[int] = None


class TaxCalculationResponse(BaseModel):
    rate_percentage: float
    taxable_amount: float
    tax_amount: float
    rule_name: str

