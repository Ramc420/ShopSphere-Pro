from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


def utc_now():
    return datetime.now(timezone.utc)


class InventoryTransfer(Base):
    __tablename__ = "inventory_transfers"

    id = Column(Integer, primary_key=True, index=True)
    transfer_number = Column(String(64), unique=True, index=True, nullable=False)
    source_warehouse_id = Column(Integer, ForeignKey("warehouses.id", ondelete="RESTRICT"), nullable=False, index=True)
    destination_warehouse_id = Column(Integer, ForeignKey("warehouses.id", ondelete="RESTRICT"), nullable=False, index=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)
    variant_id = Column(Integer, ForeignKey("product_variants.id", ondelete="SET NULL"), nullable=True, index=True)
    
    requested_quantity = Column(Integer, nullable=False)
    dispatched_quantity = Column(Integer, default=0, nullable=False)
    received_quantity = Column(Integer, default=0, nullable=False)
    status = Column(String(32), default="REQUESTED", index=True, nullable=False)  # REQUESTED, DISPATCHED, RECEIVED, CANCELLED
    notes = Column(Text, nullable=True)

    requested_by_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    dispatched_by_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    received_by_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    dispatched_at = Column(DateTime, nullable=True)
    received_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    source_warehouse = relationship("Warehouse", foreign_keys=[source_warehouse_id])
    destination_warehouse = relationship("Warehouse", foreign_keys=[destination_warehouse_id])
    product = relationship("Product")
    variant = relationship("ProductVariant")
    requested_by = relationship("User", foreign_keys=[requested_by_user_id])
    dispatched_by = relationship("User", foreign_keys=[dispatched_by_user_id])
    received_by = relationship("User", foreign_keys=[received_by_user_id])

