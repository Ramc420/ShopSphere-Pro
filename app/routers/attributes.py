import re
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_

from app.core.audit import log_user_activity
from app.core.dependencies import get_client_ip, get_current_user, require_roles
from app.core.permissions import UserRole
from app.database import get_db
from app.models.attribute import (
    Attribute,
    AttributeOption,
    CategoryAttribute,
    ProductAttributeValue,
)
from app.models.category import Category
from app.models.product import Product
from app.models.user import User
from app.schemas.attribute import (
    AttributeCreate,
    AttributeOptionCreate,
    AttributeOptionResponse,
    AttributeResponse,
    AttributeUpdate,
    CategoryAttributeAssign,
    CategoryAttributeResponse,
    ProductAttributeAssign,
    ProductAttributeValueResponse,
)
from app.schemas.common import MessageResponse
from app.schemas.product import ProductResponse

router = APIRouter(prefix="/attributes", tags=["Module 11: Product Attributes"])


def generate_code(name: str) -> str:
    cleaned = re.sub(r"[^\w\s-]", "", name.lower()).strip()
    return re.sub(r"[-\s]+", "_", cleaned)


def validate_value(attr: Attribute, val_str: str, db: Session):
    val = val_str.strip()
    if attr.data_type == "NUMBER":
        try:
            float(val)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid value '{val}' for attribute '{attr.name}'. Expected a valid number."
            )
    elif attr.data_type == "BOOLEAN":
        if val.lower() not in ["true", "false", "1", "0", "yes", "no"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid value '{val}' for attribute '{attr.name}'. Expected boolean (true/false)."
            )
    elif attr.data_type == "SELECT":
        allowed_options = db.query(AttributeOption.value).filter(AttributeOption.attribute_id == attr.id).all()
        allowed = [opt[0].lower() for opt in allowed_options]
        if allowed and val.lower() not in allowed:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid option '{val}' for attribute '{attr.name}'. Allowed options: {', '.join([o[0] for o in allowed_options])}"
            )


@router.post("", response_model=AttributeResponse, status_code=status.HTTP_201_CREATED)
def create_attribute(
    payload: AttributeCreate,
    request: Request,
    current_user: User = Depends(require_roles(UserRole.SUPER_ADMIN.value, UserRole.ADMIN.value, UserRole.EMPLOYEE.value)),
    db: Session = Depends(get_db)
):
    """
    Define a new product attribute (e.g. Size, Material, Color, Storage, RAM).
    """
    code = payload.code or generate_code(payload.name)
    existing = db.query(Attribute).filter(Attribute.code == code).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Attribute code '{code}' already exists.")

    data_type_upper = payload.data_type.upper()
    valid_types = ["TEXT", "NUMBER", "SELECT", "BOOLEAN"]
    if data_type_upper not in valid_types:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid data_type. Allowed: {valid_types}")

    attr = Attribute(
        name=payload.name.strip(),
        code=code,
        data_type=data_type_upper,
        is_required=payload.is_required,
        is_filterable=payload.is_filterable
    )
    db.add(attr)
    db.flush()

    if data_type_upper == "SELECT" and payload.options:
        for idx, opt_val in enumerate(payload.options):
            opt = AttributeOption(attribute_id=attr.id, value=opt_val.strip(), display_order=idx)
            db.add(opt)

    db.commit()
    db.refresh(attr)

    log_user_activity(
        db,
        action="ATTRIBUTE_CREATED",
        user_id=current_user.id,
        ip_address=get_client_ip(request),
        user_agent=request.headers.get("user-agent"),
        details={"attribute_id": attr.id, "name": attr.name, "code": attr.code}
    )

    return attr


@router.get("", response_model=List[AttributeResponse])
def get_attributes(
    filterable_only: Optional[bool] = Query(None, description="Only filterable attributes"),
    db: Session = Depends(get_db)
):
    """
    List all defined product attributes.
    """
    stmt = db.query(Attribute).options(joinedload(Attribute.options))
    if filterable_only is not None:
        stmt = stmt.filter(Attribute.is_filterable == filterable_only)
    return stmt.order_by(Attribute.name.asc()).all()


@router.get("/{attribute_id}", response_model=AttributeResponse)
def get_attribute_by_id(
    attribute_id: int,
    db: Session = Depends(get_db)
):
    """
    Retrieve specific attribute with its options.
    """
    attr = db.query(Attribute).options(joinedload(Attribute.options)).filter(Attribute.id == attribute_id).first()
    if not attr:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Attribute not found")
    return attr


@router.post("/{attribute_id}/options", response_model=AttributeOptionResponse, status_code=status.HTTP_201_CREATED)
def add_attribute_option(
    attribute_id: int,
    payload: AttributeOptionCreate,
    current_user: User = Depends(require_roles(UserRole.SUPER_ADMIN.value, UserRole.ADMIN.value, UserRole.EMPLOYEE.value)),
    db: Session = Depends(get_db)
):
    """
    Add a selectable option value to an attribute (e.g. 'Midnight Blue' to Color).
    """
    attr = db.query(Attribute).filter(Attribute.id == attribute_id).first()
    if not attr:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Attribute not found")

    opt = AttributeOption(
        attribute_id=attribute_id,
        value=payload.value.strip(),
        display_order=payload.display_order
    )
    db.add(opt)
    db.commit()
    db.refresh(opt)
    return opt


@router.post("/category-link", response_model=CategoryAttributeResponse, status_code=status.HTTP_201_CREATED)
def link_attribute_to_category(
    payload: CategoryAttributeAssign,
    current_user: User = Depends(require_roles(UserRole.SUPER_ADMIN.value, UserRole.ADMIN.value, UserRole.EMPLOYEE.value)),
    db: Session = Depends(get_db)
):
    """
    Associate an attribute with a category (Category-specific attributes).
    """
    cat = db.query(Category).filter(Category.id == payload.category_id).first()
    if not cat:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")

    attr = db.query(Attribute).filter(Attribute.id == payload.attribute_id).first()
    if not attr:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Attribute not found")

    existing = db.query(CategoryAttribute).filter(
        CategoryAttribute.category_id == payload.category_id,
        CategoryAttribute.attribute_id == payload.attribute_id
    ).first()
    if existing:
        existing.is_required = payload.is_required
        db.commit()
        db.refresh(existing)
        return existing

    link = CategoryAttribute(
        category_id=payload.category_id,
        attribute_id=payload.attribute_id,
        is_required=payload.is_required
    )
    db.add(link)
    db.commit()
    db.refresh(link)
    return link


@router.get("/category/{category_id}", response_model=List[CategoryAttributeResponse])
def get_category_attributes(
    category_id: int,
    include_parents: bool = Query(True, description="Inherit attributes from parent categories"),
    db: Session = Depends(get_db)
):
    """
    Retrieve attributes applicable to a category, optionally inheriting from parent hierarchy.
    """
    target_category_ids = [category_id]
    if include_parents:
        curr = db.query(Category).filter(Category.id == category_id).first()
        while curr and curr.parent_id:
            target_category_ids.append(curr.parent_id)
            curr = db.query(Category).filter(Category.id == curr.parent_id).first()

    links = (
        db.query(CategoryAttribute)
        .options(joinedload(CategoryAttribute.attribute).joinedload(Attribute.options))
        .filter(CategoryAttribute.category_id.in_(target_category_ids))
        .all()
    )
    return links


@router.post("/products/{product_id}/values", response_model=ProductAttributeValueResponse, status_code=status.HTTP_201_CREATED)
def assign_product_attribute(
    product_id: int,
    payload: ProductAttributeAssign,
    current_user: User = Depends(require_roles(UserRole.SUPER_ADMIN.value, UserRole.ADMIN.value, UserRole.EMPLOYEE.value)),
    db: Session = Depends(get_db)
):
    """
    Assign an attribute value to a product. Validates data type integrity.
    """
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

    attr = db.query(Attribute).filter(Attribute.id == payload.attribute_id).first()
    if not attr:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Attribute not found")

    # Validate value format
    validate_value(attr, payload.value, db)

    existing = db.query(ProductAttributeValue).filter(
        ProductAttributeValue.product_id == product_id,
        ProductAttributeValue.attribute_id == payload.attribute_id
    ).first()

    if existing:
        existing.value = payload.value.strip()
        db.commit()
        db.refresh(existing)
        return ProductAttributeValueResponse(
            id=existing.id,
            product_id=product_id,
            attribute_id=attr.id,
            attribute_code=attr.code,
            attribute_name=attr.name,
            value=existing.value,
            created_at=existing.created_at
        )

    val_entry = ProductAttributeValue(
        product_id=product_id,
        attribute_id=payload.attribute_id,
        value=payload.value.strip()
    )
    db.add(val_entry)
    db.commit()
    db.refresh(val_entry)

    return ProductAttributeValueResponse(
        id=val_entry.id,
        product_id=product_id,
        attribute_id=attr.id,
        attribute_code=attr.code,
        attribute_name=attr.name,
        value=val_entry.value,
        created_at=val_entry.created_at
    )


@router.get("/products/{product_id}/values", response_model=List[ProductAttributeValueResponse])
def get_product_attribute_values(
    product_id: int,
    db: Session = Depends(get_db)
):
    """
    Retrieve all assigned attributes and values for a product.
    """
    values = (
        db.query(ProductAttributeValue)
        .options(joinedload(ProductAttributeValue.attribute))
        .filter(ProductAttributeValue.product_id == product_id)
        .all()
    )
    return [
        ProductAttributeValueResponse(
            id=v.id,
            product_id=v.product_id,
            attribute_id=v.attribute_id,
            attribute_code=v.attribute.code if v.attribute else None,
            attribute_name=v.attribute.name if v.attribute else None,
            value=v.value,
            created_at=v.created_at
        )
        for v in values
    ]


@router.get("/products/filter-by-attributes", response_model=List[ProductResponse])
def filter_products_by_attributes(
    code: str = Query(..., description="Attribute code e.g. 'color' or 'material'"),
    value: str = Query(..., description="Attribute value e.g. 'Cotton' or 'Black'"),
    db: Session = Depends(get_db)
):
    """
    Filter catalog products by attribute code and value.
    """
    attr = db.query(Attribute).filter(Attribute.code == code.strip().lower()).first()
    if not attr:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Attribute '{code}' not found")

    product_ids = (
        db.query(ProductAttributeValue.product_id)
        .filter(
            ProductAttributeValue.attribute_id == attr.id,
            ProductAttributeValue.value.ilike(value.strip())
        )
        .all()
    )
    p_ids = [p[0] for p in product_ids]
    if not p_ids:
        return []

    products = db.query(Product).filter(Product.id.in_(p_ids)).all()
    return [ProductResponse.model_validate(p) for p in products]

