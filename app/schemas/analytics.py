from datetime import datetime
from typing import List, Dict, Any, Optional
from decimal import Decimal
from pydantic import BaseModel


class DailySalesMetric(BaseModel):
    date: str
    orders_count: int
    gross_sales: Decimal
    discounts: Decimal
    net_sales: Decimal


class SalesAnalyticsResponse(BaseModel):
    period_start: str
    period_end: str
    total_orders: int
    total_gross_sales: Decimal
    total_discounts: Decimal
    total_net_sales: Decimal
    average_order_value: Decimal
    daily_breakdown: List[DailySalesMetric] = []


class WarehouseStockMetric(BaseModel):
    warehouse_id: int
    warehouse_code: str
    warehouse_name: str
    total_units: int
    capacity_units: int
    utilization_percentage: float


class InventoryAnalyticsResponse(BaseModel):
    total_stock_units: int
    low_stock_variants_count: int
    total_inventory_valuation: Decimal
    warehouse_breakdown: List[WarehouseStockMetric] = []


class PaymentStatusMetric(BaseModel):
    payment_status: str
    orders_count: int
    total_amount: Decimal


class PaymentAnalyticsResponse(BaseModel):
    total_transactions_value: Decimal
    payment_status_breakdown: List[PaymentStatusMetric] = []


class TopProductPerformance(BaseModel):
    product_id: int
    product_name: str
    sku: str
    units_sold: int
    total_revenue: Decimal


class CategoryPerformance(BaseModel):
    category_id: int
    category_name: str
    revenue_share_percentage: float
    total_revenue: Decimal


class PerformanceAnalyticsResponse(BaseModel):
    top_products: List[TopProductPerformance] = []
    category_performance: List[CategoryPerformance] = []

