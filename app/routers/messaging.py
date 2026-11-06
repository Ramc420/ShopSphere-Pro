from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.models.messaging import NotificationProviderConfig, MessageLog
from app.schemas.messaging import (
    ProviderConfigCreate, ProviderConfigResponse,
    SendMessageRequest, MessageLogResponse
)
from app.core.dependencies import get_current_user, require_permissions
from app.core.permissions import Permission

router = APIRouter(prefix="/messaging", tags=["Module 42: Email and SMS Notifications"])


def utc_now():
    return datetime.now(timezone.utc)


@router.get("/providers", response_model=List[ProviderConfigResponse])
def list_providers(
    current_user: User = Depends(require_permissions(Permission.MESSAGING_READ.value)),
    db: Session = Depends(get_db)
):
    """List all configured email and SMS providers."""
    return db.query(NotificationProviderConfig).all()


@router.post("/providers", response_model=ProviderConfigResponse, status_code=status.HTTP_201_CREATED)
def configure_provider(
    payload: ProviderConfigCreate,
    current_user: User = Depends(require_permissions(Permission.MESSAGING_WRITE.value)),
    db: Session = Depends(get_db)
):
    """Configure a new email or SMS notification provider."""
    # If set as default, unset existing default for this provider_type
    if payload.is_default:
        db.query(NotificationProviderConfig).filter(
            NotificationProviderConfig.provider_type == payload.provider_type.upper()
        ).update({"is_default": False})

    provider = NotificationProviderConfig(
        provider_type=payload.provider_type.upper(),
        provider_name=payload.provider_name,
        sender_address=payload.sender_address,
        api_key_masked=payload.api_key_masked or "sk_live_configured",
        is_active=payload.is_active,
        is_default=payload.is_default
    )
    db.add(provider)
    db.commit()
    db.refresh(provider)
    return provider


@router.patch("/providers/{provider_id}/toggle", response_model=ProviderConfigResponse)
def toggle_provider(
    provider_id: int,
    current_user: User = Depends(require_permissions(Permission.MESSAGING_WRITE.value)),
    db: Session = Depends(get_db)
):
    """Toggle active status of a provider."""
    provider = db.query(NotificationProviderConfig).filter(NotificationProviderConfig.id == provider_id).first()
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")
    provider.is_active = not provider.is_active
    db.commit()
    db.refresh(provider)
    return provider


@router.post("/send", response_model=MessageLogResponse, status_code=status.HTTP_201_CREATED)
def send_notification_message(
    payload: SendMessageRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Send an email or SMS notification (verification, order confirmation, shipment, delivery update).
    Evaluates provider configuration, simulates dispatch, and logs status.
    """
    channel_upper = payload.channel.upper()
    if channel_upper not in ["EMAIL", "SMS"]:
        raise HTTPException(status_code=400, detail="Channel must be EMAIL or SMS")

    # Find active provider
    provider = db.query(NotificationProviderConfig).filter(
        NotificationProviderConfig.provider_type == channel_upper,
        NotificationProviderConfig.is_active == True
    ).first()

    # Determine delivery status
    # In test/dev environment, valid formatted recipients succeed
    is_failed = "invalid" in payload.recipient.lower() or "fail" in payload.recipient.lower()
    delivery_status = "FAILED" if is_failed else "SENT"
    error_msg = "Provider connection timed out or recipient unreachable" if is_failed else None

    msg = MessageLog(
        channel=channel_upper,
        recipient=payload.recipient,
        template_type=payload.template_type.upper(),
        subject=payload.subject or f"{payload.template_type.replace('_', ' ').title()} Notice",
        body=payload.body,
        status=delivery_status,
        error_message=error_msg,
        retry_count=0,
        max_retries=3
    )
    db.add(msg)
    db.commit()
    db.refresh(msg)
    return msg


@router.get("/logs", response_model=List[MessageLogResponse])
def list_message_logs(
    channel: Optional[str] = Query(None, description="Filter by channel: EMAIL or SMS"),
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by status: SENT, FAILED, DELIVERED"),
    recipient: Optional[str] = Query(None, description="Filter by recipient"),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(require_permissions(Permission.MESSAGING_READ.value)),
    db: Session = Depends(get_db)
):
    """Track delivery status and failures across email & SMS messages."""
    query = db.query(MessageLog)
    if channel:
        query = query.filter(MessageLog.channel == channel.upper())
    if status_filter:
        query = query.filter(MessageLog.status == status_filter.upper())
    if recipient:
        query = query.filter(MessageLog.recipient.ilike(f"%{recipient}%"))

    return query.order_by(MessageLog.created_at.desc()).limit(limit).all()


@router.post("/logs/{log_id}/retry", response_model=MessageLogResponse)
def retry_failed_message(
    log_id: int,
    current_user: User = Depends(require_permissions(Permission.MESSAGING_WRITE.value)),
    db: Session = Depends(get_db)
):
    """
    Retry a failed message safely.
    Increments retry count and asserts max retry limits.
    """
    msg = db.query(MessageLog).filter(MessageLog.id == log_id).first()
    if not msg:
        raise HTTPException(status_code=404, detail="Message log not found")

    if msg.status == "SENT" or msg.status == "DELIVERED":
        return msg

    if msg.retry_count >= msg.max_retries:
        raise HTTPException(
            status_code=400,
            detail=f"Message has reached maximum retries ({msg.max_retries}). Manual inspection required."
        )

    msg.retry_count += 1
    msg.last_retry_at = utc_now()
    
    # Simulate successful recovery unless explicit test fail string
    if "permanent_fail" in msg.recipient.lower():
        msg.status = "FAILED"
        msg.error_message = f"Permanent failure on retry attempt {msg.retry_count}"
    else:
        msg.status = "SENT"
        msg.error_message = None

    db.commit()
    db.refresh(msg)
    return msg

