from datetime import datetime, timezone, timedelta
from typing import List, Optional
from decimal import Decimal
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.models.user import User
from app.models.product import Product
from app.models.category import Category
from app.models.order import Order, OrderItem
from app.models.warehouse import Warehouse, WarehouseInventory
from app.models.inventory import InventoryItem
from app.models.low_stock import RestockAlert
from app.schemas.analytics import (
    DailySalesMetric, SalesAnalyticsResponse,
    WarehouseStockMetric, InventoryAnalyticsResponse,
    PaymentStatusMetric, PaymentAnalyticsResponse,
    TopProductPerformance, CategoryPerformance, PerformanceAnalyticsResponse
)
from app.core.dependencies import require_permissions
from app.core.permissions import Permission

router = APIRouter(prefix="/analytics", tags=["Module 48: Reports and Analytics APIs"])


def to_naive_utc(dt: Optional[datetime]) -> Optional[datetime]:
    if dt is None:
        return None
    if dt.tzinfo is not None:
        return dt.astimezone(timezone.utc).replace(tzinfo=None)
    return dt


@router.get("/sales", response_model=SalesAnalyticsResponse)
def get_sales_analytics(
    start_date: Optional[datetime] = Query(None, description="Start date (ISO)"),
    end_date: Optional[datetime] = Query(None, description="End date (ISO)"),
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by order status"),
    current_user: User = Depends(require_permissions(Permission.ANALYTICS_READ.value)),
    db: Session = Depends(get_db)
):
    """
    Generate comprehensive sales and order reports.
    Aggregates orders, gross sales, discounts, net sales, and daily trend breakdown.
    """
    query = db.query(Order)
    if status_filter:
        query = query.filter(Order.status == status_filter.upper())
    else:
        query = query.filter(Order.status != "CANCELLED")

    if start_date:
        query = query.filter(Order.created_at >= to_naive_utc(start_date))
    if end_date:
        query = query.filter(Order.created_at <= to_naive_utc(end_date))

    orders = query.all()

    total_gross = Decimal("0.00")
    total_disc = Decimal("0.00")
    total_net = Decimal("0.00")
    daily_map = {}

    for o in orders:
        gross = Decimal(str(o.subtotal_amount))
        disc = Decimal(str(o.discount_amount))
        net = Decimal(str(o.total_amount))

        total_gross += gross
        total_disc += disc
        total_net += net

        day_str = o.created_at.strftime("%Y-%m-%d") if o.created_at else "Unknown"
        if day_str not in daily_map:
            daily_map[day_str] = {
                "orders_count": 0,
                "gross_sales": Decimal("0.00"),
                "discounts": Decimal("0.00"),
                "net_sales": Decimal("0.00")
            }
        daily_map[day_str]["orders_count"] += 1
        daily_map[day_str]["gross_sales"] += gross
        daily_map[day_str]["discounts"] += disc
        daily_map[day_str]["net_sales"] += net

    aov = (total_net / len(orders)) if orders else Decimal("0.00")

    daily_list = [
        DailySalesMetric(
            date=d,
            orders_count=vals["orders_count"],
            gross_sales=vals["gross_sales"],
            discounts=vals["discounts"],
            net_sales=vals["net_sales"]
        ) for d, vals in sorted(daily_map.items())
    ]

    p_start = start_date.strftime("%Y-%m-%d") if start_date else "All-Time"
    p_end = end_date.strftime("%Y-%m-%d") if end_date else "Present"

    return SalesAnalyticsResponse(
        period_start=p_start,
        period_end=p_end,
        total_orders=len(orders),
        total_gross_sales=total_gross,
        total_discounts=total_disc,
        total_net_sales=total_net,
        average_order_value=aov.quantize(Decimal("0.01")),
        daily_breakdown=daily_list
    )


@router.get("/inventory", response_model=InventoryAnalyticsResponse)
def get_inventory_analytics(
    warehouse_id: Optional[int] = Query(None, description="Filter by warehouse ID"),
    current_user: User = Depends(require_permissions(Permission.ANALYTICS_READ.value)),
    db: Session = Depends(get_db)
):
    """
    Generate inventory reports:
    Warehouse-level stock distribution, total units, valuation, and low-stock count.
    """
    warehouses_query = db.query(Warehouse)
    if warehouse_id:
        warehouses_query = warehouses_query.filter(Warehouse.id == warehouse_id)
    warehouses = warehouses_query.all()

    wh_metrics = []
    for wh in warehouses:
        wh_items = db.query(WarehouseInventory).filter(WarehouseInventory.warehouse_id == wh.id).all()
        units = sum(i.quantity for i in wh_items)
        util_pct = (units / wh.capacity_units * 100.0) if wh.capacity_units > 0 else 0.0
        wh_metrics.append(WarehouseStockMetric(
            warehouse_id=wh.id,
            warehouse_code=wh.code,
            warehouse_name=wh.name,
            total_units=units,
            capacity_units=wh.capacity_units,
            utilization_percentage=round(util_pct, 2)
        ))

    inv_items = db.query(InventoryItem).all()
    total_stock_units = sum(i.total_quantity for i in inv_items)

    valuation = Decimal("0.00")
    for inv in inv_items:
        prod = db.query(Product).filter(Product.id == inv.product_id).first()
        if prod:
            price_basis = prod.cost_price if prod.cost_price is not None else prod.base_price
            valuation += Decimal(str(price_basis)) * inv.total_quantity

    low_stock_count = db.query(RestockAlert).filter(RestockAlert.is_resolved == False).count()

    return InventoryAnalyticsResponse(
        total_stock_units=total_stock_units,
        low_stock_variants_count=low_stock_count,
        total_inventory_valuation=valuation,
        warehouse_breakdown=wh_metrics
    )


@router.get("/payments", response_model=PaymentAnalyticsResponse)
def get_payments_analytics(
    current_user: User = Depends(require_permissions(Permission.ANALYTICS_READ.value)),
    db: Session = Depends(get_db)
):
    """
    Generate payment and refund reports.
    Provides payment status breakdowns (PAID, PENDING, REFUNDED).
    """
    orders = db.query(Order).all()
    status_map = {}
    total_trans = Decimal("0.00")

    for o in orders:
        p_status = o.payment_status or "PENDING"
        amt = Decimal(str(o.total_amount))
        total_trans += amt

        if p_status not in status_map:
            status_map[p_status] = {"orders_count": 0, "total_amount": Decimal("0.00")}
        status_map[p_status]["orders_count"] += 1
        status_map[p_status]["total_amount"] += amt

    breakdown = [
        PaymentStatusMetric(
            payment_status=k,
            orders_count=v["orders_count"],
            total_amount=v["total_amount"]
        ) for k, v in status_map.items()
    ]

    return PaymentAnalyticsResponse(
        total_transactions_value=total_trans,
        payment_status_breakdown=breakdown
    )


@router.get("/performance", response_model=PerformanceAnalyticsResponse)
def get_product_category_performance(
    category_id: Optional[int] = Query(None, description="Filter by category ID"),
    limit: int = Query(10, ge=1, le=50),
    current_user: User = Depends(require_permissions(Permission.ANALYTICS_READ.value)),
    db: Session = Depends(get_db)
):
    """
    Generate product and category performance summaries:
    Top-selling products by quantity and revenue, and category revenue share.
    """
    # 1. Product performance
    prod_sales = {}
    order_items = db.query(OrderItem).all()

    for item in order_items:
        pid = item.product_id
        if pid not in prod_sales:
            prod_sales[pid] = {
                "units_sold": 0,
                "total_revenue": Decimal("0.00"),
                "sku": item.sku,
                "name": item.product_name or f"Product #{pid}"
            }
        prod_sales[pid]["units_sold"] += item.quantity
        prod_sales[pid]["total_revenue"] += Decimal(str(getattr(item, 'subtotal', getattr(item, 'total_price', 0))))

    sorted_prods = sorted(prod_sales.items(), key=lambda x: x[1]["total_revenue"], reverse=True)[:limit]

    top_products = [
        TopProductPerformance(
            product_id=pid,
            product_name=data["name"],
            sku=data["sku"],
            units_sold=data["units_sold"],
            total_revenue=data["total_revenue"]
        ) for pid, data in sorted_prods
    ]

    # 2. Category performance
    categories = db.query(Category).all()
    cat_sales = {}
    total_cat_rev = Decimal("0.00")

    for cat in categories:
        cat_prods = db.query(Product).filter(Product.category_id == cat.id).all()
        cat_pids = {p.id for p in cat_prods}
        cat_rev = sum(prod_sales[pid]["total_revenue"] for pid in cat_pids if pid in prod_sales)
        cat_sales[cat.id] = {"name": cat.name, "revenue": cat_rev}
        total_cat_rev += cat_rev

    cat_list = []
    for cid, cdata in cat_sales.items():
        share = float(cdata["revenue"] / total_cat_rev * 100) if total_cat_rev > 0 else 0.0
        cat_list.append(CategoryPerformance(
            category_id=cid,
            category_name=cdata["name"],
            revenue_share_percentage=round(share, 2),
            total_revenue=cdata["revenue"]
        ))

    cat_list = sorted(cat_list, key=lambda x: x.total_revenue, reverse=True)

    return PerformanceAnalyticsResponse(
        top_products=top_products,
        category_performance=cat_list
    )
