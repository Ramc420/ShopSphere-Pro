from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict


class CODConfigUpdate(BaseModel):
    is_enabled: bool = True
    min_order_amount: float = 0.00
    max_order_amount: float = 1000.00
    restricted_postal_codes: List[str] = []
    extra_fee: float = 0.00


class CODConfigResponse(BaseModel):
    id: int
    is_enabled: bool
    min_order_amount: float
    max_order_amount: float
    restricted_postal_codes: List[str]
    extra_fee: float
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CODEligibilityCheck(BaseModel):
    order_id: Optional[int] = None
    order_amount: float
    postal_code: str


class CODEligibilityResponse(BaseModel):
    is_eligible: bool
    reason: Optional[str] = None
    extra_fee: float = 0.00


class CODRecordCollection(BaseModel):
    collected_amount: float
    collected_by: Optional[str] = None
    notes: Optional[str] = None


class CODCollectionResponse(BaseModel):
    id: int
    order_id: int
    expected_amount: float
    collected_amount: float
    status: str
    collected_by: Optional[str] = None
    collected_at: Optional[datetime] = None
    reconciled_at: Optional[datetime] = None
    notes: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

