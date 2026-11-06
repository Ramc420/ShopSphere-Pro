import json
import re
from decimal import Decimal
from math import ceil
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_, asc, desc

from app.core.audit import log_user_activity
from app.core.dependencies import get_client_ip, get_current_user, require_roles
from app.core.permissions import UserRole
from app.database import get_db
from app.models.brand import Brand
from app.models.category import Category
from app.models.product import Product
from app.models.user import User
from app.schemas.brand import BrandResponse
from app.schemas.category import CategoryResponse
from app.schemas.common import MessageResponse, PaginationMeta, PaginatedResponse
from app.schemas.media import ProductMediaResponse
from app.schemas.product import (
    ProductCreate,
    ProductDetailResponse,
    ProductResponse,
    ProductUpdate,
)
from app.schemas.variant import VariantResponse

router = APIRouter(prefix="/products", tags=["Module 8: Product Management"])


def generate_slug(text: str) -> str:
    cleaned = re.sub(r"[^\w\s-]", "", text.lower()).strip()
    return re.sub(r"[-\s]+", "-", cleaned)


def serialize_variant(v) -> VariantResponse:
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


@router.post("", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
def create_product(
    payload: ProductCreate,
    request: Request,
    current_user: User = Depends(require_roles(UserRole.SUPER_ADMIN.value, UserRole.ADMIN.value, UserRole.EMPLOYEE.value)),
    db: Session = Depends(get_db)
):
    """
    Create a new product with names, descriptions, prices, SKU, and category/brand associations.
    """
    sku_clean = payload.base_sku.strip().upper()
    existing_sku = db.query(Product).filter(Product.base_sku == sku_clean).first()
    if existing_sku:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Product with base SKU '{sku_clean}' already exists."
        )

    # Validate category if provided
    if payload.category_id:
        cat = db.query(Category).filter(Category.id == payload.category_id).first()
        if not cat:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Category with ID {payload.category_id} not found")

    # Validate brand if provided
    if payload.brand_id:
        brand = db.query(Brand).filter(Brand.id == payload.brand_id).first()
        if not brand:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Brand with ID {payload.brand_id} not found")

    slug = payload.slug or generate_slug(payload.name)
    existing_slug = db.query(Product).filter(Product.slug == slug).first()
    if existing_slug:
        slug = f"{slug}-{sku_clean.lower()}"

    product = Product(
        name=payload.name.strip(),
        slug=slug,
        description=payload.description,
        short_description=payload.short_description,
        base_price=payload.base_price,
        cost_price=payload.cost_price,
        compare_at_price=payload.compare_at_price,
        base_sku=sku_clean,
        currency=payload.currency.upper(),
        category_id=payload.category_id,
        brand_id=payload.brand_id,
        status=payload.status.upper(),
        is_featured=payload.is_featured
    )
    db.add(product)
    db.commit()
    db.refresh(product)

    log_user_activity(
        db,
        action="PRODUCT_CREATED",
        user_id=current_user.id,
        ip_address=get_client_ip(request),
        user_agent=request.headers.get("user-agent"),
        details={"product_id": product.id, "name": product.name, "sku": product.base_sku}
    )

    return product


@router.get("", response_model=PaginatedResponse[ProductResponse])
def search_and_filter_products(
    query: Optional[str] = Query(None, description="Search by name, description, or SKU"),
    category_id: Optional[int] = Query(None, description="Filter by category ID"),
    brand_id: Optional[int] = Query(None, description="Filter by brand ID"),
    min_price: Optional[Decimal] = Query(None, ge=Decimal("0.00"), description="Minimum price filter"),
    max_price: Optional[Decimal] = Query(None, ge=Decimal("0.00"), description="Maximum price filter"),
    product_status: Optional[str] = Query(None, alias="status", description="Filter by status: ACTIVE, INACTIVE, DRAFT, ARCHIVED"),
    is_featured: Optional[bool] = Query(None, description="Filter featured products"),
    sort_by: str = Query("newest", description="'newest', 'price_asc', 'price_desc', 'name_asc'"),
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    Search and filter products across categories, brands, price range, and keywords with sorting and pagination.
    """
    stmt = db.query(Product)

    if query:
        term = f"%{query.strip()}%"
        stmt = stmt.filter(
            or_(
                Product.name.ilike(term),
                Product.description.ilike(term),
                Product.short_description.ilike(term),
                Product.base_sku.ilike(term),
            )
        )

    if category_id:
        stmt = stmt.filter(Product.category_id == category_id)

    if brand_id:
        stmt = stmt.filter(Product.brand_id == brand_id)

    if min_price is not None:
        stmt = stmt.filter(Product.base_price >= min_price)

    if max_price is not None:
        stmt = stmt.filter(Product.base_price <= max_price)

    if product_status:
        stmt = stmt.filter(Product.status == product_status.upper())

    if is_featured is not None:
        stmt = stmt.filter(Product.is_featured == is_featured)

    # Sorting
    if sort_by == "price_asc":
        stmt = stmt.order_by(asc(Product.base_price))
    elif sort_by == "price_desc":
        stmt = stmt.order_by(desc(Product.base_price))
    elif sort_by == "name_asc":
        stmt = stmt.order_by(asc(Product.name))
    else:  # newest
        stmt = stmt.order_by(desc(Product.id))

    total_items = stmt.count()
    products = stmt.offset((page - 1) * limit).limit(limit).all()
    total_pages = ceil(total_items / limit) if total_items > 0 else 1

    return PaginatedResponse(
        items=[ProductResponse.model_validate(p) for p in products],
        meta=PaginationMeta(
            total_items=total_items,
            page=page,
            limit=limit,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_prev=page > 1
        )
    )


@router.get("/{product_id}", response_model=ProductDetailResponse)
def get_product_details(
    product_id: int,
    db: Session = Depends(get_db)
):
    """
    Retrieve comprehensive product details including associated Category, Brand, Variants, and Media files.
    """
    product = (
        db.query(Product)
        .options(
            joinedload(Product.category),
            joinedload(Product.brand),
            joinedload(Product.variants),
            joinedload(Product.media),
        )
        .filter(Product.id == product_id)
        .first()
    )
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

    cat_resp = CategoryResponse.model_validate(product.category) if product.category else None
    brand_resp = BrandResponse.model_validate(product.brand) if product.brand else None
    variants_resp = [serialize_variant(v) for v in (product.variants or [])]
    media_resp = [ProductMediaResponse.model_validate(m) for m in (product.media or [])]

    return ProductDetailResponse(
        id=product.id,
        name=product.name,
        slug=product.slug,
        description=product.description,
        short_description=product.short_description,
        base_price=product.base_price,
        cost_price=product.cost_price,
        compare_at_price=product.compare_at_price,
        base_sku=product.base_sku,
        currency=product.currency,
        category_id=product.category_id,
        brand_id=product.brand_id,
        status=product.status,
        is_featured=product.is_featured,
        created_at=product.created_at,
        updated_at=product.updated_at,
        category=cat_resp,
        brand=brand_resp,
        variants=variants_resp,
        media=media_resp
    )


@router.put("/{product_id}", response_model=ProductResponse)
def update_product(
    product_id: int,
    payload: ProductUpdate,
    request: Request,
    current_user: User = Depends(require_roles(UserRole.SUPER_ADMIN.value, UserRole.ADMIN.value, UserRole.EMPLOYEE.value)),
    db: Session = Depends(get_db)
):
    """
    Update product details.
    """
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

    if payload.base_sku and payload.base_sku.strip().upper() != product.base_sku:
        sku_clean = payload.base_sku.strip().upper()
        existing = db.query(Product).filter(Product.base_sku == sku_clean, Product.id != product.id).first()
        if existing:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Product SKU already exists")
        product.base_sku = sku_clean

    if payload.category_id is not None:
        cat = db.query(Category).filter(Category.id == payload.category_id).first()
        if not cat:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
        product.category_id = payload.category_id

    if payload.brand_id is not None:
        brand = db.query(Brand).filter(Brand.id == payload.brand_id).first()
        if not brand:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Brand not found")
        product.brand_id = payload.brand_id

    for field, val in payload.model_dump(exclude_unset=True).items():
        if field not in ["base_sku", "category_id", "brand_id"] and val is not None:
            if isinstance(val, str):
                setattr(product, field, val.strip())
            else:
                setattr(product, field, val)

    db.commit()
    db.refresh(product)

    log_user_activity(
        db,
        action="PRODUCT_UPDATED",
        user_id=current_user.id,
        ip_address=get_client_ip(request),
        user_agent=request.headers.get("user-agent"),
        details={"product_id": product.id}
    )

    return product


@router.patch("/{product_id}/status", response_model=ProductResponse)
def manage_product_status(
    product_id: int,
    product_status: str = Query(..., alias="status", description="ACTIVE, INACTIVE, DRAFT, ARCHIVED"),
    request: Request = None,
    current_user: User = Depends(require_roles(UserRole.SUPER_ADMIN.value, UserRole.ADMIN.value, UserRole.EMPLOYEE.value)),
    db: Session = Depends(get_db)
):
    """
    Manage or deactivate a product.
    """
    status_upper = product_status.upper()
    valid_statuses = ["ACTIVE", "INACTIVE", "DRAFT", "ARCHIVED"]
    if status_upper not in valid_statuses:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Status must be one of {valid_statuses}")

    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

    product.status = status_upper
    db.commit()
    db.refresh(product)

    log_user_activity(
        db,
        action=f"PRODUCT_STATUS_{status_upper}",
        user_id=current_user.id,
        ip_address=get_client_ip(request) if request else None,
        user_agent=request.headers.get("user-agent") if request else None,
        details={"product_id": product.id, "status": status_upper}
    )

    return product


@router.delete("/{product_id}", response_model=MessageResponse)
def delete_product(
    product_id: int,
    request: Request,
    current_user: User = Depends(require_roles(UserRole.SUPER_ADMIN.value, UserRole.ADMIN.value)),
    db: Session = Depends(get_db)
):
    """
    Delete a product and cascade its variants and media files.
    """
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

    p_name = product.name
    db.delete(product)
    db.commit()

    log_user_activity(
        db,
        action="PRODUCT_DELETED",
        user_id=current_user.id,
        ip_address=get_client_ip(request),
        user_agent=request.headers.get("user-agent"),
        details={"product_id": product_id, "name": p_name}
    )

    return MessageResponse(success=True, message=f"Product '{p_name}' successfully deleted.")

