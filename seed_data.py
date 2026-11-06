import json
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from sqlalchemy.orm import Session

from app.core.permissions import UserRole, UserStatus
from app.core.security import hash_password
from app.database import Base, SessionLocal, engine, ensure_database_schema
from app.models.address import Address
from app.models.attribute import (
    Attribute,
    AttributeOption,
    CategoryAttribute,
    ProductAttributeValue,
)
from app.models.brand import Brand
from app.models.category import Category
from app.models.customer_profile import CustomerProfile
from app.models.inventory import InventoryItem, StockMovement
from app.models.order import Order
from app.models.pricing import PriceHistory, ProductPrice
from app.models.product import Product
from app.models.user import User
from app.models.variant import ProductVariant
from app.models.warehouse import Warehouse, WarehouseInventory
from app.models.transfer import InventoryTransfer
from app.models.low_stock import LowStockThreshold, StockThresholdChangeHistory, RestockAlert
from app.models.cart import Cart, CartItem
from app.models.wishlist import WishlistItem
from app.models.coupon import Coupon, CouponUsage
from app.models.promotion import Promotion, PromotionHistory
from app.models.tax import TaxRate, TaxHistory
from app.models.shipping import ShippingMethod, ShippingRule
from app.models.order import OrderItem, OrderStatusHistory
from app.models.notification import Notification
from app.models.messaging import NotificationProviderConfig, MessageLog
from app.models.supplier import Supplier, SupplierHistory, ProductSupplier
from app.models.purchase_order import PurchaseOrder, PurchaseOrderItem, POStatusHistory
from app.models.supplier_invoice import SupplierInvoice
from app.models.audit_entry import AdminAuditLog
from app.models.background_task import BackgroundTaskJob
from app.models.order_cancellation import OrderCancellation
from app.models.payment import Payment, PaymentTransaction
from app.models.refund import Refund
from app.models.cod import CODConfig, CODCollection
from app.models.shipping_order import Shipment, TrackingEvent, DeliveryAssignment
from app.models.order_return import ReturnRequest, ReturnItem, ExchangeRequest
from app.models.product_interaction import ProductReview, ProductQuestion, ProductAnswer
from app.models.support_ticket import SupportTicket, TicketMessage


def seed_initial_data(db: Session):
    """Seed comprehensive test data for ShopSphere Pro (Modules 1 - 14)."""
    # 1. Super Admin
    admin = db.query(User).filter(User.email == "admin@shopsphere.com").first()
    if not admin:
        admin = User(
            email="admin@shopsphere.com",
            phone="+14155550001",
            hashed_password=hash_password("Admin@ShopSphere2026!"),
            first_name="Alexander",
            last_name="Pierce",
            role=UserRole.SUPER_ADMIN.value,
            status=UserStatus.ACTIVE.value,
            is_verified=True,
            registration_status="VERIFIED",
            department="Executive Management"
        )
        db.add(admin)

    # 2. Staff / Employee
    employee = db.query(User).filter(User.email == "employee@shopsphere.com").first()
    if not employee:
        employee = User(
            email="employee@shopsphere.com",
            phone="+14155550002",
            hashed_password=hash_password("Employee@1234!"),
            first_name="Marcus",
            last_name="Vance",
            role=UserRole.EMPLOYEE.value,
            status=UserStatus.ACTIVE.value,
            is_verified=True,
            registration_status="VERIFIED",
            department="Inventory & Catalog"
        )
        db.add(employee)

    # 3. Customer
    customer = db.query(User).filter(User.email == "customer@shopsphere.com").first()
    if not customer:
        customer = User(
            email="customer@shopsphere.com",
            phone="+14155551001",
            hashed_password=hash_password("Customer@1234!"),
            first_name="Sophia",
            last_name="Chen",
            role=UserRole.CUSTOMER.value,
            status=UserStatus.ACTIVE.value,
            is_verified=True,
            registration_status="VERIFIED"
        )
        db.add(customer)
        db.flush()

        # Customer Profile
        profile = CustomerProfile(
            user_id=customer.id,
            secondary_email="sophia.chen.alt@gmail.com",
            date_of_birth=date(1995, 5, 12),
            gender="FEMALE",
            marketing_opt_in=True,
            notes="VIP Loyalty Member"
        )
        db.add(profile)

        # Customer Addresses (Shipping & Billing)
        ship_addr = Address(
            user_id=customer.id,
            full_name="Sophia Chen",
            phone_number="+14155551001",
            address_type="SHIPPING",
            street_line1="742 Evergreen Terrace",
            city="Portland",
            state_province="OR",
            postal_code="97201",
            country="United States",
            is_default=True,
            is_default_billing=False,
            is_active=True
        )
        bill_addr = Address(
            user_id=customer.id,
            full_name="Sophia Chen",
            phone_number="+14155551001",
            address_type="BILLING",
            street_line1="100 Financial Plaza, Suite 400",
            city="Portland",
            state_province="OR",
            postal_code="97204",
            country="United States",
            is_default=False,
            is_default_billing=True,
            is_active=True
        )
        db.add(ship_addr)
        db.add(bill_addr)
        db.flush()

    # 4. Categories & Hierarchical Subcategories
    if db.query(Category).count() == 0:
        cat_elec = Category(name="Electronics", slug="electronics", description="Consumer electronics and devices", display_order=1, is_active=True)
        db.add(cat_elec)
        db.flush()

        cat_audio = Category(name="Audio & Headphones", slug="audio-headphones", parent_id=cat_elec.id, display_order=1, is_active=True)
        cat_laptops = Category(name="Laptops & Computers", slug="laptops-computers", parent_id=cat_elec.id, display_order=2, is_active=True)
        cat_phones = Category(name="Smartphones", slug="smartphones", parent_id=cat_elec.id, display_order=3, is_active=True)
        db.add_all([cat_audio, cat_laptops, cat_phones])

        cat_fashion = Category(name="Apparel & Fashion", slug="apparel-fashion", description="Designer clothing, shoes, and accessories", display_order=2, is_active=True)
        db.add(cat_fashion)
        db.flush()

        cat_men = Category(name="Men's Wear", slug="mens-wear", parent_id=cat_fashion.id, display_order=1, is_active=True)
        cat_women = Category(name="Women's Wear", slug="womens-wear", parent_id=cat_fashion.id, display_order=2, is_active=True)
        cat_shoes = Category(name="Footwear", slug="footwear", parent_id=cat_fashion.id, display_order=3, is_active=True)
        db.add_all([cat_men, cat_women, cat_shoes])
        db.flush()

    # 5. Brands
    if db.query(Brand).count() == 0:
        brand_sony = Brand(name="Sony", code="SONY", website_url="https://sony.com", status="ACTIVE")
        brand_apple = Brand(name="Apple", code="APPLE", website_url="https://apple.com", status="ACTIVE")
        brand_nike = Brand(name="Nike", code="NIKE", website_url="https://nike.com", status="ACTIVE")
        brand_samsung = Brand(name="Samsung", code="SAMSUNG", website_url="https://samsung.com", status="ACTIVE")
        db.add_all([brand_sony, brand_apple, brand_nike, brand_samsung])
        db.flush()

    # 6. Products & Variants
    cat_audio = db.query(Category).filter(Category.slug == "audio-headphones").first()
    cat_laptops = db.query(Category).filter(Category.slug == "laptops-computers").first()
    cat_shoes = db.query(Category).filter(Category.slug == "footwear").first()

    brand_sony = db.query(Brand).filter(Brand.code == "SONY").first()
    brand_apple = db.query(Brand).filter(Brand.code == "APPLE").first()
    brand_nike = db.query(Brand).filter(Brand.code == "NIKE").first()

    p1 = db.query(Product).filter(Product.base_sku == "SONY-WH1000XM5").first()
    if not p1:
        p1 = Product(
            name="Sony WH-1000XM5 Wireless Noise-Canceling Headphones",
            slug="sony-wh-1000xm5-wireless-headphones",
            description="Industry-leading noise cancellation with two processors and 8 microphones.",
            short_description="Flagship wireless noise-canceling headphones with 30-hour battery life.",
            base_price=Decimal("399.99"),
            cost_price=Decimal("240.00"),
            compare_at_price=Decimal("449.99"),
            base_sku="SONY-WH1000XM5",
            currency="USD",
            category_id=cat_audio.id if cat_audio else None,
            brand_id=brand_sony.id if brand_sony else None,
            status="ACTIVE",
            is_featured=True
        )
        db.add(p1)
        db.flush()

        v1_1 = ProductVariant(
            product_id=p1.id,
            sku="WH1000XM5-BLK",
            title="Color: Midnight Black",
            price=Decimal("399.99"),
            attributes_json=json.dumps({"color": "Midnight Black"}),
            stock_quantity=45,
            low_stock_threshold=5,
            availability_status="IN_STOCK",
            status="ACTIVE"
        )
        v1_2 = ProductVariant(
            product_id=p1.id,
            sku="WH1000XM5-SLV",
            title="Color: Platinum Silver",
            price=Decimal("399.99"),
            attributes_json=json.dumps({"color": "Platinum Silver"}),
            stock_quantity=3,
            low_stock_threshold=5,
            availability_status="LOW_STOCK",
            status="ACTIVE"
        )
        db.add_all([v1_1, v1_2])

    p2 = db.query(Product).filter(Product.base_sku == "APPL-MBA15-M3").first()
    if not p2:
        p2 = Product(
            name="Apple MacBook Air 15-inch M3 Chip",
            slug="apple-macbook-air-15-m3",
            description="Strikingly thin design with the lightning-fast Apple M3 silicon processor.",
            short_description="15.3-inch Liquid Retina display with 18 hours battery life.",
            base_price=Decimal("1299.00"),
            cost_price=Decimal("950.00"),
            base_sku="APPL-MBA15-M3",
            currency="USD",
            category_id=cat_laptops.id if cat_laptops else None,
            brand_id=brand_apple.id if brand_apple else None,
            status="ACTIVE",
            is_featured=True
        )
        db.add(p2)
        db.flush()

        v2_1 = ProductVariant(
            product_id=p2.id,
            sku="MBA15-16-512-SGRY",
            title="16GB Unified Memory / 512GB SSD / Space Gray",
            price=Decimal("1499.00"),
            attributes_json=json.dumps({"ram": "16GB", "storage": "512GB", "color": "Space Gray"}),
            stock_quantity=15,
            low_stock_threshold=3,
            availability_status="IN_STOCK",
            status="ACTIVE"
        )
        v2_2 = ProductVariant(
            product_id=p2.id,
            sku="MBA15-8-256-SLV",
            title="8GB Unified Memory / 256GB SSD / Silver",
            price=Decimal("1299.00"),
            attributes_json=json.dumps({"ram": "8GB", "storage": "256GB", "color": "Silver"}),
            stock_quantity=0,
            low_stock_threshold=3,
            availability_status="OUT_OF_STOCK",
            status="ACTIVE"
        )
        db.add_all([v2_1, v2_2])

    p3 = db.query(Product).filter(Product.base_sku == "NIKE-PEG40").first()
    if not p3:
        p3 = Product(
            name="Nike Air Zoom Pegasus 40 Running Shoes",
            slug="nike-air-zoom-pegasus-40",
            description="A responsive ride for any run with Nike React technology and Zoom Air units.",
            short_description="Everyday running shoe engineered for bounce and breathability.",
            base_price=Decimal("130.00"),
            cost_price=Decimal("65.00"),
            base_sku="NIKE-PEG40",
            currency="USD",
            category_id=cat_shoes.id if cat_shoes else None,
            brand_id=brand_nike.id if brand_nike else None,
            status="ACTIVE",
            is_featured=False
        )
        db.add(p3)
        db.flush()

        v3_1 = ProductVariant(
            product_id=p3.id,
            sku="PEG40-WHT-9",
            title="Size: 9 / White-Volt",
            price=Decimal("130.00"),
            attributes_json=json.dumps({"size": "9", "color": "White-Volt"}),
            stock_quantity=22,
            low_stock_threshold=5,
            availability_status="IN_STOCK",
            status="ACTIVE"
        )
        v3_2 = ProductVariant(
            product_id=p3.id,
            sku="PEG40-BLK-10",
            title="Size: 10 / Black-Anthracite",
            price=Decimal("130.00"),
            attributes_json=json.dumps({"size": "10", "color": "Black"}),
            stock_quantity=18,
            low_stock_threshold=5,
            availability_status="IN_STOCK",
            status="ACTIVE"
        )
        db.add_all([v3_1, v3_2])

    db.flush()

    # =========================================================================
    # MODULE 11: Product Attributes & Category Links
    # =========================================================================
    if db.query(Attribute).count() == 0:
        attr_color = Attribute(name="Color", code="color", data_type="SELECT", is_filterable=True)
        attr_size = Attribute(name="Size", code="size", data_type="SELECT", is_filterable=True)
        attr_material = Attribute(name="Material", code="material", data_type="TEXT", is_filterable=True)
        attr_ram = Attribute(name="RAM", code="ram", data_type="SELECT", is_filterable=True)
        attr_storage = Attribute(name="Storage", code="storage", data_type="SELECT", is_filterable=True)
        db.add_all([attr_color, attr_size, attr_material, attr_ram, attr_storage])
        db.flush()

        # Options for Color
        for c in ["Black", "Silver", "Navy Blue", "White", "Platinum"]:
            db.add(AttributeOption(attribute_id=attr_color.id, value=c))
        # Options for Size
        for s in ["S", "M", "L", "XL", "9", "10", "11"]:
            db.add(AttributeOption(attribute_id=attr_size.id, value=s))
        # Options for RAM
        for r in ["8GB", "16GB", "32GB", "64GB"]:
            db.add(AttributeOption(attribute_id=attr_ram.id, value=r))
        # Options for Storage
        for st in ["256GB", "512GB", "1TB", "2TB"]:
            db.add(AttributeOption(attribute_id=attr_storage.id, value=st))

        db.flush()

        # Link Category Attributes
        cat_fashion = db.query(Category).filter(Category.slug == "apparel-fashion").first()
        if cat_fashion:
            db.add(CategoryAttribute(category_id=cat_fashion.id, attribute_id=attr_color.id, is_required=True))
            db.add(CategoryAttribute(category_id=cat_fashion.id, attribute_id=attr_size.id, is_required=True))
            db.add(CategoryAttribute(category_id=cat_fashion.id, attribute_id=attr_material.id, is_required=False))

        cat_elec = db.query(Category).filter(Category.slug == "electronics").first()
        if cat_elec:
            db.add(CategoryAttribute(category_id=cat_elec.id, attribute_id=attr_ram.id, is_required=False))
            db.add(CategoryAttribute(category_id=cat_elec.id, attribute_id=attr_storage.id, is_required=False))

        db.flush()

        # Assign attribute values to products
        if p1:
            db.add(ProductAttributeValue(product_id=p1.id, attribute_id=attr_color.id, value="Black"))
            db.add(ProductAttributeValue(product_id=p1.id, attribute_id=attr_material.id, value="Recycled Acrylonitrile Butadiene Styrene"))
        if p2:
            db.add(ProductAttributeValue(product_id=p2.id, attribute_id=attr_ram.id, value="16GB"))
            db.add(ProductAttributeValue(product_id=p2.id, attribute_id=attr_storage.id, value="512GB"))
        if p3:
            db.add(ProductAttributeValue(product_id=p3.id, attribute_id=attr_color.id, value="White"))
            db.add(ProductAttributeValue(product_id=p3.id, attribute_id=attr_material.id, value="Engineered Mesh & Rubber"))

        db.flush()

    # =========================================================================
    # MODULE 12: Product Pricing & Validity Periods
    # =========================================================================
    if db.query(ProductPrice).count() == 0 and p1:
        now = datetime.now(timezone.utc)
        sale_end = now + timedelta(days=14)

        # Sony WH-1000XM5 on sale for 2 weeks
        price_p1 = ProductPrice(
            product_id=p1.id,
            base_price=Decimal("399.99"),
            sale_price=Decimal("349.99"),
            sale_start_date=now - timedelta(days=1),
            sale_end_date=sale_end,
            currency="USD",
            is_active=True
        )
        db.add(price_p1)
        db.flush()

        # Initial price history
        db.add(PriceHistory(
            product_id=p1.id,
            old_base_price=None,
            new_base_price=Decimal("399.99"),
            old_sale_price=None,
            new_sale_price=Decimal("349.99"),
            reason="Autumn promotional pricing campaign"
        ))

        if p2:
            price_p2 = ProductPrice(
                product_id=p2.id,
                base_price=Decimal("1299.00"),
                currency="USD",
                is_active=True
            )
            db.add(price_p2)
            db.add(PriceHistory(
                product_id=p2.id,
                new_base_price=Decimal("1299.00"),
                reason="Standard MSRP launch price"
            ))

        db.flush()

    # =========================================================================
    # MODULE 13: Inventory Tracking & Stock Movements
    # =========================================================================
    if db.query(InventoryItem).count() == 0 and p1:
        inv1 = InventoryItem(
            product_id=p1.id,
            variant_id=None,
            total_quantity=48,
            available_quantity=45,
            reserved_quantity=3,
            low_stock_threshold=10
        )
        db.add(inv1)
        db.flush()

        # Movement records
        db.add(StockMovement(
            inventory_item_id=inv1.id,
            product_id=p1.id,
            movement_type="ADDITION",
            quantity=50,
            balance_after=50,
            reference_type="PURCHASE_ORDER",
            reference_id="PO-2026-0089",
            notes="Initial factory batch intake"
        ))
        db.add(StockMovement(
            inventory_item_id=inv1.id,
            product_id=p1.id,
            movement_type="RESERVATION",
            quantity=3,
            balance_after=47,
            reference_type="ORDER_RESERVATION",
            reference_id="CART-RESERV-004",
            notes="Customer checkout hold"
        ))
        db.add(StockMovement(
            inventory_item_id=inv1.id,
            product_id=p1.id,
            movement_type="REDUCTION",
            quantity=-2,
            balance_after=48,
            reference_type="MANUAL_ADJUSTMENT",
            reference_id="DMG-001",
            notes="Packaging damaged during unloading"
        ))
        db.flush()

    # =========================================================================
    # MODULE 14: Warehouse Facilities & Inventory Allocations
    # =========================================================================
    if db.query(Warehouse).count() == 0:
        wh_east = Warehouse(
            code="WH-EAST-01",
            name="East Coast Fulfillment Center",
            address_line1="100 Logistics Parkway",
            city="Allentown",
            state_province="PA",
            postal_code="18109",
            country="United States",
            capacity_units=25000,
            current_utilization=120,
            status="ACTIVE"
        )
        wh_west = Warehouse(
            code="WH-WEST-01",
            name="West Coast Logistics Hub",
            address_line1="500 Harbour Way",
            city="Reno",
            state_province="NV",
            postal_code="89502",
            country="United States",
            capacity_units=30000,
            current_utilization=75,
            status="ACTIVE"
        )
        db.add_all([wh_east, wh_west])
        db.flush()

        if p1:
            db.add(WarehouseInventory(
                warehouse_id=wh_east.id,
                product_id=p1.id,
                quantity=30,
                reserved_quantity=2,
                aisle_location="Aisle 4, Bay C, Shelf 2"
            ))
            db.add(WarehouseInventory(
                warehouse_id=wh_west.id,
                product_id=p1.id,
                quantity=18,
                reserved_quantity=1,
                aisle_location="Aisle 12, Bay A, Shelf 1"
            ))

        db.flush()

    # =========================================================================
    # MODULE 15: Inventory Transfers
    # =========================================================================
    if db.query(InventoryTransfer).count() == 0 and p1:
        wh_e = db.query(Warehouse).filter(Warehouse.code == "WH-EAST-01").first()
        wh_w = db.query(Warehouse).filter(Warehouse.code == "WH-WEST-01").first()
        if wh_e and wh_w:
            trf = InventoryTransfer(
                transfer_number="TRF-20261104-E01W01",
                source_warehouse_id=wh_e.id,
                destination_warehouse_id=wh_w.id,
                product_id=p1.id,
                requested_quantity=10,
                dispatched_quantity=10,
                received_quantity=0,
                status="DISPATCHED",
                notes="Seasonal rebalancing between East and West logistics hubs",
                requested_by_user_id=employee.id,
                dispatched_by_user_id=employee.id,
                dispatched_at=datetime.now(timezone.utc)
            )
            db.add(trf)
            db.flush()

    # =========================================================================
    # MODULE 16: Low-Stock Management & Thresholds
    # =========================================================================
    if db.query(LowStockThreshold).count() == 0 and p1:
        th = LowStockThreshold(
            product_id=p1.id,
            threshold=15,
            reorder_quantity=50
        )
        db.add(th)
        db.add(StockThresholdChangeHistory(
            product_id=p1.id,
            old_threshold=10,
            new_threshold=15,
            change_reason="Increased safety stock for Q4 peak volume",
            changed_by_user_id=employee.id
        ))
        db.add(RestockAlert(
            product_id=p1.id,
            current_stock=12,
            threshold=15,
            severity="LOW",
            is_resolved=False,
            notes="Stock fell below configured threshold (15)."
        ))
        db.flush()

    # =========================================================================
    # MODULE 17 & 18: Shopping Cart & Price Calculation
    # =========================================================================
    if db.query(Cart).count() == 0 and customer and p1:
        cart = Cart(user_id=customer.id, status="ACTIVE")
        db.add(cart)
        db.flush()
        db.add(CartItem(
            cart_id=cart.id,
            product_id=p1.id,
            quantity=2
        ))
        db.flush()

    # =========================================================================
    # MODULE 19: Wishlist Management
    # =========================================================================
    if db.query(WishlistItem).count() == 0 and customer and p1:
        db.add(WishlistItem(
            user_id=customer.id,
            product_id=p1.id
        ))
        db.flush()

    # =========================================================================
    # MODULE 20: Coupon Management
    # =========================================================================
    if db.query(Coupon).count() == 0:
        c1 = Coupon(
            code="WELCOME10",
            description="10% discount for registered new customers",
            discount_type="PERCENTAGE",
            discount_value=Decimal("10.00"),
            min_purchase_amount=Decimal("50.00"),
            max_discount_amount=Decimal("50.00"),
            usage_limit=1000,
            used_count=12,
            is_active=True
        )
        c2 = Coupon(
            code="SAVE20",
            description="$20 off orders over $150",
            discount_type="FIXED_AMOUNT",
            discount_value=Decimal("20.00"),
            min_purchase_amount=Decimal("150.00"),
            usage_limit=500,
            used_count=4,
            is_active=True
        )
        db.add_all([c1, c2])
        db.flush()

    # =========================================================================
    # MODULE 21: Promotion Management
    # =========================================================================
    if db.query(Promotion).count() == 0:
        now = datetime.now(timezone.utc)
        p_fall = Promotion(
            name="Fall Tech Fest 2026",
            code="FALLTECH2026",
            description="15% discount across all consumer electronics",
            promotion_type="PERCENTAGE_DISCOUNT",
            discount_value=Decimal("15.00"),
            min_order_amount=Decimal("75.00"),
            start_date=now - timedelta(days=5),
            end_date=now + timedelta(days=25),
            is_active=True
        )
        db.add(p_fall)
        db.flush()

    # =========================================================================
    # MODULE 22: Tax Management
    # =========================================================================
    if db.query(TaxRate).count() == 0:
        t_fed = TaxRate(
            name="US Default State Tax",
            country="USA",
            state_province="*",
            rate_percentage=Decimal("8.00"),
            is_active=True
        )
        t_il = TaxRate(
            name="Illinois State & Municipal Tax",
            country="USA",
            state_province="IL",
            rate_percentage=Decimal("8.75"),
            is_active=True
        )
        t_ca = TaxRate(
            name="California State Sales Tax",
            country="USA",
            state_province="CA",
            rate_percentage=Decimal("7.25"),
            is_active=True
        )
        db.add_all([t_fed, t_il, t_ca])
        db.flush()

    # =========================================================================
    # MODULE 23: Shipping Configuration
    # =========================================================================
    if db.query(ShippingMethod).count() == 0:
        sm_std = ShippingMethod(
            name="Standard Ground Delivery",
            code="STANDARD_GROUND",
            description="Cost-effective reliable ground delivery",
            base_charge=Decimal("5.99"),
            free_shipping_threshold=Decimal("75.00"),
            estimated_days_min=3,
            estimated_days_max=5,
            is_active=True
        )
        sm_exp = ShippingMethod(
            name="Express 2-Day Air",
            code="EXPRESS_2DAY",
            description="Fast priority air delivery within 2 business days",
            base_charge=Decimal("14.99"),
            free_shipping_threshold=Decimal("200.00"),
            estimated_days_min=2,
            estimated_days_max=3,
            is_active=True
        )
        sm_overnight = ShippingMethod(
            name="Priority Next-Day Overnight",
            code="OVERNIGHT",
            description="Guaranteed next-morning expedited courier",
            base_charge=Decimal("29.99"),
            estimated_days_min=1,
            estimated_days_max=1,
            is_active=True
        )
        db.add_all([sm_std, sm_exp, sm_overnight])
        db.flush()

    # =========================================================================
    # MODULE 24 & 25: Orders & Order Item History
    # =========================================================================
    if db.query(Order).count() == 0 and customer and p1:
        ord_num = "ORD-20261104-DEMO01"
        cust_addr = db.query(Address).filter(Address.user_id == customer.id).first()
        addr_id = cust_addr.id if cust_addr else None
        v1 = db.query(ProductVariant).filter(ProductVariant.product_id == p1.id).first()

        seed_order = Order(
            order_number=ord_num,
            user_id=customer.id,
            shipping_address_id=addr_id,
            billing_address_id=addr_id,
            shipping_address_snapshot="Sophia Chen, 742 Evergreen Terrace, Portland, OR 97201, United States",
            billing_address_snapshot="Sophia Chen, 100 Financial Plaza, Suite 400, Portland, OR 97204, United States",
            status="CONFIRMED",
            payment_status="PAID",
            subtotal_amount=Decimal("3799.98"),
            discount_amount=Decimal("189.99"),
            tax_amount=Decimal("288.80"),
            shipping_amount=Decimal("0.00"),
            total_amount=Decimal("3898.79"),
            coupon_code="WELCOME10",
            shipping_method_code="STANDARD_GROUND",
            notes="Demo customer checkout order"
        )
        db.add(seed_order)
        db.flush()

        db.add(OrderItem(
            order_id=seed_order.id,
            product_id=p1.id,
            variant_id=v1.id if v1 else None,
            product_name=p1.name,
            sku=v1.sku if v1 else p1.base_sku,
            unit_price=Decimal("1899.99"),
            quantity=2,
            subtotal=Decimal("3799.98"),
            description_snapshot=p1.description,
            variant_attributes_snapshot={"Color": "Matte Black", "Edition": "Pro ANC"},
            fulfillment_status="PROCESSING"
        ))
        db.add(OrderStatusHistory(
            order_id=seed_order.id,
            from_status=None,
            to_status="CONFIRMED",
            notes="Order successfully placed via checkout",
            changed_by_user_id=customer.id
        ))
        db.flush()

    # =========================================================================
    # MODULE 41: Notification Management
    # =========================================================================
    if db.query(Notification).count() == 0 and customer and employee:
        db.add(Notification(
            user_id=customer.id,
            title="Order Confirmed",
            message="Your order ORD-20261104-DEMO01 has been confirmed and is being processed.",
            notification_type="ORDER_UPDATE",
            severity="SUCCESS",
            reference_id="ORD-20261104-DEMO01",
            is_read=False
        ))
        db.add(Notification(
            user_id=customer.id,
            title="Payment Received",
            message="Payment of $1,846.80 received successfully.",
            notification_type="PAYMENT_STATUS",
            severity="INFO",
            reference_id="ORD-20261104-DEMO01",
            is_read=True,
            read_at=datetime.now(timezone.utc)
        ))
        db.add(Notification(
            user_id=employee.id,
            title="Low-Stock Alert",
            message="ProBook X1 Carbon (Variant #1) is below reorder threshold (12/15).",
            notification_type="INVENTORY_EXCEPTION",
            severity="WARNING",
            reference_id="VAR-1",
            is_read=False
        ))
        db.flush()

    # =========================================================================
    # MODULE 42: Email and SMS Notifications
    # =========================================================================
    if db.query(NotificationProviderConfig).count() == 0:
        db.add(NotificationProviderConfig(
            provider_type="EMAIL",
            provider_name="SendGrid",
            sender_address="no-reply@shopsphere.com",
            api_key_masked="SG.live_********************",
            is_active=True,
            is_default=True
        ))
        db.add(NotificationProviderConfig(
            provider_type="SMS",
            provider_name="Twilio",
            sender_address="+18005550199",
            api_key_masked="AC_live_********************",
            is_active=True,
            is_default=True
        ))
        db.flush()

    if db.query(MessageLog).count() == 0 and customer:
        db.add(MessageLog(
            channel="EMAIL",
            recipient=customer.email,
            template_type="ORDER_CONFIRMATION",
            subject="Order Confirmation - ORD-20261104-DEMO01",
            body="Thank you for your purchase! Your order is being packed.",
            status="SENT"
        ))
        db.add(MessageLog(
            channel="SMS",
            recipient=customer.phone or "+15551234567",
            template_type="SHIPMENT_UPDATE",
            subject="Shipment Update",
            body="Your ShopSphere order is scheduled for dispatch via Standard Ground.",
            status="DELIVERED"
        ))
        db.flush()

    # =========================================================================
    # MODULE 43: Seller and Supplier Management
    # =========================================================================
    sup1 = db.query(Supplier).filter(Supplier.supplier_code == "SUP-GLOBAL-01").first()
    if not sup1:
        sup1 = Supplier(
            supplier_code="SUP-GLOBAL-01",
            company_name="Apex Global Logistics & Components",
            supplier_type="SUPPLIER",
            contact_name="Marcus Vance",
            email="marcus.vance@apexlogistics.io",
            phone="+14155552671",
            tax_id="US-94-3829102",
            business_registration_number="CORP-883921",
            address_line="100 Silicon Way, Suite 400",
            city="San Jose",
            state="CA",
            country="USA",
            postal_code="95134",
            status="APPROVED",
            rating=4.9,
            notes="Primary OEM hardware and electronics distributor."
        )
        db.add(sup1)
        db.flush()

        db.add(SupplierHistory(
            supplier_id=sup1.id,
            changed_by_user_id=admin.id,
            action="APPROVAL",
            from_status="PENDING_APPROVAL",
            to_status="APPROVED",
            notes="Full verification completed."
        ))
        if p1:
            db.add(ProductSupplier(
                supplier_id=sup1.id,
                product_id=p1.id,
                supplier_sku="APEX-PBX1-2026",
                negotiated_cost=Decimal("1100.00"),
                lead_time_days=5,
                is_primary=True
            ))
        db.flush()

    # =========================================================================
    # MODULE 44: Purchase Order Management
    # =========================================================================
    wh_east = db.query(Warehouse).filter(Warehouse.code == "WH-EAST-01").first()
    if db.query(PurchaseOrder).count() == 0 and sup1 and wh_east and p1:
        po_num = "PO-20261104-APEX01"
        po = PurchaseOrder(
            po_number=po_num,
            supplier_id=sup1.id,
            warehouse_id=wh_east.id,
            created_by_user_id=employee.id,
            status="RECEIVED",
            total_cost=Decimal("55000.00"),
            expected_delivery_date=datetime.now(timezone.utc) + timedelta(days=7),
            notes="Bulk restock order for upcoming season"
        )
        db.add(po)
        db.flush()

        db.add(PurchaseOrderItem(
            purchase_order_id=po.id,
            product_id=p1.id,
            quantity_ordered=50,
            quantity_received=50,
            unit_cost=Decimal("1100.00"),
            total_cost=Decimal("55000.00")
        ))
        db.add(POStatusHistory(
            purchase_order_id=po.id,
            changed_by_user_id=employee.id,
            from_status=None,
            to_status="SUBMITTED",
            notes="Issued PO to supplier"
        ))
        db.add(POStatusHistory(
            purchase_order_id=po.id,
            changed_by_user_id=employee.id,
            from_status="SUBMITTED",
            to_status="RECEIVED",
            notes="All 50 units received at East Coast Hub"
        ))
        db.flush()

        # =====================================================================
        # MODULE 45: Supplier Invoice Management
        # =====================================================================
        db.add(SupplierInvoice(
            invoice_number="INV-APEX-2026-9901",
            supplier_id=sup1.id,
            purchase_order_id=po.id,
            invoice_date=datetime.now(timezone.utc) - timedelta(days=2),
            due_date=datetime.now(timezone.utc) + timedelta(days=28),
            subtotal=Decimal("55000.00"),
            tax_amount=Decimal("0.00"),
            total_amount=Decimal("55000.00"),
            payment_status="PAID",
            amount_paid=Decimal("55000.00"),
            notes="Paid in full via corporate wire"
        ))
        db.flush()

    # =========================================================================
    # MODULE 46: Audit Log Management
    # =========================================================================
    if db.query(AdminAuditLog).count() == 0 and admin and p1:
        db.add(AdminAuditLog(
            actor_id=admin.id,
            action="PRODUCT_PRICING_UPDATED",
            entity_type="PRODUCT",
            entity_id=str(p1.id),
            ip_address="127.0.0.1",
            old_values=json.dumps({"base_price": "1999.99"}),
            new_values=json.dumps({"base_price": "1899.99"}),
            reason="Market competition price adjustment",
            is_immutable=True
        ))
        db.flush()

    # =========================================================================
    # MODULE 49: Background Tasks
    # =========================================================================
    if db.query(BackgroundTaskJob).count() == 0 and admin:
        db.add(BackgroundTaskJob(
            task_name="ScheduledSummary_Daily_Seed",
            task_type="SCHEDULED_SUMMARY",
            status="COMPLETED",
            payload=json.dumps({"frequency": "daily"}),
            result_summary="Daily inventory and order reconciliation passed without deviations.",
            created_by_user_id=admin.id,
            started_at=datetime.now(timezone.utc) - timedelta(hours=1),
            completed_at=datetime.now(timezone.utc) - timedelta(minutes=58)
        ))
        db.flush()

    # =========================================================================
    # MODULES 26 - 40: Seed Demo Data
    # =========================================================================
    # 1. COD Config
    if db.query(CODConfig).count() == 0:
        db.add(CODConfig(
            is_enabled=True,
            min_order_amount=Decimal("10.00"),
            max_order_amount=Decimal("1500.00"),
            restricted_postal_codes=["99999", "00000", "REMOTE-1"],
            extra_fee=Decimal("5.00")
        ))
        db.flush()

    # Find demo order
    demo_order = db.query(Order).first()
    if demo_order:
        # 2. Payment & Transactions (Modules 29 & 30)
        if db.query(Payment).filter(Payment.order_id == demo_order.id).count() == 0:
            demo_pay = Payment(
                order_id=demo_order.id,
                user_id=demo_order.user_id,
                payment_method="CREDIT_CARD",
                amount=demo_order.total_amount,
                currency="USD",
                status="SUCCESSFUL",
                gateway_provider="SANDBOX_GATEWAY",
                transaction_reference=f"PAY-SEED-{demo_order.id}"
            )
            db.add(demo_pay)
            db.flush()

            db.add(PaymentTransaction(
                payment_id=demo_pay.id,
                order_id=demo_order.id,
                action="CAPTURE",
                status="SUCCESS",
                gateway_reference=f"AUTH-SEED-{demo_order.id}",
                response_payload={"auth_code": "APPROVED_2026", "sandbox": True}
            ))
            db.flush()

        # 3. Shipment, Tracking & Delivery (Modules 33, 34, 35)
        if db.query(Shipment).filter(Shipment.order_id == demo_order.id).count() == 0:
            demo_shp = Shipment(
                shipment_number=f"SHP-SEED-{demo_order.id}",
                order_id=demo_order.id,
                carrier_name="FedEx",
                tracking_number=f"TRK-FDX-SEED{demo_order.id}",
                status="DELIVERED",
                shipping_label_url=f"/static/labels/SHP-SEED-{demo_order.id}.pdf",
                dispatched_at=datetime.now(timezone.utc) - timedelta(days=3),
                delivered_at=datetime.now(timezone.utc) - timedelta(days=1)
            )
            db.add(demo_shp)
            db.flush()

            db.add(TrackingEvent(
                shipment_id=demo_shp.id,
                tracking_number=demo_shp.tracking_number,
                event_type="DELIVERED",
                location="San Francisco, CA",
                description="Delivered to front desk - signed by S. Chen"
            ))

            db.add(DeliveryAssignment(
                shipment_id=demo_shp.id,
                driver_name="Dave Courier",
                driver_phone="+1-555-019-881",
                status="DELIVERED",
                recipient_signature_name="Sophia Chen",
                confirmation_notes="Delivered on first attempt."
            ))
            db.flush()

    # 4. Product Reviews & QA (Modules 38 & 39)
    if p1 and customer and db.query(ProductReview).count() == 0:
        db.add(ProductReview(
            product_id=p1.id,
            user_id=customer.id,
            rating=5,
            title="Exceptional build quality!",
            comment="The performance and battery life on this laptop exceeded all my expectations for 4K video rendering.",
            is_verified_purchase=True,
            status="APPROVED"
        ))

        demo_q = ProductQuestion(
            product_id=p1.id,
            user_id=customer.id,
            question_text="Does this laptop come with a 140W USB-C GaN power adapter included in the box?",
            status="APPROVED"
        )
        db.add(demo_q)
        db.flush()

        if employee:
            db.add(ProductAnswer(
                question_id=demo_q.id,
                user_id=employee.id,
                answer_text="Yes! The original package includes the official 140W USB-C Fast Charger with braided cable.",
                is_staff_answer=True
            ))
        db.flush()

    # 5. Support Tickets (Module 40)
    if customer and db.query(SupportTicket).count() == 0:
        tck = SupportTicket(
            ticket_number="TCK-SEED-001",
            user_id=customer.id,
            subject="Question regarding order invoice tax breakdown",
            category="PAYMENT",
            priority="NORMAL",
            status="OPEN"
        )
        db.add(tck)
        db.flush()

        db.add(TicketMessage(
            ticket_id=tck.id,
            sender_user_id=customer.id,
            message="Hello, could you please provide a PDF VAT tax receipt for my corporate filing?",
            is_internal_note=False
        ))
        db.flush()

    db.commit()
    print("Seed data (Modules 1 - 50) successfully populated.")


if __name__ == "__main__":
    ensure_database_schema(engine)
    session = SessionLocal()
    try:
        seed_initial_data(session)
    finally:
        session.close()
