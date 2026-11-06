from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.database import get_db
from app.models.address import Address
from app.models.cart import Cart, CartItem
from app.models.coupon import Coupon
from app.models.pricing import ProductPrice
from app.models.product import Product
from app.models.promotion import Promotion
from app.models.shipping import ShippingMethod
from app.models.tax import TaxRate
from app.models.user import User
from app.models.variant import ProductVariant
from app.schemas.checkout import (
    CalculationItemDetail,
    CartCalculationRequest,
    CartCalculationSummary,
)

router = APIRouter(prefix="/cart/calculate", tags=["Module 18: Cart Price Calculation"])


def to_naive_utc(dt):
    if dt is None:
        return None
    if dt.tzinfo is not None:
        return dt.astimezone(timezone.utc).replace(tzinfo=None)
    return dt


def utc_now():
    return datetime.now(timezone.utc).replace(tzinfo=None)


def compute_server_price(db: Session, product_id: int, variant_id: Optional[int] = None) -> float:
    """Validate and compute price strictly from server-side database records."""
    if variant_id:
        v = db.query(ProductVariant).filter(ProductVariant.id == variant_id).first()
        if v and v.price:
            return float(v.price)

    pricing = db.query(ProductPrice).filter(ProductPrice.product_id == product_id).first()
    if pricing:
        now = utc_now()
        s_start = to_naive_utc(pricing.sale_start_date)
        s_end = to_naive_utc(pricing.sale_end_date)
        if pricing.sale_price and s_start and s_end and (s_start <= now <= s_end):
            return float(pricing.sale_price)
        return float(pricing.base_price)

    prod = db.query(Product).filter(Product.id == product_id).first()
    return float(prod.base_price) if prod else 0.0


def calculate_cart_summary(
    db: Session,
    user: User,
    cart_id: Optional[int] = None,
    coupon_code: Optional[str] = None,
    shipping_method_code: Optional[str] = None,
    shipping_address_id: Optional[int] = None
) -> CartCalculationSummary:
    # 1. Resolve Cart
    if cart_id:
        cart = db.query(Cart).filter(Cart.id == cart_id).first()
    else:
        cart = db.query(Cart).filter(Cart.user_id == user.id, Cart.status == "ACTIVE").first()

    if not cart or not cart.items:
        return CartCalculationSummary(
            items=[],
            items_count=0,
            subtotal_amount=0.0,
            coupon_discount=0.0,
            promotion_discount=0.0,
            total_discount=0.0,
            tax_amount=0.0,
            tax_rate_percent=0.0,
            shipping_amount=0.0,
            grand_total=0.0
        )

    # 2. Calculate Server-Side Item Subtotals
    item_details = []
    subtotal = 0.0
    items_count = 0

    for item in cart.items:
        prod = db.query(Product).filter(Product.id == item.product_id).first()
        var = db.query(ProductVariant).filter(ProductVariant.id == item.variant_id).first() if item.variant_id else None
        prod_name = prod.name if prod else "Unknown Product"
        sku = var.sku if var else (prod.base_sku if prod else "SKU")
        unit_price = compute_server_price(db, item.product_id, item.variant_id)
        line_subtotal = round(unit_price * item.quantity, 2)

        item_details.append(
            CalculationItemDetail(
                product_id=item.product_id,
                variant_id=item.variant_id,
                product_name=prod_name,
                sku=sku,
                unit_price=unit_price,
                quantity=item.quantity,
                subtotal=line_subtotal
            )
        )
        subtotal += line_subtotal
        items_count += item.quantity

    subtotal = round(subtotal, 2)

    # 3. Apply Coupon Discount if provided
    coupon_disc = 0.0
    applied_coupon_label = None
    if coupon_code:
        code_clean = coupon_code.strip().upper()
        c = db.query(Coupon).filter(Coupon.code == code_clean, Coupon.is_active == True).first()
        if c:
            now = utc_now()
            valid_time = True
            v_from = to_naive_utc(c.valid_from)
            v_until = to_naive_utc(c.valid_until)
            if v_from and now < v_from:
                valid_time = False
            if v_until and now > v_until:
                valid_time = False
            if c.usage_limit is not None and c.used_count >= c.usage_limit:
                valid_time = False

            if valid_time and subtotal >= float(c.min_purchase_amount):
                if c.discount_type == "PERCENTAGE":
                    coupon_disc = round(subtotal * (float(c.discount_value) / 100.0), 2)
                    if c.max_discount_amount and coupon_disc > float(c.max_discount_amount):
                        coupon_disc = float(c.max_discount_amount)
                else:
                    coupon_disc = min(subtotal, float(c.discount_value))
                applied_coupon_label = c.code

    # 4. Apply Eligible Promotions
    promo_disc = 0.0
    applied_promos = []
    now = utc_now()
    all_promos = db.query(Promotion).filter(Promotion.is_active == True).all()

    for p in all_promos:
        p_start = to_naive_utc(p.start_date)
        p_end = to_naive_utc(p.end_date)
        if p_start and now < p_start:
            continue
        if p_end and now > p_end:
            continue
        if subtotal >= float(p.min_order_amount):
            disc = 0.0
            if p.promotion_type == "PERCENTAGE_DISCOUNT":
                disc = round(subtotal * (float(p.discount_value) / 100.0), 2)
            elif p.promotion_type == "FIXED_DISCOUNT":
                disc = min(subtotal, float(p.discount_value))
            if disc > 0:
                promo_disc += disc
                applied_promos.append(f"{p.name} (-${disc:.2f})")

    total_discount = min(subtotal, round(coupon_disc + promo_disc, 2))
    taxable_amount = max(0.0, round(subtotal - total_discount, 2))

    # 5. Calculate Shipping Charges
    shipping_charge = 0.0
    shipping_name = None
    if shipping_method_code:
        sm = db.query(ShippingMethod).filter(
            ShippingMethod.code == shipping_method_code.strip().upper(),
            ShippingMethod.is_active == True
        ).first()
    else:
        # Default to standard ground
        sm = db.query(ShippingMethod).filter(ShippingMethod.is_active == True).order_by(ShippingMethod.base_charge.asc()).first()

    if sm:
        shipping_name = sm.name
        shipping_charge = float(sm.base_charge)
        if sm.free_shipping_threshold and subtotal >= float(sm.free_shipping_threshold):
            shipping_charge = 0.0

    # 6. Calculate Taxes
    tax_rate_pct = 8.0  # Standard fallback
    if shipping_address_id:
        addr = db.query(Address).filter(Address.id == shipping_address_id).first()
        if addr:
            tax_rate_obj = db.query(TaxRate).filter(
                TaxRate.is_active == True,
                TaxRate.state_province == (addr.state_province or "").upper()
            ).first()
            if tax_rate_obj:
                tax_rate_pct = float(tax_rate_obj.rate_percentage)

    tax_amount = round(taxable_amount * (tax_rate_pct / 100.0), 2)

    grand_total = round(subtotal - total_discount + shipping_charge + tax_amount, 2)

    return CartCalculationSummary(
        items=item_details,
        items_count=items_count,
        subtotal_amount=subtotal,
        coupon_discount=coupon_disc,
        promotion_discount=promo_disc,
        total_discount=total_discount,
        tax_amount=tax_amount,
        tax_rate_percent=tax_rate_pct,
        shipping_amount=shipping_charge,
        shipping_method_name=shipping_name,
        grand_total=grand_total,
        applied_coupon=applied_coupon_label,
        applied_promotions=applied_promos
    )


@router.post("", response_model=CartCalculationSummary)
def calculate_checkout_price(
    payload: CartCalculationRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Calculate full price breakdown for current cart: subtotals, discounts, taxes, and shipping.
    Validates prices using current server-side records.
    """
    return calculate_cart_summary(
        db=db,
        user=current_user,
        cart_id=payload.cart_id,
        coupon_code=payload.coupon_code,
        shipping_method_code=payload.shipping_method_code,
        shipping_address_id=payload.shipping_address_id
    )
