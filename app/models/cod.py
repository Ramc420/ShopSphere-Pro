from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Numeric, DateTime, Text, ForeignKey, Boolean, JSON
from sqlalchemy.orm import relationship
from app.database import Base


def utc_now():
    return datetime.now(timezone.utc)


class CODConfig(Base):
    """
    Module 32: Cash on Delivery Management
    Stores threshold eligibility rules, restricted zones/postal codes,
    and extra COD handling surcharges.
    """
    __tablename__ = "cod_configs"

    id = Column(Integer, primary_key=True, index=True)
    is_enabled = Column(Boolean, default=True, nullable=False)
    min_order_amount = Column(Numeric(10, 2), default=0.00, nullable=False)
    max_order_amount = Column(Numeric(10, 2), default=1000.00, nullable=False)
    restricted_postal_codes = Column(JSON, default=list, nullable=False)
    extra_fee = Column(Numeric(10, 2), default=0.00, nullable=False)

    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)


class CODCollection(Base):
    """
    Module 32: COD Collection & Reconciliation
    Tracks courier/driver cash collections, deposit confirmations,
    and order payment reconciliations.
    """
    __tablename__ = "cod_collections"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    expected_amount = Column(Numeric(12, 2), nullable=False)
    collected_amount = Column(Numeric(12, 2), default=0.00, nullable=False)
    status = Column(String(50), default="PENDING", nullable=False)  # PENDING, COLLECTED, FAILED, DEPOSITED, RECONCILED
    collected_by = Column(String(100), nullable=True)
    collected_at = Column(DateTime, nullable=True)
    reconciled_at = Column(DateTime, nullable=True)
    notes = Column(Text, nullable=True)

    created_at = Column(DateTime, default=utc_now, nullable=False)

    order = relationship("Order")

