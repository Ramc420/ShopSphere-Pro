from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class PromotionCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    code: str = Field(..., min_length=2, max_length=50)
    description: Optional[str] = None
    promotion_type: str = Field("PERCENTAGE_DISCOUNT", description="PERCENTAGE_DISCOUNT, FIXED_DISCOUNT, CATEGORY_DISCOUNT")
    discount_value: float = Field(..., gt=0)
    min_order_amount: float = Field(0.0, ge=0)
    target_category_id: Optional[int] = None
    target_product_id: Optional[int] = None
    start_date: datetime
    end_date: datetime
    is_active: bool = True


class PromotionResponse(BaseModel):
    id: int
    name: str
    code: str
    description: Optional[str] = None
    promotion_type: str
    discount_value: float
    min_order_amount: float
    target_category_id: Optional[int] = None
    target_product_id: Optional[int] = None
    start_date: datetime
    end_date: datetime
    is_active: bool
    is_currently_active: bool = True
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PromotionHistoryResponse(BaseModel):
    id: int
    promotion_id: int
    order_id: Optional[int] = None
    user_id: Optional[int] = None
    discount_amount: float
    applied_at: datetime

    model_config = ConfigDict(from_attributes=True)

