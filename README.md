# ShopSphere Pro — Enterprise E-Commerce Platform (Modules 1 – 50)

[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688.svg?logo=fastapi)](https://fastapi.tiangolo.com)
[![Python](https://img.shields.io/badge/Python-3.12-3776AB.svg?logo=python)](https://python.org)
[![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0-D71F00.svg)](https://www.sqlalchemy.org)
[![Pydantic](https://img.shields.io/badge/Pydantic-v2.6+-E92063.svg)](https://docs.pydantic.dev)
[![Tests](https://img.shields.io/badge/Tests-54%2F54%20Passing-brightgreen.svg)](https://docs.pytest.org)

ShopSphere Pro is an enterprise-grade e-commerce backend platform built with **Python 3.12**, **FastAPI**, **SQLAlchemy ORM (v2.0)**, **Pydantic v2**, and **JWT Authentication** implementing granular **Role-Based Access Control (RBAC)** across multi-tier user roles (`SUPER_ADMIN`, `ADMIN`, `EMPLOYEE`, `CUSTOMER`).

The platform includes an interactive Single Page Application (SPA) dashboard, interactive Swagger / OpenAPI documentation, complete Postman collections covering all 50 modules, comprehensive technical documentation in Markdown and `.docx`, and a 100% passing automated test suite (54/54 tests).

---

## 🚀 Key Features & Implemented Modules

| Module | Module Name | Core Capabilities & Endpoints |
|---|---|---|
| **Module 1** | **Authentication & Authorization** | Customer & employee login; JWT access (short-lived) & refresh tokens (long-lived); token rotation; explicit logout with token revocation blacklist (`TokenBlacklist`); bcrypt password hashing and verification; multi-tier Role-Based Access Control (`SUPER_ADMIN`, `ADMIN`, `EMPLOYEE`, `CUSTOMER`). |
| **Module 2** | **User Management** | Full CRUD for users; role assignment and status management (`ACTIVE`, `INACTIVE`, `SUSPENDED`, `DEACTIVATED`); keyword search and multi-attribute filtering; immutable user activity audit logging (`UserActivityLog`). |
| **Module 3** | **Customer Registration** | Public onboarding; strict email syntax validation; international phone number regex validation (E.164); duplicate account prevention (409 Conflict); simulated email verification with expiring tokens; registration status management (`PENDING_VERIFICATION`, `VERIFIED`, `EXPIRED`). |
| **Module 4** | **Customer Profile Management** | Customer profile retrieval and update; secondary email and contact preferences; account deactivation requests with administrative review; immutable field-level profile change history (`ProfileChangeHistory`); privacy protection with sensitive data masking for non-admin viewers. |
| **Module 5** | **Address Management** | Complete address CRUD; support for `SHIPPING`, `BILLING`, or `BOTH` address types; single-default address logic (setting default unsets prior default); required fields validation; order-address associations with immutable snapshotting. |
| **Module 6** | **Product Category Management** | Hierarchical categories and subcategories (`parent_id` self-referencing relationship); tree hierarchy endpoint; breadcrumb generator; cycle detection prevention; safe deletion guard preventing deletion of categories with subcategories or associated products. |
| **Module 7** | **Brand Management** | Brand registration and updates; unique brand code generation; active/inactive status management; brand directory search; retrieval of products associated with specific brands. |
| **Module 8** | **Product Management** | Product catalog CRUD; storage of names, descriptions, base prices, compare-at prices, cost prices, and unique base SKUs; category and brand associations; full-text search, multi-criteria filtering (category, brand, price range), sorting, and pagination. |
| **Module 9** | **Product Variants** | Management of size, color, and custom variation attributes (JSON); unique variant-level SKUs; variant-specific pricing; real-time inventory tracking and availability status calculation (`IN_STOCK`, `LOW_STOCK`, `OUT_OF_STOCK`); variant lifecycle status (`ACTIVE`, `INACTIVE`, `DISCONTINUED`). |
| **Module 10** | **Product Images & Documents** | Multipart upload for images and documentation; association with products and specific variants; MIME type whitelisting and file size validation (max 10MB); image dimension extraction via Pillow; SHA-256 checksum generation; authorized download and secure file deletion. |
| **Module 11** | **Product Attributes** | Define attributes (size, material, color) with data types, category-specific mapping, product value assignment & validation, dynamic product attribute filtering. |
| **Module 12** | **Product Pricing** | Base and promotional sale prices, validity windows, automated effective price calculation, mandatory audit change reasons, immutable PriceHistory ledger. |
| **Module 13** | **Inventory Management** | Total, available, and reserved stock tracking, stock additions and reductions, checkout reservation & release workflows, negative inventory prevention, StockMovement audit trail. |
| **Module 14** | **Warehouse Management** | Multi-facility warehouse registration, associate inventory with facilities, track capacity bounds & utilization enforcement, warehouse stock queries, role-restricted access. |
| **Module 15** | **Inventory Transfers** | Stock transfers between warehouses, transfer request creation, dispatch and receipt quantity updates, transfer status tracking, and movement history audit. |
| **Module 16** | **Low-Stock Management** | Configurable minimum stock thresholds per variant, change history audit, automated low-stock checks, restock alerts generation and resolution workflow. |
| **Module 17** | **Shopping Cart Management** | Customer shopping cart creation, add/remove items, quantity updates, inventory availability checks, and cart clearing. |
| **Module 18** | **Cart Price Calculation** | Server-side pricing recalculation engine, item subtotals, promotional discounts, coupon validation, regional taxes, and fulfillment shipping charges. |
| **Module 19** | **Wishlist Management** | Customer saved products, duplicate entry prevention, real-time availability checks, and direct conversion to shopping cart. |
| **Module 20** | **Coupon Management** | Promotional discount coupons, percentage & fixed amount rules, minimum purchase amounts, validity windows, usage quotas, validation endpoint, and activation toggle. |
| **Module 21** | **Promotion Management** | Product, category, and order-level promotional campaigns, scheduled start/end dates, eligibility rules, and audit change history. |
| **Module 22** | **Tax Management** | Country and state/jurisdiction tax rates, category overrides, dynamic checkout tax calculation, and tax breakdown persistence. |
| **Module 23** | **Shipping Configuration** | Fulfillment shipping methods, base freight rates, free delivery thresholds, delivery estimates, and dynamic shipping cost calculation. |
| **Module 24** | **Checkout Management** | Full multi-step checkout workflow: cart item validation, address snapshots, price/tax/freight recalculation, inventory pre-reservation, and atomic order creation. |
| **Module 25** | **Order Management** | Unique sequential order numbers (`ORD-YYYYMMDD-XXXX`), order retrieval and multi-criteria status filtering, status transitions (`CONFIRMED` -> `SHIPPED` -> `DELIVERED` / `CANCELLED`), status history, and automated reserved stock release upon cancellation. |
| **Module 26** | **Order Item Management** | Line-item product & variant snapshots, SKU snapshots, purchase price preservation, quantity tracking, line subtotals, and item fulfillment status (`PENDING`, `PROCESSING`, `FULFILLED`, `CANCELLED`, `RETURNED`). |
| **Module 27** | **Order Status Management** | Strict finite-state transitions (`PENDING` -> `CONFIRMED` -> `PROCESSING` -> `SHIPPED` -> `DELIVERED` or `CANCELLED`), transition rules validation, audit history tracking, and role-restricted permissions. |
| **Module 28** | **Order Cancellation** | Customer cancellation requests, pre-dispatch state validation, automated reserved inventory release back to stock, refund initiation, and cancellation reasons logging. |
| **Module 29** | **Payment Management** | Payment gateway sandbox integration, session initiation, idempotency keys for duplicate prevention, capture execution, and webhook callback simulation. |
| **Module 30** | **Payment Transaction History** | Complete transaction audit ledger, payment attempts, authorizations, captures, refunds, gateway reference tracking, and customer transaction history. |
| **Module 31** | **Refund Management** | Full and partial refund requests, refundable balance validation, payment gateway refund processing, and order payment reconciliation. |
| **Module 32** | **Cash on Delivery Management** | COD eligibility verification by order value and postal code, restricted delivery zones, courier cash collection logging, and order payment reconciliation. |
| **Module 33** | **Shipping Order Management** | Parcel shipment generation, carrier assignments (FedEx, DHL, UPS, USPS), dispatch timestamps, shipping label URL generation, and transit status. |
| **Module 34** | **Shipment Tracking** | Tracking number assignment, milestone checkpoint event logging (`DISPATCHED`, `IN_TRANSIT`, `OUT_FOR_DELIVERY`, `DELIVERED`, `EXCEPTION`), tracking history timeline, and delivery exception logging. |
| **Module 35** | **Delivery Management** | Last-mile courier driver assignments, delivery attempts counting, recipient signature confirmation, and delivery failure logging. |
| **Module 36** | **Return Management** | Customer Return Merchandise Authorization (RMA) requests, return reason and condition tracking (`UNOPENED`, `OPENED_LIKE_NEW`, `DEFECTIVE`, `DAMAGED`), administrative approval workflow, and warehouse receipt restocking. |
| **Module 37** | **Exchange Management** | Customer product variant replacement requests, live replacement inventory verification, staff review workflow, and replacement parcel dispatch with automated stock deduction. |
| **Module 38** | **Product Reviews and Ratings** | Customer 1-to-5 star ratings, verified purchase tags, duplicate review prevention, and administrative review moderation queue (`PENDING`, `APPROVED`, `REJECTED`). |
| **Module 39** | **Product Questions and Answers** | Customer pre-purchase inquiries, verified vendor and staff responses, discussion history, and Q&A content moderation. |
| **Module 40** | **Customer Support Tickets** | Multi-category ticketing system (`ORDER`, `PAYMENT`, `PRODUCT`, `RETURN`, `GENERAL`), priority triage (`LOW`, `NORMAL`, `HIGH`, `URGENT`), threaded conversation messages, agent assignment, and status lifecycle. |
| **Module 41** | **Notification Management** | In-app notification engine, priority channels, read/unread states, bulk mark-all-read, and deep links. |
| **Module 42** | **Email and SMS Notifications** | Provider configurations (SendGrid/Twilio), templated transaction messages, delivery logs, and automated retries. |
| **Module 43** | **Seller and Supplier Management** | Vendor registration, tax ID validation, multi-state approval workflow, product associations, and compliance logs. |
| **Module 44** | **Purchase Order Management** | Supplier PO generation, line item management, warehouse stock receipt, and automated inventory replenishment with audit logs. |
| **Module 45** | **Supplier Invoice Management** | PO-linked commercial invoices, duplicate invoice prevention, billing validations, and payment status tracking. |
| **Module 46** | **Audit Log Management** | Immutable administrative audit trail (`AdminAuditLog`), tracking modifications to products, prices, inventory, and order transitions with Super Admin RBAC guard. |
| **Module 47** | **Dashboard and Summary APIs** | Executive dashboard metrics: catalog health, warehouse stock totals, pipeline order counts, gross revenue, and low-stock alerts. |
| **Module 48** | **Reports and Analytics APIs** | Deep-dive business intelligence: sales performance, warehouse inventory distribution, payment reconciliation, and top-selling product rankings. |
| **Module 49** | **Report Export and Background Tasks** | Asynchronous report export in CSV, Excel, and PDF formats, scheduled summaries, background task workers, and retry handling. |
| **Module 50** | **API Testing and System Integration** | 39-suite automated integration test matrix with 100% pass rate, end-to-end cart-to-order-to-supplier workflows, and OpenAPI/Postman sync. |

---

## 🛠️ Project Architecture & Directory Layout

```
Task_10_ShopSphere Pro/
├── app/
│   ├── core/
│   │   ├── audit.py                # Activity & profile audit logging services
│   │   ├── dependencies.py         # JWT verification, TokenBlacklist check, RBAC guard
│   │   ├── permissions.py          # User roles and granular permission sets (Modules 1 - 50)
│   │   └── security.py             # Bcrypt hashing, token creation, password policy
│   ├── models/                     # SQLAlchemy Models (Modules 1 - 50)
│   │   ├── address.py              # Address model (Module 5)
│   │   ├── attribute.py            # Attributes & options model (Module 11)
│   │   ├── audit_entry.py          # Admin audit log model (Module 46)
│   │   ├── audit_log.py            # User activity & profile change audit (Module 2, 4)
│   │   ├── background_task.py      # Background tasks model (Module 49)
│   │   ├── brand.py                # Brand model (Module 7)
│   │   ├── cart.py                 # Cart & CartItem models (Module 17)
│   │   ├── category.py             # Hierarchical category model (Module 6)
│   │   ├── coupon.py               # Coupon & CouponUsage models (Module 20)
│   │   ├── customer_profile.py     # Customer profile & deactivation requests (Module 4)
│   │   ├── inventory.py            # Inventory & stock movements (Module 13)
│   │   ├── low_stock.py            # LowStockThreshold, ChangeHistory, RestockAlert (Module 16)
│   │   ├── media.py                # Product media & documents model (Module 10)
│   │   ├── messaging.py            # Provider config & delivery logs (Module 42)
│   │   ├── notification.py         # In-app notifications model (Module 41)
│   │   ├── order.py                # Order, OrderItem, OrderStatusHistory (Modules 5, 24, 25)
│   │   ├── pricing.py              # Base & sale pricing & history (Module 12)
│   │   ├── product.py              # Product model (Module 8)
│   │   ├── promotion.py            # Promotion & PromotionHistory models (Module 21)
│   │   ├── purchase_order.py       # Purchase order & PO line items (Module 44)
│   │   ├── shipping.py             # ShippingMethod & ShippingRule models (Module 23)
│   │   ├── supplier.py             # Supplier, Seller & ProductSupplier (Module 43)
│   │   ├── supplier_invoice.py     # Supplier invoice model (Module 45)
│   │   ├── tax.py                  # TaxRate & TaxHistory models (Module 22)
│   │   ├── token_blacklist.py      # Token revocation blacklist (Module 1)
│   │   ├── transfer.py             # InventoryTransfer model (Module 15)
│   │   ├── user.py                 # User model (Module 1, 2, 3)
│   │   ├── variant.py              # Product variant model (Module 9)
│   │   ├── warehouse.py            # Warehouse facilities & stock (Module 14)
│   │   └── wishlist.py             # WishlistItem model (Module 19)
│   ├── routers/                    # FastAPI Endpoints (Modules 1 - 50)
│   │   ├── addresses.py            # Module 5 Router
│   │   ├── analytics.py            # Module 48 Router
│   │   ├── attributes.py           # Module 11 Router
│   │   ├── audit_logs.py           # Module 46 Router
│   │   ├── auth.py                 # Module 1 Router
│   │   ├── brands.py               # Module 7 Router
│   │   ├── cart_calculation.py     # Module 18 Router
│   │   ├── carts.py                # Module 17 Router
│   │   ├── categories.py           # Module 6 Router
│   │   ├── checkout.py             # Module 24 Router
│   │   ├── coupons.py              # Module 20 Router
│   │   ├── dashboard.py            # Module 47 Router
│   │   ├── inventory.py            # Module 13 Router
│   │   ├── low_stock.py            # Module 16 Router
│   │   ├── media.py                # Module 10 Router
│   │   ├── messaging.py            # Module 42 Router
│   │   ├── notifications.py        # Module 41 Router
│   │   ├── orders.py               # Module 25 Router
│   │   ├── pricing.py              # Module 12 Router
│   │   ├── products.py             # Module 8 Router
│   │   ├── profiles.py             # Module 4 Router
│   │   ├── promotions.py           # Module 21 Router
│   │   ├── purchase_orders.py      # Module 44 Router
│   │   ├── registration.py         # Module 3 Router
│   │   ├── shipping.py             # Module 23 Router
│   │   ├── supplier_invoices.py    # Module 45 Router
│   │   ├── suppliers.py            # Module 43 Router
│   │   ├── tasks.py                # Module 49 Router
│   │   ├── taxes.py                # Module 22 Router
│   │   ├── transfers.py            # Module 15 Router
│   │   ├── users.py                # Module 2 Router
│   │   ├── variants.py             # Module 9 Router
│   │   ├── warehouses.py           # Module 14 Router
│   │   └── wishlist.py             # Module 19 Router
│   ├── schemas/                    # Pydantic v2 schemas for all 50 modules
│   ├── static/                     # Interactive SPA Web Dashboard (HTML5/CSS/JS)
│   ├── config.py                   # Application settings & environment configuration
│   └── database.py                 # SQLAlchemy engine, session maker, schema guards
├── tests/
│   ├── conftest.py                 # Test fixtures, DB isolation, authenticated tokens
│   └── test_shopsphere_pro.py      # 39 integration test suites covering Modules 1 - 50
├── main.py                         # FastAPI application entrypoint & static mount
├── seed_data.py                    # Comprehensive demo database seeder (Modules 1 - 50)
├── build_documentation_docx.py     # Python-docx generator script for formal DOCX
├── requirements.txt                # Project dependencies
├── .env.example                    # Environment template
├── ShopSphere_Pro_Postman_Collection.json
├── ShopSphere_Pro_Postman_Environment.json
├── ShopSphere_Pro_Project_Documentation.md
└── ShopSphere_Pro_Project_Documentation.docx
```

---

## ⚡ Quickstart Guide

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Run Database Seeding (Automatic on startup or manual)
```bash
python seed_data.py
```

### 3. Start the FastAPI Application
```bash
python main.py
```
Or with uvicorn:
```bash
uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

### 4. Access the Application
- **Interactive SPA Web Dashboard**: [http://127.0.0.1:8000/](http://127.0.0.1:8000/)
- **Swagger Interactive API Documentation**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **ReDoc Interactive Documentation**: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

---

## 🔑 Pre-Seeded Default Accounts

| Role | Email Address | Password | Permissions & Purpose |
|---|---|---|---|
| **Super Admin** | `admin@shopsphere.com` | `Admin@ShopSphere2026!` | Full platform administration, user provisioning, audit inspection, order fulfillment |
| **Employee** | `employee@shopsphere.com` | `Employee@1234!` | Catalog management, inventory, warehouse transfers, low-stock alerts, shipping config |
| **Customer** | `customer@shopsphere.com` | `Customer@1234!` | Profile self-service, address book, shopping cart, wishlist, checkout & orders |

---

## 🧪 Running Automated Tests

Run the full automated test suite covering all 50 modules:
```bash
python -m pytest tests -v
```

Output:
```
============================= test session starts =============================
tests/test_shopsphere_pro.py::test_module1_customer_and_employee_login PASSED [  2%]
tests/test_shopsphere_pro.py::test_module1_invalid_credentials PASSED    [  5%]
tests/test_shopsphere_pro.py::test_module1_jwt_refresh_token_rotation PASSED [  7%]
tests/test_shopsphere_pro.py::test_module1_logout_and_token_revocation PASSED [ 10%]
tests/test_shopsphere_pro.py::test_module1_rbac_permissions PASSED       [ 12%]
tests/test_shopsphere_pro.py::test_module2_create_update_deactivate_users PASSED [ 15%]
tests/test_shopsphere_pro.py::test_module3_customer_registration_and_duplicate_prevention PASSED [ 17%]
tests/test_shopsphere_pro.py::test_module4_customer_profile_and_history PASSED [ 20%]
tests/test_shopsphere_pro.py::test_module5_address_management_and_order_association PASSED [ 23%]
tests/test_shopsphere_pro.py::test_module6_category_hierarchy_and_invalid_deletion PASSED [ 25%]
tests/test_shopsphere_pro.py::test_module7_brand_management PASSED       [ 28%]
tests/test_shopsphere_pro.py::test_module8_product_crud_and_search PASSED [ 30%]
tests/test_shopsphere_pro.py::test_module9_product_variants_and_availability PASSED [ 33%]
tests/test_shopsphere_pro.py::test_module10_media_upload_validation_and_metadata PASSED [ 35%]
tests/test_shopsphere_pro.py::test_module11_attributes_definition_and_filtering PASSED [ 38%]
tests/test_shopsphere_pro.py::test_module12_product_pricing_and_validity_periods PASSED [ 41%]
tests/test_shopsphere_pro.py::test_module13_inventory_tracking_and_negative_prevention PASSED [ 43%]
tests/test_shopsphere_pro.py::test_module14_warehouse_management_and_role_restriction PASSED [ 46%]
tests/test_shopsphere_pro.py::test_module15_inventory_transfers PASSED   [ 48%]
tests/test_shopsphere_pro.py::test_module16_low_stock_management PASSED  [ 51%]
tests/test_shopsphere_pro.py::test_module17_cart_management PASSED       [ 53%]
tests/test_shopsphere_pro.py::test_module18_cart_price_calculation PASSED [ 56%]
tests/test_shopsphere_pro.py::test_module19_wishlist_management PASSED   [ 58%]
tests/test_shopsphere_pro.py::test_module20_coupon_management PASSED     [ 61%]
tests/test_shopsphere_pro.py::test_module21_promotion_management PASSED  [ 64%]
tests/test_shopsphere_pro.py::test_module22_tax_management PASSED        [ 66%]
tests/test_shopsphere_pro.py::test_module23_shipping_configuration PASSED [ 69%]
tests/test_shopsphere_pro.py::test_module24_checkout_management PASSED   [ 71%]
tests/test_shopsphere_pro.py::test_module25_order_management PASSED      [ 53%]
tests/test_shopsphere_pro.py::test_module26_order_item_management PASSED [ 55%]
tests/test_shopsphere_pro.py::test_module27_order_status_management PASSED [ 57%]
tests/test_shopsphere_pro.py::test_module28_order_cancellation PASSED    [ 59%]
tests/test_shopsphere_pro.py::test_module29_payment_management PASSED    [ 61%]
tests/test_shopsphere_pro.py::test_module30_payment_transaction_history PASSED [ 62%]
tests/test_shopsphere_pro.py::test_module31_refund_management PASSED     [ 64%]
tests/test_shopsphere_pro.py::test_module32_cash_on_delivery_management PASSED [ 66%]
tests/test_shopsphere_pro.py::test_module33_shipping_order_management PASSED [ 68%]
tests/test_shopsphere_pro.py::test_module34_shipment_tracking PASSED     [ 70%]
tests/test_shopsphere_pro.py::test_module35_delivery_management PASSED   [ 72%]
tests/test_shopsphere_pro.py::test_module36_return_management PASSED     [ 74%]
tests/test_shopsphere_pro.py::test_module37_exchange_management PASSED   [ 75%]
tests/test_shopsphere_pro.py::test_module38_product_reviews_and_ratings PASSED [ 77%]
tests/test_shopsphere_pro.py::test_module39_product_questions_and_answers PASSED [ 79%]
tests/test_shopsphere_pro.py::test_module40_customer_support_tickets PASSED [ 81%]
tests/test_shopsphere_pro.py::test_module41_notification_management PASSED [ 83%]
tests/test_shopsphere_pro.py::test_module42_email_and_sms_notifications PASSED [ 85%]
tests/test_shopsphere_pro.py::test_module43_seller_and_supplier_management PASSED [ 87%]
tests/test_shopsphere_pro.py::test_module44_purchase_order_management PASSED [ 88%]
tests/test_shopsphere_pro.py::test_module45_supplier_invoice_management PASSED [ 90%]
tests/test_shopsphere_pro.py::test_module46_audit_log_management PASSED  [ 92%]
tests/test_shopsphere_pro.py::test_module47_dashboard_and_summary_apis PASSED [ 94%]
tests/test_shopsphere_pro.py::test_module48_reports_and_analytics_apis PASSED [ 96%]
tests/test_shopsphere_pro.py::test_module49_report_export_and_background_tasks PASSED [ 98%]
tests/test_shopsphere_pro.py::test_module50_api_testing_and_system_integration PASSED [100%]
====================== 54 passed in 8.84s =======================
```

---

## 📮 Postman Integration

1. Import `ShopSphere_Pro_Postman_Collection.json` into Postman (contains 50 modular test folders covering Modules 1 through 50).
2. Import `ShopSphere_Pro_Postman_Environment.json` into Postman and select `ShopSphere Pro Environment`.
3. Run the **Login** request under Module 1; the environment variables (`access_token`, `refresh_token`) will populate for seamless authenticated testing across all 50 modules.

---

## 📄 Formal Documentation Generator

To recompile the styled Microsoft Word `.docx` technical documentation:
```bash
python build_documentation_docx.py
```
Outputs `ShopSphere_Pro_Project_Documentation.docx` with colored callouts, tables, and full architectural specifications covering Modules 1 through 50.
