import enum
from typing import Dict, List, Set


class UserRole(str, enum.Enum):
    SUPER_ADMIN = "SUPER_ADMIN"
    ADMIN = "ADMIN"
    EMPLOYEE = "EMPLOYEE"
    CUSTOMER = "CUSTOMER"


class UserStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    SUSPENDED = "SUSPENDED"
    DEACTIVATED = "DEACTIVATED"


class Permission(str, enum.Enum):
    # User Management
    USERS_READ = "users:read"
    USERS_WRITE = "users:write"
    ROLES_MANAGE = "roles:manage"
    AUDIT_READ = "audit:read"
    
    # Customer Profiles & Addresses
    PROFILE_READ_ANY = "profile:read_any"
    PROFILE_WRITE_ANY = "profile:write_any"
    PROFILE_READ_SELF = "profile:read_self"
    PROFILE_WRITE_SELF = "profile:write_self"
    ADDRESS_MANAGE_ANY = "address:manage_any"
    ADDRESS_MANAGE_SELF = "address:manage_self"
    
    # Catalog Management
    CATEGORIES_READ = "categories:read"
    CATEGORIES_WRITE = "categories:write"
    BRANDS_READ = "brands:read"
    BRANDS_WRITE = "brands:write"
    PRODUCTS_READ = "products:read"
    PRODUCTS_WRITE = "products:write"
    VARIANTS_WRITE = "variants:write"
    
    # Media & Files
    MEDIA_READ = "media:read"
    MEDIA_UPLOAD = "media:upload"
    MEDIA_DELETE = "media:delete"
    
    # Orders
    ORDERS_READ = "orders:read"
    ORDERS_WRITE = "orders:write"
    
    # Module 11: Attributes
    ATTRIBUTES_READ = "attributes:read"
    ATTRIBUTES_WRITE = "attributes:write"
    
    # Module 12: Pricing
    PRICING_READ = "pricing:read"
    PRICING_WRITE = "pricing:write"
    
    # Module 13: Inventory
    INVENTORY_READ = "inventory:read"
    INVENTORY_WRITE = "inventory:write"
    
    # Module 14: Warehouses
    WAREHOUSES_READ = "warehouses:read"
    WAREHOUSES_WRITE = "warehouses:write"

    # Module 15: Inventory Transfers
    TRANSFERS_READ = "transfers:read"
    TRANSFERS_WRITE = "transfers:write"

    # Module 16: Low-Stock Management
    LOW_STOCK_READ = "low_stock:read"
    LOW_STOCK_WRITE = "low_stock:write"

    # Module 17 & 18: Shopping Cart & Price Calculation
    CART_READ = "cart:read"
    CART_WRITE = "cart:write"

    # Module 19: Wishlist Management
    WISHLIST_READ = "wishlist:read"
    WISHLIST_WRITE = "wishlist:write"

    # Module 20: Coupon Management
    COUPONS_READ = "coupons:read"
    COUPONS_WRITE = "coupons:write"

    # Module 21: Promotion Management
    PROMOTIONS_READ = "promotions:read"
    PROMOTIONS_WRITE = "promotions:write"

    # Module 22: Tax Management
    TAXES_READ = "taxes:read"
    TAXES_WRITE = "taxes:write"

    # Module 23: Shipping Configuration
    SHIPPING_READ = "shipping:read"
    SHIPPING_WRITE = "shipping:write"

    # Module 24: Checkout Management
    CHECKOUT_PROCESS = "checkout:process"

    # Module 25: Order Management
    ORDERS_ADMIN = "orders:admin"

    # Module 26: Order Item Management
    ORDER_ITEMS_READ = "order_items:read"
    ORDER_ITEMS_WRITE = "order_items:write"

    # Module 27: Order Status Management
    ORDER_STATUS_MANAGE = "order_status:manage"

    # Module 28: Order Cancellation
    ORDER_CANCEL = "order:cancel"

    # Module 29 & 30: Payment Management & History
    PAYMENTS_READ = "payments:read"
    PAYMENTS_WRITE = "payments:write"

    # Module 31: Refund Management
    REFUNDS_READ = "refunds:read"
    REFUNDS_WRITE = "refunds:write"

    # Module 32: Cash on Delivery Management
    COD_MANAGE = "cod:manage"

    # Module 33, 34 & 35: Shipping Orders, Tracking & Delivery
    SHIPMENTS_READ = "shipments:read"
    SHIPMENTS_WRITE = "shipments:write"
    DELIVERY_MANAGE = "delivery:manage"

    # Module 36 & 37: Returns & Exchanges
    RETURNS_READ = "returns:read"
    RETURNS_WRITE = "returns:write"
    EXCHANGES_READ = "exchanges:read"
    EXCHANGES_WRITE = "exchanges:write"

    # Module 38: Reviews and Ratings
    REVIEWS_READ = "reviews:read"
    REVIEWS_WRITE = "reviews:write"
    REVIEWS_MODERATE = "reviews:moderate"

    # Module 39: Questions and Answers
    QUESTIONS_READ = "questions:read"
    QUESTIONS_WRITE = "questions:write"
    QUESTIONS_MODERATE = "questions:moderate"

    # Module 40: Customer Support Tickets
    TICKETS_READ = "tickets:read"
    TICKETS_WRITE = "tickets:write"
    TICKETS_MANAGE = "tickets:manage"

    # Module 41: Notification Management
    NOTIFICATIONS_READ = "notifications:read"
    NOTIFICATIONS_WRITE = "notifications:write"

    # Module 42: Email and SMS Notifications
    MESSAGING_READ = "messaging:read"
    MESSAGING_WRITE = "messaging:write"

    # Module 43: Seller and Supplier Management
    SUPPLIERS_READ = "suppliers:read"
    SUPPLIERS_WRITE = "suppliers:write"

    # Module 44: Purchase Order Management
    PURCHASE_ORDERS_READ = "purchase_orders:read"
    PURCHASE_ORDERS_WRITE = "purchase_orders:write"

    # Module 45: Supplier Invoice Management
    SUPPLIER_INVOICES_READ = "supplier_invoices:read"
    SUPPLIER_INVOICES_WRITE = "supplier_invoices:write"

    # Module 46: Audit Log Management
    AUDIT_LOGS_READ = "audit_logs:read"
    AUDIT_LOGS_WRITE = "audit_logs:write"

    # Module 47: Dashboard and Summary APIs
    DASHBOARD_READ = "dashboard:read"

    # Module 48: Reports and Analytics APIs
    ANALYTICS_READ = "analytics:read"

    # Module 49: Report Export and Background Tasks
    TASKS_READ = "tasks:read"
    TASKS_WRITE = "tasks:write"


ROLE_PERMISSIONS: Dict[UserRole, Set[str]] = {
    UserRole.SUPER_ADMIN: {p.value for p in Permission},
    UserRole.ADMIN: {
        Permission.USERS_READ.value,
        Permission.USERS_WRITE.value,
        Permission.ROLES_MANAGE.value,
        Permission.AUDIT_READ.value,
        Permission.PROFILE_READ_ANY.value,
        Permission.PROFILE_WRITE_ANY.value,
        Permission.PROFILE_READ_SELF.value,
        Permission.PROFILE_WRITE_SELF.value,
        Permission.ADDRESS_MANAGE_ANY.value,
        Permission.ADDRESS_MANAGE_SELF.value,
        Permission.CATEGORIES_READ.value,
        Permission.CATEGORIES_WRITE.value,
        Permission.BRANDS_READ.value,
        Permission.BRANDS_WRITE.value,
        Permission.PRODUCTS_READ.value,
        Permission.PRODUCTS_WRITE.value,
        Permission.VARIANTS_WRITE.value,
        Permission.MEDIA_READ.value,
        Permission.MEDIA_UPLOAD.value,
        Permission.MEDIA_DELETE.value,
        Permission.ORDERS_READ.value,
        Permission.ORDERS_WRITE.value,
        Permission.ORDERS_ADMIN.value,
        Permission.ATTRIBUTES_READ.value,
        Permission.ATTRIBUTES_WRITE.value,
        Permission.PRICING_READ.value,
        Permission.PRICING_WRITE.value,
        Permission.INVENTORY_READ.value,
        Permission.INVENTORY_WRITE.value,
        Permission.WAREHOUSES_READ.value,
        Permission.WAREHOUSES_WRITE.value,
        Permission.TRANSFERS_READ.value,
        Permission.TRANSFERS_WRITE.value,
        Permission.LOW_STOCK_READ.value,
        Permission.LOW_STOCK_WRITE.value,
        Permission.CART_READ.value,
        Permission.CART_WRITE.value,
        Permission.WISHLIST_READ.value,
        Permission.WISHLIST_WRITE.value,
        Permission.COUPONS_READ.value,
        Permission.COUPONS_WRITE.value,
        Permission.PROMOTIONS_READ.value,
        Permission.PROMOTIONS_WRITE.value,
        Permission.TAXES_READ.value,
        Permission.TAXES_WRITE.value,
        Permission.SHIPPING_READ.value,
        Permission.SHIPPING_WRITE.value,
        Permission.CHECKOUT_PROCESS.value,
        Permission.NOTIFICATIONS_READ.value,
        Permission.NOTIFICATIONS_WRITE.value,
        Permission.MESSAGING_READ.value,
        Permission.MESSAGING_WRITE.value,
        Permission.SUPPLIERS_READ.value,
        Permission.SUPPLIERS_WRITE.value,
        Permission.PURCHASE_ORDERS_READ.value,
        Permission.PURCHASE_ORDERS_WRITE.value,
        Permission.SUPPLIER_INVOICES_READ.value,
        Permission.SUPPLIER_INVOICES_WRITE.value,
        Permission.AUDIT_LOGS_READ.value,
        Permission.AUDIT_LOGS_WRITE.value,
        Permission.DASHBOARD_READ.value,
        Permission.ANALYTICS_READ.value,
        Permission.TASKS_READ.value,
        Permission.TASKS_WRITE.value,
        Permission.ORDER_ITEMS_READ.value,
        Permission.ORDER_ITEMS_WRITE.value,
        Permission.ORDER_STATUS_MANAGE.value,
        Permission.ORDER_CANCEL.value,
        Permission.PAYMENTS_READ.value,
        Permission.PAYMENTS_WRITE.value,
        Permission.REFUNDS_READ.value,
        Permission.REFUNDS_WRITE.value,
        Permission.COD_MANAGE.value,
        Permission.SHIPMENTS_READ.value,
        Permission.SHIPMENTS_WRITE.value,
        Permission.DELIVERY_MANAGE.value,
        Permission.RETURNS_READ.value,
        Permission.RETURNS_WRITE.value,
        Permission.EXCHANGES_READ.value,
        Permission.EXCHANGES_WRITE.value,
        Permission.REVIEWS_READ.value,
        Permission.REVIEWS_WRITE.value,
        Permission.REVIEWS_MODERATE.value,
        Permission.QUESTIONS_READ.value,
        Permission.QUESTIONS_WRITE.value,
        Permission.QUESTIONS_MODERATE.value,
        Permission.TICKETS_READ.value,
        Permission.TICKETS_WRITE.value,
        Permission.TICKETS_MANAGE.value,
    },
    UserRole.EMPLOYEE: {
        Permission.USERS_READ.value,
        Permission.PROFILE_READ_SELF.value,
        Permission.PROFILE_WRITE_SELF.value,
        Permission.ADDRESS_MANAGE_SELF.value,
        Permission.CATEGORIES_READ.value,
        Permission.CATEGORIES_WRITE.value,
        Permission.BRANDS_READ.value,
        Permission.BRANDS_WRITE.value,
        Permission.PRODUCTS_READ.value,
        Permission.PRODUCTS_WRITE.value,
        Permission.VARIANTS_WRITE.value,
        Permission.MEDIA_READ.value,
        Permission.MEDIA_UPLOAD.value,
        Permission.ORDERS_READ.value,
        Permission.ORDERS_WRITE.value,
        Permission.ORDERS_ADMIN.value,
        Permission.ATTRIBUTES_READ.value,
        Permission.ATTRIBUTES_WRITE.value,
        Permission.PRICING_READ.value,
        Permission.INVENTORY_READ.value,
        Permission.INVENTORY_WRITE.value,
        Permission.WAREHOUSES_READ.value,
        Permission.TRANSFERS_READ.value,
        Permission.TRANSFERS_WRITE.value,
        Permission.LOW_STOCK_READ.value,
        Permission.LOW_STOCK_WRITE.value,
        Permission.COUPONS_READ.value,
        Permission.PROMOTIONS_READ.value,
        Permission.TAXES_READ.value,
        Permission.SHIPPING_READ.value,
        Permission.NOTIFICATIONS_READ.value,
        Permission.NOTIFICATIONS_WRITE.value,
        Permission.MESSAGING_READ.value,
        Permission.SUPPLIERS_READ.value,
        Permission.SUPPLIERS_WRITE.value,
        Permission.PURCHASE_ORDERS_READ.value,
        Permission.PURCHASE_ORDERS_WRITE.value,
        Permission.SUPPLIER_INVOICES_READ.value,
        Permission.DASHBOARD_READ.value,
        Permission.ANALYTICS_READ.value,
        Permission.TASKS_READ.value,
        Permission.TASKS_WRITE.value,
        Permission.ORDER_ITEMS_READ.value,
        Permission.ORDER_ITEMS_WRITE.value,
        Permission.ORDER_STATUS_MANAGE.value,
        Permission.ORDER_CANCEL.value,
        Permission.PAYMENTS_READ.value,
        Permission.PAYMENTS_WRITE.value,
        Permission.REFUNDS_READ.value,
        Permission.REFUNDS_WRITE.value,
        Permission.COD_MANAGE.value,
        Permission.SHIPMENTS_READ.value,
        Permission.SHIPMENTS_WRITE.value,
        Permission.DELIVERY_MANAGE.value,
        Permission.RETURNS_READ.value,
        Permission.RETURNS_WRITE.value,
        Permission.EXCHANGES_READ.value,
        Permission.EXCHANGES_WRITE.value,
        Permission.REVIEWS_READ.value,
        Permission.REVIEWS_WRITE.value,
        Permission.REVIEWS_MODERATE.value,
        Permission.QUESTIONS_READ.value,
        Permission.QUESTIONS_WRITE.value,
        Permission.QUESTIONS_MODERATE.value,
        Permission.TICKETS_READ.value,
        Permission.TICKETS_WRITE.value,
        Permission.TICKETS_MANAGE.value,
    },
    UserRole.CUSTOMER: {
        Permission.PROFILE_READ_SELF.value,
        Permission.PROFILE_WRITE_SELF.value,
        Permission.ADDRESS_MANAGE_SELF.value,
        Permission.CATEGORIES_READ.value,
        Permission.BRANDS_READ.value,
        Permission.PRODUCTS_READ.value,
        Permission.MEDIA_READ.value,
        Permission.ORDERS_READ.value,
        Permission.ORDERS_WRITE.value,
        Permission.ATTRIBUTES_READ.value,
        Permission.PRICING_READ.value,
        Permission.CART_READ.value,
        Permission.CART_WRITE.value,
        Permission.WISHLIST_READ.value,
        Permission.WISHLIST_WRITE.value,
        Permission.COUPONS_READ.value,
        Permission.PROMOTIONS_READ.value,
        Permission.SHIPPING_READ.value,
        Permission.CHECKOUT_PROCESS.value,
        Permission.NOTIFICATIONS_READ.value,
        Permission.DASHBOARD_READ.value,
        Permission.ORDER_ITEMS_READ.value,
        Permission.ORDER_CANCEL.value,
        Permission.PAYMENTS_READ.value,
        Permission.PAYMENTS_WRITE.value,
        Permission.REFUNDS_READ.value,
        Permission.SHIPMENTS_READ.value,
        Permission.RETURNS_READ.value,
        Permission.RETURNS_WRITE.value,
        Permission.EXCHANGES_READ.value,
        Permission.EXCHANGES_WRITE.value,
        Permission.REVIEWS_READ.value,
        Permission.REVIEWS_WRITE.value,
        Permission.QUESTIONS_READ.value,
        Permission.QUESTIONS_WRITE.value,
        Permission.TICKETS_READ.value,
        Permission.TICKETS_WRITE.value,
    },
}


def get_role_permissions(role: str) -> List[str]:
    try:
        user_role = UserRole(role)
        return sorted(list(ROLE_PERMISSIONS.get(user_role, set())))
    except ValueError:
        return []
