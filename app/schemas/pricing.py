from datetime import datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class PriceCreate(BaseModel):
    product_id: int
    variant_id: Optional[int] = None
    base_price: Decimal = Field(..., ge=Decimal("0.00"), description="Regular base price")
    sale_price: Optional[Decimal] = Field(None, ge=Decimal("0.00"), description="Promotional sale price")
    sale_start_date: Optional[datetime] = None
    sale_end_date: Optional[datetime] = None
    currency: str = Field(default="USD", max_length=10)
    reason: Optional[str] = Field("Initial price configuration", description="Reason for price setting")

    @model_validator(mode="after")
    def validate_pricing(self):
        if self.sale_price is not None:
            if self.sale_price > self.base_price:
                raise ValueError("Sale price cannot exceed base price.")
            if self.sale_start_date and self.sale_end_date:
                if self.sale_end_date <= self.sale_start_date:
                    raise ValueError("sale_end_date must be strictly after sale_start_date.")
        return self


class PriceUpdate(BaseModel):
    base_price: Optional[Decimal] = Field(None, ge=Decimal("0.00"))
    sale_price: Optional[Decimal] = Field(None, ge=Decimal("0.00"))
    sale_start_date: Optional[datetime] = None
    sale_end_date: Optional[datetime] = None
    currency: Optional[str] = None
    is_active: Optional[bool] = None
    reason: str = Field(..., min_length=3, description="Mandatory audit reason for price modification")


class PriceResponse(BaseModel):
    id: int
    product_id: int
    variant_id: Optional[int] = None
    base_price: Decimal
    sale_price: Optional[Decimal] = None
    sale_start_date: Optional[datetime] = None
    sale_end_date: Optional[datetime] = None
    currency: str
    is_active: bool
    is_on_sale: bool = False
    effective_price: Decimal
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PriceHistoryResponse(BaseModel):
    id: int
    product_id: int
    variant_id: Optional[int] = None
    changed_by_user_id: Optional[int] = None
    old_base_price: Optional[Decimal] = None
    new_base_price: Decimal
    old_sale_price: Optional[Decimal] = None
    new_sale_price: Optional[Decimal] = None
    reason: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

