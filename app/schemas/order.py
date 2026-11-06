from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class OrderItemResponse(BaseModel):
    id: int
    order_id: int
    product_id: int
    variant_id: Optional[int] = None
    product_name: str
    sku: str
    unit_price: float
    quantity: int
    subtotal: float

    model_config = ConfigDict(from_attributes=True)


class OrderStatusHistoryResponse(BaseModel):
    id: int
    order_id: int
    from_status: Optional[str] = None
    to_status: str
    notes: Optional[str] = None
    changed_by_user_id: Optional[int] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class OrderResponse(BaseModel):
    id: int
    order_number: str
    user_id: int
    shipping_address_id: Optional[int] = None
    billing_address_id: Optional[int] = None
    shipping_address_snapshot: Optional[str] = None
    billing_address_snapshot: Optional[str] = None
    status: str
    payment_status: str
    subtotal_amount: float
    discount_amount: float
    tax_amount: float
    shipping_amount: float
    total_amount: float
    coupon_code: Optional[str] = None
    shipping_method_code: Optional[str] = None
    notes: Optional[str] = None
    items: List[OrderItemResponse] = []
    status_history: List[OrderStatusHistoryResponse] = []
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class OrderStatusUpdate(BaseModel):
    status: str = Field(..., description="PENDING, CONFIRMED, PROCESSING, SHIPPED, DELIVERED, CANCELLED")
    notes: Optional[str] = None

