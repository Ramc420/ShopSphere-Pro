from datetime import datetime, timezone
from math import ceil
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from app.core.audit import log_profile_change, log_user_activity
from app.core.dependencies import (
    get_client_ip,
    get_current_user,
    mask_sensitive_data,
    require_roles,
)
from app.core.permissions import UserRole, UserStatus
from app.database import get_db
from app.models.audit_log import ProfileChangeHistory
from app.models.customer_profile import CustomerProfile
from app.models.user import User
from app.schemas.common import MessageResponse, PaginationMeta, PaginatedResponse
from app.schemas.profile import (
    CustomerProfileResponse,
    CustomerProfileUpdate,
    DeactivationRequestCreate,
    DeactivationReviewRequest,
    ProfileChangeHistoryResponse,
)

router = APIRouter(prefix="/customer/profile", tags=["Module 4: Customer Profile Management"])


def build_profile_response(user: User, profile: CustomerProfile, mask_sensitive: bool = False) -> CustomerProfileResponse:
    phone_val = user.phone
    secondary_email_val = profile.secondary_email
    
    if mask_sensitive:
        phone_val = mask_sensitive_data(phone_val, kind="phone")
        secondary_email_val = mask_sensitive_data(secondary_email_val, kind="email")

    return CustomerProfileResponse(
        id=profile.id,
        user_id=user.id,
        first_name=user.first_name,
        last_name=user.last_name,
        email=user.email,
        phone=phone_val,
        secondary_email=secondary_email_val,
        date_of_birth=profile.date_of_birth,
        gender=profile.gender,
        avatar_url=profile.avatar_url,
        marketing_opt_in=profile.marketing_opt_in,
        notes=profile.notes,
        deactivation_requested=profile.deactivation_requested,
        deactivation_reason=profile.deactivation_reason,
        deactivation_status=profile.deactivation_status,
        created_at=profile.created_at,
        updated_at=profile.updated_at
    )


@router.get("/me", response_model=CustomerProfileResponse)
def get_my_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Retrieve currently authenticated customer profile.
    """
    profile = db.query(CustomerProfile).filter(CustomerProfile.user_id == current_user.id).first()
    if not profile:
        # Initialize if not existing
        profile = CustomerProfile(user_id=current_user.id)
        db.add(profile)
        db.commit()
        db.refresh(profile)

    return build_profile_response(current_user, profile, mask_sensitive=False)


@router.put("/me", response_model=CustomerProfileResponse)
def update_my_profile(
    payload: CustomerProfileUpdate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update personal and contact info for authenticated customer.
    Maintains complete profile change audit history (Module 4).
    """
    profile = db.query(CustomerProfile).filter(CustomerProfile.user_id == current_user.id).first()
    if not profile:
        profile = CustomerProfile(user_id=current_user.id)
        db.add(profile)
        db.flush()

    # Track changes for User model fields
    if payload.first_name is not None and payload.first_name.strip() != current_user.first_name:
        log_profile_change(db, current_user.id, "first_name", current_user.first_name, payload.first_name.strip(), current_user.id)
        current_user.first_name = payload.first_name.strip()

    if payload.last_name is not None and payload.last_name.strip() != current_user.last_name:
        log_profile_change(db, current_user.id, "last_name", current_user.last_name, payload.last_name.strip(), current_user.id)
        current_user.last_name = payload.last_name.strip()

    if payload.phone is not None and payload.phone.strip() != (current_user.phone or ""):
        # Check uniqueness
        existing_phone = db.query(User).filter(User.phone == payload.phone.strip(), User.id != current_user.id).first()
        if existing_phone:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Phone number is already associated with another account."
            )
        log_profile_change(db, current_user.id, "phone", current_user.phone, payload.phone.strip(), current_user.id)
        current_user.phone = payload.phone.strip()

    # Track changes for CustomerProfile fields
    if payload.secondary_email is not None and payload.secondary_email != profile.secondary_email:
        log_profile_change(db, current_user.id, "secondary_email", profile.secondary_email, payload.secondary_email, current_user.id)
        profile.secondary_email = payload.secondary_email

    if payload.date_of_birth is not None and payload.date_of_birth != profile.date_of_birth:
        log_profile_change(db, current_user.id, "date_of_birth", profile.date_of_birth, payload.date_of_birth, current_user.id)
        profile.date_of_birth = payload.date_of_birth

    if payload.gender is not None and payload.gender != profile.gender:
        log_profile_change(db, current_user.id, "gender", profile.gender, payload.gender, current_user.id)
        profile.gender = payload.gender

    if payload.avatar_url is not None and payload.avatar_url != profile.avatar_url:
        log_profile_change(db, current_user.id, "avatar_url", profile.avatar_url, payload.avatar_url, current_user.id)
        profile.avatar_url = payload.avatar_url

    if payload.marketing_opt_in is not None and payload.marketing_opt_in != profile.marketing_opt_in:
        log_profile_change(db, current_user.id, "marketing_opt_in", profile.marketing_opt_in, payload.marketing_opt_in, current_user.id)
        profile.marketing_opt_in = payload.marketing_opt_in

    if payload.notes is not None and payload.notes != profile.notes:
        log_profile_change(db, current_user.id, "notes", profile.notes, payload.notes, current_user.id)
        profile.notes = payload.notes

    db.commit()
    db.refresh(current_user)
    db.refresh(profile)

    log_user_activity(
        db,
        action="PROFILE_UPDATED",
        user_id=current_user.id,
        ip_address=get_client_ip(request),
        user_agent=request.headers.get("user-agent")
    )

    return build_profile_response(current_user, profile, mask_sensitive=False)


@router.post("/deactivation-request", response_model=MessageResponse)
def request_account_deactivation(
    payload: DeactivationRequestCreate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Customer submits an account deactivation request with reasoning.
    """
    profile = db.query(CustomerProfile).filter(CustomerProfile.user_id == current_user.id).first()
    if not profile:
        profile = CustomerProfile(user_id=current_user.id)
        db.add(profile)
        db.flush()

    if profile.deactivation_requested and profile.deactivation_status == "PENDING":
        return MessageResponse(
            success=True,
            message="You already have a pending deactivation request under review.",
            data={"status": "PENDING", "requested_at": profile.deactivation_requested_at}
        )

    profile.deactivation_requested = True
    profile.deactivation_reason = payload.reason
    profile.deactivation_requested_at = datetime.now(timezone.utc)
    profile.deactivation_status = "PENDING"
    db.commit()

    log_user_activity(
        db,
        action="DEACTIVATION_REQUESTED",
        user_id=current_user.id,
        ip_address=get_client_ip(request),
        user_agent=request.headers.get("user-agent"),
        details={"reason": payload.reason}
    )

    return MessageResponse(
        success=True,
        message="Account deactivation request submitted successfully. An administrator will review your request.",
        data={"status": "PENDING"}
    )


@router.get("/history", response_model=PaginatedResponse[ProfileChangeHistoryResponse])
def get_profile_change_history(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Retrieve the immutable change history for the authenticated customer's profile.
    """
    stmt = db.query(ProfileChangeHistory).filter(ProfileChangeHistory.user_id == current_user.id)
    total_items = stmt.count()
    records = stmt.order_by(ProfileChangeHistory.changed_at.desc()).offset((page - 1) * limit).limit(limit).all()
    total_pages = ceil(total_items / limit) if total_items > 0 else 1

    return PaginatedResponse(
        items=[ProfileChangeHistoryResponse.model_validate(r) for r in records],
        meta=PaginationMeta(
            total_items=total_items,
            page=page,
            limit=limit,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_prev=page > 1
        )
    )


@router.get("/{user_id}", response_model=CustomerProfileResponse)
def get_customer_profile_by_id(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Admin or staff inspects customer profile.
    Enforces privacy access restriction (Module 4):
    - Customers cannot inspect other users' profiles.
    - Staff without full admin rights will have sensitive contact info masked.
    """
    if current_user.role == UserRole.CUSTOMER.value and current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access restricted: You cannot view another customer's personal profile."
        )

    target_user = db.query(User).filter(User.id == user_id).first()
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} was not found"
        )

    profile = db.query(CustomerProfile).filter(CustomerProfile.user_id == user_id).first()
    if not profile:
        profile = CustomerProfile(user_id=user_id)
        db.add(profile)
        db.commit()
        db.refresh(profile)

    # Restrict personal information if accessed by standard employee
    should_mask = (current_user.role == UserRole.EMPLOYEE.value)

    return build_profile_response(target_user, profile, mask_sensitive=should_mask)


@router.post("/{user_id}/deactivation-review", response_model=MessageResponse)
def review_deactivation_request(
    user_id: int,
    payload: DeactivationReviewRequest,
    request: Request,
    current_user: User = Depends(require_roles(UserRole.SUPER_ADMIN.value, UserRole.ADMIN.value)),
    db: Session = Depends(get_db)
):
    """
    Admin reviews and resolves an account deactivation request.
    If APPROVED: changes user status to DEACTIVATED.
    """
    target_user = db.query(User).filter(User.id == user_id).first()
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} was not found"
        )

    profile = db.query(CustomerProfile).filter(CustomerProfile.user_id == user_id).first()
    if not profile or not profile.deactivation_requested:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No pending deactivation request found for this user."
        )

    decision_upper = payload.decision.upper()
    if decision_upper not in ["APPROVED", "REJECTED"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Decision must be either 'APPROVED' or 'REJECTED'."
        )

    profile.deactivation_status = decision_upper
    if decision_upper == "APPROVED":
        target_user.status = UserStatus.DEACTIVATED.value
        profile.deactivation_requested = False
    else:
        profile.deactivation_requested = False

    db.commit()

    log_user_activity(
        db,
        action=f"DEACTIVATION_REVIEW_{decision_upper}",
        user_id=target_user.id,
        actor_id=current_user.id,
        ip_address=get_client_ip(request),
        user_agent=request.headers.get("user-agent"),
        details={"decision": decision_upper, "admin_notes": payload.admin_notes}
    )

    return MessageResponse(
        success=True,
        message=f"Deactivation request {decision_upper.lower()}.",
        data={"user_id": target_user.id, "account_status": target_user.status, "decision": decision_upper}
    )

