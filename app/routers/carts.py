from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.database import get_db
from app.models.cart import Cart, CartItem
from app.models.inventory import InventoryItem
from app.models.pricing import ProductPrice
from app.models.product import Product
from app.models.user import User
from app.models.variant import ProductVariant
from app.schemas.cart import CartItemAdd, CartItemResponse, CartItemUpdate, CartResponse
from app.schemas.common import MessageResponse

router = APIRouter(prefix="/cart", tags=["Module 17: Shopping Cart Management"])


def to_naive_utc(dt):
    if dt is None:
        return None
    if dt.tzinfo is not None:
        return dt.astimezone(timezone.utc).replace(tzinfo=None)
    return dt


def utc_now():
    return datetime.now(timezone.utc).replace(tzinfo=None)


def get_effective_price(db: Session, product_id: int, variant_id: Optional[int] = None) -> float:
    """Calculate effective price considering base price and active promotional sale price."""
    # Check variant price first
    if variant_id:
        v = db.query(ProductVariant).filter(ProductVariant.id == variant_id).first()
        if v and v.price:
            return float(v.price)

    # Check ProductPrice model
    pricing = db.query(ProductPrice).filter(ProductPrice.product_id == product_id).first()
    if pricing:
        now = utc_now()
        s_start = to_naive_utc(pricing.sale_start_date)
        s_end = to_naive_utc(pricing.sale_end_date)
        if pricing.sale_price and s_start and s_end and (s_start <= now <= s_end):
            return float(pricing.sale_price)
        return float(pricing.base_price)

    # Fallback to Product.base_price
    prod = db.query(Product).filter(Product.id == product_id).first()
    return float(prod.base_price) if prod else 0.0


def get_available_stock(db: Session, product_id: int, variant_id: Optional[int] = None) -> int:
    inv = db.query(InventoryItem).filter(
        InventoryItem.product_id == product_id,
        InventoryItem.variant_id == variant_id
    ).first()
    if inv:
        return max(0, inv.available_quantity)
    if variant_id:
        v = db.query(ProductVariant).filter(ProductVariant.id == variant_id).first()
        return v.stock_quantity if v else 0
    return 100  # Default assumption if unmanaged


def get_or_create_active_cart(db: Session, user_id: int) -> Cart:
    cart = db.query(Cart).filter(
        Cart.user_id == user_id,
        Cart.status == "ACTIVE"
    ).first()
    if not cart:
        cart = Cart(user_id=user_id, status="ACTIVE")
        db.add(cart)
        db.commit()
        db.refresh(cart)
    return cart


def build_cart_response(db: Session, cart: Cart) -> CartResponse:
    item_responses = []
    total_subtotal = 0.0
    total_qty = 0

    for item in cart.items:
        prod = db.query(Product).filter(Product.id == item.product_id).first()
        var = db.query(ProductVariant).filter(ProductVariant.id == item.variant_id).first() if item.variant_id else None

        prod_name = prod.name if prod else "Unknown Product"
        sku = var.sku if var else (prod.base_sku if prod else "SKU-UNKNOWN")
        unit_price = get_effective_price(db, item.product_id, item.variant_id)
        subtotal = round(unit_price * item.quantity, 2)
        avail = get_available_stock(db, item.product_id, item.variant_id)

        item_responses.append(
            CartItemResponse(
                id=item.id,
                cart_id=cart.id,
                product_id=item.product_id,
                variant_id=item.variant_id,
                product_name=prod_name,
                sku=sku,
                unit_price=unit_price,
                quantity=item.quantity,
                subtotal=subtotal,
                is_available=avail >= item.quantity,
                available_stock=avail
            )
        )
        total_subtotal += subtotal
        total_qty += item.quantity

    return CartResponse(
        id=cart.id,
        user_id=cart.user_id,
        status=cart.status,
        items=item_responses,
        item_count=total_qty,
        subtotal=round(total_subtotal, 2),
        created_at=cart.created_at,
        updated_at=cart.updated_at
    )


@router.get("", response_model=CartResponse)
def get_cart(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Retrieve customer's active shopping cart, items, live prices, and stock availability.
    """
    cart = get_or_create_active_cart(db, current_user.id)
    return build_cart_response(db, cart)


@router.post("/items", response_model=CartResponse, status_code=status.HTTP_201_CREATED)
def add_item_to_cart(
    payload: CartItemAdd,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Add product or variant to shopping cart. Validates product availability.
    """
    prod = db.query(Product).filter(Product.id == payload.product_id).first()
    if not prod or not prod.is_active:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found or inactive")

    if payload.variant_id:
        v = db.query(ProductVariant).filter(
            ProductVariant.id == payload.variant_id,
            ProductVariant.product_id == payload.product_id
        ).first()
        if not v:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product variant not found")

    avail_stock = get_available_stock(db, payload.product_id, payload.variant_id)

    cart = get_or_create_active_cart(db, current_user.id)

    # Check if item exists in cart
    existing_item = db.query(CartItem).filter(
        CartItem.cart_id == cart.id,
        CartItem.product_id == payload.product_id,
        CartItem.variant_id == payload.variant_id
    ).first()

    requested_qty = payload.quantity
    if existing_item:
        new_qty = existing_item.quantity + payload.quantity
        if new_qty > avail_stock:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Requested total quantity ({new_qty}) exceeds available stock ({avail_stock})."
            )
        existing_item.quantity = new_qty
    else:
        if requested_qty > avail_stock:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Requested quantity ({requested_qty}) exceeds available stock ({avail_stock})."
            )
        new_item = CartItem(
            cart_id=cart.id,
            product_id=payload.product_id,
            variant_id=payload.variant_id,
            quantity=payload.quantity
        )
        db.add(new_item)

    cart.updated_at = utc_now()
    db.commit()
    db.refresh(cart)

    return build_cart_response(db, cart)


@router.put("/items/{item_id}", response_model=CartResponse)
def update_cart_item_quantity(
    item_id: int,
    payload: CartItemUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update quantity of an existing item in the cart.
    """
    cart = get_or_create_active_cart(db, current_user.id)
    item = db.query(CartItem).filter(
        CartItem.id == item_id,
        CartItem.cart_id == cart.id
    ).first()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cart item not found")

    avail_stock = get_available_stock(db, item.product_id, item.variant_id)
    if payload.quantity > avail_stock:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Requested quantity ({payload.quantity}) exceeds available stock ({avail_stock})."
        )

    item.quantity = payload.quantity
    cart.updated_at = utc_now()
    db.commit()
    db.refresh(cart)

    return build_cart_response(db, cart)


@router.delete("/items/{item_id}", response_model=CartResponse)
def remove_cart_item(
    item_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Remove an item from the customer's cart.
    """
    cart = get_or_create_active_cart(db, current_user.id)
    item = db.query(CartItem).filter(
        CartItem.id == item_id,
        CartItem.cart_id == cart.id
    ).first()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cart item not found")

    db.delete(item)
    cart.updated_at = utc_now()
    db.commit()
    db.refresh(cart)

    return build_cart_response(db, cart)


@router.delete("/clear", response_model=MessageResponse)
def clear_cart(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Empty all items from customer's shopping cart.
    """
    cart = get_or_create_active_cart(db, current_user.id)
    db.query(CartItem).filter(CartItem.cart_id == cart.id).delete()
    cart.updated_at = utc_now()
    db.commit()
    return MessageResponse(message="Cart cleared successfully.")
