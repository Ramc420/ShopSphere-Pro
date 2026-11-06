from typing import Dict, Any, Optional
from decimal import Decimal
from pydantic import BaseModel


class DashboardSummaryResponse(BaseModel):
    # Products & Inventory
    total_products: int
    active_products: int
    total_variants: int
    low_stock_count: int
    total_inventory_units: int
    inventory_valuation: Decimal

    # Orders
    order_counts_by_status: Dict[str, int]
    total_orders: int

    # Revenue & Payments
    gross_revenue: Decimal
    net_revenue: Decimal
    pending_payments_count: int
    paid_orders_count: int

    # Exceptions & Alerts
    open_restock_alerts: int
    supplier_count: int
    open_purchase_orders: int


class CustomerDashboardResponse(BaseModel):
    user_id: int
    total_orders: int
    active_orders: int
    total_spent: Decimal
    wishlist_items_count: int
    unread_notifications_count: int

