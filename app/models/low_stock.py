from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.database import Base


def utc_now():
    return datetime.now(timezone.utc)


class LowStockThreshold(Base):
    __tablename__ = "low_stock_thresholds"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)
    variant_id = Column(Integer, ForeignKey("product_variants.id", ondelete="CASCADE"), nullable=True, index=True)
    warehouse_id = Column(Integer, ForeignKey("warehouses.id", ondelete="CASCADE"), nullable=True, index=True)
    
    threshold = Column(Integer, default=10, nullable=False)
    reorder_quantity = Column(Integer, default=50, nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    product = relationship("Product")
    variant = relationship("ProductVariant")
    warehouse = relationship("Warehouse")

    @property
    def status(self) -> str:
        return "RESOLVED" if self.is_resolved else "OPEN"


class StockThresholdChangeHistory(Base):
    __tablename__ = "stock_threshold_change_history"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)
    variant_id = Column(Integer, ForeignKey("product_variants.id", ondelete="SET NULL"), nullable=True, index=True)
    old_threshold = Column(Integer, nullable=False)
    new_threshold = Column(Integer, nullable=False)
    change_reason = Column(String(255), nullable=True)
    changed_by_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)

    product = relationship("Product")
    variant = relationship("ProductVariant")
    changed_by = relationship("User")


class RestockAlert(Base):
    __tablename__ = "restock_alerts"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)
    variant_id = Column(Integer, ForeignKey("product_variants.id", ondelete="SET NULL"), nullable=True, index=True)
    warehouse_id = Column(Integer, ForeignKey("warehouses.id", ondelete="SET NULL"), nullable=True, index=True)
    current_stock = Column(Integer, nullable=False)
    threshold = Column(Integer, nullable=False)
    severity = Column(String(32), default="LOW", nullable=False)  # LOW, CRITICAL, OUT_OF_STOCK
    is_resolved = Column(Boolean, default=False, index=True, nullable=False)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    resolved_at = Column(DateTime, nullable=True)

    product = relationship("Product")
    variant = relationship("ProductVariant")
    warehouse = relationship("Warehouse")

    @property
    def status(self) -> str:
        return "RESOLVED" if self.is_resolved else "OPEN"

