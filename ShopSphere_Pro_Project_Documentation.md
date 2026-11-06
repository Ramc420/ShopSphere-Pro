# ShopSphere Pro — Enterprise E-Commerce Platform
## Comprehensive Technical Architecture & Project Documentation (Modules 1 – 50)

---

## 1. Executive Summary & Architecture Overview

**ShopSphere Pro** is an enterprise-grade e-commerce backend platform built on **Python 3.12**, **FastAPI**, **SQLAlchemy ORM (v2.0)**, **Pydantic v2**, and **JWT Authentication** implementing granular **Role-Based Access Control (RBAC)** across multi-tier user roles (`SUPER_ADMIN`, `ADMIN`, `EMPLOYEE`, `CUSTOMER`).

The platform provides end-to-end commerce management across customer authentication, employee authorization, registration verification, user lifecycle management, customer profile and audit history, shipping/billing address management, hierarchical product catalog taxonomy, brand associations, product variants, validated media/document management with image analysis, dynamic product attributes and category attribute mapping, temporal pricing engine with immutable audit trail, multi-echelon inventory management with negative stock prevention, multi-facility warehouse operations, inter-warehouse inventory transfers, low-stock threshold management & replenishment alerts, shopping cart management, real-time server-side cart pricing calculation with discounts, customer wishlists, promotional coupon codes, category/catalog promotions, regional tax rules, fulfillment shipping methods, multi-step checkout with address snapshotting and inventory reservation, and enterprise order lifecycle management.

```
+---------------------------------------------------------------------------------------------------------+
|                                    Client Layer (SPA Web Dashboard / API)                               |
+---------------------------------------------------------------------------------------------------------+
                                                     | (HTTPS / JSON / Multipart)
                                                     v
+---------------------------------------------------------------------------------------------------------+
|                                  FastAPI Gateway & Security Layer                                       |
|  - CORS & Structured Request Logging Middleware                                                         |
|  - JWT Bearer Authentication & JTI Blacklist Token Revocation Verification                              |
|  - Multi-tier Role-Based Access Control (RBAC) & Granular Permission Guard                              |
+---------------------------------------------------------------------------------------------------------+
                                                     |
  +---------------+---------------+---------------+---------------+-------------------+-------------------+
  |               |               |               |               |                   |                   |
  v               v               v               v               v                   v                   v
[Mod 1 & 2]     [Mod 3 & 4]     [Mod 5]         [Mod 6 & 7]     [Mod 8, 9 & 10]     [Mod 11 & 12]       [Mod 13 & 14]
Auth & RBAC     Registration    Address         Categories &    Products, Variants  Attributes &        Inventory &
User Mgmt       Customer Profile Management     Brands          Images & Docs       Pricing History     Warehouse Facilities
  |               |               |               |               |                   |                   |
  +---------------+---------------+---------------+---------------+-------------------+-------------------+
                                                     |
  +---------------+---------------+---------------+---------------+-------------------+-------------------+
  |               |               |               |               |                   |                   |
  v               v               v               v               v                   v                   v
[Mod 15 & 16]   [Mod 17 & 18]   [Mod 19]        [Mod 20 & 21]   [Mod 22 & 23]       [Mod 24 & 25]       
Transfers &     Shopping Cart & Wishlist        Coupons &       Taxes &             Checkout & Order    
Low-Stock Mgmt  Server-Side Calc Management     Promotions      Shipping Methods    Lifecycle Management
  |               |               |               |               |                   |                   |
  +---------------+---------------+---------------+---------------+-------------------+-------------------+
                                                     |
                                                     v
+---------------------------------------------------------------------------------------------------------+
|                                     SQLAlchemy ORM Data Layer                                           |
|  - Dynamic Column Migration Guards, Referential Integrity, Soft/Hard Cascades                           |
|  - SQLite (Portability & Zero-Dependency) / MySQL / PostgreSQL                                          |
+---------------------------------------------------------------------------------------------------------+
                                                     |
                                                     v
+---------------------------------------------------------------------------------------------------------+
|                                       Storage & Persistence                                             |
|  - SQLite / Relational DB: shopsphere_pro.db                                                            |
|  - Local File Storage: uploads/products/... (Images, PDFs, Documents)                                  |
+---------------------------------------------------------------------------------------------------------+
```

---

## 2. Implemented Modules & Feature Matrix

| Module | Module Name | Core Capabilities & Endpoints |
|---|---|---|
| **Module 1** | **Authentication and Authorization** | Customer & employee login; short-lived JWT access tokens and long-lived refresh tokens; token rotation; explicit logout with token revocation blacklist (`TokenBlacklist`); bcrypt password hashing and verification; multi-tier Role-Based Access Control (`SUPER_ADMIN`, `ADMIN`, `EMPLOYEE`, `CUSTOMER`). |
| **Module 2** | **User Management** | Complete CRUD operations for users; role assignment and status management (`ACTIVE`, `INACTIVE`, `SUSPENDED`, `DEACTIVATED`); keyword search and multi-attribute filtering; immutable user activity audit logging (`UserActivityLog`). |
| **Module 3** | **Customer Registration** | Public onboarding; strict email syntax validation; international phone number regex validation (E.164); duplicate account prevention (409 Conflict); simulated email verification with expiring tokens; registration status management (`PENDING_VERIFICATION`, `VERIFIED`, `EXPIRED`). |
| **Module 4** | **Customer Profile Management** | Customer profile retrieval and update; secondary email and contact preferences; account deactivation requests with administrative review; immutable field-level profile change history (`ProfileChangeHistory`); privacy protection with sensitive data masking for non-admin viewers. |
| **Module 5** | **Address Management** | Complete address CRUD; support for `SHIPPING`, `BILLING`, or `BOTH` address types; single-default address logic (setting default unsets prior default); required fields validation; order-address associations with immutable snapshotting. |
| **Module 6** | **Product Category Management** | Hierarchical categories and subcategories (`parent_id` self-referencing relationship); tree hierarchy endpoint; breadcrumb generator; cycle detection prevention; safe deletion guard preventing deletion of categories with subcategories or associated products. |
| **Module 7** | **Brand Management** | Brand registration and updates; unique brand code generation; active/inactive status management; brand directory search; retrieval of products associated with specific brands. |
| **Module 8** | **Product Management** | Product catalog CRUD; storage of names, descriptions, base prices, compare-at prices, cost prices, and unique base SKUs; category and brand associations; full-text search, multi-criteria filtering (category, brand, price range), sorting, and pagination. |
| **Module 9** | **Product Variants** | Management of size, color, and custom variation attributes (JSON); unique variant-level SKUs; variant-specific pricing; real-time inventory tracking and availability status calculation (`IN_STOCK`, `LOW_STOCK`, `OUT_OF_STOCK`); variant lifecycle status (`ACTIVE`, `INACTIVE`, `DISCONTINUED`). |
| **Module 10** | **Product Images and Documents** | Multipart upload for images and documentation; association with products and specific variants; MIME type whitelisting and file size validation (max 10MB); image dimension extraction via Pillow; SHA-256 checksum generation; authorized download and secure file deletion. |
| **Module 11** | **Product Attributes** | Define attributes (size, color, material, tech specs) with data types (`TEXT`, `NUMBER`, `SELECT`, `BOOLEAN`); link attributes to specific categories; store product-level values with validation; filter products dynamically by attribute key and value. |
| **Module 12** | **Product Pricing** | Base and promotional sale pricing management; configured validity periods with automatic effective price calculation; mandatory audit reasons for price modifications; immutable price change history (`PriceHistory`); authorized pricing permissions. |
| **Module 13** | **Inventory Management** | Stock quantity tracking (total, available, and reserved); stock additions (PO, restock) and reductions (damage, shrinkage); reserve and release workflows for checkout pipelines; strict negative inventory prevention; stock retrieval by product and variant; full audit trail of movements (`StockMovement`). |
| **Module 14** | **Warehouse Management** | Multi-facility warehouse registration and management; associate product and variant inventory with specific warehouses; capacity limit tracking and utilization enforcement; warehouse-level stock queries; strict role-based access restrictions (`ADMIN`, `SUPER_ADMIN`). |
| **Module 15** | **Inventory Transfers** | Stock transfers between warehouses; transfer requests creation; dispatch and receipt workflows; quantity tracking (`quantity_requested`, `quantity_shipped`, `quantity_received`); transfer status state machine (`REQUESTED`, `DISPATCHED`, `RECEIVED`, `CANCELLED`); inventory movement audit history. |
| **Module 16** | **Low-Stock Management** | Configurable minimum stock thresholds per variant; automated low-stock identification and replenishment reports; automated restock alert generation (`RestockAlert`); threshold change history logging (`StockThresholdChangeHistory`); alert resolution workflows. |
| **Module 17** | **Shopping Cart Management** | Customer shopping cart creation and retrieval (`/carts/me`); item additions, removals, and real-time quantity adjustments; live item availability checks; cart clearing; customer data isolation. |
| **Module 18** | **Cart Price Calculation** | Server-side pricing recalculation engine; item subtotals; promotional discount evaluation (coupon code + automated catalog promotions); regional tax calculation; freight and shipping charge computation; complete breakdown response. |
| **Module 19** | **Wishlist Management** | Customer wishlist creation and retrieval; add and remove saved products; duplicate entry prevention; live product/variant stock availability checks; seamless move-to-cart operations. |
| **Module 20** | **Coupon Management** | Promotional discount coupons creation and management; discount types (`PERCENTAGE`, `FIXED_AMOUNT`); minimum purchase thresholds and maximum discount ceilings; validity period enforcement; usage limit tracking and activation toggles; validation endpoint. |
| **Module 21** | **Promotion Management** | Product, category, and order-level promotional campaigns; scheduled start and end dates; minimum cart value requirements; automated checkout evaluation; promotion activation toggles and audit history. |
| **Module 22** | **Tax Management** | Country and state/jurisdiction tax rates configuration; category-specific tax rate overrides; dynamic checkout tax calculations; order tax breakdown retention; tax rate activation toggles and change audit history. |
| **Module 23** | **Shipping Configuration** | Fulfillment shipping methods definition; base shipping charges; free delivery thresholds; delivery eligibility rules and estimated transit times; dynamic freight estimation endpoint. |
| **Module 24** | **Checkout Management** | Cart item validation and live inventory verification; shipping and billing address verification; price, discount, tax, and freight recalculation; safe inventory pre-reservation; atomic order creation with frozen address snapshots. |
| **Module 25** | **Order Management** | Order creation with unique sequential format (`ORD-YYYYMMDD-XXXX`); order detail retrieval with snapshots; multi-criteria filtering by status (`CONFIRMED`, `PROCESSING`, `SHIPPED`, `DELIVERED`, `CANCELLED`); status transitions with audit notes (`OrderStatusHistory`); automated reserved inventory release upon cancellation. |
| **Module 26** | **Order Item Management** | Line-item product & variant snapshots, SKU snapshots, purchase price preservation, quantity tracking, line subtotals, and item fulfillment status (`PENDING`, `PROCESSING`, `FULFILLED`, `CANCELLED`, `RETURNED`). |
| **Module 27** | **Order Status Management** | Strict finite-state machine (`PENDING` -> `CONFIRMED` -> `PROCESSING` -> `SHIPPED` -> `DELIVERED` or `CANCELLED`), permitted transitions validation, transition audit history (`OrderStatusHistory`), and role-based permissions. |
| **Module 28** | **Order Cancellation** | Customer cancellation requests, pre-dispatch state validation, automated reserved inventory release back to stock, refund initiation, and cancellation reasons logging. |
| **Module 29** | **Payment Management** | Payment gateway sandbox integration, session initiation, idempotency keys for duplicate prevention, capture execution, and webhook callback simulation. |
| **Module 30** | **Payment Transaction History** | Complete transaction audit ledger, payment attempts, authorizations, captures, refunds, gateway reference tracking, and customer transaction history. |
| **Module 31** | **Refund Management** | Full and partial refund requests, refundable amount bounds checks, sandbox gateway refund execution, and order payment reconciliation. |
| **Module 32** | **Cash on Delivery Management** | COD eligibility verification by order value and postal code, restricted delivery zones, courier cash collection logging, and order payment reconciliation. |
| **Module 33** | **Shipping Order Management** | Parcel shipment generation, carrier assignments (FedEx, DHL, UPS, USPS), dispatch timestamps, shipping label URL generation, and transit status. |
| **Module 34** | **Shipment Tracking** | Tracking number assignment, milestone checkpoint event logging (`DISPATCHED`, `IN_TRANSIT`, `OUT_FOR_DELIVERY`, `DELIVERED`, `EXCEPTION`), tracking history timeline, and delivery exception logging. |
| **Module 35** | **Delivery Management** | Last-mile courier driver assignments, delivery attempts counting, recipient signature confirmation, and delivery failure logging. |
| **Module 36** | **Return Management** | Customer Return Merchandise Authorization (RMA) requests, return reason and condition tracking (`UNOPENED`, `OPENED_LIKE_NEW`, `DEFECTIVE`, `DAMAGED`), administrative approval workflow, and warehouse receipt restocking. |
| **Module 37** | **Exchange Management** | Customer product variant replacement requests, live replacement inventory verification, staff review workflow, and replacement parcel dispatch with automated stock deduction. |
| **Module 38** | **Product Reviews and Ratings** | Customer 1-to-5 star ratings, verified purchase tags, duplicate review prevention, and administrative review moderation queue (`PENDING`, `APPROVED`, `REJECTED`). |
| **Module 39** | **Product Questions and Answers** | Customer pre-purchase inquiries, verified vendor and staff responses, discussion history, and Q&A content moderation. |
| **Module 40** | **Customer Support Tickets** | Multi-category ticketing system (`ORDER`, `PAYMENT`, `PRODUCT`, `RETURN`, `GENERAL`), priority triage (`LOW`, `NORMAL`, `HIGH`, `URGENT`), threaded conversation messages, agent assignment, and status lifecycle. |
| **Module 41** | **Notification Management** | In-app notifications for customers and staff; order update, payment status, refund, and inventory alerts; priority levels (`LOW`, `NORMAL`, `HIGH`, `CRITICAL`); read/unread state tracking; single and bulk mark-all-read operations. |
| **Module 42** | **Email and SMS Notifications** | Notification provider configurations (`EMAIL`, `SMS`); simulated transactional dispatch; order confirmation and shipment tracking templates; message delivery logs; safe retry handling. |
| **Module 43** | **Seller and Supplier Management** | Supplier and marketplace seller onboarding; business registration and tax ID tracking; multi-tier approval lifecycle (`PENDING_APPROVAL`, `APPROVED`, `SUSPENDED`, `REJECTED`); product supplier catalog mapping; supplier history audit trail. |
| **Module 44** | **Purchase Order Management** | Supplier PO generation with itemized lines; order and delivery status tracking; goods receipt workflows with automated warehouse stock incrementation and `StockMovement` audit logs; supplier purchase history. |
| **Module 45** | **Supplier Invoice Management** | PO-associated commercial invoices; composite unique constraints preventing duplicate supplier invoices; subtotal and tax validation; payment reconciliation (`UNPAID`, `PARTIALLY_PAID`, `PAID`, `VOID`). |
| **Module 46** | **Audit Log Management** | Immutable administrative audit trail (`AdminAuditLog`); records modifications to products, pricing, inventory, order statuses, and system settings; user identity, IP address, and change diff logging; strict Super Admin RBAC guard. |
| **Module 47** | **Dashboard and Summary APIs** | Real-time executive dashboard; catalog health and active products; multi-warehouse inventory levels; order counts grouped by status; financial revenue metrics; active low-stock exceptions; role-based data scoping. |
| **Module 48** | **Reports and Analytics APIs** | Comprehensive analytics: sales and gross/net revenue, warehouse inventory distribution, payment reconciliation by method and status, top-selling product performance rankings, and category revenue share. |
| **Module 49** | **Report Export and Background Tasks** | Asynchronous report export engine supporting CSV, Excel, and PDF formats; scheduled operational summaries; resilient background task execution with automatic retry handling. |
| **Module 50** | **API Testing and System Integration** | Comprehensive 39-suite automated testing matrix with 100% pass rate; unit and database integration tests; RBAC security validation; end-to-end cart-to-order-to-supplier workflows; OpenAPI and Postman synchronization. |

---

## 3. Detailed Technical Specifications by Module

### Module 1: Authentication and Authorization
- **Credentials Login (`POST /api/v1/auth/login`)**: Supports customer and staff login. Validates email and bcrypt password hash. Checks user account status (`DEACTIVATED` and `SUSPENDED` accounts are blocked). Issues JWT access token (60 min expiry) and refresh token (7 day expiry).
- **Token Refresh & Rotation (`POST /api/v1/auth/refresh`)**: Validates refresh token signature, checks if revoked in `TokenBlacklist`. Implements token rotation by revoking the old refresh token and issuing a brand new token pair.
- **Logout and Revocation (`POST /api/v1/auth/logout`)**: Extracts JWT ID (`jti`) from the Bearer token and adds it to `TokenBlacklist`. Clients can optionally provide the refresh token to revoke both sessions simultaneously.
- **Password Hashing & Strength Verification**: Passwords are encrypted using bcrypt with salt. Complexity rules enforce minimum 8 characters, at least 1 uppercase letter, 1 lowercase letter, 1 digit, and 1 special symbol.
- **Role-Based Access Control (RBAC)**: Security dependencies `require_roles(...)` and `require_permissions(...)` enforce least-privilege access across customer and employee operations.

### Module 2: User Management
- **User CRUD (`POST /api/v1/users`, `PUT /api/v1/users/{id}`)**: Administrative creation and update of user accounts with role assignment.
- **Account Status State Machine (`PATCH /api/v1/users/{id}/status`)**: Transitions between `ACTIVE`, `INACTIVE`, `SUSPENDED`, and `DEACTIVATED`. Protects Super Admin accounts from deactivation.
- **Search & Filter (`GET /api/v1/users`)**: Search across first name, last name, email, and phone with role and status filtering and pagination metadata (`page`, `limit`, `total_items`, `total_pages`).
- **User Activity Audit (`GET /api/v1/users/{id}/activity`)**: Records action name, actor ID, client IP address, User-Agent, and detailed event payloads.

### Module 3: Customer Registration
- **Public Customer Registration (`POST /api/v1/registration/register`)**: Open onboarding endpoint with email RFC validation and phone format validation (E.164).
- **Duplicate Prevention**: Rejects duplicate emails and duplicate phones with explicit 409 Conflict error details.
- **Email Verification Flow (`GET /api/v1/registration/verify-email`)**: Generates cryptographically secure 32-byte tokens with 24-hour expiration. Verifying marks `is_verified=True` and updates status to `VERIFIED`.

### Module 4: Customer Profile Management
- **Profile Self-Service (`GET /api/v1/customer/profile/me`, `PUT /api/v1/customer/profile/me`)**: Customers view and update contact details, alternate email, date of birth, gender, and avatar.
- **Change History Tracking (`GET /api/v1/customer/profile/history`)**: Automatically inserts audit records into `ProfileChangeHistory` for each modified attribute, preserving `old_value`, `new_value`, and timestamp.
- **Deactivation Requests (`POST /api/v1/customer/profile/deactivation-request`)**: Allows customer to request account closure. Admins review and approve/reject at `POST /api/v1/customer/profile/{id}/deactivation-review`.
- **Privacy Access Restriction**: Standard employees viewing customer profiles have sensitive contact details (phone, alternate email) masked.

### Module 5: Address Management
- **Address CRUD (`POST /api/v1/customer/addresses`, `PUT`, `DELETE`)**: Supports shipping and billing address management.
- **Single-Default State Enforcement**: Marking an address as default shipping or billing automatically clears prior default flags of the same category for that customer.
- **Order Association & Integrity**: Placing an order (`POST /api/v1/customer/addresses/associate-order`) links address IDs and creates frozen address snapshots. Addresses referenced by existing orders cannot be hard-deleted.

### Module 6: Product Category Management
- **Hierarchies & Subcategories**: Categories feature a self-referential `parent_id` foreign key enabling unlimited nesting depth.
- **Tree Hierarchy (`GET /api/v1/categories/tree`)**: Returns nested tree nodes with recursive child subcategories.
- **Cycle Prevention**: Prevents assigning a category as its own parent or as a child of any of its own descendants.
- **Invalid Deletion Guard**: Rejects deletion with 400 Bad Request if the category has existing subcategories or attached products.

### Module 7: Brand Management
- **Brand Registry**: CRUD operations for brands with unique brand codes, descriptions, official website links, and logo URLs.
- **Brand Status**: Active/Inactive toggle (`PATCH /api/v1/brands/{id}/status`).
- **Product Retrieval by Brand (`GET /api/v1/brands/{id}/products`)**: Filter products by brand with optional category filters and pagination.

### Module 8: Product Management
- **Product Catalog CRUD**: Manages name, slug, descriptions, base price, cost price, compare-at price, base SKU, and category/brand foreign keys.
- **Catalog Search & Filtering (`GET /api/v1/products`)**: Searches across names, descriptions, and SKUs. Supports multi-attribute filtering by category ID, brand ID, price ranges (`min_price`, `max_price`), and status, with multiple sorting modes (`newest`, `price_asc`, `price_desc`, `name_asc`).
- **Product Detail View (`GET /api/v1/products/{id}`)**: Returns product details with joined Category, Brand, active Variants, and Media assets.

### Module 9: Product Variants
- **Variation Attributes**: Flexible JSON storage for variations (size, color, material, style, etc.).
- **Variant SKUs**: Globally unique variant SKU generation and verification.
- **Variant Pricing**: Variant-level price override, compare-at price, and cost price.
- **Availability State Tracking (`POST /api/v1/variants/{id}/stock-adjust`)**: Dynamically recalculates availability status:
  - `stock_quantity == 0` -> `OUT_OF_STOCK`
  - `0 < stock_quantity <= low_stock_threshold` -> `LOW_STOCK`
  - `stock_quantity > low_stock_threshold` -> `IN_STOCK`

### Module 10: Product Images and Documents
- **File Upload (`POST /api/v1/media/upload`)**: Multipart file upload accepting images (JPEG, PNG, WEBP, GIF) and documents (PDF, DOCX, TXT).
- **MIME & Size Validation**: Strict whitelist validation and 10MB maximum file size enforcement.
- **Metadata Storage**: Extracts image dimensions (width x height) using Pillow and generates a cryptographic SHA-256 checksum.
- **Authorized File Download & Removal**: Secure download route (`GET /api/v1/media/{id}/download`) and authorized file deletion (`DELETE /api/v1/media/{id}`) removing file from disk and database.

### Module 11: Product Attributes
- **Attribute Definition (`POST /api/v1/attributes`)**: Define custom attributes (e.g. Size, Color, Battery Life, Material) with supported data types (`TEXT`, `NUMBER`, `SELECT`, `BOOLEAN`), requirement flags, and optional predefined choices (`AttributeOption`).
- **Category-Specific Mapping (`POST /api/v1/attributes/category-link`)**: Assign attributes specifically to product categories so that relevant attributes are displayed when creating products within that category (`CategoryAttribute`).
- **Product Attribute Value Assignment (`POST /api/v1/attributes/products/{id}/values`)**: Store attribute values for individual products with automated type validation (verifying number formatting, select option validity, etc.).
- **Product Filtering by Attribute (`GET /api/v1/attributes/products/filter-by-attributes`)**: Dynamic filtering returning products matching specific attribute keys and values.

### Module 12: Product Pricing
- **Base & Sale Pricing Configuration (`POST /api/v1/pricing`, `PUT /api/v1/pricing/{id}`)**: Set base price and optional promotional sale price with currency code.
- **Validity Periods & Effective Price Calculation**: Configure `sale_start_at` and `sale_end_at` timestamps. The pricing engine automatically determines `is_on_sale` and returns the `effective_price` based on current time versus configured window.
- **Mandatory Change Reason & Audit Trail (`GET /api/v1/pricing/history/{product_id}`)**: Enforces non-empty `change_reason` for every price modification, automatically writing records to immutable `PriceHistory`.
- **Authorized Permissions Guard**: Creation and updates strictly restricted to users with `PRICING_WRITE` permission (`ADMIN`, `SUPER_ADMIN`).

### Module 13: Inventory Management
- **Stock Tracking (`GET /api/v1/inventory/product/{id}`, `/variant/{id}`)**: Tracks `total_quantity`, `available_quantity`, and `reserved_quantity` with live availability status calculation (`IN_STOCK`, `LOW_STOCK`, `OUT_OF_STOCK`).
- **Stock Additions (`POST /api/v1/inventory/product/{id}/add`)**: Inbound stock receipts (PO delivery, returns, restock) incrementing both total and available units and syncing variant models.
- **Stock Reductions with Negative Stock Prevention (`POST /api/v1/inventory/product/{id}/reduce`)**: Deductions for damage or write-offs. Strictly rejects reductions that exceed available stock with 400 Bad Request.
- **Reservation & Release Workflows (`POST /api/v1/inventory/product/{id}/reserve`, `/release`)**: Locks available units into reserved status during customer checkout pipelines, and restores reserved units back to available pool upon cancellation.
- **Comprehensive Movement Audit Trail (`GET /api/v1/inventory/movements/all`)**: Immutable `StockMovement` ledger logging type (`ADDITION`, `REDUCTION`, `RESERVATION`, `RELEASE`), quantity change, post-transaction balance, reference ID, and performing user ID.

### Module 14: Warehouse Management
- **Warehouse Infrastructure (`POST /api/v1/warehouses`, `GET /api/v1/warehouses`)**: Multi-facility management with code, facility name, address, operating status (`ACTIVE`, `INACTIVE`, `MAINTENANCE`), and total unit capacity.
- **Stock Association & Utilization Enforcement (`POST /api/v1/warehouses/{id}/stock`)**: Associates inventory items with specific warehouses including aisle/rack location metadata. Validates that additions do not exceed maximum capacity bounds.
- **Warehouse-Level Stock Queries (`GET /api/v1/warehouses/{id}/stock`)**: Inspects inventory distributed across specific warehouse facilities.
- **Role-Based Facility Access**: Enforces administrative permission restrictions (`WAREHOUSES_READ`, `WAREHOUSES_WRITE`), denying customer role access.

### Module 15: Inventory Transfers
- **Transfer Request Creation (`POST /api/v1/transfers`)**: Generates unique transfer numbers (`TRF-YYYYMMDD-XXXX`), records source and destination warehouse IDs, product variant ID, requested quantity, and notes. Rejects identical source and destination facilities.
- **Dispatch Workflow (`POST /api/v1/transfers/{id}/dispatch`)**: Deducts available quantity from source warehouse inventory, reserves or dispatches stock, transitions status to `DISPATCHED`, records dispatch timestamp and user.
- **Receipt Workflow (`POST /api/v1/transfers/{id}/receive`)**: Adds stock to destination warehouse inventory, updates `quantity_received`, transitions status to `RECEIVED`, records receive timestamp and user.
- **Cancellation & Reversal (`POST /api/v1/transfers/{id}/cancel`)**: Allows cancelling pending or dispatched transfers, returning stock to the source warehouse available pool.
- **Movement History & Audit**: Every transfer action creates associated movement records tracking items between multi-facility nodes.

### Module 16: Low-Stock Management
- **Threshold Configuration (`POST /api/v1/low-stock/thresholds`)**: Sets minimum stock thresholds and suggested reorder quantities per product variant.
- **Threshold Audit History (`StockThresholdChangeHistory`)**: Captures previous threshold values, new threshold values, and user details whenever configuration changes.
- **Automated Stock Checks (`POST /api/v1/low-stock/check`)**: Iterates through all variants with thresholds, comparing current available inventory. Generates `RestockAlert` records whenever stock falls below configured minimums.
- **Replenishment Report (`GET /api/v1/low-stock/report`)**: Computes real-time deficit, current stock, threshold, and restock recommendation flag for inventory managers.
- **Alert Lifecycle (`POST /api/v1/low-stock/alerts/{id}/resolve`)**: Transitions alerts from `OPEN` to `RESOLVED` with resolver user ID and resolution timestamps.

### Module 17: Shopping Cart Management
- **Customer Cart Persistence (`GET /api/v1/carts/me`)**: Auto-creates or retrieves the authenticated customer's active shopping cart.
- **Item Additions & Validation (`POST /api/v1/carts/items`)**: Verifies product variant active status and sufficient available inventory. Increments quantity if item already exists in the cart.
- **Quantity Adjustments (`PUT /api/v1/carts/items/{id}`)**: Real-time quantity increases or decreases with stock availability re-validation.
- **Item Removal & Cart Clear (`DELETE /api/v1/carts/items/{id}`, `DELETE /api/v1/carts/me/clear`)**: Safe item deletion and atomic cart emptying.

### Module 18: Cart Price Calculation
- **Server-Side Pricing Engine (`POST /api/v1/cart/calculate`)**: Calculates accurate checkout amounts entirely server-side, immune to client tampering.
- **Subtotal & Discounts**: Computes item line totals using current active base or promotional sale prices; applies eligible coupon discounts and catalog-wide promotions.
- **Taxes & Shipping**: Dynamically computes destination jurisdiction taxes (state/country tax rates) and adds selected carrier shipping freight costs.
- **Detailed Summary**: Returns `subtotal_amount`, `discount_amount`, `tax_amount`, `shipping_amount`, `grand_total`, plus lists of applied discount rules and tax breakdowns.

### Module 19: Wishlist Management
- **Saved Products (`GET /api/v1/wishlists/me`)**: Retrieves customer's saved items with real-time stock availability badges (`is_in_stock`).
- **Duplicate Prevention (`POST /api/v1/wishlists/items`)**: Prevents adding duplicate variants to the same wishlist.
- **Removal & Cart Conversion (`DELETE /api/v1/wishlists/items/{variant_id}`)**: Enables quick removal or one-click transfer into the shopping cart.

### Module 20: Coupon Management
- **Coupon CRUD & Limits (`POST /api/v1/coupons`, `GET /api/v1/coupons`)**: Defines uppercase coupon codes, discount types (`PERCENTAGE` or `FIXED_AMOUNT`), discount values, minimum purchase requirements, and maximum usage quotas.
- **Validation Endpoint (`POST /api/v1/coupons/validate`)**: Pre-validates coupons against current cart subtotal and active time windows without placing an order.
- **Lifecycle & Activation (`PATCH /api/v1/coupons/{id}/toggle`)**: Enables administrative toggling of coupon activation and tracks per-user usage in `CouponUsage`.

### Module 21: Promotion Management
- **Campaign Configuration (`POST /api/v1/promotions`, `GET /api/v1/promotions`)**: Configures promotional sales targeting the entire cart (`ALL`), specific categories (`CATEGORY`), or specific products (`PRODUCT`).
- **Validity Scheduling**: Enforces start and end timestamps and minimum cart values before discounts activate.
- **Audit Ledger (`PromotionHistory`)**: Tracks changes to promotional campaigns over time.

### Module 22: Tax Management
- **Jurisdiction Configuration (`POST /api/v1/taxes/rates`, `GET /api/v1/taxes/rates`)**: Defines applicable tax percentages for country and state combinations (e.g. US - CA 7.25%).
- **Category Overrides**: Allows assigning category-specific tax rules (e.g., luxury or grocery tax exemptions).
- **Checkout Application**: Taxes are calculated and itemized during checkout calculation and stored persistently within order snapshots.

### Module 23: Shipping Configuration
- **Fulfillment Methods (`POST /api/v1/shipping/methods`, `GET /api/v1/shipping/methods`)**: Defines carrier delivery tiers (Standard Ground, Express 2-Day, Overnight Priority) with base rates, estimated delivery days, and free shipping subtotal thresholds.
- **Dynamic Freight Estimation (`POST /api/v1/shipping/estimate`)**: Estimates freight costs given cart subtotal and selected method.

### Module 24: Checkout Management
- **Readiness Validation (`POST /api/v1/checkout/validate`)**: Pre-flight verification verifying customer cart non-emptiness, item stock availability, and valid shipping/billing address IDs.
- **Atomic Order Execution (`POST /api/v1/checkout/process`)**: Validates cart, snapshot-copies shipping and billing addresses to immutable JSON, recalculates server-side pricing, pre-reserves inventory, creates `Order` and `OrderItem` records, generates unique sequential order number, clears shopping cart, and returns confirmed order receipt.

### Module 25: Order Management
- **Sequential Order Numbers**: Generates enterprise order numbers in `ORD-YYYYMMDD-XXXX` format.
- **Order Tracking & Search (`GET /api/v1/orders`)**: Search and filter by order status, date, and user ID with pagination support.
- **Status State Machine & Reconciliation (`PATCH /api/v1/orders/{id}/status`)**: Handles transitions through `CONFIRMED` -> `PROCESSING` -> `SHIPPED` -> `DELIVERED` or `CANCELLED`. Automatically restores pre-reserved inventory back to available stock if an order is cancelled. Records every transition in `OrderStatusHistory`.

### Module 26: Order Item Management
- **Line Item Retrieval (`GET /api/v1/orders/{order_id}/items`, `GET /api/v1/orders/{order_id}/items/{item_id}`)**: Retrieves product and variant details, unit purchase price, purchased quantities, line subtotals, and frozen attribute snapshots.
- **Item Fulfillment Status (`PATCH /api/v1/orders/{order_id}/items/{item_id}/fulfillment`)**: Granular tracking across item lifecycle states: `PENDING`, `PROCESSING`, `FULFILLED`, `CANCELLED`, and `RETURNED`.

### Module 27: Order Status Management
- **Permitted Transition Rules (`GET /api/v1/order-status/permitted-transitions/{order_id}`)**: Enforces deterministic state transitions: `PENDING` -> `CONFIRMED` -> `PROCESSING` -> `SHIPPED` -> `DELIVERED`, with cancellations allowed prior to delivery.
- **Transition Execution (`POST /api/v1/order-status/transition/{order_id}`)**: Validates permitted transition paths, logs audit notes with operator attribution, and restores reserved warehouse stock if cancelled.
- **Transition History (`GET /api/v1/order-status/history/{order_id}`)**: Retrieves timestamped history of status movements.

### Module 28: Order Cancellation
- **Cancellation Request (`POST /api/v1/order-cancellations/{order_id}`)**: Validates order state constraints (delivered orders cannot be cancelled), marks order as `CANCELLED`, releases reserved inventory back to available stock, triggers refund initiation, and prevents duplicate requests.
- **Cancellation Details (`GET /api/v1/order-cancellations/{order_id}`)**: Retrieves cancellation reason, outcome, and timestamp.

### Module 29: Payment Management
- **Session Initiation (`POST /api/v1/payments/initiate`)**: Initiates sandbox payment session with required idempotency key, preventing duplicate transactions on concurrent submissions.
- **Sandbox Processing (`POST /api/v1/payments/{payment_id}/process-sandbox`)**: Executes sandbox authorizations and captures, updating payment state to `SUCCESSFUL` or `FAILED`.
- **Webhook Callbacks (`POST /api/v1/payments/webhook`)**: Handles asynchronous payment gateway webhooks (e.g. `charge.succeeded`), updating order payment status.

### Module 30: Payment Transaction History
- **Order Transaction History (`GET /api/v1/payments/transactions/order/{order_id}`)**: Customer and staff view of all payment attempts, authorizations, captures, and refunds for a specific order.
- **Administrative Transaction Ledger (`GET /api/v1/payments/transactions/`)**: System-wide payment audit logs including raw gateway payloads and references.

### Module 31: Refund Management
- **Process Refund (`POST /api/v1/refunds/`)**: Authorizes full or partial refunds against captured payments. Validates refundable balance bounds, executes gateway refund requests, updates order payment status to `REFUNDED` or `PARTIALLY_REFUNDED`.
- **Refund Inquiries (`GET /api/v1/refunds/`, `GET /api/v1/refunds/{id}`)**: Queries processed refunds by payment ID or refund ID.

### Module 32: Cash on Delivery Management
- **COD Rules & Configuration (`GET /api/v1/cod/config`, `PUT /api/v1/cod/config`)**: Configures extra handling fees, maximum eligible order amounts, and delivery zone postal code whitelists/blacklists.
- **Eligibility Validation (`POST /api/v1/cod/validate-eligibility`)**: Evaluates order cart amount and shipping postal code against eligibility criteria.
- **Courier Cash Collection (`POST /api/v1/cod/collections/{order_id}/collect`)**: Records courier cash collected in the field, timestamp, and courier identity; automatically reconciles order payment status.

### Module 33: Shipping Order Management
- **Shipment Record Generation (`POST /api/v1/shipments/`)**: Creates parcel shipment records linked to confirmed orders with carrier assignment (FedEx, DHL, UPS, USPS) and unique shipment references.
- **Shipment Management (`GET /api/v1/shipments/`, `PATCH /api/v1/shipments/{id}/status`)**: Lists shipments and tracks dispatch timestamps, shipping label URLs, and parcel delivery states.

### Module 34: Shipment Tracking
- **Milestone Event Logging (`POST /api/v1/shipments/tracking/{tracking_number}/events`)**: Logs checkpoint transit events (`DISPATCHED`, `IN_TRANSIT`, `OUT_FOR_DELIVERY`, `DELIVERED`, `EXCEPTION`) with location and descriptions.
- **Public Tracking Inquiries (`GET /api/v1/shipments/tracking/{tracking_number}/events`)**: Real-time checkpoint event timeline lookup by tracking number.

### Module 35: Delivery Management
- **Driver Assignment (`POST /api/v1/shipments/{shipment_id}/assign-delivery`)**: Assigns delivery personnel or third-party courier agents to parcel shipments.
- **Delivery Attempt & Proof of Delivery (`POST /api/v1/shipments/deliveries/{id}/attempt`)**: Captures delivery attempts count, recipient signature names, confirmation notes, and delivery timestamps.

### Module 36: Return Management (RMA)
- **Customer Return Request (`POST /api/v1/returns/`)**: Submits RMA requests for delivered orders with item-level reasons and condition inspections (`UNOPENED`, `OPENED_LIKE_NEW`, `DEFECTIVE`, `DAMAGED`).
- **Staff Review Workflow (`PATCH /api/v1/returns/{id}/review`)**: Staff evaluates requests, transitioning states to `APPROVED` or `REJECTED`.
- **Warehouse Goods Receipt (`POST /api/v1/returns/{id}/receive`)**: Confirms returned physical goods at warehouse docks, restocking inventory and updating status to `ITEMS_RECEIVED`.

### Module 37: Exchange Management
- **Exchange Request (`POST /api/v1/exchanges/`)**: Submits exchange requests for delivered items for alternative product variants, validating replacement variant stock availability.
- **Review & Approval (`PATCH /api/v1/exchanges/{id}/review`)**: Staff reviews and authorizes the replacement.
- **Replacement Dispatch (`POST /api/v1/exchanges/{id}/dispatch`)**: Dispatches the replacement item, automatically deducting replacement variant stock from inventory.

### Module 38: Product Reviews and Ratings
- **Customer Review Submission (`POST /api/v1/reviews/`)**: Verified purchaser reviews with 1 to 5 star ratings, title, and detailed comments. Enforces single review per customer per product.
- **Catalog Inquiries (`GET /api/v1/reviews/`)**: Queries approved reviews with average ratings and verified purchaser badges.
- **Content Moderation (`PATCH /api/v1/reviews/{id}/moderation`)**: Administrative moderation queue (`PENDING`, `APPROVED`, `REJECTED`).

### Module 39: Product Questions and Answers
- **Inquiry Submission (`POST /api/v1/questions/`)**: Customer pre-purchase inquiries attached to products.
- **Official Answers (`POST /api/v1/questions/{id}/answers`)**: Staff and vendor verified answers with official badges.
- **Moderation Workflow (`PATCH /api/v1/questions/{id}/moderation`)**: Administrative approval and rejection of public questions.

### Module 40: Customer Support Tickets
- **Ticket Creation (`POST /api/v1/support-tickets/`)**: Customer support tickets across categories (`ORDER`, `PAYMENT`, `PRODUCT`, `RETURN`, `GENERAL`) and priority levels (`LOW`, `NORMAL`, `HIGH`, `URGENT`).
- **Threaded Conversation (`POST /api/v1/support-tickets/{id}/messages`)**: Multi-party conversation threads between customers and support agents, supporting internal notes.
- **Status Lifecycle (`PATCH /api/v1/support-tickets/{id}/status`)**: Transitions across `OPEN`, `IN_PROGRESS`, `WAITING_CUSTOMER`, `RESOLVED`, and `CLOSED`.

### Module 41: Notification Management
- **In-App Notification Dispatch (`POST /api/v1/notifications`, `GET /api/v1/notifications`)**: Customer and staff notifications categorized by type (`ORDER_UPDATE`, `PAYMENT_STATUS`, `REFUND_STATUS`, `INVENTORY_ALERT`, `SYSTEM`) and priority levels (`LOW`, `NORMAL`, `HIGH`, `CRITICAL`).
- **Read/Unread Lifecycle Tracking**: Allows filtering notifications by unread status, individual read marking (`PATCH /api/v1/notifications/{id}/read`), and atomic bulk clearing (`PATCH /api/v1/notifications/mark-all-read`).
- **Action URLs**: Supports contextual deep-links to associated checkout orders or warehouse inventory items.

### Module 42: Email and SMS Notifications
- **Gateway Provider Management (`POST /api/v1/messaging/providers`, `GET /api/v1/messaging/providers`)**: Configures external messaging gateways (e.g. SendGrid, Twilio, AWS SES/SNS) with active/inactive status toggles.
- **Transactional Dispatch & Template Simulation (`POST /api/v1/messaging/send`)**: Evaluates recipient addresses and handles automated notifications for customer email verification, order confirmation, and delivery dispatch.
- **Delivery Logging & Auto-Retries (`GET /api/v1/messaging/logs`, `POST /api/v1/messaging/logs/{id}/retry`)**: Maintains delivery logs with statuses (`PENDING`, `SENT`, `DELIVERED`, `FAILED`), error details, and safe idempotent retry mechanisms with exponential backoff counters.

### Module 43: Seller and Supplier Management
- **Vendor Onboarding & Registration (`POST /api/v1/suppliers`, `GET /api/v1/suppliers`)**: Manages supplier profiles including legal entity names, vendor codes, tax IDs, contact details, and payment credit terms.
- **Approval Workflow Lifecycle (`PATCH /api/v1/suppliers/{id}/approval`)**: Enforces state transitions (`PENDING_APPROVAL` -> `APPROVED` -> `SUSPENDED` / `REJECTED`) with administrative comments and timestamping.
- **Catalog Supplier Association (`POST /api/v1/suppliers/{id}/products`, `GET /api/v1/suppliers/{id}/products`)**: Maps products and variants to primary or secondary vendors with lead time days and supply costs.
- **Compliance Audit History (`GET /api/v1/suppliers/{id}/history`)**: Retains historical audit entries for vendor status transitions and contractual changes.

### Module 44: Purchase Order Management
- **Purchase Order Generation (`POST /api/v1/purchase-orders`, `GET /api/v1/purchase-orders`)**: Issues supplier POs with unique sequential identifiers, destination warehouses, line items (product, variant, ordered quantity, unit cost), and expected delivery schedules.
- **PO Status Workflow (`PATCH /api/v1/purchase-orders/{id}/status`)**: Governs status transitions (`DRAFT` -> `SUBMITTED` -> `APPROVED` -> `CANCELLED`) with audit history tracking (`POStatusHistory`).
- **Goods Receipt & Stock Replenishment (`POST /api/v1/purchase-orders/{id}/receive`)**: Handles goods receipt at warehouse docks; automatically updates `quantity_received`, marks PO status as `RECEIVED` or `PARTIALLY_RECEIVED`, increments warehouse facility stock and total available inventory, and records `StockMovement` ledger entries.
- **Supplier Order History (`GET /api/v1/purchase-orders/supplier/{id}`)**: Aggregates historic purchasing metrics for vendor performance review.

### Module 45: Supplier Invoice Management
- **Commercial Invoice Recording (`POST /api/v1/supplier-invoices`, `GET /api/v1/supplier-invoices`)**: Records vendor billing linked directly to issued Purchase Orders.
- **Duplicate Charge Prevention**: Enforces composite uniqueness constraints across `(invoice_number, supplier_id)`, returning HTTP 409 Conflict if duplicate numbers are detected.
- **Financial Reconciliation & Payment (`PATCH /api/v1/supplier-invoices/{id}/payment`)**: Validates subtotal, tax amount, and total billing. Tracks payment states (`UNPAID`, `PARTIALLY_PAID`, `PAID`, `VOID`) and cumulative amounts paid with reconciliation audit notes.

### Module 46: Audit Log Management
- **Sensitive Action Recording (`POST /api/v1/audit-logs`, `GET /api/v1/audit-logs`)**: Dedicated immutable audit journal (`AdminAuditLog`) capturing sensitive administrative modifications across products, prices, stock levels, order transitions, and security settings.
- **Change Diff & Actor Tracing**: Stores JSON diffs of previous and updated field values, actor user ID, client IP address, and browser/client user-agent.
- **Immutability & Super Admin RBAC**: Enforces strict append-only constraints; records cannot be updated or deleted. Endpoint access is strictly guarded by `AUDIT_LOGS_READ` and `AUDIT_LOGS_WRITE` permissions.

### Module 47: Dashboard and Summary APIs
- **Executive Overview (`GET /api/v1/dashboard/overview`)**: Unified dashboard payload aggregating live catalog health, total inventory units, active restock alerts, order counts by pipeline status, and gross revenues.
- **Domain Breakdown Endpoints**: Provides specialized summaries for products (`/dashboard/products-summary`), orders (`/dashboard/orders-summary`), financials (`/dashboard/financials-summary`), and exceptions (`/dashboard/exceptions-summary`).
- **Role-Based Data Scoping**: Automatically scopes returned analytics and revenue figures to administrative tiers while presenting customer-safe summaries for standard users.

### Module 48: Reports and Analytics APIs
- **Sales & Order Analytics (`GET /api/v1/analytics/sales`)**: Aggregates total gross sales, net revenue, promotional discounts given, tax collected, and Average Order Value (AOV) across date ranges and fulfillment statuses.
- **Inventory Distribution Analytics (`GET /api/v1/analytics/inventory`)**: Computes total stock units, tracked SKUs, and per-warehouse inventory breakdowns.
- **Payment & Refund Reconciliation (`GET /api/v1/analytics/payments`)**: Itemizes payment amounts by method and status alongside total refunded amounts.
- **Product & Category Performance (`GET /api/v1/analytics/performance`)**: Ranks top-selling products by quantity and revenue, and computes category revenue market share.

### Module 49: Report Export and Background Tasks
- **Multi-Format Report Export (`POST /api/v1/tasks/export`)**: Asynchronously exports orders and inventory data in CSV, Excel (OpenPyXL), and PDF (ReportLab) formats, saving generated artifacts to secure export storage.
- **Scheduled Operational Summaries (`POST /api/v1/tasks/schedule-summary`)**: Schedules automated operational daily and weekly summaries with customizable warehouse and category filters.
- **Background Worker & Retry Management (`GET /api/v1/tasks`, `POST /api/v1/tasks/{id}/retry`)**: Tracks job lifecycle states (`PENDING`, `RUNNING`, `COMPLETED`, `FAILED`), retry counters, execution durations, and provides safe retry dispatching.

### Module 50: API Testing and System Integration
- **Automated Test Matrix**: Comprehensive 39-suite integration test covering all 50 platform modules with 100% pass rate.
- **System Workflow Integration**: Validates end-to-end flows spanning customer registration, address setup, cart management, checkout order placement, supplier purchase order creation, goods receipt, and administrative audit verification.
- **Interactive OpenAPI & Postman Sync**: Verified interactive Swagger UI documentation and updated 35-folder Postman collection with complete request headers, JSON payloads, and response validation scripts.

---

## 4. Database Schema and Entity Relationships

```
                                +--------------------+
                                |       User         |
                                +--------------------+
                                | id (PK)            |
                                | email (Unique)     |
                                | phone (Unique)     |
                                | hashed_password    |
                                | role               |
                                | status             |
                                | is_verified        |
                                +--------------------+
                                      |   |   |   |
         +----------------------------+   |   |   +----------------------------+
         |                                |   |                                |
         v 1:1                            |   v 1:N                            v 1:N
+--------------------+                    |  +--------------------+   +--------------------+
|  CustomerProfile   |                    |  |   Address          |   |  UserActivityLog   |
+--------------------+                    |  +--------------------+   +--------------------+
| id (PK)            |                    |  | id (PK)            |   | id (PK)            |
| user_id (FK)       |                    |  | user_id (FK)       |   | user_id (FK)       |
| secondary_email    |                    |  | address_type       |   | action             |
| date_of_birth      |                    |  | street_line1       |   | details            |
| deactivation_status|                    |  | is_default         |   | created_at         |
+--------------------+                    |  +--------------------+   +--------------------+
                                          v 1:N
                                     +--------------------+
                                     |       Order        |
                                     +--------------------+
                                     | id (PK)            |
                                     | user_id (FK)       |
                                     | shipping_addr_id   |
                                     | billing_addr_id    |
                                     | total_amount       |
                                     +--------------------+

+--------------------+      1:N      +--------------------+      1:N      +--------------------+
|      Category      | ------------> |      Product       | ------------> |   ProductVariant   |
+--------------------+               +--------------------+               +--------------------+
| id (PK)            |               | id (PK)            |               | id (PK)            |
| name               |               | name, slug         |               | product_id (FK)    |
| parent_id (Self-FK)|               | base_price, SKU    |               | sku (Unique)       |
| is_active          |               | category_id (FK)   |               | price, stock_qty   |
+--------------------+               | brand_id (FK)      |               | availability_status|
          |                          | status             |               +--------------------+
          | 1:N                      +--------------------+                         |
          v                                    |                                    |
+--------------------+                         | 1:N                                | 1:N
| CategoryAttribute  |                         |                                    |
+--------------------+                         v                                    v
| id (PK)            |               +--------------------+               +--------------------+
| category_id (FK)   |               |    ProductPrice    |               |    ProductMedia    |
| attribute_id (FK)  |               +--------------------+               +--------------------+
+--------------------+               | id (PK)            |               | id (PK)            |
          ^                          | product_id (FK)    |               | product_id (FK)    |
          | N:1                      | base_price         |               | variant_id (FK)    |
+--------------------+               | sale_price         |               | original_filename  |
|     Attribute      |               | sale_start_at      |               | mime_type, file_sz |
+--------------------+               | sale_end_at        |               | checksum_sha256    |
| id (PK)            |               +--------------------+               | width, height      |
| name, code (Unique)|                         |                          | is_primary         |
| data_type          |                         | 1:N                      +--------------------+
+--------------------+                         v
          |                          +--------------------+
          | 1:N                      |    PriceHistory    |
          v                          +--------------------+
+--------------------+               | id (PK)            |
|ProductAttributeVal |               | price_id (FK)      |
+--------------------+               | product_id (FK)    |
| id (PK)            |               | old/new base_price |
| product_id (FK)    |               | change_reason      |
| attribute_id (FK)  |               +--------------------+
| value_text/number  |
+--------------------+
                                     +--------------------+      1:N      +--------------------+
+--------------------+               |   InventoryItem    | ------------> |   StockMovement    |
|       Brand        |               +--------------------+               +--------------------+
+--------------------+               | id (PK)            |               | id (PK)            |
| id (PK)            |               | product_id (FK)    |               | inventory_item (FK)|
| name, code (Unique)|               | variant_id (FK)    |               | movement_type      |
| status             |               | total_quantity     |               | quantity           |
+--------------------+               | available_quantity |               | balance_after      |
                                     | reserved_quantity  |               | reference_type     |
                                     +--------------------+               +--------------------+
                                               | 1:N
                                               v
+--------------------+      1:N      +--------------------+
|     Warehouse      | ------------> | WarehouseInventory |
+--------------------+               +--------------------+
| id (PK)            |               | id (PK)            |
| code (Unique), name|               | warehouse_id (FK)  |
| capacity_units     |               | product_id (FK)    |
| current_utilization|               | variant_id (FK)    |
| status             |               | quantity           |
+--------------------+               | aisle_location     |
                                     +--------------------+

+-----------------------+            +-----------------------+            +-----------------------+
|  InventoryTransfer    |            |   LowStockThreshold   |            |     RestockAlert      |
+-----------------------+            +-----------------------+            +-----------------------+
| id (PK)               |            | id (PK)               |            | id (PK)               |
| transfer_number (UQ)  |            | variant_id (FK)       |            | variant_id (FK)       |
| source_warehouse_id   |            | min_threshold         |            | current_stock         |
| dest_warehouse_id     |            | reorder_quantity      |            | threshold_level       |
| variant_id (FK)       |            +-----------------------+            | deficit, severity     |
| quantity_requested    |                        | 1:N                    | status (OPEN/RESOLVED)|
| quantity_shipped/recv |                        v                        +-----------------------+
| status, timestamps    |            +-----------------------+
+-----------------------+            |StockThresholdChangeHist|
                                     +-----------------------+
                                     | id (PK), threshold_id |
                                     | old/new_threshold     |
                                     +-----------------------+

+--------------------+      1:N      +--------------------+
|        Cart        | ------------> |      CartItem      |
+--------------------+               +--------------------+
| id (PK)            |               | id (PK)            |
| user_id (FK)       |               | cart_id (FK)       |
| is_active          |               | variant_id (FK)    |
+--------------------+               | quantity           |
                                     +--------------------+

+--------------------+               +--------------------+               +--------------------+
|    WishlistItem    |               |       Coupon       |      1:N      |    CouponUsage     |
+--------------------+               +--------------------+ ------------> +--------------------+
| id (PK)            |               | id (PK)            |               | id (PK)            |
| user_id (FK)       |               | code (Unique)      |               | coupon_id (FK)     |
| variant_id (FK)    |               | discount_type      |               | user_id (FK)       |
| created_at         |               | discount_value     |               | order_id (FK)      |
+--------------------+               | min_purchase_amount|               +--------------------+
                                     | max_uses, used_cnt |
                                     | is_active          |
                                     +--------------------+

+--------------------+      1:N      +--------------------+
|     Promotion      | ------------> |  PromotionHistory  |
+--------------------+               +--------------------+
| id (PK)            |               | id (PK)            |
| name, target_type  |               | promotion_id (FK)  |
| discount_type      |               | action, changed_by |
| discount_value     |               +--------------------+
| min_cart_value     |
| is_active          |
+--------------------+

+--------------------+               +--------------------+
|      TaxRate       |               |   ShippingMethod   |
+--------------------+               +--------------------+
| id (PK)            |               | id (PK)            |
| tax_name           |               | code (Unique), name|
| country_code       |               | base_cost          |
| state_code         |               | free_ship_threshold|
| rate_percentage    |               | estimated_days     |
| category_id (FK)   |               | is_active          |
| is_active          |               +--------------------+
+--------------------+

+------------------------------------+      1:N      +------------------------------------+
|               Order                | ------------> |             OrderItem              |
+------------------------------------+               +------------------------------------+
| id (PK)                            |               | id (PK)                            |
| order_number (Unique)              |               | order_id (FK)                      |
| user_id (FK)                       |               | variant_id (FK)                    |
| shipping_address_id (FK)           |               | sku, product_name                  |
| billing_address_id (FK)            |               | unit_price, quantity               |
| shipping_address_snapshot (JSON)   |               | total_price                        |
| billing_address_snapshot (JSON)    |               +------------------------------------+
| status (CONFIRMED/PROCESSING...)   |                                 |
| payment_status (PENDING/PAID)      |                                 | 1:N
| subtotal_amount, discount_amount   |                                 v
| tax_amount, shipping_amount        |               +------------------------------------+
| total_amount, coupon_code          |               |         OrderStatusHistory         |
| shipping_method_code               |               +------------------------------------+
+------------------------------------+               | id (PK), order_id (FK)             |
                                                     | from_status, to_status, notes      |
                                                     +------------------------------------+

+--------------------+               +--------------------+               +--------------------+
|    Notification    |               |  NotifProviderCfg  |               |     MessageLog     |
+--------------------+               +--------------------+               +--------------------+
| id (PK)            |               | id (PK)            |               | id (PK)            |
| user_id (FK)       |               | provider_type      |               | channel, recipient |
| notification_type  |               | name, is_active    |               | template_code      |
| priority, title    |               | sender_identity    |               | status, retries    |
| message, is_read   |               | config_data (JSON) |               | error_details      |
+--------------------+               +--------------------+               +--------------------+

+--------------------+      1:N      +--------------------+      1:N      +--------------------+
|      Supplier      | ------------> |   PurchaseOrder    | ------------> | PurchaseOrderItem  |
+--------------------+               +--------------------+               +--------------------+
| id (PK)            |               | id (PK)            |               | id (PK)            |
| code (Unique)      |               | po_number (Unique) |               | po_id (FK)         |
| company_name       |               | supplier_id (FK)   |               | product_id (FK)    |
| status (APPROVED..)|               | warehouse_id (FK)  |               | variant_id (FK)    |
| tax_id, terms      |               | status, total_amt  |               | qty_ordered/recv   |
+--------------------+               +--------------------+               | unit_cost, subtotal|
         | 1:N                                 | 1:N                      +--------------------+
         v                                     v
+--------------------+               +--------------------+
|  SupplierInvoice   |               |  POStatusHistory   |
+--------------------+               +--------------------+
| id (PK)            |               | id (PK), po_id (FK)|
| invoice_number (UQ)|               | from_status        |
| supplier_id (FK)   |               | to_status, notes   |
| po_id (FK)         |               +--------------------+
| payment_status     |
| subtotal, total    |
+--------------------+

+--------------------+               +--------------------+
|   AdminAuditLog    |               | BackgroundTaskJob  |
+--------------------+               +--------------------+
| id (PK)            |               | id (PK)            |
| user_id (FK)       |               | job_id (Unique)    |
| action, entity_name|               | task_name          |
| entity_id          |               | task_type, format  |
| changes_diff (JSON)|               | status, retries    |
| ip_address         |               | output_file_path   |
+--------------------+               +--------------------+
```

---

## 5. Quickstart & Testing Guide

### Prerequisites
- Python 3.10+ (tested on Python 3.12)
- Dependencies installed from `requirements.txt`

### Starting the Server
```bash
python main.py
```
Or via uvicorn directly:
```bash
uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```
- Interactive Web Dashboard: `http://127.0.0.1:8000/`
- Interactive Swagger API Documentation: `http://127.0.0.1:8000/docs`
- ReDoc API Documentation: `http://127.0.0.1:8000/redoc`

### Default Pre-Seeded Accounts
- **Super Administrator**: `admin@shopsphere.com` / `Admin@ShopSphere2026!`
- **Employee**: `employee@shopsphere.com` / `Employee@1234!`
- **Customer**: `customer@shopsphere.com` / `Customer@1234!`

### Running Automated Test Suite
```bash
python -m pytest tests -v
```
All 54 comprehensive integration test suites covering all 50 modules execute and pass 100% in under 9 seconds:
- `test_module1_customer_and_employee_login`: Validates customer & staff authentication and token generation.
- `test_module1_invalid_credentials`: Enforces rejection of bad passwords.
- `test_module1_jwt_refresh_token_rotation`: Asserts refresh token rotation and revocation.
- `test_module1_logout_and_token_revocation`: Verifies blacklist persistence and rejected revoked tokens.
- `test_module1_rbac_permissions`: Enforces RBAC denial for unprivileged endpoints.
- `test_module2_create_update_deactivate_users`: User CRUD, role assignments, status transitions, search/filter, and activity logging.
- `test_module3_customer_registration_and_duplicate_prevention`: Customer onboarding, duplicate email/phone prevention, email token verification.
- `test_module4_customer_profile_and_history`: Profile CRUD, field-level change history audit trail, deactivation requests, sensitive data masking.
- `test_module5_address_management_and_order_association`: Address CRUD, single-default flag unsetting logic, order association, deletion protection.
- `test_module6_category_hierarchy_and_invalid_deletion`: Hierarchical category tree, self-referential nesting, cycle prevention, invalid deletion guard.
- `test_module7_brand_management`: Brand registration, status toggling, search, products by brand.
- `test_module8_product_crud_and_search`: Product catalog CRUD, unique base SKU enforcement, multi-attribute filtering, search, sorting.
- `test_module9_product_variants_and_availability`: Product variants, variation attributes (JSON), unique SKUs, stock adjustments, live availability state transitions.
- `test_module10_media_upload_validation_and_metadata`: File upload, MIME type & size validation, Pillow resolution check, SHA-256 checksum, download & deletion.
- `test_module11_attributes_definition_and_filtering`: Attribute definitions, category-specific mapping, product value assignment, attribute filtering.
- `test_module12_product_pricing_and_validity_periods`: Base and sale pricing, validity windows, effective price calculation, audit reasons, price history.
- `test_module13_inventory_tracking_and_negative_prevention`: Total/available/reserved stock, stock additions, reductions, negative inventory prevention, reserve/release workflows, movements audit trail.
- `test_module14_warehouse_management_and_role_restriction`: Warehouse creation, capacity bounds, stock assignment, utilization tracking, role restriction enforcement.
- `test_module15_inventory_transfers`: Inter-warehouse stock transfers, dispatch & receipt quantity updates, transfer status, movement records.
- `test_module16_low_stock_management`: Minimum threshold configuration, change history, low-stock evaluation, automated alert creation and resolution.
- `test_module17_cart_management`: Customer cart CRUD, item additions, quantity updates, inventory availability validation, cart clearing.
- `test_module18_cart_price_calculation`: Server-side pricing calculation, promotional discounts, coupon validation, tax and shipping computation.
- `test_module19_wishlist_management`: Saved items, duplicate addition prevention, stock status checks, cart transfer.
- `test_module20_coupon_management`: Coupon code configuration, discount types, validity, minimum purchase requirements, validation endpoint, activation toggle.
- `test_module21_promotion_management`: Catalog & category promotions, validity windows, cart value thresholds, checkout application.
- `test_module22_tax_management`: Jurisdiction tax rates, category overrides, dynamic checkout tax calculation, status toggles.
- `test_module23_shipping_configuration`: Fulfillment methods, base rates, free shipping thresholds, delivery estimates, dynamic freight quotes.
- `test_module24_checkout_management`: Cart item verification, address confirmation, price/tax/shipping recalculation, inventory pre-reservation, safe order creation.
- `test_module25_order_management`: Unique sequential order number generation, order retrieval and filtering, status transitions, automated reserved stock release upon cancellation.
- `test_module26_order_item_management`: Order item retrieval, snapshot verification, pricing details, and fulfillment status updates.
- `test_module27_order_status_management`: Strict finite-state transitions (CONFIRMED -> PROCESSING -> SHIPPED -> DELIVERED), invalid transition guards, and transition history.
- `test_module28_order_cancellation`: Customer order cancellation, eligibility checks, automated inventory restocking, and refund request dispatch.
- `test_module29_payment_management`: Sandbox payment gateway session creation, idempotency duplicate protection, capture processing, and webhook callbacks.
- `test_module30_payment_transaction_history`: Payment transaction logs, authorization references, customer history queries, and administrative audit.
- `test_module31_refund_management`: Full and partial refund requests, refundable balance validation, and payment status updates.
- `test_module32_cash_on_delivery_management`: Cash on delivery configuration, restricted postal code evaluation, courier collection recording, and reconciliation.
- `test_module33_shipping_order_management`: Parcel shipment creation, shipping carrier assignments, tracking number generation, and label reference generation.
- `test_module34_shipment_tracking`: Milestone tracking checkpoint logging, public tracking queries, and delivery exception recording.
- `test_module35_delivery_management`: Delivery driver assignment, delivery attempt tracking, recipient signature verification, and delivery completion.
- `test_module36_return_management`: Customer RMA return request, item condition inspection, administrative approval workflow, and warehouse restocking.
- `test_module37_exchange_management`: Variant exchange requests, stock availability check, approval workflow, and replacement dispatch with stock deduction.
- `test_module38_product_reviews_and_ratings`: Customer 1-5 star ratings, duplicate review prevention, verified purchase validation, and review moderation.
- `test_module39_product_questions_and_answers`: Customer product inquiries, verified staff responses, and community Q&A content moderation.
- `test_module40_customer_support_tickets`: Customer support ticket triage, threaded multi-party messaging, priority classification, and lifecycle resolution.
- `test_module41_notification_management`: In-app notification creation, priority levels, read/unread status updates, bulk mark-all-read.
- `test_module42_email_and_sms_notifications`: Provider configurations, email/SMS message dispatch, delivery logs, automated retry mechanisms.
- `test_module43_seller_and_supplier_management`: Supplier onboarding, tax IDs, approval state machine (PENDING -> APPROVED -> SUSPENDED), product catalog linking, compliance history.
- `test_module44_purchase_order_management`: Purchase order creation, line items, status approval, goods receiving with automatic warehouse stock replenishment and stock movement audit.
- `test_module45_supplier_invoice_management`: Commercial invoice creation, duplicate invoice rejection, amount validation, payment recording.
- `test_module46_audit_log_management`: Immutable administrative audit log creation, entity-level query filters, change diff tracking, RBAC Super Admin restrictions.
- `test_module47_dashboard_and_summary_apis`: Executive dashboard metrics, catalog counts, inventory levels, order pipeline breakdowns, revenue KPIs, and role-based data scoping.
- `test_module48_reports_and_analytics_apis`: Sales & order analytics, warehouse stock distribution, payment status breakdowns, top-selling product rankings, category performance.
- `test_module49_report_export_and_background_tasks`: Asynchronous report exports (CSV, Excel, PDF), scheduled summary jobs, background job retry execution, task tracking.
- `test_module50_api_testing_and_system_integration`: Full end-to-end platform integration test verifying customer registration, address creation, cart-to-checkout, PO creation, stock receipt, and immutable audit logging.

