from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


def utc_now():
    return datetime.now(timezone.utc)


class BackgroundTaskJob(Base):
    __tablename__ = "background_task_jobs"

    id = Column(Integer, primary_key=True, index=True)
    task_name = Column(String(100), nullable=False, index=True)
    task_type = Column(String(50), nullable=False, index=True)  # REPORT_EXPORT, SCHEDULED_SUMMARY, NOTIFICATION_TASK, STOCK_SYNC
    status = Column(String(30), default="PENDING", index=True)  # PENDING, RUNNING, COMPLETED, FAILED, RETRYING
    export_format = Column(String(20), nullable=True)           # CSV, EXCEL, PDF
    file_path = Column(String(255), nullable=True)
    payload = Column(Text, nullable=True)                       # JSON configuration or parameters
    result_summary = Column(Text, nullable=True)                # Output result or metrics
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)
    created_by_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now)

    created_by = relationship("User", foreign_keys=[created_by_user_id])

