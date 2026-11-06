from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict


class ShipmentCreate(BaseModel):
    order_id: int
    carrier_name: str = "FedEx"
    dispatch_notes: Optional[str] = None


class ShipmentDispatch(BaseModel):
    tracking_number: Optional[str] = None
    dispatch_notes: Optional[str] = None


class TrackingEventCreate(BaseModel):
    event_type: str  # LABEL_CREATED, PICKED_UP, IN_TRANSIT, OUT_FOR_DELIVERY, DELIVERED, EXCEPTION
    location: Optional[str] = None
    description: str


class TrackingEventResponse(BaseModel):
    id: int
    shipment_id: int
    tracking_number: str
    event_type: str
    location: Optional[str] = None
    description: str
    event_timestamp: datetime

    model_config = ConfigDict(from_attributes=True)


class DeliveryAssignmentResponse(BaseModel):
    id: int
    shipment_id: int
    driver_name: str
    driver_phone: Optional[str] = None
    status: str
    delivery_attempts: int
    failure_reason: Optional[str] = None
    recipient_signature_name: Optional[str] = None
    confirmation_notes: Optional[str] = None
    assigned_at: datetime
    completed_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class ShipmentResponse(BaseModel):
    id: int
    shipment_number: str
    order_id: int
    carrier_name: str
    tracking_number: str
    status: str
    shipping_label_url: Optional[str] = None
    dispatch_notes: Optional[str] = None
    dispatched_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    tracking_events: List[TrackingEventResponse] = []
    delivery_assignment: Optional[DeliveryAssignmentResponse] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DeliveryAssignRequest(BaseModel):
    shipment_id: int
    driver_name: str
    driver_phone: Optional[str] = None


class DeliveryAttemptRequest(BaseModel):
    failure_reason: str


class DeliveryConfirmRequest(BaseModel):
    recipient_signature_name: str
    confirmation_notes: Optional[str] = None

