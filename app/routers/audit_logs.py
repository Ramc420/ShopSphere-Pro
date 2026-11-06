from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.models.audit_entry import AdminAuditLog
from app.schemas.audit_entry import AuditLogEntryCreate, AuditLogEntryResponse
from app.core.dependencies import get_current_user, require_permissions
from app.core.permissions import Permission

router = APIRouter(prefix="/audit-logs", tags=["Module 46: Audit Log Management"])


def utc_now():
    return datetime.now(timezone.utc)


@router.post("", response_model=AuditLogEntryResponse, status_code=status.HTTP_201_CREATED)
def record_audit_log(
    payload: AuditLogEntryCreate,
    request: Request,
    current_user: User = Depends(require_permissions(Permission.AUDIT_LOGS_WRITE.value)),
    db: Session = Depends(get_db)
):
    """
    Record sensitive administrative actions:
    Tracks product, pricing, inventory changes, order, and refund state transitions.
    """
    client_ip = request.client.host if request.client else "127.0.0.1"

    entry = AdminAuditLog(
        actor_id=current_user.id,
        action=payload.action.upper(),
        entity_type=payload.entity_type.upper(),
        entity_id=payload.entity_id,
        ip_address=client_ip,
        old_values=payload.old_values,
        new_values=payload.new_values,
        reason=payload.reason,
        is_immutable=True
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


@router.get("", response_model=List[AuditLogEntryResponse])
def query_audit_logs(
    entity_type: Optional[str] = Query(None, description="Filter by entity type (PRODUCT, PRICING, INVENTORY, ORDER, REFUND, USER)"),
    action: Optional[str] = Query(None, description="Filter by action name"),
    actor_id: Optional[int] = Query(None, description="Filter by actor user ID"),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(require_permissions(Permission.AUDIT_LOGS_READ.value)),
    db: Session = Depends(get_db)
):
    """
    Restrictively query immutable administrative audit logs.
    Restricted to Admins and Super Admins.
    """
    query = db.query(AdminAuditLog)
    if entity_type:
        query = query.filter(AdminAuditLog.entity_type == entity_type.upper())
    if action:
        query = query.filter(AdminAuditLog.action.ilike(f"%{action}%"))
    if actor_id:
        query = query.filter(AdminAuditLog.actor_id == actor_id)

    return query.order_by(AdminAuditLog.created_at.desc()).limit(limit).all()


@router.get("/{log_id}", response_model=AuditLogEntryResponse)
def get_audit_log_entry(
    log_id: int,
    current_user: User = Depends(require_permissions(Permission.AUDIT_LOGS_READ.value)),
    db: Session = Depends(get_db)
):
    """Retrieve a single audit log entry by ID."""
    entry = db.query(AdminAuditLog).filter(AdminAuditLog.id == log_id).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Audit log entry not found")
    return entry

