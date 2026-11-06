from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class CalculationItemDetail(BaseModel):
    product_id: int
    variant_id: Optional[int] = None
    product_name: str
    sku: str
    unit_price: float
    quantity: int
    subtotal: float

    model_config = ConfigDict(from_attributes=True)


class CartCalculationRequest(BaseModel):
    cart_id: Optional[int] = None
    coupon_code: Optional[str] = None
    shipping_method_code: Optional[str] = None
    shipping_address_id: Optional[int] = None


class CartCalculationSummary(BaseModel):
    items: List[CalculationItemDetail] = []
    items_count: int = 0
    subtotal_amount: float = 0.0
    coupon_discount: float = 0.0
    promotion_discount: float = 0.0
    total_discount: float = 0.0
    tax_amount: float = 0.0
    tax_rate_percent: float = 0.0
    shipping_amount: float = 0.0
    shipping_method_name: Optional[str] = None
    grand_total: float = 0.0
    applied_coupon: Optional[str] = None
    applied_promotions: List[str] = []

    model_config = ConfigDict(from_attributes=True)


class CheckoutInitRequest(BaseModel):
    cart_id: Optional[int] = None
    shipping_address_id: int
    billing_address_id: int
    shipping_method_code: str
    coupon_code: Optional[str] = None
    notes: Optional[str] = None


class CheckoutSessionResponse(BaseModel):
    checkout_id: str
    order_id: int
    order_number: str
    status: str
    summary: CartCalculationSummary
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

