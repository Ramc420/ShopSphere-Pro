from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.models.product import Product
from app.models.supplier import Supplier, SupplierHistory, ProductSupplier
from app.schemas.supplier import (
    SupplierCreate, SupplierUpdate, SupplierApprovalUpdate, SupplierResponse,
    SupplierHistoryResponse, ProductSupplierCreate, ProductSupplierResponse
)
from app.core.dependencies import get_current_user, require_permissions
from app.core.permissions import Permission

router = APIRouter(prefix="/suppliers", tags=["Module 43: Seller and Supplier Management"])


def utc_now():
    return datetime.now(timezone.utc)


@router.post("", response_model=SupplierResponse, status_code=status.HTTP_201_CREATED)
def register_supplier(
    payload: SupplierCreate,
    current_user: User = Depends(require_permissions(Permission.SUPPLIERS_WRITE.value)),
    db: Session = Depends(get_db)
):
    """Register a new supplier or marketplace seller."""
    existing_code = db.query(Supplier).filter(Supplier.supplier_code == payload.supplier_code).first()
    if existing_code:
        raise HTTPException(status_code=409, detail=f"Supplier code '{payload.supplier_code}' already exists")

    existing_email = db.query(Supplier).filter(Supplier.email == payload.email).first()
    if existing_email:
        raise HTTPException(status_code=409, detail=f"Supplier with email '{payload.email}' already exists")

    supplier = Supplier(
        supplier_code=payload.supplier_code,
        company_name=payload.company_name,
        supplier_type=payload.supplier_type or "SUPPLIER",
        contact_name=payload.contact_name,
        email=payload.email,
        phone=payload.phone,
        tax_id=payload.tax_id,
        business_registration_number=payload.business_registration_number,
        address_line=payload.address_line,
        city=payload.city,
        state=payload.state,
        country=payload.country or "USA",
        postal_code=payload.postal_code,
        status="PENDING_APPROVAL",
        rating=5.0,
        notes=payload.notes
    )
    db.add(supplier)
    db.flush()

    # Log registration history
    history = SupplierHistory(
        supplier_id=supplier.id,
        changed_by_user_id=current_user.id,
        action="REGISTERED",
        from_status=None,
        to_status="PENDING_APPROVAL",
        notes="Initial supplier/seller registration submitted."
    )
    db.add(history)
    db.commit()
    db.refresh(supplier)
    return supplier


@router.get("", response_model=List[SupplierResponse])
def list_suppliers(
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by approval status"),
    supplier_type: Optional[str] = Query(None, description="Filter by type: SUPPLIER or MARKETPLACE_SELLER"),
    search: Optional[str] = Query(None, description="Search company name, contact, or email"),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(require_permissions(Permission.SUPPLIERS_READ.value)),
    db: Session = Depends(get_db)
):
    """List and search suppliers and marketplace sellers."""
    query = db.query(Supplier)
    if status_filter:
        query = query.filter(Supplier.status == status_filter.upper())
    if supplier_type:
        query = query.filter(Supplier.supplier_type == supplier_type.upper())
    if search:
        term = f"%{search}%"
        query = query.filter(
            (Supplier.company_name.ilike(term)) |
            (Supplier.contact_name.ilike(term)) |
            (Supplier.email.ilike(term)) |
            (Supplier.supplier_code.ilike(term))
        )

    return query.order_by(Supplier.created_at.desc()).limit(limit).all()


@router.get("/{supplier_id}", response_model=SupplierResponse)
def get_supplier_details(
    supplier_id: int,
    current_user: User = Depends(require_permissions(Permission.SUPPLIERS_READ.value)),
    db: Session = Depends(get_db)
):
    """Get supplier profile and contact details."""
    supplier = db.query(Supplier).filter(Supplier.id == supplier_id).first()
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")
    return supplier


@router.put("/{supplier_id}", response_model=SupplierResponse)
def update_supplier(
    supplier_id: int,
    payload: SupplierUpdate,
    current_user: User = Depends(require_permissions(Permission.SUPPLIERS_WRITE.value)),
    db: Session = Depends(get_db)
):
    """Update supplier contact and business information."""
    supplier = db.query(Supplier).filter(Supplier.id == supplier_id).first()
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")

    update_dict = payload.model_dump(exclude_unset=True)
    for field, val in update_dict.items():
        setattr(supplier, field, val)

    supplier.updated_at = utc_now()

    # Log update
    history = SupplierHistory(
        supplier_id=supplier.id,
        changed_by_user_id=current_user.id,
        action="UPDATED",
        from_status=supplier.status,
        to_status=supplier.status,
        notes=f"Updated supplier fields: {list(update_dict.keys())}"
    )
    db.add(history)
    db.commit()
    db.refresh(supplier)
    return supplier


@router.patch("/{supplier_id}/approval", response_model=SupplierResponse)
def update_supplier_approval(
    supplier_id: int,
    payload: SupplierApprovalUpdate,
    current_user: User = Depends(require_permissions(Permission.SUPPLIERS_WRITE.value)),
    db: Session = Depends(get_db)
):
    """
    Track and update supplier account approval status.
    Transitions: APPROVED, REJECTED, SUSPENDED.
    """
    status_upper = payload.status.upper()
    if status_upper not in ["APPROVED", "REJECTED", "SUSPENDED", "PENDING_APPROVAL"]:
        raise HTTPException(status_code=400, detail="Invalid approval status")

    supplier = db.query(Supplier).filter(Supplier.id == supplier_id).first()
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")

    from_status = supplier.status
    supplier.status = status_upper
    supplier.updated_at = utc_now()

    history = SupplierHistory(
        supplier_id=supplier.id,
        changed_by_user_id=current_user.id,
        action="APPROVAL_CHANGE",
        from_status=from_status,
        to_status=status_upper,
        notes=payload.notes or f"Approval status transitioned from {from_status} to {status_upper}"
    )
    db.add(history)
    db.commit()
    db.refresh(supplier)
    return supplier


@router.post("/{supplier_id}/products", response_model=ProductSupplierResponse, status_code=status.HTTP_201_CREATED)
def associate_product_with_supplier(
    supplier_id: int,
    payload: ProductSupplierCreate,
    current_user: User = Depends(require_permissions(Permission.SUPPLIERS_WRITE.value)),
    db: Session = Depends(get_db)
):
    """Associate a catalog product with a supplier or marketplace seller."""
    supplier = db.query(Supplier).filter(Supplier.id == supplier_id).first()
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")

    product = db.query(Product).filter(Product.id == payload.product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    existing = db.query(ProductSupplier).filter(
        ProductSupplier.supplier_id == supplier_id,
        ProductSupplier.product_id == payload.product_id
    ).first()

    if existing:
        existing.negotiated_cost = payload.negotiated_cost
        existing.lead_time_days = payload.lead_time_days or existing.lead_time_days
        existing.supplier_sku = payload.supplier_sku or existing.supplier_sku
        existing.is_primary = payload.is_primary if payload.is_primary is not None else existing.is_primary
        db.commit()
        db.refresh(existing)
        return existing

    assoc = ProductSupplier(
        supplier_id=supplier_id,
        product_id=payload.product_id,
        supplier_sku=payload.supplier_sku,
        negotiated_cost=payload.negotiated_cost,
        lead_time_days=payload.lead_time_days or 7,
        is_primary=payload.is_primary or False
    )
    db.add(assoc)
    db.commit()
    db.refresh(assoc)
    return assoc


@router.get("/{supplier_id}/products", response_model=List[ProductSupplierResponse])
def get_supplier_products(
    supplier_id: int,
    current_user: User = Depends(require_permissions(Permission.SUPPLIERS_READ.value)),
    db: Session = Depends(get_db)
):
    """Retrieve all products associated with a supplier."""
    supplier = db.query(Supplier).filter(Supplier.id == supplier_id).first()
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")
    return db.query(ProductSupplier).filter(ProductSupplier.supplier_id == supplier_id).all()


@router.get("/{supplier_id}/history", response_model=List[SupplierHistoryResponse])
def get_supplier_history(
    supplier_id: int,
    current_user: User = Depends(require_permissions(Permission.SUPPLIERS_READ.value)),
    db: Session = Depends(get_db)
):
    """Maintain and view full change and approval history of a supplier."""
    supplier = db.query(Supplier).filter(Supplier.id == supplier_id).first()
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")
    return db.query(SupplierHistory).filter(SupplierHistory.supplier_id == supplier_id).order_by(SupplierHistory.created_at.desc()).all()

