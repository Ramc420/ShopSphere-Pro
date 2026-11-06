from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from app.core.audit import log_user_activity
from app.core.dependencies import get_client_ip, get_current_user, require_roles
from app.core.permissions import UserRole
from app.database import get_db
from app.models.coupon import Coupon
from app.models.user import User
from app.schemas.common import MessageResponse
from app.schemas.coupon import (
    CouponCreate,
    CouponResponse,
    CouponUpdate,
    CouponValidateRequest,
    CouponValidateResponse,
)

router = APIRouter(prefix="/coupons", tags=["Module 20: Coupon Management"])


def to_naive_utc(dt):
    if dt is None:
        return None
    if dt.tzinfo is not None:
        return dt.astimezone(timezone.utc).replace(tzinfo=None)
    return dt


def utc_now():
    return datetime.now(timezone.utc).replace(tzinfo=None)


def serialize_coupon(c: Coupon) -> CouponResponse:
    now = utc_now()
    is_valid_now = c.is_active
    v_from = to_naive_utc(c.valid_from)
    v_until = to_naive_utc(c.valid_until)
    if v_from and now < v_from:
        is_valid_now = False
    if v_until and now > v_until:
        is_valid_now = False
    if c.usage_limit is not None and c.used_count >= c.usage_limit:
        is_valid_now = False

    return CouponResponse(
        id=c.id,
        code=c.code,
        description=c.description,
        discount_type=c.discount_type,
        discount_value=float(c.discount_value),
        min_purchase_amount=float(c.min_purchase_amount),
        max_discount_amount=float(c.max_discount_amount) if c.max_discount_amount else None,
        usage_limit=c.usage_limit,
        used_count=c.used_count,
        valid_from=c.valid_from,
        valid_until=c.valid_until,
        is_active=c.is_active,
        is_valid_now=is_valid_now,
        created_at=c.created_at,
        updated_at=c.updated_at
    )


@router.post("", response_model=CouponResponse, status_code=status.HTTP_201_CREATED)
def create_coupon(
    payload: CouponCreate,
    request: Request,
    current_user: User = Depends(require_roles(UserRole.SUPER_ADMIN.value, UserRole.ADMIN.value, UserRole.EMPLOYEE.value)),
    db: Session = Depends(get_db)
):
    """
    Create a new coupon code with discount types and validity rules.
    """
    code_clean = payload.code.strip().upper()
    existing = db.query(Coupon).filter(Coupon.code == code_clean).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Coupon code '{code_clean}' already exists.")

    coupon = Coupon(
        code=code_clean,
        description=payload.description.strip() if payload.description else None,
        discount_type=payload.discount_type.upper(),
        discount_value=payload.discount_value,
        min_purchase_amount=payload.min_purchase_amount,
        max_discount_amount=payload.max_discount_amount,
        usage_limit=payload.usage_limit,
        used_count=0,
        valid_from=payload.valid_from,
        valid_until=payload.valid_until,
        is_active=payload.is_active
    )
    db.add(coupon)
    db.commit()
    db.refresh(coupon)

    log_user_activity(
        db,
        action="COUPON_CREATED",
        user_id=current_user.id,
        ip_address=get_client_ip(request),
        user_agent=request.headers.get("user-agent"),
        details={"coupon_id": coupon.id, "code": coupon.code}
    )

    return serialize_coupon(coupon)


@router.get("", response_model=List[CouponResponse])
def get_coupons(
    is_active: Optional[bool] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List coupons. Staff can see all; customers see active coupons.
    """
    stmt = db.query(Coupon)
    if is_active is not None:
        stmt = stmt.filter(Coupon.is_active == is_active)
    elif current_user.role == UserRole.CUSTOMER.value:
        stmt = stmt.filter(Coupon.is_active == True)

    coupons = stmt.order_by(Coupon.id.desc()).all()
    return [serialize_coupon(c) for c in coupons]


@router.get("/{coupon_id}", response_model=CouponResponse)
def get_coupon_by_id(
    coupon_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Retrieve coupon details by ID.
    """
    coupon = db.query(Coupon).filter(Coupon.id == coupon_id).first()
    if not coupon:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Coupon not found")
    return serialize_coupon(coupon)


@router.put("/{coupon_id}", response_model=CouponResponse)
def update_coupon(
    coupon_id: int,
    payload: CouponUpdate,
    request: Request,
    current_user: User = Depends(require_roles(UserRole.SUPER_ADMIN.value, UserRole.ADMIN.value, UserRole.EMPLOYEE.value)),
    db: Session = Depends(get_db)
):
    """
    Update coupon rules, validity periods, and status.
    """
    coupon = db.query(Coupon).filter(Coupon.id == coupon_id).first()
    if not coupon:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Coupon not found")

    for field, val in payload.model_dump(exclude_unset=True).items():
        if val is not None:
            setattr(coupon, field, val)

    coupon.updated_at = utc_now()
    db.commit()
    db.refresh(coupon)

    log_user_activity(
        db,
        action="COUPON_UPDATED",
        user_id=current_user.id,
        ip_address=get_client_ip(request),
        user_agent=request.headers.get("user-agent"),
        details={"coupon_id": coupon.id, "code": coupon.code}
    )

    return serialize_coupon(coupon)


@router.post("/validate", response_model=CouponValidateResponse)
def validate_coupon_code(
    payload: CouponValidateRequest,
    db: Session = Depends(get_db)
):
    """
    Public validation endpoint to verify coupon code eligibility against a cart subtotal.
    """
    code_clean = payload.code.strip().upper()
    c = db.query(Coupon).filter(Coupon.code == code_clean).first()
    if not c or not c.is_active:
        return CouponValidateResponse(
            is_valid=False,
            code=code_clean,
            discount_type="NONE",
            discount_value=0.0,
            calculated_discount=0.0,
            message="Invalid or inactive coupon code."
        )

    now = utc_now()
    v_from = to_naive_utc(c.valid_from)
    v_until = to_naive_utc(c.valid_until)
    if v_from and now < v_from:
        return CouponValidateResponse(
            is_valid=False,
            code=code_clean,
            discount_type=c.discount_type,
            discount_value=float(c.discount_value),
            calculated_discount=0.0,
            message="Coupon is not yet active."
        )

    if v_until and now > v_until:
        return CouponValidateResponse(
            is_valid=False,
            code=code_clean,
            discount_type=c.discount_type,
            discount_value=float(c.discount_value),
            calculated_discount=0.0,
            message="Coupon has expired."
        )

    if c.usage_limit is not None and c.used_count >= c.usage_limit:
        return CouponValidateResponse(
            is_valid=False,
            code=code_clean,
            discount_type=c.discount_type,
            discount_value=float(c.discount_value),
            calculated_discount=0.0,
            message="Coupon usage limit has been reached."
        )

    if payload.cart_subtotal < float(c.min_purchase_amount):
        return CouponValidateResponse(
            is_valid=False,
            code=code_clean,
            discount_type=c.discount_type,
            discount_value=float(c.discount_value),
            calculated_discount=0.0,
            message=f"Minimum purchase amount of ${float(c.min_purchase_amount):.2f} required."
        )

    # Compute discount
    if c.discount_type == "PERCENTAGE":
        discount = round(payload.cart_subtotal * (float(c.discount_value) / 100.0), 2)
        if c.max_discount_amount and discount > float(c.max_discount_amount):
            discount = float(c.max_discount_amount)
    else:  # FIXED_AMOUNT
        discount = min(payload.cart_subtotal, float(c.discount_value))

    return CouponValidateResponse(
        is_valid=True,
        code=code_clean,
        discount_type=c.discount_type,
        discount_value=float(c.discount_value),
        calculated_discount=discount,
        message="Coupon applied successfully!"
    )
