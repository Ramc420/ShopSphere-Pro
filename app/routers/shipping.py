from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from app.core.audit import log_user_activity
from app.core.dependencies import get_client_ip, get_current_user, require_roles
from app.core.permissions import UserRole
from app.database import get_db
from app.models.shipping import ShippingMethod, ShippingRule
from app.models.user import User
from app.schemas.shipping import (
    ShippingEstimateOption,
    ShippingEstimateRequest,
    ShippingEstimateResponse,
    ShippingMethodCreate,
    ShippingMethodResponse,
)

router = APIRouter(prefix="/shipping", tags=["Module 23: Shipping Configuration"])


def utc_now():
    return datetime.now(timezone.utc)


def serialize_shipping_method(m: ShippingMethod) -> ShippingMethodResponse:
    return ShippingMethodResponse(
        id=m.id,
        name=m.name,
        code=m.code,
        description=m.description,
        base_charge=float(m.base_charge),
        free_shipping_threshold=float(m.free_shipping_threshold) if m.free_shipping_threshold else None,
        estimated_days_min=m.estimated_days_min,
        estimated_days_max=m.estimated_days_max,
        is_active=m.is_active,
        created_at=m.created_at,
        updated_at=m.updated_at
    )


@router.post("/methods", response_model=ShippingMethodResponse, status_code=status.HTTP_201_CREATED)
def create_shipping_method(
    payload: ShippingMethodCreate,
    request: Request,
    current_user: User = Depends(require_roles(UserRole.SUPER_ADMIN.value, UserRole.ADMIN.value)),
    db: Session = Depends(get_db)
):
    """
    Define a new delivery shipping method and base pricing rules.
    """
    code_clean = payload.code.strip().upper()
    existing = db.query(ShippingMethod).filter(ShippingMethod.code == code_clean).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Shipping method code '{code_clean}' already exists.")

    method = ShippingMethod(
        name=payload.name.strip(),
        code=code_clean,
        description=payload.description.strip() if payload.description else None,
        base_charge=payload.base_charge,
        free_shipping_threshold=payload.free_shipping_threshold,
        estimated_days_min=payload.estimated_days_min,
        estimated_days_max=payload.estimated_days_max,
        is_active=payload.is_active
    )
    db.add(method)
    db.commit()
    db.refresh(method)

    log_user_activity(
        db,
        action="SHIPPING_METHOD_CREATED",
        user_id=current_user.id,
        ip_address=get_client_ip(request),
        user_agent=request.headers.get("user-agent"),
        details={"shipping_method_id": method.id, "code": method.code}
    )

    return serialize_shipping_method(method)


@router.get("/methods", response_model=List[ShippingMethodResponse])
def get_shipping_methods(
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db)
):
    """
    List shipping options available to customers.
    """
    stmt = db.query(ShippingMethod)
    if is_active is not None:
        stmt = stmt.filter(ShippingMethod.is_active == is_active)
    methods = stmt.order_by(ShippingMethod.base_charge.asc()).all()
    return [serialize_shipping_method(m) for m in methods]


@router.get("/methods/{method_id}", response_model=ShippingMethodResponse)
def get_shipping_method_by_id(
    method_id: int,
    db: Session = Depends(get_db)
):
    """
    Retrieve shipping method details.
    """
    m = db.query(ShippingMethod).filter(ShippingMethod.id == method_id).first()
    if not m:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Shipping method not found")
    return serialize_shipping_method(m)


@router.post("/estimate", response_model=ShippingEstimateResponse)
def estimate_shipping_rates(
    payload: ShippingEstimateRequest,
    db: Session = Depends(get_db)
):
    """
    Calculate dynamic delivery charges across all active shipping methods for an order subtotal.
    """
    methods = db.query(ShippingMethod).filter(ShippingMethod.is_active == True).all()
    options = []

    for m in methods:
        charge = float(m.base_charge)
        is_free = False
        if m.free_shipping_threshold and payload.subtotal >= float(m.free_shipping_threshold):
            charge = 0.0
            is_free = True

        options.append(
            ShippingEstimateOption(
                code=m.code,
                name=m.name,
                estimated_days=f"{m.estimated_days_min}-{m.estimated_days_max} business days",
                charge=charge,
                is_free=is_free
            )
        )

    return ShippingEstimateResponse(options=options)

