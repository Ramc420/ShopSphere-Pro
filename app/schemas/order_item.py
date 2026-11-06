from typing import Optional, Dict, Any
from pydantic import BaseModel, ConfigDict


class OrderItemFulfillmentUpdate(BaseModel):
    fulfillment_status: str  # PENDING, PROCESSING, FULFILLED, CANCELLED, RETURNED


class OrderItemDetailResponse(BaseModel):
    id: int
    order_id: int
    product_id: int
    variant_id: Optional[int] = None
    product_name: str
    sku: str
    description_snapshot: Optional[str] = None
    variant_attributes_snapshot: Optional[Dict[str, Any]] = None
    fulfillment_status: str
    unit_price: float
    quantity: int
    subtotal: float

    model_config = ConfigDict(from_attributes=True)

