import json
from decimal import Decimal
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from app.core.audit import log_user_activity
from app.core.dependencies import get_client_ip, get_current_user, require_roles
from app.core.permissions import UserRole
from app.database import get_db
from app.models.product import Product
from app.models.user import User
from app.models.variant import ProductVariant
from app.schemas.common import MessageResponse
from app.schemas.variant import (
    VariantCreate,
    VariantResponse,
    VariantStockAdjust,
    VariantUpdate,
)

router = APIRouter(tags=["Module 9: Product Variants"])


def calculate_availability(stock: int, threshold: int) -> str:
    if stock <= 0:
        return "OUT_OF_STOCK"
    elif stock <= threshold:
        return "LOW_STOCK"
    return "IN_STOCK"


def serialize_variant(v: ProductVariant) -> VariantResponse:
    attrs = None
    if v.attributes_json:
        try:
            attrs = json.loads(v.attributes_json)
        except Exception:
            attrs = {}
    return VariantResponse(
        id=v.id,
        product_id=v.product_id,
        sku=v.sku,
        title=v.title,
        price=v.price,
        compare_at_price=v.compare_at_price,
        cost_price=v.cost_price,
        attributes=attrs,
        stock_quantity=v.stock_quantity,
        reserved_quantity=v.reserved_quantity,
        low_stock_threshold=v.low_stock_threshold,
        availability_status=v.availability_status,
        status=v.status,
        created_at=v.created_at,
        updated_at=v.updated_at
    )


@router.post("/products/{product_id}/variants", response_model=VariantResponse, status_code=status.HTTP_201_CREATED)
def create_product_variant(
    product_id: int,
    payload: VariantCreate,
    request: Request,
    current_user: User = Depends(require_roles(UserRole.SUPER_ADMIN.value, UserRole.ADMIN.value, UserRole.EMPLOYEE.value)),
    db: Session = Depends(get_db)
):
    """
    Create a variant for a product with variations (size, color, etc.), unique SKU, and pricing.
    """
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Product with ID {product_id} not found")

    sku_clean = payload.sku.strip().upper()
    existing_sku = db.query(ProductVariant).filter(ProductVariant.sku == sku_clean).first()
    if existing_sku:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Variant SKU '{sku_clean}' is already in use.")

    # Calculate initial availability status
    avail_status = calculate_availability(payload.stock_quantity, payload.low_stock_threshold)

    attributes_json = json.dumps(payload.attributes) if payload.attributes else None

    variant = ProductVariant(
        product_id=product_id,
        sku=sku_clean,
        title=payload.title.strip(),
        price=payload.price,
        compare_at_price=payload.compare_at_price,
        cost_price=payload.cost_price,
        attributes_json=attributes_json,
        stock_quantity=payload.stock_quantity,
        low_stock_threshold=payload.low_stock_threshold,
        availability_status=avail_status,
        status=payload.status.upper()
    )
    db.add(variant)
    db.commit()
    db.refresh(variant)

    log_user_activity(
        db,
        action="VARIANT_CREATED",
        user_id=current_user.id,
        ip_address=get_client_ip(request),
        user_agent=request.headers.get("user-agent"),
        details={"product_id": product_id, "variant_id": variant.id, "sku": variant.sku}
    )

    return serialize_variant(variant)


@router.get("/products/{product_id}/variants", response_model=List[VariantResponse])
def get_product_variants(
    product_id: int,
    status: Optional[str] = Query(None, description="Filter by status: ACTIVE, INACTIVE, DISCONTINUED"),
    db: Session = Depends(get_db)
):
    """
    Retrieve all variants for a given product.
    """
    stmt = db.query(ProductVariant).filter(ProductVariant.product_id == product_id)
    if status:
        stmt = stmt.filter(ProductVariant.status == status.upper())
    variants = stmt.order_by(ProductVariant.id.asc()).all()
    return [serialize_variant(v) for v in variants]


@router.get("/variants/{variant_id}", response_model=VariantResponse)
def get_variant_by_id(
    variant_id: int,
    db: Session = Depends(get_db)
):
    """
    Retrieve specific variant details.
    """
    variant = db.query(ProductVariant).filter(ProductVariant.id == variant_id).first()
    if not variant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Variant not found")
    return serialize_variant(variant)


@router.put("/variants/{variant_id}", response_model=VariantResponse)
def update_variant(
    variant_id: int,
    payload: VariantUpdate,
    request: Request,
    current_user: User = Depends(require_roles(UserRole.SUPER_ADMIN.value, UserRole.ADMIN.value, UserRole.EMPLOYEE.value)),
    db: Session = Depends(get_db)
):
    """
    Update variant attributes, prices, SKU, and threshold.
    """
    variant = db.query(ProductVariant).filter(ProductVariant.id == variant_id).first()
    if not variant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Variant not found")

    if payload.sku and payload.sku.strip().upper() != variant.sku:
        sku_clean = payload.sku.strip().upper()
        existing = db.query(ProductVariant).filter(ProductVariant.sku == sku_clean, ProductVariant.id != variant.id).first()
        if existing:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Variant SKU is already taken")
        variant.sku = sku_clean

    if payload.attributes is not None:
        variant.attributes_json = json.dumps(payload.attributes)

    if payload.stock_quantity is not None:
        variant.stock_quantity = payload.stock_quantity
        
    if payload.low_stock_threshold is not None:
        variant.low_stock_threshold = payload.low_stock_threshold

    # Recalculate availability
    variant.availability_status = calculate_availability(variant.stock_quantity, variant.low_stock_threshold)

    for field, val in payload.model_dump(exclude_unset=True).items():
        if field not in ["sku", "attributes", "stock_quantity", "low_stock_threshold"] and val is not None:
            if isinstance(val, str):
                setattr(variant, field, val.strip())
            else:
                setattr(variant, field, val)

    db.commit()
    db.refresh(variant)

    log_user_activity(
        db,
        action="VARIANT_UPDATED",
        user_id=current_user.id,
        ip_address=get_client_ip(request),
        user_agent=request.headers.get("user-agent"),
        details={"variant_id": variant.id}
    )

    return serialize_variant(variant)


@router.post("/variants/{variant_id}/stock-adjust", response_model=VariantResponse)
def adjust_variant_stock(
    variant_id: int,
    payload: VariantStockAdjust,
    request: Request,
    current_user: User = Depends(require_roles(UserRole.SUPER_ADMIN.value, UserRole.ADMIN.value, UserRole.EMPLOYEE.value)),
    db: Session = Depends(get_db)
):
    """
    Adjust variant inventory stock levels (Module 9).
    Automatically updates availability status: IN_STOCK, LOW_STOCK, OUT_OF_STOCK.
    """
    variant = db.query(ProductVariant).filter(ProductVariant.id == variant_id).first()
    if not variant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Variant not found")

    old_stock = variant.stock_quantity
    new_stock = old_stock + payload.adjustment
    if new_stock < 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Adjustment of {payload.adjustment} would cause negative stock. Current stock: {old_stock}"
        )

    variant.stock_quantity = new_stock
    variant.availability_status = calculate_availability(new_stock, variant.low_stock_threshold)
    db.commit()
    db.refresh(variant)

    log_user_activity(
        db,
        action="STOCK_ADJUSTED",
        user_id=current_user.id,
        ip_address=get_client_ip(request),
        user_agent=request.headers.get("user-agent"),
        details={
            "variant_id": variant.id,
            "old_stock": old_stock,
            "adjustment": payload.adjustment,
            "new_stock": new_stock,
            "reason": payload.reason,
            "availability_status": variant.availability_status
        }
    )

    return serialize_variant(variant)


@router.patch("/variants/{variant_id}/status", response_model=VariantResponse)
def update_variant_status(
    variant_id: int,
    variant_status: str = Query(..., alias="status", description="ACTIVE, INACTIVE, DISCONTINUED"),
    request: Request = None,
    current_user: User = Depends(require_roles(UserRole.SUPER_ADMIN.value, UserRole.ADMIN.value, UserRole.EMPLOYEE.value)),
    db: Session = Depends(get_db)
):
    """
    Maintain variant status: ACTIVE, INACTIVE, DISCONTINUED.
    """
    status_upper = variant_status.upper()
    valid_statuses = ["ACTIVE", "INACTIVE", "DISCONTINUED"]
    if status_upper not in valid_statuses:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Status must be one of {valid_statuses}")

    variant = db.query(ProductVariant).filter(ProductVariant.id == variant_id).first()
    if not variant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Variant not found")

    variant.status = status_upper
    db.commit()
    db.refresh(variant)

    log_user_activity(
        db,
        action=f"VARIANT_STATUS_{status_upper}",
        user_id=current_user.id,
        ip_address=get_client_ip(request) if request else None,
        user_agent=request.headers.get("user-agent") if request else None,
        details={"variant_id": variant.id, "status": status_upper}
    )

    return serialize_variant(variant)


@router.delete("/variants/{variant_id}", response_model=MessageResponse)
def delete_variant(
    variant_id: int,
    request: Request,
    current_user: User = Depends(require_roles(UserRole.SUPER_ADMIN.value, UserRole.ADMIN.value)),
    db: Session = Depends(get_db)
):
    """
    Delete a variant.
    """
    variant = db.query(ProductVariant).filter(ProductVariant.id == variant_id).first()
    if not variant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Variant not found")

    v_sku = variant.sku
    db.delete(variant)
    db.commit()

    log_user_activity(
        db,
        action="VARIANT_DELETED",
        user_id=current_user.id,
        ip_address=get_client_ip(request),
        user_agent=request.headers.get("user-agent"),
        details={"variant_id": variant_id, "sku": v_sku}
    )

    return MessageResponse(success=True, message=f"Variant '{v_sku}' deleted successfully.")

