from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class TransferCreate(BaseModel):
    source_warehouse_id: int
    destination_warehouse_id: int
    product_id: int
    variant_id: Optional[int] = None
    requested_quantity: int = Field(..., gt=0, description="Quantity to transfer")
    notes: Optional[str] = None


class TransferDispatch(BaseModel):
    dispatched_quantity: int = Field(..., gt=0)
    notes: Optional[str] = None


class TransferReceive(BaseModel):
    received_quantity: int = Field(..., gt=0)
    notes: Optional[str] = None


class TransferResponse(BaseModel):
    id: int
    transfer_number: str
    source_warehouse_id: int
    destination_warehouse_id: int
    product_id: int
    variant_id: Optional[int] = None
    requested_quantity: int
    dispatched_quantity: int
    received_quantity: int
    status: str
    notes: Optional[str] = None
    requested_by_user_id: Optional[int] = None
    dispatched_by_user_id: Optional[int] = None
    received_by_user_id: Optional[int] = None
    dispatched_at: Optional[datetime] = None
    received_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    source_warehouse_name: Optional[str] = None
    destination_warehouse_name: Optional[str] = None
    product_name: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

