from math import ceil
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.core.audit import log_user_activity
from app.core.dependencies import (
    get_client_ip,
    get_current_user,
    require_permissions,
    require_roles,
)
from app.core.permissions import Permission, UserRole, UserStatus, get_role_permissions
from app.core.security import hash_password, validate_password_strength
from app.database import get_db
from app.models.audit_log import UserActivityLog
from app.models.customer_profile import CustomerProfile
from app.models.user import User
from app.schemas.common import MessageResponse, PaginationMeta, PaginatedResponse
from app.schemas.user import (
    UserActivityLogResponse,
    UserCreate,
    UserResponse,
    UserRoleAssign,
    UserStatusUpdate,
    UserUpdate,
)

router = APIRouter(prefix="/users", tags=["Module 2: User Management"])


def serialize_user(user: User) -> UserResponse:
    return UserResponse(
        id=user.id,
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
        phone=user.phone,
        role=user.role,
        status=user.status,
        is_verified=user.is_verified,
        registration_status=user.registration_status,
        department=user.department,
        permissions=get_role_permissions(user.role),
        created_at=user.created_at,
        updated_at=user.updated_at
    )


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(
    payload: UserCreate,
    request: Request,
    current_user: User = Depends(require_roles(UserRole.SUPER_ADMIN.value, UserRole.ADMIN.value)),
    db: Session = Depends(get_db)
):
    """
    Create a new user (customer, employee, or administrator) with assigned role and status.
    Requires ADMIN or SUPER_ADMIN role.
    """
    email_clean = payload.email.strip().lower()
    
    # Duplicate email check
    existing = db.query(User).filter(User.email == email_clean).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"User with email '{email_clean}' already exists."
        )

    # Phone uniqueness check
    if payload.phone:
        phone_existing = db.query(User).filter(User.phone == payload.phone.strip()).first()
        if phone_existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"User with phone '{payload.phone}' already exists."
            )

    if not validate_password_strength(payload.password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 8 characters long and contain uppercase, lowercase, numbers, and symbols."
        )

    role_val = payload.role.upper()
    if role_val not in [r.value for r in UserRole]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid role '{payload.role}'. Must be one of {[r.value for r in UserRole]}"
        )

    # Only SUPER_ADMIN can create another SUPER_ADMIN
    if role_val == UserRole.SUPER_ADMIN.value and current_user.role != UserRole.SUPER_ADMIN.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only Super Admins can create another Super Admin account."
        )

    new_user = User(
        email=email_clean,
        phone=payload.phone.strip() if payload.phone else None,
        hashed_password=hash_password(payload.password),
        first_name=payload.first_name.strip(),
        last_name=payload.last_name.strip(),
        role=role_val,
        status=UserStatus.ACTIVE.value,
        is_verified=payload.is_verified,
        registration_status="VERIFIED" if payload.is_verified else "PENDING_VERIFICATION",
        department=payload.department.strip() if payload.department else None
    )
    db.add(new_user)
    db.flush()

    # Automatically create profile for customers
    if role_val == UserRole.CUSTOMER.value:
        profile = CustomerProfile(user_id=new_user.id)
        db.add(profile)

    db.commit()
    db.refresh(new_user)

    log_user_activity(
        db,
        action="USER_CREATED",
        user_id=new_user.id,
        actor_id=current_user.id,
        ip_address=get_client_ip(request),
        user_agent=request.headers.get("user-agent"),
        details={"created_user_id": new_user.id, "email": new_user.email, "role": new_user.role}
    )

    return serialize_user(new_user)


@router.get("", response_model=PaginatedResponse[UserResponse])
def search_and_filter_users(
    query: Optional[str] = Query(None, description="Search by name, email, or phone"),
    role: Optional[str] = Query(None, description="Filter by role"),
    user_status: Optional[str] = Query(None, alias="status", description="Filter by account status"),
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    current_user: User = Depends(require_roles(UserRole.SUPER_ADMIN.value, UserRole.ADMIN.value, UserRole.EMPLOYEE.value)),
    db: Session = Depends(get_db)
):
    """
    Search and filter users across roles, statuses, and keywords with pagination.
    """
    stmt = db.query(User)

    if query:
        q_term = f"%{query.strip()}%"
        stmt = stmt.filter(
            or_(
                User.first_name.ilike(q_term),
                User.last_name.ilike(q_term),
                User.email.ilike(q_term),
                User.phone.ilike(q_term),
            )
        )

    if role:
        stmt = stmt.filter(User.role == role.upper())

    if user_status:
        stmt = stmt.filter(User.status == user_status.upper())

    total_items = stmt.count()
    users = stmt.order_by(User.id.desc()).offset((page - 1) * limit).limit(limit).all()
    total_pages = ceil(total_items / limit) if total_items > 0 else 1

    return PaginatedResponse(
        items=[serialize_user(u) for u in users],
        meta=PaginationMeta(
            total_items=total_items,
            page=page,
            limit=limit,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_prev=page > 1
        )
    )


@router.get("/{user_id}", response_model=UserResponse)
def get_user_by_id(
    user_id: int,
    current_user: User = Depends(require_roles(UserRole.SUPER_ADMIN.value, UserRole.ADMIN.value, UserRole.EMPLOYEE.value)),
    db: Session = Depends(get_db)
):
    """
    Retrieve user details by ID.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} was not found"
        )
    return serialize_user(user)


@router.put("/{user_id}", response_model=UserResponse)
def update_user(
    user_id: int,
    payload: UserUpdate,
    request: Request,
    current_user: User = Depends(require_roles(UserRole.SUPER_ADMIN.value, UserRole.ADMIN.value)),
    db: Session = Depends(get_db)
):
    """
    Update user information (names, contact phone, department).
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} was not found"
        )

    if payload.phone and payload.phone.strip() != user.phone:
        existing_phone = db.query(User).filter(User.phone == payload.phone.strip(), User.id != user.id).first()
        if existing_phone:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Phone number is already associated with another account."
            )
        user.phone = payload.phone.strip()

    if payload.first_name is not None:
        user.first_name = payload.first_name.strip()
    if payload.last_name is not None:
        user.last_name = payload.last_name.strip()
    if payload.department is not None:
        user.department = payload.department.strip()

    db.commit()
    db.refresh(user)

    log_user_activity(
        db,
        action="USER_UPDATED",
        user_id=user.id,
        actor_id=current_user.id,
        ip_address=get_client_ip(request),
        user_agent=request.headers.get("user-agent"),
        details={"updated_fields": payload.model_dump(exclude_unset=True)}
    )

    return serialize_user(user)


@router.patch("/{user_id}/status", response_model=UserResponse)
def update_user_status(
    user_id: int,
    payload: UserStatusUpdate,
    request: Request,
    current_user: User = Depends(require_roles(UserRole.SUPER_ADMIN.value, UserRole.ADMIN.value)),
    db: Session = Depends(get_db)
):
    """
    Manage user account status: ACTIVE, INACTIVE, SUSPENDED, DEACTIVATED.
    """
    status_upper = payload.status.upper()
    valid_statuses = [s.value for s in UserStatus]
    if status_upper not in valid_statuses:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid status '{payload.status}'. Allowed: {valid_statuses}"
        )

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} was not found"
        )

    # Protect SUPER_ADMIN from deactivation by non-superadmins
    if user.role == UserRole.SUPER_ADMIN.value and current_user.role != UserRole.SUPER_ADMIN.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot change status of a Super Administrator."
        )

    old_status = user.status
    user.status = status_upper
    db.commit()
    db.refresh(user)

    log_user_activity(
        db,
        action=f"STATUS_CHANGED_{status_upper}",
        user_id=user.id,
        actor_id=current_user.id,
        ip_address=get_client_ip(request),
        user_agent=request.headers.get("user-agent"),
        details={"old_status": old_status, "new_status": status_upper, "reason": payload.reason}
    )

    return serialize_user(user)


@router.patch("/{user_id}/role", response_model=UserResponse)
def assign_user_role(
    user_id: int,
    payload: UserRoleAssign,
    request: Request,
    current_user: User = Depends(require_roles(UserRole.SUPER_ADMIN.value, UserRole.ADMIN.value)),
    db: Session = Depends(get_db)
):
    """
    Assign role and permissions to a user.
    """
    role_upper = payload.role.upper()
    valid_roles = [r.value for r in UserRole]
    if role_upper not in valid_roles:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid role '{payload.role}'. Allowed: {valid_roles}"
        )

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} was not found"
        )

    if (role_upper == UserRole.SUPER_ADMIN.value or user.role == UserRole.SUPER_ADMIN.value) and current_user.role != UserRole.SUPER_ADMIN.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only a Super Admin can promote to or alter a Super Admin account."
        )

    old_role = user.role
    user.role = role_upper
    db.commit()
    db.refresh(user)

    log_user_activity(
        db,
        action="ROLE_ASSIGNED",
        user_id=user.id,
        actor_id=current_user.id,
        ip_address=get_client_ip(request),
        user_agent=request.headers.get("user-agent"),
        details={"old_role": old_role, "new_role": role_upper}
    )

    return serialize_user(user)


@router.get("/{user_id}/activity", response_model=PaginatedResponse[UserActivityLogResponse])
def get_user_activity(
    user_id: int,
    action: Optional[str] = Query(None, description="Filter by action name"),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Track user activity history. Customers can view their own activity; Staff/Admins can view any user's activity.
    """
    if current_user.role == UserRole.CUSTOMER.value and current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to another user's activity records."
        )

    stmt = db.query(UserActivityLog).filter(UserActivityLog.user_id == user_id)
    if action:
        stmt = stmt.filter(UserActivityLog.action.ilike(f"%{action}%"))

    total_items = stmt.count()
    logs = stmt.order_by(UserActivityLog.created_at.desc()).offset((page - 1) * limit).limit(limit).all()
    total_pages = ceil(total_items / limit) if total_items > 0 else 1

    return PaginatedResponse(
        items=[UserActivityLogResponse.model_validate(l) for l in logs],
        meta=PaginationMeta(
            total_items=total_items,
            page=page,
            limit=limit,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_prev=page > 1
        )
    )

