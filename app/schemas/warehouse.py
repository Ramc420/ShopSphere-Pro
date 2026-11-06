from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict, Field


class WarehouseCreate(BaseModel):
    code: str = Field(..., min_length=2, max_length=50, description="Unique warehouse identifier e.g. WH-EAST-01")
    name: str = Field(..., min_length=2, max_length=150)
    address_line1: str = Field(..., min_length=3, max_length=255)
    city: str = Field(..., min_length=2, max_length=100)
    state_province: str = Field(..., min_length=2, max_length=100)
    postal_code: str = Field(..., min_length=3, max_length=20)
    country: str = Field(default="United States", max_length=100)
    capacity_units: int = Field(default=10000, gt=0, description="Maximum total units the facility can hold")
    manager_id: Optional[int] = None
    status: str = Field(default="ACTIVE", description="ACTIVE, INACTIVE, MAINTENANCE")


class WarehouseUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=150)
    address_line1: Optional[str] = None
    city: Optional[str] = None
    state_province: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = None
    capacity_units: Optional[int] = Field(None, gt=0)
    manager_id: Optional[int] = None
    status: Optional[str] = None


class WarehouseResponse(BaseModel):
    id: int
    code: str
    name: str
    address_line1: str
    city: str
    state_province: str
    postal_code: str
    country: str
    capacity_units: int
    current_utilization: int
    utilization_percentage: float = 0.0
    status: str
    manager_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class WarehouseStockAssignRequest(BaseModel):
    product_id: int
    variant_id: Optional[int] = None
    quantity: int = Field(..., gt=0)
    aisle_location: Optional[str] = Field(None, description="e.g. Aisle 3, Shelf B, Bin 12")


class WarehouseInventoryResponse(BaseModel):
    id: int
    warehouse_id: int
    product_id: int
    variant_id: Optional[int] = None
    product_name: Optional[str] = None
    sku: Optional[str] = None
    quantity: int
    reserved_quantity: int
    aisle_location: Optional[str] = None
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

