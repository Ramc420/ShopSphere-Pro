from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, Numeric, Float, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


def utc_now():
    return datetime.now(timezone.utc)


class Supplier(Base):
    __tablename__ = "suppliers"

    id = Column(Integer, primary_key=True, index=True)
    supplier_code = Column(String(50), unique=True, nullable=False, index=True)
    company_name = Column(String(255), nullable=False, index=True)
    supplier_type = Column(String(30), default="SUPPLIER", index=True)  # SUPPLIER, MARKETPLACE_SELLER
    contact_name = Column(String(150), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    phone = Column(String(50), nullable=False)
    tax_id = Column(String(100), nullable=True)
    business_registration_number = Column(String(100), nullable=True)
    address_line = Column(String(255), nullable=False)
    city = Column(String(100), nullable=False)
    state = Column(String(100), nullable=False)
    country = Column(String(100), nullable=False, default="USA")
    postal_code = Column(String(20), nullable=False)
    status = Column(String(30), default="PENDING_APPROVAL", index=True)  # PENDING_APPROVAL, APPROVED, REJECTED, SUSPENDED
    rating = Column(Float, default=5.0)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    products = relationship("ProductSupplier", back_populates="supplier", cascade="all, delete-orphan")
    history = relationship("SupplierHistory", back_populates="supplier", cascade="all, delete-orphan")


class SupplierHistory(Base):
    __tablename__ = "supplier_history"

    id = Column(Integer, primary_key=True, index=True)
    supplier_id = Column(Integer, ForeignKey("suppliers.id", ondelete="CASCADE"), nullable=False, index=True)
    changed_by_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    action = Column(String(50), nullable=False)  # REGISTERED, APPROVED, REJECTED, SUSPENDED, UPDATED
    from_status = Column(String(30), nullable=True)
    to_status = Column(String(30), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now)

    supplier = relationship("Supplier", back_populates="history")
    changed_by = relationship("User", foreign_keys=[changed_by_user_id])


class ProductSupplier(Base):
    __tablename__ = "product_suppliers"

    id = Column(Integer, primary_key=True, index=True)
    supplier_id = Column(Integer, ForeignKey("suppliers.id", ondelete="CASCADE"), nullable=False, index=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)
    supplier_sku = Column(String(100), nullable=True)
    negotiated_cost = Column(Numeric(12, 2), nullable=False, default=0.00)
    lead_time_days = Column(Integer, default=7)
    is_primary = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=utc_now)

    supplier = relationship("Supplier", back_populates="products")
    product = relationship("Product")

