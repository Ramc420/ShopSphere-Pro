from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from app.database import Base


def utc_now():
    return datetime.now(timezone.utc)


class Cart(Base):
    __tablename__ = "carts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)
    session_id = Column(String(128), nullable=True, index=True)
    status = Column(String(32), default="ACTIVE", index=True, nullable=False)  # ACTIVE, CHECKED_OUT, ABANDONED
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    user = relationship("User")
    items = relationship("CartItem", back_populates="cart", cascade="all, delete-orphan")


class CartItem(Base):
    __tablename__ = "cart_items"

    id = Column(Integer, primary_key=True, index=True)
    cart_id = Column(Integer, ForeignKey("carts.id", ondelete="CASCADE"), nullable=False, index=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)
    variant_id = Column(Integer, ForeignKey("product_variants.id", ondelete="CASCADE"), nullable=True, index=True)
    quantity = Column(Integer, default=1, nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    cart = relationship("Cart", back_populates="items")
    product = relationship("Product")
    variant = relationship("ProductVariant")

    __table_args__ = (
        UniqueConstraint("cart_id", "product_id", "variant_id", name="uq_cart_product_variant"),
    )

