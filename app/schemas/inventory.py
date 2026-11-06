from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class StockAdditionRequest(BaseModel):
    quantity: int = Field(..., gt=0, description="Quantity to add to stock")
    warehouse_id: Optional[int] = None
    reference_type: str = Field(default="PURCHASE_ORDER", description="e.g. PURCHASE_ORDER, RESTOCK, RETURN")
    reference_id: Optional[str] = None
    notes: Optional[str] = None


class StockReductionRequest(BaseModel):
    quantity: int = Field(..., gt=0, description="Quantity to reduce from stock")
    warehouse_id: Optional[int] = None
    reference_type: str = Field(default="MANUAL_ADJUSTMENT", description="e.g. DAMAGE, SHRINKAGE, WRITE_OFF")
    reference_id: Optional[str] = None
    notes: Optional[str] = None


class StockReservationRequest(BaseModel):
    quantity: int = Field(..., gt=0, description="Quantity to reserve (e.g. for checkout)")
    reference_id: Optional[str] = Field(None, description="e.g. order or cart reference")
    notes: Optional[str] = None


class StockReleaseRequest(BaseModel):
    quantity: int = Field(..., gt=0, description="Quantity to release from reservation back to available")
    reference_id: Optional[str] = None
    notes: Optional[str] = None


class InventoryItemResponse(BaseModel):
    id: int
    product_id: int
    variant_id: Optional[int] = None
    total_quantity: int
    available_quantity: int
    reserved_quantity: int
    low_stock_threshold: int
    availability_status: str
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class StockMovementResponse(BaseModel):
    id: int
    inventory_item_id: int
    product_id: int
    variant_id: Optional[int] = None
    warehouse_id: Optional[int] = None
    movement_type: str
    quantity: int
    balance_after: int
    reference_type: Optional[str] = None
    reference_id: Optional[str] = None
    notes: Optional[str] = None
    performed_by_user_id: Optional[int] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

