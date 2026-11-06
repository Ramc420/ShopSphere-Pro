from datetime import datetime, timezone
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.database import get_db
from app.models.inventory import InventoryItem
from app.models.pricing import ProductPrice
from app.models.product import Product
from app.models.user import User
from app.models.variant import ProductVariant
from app.models.wishlist import WishlistItem
from app.schemas.common import MessageResponse
from app.schemas.wishlist import WishlistItemAdd, WishlistItemResponse

router = APIRouter(prefix="/wishlist", tags=["Module 19: Wishlist Management"])


def to_naive_utc(dt):
    if dt is None:
        return None
    if dt.tzinfo is not None:
        return dt.astimezone(timezone.utc).replace(tzinfo=None)
    return dt


def utc_now():
    return datetime.now(timezone.utc).replace(tzinfo=None)


def resolve_wishlist_item(db: Session, item: WishlistItem) -> WishlistItemResponse:
    prod = db.query(Product).filter(Product.id == item.product_id).first()
    var = db.query(ProductVariant).filter(ProductVariant.id == item.variant_id).first() if item.variant_id else None

    prod_name = prod.name if prod else "Unknown Product"
    sku = var.sku if var else (prod.base_sku if prod else "SKU")

    # Price resolution
    price = 0.0
    if var and var.price:
        price = float(var.price)
    else:
        pricing = db.query(ProductPrice).filter(ProductPrice.product_id == item.product_id).first()
        if pricing:
            now = utc_now()
            s_start = to_naive_utc(pricing.sale_start_date)
            s_end = to_naive_utc(pricing.sale_end_date)
            if pricing.sale_price and s_start and s_end and (s_start <= now <= s_end):
                price = float(pricing.sale_price)
            else:
                price = float(pricing.base_price)
        elif prod:
            price = float(prod.base_price)

    # Availability resolution
    inv = db.query(InventoryItem).filter(
        InventoryItem.product_id == item.product_id,
        InventoryItem.variant_id == item.variant_id
    ).first()

    avail_qty = inv.available_quantity if inv else (var.stock_quantity if var else 10)
    if avail_qty <= 0:
        avail_status = "OUT_OF_STOCK"
        in_stock = False
    elif avail_qty <= (inv.low_stock_threshold if inv else 5):
        avail_status = "LOW_STOCK"
        in_stock = True
    else:
        avail_status = "IN_STOCK"
        in_stock = True

    return WishlistItemResponse(
        id=item.id,
        user_id=item.user_id,
        product_id=item.product_id,
        variant_id=item.variant_id,
        product_name=prod_name,
        sku=sku,
        price=price,
        availability_status=avail_status,
        is_in_stock=in_stock,
        created_at=item.created_at
    )


@router.post("", response_model=WishlistItemResponse, status_code=status.HTTP_201_CREATED)
def add_to_wishlist(
    payload: WishlistItemAdd,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Save a product or variant to the customer's wishlist. Prevents duplicate entries.
    """
    prod = db.query(Product).filter(Product.id == payload.product_id).first()
    if not prod:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

    if payload.variant_id:
        v = db.query(ProductVariant).filter(
            ProductVariant.id == payload.variant_id,
            ProductVariant.product_id == payload.product_id
        ).first()
        if not v:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Variant not found")

    # Prevent duplicate entries
    existing = db.query(WishlistItem).filter(
        WishlistItem.user_id == current_user.id,
        WishlistItem.product_id == payload.product_id,
        WishlistItem.variant_id == payload.variant_id
    ).first()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Product is already in your wishlist."
        )

    item = WishlistItem(
        user_id=current_user.id,
        product_id=payload.product_id,
        variant_id=payload.variant_id
    )
    db.add(item)
    db.commit()
    db.refresh(item)

    return resolve_wishlist_item(db, item)


@router.get("", response_model=List[WishlistItemResponse])
def get_wishlist(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Retrieve customer's saved wishlist items with live availability states.
    """
    items = db.query(WishlistItem).filter(WishlistItem.user_id == current_user.id).order_by(WishlistItem.created_at.desc()).all()
    return [resolve_wishlist_item(db, i) for i in items]


@router.delete("/{item_id}", response_model=MessageResponse)
def remove_from_wishlist(
    item_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Remove an item from customer's wishlist.
    """
    item = db.query(WishlistItem).filter(
        WishlistItem.id == item_id,
        WishlistItem.user_id == current_user.id
    ).first()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Wishlist item not found")

    db.delete(item)
    db.commit()
    return MessageResponse(message="Item removed from wishlist.")


@router.delete("/clear", response_model=MessageResponse)
def clear_wishlist(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Clear all items from wishlist.
    """
    db.query(WishlistItem).filter(WishlistItem.user_id == current_user.id).delete()
    db.commit()
    return MessageResponse(message="Wishlist cleared.")
