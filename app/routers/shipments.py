import uuid
from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.models.order import Order
from app.models.shipping_order import Shipment, TrackingEvent, DeliveryAssignment
from app.schemas.shipment import (
    ShipmentCreate, ShipmentDispatch, ShipmentResponse,
    TrackingEventCreate, TrackingEventResponse,
    DeliveryAssignRequest, DeliveryAttemptRequest, DeliveryConfirmRequest,
    DeliveryAssignmentResponse
)
from app.core.dependencies import require_permissions
from app.core.permissions import Permission

router = APIRouter(prefix="/shipments", tags=["Modules 33 - 35: Shipment, Tracking & Delivery Management"])


def utc_now():
    return datetime.now(timezone.utc)


# =====================================================================
# MODULE 33: SHIPPING ORDER MANAGEMENT
# =====================================================================
@router.post("/", response_model=ShipmentResponse, status_code=status.HTTP_201_CREATED)
def create_shipment(
    payload: ShipmentCreate,
    current_user: User = Depends(require_permissions(Permission.SHIPMENTS_WRITE.value)),
    db: Session = Depends(get_db)
):
    """
    Module 33: Create shipment record, assign shipping provider, and generate shipment reference.
    """
    order = db.query(Order).filter(Order.id == payload.order_id).first()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")

    shipment_num = f"SHP-{uuid.uuid4().hex[:8].upper()}"
    tracking_num = f"TRK-{payload.carrier_name[:3].upper()}-{uuid.uuid4().hex[:10].upper()}"

    shipment = Shipment(
        shipment_number=shipment_num,
        order_id=order.id,
        carrier_name=payload.carrier_name,
        tracking_number=tracking_num,
        status="LABEL_GENERATED",
        shipping_label_url=f"/static/labels/{shipment_num}.pdf",
        dispatch_notes=payload.dispatch_notes
    )
    db.add(shipment)
    db.flush()

    # Initial tracking event
    evt = TrackingEvent(
        shipment_id=shipment.id,
        tracking_number=tracking_num,
        event_type="LABEL_CREATED",
        location="Fulfillment Logistics Hub",
        description=f"Shipping label generated for carrier {payload.carrier_name}"
    )
    db.add(evt)
    db.commit()
    db.refresh(shipment)
    return shipment


@router.get("/", response_model=List[ShipmentResponse])
def list_shipments(
    order_id: Optional[int] = None,
    current_user: User = Depends(require_permissions(Permission.SHIPMENTS_READ.value)),
    db: Session = Depends(get_db)
):
    """
    List shipments, optionally filtered by order ID.
    """
    query = db.query(Shipment)
    if order_id:
        query = query.filter(Shipment.order_id == order_id)

    if current_user.role == "CUSTOMER":
        query = query.join(Order).filter(Order.user_id == current_user.id)

    shipments = query.order_by(Shipment.created_at.desc()).all()
    return shipments


@router.get("/{shipment_id}", response_model=ShipmentResponse)
def get_shipment_details(
    shipment_id: int,
    current_user: User = Depends(require_permissions(Permission.SHIPMENTS_READ.value)),
    db: Session = Depends(get_db)
):
    """
    Retrieve shipment details, tracking events, and delivery assignment.
    """
    shipment = db.query(Shipment).filter(Shipment.id == shipment_id).first()
    if not shipment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Shipment not found")

    return shipment


@router.post("/{shipment_id}/dispatch", response_model=ShipmentResponse)
def dispatch_shipment(
    shipment_id: int,
    payload: ShipmentDispatch,
    current_user: User = Depends(require_permissions(Permission.SHIPMENTS_WRITE.value)),
    db: Session = Depends(get_db)
):
    """
    Record dispatch information and transition shipment to DISPATCHED / IN_TRANSIT.
    """
    shipment = db.query(Shipment).filter(Shipment.id == shipment_id).first()
    if not shipment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Shipment not found")

    shipment.status = "DISPATCHED"
    shipment.dispatched_at = utc_now()
    if payload.dispatch_notes:
        shipment.dispatch_notes = payload.dispatch_notes
    if payload.tracking_number:
        shipment.tracking_number = payload.tracking_number

    # Also update order status to SHIPPED if not already
    order = db.query(Order).filter(Order.id == shipment.order_id).first()
    if order and order.status in ["CONFIRMED", "PROCESSING"]:
        order.status = "SHIPPED"

    evt = TrackingEvent(
        shipment_id=shipment.id,
        tracking_number=shipment.tracking_number,
        event_type="PICKED_UP",
        location="Central Logistics Dock",
        description="Shipment picked up by carrier vehicle"
    )
    db.add(evt)
    db.commit()
    db.refresh(shipment)
    return shipment


# =====================================================================
# MODULE 34: SHIPMENT TRACKING
# =====================================================================
@router.get("/tracking/{tracking_number}", response_model=List[TrackingEventResponse])
def get_tracking_timeline(
    tracking_number: str,
    db: Session = Depends(get_db)
):
    """
    Module 34: Retrieve full carrier tracking history and event log.
    Publicly accessible with tracking number.
    """
    events = db.query(TrackingEvent).filter(
        TrackingEvent.tracking_number == tracking_number
    ).order_by(TrackingEvent.event_timestamp.asc()).all()

    if not events:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No tracking records found for this tracking number")

    return events


@router.post("/{shipment_id}/events", response_model=TrackingEventResponse, status_code=status.HTTP_201_CREATED)
def record_tracking_event(
    shipment_id: int,
    payload: TrackingEventCreate,
    current_user: User = Depends(require_permissions(Permission.SHIPMENTS_WRITE.value)),
    db: Session = Depends(get_db)
):
    """
    Module 34: Log a checkpoint update or delivery exception event from carrier.
    """
    shipment = db.query(Shipment).filter(Shipment.id == shipment_id).first()
    if not shipment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Shipment not found")

    event = TrackingEvent(
        shipment_id=shipment.id,
        tracking_number=shipment.tracking_number,
        event_type=payload.event_type.upper(),
        location=payload.location,
        description=payload.description
    )
    db.add(event)

    # Update shipment status accordingly
    if payload.event_type.upper() in ["IN_TRANSIT", "OUT_FOR_DELIVERY", "EXCEPTION"]:
        shipment.status = payload.event_type.upper()

    db.commit()
    db.refresh(event)
    return event


# =====================================================================
# MODULE 35: DELIVERY MANAGEMENT
# =====================================================================
@router.post("/deliveries/assign", response_model=DeliveryAssignmentResponse, status_code=status.HTTP_201_CREATED)
def assign_delivery_personnel(
    payload: DeliveryAssignRequest,
    current_user: User = Depends(require_permissions(Permission.DELIVERY_MANAGE.value)),
    db: Session = Depends(get_db)
):
    """
    Module 35: Assign shipment to delivery personnel or dedicated courier.
    """
    shipment = db.query(Shipment).filter(Shipment.id == payload.shipment_id).first()
    if not shipment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Shipment not found")

    existing = db.query(DeliveryAssignment).filter(DeliveryAssignment.shipment_id == payload.shipment_id).first()
    if existing:
        existing.driver_name = payload.driver_name
        existing.driver_phone = payload.driver_phone
        existing.status = "ASSIGNED"
        db.commit()
        db.refresh(existing)
        return existing

    assignment = DeliveryAssignment(
        shipment_id=shipment.id,
        driver_name=payload.driver_name,
        driver_phone=payload.driver_phone,
        status="ASSIGNED"
    )
    db.add(assignment)
    db.commit()
    db.refresh(assignment)
    return assignment


@router.post("/deliveries/{assignment_id}/attempt", response_model=DeliveryAssignmentResponse)
def record_delivery_attempt(
    assignment_id: int,
    payload: DeliveryAttemptRequest,
    current_user: User = Depends(require_permissions(Permission.DELIVERY_MANAGE.value)),
    db: Session = Depends(get_db)
):
    """
    Module 35: Record failed delivery attempt and exception reason.
    """
    assignment = db.query(DeliveryAssignment).filter(DeliveryAssignment.id == assignment_id).first()
    if not assignment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Delivery assignment not found")

    assignment.delivery_attempts += 1
    assignment.status = "ATTEMPTED_FAILED"
    assignment.failure_reason = payload.failure_reason

    # Add tracking exception
    shipment = db.query(Shipment).filter(Shipment.id == assignment.shipment_id).first()
    if shipment:
        shipment.status = "EXCEPTION"
        evt = TrackingEvent(
            shipment_id=shipment.id,
            tracking_number=shipment.tracking_number,
            event_type="EXCEPTION",
            location="Customer Destination Address",
            description=f"Delivery attempt #{assignment.delivery_attempts} failed: {payload.failure_reason}"
        )
        db.add(evt)

    db.commit()
    db.refresh(assignment)
    return assignment


@router.post("/deliveries/{assignment_id}/confirm", response_model=DeliveryAssignmentResponse)
def confirm_delivery_completion(
    assignment_id: int,
    payload: DeliveryConfirmRequest,
    current_user: User = Depends(require_permissions(Permission.DELIVERY_MANAGE.value)),
    db: Session = Depends(get_db)
):
    """
    Module 35: Capture delivery confirmation, signature name, and mark shipment & order DELIVERED.
    """
    assignment = db.query(DeliveryAssignment).filter(DeliveryAssignment.id == assignment_id).first()
    if not assignment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Delivery assignment not found")

    assignment.status = "DELIVERED"
    assignment.recipient_signature_name = payload.recipient_signature_name
    assignment.confirmation_notes = payload.confirmation_notes
    assignment.completed_at = utc_now()

    shipment = db.query(Shipment).filter(Shipment.id == assignment.shipment_id).first()
    if shipment:
        shipment.status = "DELIVERED"
        shipment.delivered_at = utc_now()

        # Update order status to DELIVERED
        order = db.query(Order).filter(Order.id == shipment.order_id).first()
        if order:
            order.status = "DELIVERED"

        evt = TrackingEvent(
            shipment_id=shipment.id,
            tracking_number=shipment.tracking_number,
            event_type="DELIVERED",
            location="Customer Destination Address",
            description=f"Package delivered and signed by {payload.recipient_signature_name}"
        )
        db.add(evt)

    db.commit()
    db.refresh(assignment)
    return assignment

