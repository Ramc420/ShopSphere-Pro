from datetime import datetime, timezone
from decimal import Decimal
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from app.core.audit import log_user_activity
from app.core.dependencies import get_client_ip, get_current_user, require_permissions, require_roles
from app.core.permissions import Permission, UserRole
from app.database import get_db
from app.models.pricing import PriceHistory, ProductPrice
from app.models.product import Product
from app.models.user import User
from app.models.variant import ProductVariant
from app.schemas.common import MessageResponse
from app.schemas.pricing import PriceCreate, PriceHistoryResponse, PriceResponse, PriceUpdate

router = APIRouter(prefix="/pricing", tags=["Module 12: Product Pricing"])


def compute_effective_price(price: ProductPrice) -> tuple[Decimal, bool]:
    now = datetime.now(timezone.utc)
    if price.sale_price is not None and price.is_active:
        start = price.sale_start_date
        end = price.sale_end_date
        
        # Ensure timezone-aware comparison
        if start and start.tzinfo is None:
            start = start.replace(tzinfo=timezone.utc)
        if end and end.tzinfo is None:
            end = end.replace(tzinfo=timezone.utc)

        is_valid_start = (start is None) or (now >= start)
        is_valid_end = (end is None) or (now <= end)

        if is_valid_start and is_valid_end:
            return price.sale_price, True

    return price.base_price, False


def serialize_price(price: ProductPrice) -> PriceResponse:
    eff_price, on_sale = compute_effective_price(price)
    return PriceResponse(
        id=price.id,
        product_id=price.product_id,
        variant_id=price.variant_id,
        base_price=price.base_price,
        sale_price=price.sale_price,
        sale_start_date=price.sale_start_date,
        sale_end_date=price.sale_end_date,
        currency=price.currency,
        is_active=price.is_active,
        is_on_sale=on_sale,
        effective_price=eff_price,
        created_at=price.created_at,
        updated_at=price.updated_at
    )


@router.post("", response_model=PriceResponse, status_code=status.HTTP_201_CREATED)
def configure_price(
    payload: PriceCreate,
    request: Request,
    current_user: User = Depends(require_roles(UserRole.SUPER_ADMIN.value, UserRole.ADMIN.value)),
    db: Session = Depends(get_db)
):
    """
    Configure base price, promotional sale price, and price validity period.
    Requires ADMIN or SUPER_ADMIN role (authorized pricing permission).
    """
    product = db.query(Product).filter(Product.id == payload.product_id).first()
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Product {payload.product_id} not found")

    if payload.variant_id:
        variant = db.query(ProductVariant).filter(ProductVariant.id == payload.variant_id).first()
        if not variant:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Variant {payload.variant_id} not found")

    existing_price = db.query(ProductPrice).filter(
        ProductPrice.product_id == payload.product_id,
        ProductPrice.variant_id == payload.variant_id
    ).first()

    if existing_price:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Price configuration already exists for this item. Use PUT to update prices."
        )

    price_record = ProductPrice(
        product_id=payload.product_id,
        variant_id=payload.variant_id,
        base_price=payload.base_price,
        sale_price=payload.sale_price,
        sale_start_date=payload.sale_start_date,
        sale_end_date=payload.sale_end_date,
        currency=payload.currency.upper(),
        is_active=True
    )
    db.add(price_record)

    # Also sync base price back to Product or Variant
    if payload.variant_id:
        variant.price = payload.base_price
        variant.compare_at_price = payload.sale_price
    else:
        product.base_price = payload.base_price
        product.compare_at_price = payload.sale_price

    # Create initial price history
    history = PriceHistory(
        product_id=payload.product_id,
        variant_id=payload.variant_id,
        changed_by_user_id=current_user.id,
        old_base_price=None,
        new_base_price=payload.base_price,
        old_sale_price=None,
        new_sale_price=payload.sale_price,
        reason=payload.reason
    )
    db.add(history)
    db.commit()
    db.refresh(price_record)

    log_user_activity(
        db,
        action="PRICE_CONFIGURED",
        user_id=current_user.id,
        ip_address=get_client_ip(request),
        user_agent=request.headers.get("user-agent"),
        details={
            "product_id": payload.product_id,
            "base_price": str(payload.base_price),
            "sale_price": str(payload.sale_price) if payload.sale_price else None
        }
    )

    return serialize_price(price_record)


@router.get("/product/{product_id}", response_model=List[PriceResponse])
def get_product_pricing(
    product_id: int,
    db: Session = Depends(get_db)
):
    """
    Retrieve price records and current effective prices for a product and its variants.
    """
    prices = db.query(ProductPrice).filter(ProductPrice.product_id == product_id).all()
    return [serialize_price(p) for p in prices]


@router.put("/{price_id}", response_model=PriceResponse)
def update_price(
    price_id: int,
    payload: PriceUpdate,
    request: Request,
    current_user: User = Depends(require_roles(UserRole.SUPER_ADMIN.value, UserRole.ADMIN.value)),
    db: Session = Depends(get_db)
):
    """
    Update product prices, adjust validity periods, and log immutable price change history.
    """
    price_record = db.query(ProductPrice).filter(ProductPrice.id == price_id).first()
    if not price_record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Price record not found")

    old_base = price_record.base_price
    old_sale = price_record.sale_price

    new_base = payload.base_price if payload.base_price is not None else old_base
    new_sale = payload.sale_price if payload.sale_price is not None else old_sale

    if new_sale is not None and new_sale > new_base:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Sale price ({new_sale}) cannot exceed base price ({new_base})."
        )

    # Date validity check
    start_d = payload.sale_start_date if payload.sale_start_date is not None else price_record.sale_start_date
    end_d = payload.sale_end_date if payload.sale_end_date is not None else price_record.sale_end_date
    if start_d and end_d and end_d <= start_d:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="sale_end_date must be strictly after sale_start_date."
        )

    # Update values
    if payload.base_price is not None:
        price_record.base_price = payload.base_price
    if payload.sale_price is not None:
        price_record.sale_price = payload.sale_price
    if payload.sale_start_date is not None:
        price_record.sale_start_date = payload.sale_start_date
    if payload.sale_end_date is not None:
        price_record.sale_end_date = payload.sale_end_date
    if payload.is_active is not None:
        price_record.is_active = payload.is_active

    # Sync back to product
    product = db.query(Product).filter(Product.id == price_record.product_id).first()
    if product and not price_record.variant_id:
        product.base_price = price_record.base_price
        product.compare_at_price = price_record.sale_price

    # Record Price History
    history = PriceHistory(
        product_id=price_record.product_id,
        variant_id=price_record.variant_id,
        changed_by_user_id=current_user.id,
        old_base_price=old_base,
        new_base_price=price_record.base_price,
        old_sale_price=old_sale,
        new_sale_price=price_record.sale_price,
        reason=payload.reason
    )
    db.add(history)
    db.commit()
    db.refresh(price_record)

    log_user_activity(
        db,
        action="PRICE_UPDATED",
        user_id=current_user.id,
        ip_address=get_client_ip(request),
        user_agent=request.headers.get("user-agent"),
        details={"price_id": price_id, "reason": payload.reason}
    )

    return serialize_price(price_record)


@router.get("/history/{product_id}", response_model=List[PriceHistoryResponse])
def get_price_history(
    product_id: int,
    db: Session = Depends(get_db)
):
    """
    Retrieve immutable price change audit history for a product.
    """
    history = db.query(PriceHistory).filter(PriceHistory.product_id == product_id).order_by(PriceHistory.created_at.desc()).all()
    return history

