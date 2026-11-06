import json
from typing import Any, Optional
from sqlalchemy.orm import Session
from app.models.audit_log import UserActivityLog, ProfileChangeHistory


def log_user_activity(
    db: Session,
    action: str,
    user_id: Optional[int] = None,
    actor_id: Optional[int] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    details: Optional[Any] = None
) -> UserActivityLog:
    """Record an audit trail event for user activities."""
    details_str = None
    if details is not None:
        if isinstance(details, (dict, list)):
            details_str = json.dumps(details)
        else:
            details_str = str(details)
            
    log_entry = UserActivityLog(
        user_id=user_id,
        actor_id=actor_id or user_id,
        action=action,
        ip_address=ip_address,
        user_agent=user_agent,
        details=details_str
    )
    db.add(log_entry)
    db.commit()
    db.refresh(log_entry)
    return log_entry


def log_profile_change(
    db: Session,
    user_id: int,
    field_name: str,
    old_value: Any,
    new_value: Any,
    changed_by_user_id: Optional[int] = None
) -> Optional[ProfileChangeHistory]:
    """Log individual field changes for customer profiles."""
    old_str = str(old_value) if old_value is not None else ""
    new_str = str(new_value) if new_value is not None else ""
    
    if old_str == new_str:
        return None
        
    entry = ProfileChangeHistory(
        user_id=user_id,
        changed_by_user_id=changed_by_user_id or user_id,
        field_name=field_name,
        old_value=old_str,
        new_value=new_str
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry

