from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Numeric, DateTime, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.database import Base


def utc_now():
    return datetime.now(timezone.utc)


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    order_number = Column(String(64), unique=True, index=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    shipping_address_id = Column(Integer, ForeignKey("addresses.id", ondelete="SET NULL"), nullable=True, index=True)
    billing_address_id = Column(Integer, ForeignKey("addresses.id", ondelete="SET NULL"), nullable=True, index=True)
    shipping_address_snapshot = Column(Text, nullable=True)
    billing_address_snapshot = Column(Text, nullable=True)
    
    status = Column(String(50), default="CONFIRMED", index=True, nullable=False)  # PENDING, CONFIRMED, PROCESSING, SHIPPED, DELIVERED, CANCELLED
    payment_status = Column(String(50), default="PENDING", index=True, nullable=False)  # PENDING, PAID, REFUNDED
    
    subtotal_amount = Column(Numeric(12, 2), default=0.00, nullable=False)
    discount_amount = Column(Numeric(12, 2), default=0.00, nullable=False)
    tax_amount = Column(Numeric(12, 2), default=0.00, nullable=False)
    shipping_amount = Column(Numeric(12, 2), default=0.00, nullable=False)
    total_amount = Column(Numeric(12, 2), default=0.00, nullable=False)
    
    coupon_code = Column(String(50), nullable=True)
    shipping_method_code = Column(String(50), nullable=True)
    notes = Column(Text, nullable=True)

    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    user = relationship("User", back_populates="orders")
    shipping_address = relationship("Address", foreign_keys=[shipping_address_id], back_populates="shipping_orders")
    billing_address = relationship("Address", foreign_keys=[billing_address_id], back_populates="billing_orders")
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")
    status_history = relationship("OrderStatusHistory", back_populates="order", cascade="all, delete-orphan")


class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, index=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="RESTRICT"), nullable=False, index=True)
    variant_id = Column(Integer, ForeignKey("product_variants.id", ondelete="SET NULL"), nullable=True, index=True)
    
    product_name = Column(String(255), nullable=False)
    sku = Column(String(100), nullable=False)
    description_snapshot = Column(Text, nullable=True)
    variant_attributes_snapshot = Column(JSON, nullable=True)
    fulfillment_status = Column(String(50), default="PENDING", nullable=False)  # PENDING, PROCESSING, FULFILLED, CANCELLED, RETURNED
    unit_price = Column(Numeric(10, 2), nullable=False)
    quantity = Column(Integer, default=1, nullable=False)
    subtotal = Column(Numeric(12, 2), nullable=False)

    @property
    def total_price(self):
        return self.subtotal

    order = relationship("Order", back_populates="items")
    product = relationship("Product")
    variant = relationship("ProductVariant")


class OrderStatusHistory(Base):
    __tablename__ = "order_status_history"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, index=True)
    from_status = Column(String(50), nullable=True)
    to_status = Column(String(50), nullable=False)
    notes = Column(String(255), nullable=True)
    changed_by_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)

    order = relationship("Order", back_populates="status_history")
    changed_by = relationship("User")
