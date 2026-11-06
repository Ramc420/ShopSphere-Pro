import re
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from app.core.audit import log_user_activity
from app.core.dependencies import get_client_ip, get_current_user, require_roles
from app.core.permissions import UserRole
from app.database import get_db
from app.models.category import Category
from app.models.product import Product
from app.models.user import User
from app.schemas.category import (
    CategoryBreadcrumb,
    CategoryCreate,
    CategoryResponse,
    CategoryTreeNode,
    CategoryUpdate,
)
from app.schemas.common import MessageResponse

router = APIRouter(prefix="/categories", tags=["Module 6: Product Category Management"])


def generate_slug(text: str) -> str:
    cleaned = re.sub(r"[^\w\s-]", "", text.lower()).strip()
    return re.sub(r"[-\s]+", "-", cleaned)


def build_tree_node(category: Category, all_cats: List[Category]) -> CategoryTreeNode:
    node = CategoryTreeNode(
        id=category.id,
        name=category.name,
        slug=category.slug,
        description=category.description,
        parent_id=category.parent_id,
        image_url=category.image_url,
        display_order=category.display_order,
        is_active=category.is_active,
        created_at=category.created_at,
        updated_at=category.updated_at,
        children=[]
    )
    children = [c for c in all_cats if c.parent_id == category.id]
    children.sort(key=lambda x: (x.display_order, x.name))
    node.children = [build_tree_node(child, all_cats) for child in children]
    return node


@router.post("", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
def create_category(
    payload: CategoryCreate,
    request: Request,
    current_user: User = Depends(require_roles(UserRole.SUPER_ADMIN.value, UserRole.ADMIN.value, UserRole.EMPLOYEE.value)),
    db: Session = Depends(get_db)
):
    """
    Create a new category or subcategory (by specifying parent_id).
    """
    slug = payload.slug or generate_slug(payload.name)
    existing_slug = db.query(Category).filter(Category.slug == slug).first()
    if existing_slug:
        slug = f"{slug}-{Category.id}"

    # If parent_id provided, verify parent exists
    if payload.parent_id:
        parent = db.query(Category).filter(Category.id == payload.parent_id).first()
        if not parent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Parent category with ID {payload.parent_id} was not found"
            )

    cat = Category(
        name=payload.name.strip(),
        slug=slug,
        description=payload.description,
        parent_id=payload.parent_id,
        image_url=payload.image_url,
        display_order=payload.display_order,
        is_active=payload.is_active
    )
    db.add(cat)
    db.commit()
    db.refresh(cat)

    log_user_activity(
        db,
        action="CATEGORY_CREATED",
        user_id=current_user.id,
        ip_address=get_client_ip(request),
        user_agent=request.headers.get("user-agent"),
        details={"category_id": cat.id, "name": cat.name, "parent_id": cat.parent_id}
    )

    return cat


@router.get("", response_model=List[CategoryResponse])
def get_categories(
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    parent_id: Optional[int] = Query(None, description="Filter by parent ID (pass 0 for root categories)"),
    db: Session = Depends(get_db)
):
    """
    Retrieve flat list of product categories with filtering.
    """
    stmt = db.query(Category)
    if is_active is not None:
        stmt = stmt.filter(Category.is_active == is_active)
        
    if parent_id is not None:
        if parent_id == 0:
            stmt = stmt.filter(Category.parent_id.is_(None))
        else:
            stmt = stmt.filter(Category.parent_id == parent_id)
            
    return stmt.order_by(Category.display_order.asc(), Category.name.asc()).all()


@router.get("/tree", response_model=List[CategoryTreeNode])
def get_category_hierarchy_tree(
    active_only: bool = Query(True, description="Only include active categories"),
    db: Session = Depends(get_db)
):
    """
    Retrieve complete hierarchical category tree (Module 6).
    Recursively nests subcategories inside parent nodes.
    """
    stmt = db.query(Category)
    if active_only:
        stmt = stmt.filter(Category.is_active == True)
        
    all_cats = stmt.all()
    roots = [c for c in all_cats if c.parent_id is None]
    roots.sort(key=lambda x: (x.display_order, x.name))

    return [build_tree_node(r, all_cats) for r in roots]


@router.get("/{category_id}", response_model=CategoryResponse)
def get_category_by_id(
    category_id: int,
    db: Session = Depends(get_db)
):
    """
    Retrieve specific category by ID.
    """
    cat = db.query(Category).filter(Category.id == category_id).first()
    if not cat:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
    return cat


@router.get("/{category_id}/breadcrumbs", response_model=List[CategoryBreadcrumb])
def get_category_breadcrumbs(
    category_id: int,
    db: Session = Depends(get_db)
):
    """
    Retrieve breadcrumb trail from root category down to the given category.
    """
    cat = db.query(Category).filter(Category.id == category_id).first()
    if not cat:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")

    breadcrumbs = []
    curr = cat
    visited = set()
    while curr and curr.id not in visited:
        visited.add(curr.id)
        breadcrumbs.append(CategoryBreadcrumb(id=curr.id, name=curr.name, slug=curr.slug))
        if curr.parent_id:
            curr = db.query(Category).filter(Category.id == curr.parent_id).first()
        else:
            curr = None

    breadcrumbs.reverse()
    return breadcrumbs


@router.put("/{category_id}", response_model=CategoryResponse)
def update_category(
    category_id: int,
    payload: CategoryUpdate,
    request: Request,
    current_user: User = Depends(require_roles(UserRole.SUPER_ADMIN.value, UserRole.ADMIN.value, UserRole.EMPLOYEE.value)),
    db: Session = Depends(get_db)
):
    """
    Update category details. Validates against cyclic parenting.
    """
    cat = db.query(Category).filter(Category.id == category_id).first()
    if not cat:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")

    # Prevent setting parent to itself
    if payload.parent_id is not None:
        if payload.parent_id == category_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A category cannot be its own parent"
            )
            
        # Prevent setting parent to any descendant (cycle prevention)
        descendants = []
        queue = [category_id]
        while queue:
            curr_id = queue.pop(0)
            children = db.query(Category.id).filter(Category.parent_id == curr_id).all()
            for ch in children:
                descendants.append(ch[0])
                queue.append(ch[0])
                
        if payload.parent_id in descendants:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot set parent to a descendant category (cyclic hierarchy detected)."
            )

    for field, val in payload.model_dump(exclude_unset=True).items():
        if val is not None:
            if isinstance(val, str):
                setattr(cat, field, val.strip())
            else:
                setattr(cat, field, val)

    db.commit()
    db.refresh(cat)

    log_user_activity(
        db,
        action="CATEGORY_UPDATED",
        user_id=current_user.id,
        ip_address=get_client_ip(request),
        user_agent=request.headers.get("user-agent"),
        details={"category_id": cat.id}
    )

    return cat


@router.patch("/{category_id}/status", response_model=CategoryResponse)
def toggle_category_status(
    category_id: int,
    is_active: bool = Query(..., description="Activate or deactivate"),
    request: Request = None,
    current_user: User = Depends(require_roles(UserRole.SUPER_ADMIN.value, UserRole.ADMIN.value, UserRole.EMPLOYEE.value)),
    db: Session = Depends(get_db)
):
    """
    Activate or deactivate a category.
    """
    cat = db.query(Category).filter(Category.id == category_id).first()
    if not cat:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")

    cat.is_active = is_active
    db.commit()
    db.refresh(cat)

    log_user_activity(
        db,
        action="CATEGORY_STATUS_TOGGLED",
        user_id=current_user.id,
        ip_address=get_client_ip(request) if request else None,
        user_agent=request.headers.get("user-agent") if request else None,
        details={"category_id": cat.id, "is_active": is_active}
    )

    return cat


@router.delete("/{category_id}", response_model=MessageResponse)
def delete_category(
    category_id: int,
    request: Request,
    current_user: User = Depends(require_roles(UserRole.SUPER_ADMIN.value, UserRole.ADMIN.value)),
    db: Session = Depends(get_db)
):
    """
    Prevent invalid category deletion (Module 6):
    - Rejects deletion if subcategories exist.
    - Rejects deletion if products are associated.
    """
    cat = db.query(Category).filter(Category.id == category_id).first()
    if not cat:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")

    # 1. Check for child subcategories
    subcategories_count = db.query(Category).filter(Category.parent_id == category_id).count()
    if subcategories_count > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot delete category: It contains {subcategories_count} subcategories. Please delete or reassign them first."
        )

    # 2. Check for associated products
    products_count = db.query(Product).filter(Product.category_id == category_id).count()
    if products_count > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot delete category: It is currently associated with {products_count} products. Reassign or remove products first."
        )

    cat_name = cat.name
    db.delete(cat)
    db.commit()

    log_user_activity(
        db,
        action="CATEGORY_DELETED",
        user_id=current_user.id,
        ip_address=get_client_ip(request),
        user_agent=request.headers.get("user-agent"),
        details={"category_id": category_id, "name": cat_name}
    )

    return MessageResponse(
        success=True,
        message=f"Category '{cat_name}' (ID: {category_id}) successfully deleted."
    )

