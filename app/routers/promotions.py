from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from app.core.audit import log_user_activity
from app.core.dependencies import get_client_ip, get_current_user, require_roles
from app.core.permissions import UserRole
from app.database import get_db
from app.models.category import Category
from app.models.product import Product
from app.models.promotion import Promotion, PromotionHistory
from app.models.user import User
from app.schemas.promotion import (
    PromotionCreate,
    PromotionHistoryResponse,
    PromotionResponse,
)

router = APIRouter(prefix="/promotions", tags=["Module 21: Promotion Management"])


def to_naive_utc(dt):
    if dt is None:
        return None
    if dt.tzinfo is not None:
        return dt.astimezone(timezone.utc).replace(tzinfo=None)
    return dt


def utc_now():
    return datetime.now(timezone.utc).replace(tzinfo=None)


def serialize_promotion(p: Promotion) -> PromotionResponse:
    now = utc_now()
    start = to_naive_utc(p.start_date)
    end = to_naive_utc(p.end_date)
    is_curr = p.is_active
    if start and now < start:
        is_curr = False
    if end and now > end:
        is_curr = False

    return PromotionResponse(
        id=p.id,
        name=p.name,
        code=p.code,
        description=p.description,
        promotion_type=p.promotion_type,
        discount_value=float(p.discount_value),
        min_order_amount=float(p.min_order_amount),
        target_category_id=p.target_category_id,
        target_product_id=p.target_product_id,
        start_date=p.start_date,
        end_date=p.end_date,
        is_active=p.is_active,
        is_currently_active=is_curr,
        created_at=p.created_at,
        updated_at=p.updated_at
    )


@router.post("", response_model=PromotionResponse, status_code=status.HTTP_201_CREATED)
def create_promotion(
    payload: PromotionCreate,
    request: Request,
    current_user: User = Depends(require_roles(UserRole.SUPER_ADMIN.value, UserRole.ADMIN.value, UserRole.EMPLOYEE.value)),
    db: Session = Depends(get_db)
):
    """
    Configure a new product or category-level promotion.
    """
    code_clean = payload.code.strip().upper()
    existing = db.query(Promotion).filter(Promotion.code == code_clean).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Promotion code '{code_clean}' already exists.")

    if payload.target_category_id:
        c = db.query(Category).filter(Category.id == payload.target_category_id).first()
        if not c:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Target category not found")

    if payload.target_product_id:
        pr = db.query(Product).filter(Product.id == payload.target_product_id).first()
        if not pr:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Target product not found")

    promo = Promotion(
        name=payload.name.strip(),
        code=code_clean,
        description=payload.description.strip() if payload.description else None,
        promotion_type=payload.promotion_type.upper(),
        discount_value=payload.discount_value,
        min_order_amount=payload.min_order_amount,
        target_category_id=payload.target_category_id,
        target_product_id=payload.target_product_id,
        start_date=to_naive_utc(payload.start_date),
        end_date=to_naive_utc(payload.end_date),
        is_active=payload.is_active
    )
    db.add(promo)
    db.commit()
    db.refresh(promo)

    log_user_activity(
        db,
        action="PROMOTION_CREATED",
        user_id=current_user.id,
        ip_address=get_client_ip(request),
        user_agent=request.headers.get("user-agent"),
        details={"promotion_id": promo.id, "code": promo.code}
    )

    return serialize_promotion(promo)


@router.get("", response_model=List[PromotionResponse])
def get_promotions(
    is_active: Optional[bool] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List all configured promotions.
    """
    stmt = db.query(Promotion)
    if is_active is not None:
        stmt = stmt.filter(Promotion.is_active == is_active)
    elif current_user.role == UserRole.CUSTOMER.value:
        stmt = stmt.filter(Promotion.is_active == True)

    promos = stmt.order_by(Promotion.id.desc()).all()
    return [serialize_promotion(p) for p in promos]


@router.get("/{promotion_id}", response_model=PromotionResponse)
def get_promotion_by_id(
    promotion_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Retrieve promotion details by ID.
    """
    p = db.query(Promotion).filter(Promotion.id == promotion_id).first()
    if not p:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Promotion not found")
    return serialize_promotion(p)


@router.get("/history/all", response_model=List[PromotionHistoryResponse])
def get_promotion_history(
    promotion_id: Optional[int] = None,
    current_user: User = Depends(require_roles(UserRole.SUPER_ADMIN.value, UserRole.ADMIN.value, UserRole.EMPLOYEE.value)),
    db: Session = Depends(get_db)
):
    """
    Retrieve immutable audit ledger of promotional discounts applied during checkout.
    """
    stmt = db.query(PromotionHistory)
    if promotion_id:
        stmt = stmt.filter(PromotionHistory.promotion_id == promotion_id)
    return stmt.order_by(PromotionHistory.applied_at.desc()).limit(100).all()
