from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


def utc_now():
    return datetime.now(timezone.utc)


class ProductMedia(Base):
    __tablename__ = "product_media"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=True, index=True)
    variant_id = Column(Integer, ForeignKey("product_variants.id", ondelete="SET NULL"), nullable=True, index=True)
    
    original_filename = Column(String(255), nullable=False)
    storage_path = Column(String(500), nullable=False)
    file_url = Column(String(500), nullable=False)
    file_size_bytes = Column(Integer, nullable=False)
    mime_type = Column(String(100), nullable=False)
    file_type = Column(String(50), default="IMAGE", nullable=False)  # IMAGE, DOCUMENT, MANUAL, SPEC_SHEET
    
    # Image specific metadata
    image_width = Column(Integer, nullable=True)
    image_height = Column(Integer, nullable=True)
    
    checksum_sha256 = Column(String(64), nullable=True)
    is_primary = Column(Boolean, default=False, nullable=False)
    display_order = Column(Integer, default=0, nullable=False)
    uploaded_by_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    
    created_at = Column(DateTime, default=utc_now, nullable=False)

    product = relationship("Product", back_populates="media")
    variant = relationship("ProductVariant", back_populates="media")
    uploader = relationship("User", foreign_keys=[uploaded_by_user_id])

