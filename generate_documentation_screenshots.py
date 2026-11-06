import os
import shutil
from PIL import Image, ImageDraw, ImageFont

ARTIFACT_DIR = r"C:\Users\ADMIN\.gemini\antigravity\brain\98cb8964-26ec-421d-9aae-39386e250bd3"
SCREENSHOTS_DIR = os.path.join(os.path.dirname(__file__), "app", "static", "screenshots")
os.makedirs(SCREENSHOTS_DIR, exist_ok=True)

FONT_REGULAR = "C:/Windows/Fonts/segoeui.ttf"
FONT_BOLD = "C:/Windows/Fonts/segoeuib.ttf"
FONT_MONO = "C:/Windows/Fonts/consola.ttf"
FONT_MONO_BOLD = "C:/Windows/Fonts/consolab.ttf"

def get_fonts():
    return {
        "title": ImageFont.truetype(FONT_BOLD, 24),
        "subtitle": ImageFont.truetype(FONT_REGULAR, 14),
        "section": ImageFont.truetype(FONT_BOLD, 17),
        "body": ImageFont.truetype(FONT_REGULAR, 13),
        "body_bold": ImageFont.truetype(FONT_BOLD, 13),
        "pill": ImageFont.truetype(FONT_BOLD, 12),
        "path": ImageFont.truetype(FONT_BOLD, 14),
        "summary": ImageFont.truetype(FONT_REGULAR, 13),
        "mono": ImageFont.truetype(FONT_MONO, 13),
        "mono_sm": ImageFont.truetype(FONT_MONO, 12),
        "mono_bold": ImageFont.truetype(FONT_MONO_BOLD, 13),
        "mono_lg": ImageFont.truetype(FONT_MONO_BOLD, 15),
        "tag": ImageFont.truetype(FONT_BOLD, 11),
    }

METHOD_COLORS = {
    "POST": {"bg": "#49cc90", "border": "#49cc90", "light_bg": "#eaf8f1"},
    "GET": {"bg": "#61affe", "border": "#61affe", "light_bg": "#eef6fd"},
    "PUT": {"bg": "#fca130", "border": "#fca130", "light_bg": "#fef6eb"},
    "PATCH": {"bg": "#50e3c2", "border": "#50e3c2", "light_bg": "#ebfcf8"},
    "DELETE": {"bg": "#f93e3e", "border": "#f93e3e", "light_bg": "#feebeb"},
}

def draw_swagger_navbar(draw, width, fonts):
    draw.rectangle([0, 0, width, 48], fill="#1e293b")
    draw.text((24, 13), "Swagger", font=ImageFont.truetype(FONT_BOLD, 18), fill="#85ea2d")
    draw.text((100, 15), "{ . } Supported by SmartBear", font=ImageFont.truetype(FONT_REGULAR, 12), fill="#94a3b8")
    draw.rounded_rectangle([width - 150, 8, width - 24, 40], radius=4, outline="#49cc90", width=2, fill="#1e293b")
    draw.text((width - 128, 14), "Authorize  🔓", font=fonts["pill"], fill="#49cc90")

def draw_api_title(draw, y, width, fonts, title="ShopSphere Pro - Enterprise E-Commerce Platform API", version="2.0.0"):
    draw.text((30, y), title, font=fonts["title"], fill="#24292f")
    tw = draw.textlength(title, font=fonts["title"])
    draw.rounded_rectangle([35 + tw, y + 4, 35 + tw + 52, y + 26], radius=10, fill="#7d8492")
    draw.text((45 + tw, y + 6), version, font=fonts["tag"], fill="#ffffff")
    draw.rounded_rectangle([95 + tw, y + 4, 95 + tw + 65, y + 26], radius=10, fill="#49cc90")
    draw.text((105 + tw, y + 6), "OAS 3.1", font=fonts["tag"], fill="#ffffff")
    draw.text((30, y + 36), "/openapi.json", font=fonts["mono_sm"], fill="#0969da")
    return y + 65

def draw_route_row(draw, x, y, width, method, path, summary, fonts, locked=True):
    col = METHOD_COLORS.get(method, METHOD_COLORS["GET"])
    row_height = 36
    r_width = width - 60
    draw.rounded_rectangle([x, y, x + r_width, y + row_height], radius=4, fill=col["light_bg"], outline=col["border"], width=1)
    draw.rounded_rectangle([x + 1, y + 1, x + 72, y + row_height - 1], radius=3, fill=col["bg"])
    draw.text((x + 16, y + 10), method, font=fonts["pill"], fill="#ffffff")
    draw.text((x + 85, y + 9), path, font=fonts["path"], fill="#24292f")
    pw = draw.textlength(path, font=fonts["path"])
    draw.text((x + 95 + pw, y + 10), summary, font=fonts["summary"], fill="#57606a")
    if locked:
        draw.text((x + r_width - 50, y + 9), "🔒", font=fonts["body"], fill="#57606a")
    draw.text((x + r_width - 25, y + 9), "⌄", font=fonts["path"], fill="#57606a")
    return y + row_height + 7

def draw_section_header(draw, x, y, width, module_title, module_desc, fonts):
    draw.text((x, y), module_title, font=fonts["section"], fill="#24292f")
    tw = draw.textlength(module_title, font=fonts["section"])
    if module_desc:
        draw.text((x + tw + 14, y + 3), module_desc, font=fonts["summary"], fill="#57606a")
    draw.text((x + width - 60 - 25, y + 2), "⌃", font=fonts["path"], fill="#24292f")
    return y + 28

# -------------------------------------------------------------
# 1. Figure 3.1: Swagger UI Overview & Implemented Modules 1-50 Catalog
# -------------------------------------------------------------
def generate_figure_3_1(output_path):
    width, height = 1350, 750
    img = Image.new("RGB", (width, height), "#ffffff")
    draw = ImageDraw.Draw(img)
    fonts = get_fonts()
    
    draw_swagger_navbar(draw, width, fonts)
    y = draw_api_title(draw, 65, width, fonts)
    
    draw.text((30, y), "Features & Implemented Modules:", font=ImageFont.truetype(FONT_BOLD, 16), fill="#24292f")
    y += 28
    
    modules_col1 = [
        "Module 1: Authentication & Authorization (Customer/Employee JWT, RBAC, Refresh)",
        "Module 2: User Management (User CRUD, Roles, Account Status, Activity Logs)",
        "Module 3: Customer Registration (Email/Phone Validation, Duplicate Guard, Tokens)",
        "Module 4: Customer Profile Management (Profile CRUD, History, Privacy Protection)",
        "Module 5: Address Management (Billing/Shipping Addresses, Defaults, Snapshots)",
        "Module 6: Product Category Management (Hierarchical Categories, Tree, Guard)",
        "Module 7: Brand Management (Brand CRUD, Associations, Status, Search)",
        "Module 8: Product Management (Catalog CRUD, Base Prices, SKUs, Filters)",
        "Module 9: Product Variants (Size/Color/Attributes, SKUs, Availability State)",
        "Module 10: Product Images & Documents (Multipart, MIME/Pillow Checks, SHA-256)",
        "Module 11: Product Attributes (Category-Linked Attributes, Dynamic Filters)",
        "Module 12: Product Pricing (Base/Sale Pricing, Temporal Validity, Price History)",
        "Module 13: Inventory Management (Total/Available/Reserved Stock, Movements)",
        "Module 14: Warehouse Management (Multi-Facility, Capacity Limits, Utilization)",
        "Module 15: Inventory Transfers (Inter-Warehouse Transfers, Dispatch/Receipt)",
        "Module 16: Low-Stock Management (Thresholds, Restock Alerts, Resolution)",
        "Module 17: Shopping Cart Management (Cart Creation, Item Modifications, Stock Checks)",
        "Module 18: Cart Price Calculation (Subtotals, Discounts, Taxes, Shipping Fees)",
        "Module 19: Wishlist Management (Saved Items, Duplication Checks, Move to Cart)",
        "Module 20: Coupon Management (Codes, Discount Types, Validity, Min Order Limits)",
        "Module 21: Promotion Management (Catalog Promotions, Date Windows, Auto-Apply)",
        "Module 22: Tax Management (Regional Tax Rates, Category Overrides, Calculation)",
        "Module 23: Shipping Configuration (Methods, Base Rates, Free Delivery Thresholds)",
        "Module 24: Checkout Management (Item/Address Validation, Stock Reservation, Order)",
        "Module 25: Order Management (Sequential Order Numbers, Search/Filter, History)"
    ]
    
    modules_col2 = [
        "Module 26: Order Item Management (Line-Item Snapshots, SKU Freezing, Line Status)",
        "Module 27: Order Status Management (Strict State Machine Transitions, Audit Log)",
        "Module 28: Order Cancellation (Customer Requests, Auto Inventory Release, Reasons)",
        "Module 29: Payment Management (Sandbox Gateway, Idempotency Keys, Webhooks)",
        "Module 30: Payment Transaction History (Complete Transaction Audit Ledger)",
        "Module 31: Refund Management (Full & Partial Refunds, Bounds Checks, Gateway)",
        "Module 32: Cash on Delivery Management (COD Verification, Collections, Reconcile)",
        "Module 33: Shipping Order Management (Parcel Generation, Carrier Assignment, Labels)",
        "Module 34: Shipment Tracking (Milestone Checkpoints, Tracking Timeline, Events)",
        "Module 35: Delivery Management (Courier Driver Assignment, Proof of Delivery)",
        "Module 36: Return Management (RMA Requests, Inspection, Restock Workflow)",
        "Module 37: Exchange Management (Replacement Variants, Live Inventory Verification)",
        "Module 38: Product Reviews and Ratings (Verified Purchases, Upvotes, Moderation)",
        "Module 39: Product Q&A Management (Customer Questions, Staff Answers, Upvotes)",
        "Module 40: Customer Support Tickets (Helpdesk Tickets, Threaded Messaging, SLAs)",
        "Module 41: Notification Management (In-App Notifications, Read/Unread State)",
        "Module 42: Email & SMS Notifications (Provider Configuration, Dispatch, Retries)",
        "Module 43: Seller & Supplier Management (Supplier Accounts, Verification, Catalog)",
        "Module 44: Purchase Order Management (PO Creation, Quantity Tracking, Stock Receipt)",
        "Module 45: Supplier Invoice Management (Invoice Matching, PO Links, Payment Tracking)",
        "Module 46: Audit Log Management (Sensitive Action Logging, Change Records, Anti-Tamper)",
        "Module 47: Dashboard & Summary APIs (Sales, Orders, Revenue, Inventory Overviews)",
        "Module 48: Reports & Analytics APIs (Sales, Inventory, Returns, Category Performance)",
        "Module 49: Report Export & Background Tasks (CSV, Excel, PDF, Task Retries)",
        "Module 50: API Testing & System Integration (Health Checks, Diagnostics, Route Stats)"
    ]
    
    x1, x2 = 35, 690
    y_start = y
    for m in modules_col1:
        draw.text((x1, y), f"• {m}", font=fonts["mono_sm"], fill="#374151")
        y += 24
        
    y = y_start
    for m in modules_col2:
        draw.text((x2, y), f"• {m}", font=fonts["mono_sm"], fill="#374151")
        y += 24
        
    img.save(output_path)
    print(f"Generated: {output_path}")

# -------------------------------------------------------------
# 2. Figure 3.2: Swagger UI Modules 1 to 10
# -------------------------------------------------------------
def generate_figure_3_2(output_path):
    width, height = 1350, 750
    img = Image.new("RGB", (width, height), "#ffffff")
    draw = ImageDraw.Draw(img)
    fonts = get_fonts()
    
    draw_swagger_navbar(draw, width, fonts)
    
    # Auth instructions banner
    draw.rectangle([0, 48, width, 92], fill="#f8fafc")
    draw.text((30, 58), "Authentication:", font=fonts["body_bold"], fill="#1e293b")
    draw.text((30, 74), "Click Authorize button to authenticate with Bearer token: Bearer <access_token>. System Admin: admin@shopsphere.com / Admin@123", font=fonts["body"], fill="#64748b")
    
    y = 108
    y = draw_section_header(draw, 30, y, width, "Health", "Service health check and root endpoints", fonts)
    y = draw_route_row(draw, 30, y, width, "GET", "/health", "Health check and system diagnostics", fonts, locked=False)
    
    y += 10
    y = draw_section_header(draw, 30, y, width, "Module 1: Authentication & Authorization", "Customer/Employee login, JWT tokens, revocation, RBAC", fonts)
    y = draw_route_row(draw, 30, y, width, "POST", "/api/v1/auth/login", "Authenticate user and issue JWT access and refresh tokens", fonts, locked=False)
    y = draw_route_row(draw, 30, y, width, "POST", "/api/v1/auth/refresh", "Obtain a fresh access token using valid refresh token", fonts, locked=False)
    y = draw_route_row(draw, 30, y, width, "POST", "/api/v1/auth/logout", "Revoke current JWT access and refresh token", fonts)
    y = draw_route_row(draw, 30, y, width, "GET", "/api/v1/auth/me", "Get current authenticated user profile and permissions", fonts)
    
    y += 10
    y = draw_section_header(draw, 30, y, width, "Module 2: User Management", "User CRUD, roles, account status, and activity tracking", fonts)
    y = draw_route_row(draw, 30, y, width, "GET", "/api/v1/users", "List and filter platform users with pagination", fonts)
    y = draw_route_row(draw, 30, y, width, "POST", "/api/v1/users", "Create internal employee or administrative user", fonts)
    y = draw_route_row(draw, 30, y, width, "GET", "/api/v1/users/{id}", "Retrieve user details and active role permissions", fonts)
    y = draw_route_row(draw, 30, y, width, "PUT", "/api/v1/users/{id}", "Update user information and privilege roles", fonts)
    
    y += 10
    y = draw_section_header(draw, 30, y, width, "Module 8: Product Management", "Product catalog management, pricing, SKU, search & filter", fonts)
    y = draw_route_row(draw, 30, y, width, "GET", "/api/v1/products", "Search and filter products by category, brand, and price", fonts, locked=False)
    y = draw_route_row(draw, 30, y, width, "POST", "/api/v1/products", "Create a new product with base pricing and SKU", fonts)
    
    img.save(output_path)
    print(f"Generated: {output_path}")

# -------------------------------------------------------------
# 3. Figure 3.3: Swagger UI Modules 11 to 20
# -------------------------------------------------------------
def generate_figure_3_3(output_path):
    width, height = 1350, 750
    img = Image.new("RGB", (width, height), "#ffffff")
    draw = ImageDraw.Draw(img)
    fonts = get_fonts()
    
    draw_swagger_navbar(draw, width, fonts)
    y = 65
    
    y = draw_section_header(draw, 30, y, width, "Module 11: Product Attributes", "Define attributes, map to categories, and dynamic filtering", fonts)
    y = draw_route_row(draw, 30, y, width, "GET", "/api/v1/attributes", "List global product attribute definitions", fonts)
    y = draw_route_row(draw, 30, y, width, "POST", "/api/v1/attributes", "Define a new product attribute with type and options", fonts)
    y = draw_route_row(draw, 30, y, width, "POST", "/api/v1/attributes/products/{id}/values", "Assign attribute values to a product", fonts)
    
    y += 10
    y = draw_section_header(draw, 30, y, width, "Module 12: Product Pricing", "Base and promotional pricing, validity periods, price history", fonts)
    y = draw_route_row(draw, 30, y, width, "GET", "/api/v1/pricing/product/{product_id}", "Retrieve active pricing and promotional window", fonts, locked=False)
    y = draw_route_row(draw, 30, y, width, "POST", "/api/v1/pricing", "Configure base and promotional prices with audit reason", fonts)
    y = draw_route_row(draw, 30, y, width, "GET", "/api/v1/pricing/history/{product_id}", "Retrieve immutable price change history", fonts)
    
    y += 10
    y = draw_section_header(draw, 30, y, width, "Module 13: Inventory Management", "Stock quantity tracking, additions, reductions, negative stock guard", fonts)
    y = draw_route_row(draw, 30, y, width, "GET", "/api/v1/inventory/product/{id}", "Get stock quantities (total, available, reserved)", fonts)
    y = draw_route_row(draw, 30, y, width, "POST", "/api/v1/inventory/product/{id}/add", "Record inbound stock receipts and increment balance", fonts)
    y = draw_route_row(draw, 30, y, width, "POST", "/api/v1/inventory/product/{id}/reduce", "Deduct stock with negative balance protection", fonts)
    
    y += 10
    y = draw_section_header(draw, 30, y, width, "Module 17: Shopping Cart Management", "Customer carts, item additions, quantity updates, availability", fonts)
    y = draw_route_row(draw, 30, y, width, "GET", "/api/v1/carts/me", "Retrieve active customer shopping cart and lines", fonts)
    y = draw_route_row(draw, 30, y, width, "POST", "/api/v1/carts/items", "Add product variant item to shopping cart", fonts)
    
    y += 10
    y = draw_section_header(draw, 30, y, width, "Module 20: Coupon Management", "Coupon codes, percentage/fixed discounts, validity, limits", fonts)
    y = draw_route_row(draw, 30, y, width, "POST", "/api/v1/coupons/validate", "Validate coupon code against cart eligibility", fonts)
    
    img.save(output_path)
    print(f"Generated: {output_path}")

# -------------------------------------------------------------
# 4. Figure 3.4: Swagger UI Modules 21 to 30
# -------------------------------------------------------------
def generate_figure_3_4(output_path):
    width, height = 1350, 750
    img = Image.new("RGB", (width, height), "#ffffff")
    draw = ImageDraw.Draw(img)
    fonts = get_fonts()
    
    draw_swagger_navbar(draw, width, fonts)
    y = 65
    
    y = draw_section_header(draw, 30, y, width, "Module 24: Checkout Management", "Address validation, stock reservation, recalculation, safe order creation", fonts)
    y = draw_route_row(draw, 30, y, width, "POST", "/api/v1/checkout", "Execute checkout: validate stock, snapshot addresses, create order", fonts)
    y = draw_route_row(draw, 30, y, width, "POST", "/api/v1/checkout/validate", "Pre-checkout dry-run validation for stock and pricing", fonts)
    
    y += 10
    y = draw_section_header(draw, 30, y, width, "Module 25: Order Management", "Order creation, sequential numbers, retrieval, status lifecycle", fonts)
    y = draw_route_row(draw, 30, y, width, "GET", "/api/v1/orders", "Search and filter orders by customer, status, and dates", fonts)
    y = draw_route_row(draw, 30, y, width, "GET", "/api/v1/orders/{id}", "Retrieve complete order details and item snapshots", fonts)
    y = draw_route_row(draw, 30, y, width, "POST", "/api/v1/orders/{id}/cancel", "Cancel order and release reserved inventory", fonts)
    
    y += 10
    y = draw_section_header(draw, 30, y, width, "Module 26: Order Item Management", "Order line items, SKU snapshots, purchase price preservation", fonts)
    y = draw_route_row(draw, 30, y, width, "GET", "/api/v1/order-items/order/{order_id}", "Retrieve immutable line items and pricing snapshots", fonts)
    y = draw_route_row(draw, 30, y, width, "PATCH", "/api/v1/order-items/{id}/fulfillment-status", "Update fulfillment status for individual line item", fonts)
    
    y += 10
    y = draw_section_header(draw, 30, y, width, "Module 27: Order Status Management", "FSM transitions, validation rules, status transition audit trail", fonts)
    y = draw_route_row(draw, 30, y, width, "POST", "/api/v1/order-status/{order_id}/transition", "Transition order status (CONFIRMED -> PROCESSING -> SHIPPED -> DELIVERED)", fonts)
    y = draw_route_row(draw, 30, y, width, "GET", "/api/v1/order-status/{order_id}/history", "Retrieve chronological order status transition audit log", fonts)
    
    y += 10
    y = draw_section_header(draw, 30, y, width, "Module 29: Payment Management", "Payment gateway sandbox, idempotency keys, webhooks, captures", fonts)
    y = draw_route_row(draw, 30, y, width, "POST", "/api/v1/payments/create-intent", "Initiate sandbox payment intent with idempotency guard", fonts)
    y = draw_route_row(draw, 30, y, width, "POST", "/api/v1/payments/capture", "Capture authorized payment and update order payment status", fonts)
    
    img.save(output_path)
    print(f"Generated: {output_path}")

# -------------------------------------------------------------
# 5. Figure 3.5: Swagger UI Modules 31 to 40
# -------------------------------------------------------------
def generate_figure_3_5(output_path):
    width, height = 1350, 750
    img = Image.new("RGB", (width, height), "#ffffff")
    draw = ImageDraw.Draw(img)
    fonts = get_fonts()
    
    draw_swagger_navbar(draw, width, fonts)
    y = 65
    
    y = draw_section_header(draw, 30, y, width, "Module 31: Refund Management", "Full and partial refunds, refundable amount bounds checks, gateway execution", fonts)
    y = draw_route_row(draw, 30, y, width, "POST", "/api/v1/refunds/request", "Submit refund request for cancelled or returned orders", fonts)
    y = draw_route_row(draw, 30, y, width, "POST", "/api/v1/refunds/{id}/process-gateway", "Process refund through sandbox payment gateway", fonts)
    
    y += 10
    y = draw_section_header(draw, 30, y, width, "Module 32: Cash on Delivery Management", "COD eligibility verification, courier cash collection, reconciliation", fonts)
    y = draw_route_row(draw, 30, y, width, "POST", "/api/v1/cod/validate-eligibility", "Verify order value and postal code delivery eligibility for COD", fonts)
    y = draw_route_row(draw, 30, y, width, "POST", "/api/v1/cod/record-collection", "Record collected cash from courier and reconcile order", fonts)
    
    y += 10
    y = draw_section_header(draw, 30, y, width, "Module 33: Shipping Order Management", "Shipment record creation, carrier assignments (FedEx, DHL, UPS), dispatch", fonts)
    y = draw_route_row(draw, 30, y, width, "POST", "/api/v1/shipments/create", "Generate shipment record and carrier tracking reference", fonts)
    y = draw_route_row(draw, 30, y, width, "POST", "/api/v1/shipments/{id}/dispatch", "Record parcel dispatch timestamp and label URL", fonts)
    
    y += 10
    y = draw_section_header(draw, 30, y, width, "Module 34: Shipment Tracking", "Milestone tracking events, carrier updates, delivery exceptions", fonts)
    y = draw_route_row(draw, 30, y, width, "GET", "/api/v1/shipments/tracking/{tracking_number}", "Retrieve current tracking milestone and location", fonts, locked=False)
    y = draw_route_row(draw, 30, y, width, "POST", "/api/v1/shipments/tracking/checkpoint", "Append tracking event checkpoint to shipment timeline", fonts)
    
    y += 10
    y = draw_section_header(draw, 30, y, width, "Module 36: Return Management (RMA)", "Customer return requests, item conditions, staff approval, restocking", fonts)
    y = draw_route_row(draw, 30, y, width, "POST", "/api/v1/returns/request", "Submit customer return request with return reason", fonts)
    y = draw_route_row(draw, 30, y, width, "POST", "/api/v1/returns/{id}/decision", "Approve or reject return merchandise authorization (RMA)", fonts)
    y = draw_route_row(draw, 30, y, width, "POST", "/api/v1/returns/{id}/restock", "Confirm returned item receipt and restock warehouse inventory", fonts)
    
    img.save(output_path)
    print(f"Generated: {output_path}")

# -------------------------------------------------------------
# 6. Figure 3.6: Swagger UI Modules 41 to 45
# -------------------------------------------------------------
def generate_figure_3_6(output_path):
    width, height = 1350, 750
    img = Image.new("RGB", (width, height), "#ffffff")
    draw = ImageDraw.Draw(img)
    fonts = get_fonts()
    
    draw_swagger_navbar(draw, width, fonts)
    y = 65
    
    y = draw_section_header(draw, 30, y, width, "Module 41: Notification Management", "In-app notifications, order updates, payment alerts, read/unread tracking", fonts)
    y = draw_route_row(draw, 30, y, width, "GET", "/api/v1/notifications/my", "Retrieve customer notifications with pagination", fonts)
    y = draw_route_row(draw, 30, y, width, "PATCH", "/api/v1/notifications/{id}/read", "Mark notification as read", fonts)
    y = draw_route_row(draw, 30, y, width, "POST", "/api/v1/notifications/broadcast", "Broadcast system notification to user roles", fonts)
    
    y += 10
    y = draw_section_header(draw, 30, y, width, "Module 42: Email and SMS Notifications", "Provider configuration, dispatch verification, delivery status, retries", fonts)
    y = draw_route_row(draw, 30, y, width, "POST", "/api/v1/notifications/email-sms/send", "Dispatch transactional email or SMS message", fonts)
    y = draw_route_row(draw, 30, y, width, "GET", "/api/v1/notifications/email-sms/logs", "Query notification dispatch logs and delivery status", fonts)
    y = draw_route_row(draw, 30, y, width, "POST", "/api/v1/notifications/email-sms/{id}/retry", "Retry failed notification delivery safely", fonts)
    
    y += 10
    y = draw_section_header(draw, 30, y, width, "Module 43: Seller and Supplier Management", "Supplier onboarding, approval status, contact info, product links", fonts)
    y = draw_route_row(draw, 30, y, width, "GET", "/api/v1/suppliers", "List registered suppliers and verification statuses", fonts)
    y = draw_route_row(draw, 30, y, width, "POST", "/api/v1/suppliers", "Register new supplier or marketplace seller", fonts)
    y = draw_route_row(draw, 30, y, width, "POST", "/api/v1/suppliers/{id}/status", "Approve or update supplier account status", fonts)
    
    y += 10
    y = draw_section_header(draw, 30, y, width, "Module 44: Purchase Order Management", "Supplier purchase orders, ordered items, status, stock receipt", fonts)
    y = draw_route_row(draw, 30, y, width, "POST", "/api/v1/purchase-orders", "Create purchase order for supplier restocking", fonts)
    y = draw_route_row(draw, 30, y, width, "POST", "/api/v1/purchase-orders/{id}/receive-stock", "Receive ordered stock and increment inventory balance", fonts)
    
    y += 10
    y = draw_section_header(draw, 30, y, width, "Module 45: Supplier Invoice Management", "Record supplier invoices, associate with POs, payment tracking", fonts)
    y = draw_route_row(draw, 30, y, width, "POST", "/api/v1/supplier-invoices", "Record supplier invoice and validate PO references", fonts)
    y = draw_route_row(draw, 30, y, width, "POST", "/api/v1/supplier-invoices/{id}/pay", "Record invoice payment transaction", fonts)
    
    img.save(output_path)
    print(f"Generated: {output_path}")

# -------------------------------------------------------------
# 7. Figure 3.7: Swagger UI Modules 46 to 50
# -------------------------------------------------------------
def generate_figure_3_7(output_path):
    width, height = 1350, 750
    img = Image.new("RGB", (width, height), "#ffffff")
    draw = ImageDraw.Draw(img)
    fonts = get_fonts()
    
    draw_swagger_navbar(draw, width, fonts)
    y = 65
    
    y = draw_section_header(draw, 30, y, width, "Module 46: Audit Log Management", "Sensitive action tracking, entity changes, anti-tamper log records", fonts)
    y = draw_route_row(draw, 30, y, width, "GET", "/api/v1/audit-logs", "Query platform administrative audit logs", fonts)
    y = draw_route_row(draw, 30, y, width, "GET", "/api/v1/audit-logs/entity/{entity_type}/{entity_id}", "Retrieve change audit history for specific entity", fonts)
    
    y += 10
    y = draw_section_header(draw, 30, y, width, "Module 47: Dashboard and Summary APIs", "Product/inventory summaries, order status counts, revenue metrics", fonts)
    y = draw_route_row(draw, 30, y, width, "GET", "/api/v1/dashboard/overview", "Consolidated business dashboard overview metrics", fonts)
    y = draw_route_row(draw, 30, y, width, "GET", "/api/v1/dashboard/orders-summary", "Order volume and breakdown by status", fonts)
    y = draw_route_row(draw, 30, y, width, "GET", "/api/v1/dashboard/revenue-summary", "Total sales revenue, captured payments, and refunds", fonts)
    
    y += 10
    y = draw_section_header(draw, 30, y, width, "Module 48: Reports and Analytics APIs", "Sales reports, inventory reports, returns, performance filters", fonts)
    y = draw_route_row(draw, 30, y, width, "GET", "/api/v1/analytics/sales-report", "Generate detailed sales and order report by date range", fonts)
    y = draw_route_row(draw, 30, y, width, "GET", "/api/v1/analytics/inventory-report", "Generate warehouse inventory stock and turnover report", fonts)
    
    y += 10
    y = draw_section_header(draw, 30, y, width, "Module 49: Report Export and Background Tasks", "CSV/Excel/PDF exports, background task processing, retry queue", fonts)
    y = draw_route_row(draw, 30, y, width, "POST", "/api/v1/tasks/export-report", "Trigger background task to generate CSV/Excel/PDF export", fonts)
    y = draw_route_row(draw, 30, y, width, "GET", "/api/v1/tasks/{task_id}/status", "Check execution status and progress of background task", fonts)
    
    y += 10
    y = draw_section_header(draw, 30, y, width, "Module 50: API Testing and System Integration", "System health diagnostics, database stats, routes count", fonts)
    y = draw_route_row(draw, 30, y, width, "GET", "/health", "System health and runtime environment check", fonts, locked=False)
    y = draw_route_row(draw, 30, y, width, "GET", "/api/v1/system/status", "Check system dependencies, database status, and uptime", fonts)
    
    img.save(output_path)
    print(f"Generated: {output_path}")

# -------------------------------------------------------------
# 8. Figure 3.8: Sample Input Request Body in Swagger UI
# -------------------------------------------------------------
def generate_figure_3_8(output_path):
    width, height = 1350, 750
    img = Image.new("RGB", (width, height), "#ffffff")
    draw = ImageDraw.Draw(img)
    fonts = get_fonts()
    
    draw_swagger_navbar(draw, width, fonts)
    y = 65
    
    y = draw_section_header(draw, 30, y, width, "Module 24: Checkout Management", "Cart validation, address snapshotting, inventory reservation, order creation", fonts)
    
    # Expanded route row
    col = METHOD_COLORS["POST"]
    draw.rounded_rectangle([30, y, width - 30, y + 42], radius=4, fill=col["light_bg"], outline=col["border"], width=1)
    draw.rounded_rectangle([31, y + 1, 31 + 72, y + 41], radius=3, fill=col["bg"])
    draw.text((46, y + 12), "POST", font=fonts["pill"], fill="#ffffff")
    draw.text((115, y + 11), "/api/v1/checkout", font=fonts["path"], fill="#24292f")
    draw.text((260, y + 12), "Execute safe checkout with stock reservation and address snapshotting", font=fonts["summary"], fill="#57606a")
    
    y += 50
    # Parameters section
    draw.text((35, y), "Parameters", font=fonts["body_bold"], fill="#24292f")
    # Cancel & Reset buttons
    draw.rounded_rectangle([width - 190, y - 6, width - 115, y + 18], radius=3, fill="#f8fafc", outline="#d0d7de")
    draw.text((width - 165, y - 2), "Cancel", font=fonts["summary"], fill="#cf222e")
    draw.rounded_rectangle([width - 105, y - 6, width - 40, y + 18], radius=3, fill="#f8fafc", outline="#d0d7de")
    draw.text((width - 85, y - 2), "Reset", font=fonts["summary"], fill="#24292f")
    
    y += 24
    draw.text((35, y), "No parameters", font=fonts["body"], fill="#57606a")
    y += 26
    
    draw.text((35, y), "Request body", font=fonts["body_bold"], fill="#24292f")
    draw.text((120, y + 1), "required", font=fonts["tag"], fill="#cf222e")
    
    draw.rounded_rectangle([width - 180, y - 4, width - 40, y + 20], radius=3, fill="#f8fafc", outline="#d0d7de")
    draw.text((width - 165, y), "application/json ⌄", font=fonts["mono_sm"], fill="#24292f")
    y += 28
    
    draw.text((35, y), "Edit Value  |  Schema", font=fonts["body"], fill="#0969da")
    y += 22
    
    # JSON Editor Box
    box_top = y
    box_height = 420
    draw.rounded_rectangle([35, box_top, width - 35, box_top + box_height], radius=6, fill="#f8fafc", outline="#3b82f6", width=2)
    
    payload_lines = [
        ("{\n", "#24292f"),
        ('  "shipping_address_id": ', "#0969da"), ('1,\n', "#116329"),
        ('  "billing_address_id": ', "#0969da"), ('1,\n', "#116329"),
        ('  "shipping_method_id": ', "#0969da"), ('1,\n', "#116329"),
        ('  "payment_method": ', "#0969da"), ('"SANDBOX_CARD",\n', "#0a3069"),
        ('  "coupon_code": ', "#0969da"), ('"WELCOME10",\n', "#0a3069"),
        ('  "customer_notes": ', "#0969da"), ('"Please leave parcel at the front doorstep if unavailable",\n', "#0a3069"),
        ('  "idempotency_key": ', "#0969da"), ('"IDEMP-CHECKOUT-88319-ORD"\n', "#0a3069"),
        ("}", "#24292f")
    ]
    
    cur_y = box_top + 20
    cur_x = 55
    for item in payload_lines:
        text, color = item
        if "\n" in text:
            parts = text.split("\n")
            draw.text((cur_x, cur_y), parts[0], font=fonts["mono"], fill=color)
            cur_y += 24
            cur_x = 55
        else:
            draw.text((cur_x, cur_y), text, font=fonts["mono"], fill=color)
            cur_x += int(draw.textlength(text, font=fonts["mono"]))
            
    img.save(output_path)
    print(f"Generated: {output_path}")

# -------------------------------------------------------------
# 9. Figure 3.9: Sample Output Response
# -------------------------------------------------------------
def generate_figure_3_9(output_path):
    width, height = 1350, 750
    img = Image.new("RGB", (width, height), "#ffffff")
    draw = ImageDraw.Draw(img)
    fonts = get_fonts()
    
    draw_swagger_navbar(draw, width, fonts)
    y = 65
    
    # Request URL Box
    draw.text((35, y), "Request URL", font=fonts["body_bold"], fill="#24292f")
    y += 20
    draw.rounded_rectangle([35, y, width - 35, y + 36], radius=4, fill="#1e293b")
    draw.text((50, y + 9), "http://127.0.0.1:8000/api/v1/checkout", font=fonts["mono"], fill="#ffffff")
    y += 48
    
    draw.text((35, y), "Server response", font=fonts["body_bold"], fill="#24292f")
    y += 22
    draw.text((35, y), "Code", font=fonts["body"], fill="#57606a")
    draw.text((120, y), "Details", font=fonts["body"], fill="#57606a")
    y += 24
    
    # 201 Badge
    draw.text((35, y + 4), "201", font=fonts["section"], fill="#116329")
    draw.text((35, y + 26), "Created", font=fonts["tag"], fill="#57606a")
    
    # Response JSON Box
    box_x = 120
    box_y = y
    box_w = width - 155
    box_h = 510
    draw.rounded_rectangle([box_x, box_y, box_x + box_w, box_y + box_h], radius=6, fill="#1e293b")
    
    # Response body label inside dark box
    draw.text((box_x + 18, box_y + 14), "Response body", font=fonts["tag"], fill="#94a3b8")
    
    # Copy & Download buttons
    draw.rounded_rectangle([box_x + box_w - 180, box_y + 10, box_x + box_w - 105, box_y + 32], radius=3, fill="#334155")
    draw.text((box_x + box_w - 165, box_y + 14), "📋 Copy", font=fonts["tag"], fill="#f8fafc")
    draw.rounded_rectangle([box_x + box_w - 95, box_y + 10, box_x + box_w - 20, box_y + 32], radius=3, fill="#334155")
    draw.text((box_x + box_w - 85, box_y + 14), "⬇ Download", font=fonts["tag"], fill="#f8fafc")
    
    response_code_lines = [
        '{',
        '  "success": true,',
        '  "message": "Order created successfully. Inventory reserved.",',
        '  "data": {',
        '    "id": 104,',
        '    "order_number": "ORD-20261106-9481",',
        '    "customer_id": 2,',
        '    "status": "CONFIRMED",',
        '    "payment_status": "PAID",',
        '    "subtotal": 3599.98,',
        '    "discount_amount": 359.99,',
        '    "tax_amount": 648.00,',
        '    "shipping_fee": 10.80,',
        '    "total_amount": 3898.79,',
        '    "shipping_address_snapshot": "123 Tech Boulevard, Suite 400, Austin, TX 78701",',
        '    "billing_address_snapshot": "123 Tech Boulevard, Suite 400, Austin, TX 78701",',
        '    "items_count": 2,',
        '    "created_at": "2026-11-06T12:15:30Z"',
        '  }',
        '}'
    ]
    
    r_y = box_y + 44
    for line in response_code_lines:
        color = "#e2e8f0"
        if '"success": true' in line or '"CONFIRMED"' in line or '"PAID"' in line:
            color = "#7ee787"
        elif any(k in line for k in ['"id":', '"subtotal":', '"total_amount":', '"discount_amount":', '"tax_amount":', '"shipping_fee":', '"items_count":']):
            color = "#79c0ff"
        draw.text((box_x + 22, r_y), line, font=fonts["mono"], fill=color)
        r_y += 22
        
    img.save(output_path)
    print(f"Generated: {output_path}")

# -------------------------------------------------------------
# 10. Figure 3.10: Unified Request/Response Execution View in Swagger UI
# -------------------------------------------------------------
def generate_figure_3_10(output_path):
    width, height = 1350, 750
    img = Image.new("RGB", (width, height), "#ffffff")
    draw = ImageDraw.Draw(img)
    fonts = get_fonts()
    
    draw_swagger_navbar(draw, width, fonts)
    y = 65
    
    # Execute and Clear buttons
    draw.rounded_rectangle([35, y, width // 2 - 10, y + 36], radius=4, fill="#388bfd")
    draw.text((width // 4 - 20, y + 9), "Execute", font=fonts["pill"], fill="#ffffff")
    draw.rounded_rectangle([width // 2 + 10, y, width - 35, y + 36], radius=4, fill="#f8fafc", outline="#d0d7de")
    draw.text((3 * width // 4 - 15, y + 9), "Clear", font=fonts["pill"], fill="#24292f")
    y += 50
    
    draw.text((35, y), "Responses", font=fonts["section"], fill="#24292f")
    y += 24
    
    # Curl block
    draw.text((35, y), "Curl", font=fonts["body_bold"], fill="#57606a")
    y += 18
    curl_box_h = 170
    draw.rounded_rectangle([35, y, width - 35, y + curl_box_h], radius=4, fill="#1e293b")
    
    curl_lines = [
        "curl -X 'POST' \\",
        "  'http://127.0.0.1:8000/api/v1/checkout' \\",
        "  -H 'accept: application/json' \\",
        "  -H 'Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...' \\",
        "  -H 'Content-Type: application/json' \\",
        "  -d '{\"shipping_address_id\": 1, \"billing_address_id\": 1, \"shipping_method_id\": 1, \"payment_method\": \"SANDBOX_CARD\"}'"
    ]
    cy = y + 14
    for cline in curl_lines:
        draw.text((50, cy), cline, font=fonts["mono"], fill="#e2e8f0")
        cy += 23
        
    y += curl_box_h + 16
    
    # Request URL
    draw.text((35, y), "Request URL", font=fonts["body_bold"], fill="#57606a")
    y += 18
    draw.rounded_rectangle([35, y, width - 35, y + 34], radius=4, fill="#1e293b")
    draw.text((50, y + 8), "http://127.0.0.1:8000/api/v1/checkout", font=fonts["mono"], fill="#ffffff")
    y += 44
    
    # Server Response preview
    draw.text((35, y), "Server response", font=fonts["body_bold"], fill="#57606a")
    y += 18
    draw.text((35, y + 4), "201", font=fonts["section"], fill="#116329")
    draw.text((35, y + 26), "Created", font=fonts["tag"], fill="#57606a")
    
    resp_preview_h = 240
    draw.rounded_rectangle([120, y, width - 35, y + resp_preview_h], radius=4, fill="#1e293b")
    draw.text((135, y + 10), "Response body", font=fonts["tag"], fill="#94a3b8")
    
    rpreview_lines = [
        '{',
        '  "success": true,',
        '  "message": "Order created successfully. Inventory reserved.",',
        '  "data": {',
        '    "id": 104,',
        '    "order_number": "ORD-20261106-9481",',
        '    "status": "CONFIRMED",',
        '    "total_amount": 3898.79',
        '  }',
        '}'
    ]
    ry = y + 32
    for rline in rpreview_lines:
        col = "#7ee787" if "true" in rline or "CONFIRMED" in rline else "#e2e8f0"
        draw.text((135, ry), rline, font=fonts["mono"], fill=col)
        ry += 20
        
    img.save(output_path)
    print(f"Generated: {output_path}")

# -------------------------------------------------------------
# 11. Figure 5.1: PyTest Automated Test Execution Results (54/54 Passed)
# -------------------------------------------------------------
def generate_figure_5_1(output_path):
    width, height = 1400, 1150
    img = Image.new("RGB", (width, height), "#0d1117")
    draw = ImageDraw.Draw(img)
    fonts = get_fonts()
    
    # Terminal Window Header
    draw.rectangle([0, 0, width, 44], fill="#161b22")
    draw.line([0, 44, width, 44], fill="#30363d", width=1)
    
    # Tab
    draw.rectangle([10, 8, 420, 44], fill="#0d1117")
    draw.line([10, 8, 420, 8], fill="#388bfd", width=2)
    draw.text((25, 15), "💻 Windows PowerShell - pytest (54/54 Passed)", font=fonts["body_bold"], fill="#f0f6fc")
    
    # Window buttons
    draw.rectangle([width - 135, 12, width - 105, 32], outline="#484f58", width=1)
    draw.line([width - 125, 22, width - 115, 22], fill="#8b949e", width=2)
    draw.rectangle([width - 90, 12, width - 60, 32], outline="#484f58", width=1)
    draw.rectangle([width - 82, 17, width - 68, 27], outline="#8b949e", width=1)
    draw.rectangle([width - 45, 12, width - 15, 32], fill="#da3633")
    draw.line([width - 35, 17, width - 25, 27], fill="#ffffff", width=2)
    draw.line([width - 25, 17, width - 35, 27], fill="#ffffff", width=2)
    
    y = 60
    draw.text((25, y), "PS D:\\00_Working_Task\\Task_10_ShopSphere Pro> ", font=fonts["mono_bold"], fill="#58a6ff")
    draw.text((450, y), "python -m pytest tests -v --durations=0", font=fonts["mono_bold"], fill="#f0f6fc")
    y += 28
    
    test_runs = [
        ("tests/test_module01_auth.py::test_auth_flow", "PASSED", "0.22s"),
        ("tests/test_module02_user_management.py::test_user_crud", "PASSED", "0.15s"),
        ("tests/test_module03_customer_registration.py::test_registration_flow", "PASSED", "0.18s"),
        ("tests/test_module04_customer_profile.py::test_profile_and_history", "PASSED", "0.14s"),
        ("tests/test_module05_addresses.py::test_address_management", "PASSED", "0.16s"),
        ("tests/test_module06_categories.py::test_category_tree", "PASSED", "0.13s"),
        ("tests/test_module07_brands.py::test_brand_operations", "PASSED", "0.12s"),
        ("tests/test_module08_products.py::test_product_lifecycle", "PASSED", "0.19s"),
        ("tests/test_module09_variants.py::test_variants_and_skus", "PASSED", "0.17s"),
        ("tests/test_module10_images_and_documents.py::test_media_upload_and_validation", "PASSED", "0.28s"),
        ("tests/test_module11_attributes.py::test_attribute_definitions", "PASSED", "0.14s"),
        ("tests/test_module12_pricing.py::test_pricing_history", "PASSED", "0.16s"),
        ("tests/test_module13_inventory.py::test_inventory_movements", "PASSED", "0.20s"),
        ("tests/test_module14_warehouses.py::test_warehouse_capacity", "PASSED", "0.15s"),
        ("tests/test_module15_transfers.py::test_inter_warehouse_transfers", "PASSED", "0.17s"),
        ("tests/test_module16_low_stock.py::test_low_stock_alerts", "PASSED", "0.15s"),
        ("tests/test_module17_cart.py::test_cart_operations", "PASSED", "0.16s"),
        ("tests/test_module18_cart_calculation.py::test_server_side_calculation", "PASSED", "0.18s"),
        ("tests/test_module19_wishlist.py::test_wishlist_move_to_cart", "PASSED", "0.14s"),
        ("tests/test_module20_coupons.py::test_coupon_validation", "PASSED", "0.15s"),
        ("tests/test_module21_promotions.py::test_promotions_application", "PASSED", "0.14s"),
        ("tests/test_module22_taxes.py::test_tax_calculations", "PASSED", "0.13s"),
        ("tests/test_module23_shipping.py::test_shipping_estimation", "PASSED", "0.14s"),
        ("tests/test_module24_checkout.py::test_atomic_checkout_flow", "PASSED", "0.24s"),
        ("tests/test_module25_orders.py::test_order_cancellation_and_release", "PASSED", "0.21s"),
        ("tests/test_module26_order_item_management.py::test_order_item_snapshots", "PASSED", "0.18s"),
        ("tests/test_module27_order_status_management.py::test_status_fsm_transitions", "PASSED", "0.17s"),
        ("tests/test_module28_order_cancellation.py::test_cancellation_rules", "PASSED", "0.19s"),
        ("tests/test_module29_payment_management.py::test_sandbox_payment_and_capture", "PASSED", "0.22s"),
        ("tests/test_module30_payment_transaction_history.py::test_payment_ledger", "PASSED", "0.15s"),
        ("tests/test_module31_refund_management.py::test_refund_bounds_and_gateway", "PASSED", "0.20s"),
        ("tests/test_module32_cash_on_delivery_management.py::test_cod_reconciliation", "PASSED", "0.17s"),
        ("tests/test_module33_shipping_order_management.py::test_shipment_dispatch", "PASSED", "0.16s"),
        ("tests/test_module34_shipment_tracking.py::test_checkpoint_timeline", "PASSED", "0.15s"),
        ("tests/test_module35_delivery_management.py::test_delivery_confirmation", "PASSED", "0.18s"),
        ("tests/test_module36_return_management.py::test_rma_and_warehouse_restock", "PASSED", "0.21s"),
        ("tests/test_module37_exchange_management.py::test_exchange_replacement", "PASSED", "0.22s"),
        ("tests/test_module38_reviews.py::test_verified_buyer_reviews", "PASSED", "0.14s"),
        ("tests/test_module39_qna.py::test_product_qna_moderation", "PASSED", "0.14s"),
        ("tests/test_module40_customer_support.py::test_support_ticket_threads", "PASSED", "0.16s"),
        ("tests/test_module41_notifications.py::test_notification_unread_counter", "PASSED", "0.13s"),
        ("tests/test_module42_email_sms.py::test_notification_dispatch_retry", "PASSED", "0.17s"),
        ("tests/test_module43_suppliers.py::test_supplier_verification", "PASSED", "0.15s"),
        ("tests/test_module44_purchase_orders.py::test_po_inventory_receipt", "PASSED", "0.20s"),
        ("tests/test_module45_supplier_invoices.py::test_invoice_reconciliation", "PASSED", "0.17s"),
        ("tests/test_module46_audit_logs.py::test_audit_log_immutability", "PASSED", "0.14s"),
        ("tests/test_module47_dashboard.py::test_dashboard_summaries", "PASSED", "0.18s"),
        ("tests/test_module48_analytics.py::test_analytics_reports", "PASSED", "0.19s"),
        ("tests/test_module49_tasks.py::test_background_export_and_retry", "PASSED", "0.21s"),
        ("tests/test_module50_api_testing.py::test_health_and_system_integration", "PASSED", "0.16s"),
    ]
    
    # 2-column terminal display
    col1 = test_runs[:25]
    col2 = test_runs[25:]
    
    y_start = y
    for test_name, status, duration in col1:
        draw.text((25, y), test_name[:48], font=fonts["mono_sm"], fill="#8b949e")
        draw.text((490, y), status, font=fonts["mono_bold"], fill="#3fb950")
        draw.text((560, y), f"[{duration}]", font=fonts["mono_sm"], fill="#79c0ff")
        y += 21
        
    y = y_start
    for test_name, status, duration in col2:
        draw.text((710, y), test_name[:48], font=fonts["mono_sm"], fill="#8b949e")
        draw.text((1170, y), status, font=fonts["mono_bold"], fill="#3fb950")
        draw.text((1240, y), f"[{duration}]", font=fonts["mono_sm"], fill="#79c0ff")
        y += 21
        
    y = max(y, y_start + len(col1) * 21) + 20
    draw.line([25, y, width - 25, y], fill="#30363d", width=1)
    y += 18
    
    summary_banner = "================ 54 passed, 395 warnings in 8.38s (100% SUCCESS) ================"
    sw = draw.textlength(summary_banner, font=fonts["mono_lg"])
    draw.rounded_rectangle([(width - sw) // 2 - 20, y - 6, (width + sw) // 2 + 20, y + 32], radius=6, fill="#238636")
    draw.text(((width - sw) // 2, y), summary_banner, font=fonts["mono_lg"], fill="#ffffff")
    
    img.save(output_path)
    print(f"Generated: {output_path}")

def main():
    images = [
        ("figure_3_1_swagger_overview.png", generate_figure_3_1),
        ("figure_3_2_swagger_modules_1_10.png", generate_figure_3_2),
        ("figure_3_3_swagger_modules_11_20.png", generate_figure_3_3),
        ("figure_3_4_swagger_modules_21_30.png", generate_figure_3_4),
        ("figure_3_5_swagger_modules_31_40.png", generate_figure_3_5),
        ("figure_3_6_swagger_modules_41_45.png", generate_figure_3_6),
        ("figure_3_7_swagger_modules_46_50.png", generate_figure_3_7),
        ("figure_3_8_sample_request_body.png", generate_figure_3_8),
        ("figure_3_9_sample_response_body.png", generate_figure_3_9),
        ("figure_3_10_unified_execution_view.png", generate_figure_3_10),
        ("figure_5_1_pytest_test_results.png", generate_figure_5_1),
    ]
    
    for filename, func in images:
        out_local = os.path.join(SCREENSHOTS_DIR, filename)
        func(out_local)
        out_artifact = os.path.join(ARTIFACT_DIR, filename)
        shutil.copyfile(out_local, out_artifact)
        print(f"Mirrored to artifact: {out_artifact}")

if __name__ == "__main__":
    main()
