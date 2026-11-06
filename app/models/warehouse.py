from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from app.database import Base


def utc_now():
    return datetime.now(timezone.utc)


class Warehouse(Base):
    __tablename__ = "warehouses"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(50), unique=True, index=True, nullable=False)
    name = Column(String(150), nullable=False)
    address_line1 = Column(String(255), nullable=False)
    city = Column(String(100), nullable=False)
    state_province = Column(String(100), nullable=False)
    postal_code = Column(String(20), nullable=False)
    country = Column(String(100), default="United States", nullable=False)
    
    capacity_units = Column(Integer, default=10000, nullable=False)
    current_utilization = Column(Integer, default=0, nullable=False)
    status = Column(String(20), default="ACTIVE", nullable=False)  # ACTIVE, INACTIVE, MAINTENANCE
    manager_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    manager = relationship("User")
    inventory = relationship("WarehouseInventory", back_populates="warehouse", cascade="all, delete-orphan")


class WarehouseInventory(Base):
    __tablename__ = "warehouse_inventory"

    id = Column(Integer, primary_key=True, index=True)
    warehouse_id = Column(Integer, ForeignKey("warehouses.id", ondelete="CASCADE"), nullable=False, index=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)
    variant_id = Column(Integer, ForeignKey("product_variants.id", ondelete="CASCADE"), nullable=True, index=True)
    
    quantity = Column(Integer, default=0, nullable=False)
    reserved_quantity = Column(Integer, default=0, nullable=False)
    aisle_location = Column(String(50), nullable=True)  # e.g., "A1-B2-C3"
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    warehouse = relationship("Warehouse", back_populates="inventory")
    product = relationship("Product")
    variant = relationship("ProductVariant")

    __table_args__ = (
        UniqueConstraint("warehouse_id", "product_id", "variant_id", name="uq_warehouse_product_variant"),
    )

