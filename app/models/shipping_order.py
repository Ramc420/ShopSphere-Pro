from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


def utc_now():
    return datetime.now(timezone.utc)


class Shipment(Base):
    """
    Module 33: Shipping Order Management
    Stores shipment records, assigned carrier providers, tracking IDs,
    dispatch timestamps, and overall shipment status.
    """
    __tablename__ = "shipments"

    id = Column(Integer, primary_key=True, index=True)
    shipment_number = Column(String(50), unique=True, index=True, nullable=False)
    order_id = Column(Integer, ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, index=True)
    carrier_name = Column(String(100), nullable=False)  # FedEx, UPS, DHL, USPS, LocalCourier
    tracking_number = Column(String(100), unique=True, index=True, nullable=False)
    status = Column(String(50), default="CREATED", index=True, nullable=False)  # CREATED, LABEL_GENERATED, DISPATCHED, IN_TRANSIT, OUT_FOR_DELIVERY, DELIVERED, EXCEPTION
    shipping_label_url = Column(String(255), nullable=True)
    dispatch_notes = Column(Text, nullable=True)
    dispatched_at = Column(DateTime, nullable=True)
    delivered_at = Column(DateTime, nullable=True)

    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    order = relationship("Order")
    tracking_events = relationship("TrackingEvent", back_populates="shipment", cascade="all, delete-orphan")
    delivery_assignment = relationship("DeliveryAssignment", back_populates="shipment", uselist=False, cascade="all, delete-orphan")


class TrackingEvent(Base):
    """
    Module 34: Shipment Tracking
    Stores carrier tracking checkpoints, locations, and exception logs.
    """
    __tablename__ = "tracking_events"

    id = Column(Integer, primary_key=True, index=True)
    shipment_id = Column(Integer, ForeignKey("shipments.id", ondelete="CASCADE"), nullable=False, index=True)
    tracking_number = Column(String(100), index=True, nullable=False)
    event_type = Column(String(50), nullable=False)  # LABEL_CREATED, PICKED_UP, IN_TRANSIT, OUT_FOR_DELIVERY, DELIVERED, EXCEPTION
    location = Column(String(150), nullable=True)
    description = Column(Text, nullable=False)
    event_timestamp = Column(DateTime, default=utc_now, nullable=False)

    shipment = relationship("Shipment", back_populates="tracking_events")


class DeliveryAssignment(Base):
    """
    Module 35: Delivery Management
    Assigns deliveries to couriers/personnel, records delivery attempts,
    captures customer delivery confirmation, and logs failure reasons.
    """
    __tablename__ = "delivery_assignments"

    id = Column(Integer, primary_key=True, index=True)
    shipment_id = Column(Integer, ForeignKey("shipments.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    driver_name = Column(String(100), nullable=False)
    driver_phone = Column(String(50), nullable=True)
    status = Column(String(50), default="ASSIGNED", nullable=False)  # ASSIGNED, OUT_FOR_DELIVERY, DELIVERED, ATTEMPTED_FAILED
    delivery_attempts = Column(Integer, default=0, nullable=False)
    failure_reason = Column(String(255), nullable=True)
    recipient_signature_name = Column(String(100), nullable=True)
    confirmation_notes = Column(Text, nullable=True)

    assigned_at = Column(DateTime, default=utc_now, nullable=False)
    completed_at = Column(DateTime, nullable=True)

    shipment = relationship("Shipment", back_populates="delivery_assignment")

