import json
import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.audit import log_user_activity
from app.core.dependencies import get_client_ip, get_current_user
from app.database import get_db
from app.models.address import Address
from app.models.cart import Cart, CartItem
from app.models.coupon import Coupon, CouponUsage
from app.models.inventory import InventoryItem, StockMovement
from app.models.order import Order, OrderItem, OrderStatusHistory
from app.models.shipping import ShippingMethod
from app.models.user import User
from app.routers.cart_calculation import calculate_cart_summary
from app.schemas.checkout import CheckoutInitRequest, CheckoutSessionResponse

router = APIRouter(prefix="/checkout", tags=["Module 24: Checkout Management"])


def utc_now():
    return datetime.now(timezone.utc)


@router.post("", response_model=CheckoutSessionResponse, status_code=status.HTTP_201_CREATED)
@router.post("/process", response_model=CheckoutSessionResponse, status_code=status.HTTP_201_CREATED, include_in_schema=False)
def process_checkout(
    payload: CheckoutInitRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Safely process customer checkout:
    1. Validates active cart and live stock availability.
    2. Confirms shipping and billing addresses.
    3. Re-evaluates server-side pricing, discounts, taxes, and shipping.
    4. Reserves stock in inventory (preventing negative inventory).
    5. Creates a pending/confirmed Order safely.
    6. Marks cart as CHECKED_OUT.
    """
    # 1. Resolve Cart
    if payload.cart_id:
        cart = db.query(Cart).filter(Cart.id == payload.cart_id, Cart.user_id == current_user.id).first()
    else:
        cart = db.query(Cart).filter(Cart.user_id == current_user.id, Cart.status == "ACTIVE").first()

    if not cart or not cart.items:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot checkout with an empty cart.")

    # 2. Confirm Addresses
    shipping_addr = db.query(Address).filter(Address.id == payload.shipping_address_id, Address.user_id == current_user.id).first()
    if not shipping_addr:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Shipping address not found or does not belong to you.")

    billing_addr = db.query(Address).filter(Address.id == payload.billing_address_id, Address.user_id == current_user.id).first()
    if not billing_addr:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Billing address not found or does not belong to you.")

    # 3. Validate Live Stock Availability
    for item in cart.items:
        inv = db.query(InventoryItem).filter(
            InventoryItem.product_id == item.product_id,
            InventoryItem.variant_id == item.variant_id
        ).first()
        available_qty = inv.available_quantity if inv else 100
        if item.quantity > available_qty:
            prod_title = item.product.name if item.product else f"Product #{item.product_id}"
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Item '{prod_title}' exceeds available inventory. Available: {available_qty}, In Cart: {item.quantity}"
            )

    # 4. Calculate Server-Side Pricing Breakdown
    summary = calculate_cart_summary(
        db=db,
        user=current_user,
        cart_id=cart.id,
        coupon_code=payload.coupon_code,
        shipping_method_code=payload.shipping_method_code,
        shipping_address_id=shipping_addr.id
    )

    # 5. Generate Unique Order Number
    today_str = datetime.now(timezone.utc).strftime("%Y%m%d")
    unique_suffix = uuid.uuid4().hex[:6].upper()
    order_number = f"ORD-{today_str}-{unique_suffix}"

    # Snapshots
    ship_snap = json.dumps({
        "full_name": shipping_addr.full_name,
        "phone": shipping_addr.phone_number,
        "address_line1": shipping_addr.street_line1,
        "city": shipping_addr.city,
        "state": shipping_addr.state_province,
        "postal_code": shipping_addr.postal_code,
        "country": shipping_addr.country
    })
    bill_snap = json.dumps({
        "full_name": billing_addr.full_name,
        "phone": billing_addr.phone_number,
        "address_line1": billing_addr.street_line1,
        "city": billing_addr.city,
        "state": billing_addr.state_province,
        "postal_code": billing_addr.postal_code,
        "country": billing_addr.country
    })

    # 6. Create Order
    order = Order(
        order_number=order_number,
        user_id=current_user.id,
        shipping_address_id=shipping_addr.id,
        billing_address_id=billing_addr.id,
        shipping_address_snapshot=ship_snap,
        billing_address_snapshot=bill_snap,
        status="CONFIRMED",
        payment_status="PENDING",
        subtotal_amount=summary.subtotal_amount,
        discount_amount=summary.total_discount,
        tax_amount=summary.tax_amount,
        shipping_amount=summary.shipping_amount,
        total_amount=summary.grand_total,
        coupon_code=summary.applied_coupon,
        shipping_method_code=payload.shipping_method_code,
        notes=payload.notes
    )
    db.add(order)
    db.flush()

    # 7. Add Order Items & Reserve Inventory
    for line in summary.items:
        order_item = OrderItem(
            order_id=order.id,
            product_id=line.product_id,
            variant_id=line.variant_id,
            product_name=line.product_name,
            sku=line.sku,
            unit_price=line.unit_price,
            quantity=line.quantity,
            subtotal=line.subtotal
        )
        db.add(order_item)

        # Inventory reservation
        inv = db.query(InventoryItem).filter(
            InventoryItem.product_id == line.product_id,
            InventoryItem.variant_id == line.variant_id
        ).first()
        if inv:
            inv.available_quantity -= line.quantity
            inv.reserved_quantity += line.quantity

            movement = StockMovement(
                inventory_item_id=inv.id,
                product_id=line.product_id,
                variant_id=line.variant_id,
                movement_type="RESERVATION",
                quantity=line.quantity,
                balance_after=inv.available_quantity,
                reference_type="ORDER_CHECKOUT",
                reference_id=order.order_number,
                notes=f"Reserved for order {order.order_number}",
                performed_by_user_id=current_user.id
            )
            db.add(movement)

    # 8. Record Order Initial Status History
    status_hist = OrderStatusHistory(
        order_id=order.id,
        from_status=None,
        to_status="CONFIRMED",
        notes="Order placed via checkout",
        changed_by_user_id=current_user.id
    )
    db.add(status_hist)

    # 9. Update Coupon Usage if applied
    if summary.applied_coupon:
        c = db.query(Coupon).filter(Coupon.code == summary.applied_coupon).first()
        if c:
            c.used_count += 1
            usage = CouponUsage(
                coupon_id=c.id,
                user_id=current_user.id,
                order_id=order.id,
                discount_applied=summary.coupon_discount
            )
            db.add(usage)

    # 10. Mark Cart Checked Out
    cart.status = "CHECKED_OUT"
    cart.updated_at = utc_now()

    db.commit()
    db.refresh(order)

    log_user_activity(
        db,
        action="CHECKOUT_COMPLETED",
        user_id=current_user.id,
        ip_address=get_client_ip(request),
        user_agent=request.headers.get("user-agent"),
        details={"order_id": order.id, "order_number": order.order_number, "total": float(order.total_amount)}
    )

    checkout_id = f"CHK-{order.order_number}"
    return CheckoutSessionResponse(
        checkout_id=checkout_id,
        order_id=order.id,
        order_number=order.order_number,
        status=order.status,
        summary=summary,
        created_at=order.created_at
    )
