from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class CartItemAdd(BaseModel):
    product_id: int
    variant_id: Optional[int] = None
    quantity: int = Field(1, gt=0, description="Quantity to add")


class CartItemUpdate(BaseModel):
    quantity: int = Field(..., gt=0, description="Updated quantity")


class CartItemResponse(BaseModel):
    id: int
    cart_id: int
    product_id: int
    variant_id: Optional[int] = None
    product_name: str
    sku: str
    unit_price: float
    quantity: int
    subtotal: float
    is_available: bool = True
    available_stock: int = 0

    model_config = ConfigDict(from_attributes=True)


class CartResponse(BaseModel):
    id: int
    user_id: Optional[int] = None
    status: str
    items: List[CartItemResponse] = []
    item_count: int = 0
    subtotal: float = 0.0
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

