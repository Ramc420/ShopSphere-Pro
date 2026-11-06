import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.database import Base, engine, SessionLocal, ensure_database_schema
from app.routers import (
    addresses_router,
    attributes_router,
    auth_router,
    brands_router,
    cart_calculation_router,
    carts_router,
    categories_router,
    checkout_router,
    coupons_router,
    inventory_router,
    low_stock_router,
    media_router,
    orders_router,
    pricing_router,
    products_router,
    profiles_router,
    promotions_router,
    registration_router,
    shipping_router,
    taxes_router,
    transfers_router,
    users_router,
    variants_router,
    warehouses_router,
    wishlist_router,
    notifications_router,
    messaging_router,
    suppliers_router,
    purchase_orders_router,
    supplier_invoices_router,
    audit_logs_router,
    dashboard_router,
    analytics_router,
    tasks_router,
    order_items_router,
    order_status_router,
    order_cancellations_router,
    payments_router,
    refunds_router,
    cod_router,
    shipments_router,
    returns_router,
    exchanges_router,
    reviews_router,
    questions_router,
    support_tickets_router,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Ensure database schema is created
    ensure_database_schema(engine)
    
    # Ensure seed data exists
    from seed_data import seed_initial_data
    db = SessionLocal()
    try:
        seed_initial_data(db)
    finally:
        db.close()
        
    yield
    # Shutdown logic if any


app = FastAPI(
    title=settings.APP_NAME,
    description="""
# ShopSphere Pro - Enterprise E-Commerce Platform API

Complete enterprise backend implementation covering Modules 1 through 25:
* **Module 1**: Authentication and Authorization (Customer/employee login, JWT access & refresh tokens, token revocation, bcrypt hashing, RBAC)
* **Module 2**: User Management (User CRUD, roles & permissions, search/filter, account status, user activity tracking)
* **Module 3**: Customer Registration (Customer onboarding, email & phone validation, duplicate prevention, email verification tokens)
* **Module 4**: Customer Profile Management (Profile CRUD, contact info, deactivation requests, profile change audit history, personal info access restrictions)
* **Module 5**: Address Management (Billing & shipping addresses, default address selection, field validation, order address associations)
* **Module 6**: Product Category Management (Hierarchical categories & subcategories, category tree, activation/deactivation, invalid deletion prevention)
* **Module 7**: Brand Management (Brand CRUD, brand-to-product associations, status management, search, products by brand)
* **Module 8**: Product Management (Product CRUD, names, descriptions, base prices, SKU values, category & brand links, search & filter)
* **Module 9**: Product Variants (Size, color, attributes, unique variant SKUs, variant pricing, live stock availability tracking, variant status)
* **Module 10**: Product Images and Documents (Uploads, product & variant associations, MIME & size validation, Pillow resolution check, SHA256 checksums, authorized download & removal)
* **Module 11**: Product Attributes (Size/color/material attributes, category-specific attributes, value validation, attribute-based filtering)
* **Module 12**: Product Pricing (Base & sale prices, price validity periods, price validation, immutable price change history, authorized pricing permissions)
* **Module 13**: Inventory Management (Total, available, reserved stock tracking, stock additions & reductions, negative inventory prevention, movements audit)
* **Module 14**: Warehouse Management (Warehouse facilities, inventory association, capacity and utilization tracking, warehouse-level stock, role restrictions)
* **Module 15**: Inventory Transfers (Transfer stock between warehouses, requests, dispatch & receipt, movement history)
* **Module 16**: Low-Stock Management (Minimum stock thresholds, low-stock identification, restocking alerts, threshold change history, reports)
* **Module 17**: Shopping Cart Management (Create carts, add/remove items, update quantities, cart contents, product availability validation)
* **Module 18**: Cart Price Calculation (Item subtotals, discounts, shipping and taxes, server-side price validation, checkout summary)
* **Module 19**: Wishlist Management (Add/remove wishlist products, retrieve saved items, prevent duplicates, availability validation)
* **Module 20**: Coupon Management (Coupon codes, discount types & values, validity periods, min purchase amounts, activation/deactivation)
* **Module 21**: Promotion Management (Product/category promotions, date ranges, eligibility rules, checkout application, promotion history)
* **Module 22**: Tax Management (Applicable tax rates, product/category rules, checkout calculation, order tax breakdown, history)
* **Module 23**: Shipping Configuration (Shipping methods, charges, delivery eligibility, cost calculation, activation/deactivation)
* **Module 24**: Checkout Management (Cart validation, address confirmation, recalculations, stock validation, safe pending order creation)
* **Module 25**: Order Management (Create orders, unique order numbers, order details, search/filter, status history, cancel release)
    """,
    version="2.0.0",
    lifespan=lifespan
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Static Files & Uploads
static_dir = os.path.join(os.path.dirname(__file__), "app", "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")

# Include Routers for Modules 1 - 25
api_prefix = settings.API_V1_STR
app.include_router(auth_router, prefix=api_prefix)
app.include_router(users_router, prefix=api_prefix)
app.include_router(registration_router, prefix=api_prefix)
app.include_router(profiles_router, prefix=api_prefix)
app.include_router(addresses_router, prefix=api_prefix)
app.include_router(categories_router, prefix=api_prefix)
app.include_router(brands_router, prefix=api_prefix)
app.include_router(products_router, prefix=api_prefix)
app.include_router(variants_router, prefix=api_prefix)
app.include_router(media_router, prefix=api_prefix)
app.include_router(attributes_router, prefix=api_prefix)
app.include_router(pricing_router, prefix=api_prefix)
app.include_router(inventory_router, prefix=api_prefix)
app.include_router(warehouses_router, prefix=api_prefix)
app.include_router(transfers_router, prefix=api_prefix)
app.include_router(low_stock_router, prefix=api_prefix)
app.include_router(carts_router, prefix=api_prefix)
app.include_router(cart_calculation_router, prefix=api_prefix)
app.include_router(wishlist_router, prefix=api_prefix)
app.include_router(coupons_router, prefix=api_prefix)
app.include_router(promotions_router, prefix=api_prefix)
app.include_router(taxes_router, prefix=api_prefix)
app.include_router(shipping_router, prefix=api_prefix)
app.include_router(checkout_router, prefix=api_prefix)
app.include_router(orders_router, prefix=api_prefix)
app.include_router(notifications_router, prefix=api_prefix)
app.include_router(messaging_router, prefix=api_prefix)
app.include_router(suppliers_router, prefix=api_prefix)
app.include_router(purchase_orders_router, prefix=api_prefix)
app.include_router(supplier_invoices_router, prefix=api_prefix)
app.include_router(audit_logs_router, prefix=api_prefix)
app.include_router(dashboard_router, prefix=api_prefix)
app.include_router(analytics_router, prefix=api_prefix)
app.include_router(tasks_router, prefix=api_prefix)
app.include_router(order_items_router, prefix=api_prefix)
app.include_router(order_status_router, prefix=api_prefix)
app.include_router(order_cancellations_router, prefix=api_prefix)
app.include_router(payments_router, prefix=api_prefix)
app.include_router(refunds_router, prefix=api_prefix)
app.include_router(cod_router, prefix=api_prefix)
app.include_router(shipments_router, prefix=api_prefix)
app.include_router(returns_router, prefix=api_prefix)
app.include_router(exchanges_router, prefix=api_prefix)
app.include_router(reviews_router, prefix=api_prefix)
app.include_router(questions_router, prefix=api_prefix)
app.include_router(support_tickets_router, prefix=api_prefix)


@app.get("/", response_class=HTMLResponse, tags=["Dashboard Web UI"])
def get_dashboard():
    """
    Serve the interactive single page application (SPA) dashboard for ShopSphere Pro.
    """
    index_file = os.path.join(static_dir, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    return HTMLResponse("<h1>ShopSphere Pro API running. Visit <a href='/docs'>/docs</a> for Swagger documentation.</h1>")


@app.get("/health", tags=["System"])
def health_check():
    """System health check endpoint."""
    return {
        "status": "healthy",
        "service": settings.APP_NAME,
        "version": "1.1.0",
        "environment": settings.APP_ENV
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
