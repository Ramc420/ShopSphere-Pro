from app.routers.auth import router as auth_router
from app.routers.users import router as users_router
from app.routers.registration import router as registration_router
from app.routers.profiles import router as profiles_router
from app.routers.addresses import router as addresses_router
from app.routers.categories import router as categories_router
from app.routers.brands import router as brands_router
from app.routers.products import router as products_router
from app.routers.variants import router as variants_router
from app.routers.media import router as media_router
from app.routers.attributes import router as attributes_router
from app.routers.pricing import router as pricing_router
from app.routers.inventory import router as inventory_router
from app.routers.warehouses import router as warehouses_router
from app.routers.transfers import router as transfers_router
from app.routers.low_stock import router as low_stock_router
from app.routers.carts import router as carts_router
from app.routers.cart_calculation import router as cart_calculation_router
from app.routers.wishlist import router as wishlist_router
from app.routers.coupons import router as coupons_router
from app.routers.promotions import router as promotions_router
from app.routers.taxes import router as taxes_router
from app.routers.shipping import router as shipping_router
from app.routers.checkout import router as checkout_router
from app.routers.orders import router as orders_router
from app.routers.notifications import router as notifications_router
from app.routers.messaging import router as messaging_router
from app.routers.suppliers import router as suppliers_router
from app.routers.purchase_orders import router as purchase_orders_router
from app.routers.supplier_invoices import router as supplier_invoices_router
from app.routers.audit_logs import router as audit_logs_router
from app.routers.dashboard import router as dashboard_router
from app.routers.analytics import router as analytics_router
from app.routers.tasks import router as tasks_router
from app.routers.order_items import router as order_items_router
from app.routers.order_status import router as order_status_router
from app.routers.order_cancellations import router as order_cancellations_router
from app.routers.payments import router as payments_router
from app.routers.refunds import router as refunds_router
from app.routers.cod import router as cod_router
from app.routers.shipments import router as shipments_router
from app.routers.returns import router as returns_router
from app.routers.exchanges import router as exchanges_router
from app.routers.reviews import router as reviews_router
from app.routers.questions import router as questions_router
from app.routers.support_tickets import router as support_tickets_router

__all__ = [
    "auth_router",
    "users_router",
    "registration_router",
    "profiles_router",
    "addresses_router",
    "categories_router",
    "brands_router",
    "products_router",
    "variants_router",
    "media_router",
    "attributes_router",
    "pricing_router",
    "inventory_router",
    "warehouses_router",
    "transfers_router",
    "low_stock_router",
    "carts_router",
    "cart_calculation_router",
    "wishlist_router",
    "coupons_router",
    "promotions_router",
    "taxes_router",
    "shipping_router",
    "checkout_router",
    "orders_router",
    "notifications_router",
    "messaging_router",
    "suppliers_router",
    "purchase_orders_router",
    "supplier_invoices_router",
    "audit_logs_router",
    "dashboard_router",
    "analytics_router",
    "tasks_router",
    "order_items_router",
    "order_status_router",
    "order_cancellations_router",
    "payments_router",
    "refunds_router",
    "cod_router",
    "shipments_router",
    "returns_router",
    "exchanges_router",
    "reviews_router",
    "questions_router",
    "support_tickets_router",
]
