from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.models.notification import Notification
from app.schemas.notification import NotificationCreate, NotificationResponse, UnreadCountResponse
from app.core.dependencies import get_current_user, require_permissions
from app.core.permissions import Permission

router = APIRouter(prefix="/notifications", tags=["Module 41: Notification Management"])


def utc_now():
    return datetime.now(timezone.utc)


@router.get("/me", response_model=List[NotificationResponse])
def get_my_notifications(
    is_read: Optional[bool] = Query(None, description="Filter by read status"),
    notification_type: Optional[str] = Query(None, description="Filter by notification type"),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieve notifications for the authenticated user."""
    query = db.query(Notification).filter(Notification.user_id == current_user.id)
    if is_read is not None:
        query = query.filter(Notification.is_read == is_read)
    if notification_type:
        query = query.filter(Notification.notification_type == notification_type)
    
    return query.order_by(Notification.created_at.desc()).limit(limit).all()


@router.get("/me/unread-count", response_model=UnreadCountResponse)
def get_unread_count(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get the unread notification count for the authenticated user badge."""
    count = db.query(Notification).filter(
        Notification.user_id == current_user.id,
        Notification.is_read == False
    ).count()
    return UnreadCountResponse(unread_count=count)


@router.patch("/{notification_id}/read", response_model=NotificationResponse)
def mark_notification_read(
    notification_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Mark a specific notification as read."""
    notif = db.query(Notification).filter(Notification.id == notification_id).first()
    if not notif:
        raise HTTPException(status_code=404, detail="Notification not found")
    
    # Ownership or staff check
    if notif.user_id != current_user.id and current_user.role not in ["ADMIN", "SUPER_ADMIN"]:
        raise HTTPException(status_code=403, detail="Not authorized to modify this notification")
    
    notif.is_read = True
    notif.read_at = utc_now()
    db.commit()
    db.refresh(notif)
    return notif


@router.post("/me/mark-all-read")
def mark_all_notifications_read(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Mark all unread notifications as read for current user."""
    updated = db.query(Notification).filter(
        Notification.user_id == current_user.id,
        Notification.is_read == False
    ).update({"is_read": True, "read_at": utc_now()}, synchronize_session=False)
    db.commit()
    return {"message": "All notifications marked as read", "count": updated}


@router.post("", response_model=NotificationResponse, status_code=status.HTTP_201_CREATED)
def create_notification(
    payload: NotificationCreate,
    current_user: User = Depends(require_permissions(Permission.NOTIFICATIONS_WRITE.value)),
    db: Session = Depends(get_db)
):
    """
    Generate an in-app notification.
    Used for customer order updates, payment/refund status, or staff alerts.
    """
    target_user = db.query(User).filter(User.id == payload.user_id).first()
    if not target_user:
        raise HTTPException(status_code=404, detail=f"Target user #{payload.user_id} not found")

    notif = Notification(
        user_id=payload.user_id,
        title=payload.title,
        message=payload.message,
        notification_type=payload.notification_type or "SYSTEM",
        severity=payload.severity or "INFO",
        reference_id=payload.reference_id,
        is_read=False
    )
    db.add(notif)
    db.commit()
    db.refresh(notif)
    return notif


@router.get("/staff-exceptions", response_model=List[NotificationResponse])
def get_staff_exception_notifications(
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(require_permissions(Permission.NOTIFICATIONS_READ.value)),
    db: Session = Depends(get_db)
):
    """
    Retrieve inventory and order exception alerts for staff members.
    """
    exceptions = db.query(Notification).filter(
        Notification.notification_type.in_(["INVENTORY_EXCEPTION", "ORDER_EXCEPTION", "SYSTEM_ALERT"])
    ).order_by(Notification.created_at.desc()).limit(limit).all()
    return exceptions

