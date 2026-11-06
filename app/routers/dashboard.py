from typing import Dict, Any, Union
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.models.user import User
from app.models.product import Product
from app.models.variant import ProductVariant
from app.models.inventory import InventoryItem
from app.models.order import Order
from app.models.low_stock import RestockAlert, LowStockThreshold
from app.models.supplier import Supplier
from app.models.purchase_order import PurchaseOrder
from app.models.wishlist import WishlistItem
from app.models.notification import Notification
from app.schemas.dashboard import DashboardSummaryResponse, CustomerDashboardResponse
from app.core.dependencies import get_current_user

router = APIRouter(prefix="/dashboard", tags=["Module 47: Dashboard and Summary APIs"])


@router.get("/summary")
def get_dashboard_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Return platform dashboard and summaries with role-based access control:
    - Customers receive personal metrics (orders, total spent, wishlist, unread notifications).
    - Admins and Employees receive full enterprise platform health metrics.
    """
    # 1. Customer Scoped Dashboard
    if current_user.role == "CUSTOMER":
        user_orders = db.query(Order).filter(Order.user_id == current_user.id).all()
        total_orders = len(user_orders)
        active_orders = sum(1 for o in user_orders if o.status in ["CONFIRMED", "PROCESSING", "SHIPPED"])
        total_spent = sum(Decimal(str(o.total_amount)) for o in user_orders if o.status != "CANCELLED")
        
        wishlist_count = db.query(WishlistItem).filter(WishlistItem.user_id == current_user.id).count()
        unread_notifs = db.query(Notification).filter(
            Notification.user_id == current_user.id,
            Notification.is_read == False
        ).count()

        return CustomerDashboardResponse(
            user_id=current_user.id,
            total_orders=total_orders,
            active_orders=active_orders,
            total_spent=Decimal(str(total_spent)),
            wishlist_items_count=wishlist_count,
            unread_notifications_count=unread_notifs
        )

    # 2. Admin & Employee Enterprise Dashboard
    total_prods = db.query(Product).count()
    active_prods = db.query(Product).filter(Product.status == "ACTIVE").count()
    total_vars = db.query(ProductVariant).count()

    # Inventory calculation
    inv_items = db.query(InventoryItem).all()
    total_units = sum(item.total_quantity for item in inv_items)
    
    # Valuation: sum(inv.total_quantity * prod.cost_price or base_price)
    valuation = Decimal("0.00")
    for inv in inv_items:
        prod = db.query(Product).filter(Product.id == inv.product_id).first()
        if prod:
            price_basis = prod.cost_price if prod.cost_price is not None else prod.base_price
            valuation += Decimal(str(price_basis)) * inv.total_quantity

    # Low stock items count
    low_stock_count = db.query(RestockAlert).filter(RestockAlert.is_resolved == False).count()

    # Orders by status
    orders = db.query(Order).all()
    status_counts: Dict[str, int] = {
        "CONFIRMED": 0,
        "PROCESSING": 0,
        "SHIPPED": 0,
        "DELIVERED": 0,
        "CANCELLED": 0
    }
    gross_rev = Decimal("0.00")
    net_rev = Decimal("0.00")
    pending_payments = 0
    paid_orders = 0

    for ord in orders:
        status_counts[ord.status] = status_counts.get(ord.status, 0) + 1
        if ord.status != "CANCELLED":
            gross_rev += Decimal(str(ord.subtotal_amount))
            net_rev += Decimal(str(ord.total_amount))
        if ord.payment_status == "PAID":
            paid_orders += 1
        elif ord.payment_status == "PENDING":
            pending_payments += 1

    # Suppliers and Purchase Orders
    supplier_count = db.query(Supplier).count()
    open_pos = db.query(PurchaseOrder).filter(PurchaseOrder.status.in_(["DRAFT", "SUBMITTED", "PARTIALLY_RECEIVED"])).count()

    return DashboardSummaryResponse(
        total_products=total_prods,
        active_products=active_prods,
        total_variants=total_vars,
        low_stock_count=low_stock_count,
        total_inventory_units=total_units,
        inventory_valuation=Decimal(str(valuation)),
        order_counts_by_status=status_counts,
        total_orders=len(orders),
        gross_revenue=Decimal(str(gross_rev)),
        net_revenue=Decimal(str(net_rev)),
        pending_payments_count=pending_payments,
        paid_orders_count=paid_orders,
        open_restock_alerts=low_stock_count,
        supplier_count=supplier_count,
        open_purchase_orders=open_pos
    )
