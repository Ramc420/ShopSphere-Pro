from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


def utc_now():
    return datetime.now(timezone.utc)


class UserActivityLog(Base):
    __tablename__ = "user_activity_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    actor_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    action = Column(String(100), nullable=False, index=True)
    ip_address = Column(String(100), nullable=True)
    user_agent = Column(String(255), nullable=True)
    details = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False, index=True)

    user = relationship("User", foreign_keys=[user_id], back_populates="activity_logs")
    actor = relationship("User", foreign_keys=[actor_id], back_populates="performed_logs")


class ProfileChangeHistory(Base):
    __tablename__ = "profile_change_history"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    changed_by_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    field_name = Column(String(100), nullable=False)
    old_value = Column(Text, nullable=True)
    new_value = Column(Text, nullable=True)
    changed_at = Column(DateTime, default=utc_now, nullable=False, index=True)

    user = relationship("User", foreign_keys=[user_id], back_populates="profile_history")
    changed_by = relationship("User", foreign_keys=[changed_by_user_id])

