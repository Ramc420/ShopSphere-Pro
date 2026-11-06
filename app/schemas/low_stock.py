from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class ThresholdConfigure(BaseModel):
    product_id: int
    variant_id: Optional[int] = None
    warehouse_id: Optional[int] = None
    threshold: int = Field(..., ge=0, description="Minimum stock threshold")
    reorder_quantity: int = Field(50, gt=0, description="Recommended reorder quantity")
    change_reason: Optional[str] = "Threshold updated"


class ThresholdResponse(BaseModel):
    id: int
    product_id: int
    variant_id: Optional[int] = None
    warehouse_id: Optional[int] = None
    threshold: int
    reorder_quantity: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ThresholdHistoryResponse(BaseModel):
    id: int
    product_id: int
    variant_id: Optional[int] = None
    old_threshold: int
    new_threshold: int
    change_reason: Optional[str] = None
    changed_by_user_id: Optional[int] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class RestockAlertResponse(BaseModel):
    id: int
    product_id: int
    variant_id: Optional[int] = None
    warehouse_id: Optional[int] = None
    current_stock: int
    threshold: int
    severity: str
    is_resolved: bool
    notes: Optional[str] = None
    created_at: datetime
    resolved_at: Optional[datetime] = None
    product_name: Optional[str] = None
    sku: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class LowStockReportItem(BaseModel):
    product_id: int
    variant_id: Optional[int] = None
    product_name: str
    sku: str
    warehouse_id: Optional[int] = None
    warehouse_name: Optional[str] = None
    current_stock: int
    threshold: int
    shortage: int
    severity: str
    reorder_recommended: int

    model_config = ConfigDict(from_attributes=True)

