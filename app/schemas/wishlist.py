from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class WishlistItemAdd(BaseModel):
    product_id: int
    variant_id: Optional[int] = None


class WishlistItemResponse(BaseModel):
    id: int
    user_id: int
    product_id: int
    variant_id: Optional[int] = None
    product_name: str
    sku: str
    price: float
    availability_status: str
    is_in_stock: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

