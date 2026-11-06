from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from app.database import Base


def utc_now():
    return datetime.now(timezone.utc)


class InventoryItem(Base):
    __tablename__ = "inventory_items"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)
    variant_id = Column(Integer, ForeignKey("product_variants.id", ondelete="CASCADE"), nullable=True, index=True)
    
    total_quantity = Column(Integer, default=0, nullable=False)
    available_quantity = Column(Integer, default=0, nullable=False)
    reserved_quantity = Column(Integer, default=0, nullable=False)
    low_stock_threshold = Column(Integer, default=5, nullable=False)
    
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    product = relationship("Product")
    variant = relationship("ProductVariant")
    movements = relationship("StockMovement", back_populates="inventory_item", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("product_id", "variant_id", name="uq_inventory_product_variant"),
    )


class StockMovement(Base):
    __tablename__ = "stock_movements"

    id = Column(Integer, primary_key=True, index=True)
    inventory_item_id = Column(Integer, ForeignKey("inventory_items.id", ondelete="CASCADE"), nullable=False, index=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)
    variant_id = Column(Integer, ForeignKey("product_variants.id", ondelete="CASCADE"), nullable=True, index=True)
    warehouse_id = Column(Integer, ForeignKey("warehouses.id", ondelete="SET NULL"), nullable=True, index=True)
    
    movement_type = Column(String(30), nullable=False)  # ADDITION, REDUCTION, RESERVATION, RELEASE, ADJUSTMENT
    quantity = Column(Integer, nullable=False)  # Quantity moved (positive or negative)
    balance_after = Column(Integer, nullable=False)
    
    reference_type = Column(String(50), nullable=True)  # PURCHASE_ORDER, ORDER_RESERVATION, ORDER_FULFILLMENT, MANUAL
    reference_id = Column(String(100), nullable=True)
    notes = Column(Text, nullable=True)
    performed_by_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)

    inventory_item = relationship("InventoryItem", back_populates="movements")
    product = relationship("Product")
    variant = relationship("ProductVariant")
    performed_by = relationship("User")

