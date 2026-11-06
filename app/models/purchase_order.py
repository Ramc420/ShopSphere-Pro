from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, Text, Numeric, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


def utc_now():
    return datetime.now(timezone.utc)


class PurchaseOrder(Base):
    __tablename__ = "purchase_orders"

    id = Column(Integer, primary_key=True, index=True)
    po_number = Column(String(50), unique=True, nullable=False, index=True)
    supplier_id = Column(Integer, ForeignKey("suppliers.id", ondelete="RESTRICT"), nullable=False, index=True)
    warehouse_id = Column(Integer, ForeignKey("warehouses.id", ondelete="RESTRICT"), nullable=False, index=True)
    created_by_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    status = Column(String(30), default="DRAFT", index=True)  # DRAFT, SUBMITTED, PARTIALLY_RECEIVED, RECEIVED, CANCELLED
    total_cost = Column(Numeric(12, 2), default=0.00)
    expected_delivery_date = Column(DateTime(timezone=True), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    supplier = relationship("Supplier")
    warehouse = relationship("Warehouse")
    created_by = relationship("User", foreign_keys=[created_by_user_id])
    items = relationship("PurchaseOrderItem", back_populates="purchase_order", cascade="all, delete-orphan")
    status_history = relationship("POStatusHistory", back_populates="purchase_order", cascade="all, delete-orphan")


class PurchaseOrderItem(Base):
    __tablename__ = "purchase_order_items"

    id = Column(Integer, primary_key=True, index=True)
    purchase_order_id = Column(Integer, ForeignKey("purchase_orders.id", ondelete="CASCADE"), nullable=False, index=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="RESTRICT"), nullable=False)
    variant_id = Column(Integer, ForeignKey("product_variants.id", ondelete="SET NULL"), nullable=True)
    quantity_ordered = Column(Integer, nullable=False)
    quantity_received = Column(Integer, default=0)
    unit_cost = Column(Numeric(12, 2), nullable=False)
    total_cost = Column(Numeric(12, 2), nullable=False)

    purchase_order = relationship("PurchaseOrder", back_populates="items")
    product = relationship("Product")
    variant = relationship("ProductVariant")


class POStatusHistory(Base):
    __tablename__ = "po_status_history"

    id = Column(Integer, primary_key=True, index=True)
    purchase_order_id = Column(Integer, ForeignKey("purchase_orders.id", ondelete="CASCADE"), nullable=False, index=True)
    changed_by_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    from_status = Column(String(30), nullable=True)
    to_status = Column(String(30), nullable=False)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now)

    purchase_order = relationship("PurchaseOrder", back_populates="status_history")
    changed_by = relationship("User", foreign_keys=[changed_by_user_id])

