from datetime import datetime, timezone
from sqlalchemy import Column, Integer, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from app.database import Base


def utc_now():
    return datetime.now(timezone.utc)


class WishlistItem(Base):
    __tablename__ = "wishlist_items"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)
    variant_id = Column(Integer, ForeignKey("product_variants.id", ondelete="CASCADE"), nullable=True, index=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)

    user = relationship("User")
    product = relationship("Product")
    variant = relationship("ProductVariant")

    __table_args__ = (
        UniqueConstraint("user_id", "product_id", "variant_id", name="uq_wishlist_user_product_variant"),
    )

