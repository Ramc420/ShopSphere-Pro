from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


def utc_now():
    return datetime.now(timezone.utc)


class AdminAuditLog(Base):
    __tablename__ = "admin_audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    actor_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    action = Column(String(100), nullable=False, index=True)
    entity_type = Column(String(50), nullable=False, index=True)  # PRODUCT, PRICING, INVENTORY, ORDER, REFUND, USER, SUPPLIER, SYSTEM
    entity_id = Column(String(100), nullable=True, index=True)
    ip_address = Column(String(100), nullable=True)
    old_values = Column(Text, nullable=True)
    new_values = Column(Text, nullable=True)
    reason = Column(Text, nullable=True)
    is_immutable = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, index=True)

    actor = relationship("User", foreign_keys=[actor_id])

