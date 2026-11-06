from datetime import datetime
from typing import Optional, List
from decimal import Decimal
from pydantic import BaseModel, ConfigDict


class POCreateItem(BaseModel):
    product_id: int
    variant_id: Optional[int] = None
    quantity_ordered: int
    unit_cost: Decimal


class POCreate(BaseModel):
    supplier_id: int
    warehouse_id: int
    expected_delivery_date: Optional[datetime] = None
    notes: Optional[str] = None
    items: List[POCreateItem]


class POResponseItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    purchase_order_id: int
    product_id: int
    variant_id: Optional[int] = None
    quantity_ordered: int
    quantity_received: int
    unit_cost: Decimal
    total_cost: Decimal


class POStatusHistoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    purchase_order_id: int
    changed_by_user_id: Optional[int] = None
    from_status: Optional[str] = None
    to_status: str
    notes: Optional[str] = None
    created_at: datetime


class POResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    po_number: str
    supplier_id: int
    warehouse_id: int
    created_by_user_id: Optional[int] = None
    status: str
    total_cost: Decimal
    expected_delivery_date: Optional[datetime] = None
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    items: List[POResponseItem] = []
    status_history: List[POStatusHistoryResponse] = []


class POStatusUpdate(BaseModel):
    status: str  # SUBMITTED, CANCELLED
    notes: Optional[str] = None


class POReceiveItem(BaseModel):
    item_id: int
    quantity_to_receive: int


class POReceiveRequest(BaseModel):
    items: List[POReceiveItem]
    notes: Optional[str] = None

