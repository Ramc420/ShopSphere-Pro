import re
from math import ceil
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session
from sqlalchemy import or_, func

from app.core.audit import log_user_activity
from app.core.dependencies import get_client_ip, get_current_user, require_roles
from app.core.permissions import UserRole
from app.database import get_db
from app.models.brand import Brand
from app.models.product import Product
from app.models.user import User
from app.schemas.brand import BrandCreate, BrandResponse, BrandUpdate
from app.schemas.common import MessageResponse, PaginationMeta, PaginatedResponse
from app.schemas.product import ProductResponse

router = APIRouter(prefix="/brands", tags=["Module 7: Brand Management"])


def generate_code(name: str) -> str:
    cleaned = re.sub(r"[^\w\s-]", "", name.upper()).strip()
    return re.sub(r"[-\s]+", "_", cleaned)


@router.post("", response_model=BrandResponse, status_code=status.HTTP_201_CREATED)
def register_brand(
    payload: BrandCreate,
    request: Request,
    current_user: User = Depends(require_roles(UserRole.SUPER_ADMIN.value, UserRole.ADMIN.value, UserRole.EMPLOYEE.value)),
    db: Session = Depends(get_db)
):
    """
    Register a new product brand.
    """
    brand_code = payload.code or generate_code(payload.name)
    existing = db.query(Brand).filter(Brand.code == brand_code).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Brand with code '{brand_code}' already exists."
        )

    brand = Brand(
        name=payload.name.strip(),
        code=brand_code,
        description=payload.description,
        website_url=payload.website_url,
        logo_url=payload.logo_url,
        status=payload.status.upper()
    )
    db.add(brand)
    db.commit()
    db.refresh(brand)

    log_user_activity(
        db,
        action="BRAND_REGISTERED",
        user_id=current_user.id,
        ip_address=get_client_ip(request),
        user_agent=request.headers.get("user-agent"),
        details={"brand_id": brand.id, "name": brand.name, "code": brand.code}
    )

    return BrandResponse(
        id=brand.id,
        name=brand.name,
        code=brand.code,
        description=brand.description,
        website_url=brand.website_url,
        logo_url=brand.logo_url,
        status=brand.status,
        products_count=0,
        created_at=brand.created_at,
        updated_at=brand.updated_at
    )


@router.get("", response_model=PaginatedResponse[BrandResponse])
def search_and_list_brands(
    query: Optional[str] = Query(None, description="Search by brand name or code"),
    status: Optional[str] = Query(None, description="Filter by status: ACTIVE or INACTIVE"),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    Search and filter brands with pagination and associated product counts.
    """
    stmt = db.query(Brand)
    if query:
        q_term = f"%{query.strip()}%"
        stmt = stmt.filter(or_(Brand.name.ilike(q_term), Brand.code.ilike(q_term)))
    if status:
        stmt = stmt.filter(Brand.status == status.upper())

    total_items = stmt.count()
    brands = stmt.order_by(Brand.name.asc()).offset((page - 1) * limit).limit(limit).all()
    total_pages = ceil(total_items / limit) if total_items > 0 else 1

    # Fetch product counts
    items = []
    for b in brands:
        p_count = db.query(func.count(Product.id)).filter(Product.brand_id == b.id).scalar() or 0
        items.append(
            BrandResponse(
                id=b.id,
                name=b.name,
                code=b.code,
                description=b.description,
                website_url=b.website_url,
                logo_url=b.logo_url,
                status=b.status,
                products_count=p_count,
                created_at=b.created_at,
                updated_at=b.updated_at
            )
        )

    return PaginatedResponse(
        items=items,
        meta=PaginationMeta(
            total_items=total_items,
            page=page,
            limit=limit,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_prev=page > 1
        )
    )


@router.get("/{brand_id}", response_model=BrandResponse)
def get_brand_by_id(
    brand_id: int,
    db: Session = Depends(get_db)
):
    """
    Retrieve specific brand details.
    """
    brand = db.query(Brand).filter(Brand.id == brand_id).first()
    if not brand:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Brand not found")

    p_count = db.query(func.count(Product.id)).filter(Product.brand_id == brand.id).scalar() or 0
    return BrandResponse(
        id=brand.id,
        name=brand.name,
        code=brand.code,
        description=brand.description,
        website_url=brand.website_url,
        logo_url=brand.logo_url,
        status=brand.status,
        products_count=p_count,
        created_at=brand.created_at,
        updated_at=brand.updated_at
    )


@router.put("/{brand_id}", response_model=BrandResponse)
def update_brand(
    brand_id: int,
    payload: BrandUpdate,
    request: Request,
    current_user: User = Depends(require_roles(UserRole.SUPER_ADMIN.value, UserRole.ADMIN.value, UserRole.EMPLOYEE.value)),
    db: Session = Depends(get_db)
):
    """
    Update brand details.
    """
    brand = db.query(Brand).filter(Brand.id == brand_id).first()
    if not brand:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Brand not found")

    if payload.code and payload.code.strip() != brand.code:
        existing = db.query(Brand).filter(Brand.code == payload.code.strip(), Brand.id != brand.id).first()
        if existing:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Brand code already exists")
        brand.code = payload.code.strip()

    for field, val in payload.model_dump(exclude_unset=True).items():
        if field != "code" and val is not None:
            if isinstance(val, str):
                setattr(brand, field, val.strip())
            else:
                setattr(brand, field, val)

    db.commit()
    db.refresh(brand)

    log_user_activity(
        db,
        action="BRAND_UPDATED",
        user_id=current_user.id,
        ip_address=get_client_ip(request),
        user_agent=request.headers.get("user-agent"),
        details={"brand_id": brand.id}
    )

    p_count = db.query(func.count(Product.id)).filter(Product.brand_id == brand.id).scalar() or 0
    return BrandResponse(
        id=brand.id,
        name=brand.name,
        code=brand.code,
        description=brand.description,
        website_url=brand.website_url,
        logo_url=brand.logo_url,
        status=brand.status,
        products_count=p_count,
        created_at=brand.created_at,
        updated_at=brand.updated_at
    )


@router.patch("/{brand_id}/status", response_model=BrandResponse)
def manage_brand_status(
    brand_id: int,
    brand_status: str = Query(..., alias="status", description="ACTIVE or INACTIVE"),
    request: Request = None,
    current_user: User = Depends(require_roles(UserRole.SUPER_ADMIN.value, UserRole.ADMIN.value, UserRole.EMPLOYEE.value)),
    db: Session = Depends(get_db)
):
    """
    Manage brand status: ACTIVE or INACTIVE.
    """
    status_upper = brand_status.upper()
    if status_upper not in ["ACTIVE", "INACTIVE"]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Status must be ACTIVE or INACTIVE")

    brand = db.query(Brand).filter(Brand.id == brand_id).first()
    if not brand:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Brand not found")

    brand.status = status_upper
    db.commit()
    db.refresh(brand)

    log_user_activity(
        db,
        action=f"BRAND_STATUS_CHANGED_{status_upper}",
        user_id=current_user.id,
        ip_address=get_client_ip(request) if request else None,
        user_agent=request.headers.get("user-agent") if request else None,
        details={"brand_id": brand.id, "status": status_upper}
    )

    p_count = db.query(func.count(Product.id)).filter(Product.brand_id == brand.id).scalar() or 0
    return BrandResponse(
        id=brand.id,
        name=brand.name,
        code=brand.code,
        description=brand.description,
        website_url=brand.website_url,
        logo_url=brand.logo_url,
        status=brand.status,
        products_count=p_count,
        created_at=brand.created_at,
        updated_at=brand.updated_at
    )


@router.get("/{brand_id}/products", response_model=PaginatedResponse[ProductResponse])
def get_products_by_brand(
    brand_id: int,
    category_id: Optional[int] = Query(None, description="Filter products by category ID"),
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    Retrieve products associated with a specific brand (Module 7).
    """
    brand = db.query(Brand).filter(Brand.id == brand_id).first()
    if not brand:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Brand not found")

    stmt = db.query(Product).filter(Product.brand_id == brand_id)
    if category_id:
        stmt = stmt.filter(Product.category_id == category_id)

    total_items = stmt.count()
    products = stmt.order_by(Product.id.desc()).offset((page - 1) * limit).limit(limit).all()
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

