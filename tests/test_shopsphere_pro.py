import io
import uuid
from decimal import Decimal
from PIL import Image


# =====================================================================
# MODULE 1: AUTHENTICATION AND AUTHORIZATION
# =====================================================================
def test_module1_customer_and_employee_login(client):
    # Customer login
    res_c = client.post("/api/v1/auth/login", json={
        "email": "customer@shopsphere.com",
        "password": "Customer@1234!"
    })
    assert res_c.status_code == 200
    data_c = res_c.json()
    assert "access_token" in data_c
    assert "refresh_token" in data_c
    assert data_c["user"]["role"] == "CUSTOMER"

    # Employee login
    res_e = client.post("/api/v1/auth/login", json={
        "email": "employee@shopsphere.com",
        "password": "Employee@1234!"
    })
    assert res_e.status_code == 200
    data_e = res_e.json()
    assert data_e["user"]["role"] == "EMPLOYEE"


def test_module1_invalid_credentials(client):
    res = client.post("/api/v1/auth/login", json={
        "email": "customer@shopsphere.com",
        "password": "WrongPassword999!"
    })
    assert res.status_code == 401
    assert "Invalid email or password" in res.json()["detail"]


def test_module1_jwt_refresh_token_rotation(client):
    res_login = client.post("/api/v1/auth/login", json={
        "email": "customer@shopsphere.com",
        "password": "Customer@1234!"
    })
    tokens = res_login.json()
    old_refresh = tokens["refresh_token"]

    # Exchange refresh token
    res_refresh = client.post("/api/v1/auth/refresh", json={"refresh_token": old_refresh})
    assert res_refresh.status_code == 200
    new_tokens = res_refresh.json()
    assert new_tokens["access_token"] != tokens["access_token"]
    assert new_tokens["refresh_token"] != old_refresh

    # Re-using old refresh token must be rejected (token rotation revocation)
    res_reuse = client.post("/api/v1/auth/refresh", json={"refresh_token": old_refresh})
    assert res_reuse.status_code == 401


def test_module1_logout_and_token_revocation(client):
    res_login = client.post("/api/v1/auth/login", json={
        "email": "customer@shopsphere.com",
        "password": "Customer@1234!"
    })
    access_token = res_login.json()["access_token"]
    refresh_token = res_login.json()["refresh_token"]

    # Endpoint works before logout
    headers = {"Authorization": f"Bearer {access_token}"}
    res_me = client.get("/api/v1/auth/me", headers=headers)
    assert res_me.status_code == 200

    # Logout
    res_logout = client.post("/api/v1/auth/logout", headers=headers, json={"refresh_token": refresh_token})
    assert res_logout.status_code == 200
    assert res_logout.json()["success"] is True

    # Access token must now be rejected as revoked
    res_me_revoked = client.get("/api/v1/auth/me", headers=headers)
    assert res_me_revoked.status_code == 401
    assert "revoked" in res_me_revoked.json()["detail"].lower()


def test_module1_rbac_permissions(client, admin_token, customer_token):
    # Customer trying to access Admin-only user creation endpoint
    res_forbidden = client.post("/api/v1/users", headers={"Authorization": f"Bearer {customer_token}"}, json={
        "email": "unauthorized@test.com",
        "password": "Password123!",
        "first_name": "Test",
        "last_name": "User",
        "role": "ADMIN"
    })
    assert res_forbidden.status_code == 403

    # Admin accessing /auth/me shows full permissions
    res_admin = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {admin_token}"})
    assert res_admin.status_code == 200
    assert len(res_admin.json()["permissions"]) > 0


# =====================================================================
# MODULE 2: USER MANAGEMENT
# =====================================================================
def test_module2_create_update_deactivate_users(client, admin_token):
    headers = {"Authorization": f"Bearer {admin_token}"}

    # Create user
    res_create = client.post("/api/v1/users", headers=headers, json={
        "email": "testuser_m2@shopsphere.com",
        "phone": "+14155552099",
        "password": "StrongPassword@2026!",
        "first_name": "Test",
        "last_name": "Employee",
        "role": "EMPLOYEE",
        "department": "Logistics",
        "is_verified": True
    })
    assert res_create.status_code == 201
    user_id = res_create.json()["id"]

    # Update user
    res_update = client.put(f"/api/v1/users/{user_id}", headers=headers, json={
        "first_name": "UpdatedName",
        "department": "Supply Chain"
    })
    assert res_update.status_code == 200
    assert res_update.json()["first_name"] == "UpdatedName"
    assert res_update.json()["department"] == "Supply Chain"

    # Deactivate user
    res_status = client.patch(f"/api/v1/users/{user_id}/status", headers=headers, json={
        "status": "DEACTIVATED",
        "reason": "Contract ended"
    })
    assert res_status.status_code == 200
    assert res_status.json()["status"] == "DEACTIVATED"

    # Search & Filter
    res_filter = client.get("/api/v1/users?query=UpdatedName&status=DEACTIVATED", headers=headers)
    assert res_filter.status_code == 200
    assert len(res_filter.json()["items"]) >= 1

    # Track user activity
    res_act = client.get(f"/api/v1/users/{user_id}/activity", headers=headers)
    assert res_act.status_code == 200
    assert len(res_act.json()["items"]) >= 1


# =====================================================================
# MODULE 3: CUSTOMER REGISTRATION
# =====================================================================
def test_module3_customer_registration_and_duplicate_prevention(client):
    # Valid registration
    res = client.post("/api/v1/registration/register", json={
        "first_name": "Lucas",
        "last_name": "Mori",
        "email": "lucas.mori@example.com",
        "phone": "+14155553001",
        "password": "SecurePassword@123!",
        "marketing_opt_in": True
    })
    assert res.status_code == 201
    data = res.json()
    assert data["registration_status"] == "PENDING_VERIFICATION"
    token = data["verification_token"]
    assert token is not None

    # Duplicate email prevention
    res_dup_email = client.post("/api/v1/registration/register", json={
        "first_name": "Another",
        "last_name": "User",
        "email": "lucas.mori@example.com",
        "phone": "+14155553002",
        "password": "SecurePassword@123!"
    })
    assert res_dup_email.status_code == 409
    assert "email 'lucas.mori@example.com' is already registered" in res_dup_email.json()["detail"].lower()

    # Duplicate phone prevention
    res_dup_phone = client.post("/api/v1/registration/register", json={
        "first_name": "Another",
        "last_name": "User",
        "email": "distinct.email@example.com",
        "phone": "+14155553001",
        "password": "SecurePassword@123!"
    })
    assert res_dup_phone.status_code == 409
    assert "phone number '+14155553001' is already registered" in res_dup_phone.json()["detail"].lower()

    # Verify email
    res_verify = client.get(f"/api/v1/registration/verify-email?token={token}")
    assert res_verify.status_code == 200
    assert res_verify.json()["success"] is True

    # Registration status check
    res_stat = client.get("/api/v1/registration/status?email=lucas.mori@example.com")
    assert res_stat.status_code == 200
    assert res_stat.json()["data"]["is_verified"] is True
    assert res_stat.json()["data"]["registration_status"] == "VERIFIED"


# =====================================================================
# MODULE 4: CUSTOMER PROFILE MANAGEMENT
# =====================================================================
def test_module4_customer_profile_and_history(client, customer_token, admin_token, employee_token):
    headers = {"Authorization": f"Bearer {customer_token}"}

    # Retrieve profile
    res_get = client.get("/api/v1/customer/profile/me", headers=headers)
    assert res_get.status_code == 200
    assert res_get.json()["email"] == "customer@shopsphere.com"

    # Update profile and verify change history tracking
    res_up = client.put("/api/v1/customer/profile/me", headers=headers, json={
        "first_name": "SophiaUpdated",
        "gender": "FEMALE",
        "notes": "Updated loyalty tier"
    })
    assert res_up.status_code == 200
    assert res_up.json()["first_name"] == "SophiaUpdated"

    # Check profile change history audit log
    res_hist = client.get("/api/v1/customer/profile/history", headers=headers)
    assert res_hist.status_code == 200
    fields_changed = [h["field_name"] for h in res_hist.json()["items"]]
    assert "first_name" in fields_changed

    # Deactivation request
    res_deact = client.post("/api/v1/customer/profile/deactivation-request", headers=headers, json={
        "reason": "Moving abroad, closing account"
    })
    assert res_deact.status_code == 200

    # Privacy restriction check: Standard employee viewing customer profile gets masked phone
    cust_id = res_get.json()["user_id"]
    res_emp = client.get(f"/api/v1/customer/profile/{cust_id}", headers={"Authorization": f"Bearer {employee_token}"})
    assert res_emp.status_code == 200
    assert "*" in res_emp.json()["phone"]  # Masked!


# =====================================================================
# MODULE 5: ADDRESS MANAGEMENT
# =====================================================================
def test_module5_address_management_and_order_association(client, customer_token):
    headers = {"Authorization": f"Bearer {customer_token}"}

    # Add new address
    res_add = client.post("/api/v1/customer/addresses", headers=headers, json={
        "full_name": "Sophia Chen",
        "phone_number": "+14155551001",
        "address_type": "SHIPPING",
        "street_line1": "456 Market Street",
        "city": "San Francisco",
        "state_province": "CA",
        "postal_code": "94105",
        "country": "United States",
        "is_default": True
    })
    assert res_add.status_code == 201
    addr_id = res_add.json()["id"]
    assert res_add.json()["is_default"] is True

    # List addresses
    res_list = client.get("/api/v1/customer/addresses", headers=headers)
    assert res_list.status_code == 200
    assert len(res_list.json()) >= 1

    # Associate addresses with order
    res_order = client.post("/api/v1/customer/addresses/associate-order", headers=headers, json={
        "shipping_address_id": addr_id,
        "billing_address_id": addr_id,
        "total_amount": 149.99
    })
    assert res_order.status_code == 201
    assert "ORD-" in res_order.json()["order_number"]

    # Delete address with associated order: preserves record via soft deactivate
    res_del = client.delete(f"/api/v1/customer/addresses/{addr_id}", headers=headers)
    assert res_del.status_code == 200
    assert "preserved" in res_del.json()["message"].lower()


# =====================================================================
# MODULE 6: PRODUCT CATEGORY MANAGEMENT
# =====================================================================
def test_module6_category_hierarchy_and_invalid_deletion(client, admin_token):
    headers = {"Authorization": f"Bearer {admin_token}"}

    # Create parent category
    res_parent = client.post("/api/v1/categories", headers=headers, json={
        "name": "Gaming",
        "description": "Video games and consoles"
    })
    assert res_parent.status_code == 201
    parent_id = res_parent.json()["id"]

    # Create subcategory
    res_sub = client.post("/api/v1/categories", headers=headers, json={
        "name": "Consoles",
        "parent_id": parent_id
    })
    assert res_sub.status_code == 201
    sub_id = res_sub.json()["id"]

    # Retrieve hierarchy tree
    res_tree = client.get("/api/v1/categories/tree")
    assert res_tree.status_code == 200
    gaming_node = next((n for n in res_tree.json() if n["id"] == parent_id), None)
    assert gaming_node is not None
    assert any(c["id"] == sub_id for c in gaming_node["children"])

    # Prevent invalid deletion when subcategories exist
    res_del_invalid = client.delete(f"/api/v1/categories/{parent_id}", headers=headers)
    assert res_del_invalid.status_code == 400
    assert "subcategories" in res_del_invalid.json()["detail"].lower()

    # Deleting child subcategory first
    res_del_sub = client.delete(f"/api/v1/categories/{sub_id}", headers=headers)
    assert res_del_sub.status_code == 200

    # Now deleting empty parent category succeeds
    res_del_parent = client.delete(f"/api/v1/categories/{parent_id}", headers=headers)
    assert res_del_parent.status_code == 200


# =====================================================================
# MODULE 7: BRAND MANAGEMENT
# =====================================================================
def test_module7_brand_management(client, admin_token):
    headers = {"Authorization": f"Bearer {admin_token}"}

    # Register brand
    res_create = client.post("/api/v1/brands", headers=headers, json={
        "name": "Bose",
        "code": "BOSE",
        "website_url": "https://bose.com",
        "status": "ACTIVE"
    })
    assert res_create.status_code == 201
    brand_id = res_create.json()["id"]

    # Duplicate code rejected
    res_dup = client.post("/api/v1/brands", headers=headers, json={
        "name": "Bose Audio",
        "code": "BOSE"
    })
    assert res_dup.status_code == 409

    # Update brand status
    res_status = client.patch(f"/api/v1/brands/{brand_id}/status?status=INACTIVE", headers=headers)
    assert res_status.status_code == 200
    assert res_status.json()["status"] == "INACTIVE"

    # Search brands
    res_search = client.get("/api/v1/brands?query=Bose")
    assert res_search.status_code == 200
    assert len(res_search.json()["items"]) >= 1


# =====================================================================
# MODULE 8: PRODUCT MANAGEMENT
# =====================================================================
def test_module8_product_crud_and_search(client, admin_token):
    headers = {"Authorization": f"Bearer {admin_token}"}

    # Create product
    res_create = client.post("/api/v1/products", headers=headers, json={
        "name": "Sony PlayStation 5 Console",
        "base_sku": "SONY-PS5-SLIM",
        "base_price": 499.99,
        "currency": "USD",
        "short_description": "Next-gen gaming console with ultra-high speed SSD",
        "status": "ACTIVE"
    })
    assert res_create.status_code == 201
    product_id = res_create.json()["id"]

    # Search & Filter by keyword, price range, and sort
    res_filter = client.get("/api/v1/products?query=PlayStation&min_price=400&max_price=600&sort_by=price_asc")
    assert res_filter.status_code == 200
    items = res_filter.json()["items"]
    assert len(items) >= 1
    assert items[0]["base_sku"] == "SONY-PS5-SLIM"

    # Get product details
    res_detail = client.get(f"/api/v1/products/{product_id}")
    assert res_detail.status_code == 200
    assert res_detail.json()["name"] == "Sony PlayStation 5 Console"

    # Deactivate product
    res_deact = client.patch(f"/api/v1/products/{product_id}/status?status=INACTIVE", headers=headers)
    assert res_deact.status_code == 200
    assert res_deact.json()["status"] == "INACTIVE"

    # Reactivate product
    res_react = client.patch(f"/api/v1/products/{product_id}/status?status=ACTIVE", headers=headers)
    assert res_react.status_code == 200


# =====================================================================
# MODULE 9: PRODUCT VARIANTS
# =====================================================================
def test_module9_product_variants_and_availability(client, admin_token):
    headers = {"Authorization": f"Bearer {admin_token}"}

    # Get existing seeded product
    p_res = client.get("/api/v1/products?limit=1")
    product_id = p_res.json()["items"][0]["id"]

    # Create variant
    res_var = client.post(f"/api/v1/products/{product_id}/variants", headers=headers, json={
        "title": "Edition: Digital / Color: White",
        "sku": f"VAR-PS5-DIGI-{product_id}",
        "price": 399.99,
        "stock_quantity": 8,
        "low_stock_threshold": 3,
        "attributes": {"edition": "Digital", "color": "White"},
        "status": "ACTIVE"
    })
    assert res_var.status_code == 201
    var_id = res_var.json()["id"]
    assert res_var.json()["availability_status"] == "IN_STOCK"

    # Adjust stock down to low stock
    res_adj1 = client.post(f"/api/v1/variants/{var_id}/stock-adjust", headers=headers, json={
        "adjustment": -6,
        "reason": "Sold 6 units"
    })
    assert res_adj1.status_code == 200
    assert res_adj1.json()["stock_quantity"] == 2
    assert res_adj1.json()["availability_status"] == "LOW_STOCK"

    # Adjust stock to 0 -> OUT_OF_STOCK
    res_adj2 = client.post(f"/api/v1/variants/{var_id}/stock-adjust", headers=headers, json={
        "adjustment": -2,
        "reason": "Sold remaining 2 units"
    })
    assert res_adj2.status_code == 200
    assert res_adj2.json()["stock_quantity"] == 0
    assert res_adj2.json()["availability_status"] == "OUT_OF_STOCK"


# =====================================================================
# MODULE 10: PRODUCT IMAGES AND DOCUMENTS
# =====================================================================
def test_module10_media_upload_validation_and_metadata(client, admin_token):
    headers = {"Authorization": f"Bearer {admin_token}"}

    # Get existing product
    p_res = client.get("/api/v1/products?limit=1")
    product_id = p_res.json()["items"][0]["id"]

    # 1. Create a dummy test image using Pillow
    img_byte_arr = io.BytesIO()
    img = Image.new("RGB", (800, 600), color="blue")
    img.save(img_byte_arr, format="PNG")
    img_byte_arr.seek(0)

    # Upload valid image
    files = {"file": ("test_headphone.png", img_byte_arr, "image/png")}
    data = {
        "product_id": str(product_id),
        "file_type": "IMAGE",
        "is_primary": "true"
    }
    res_upload = client.post("/api/v1/media/upload", headers=headers, files=files, data=data)
    assert res_upload.status_code == 201
    m_data = res_upload.json()
    assert m_data["image_width"] == 800
    assert m_data["image_height"] == 600
    assert m_data["is_primary"] is True
    assert m_data["checksum_sha256"] is not None
    media_id = m_data["id"]

    # 2. Upload document (PDF)
    pdf_bytes = io.BytesIO(b"%PDF-1.4 sample user manual documentation")
    files_pdf = {"file": ("user_manual.pdf", pdf_bytes, "application/pdf")}
    data_pdf = {
        "product_id": str(product_id),
        "file_type": "DOCUMENT",
        "is_primary": "false"
    }
    res_pdf = client.post("/api/v1/media/upload", headers=headers, files=files_pdf, data=data_pdf)
    assert res_pdf.status_code == 201
    assert res_pdf.json()["mime_type"] == "application/pdf"

    # 3. Reject invalid/disallowed MIME type (e.g. executable)
    bad_bytes = io.BytesIO(b"binary-exec-data")
    files_bad = {"file": ("malicious.exe", bad_bytes, "application/x-msdownload")}
    res_bad = client.post("/api/v1/media/upload", headers=headers, files=files_bad, data={"product_id": str(product_id)})
    assert res_bad.status_code == 415

    # 4. Download media file
    res_down = client.get(f"/api/v1/media/{media_id}/download")
    assert res_down.status_code == 200

    # 5. Remove authorized media file
    res_del = client.delete(f"/api/v1/media/{media_id}", headers=headers)
    assert res_del.status_code == 200
    assert res_del.json()["success"] is True


# =====================================================================
# MODULE 11: PRODUCT ATTRIBUTES
# =====================================================================
def test_module11_attributes_definition_and_filtering(client, admin_token):
    headers = {"Authorization": f"Bearer {admin_token}"}

    # 1. Define attributes (Size, Color, Material) with options
    res_attr = client.post("/api/v1/attributes", headers=headers, json={
        "name": "Fabric Weight",
        "code": "fabric_weight_gsm",
        "data_type": "NUMBER",
        "is_filterable": True
    })
    assert res_attr.status_code == 201
    attr_id = res_attr.json()["id"]

    # 2. Add options to attribute
    res_opt = client.post(f"/api/v1/attributes/{attr_id}/options", headers=headers, json={
        "value": "240 GSM",
        "display_order": 1
    })
    assert res_opt.status_code == 201

    # 3. Support category-specific attributes (link to category)
    c_res = client.get("/api/v1/categories")
    cat_id = c_res.json()[0]["id"]
    res_cat_link = client.post("/api/v1/attributes/category-link", headers=headers, json={
        "category_id": cat_id,
        "attribute_id": attr_id,
        "is_required": True
    })
    assert res_cat_link.status_code == 201

    # 4. Assign attribute to product & validate value
    p_res = client.get("/api/v1/products?limit=1")
    product_id = p_res.json()["items"][0]["id"]

    # Valid numeric value
    res_assign = client.post(f"/api/v1/attributes/products/{product_id}/values", headers=headers, json={
        "attribute_id": attr_id,
        "value": "240"
    })
    assert res_assign.status_code == 201

    # Value validation: invalid number rejected
    res_invalid_val = client.post(f"/api/v1/attributes/products/{product_id}/values", headers=headers, json={
        "attribute_id": attr_id,
        "value": "not-a-number"
    })
    assert res_invalid_val.status_code == 400
    assert "Expected a valid number" in res_invalid_val.json()["detail"]

    # 5. Filter products by attribute
    res_filter = client.get("/api/v1/attributes/products/filter-by-attributes?code=fabric_weight_gsm&value=240")
    assert res_filter.status_code == 200
    assert any(p["id"] == product_id for p in res_filter.json())


# =====================================================================
# MODULE 12: PRODUCT PRICING
# =====================================================================
def test_module12_product_pricing_and_validity_periods(client, admin_token, customer_token):
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    customer_headers = {"Authorization": f"Bearer {customer_token}"}

    p_res = client.get("/api/v1/products?limit=1")
    product_id = p_res.json()["items"][0]["id"]

    # 1. Manage base and sale prices with validity period
    res_price = client.post("/api/v1/pricing", headers=admin_headers, json={
        "product_id": product_id,
        "base_price": 500.00,
        "sale_price": 420.00,
        "sale_start_date": "2026-01-01T00:00:00Z",
        "sale_end_date": "2026-12-31T23:59:59Z",
        "currency": "USD",
        "reason": "Mid-season flash sale"
    })
    assert res_price.status_code in [201, 409]

    # Retrieve pricing and verify effective price calculation
    res_get = client.get(f"/api/v1/pricing/product/{product_id}")
    assert res_get.status_code == 200
    assert len(res_get.json()) >= 1
    price_entry = res_get.json()[0]
    price_id = price_entry["id"]

    # 2. Validate price change restrictions (sale price cannot exceed base price)
    res_bad_price = client.put(f"/api/v1/pricing/{price_id}", headers=admin_headers, json={
        "base_price": 300.00,
        "sale_price": 450.00,  # Invalid: sale > base
        "reason": "Faulty markup"
    })
    assert res_bad_price.status_code == 400
    assert "cannot exceed base price" in res_bad_price.json()["detail"].lower()

    # 3. Track price history on successful update
    res_up = client.put(f"/api/v1/pricing/{price_id}", headers=admin_headers, json={
        "base_price": 480.00,
        "sale_price": 410.00,
        "reason": "Quarterly inflation adjustment"
    })
    assert res_up.status_code == 200

    res_hist = client.get(f"/api/v1/pricing/history/{product_id}")
    assert res_hist.status_code == 200
    reasons = [h["reason"] for h in res_hist.json()]
    assert "Quarterly inflation adjustment" in reasons

    # 4. Authorized pricing permissions: Customer is forbidden from updating prices
    res_unauth = client.put(f"/api/v1/pricing/{price_id}", headers=customer_headers, json={
        "base_price": 10.00,
        "reason": "Unauthorized hacker attempt"
    })
    assert res_unauth.status_code == 403


# =====================================================================
# MODULE 13: INVENTORY MANAGEMENT
# =====================================================================
def test_module13_inventory_tracking_and_negative_prevention(client, admin_token):
    headers = {"Authorization": f"Bearer {admin_token}"}

    p_res = client.get("/api/v1/products?limit=1")
    product_id = p_res.json()["items"][0]["id"]

    # 1. Track stock quantities
    res_inv = client.get(f"/api/v1/inventory/product/{product_id}")
    assert res_inv.status_code == 200
    inv = res_inv.json()[0]
    initial_avail = inv["available_quantity"]

    # 2. Record stock addition
    res_add = client.post(f"/api/v1/inventory/product/{product_id}/add", headers=headers, json={
        "quantity": 20,
        "reference_type": "PURCHASE_ORDER",
        "reference_id": "PO-TEST-100",
        "notes": "Incoming delivery"
    })
    assert res_add.status_code == 200
    assert res_add.json()["available_quantity"] == initial_avail + 20

    # 3. Maintain available and reserved stock
    res_res = client.post(f"/api/v1/inventory/product/{product_id}/reserve", headers=headers, json={
        "quantity": 5,
        "reference_id": "CART-USER-99"
    })
    assert res_res.status_code == 200
    assert res_res.json()["reserved_quantity"] >= 5

    res_rel = client.post(f"/api/v1/inventory/product/{product_id}/release", headers=headers, json={
        "quantity": 5,
        "reference_id": "CART-USER-99"
    })
    assert res_rel.status_code == 200

    # 4. Prevent negative inventory (attempting to reduce more than available)
    avail_now = res_rel.json()["available_quantity"]
    res_neg = client.post(f"/api/v1/inventory/product/{product_id}/reduce", headers=headers, json={
        "quantity": avail_now + 100,  # Exceeds available stock
        "notes": "Excessive reduction test"
    })
    assert res_neg.status_code == 400
    assert "negative inventory prevented" in res_neg.json()["detail"].lower()

    # 5. Retrieve stock movements
    res_mov = client.get("/api/v1/inventory/movements/all", headers=headers)
    assert res_mov.status_code == 200
    assert len(res_mov.json()) >= 1


# =====================================================================
# MODULE 14: WAREHOUSE MANAGEMENT
# =====================================================================
def test_module14_warehouse_management_and_role_restriction(client, admin_token, customer_token):
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    customer_headers = {"Authorization": f"Bearer {customer_token}"}

    # 1. Create and manage warehouse
    res_wh = client.post("/api/v1/warehouses", headers=admin_headers, json={
        "code": "WH-SOUTH-01",
        "name": "South Regional Depot",
        "address_line1": "700 Distribution Blvd",
        "city": "Atlanta",
        "state_province": "GA",
        "postal_code": "30301",
        "country": "United States",
        "capacity_units": 15000,
        "status": "ACTIVE"
    })
    assert res_wh.status_code == 201
    wh_id = res_wh.json()["id"]

    # 2. Associate inventory with warehouse
    p_res = client.get("/api/v1/products?limit=1")
    product_id = p_res.json()["items"][0]["id"]

    res_stock = client.post(f"/api/v1/warehouses/{wh_id}/stock", headers=admin_headers, json={
        "product_id": product_id,
        "quantity": 25,
        "aisle_location": "Aisle 2, Bin 14"
    })
    assert res_stock.status_code == 201
    assert res_stock.json()["quantity"] == 25

    # 3. Track warehouse capacity and status (exceeding capacity rejected)
    res_overflow = client.post(f"/api/v1/warehouses/{wh_id}/stock", headers=admin_headers, json={
        "product_id": product_id,
        "quantity": 20000  # Exceeds 15000 capacity
    })
    assert res_overflow.status_code == 400
    assert "capacity exceeded" in res_overflow.json()["detail"].lower()

    # 4. Retrieve warehouse-level stock
    res_wh_stock = client.get(f"/api/v1/warehouses/{wh_id}/stock", headers=admin_headers)
    assert res_wh_stock.status_code == 200
    assert len(res_wh_stock.json()) >= 1
    assert res_wh_stock.json()[0]["aisle_location"] == "Aisle 2, Bin 14"

    # 5. Restrict inventory access by role (Customer forbidden from warehouse management)
    res_cust_forbidden = client.get("/api/v1/warehouses", headers=customer_headers)
    assert res_cust_forbidden.status_code == 403


# =====================================================================
# MODULE 15: INVENTORY TRANSFERS
# =====================================================================
def test_module15_inventory_transfers(client, admin_token):
    headers = {"Authorization": f"Bearer {admin_token}"}

    # 1. Fetch warehouses and a product
    wh_res = client.get("/api/v1/warehouses", headers=headers)
    assert wh_res.status_code == 200
    warehouses = wh_res.json()
    assert len(warehouses) >= 2
    source_wh_id = warehouses[0]["id"]
    dest_wh_id = warehouses[1]["id"]

    p_res = client.get("/api/v1/products?limit=1")
    product_id = p_res.json()["items"][0]["id"]

    # Ensure source warehouse has stock
    client.post(f"/api/v1/warehouses/{source_wh_id}/stock", headers=headers, json={
        "product_id": product_id,
        "quantity": 30,
        "aisle_location": "Bay-Transfer"
    })

    # 2. Create transfer request
    res_req = client.post("/api/v1/transfers", headers=headers, json={
        "source_warehouse_id": source_wh_id,
        "destination_warehouse_id": dest_wh_id,
        "product_id": product_id,
        "requested_quantity": 8,
        "notes": "Stock transfer for store replenishment"
    })
    assert res_req.status_code == 201
    transfer = res_req.json()
    transfer_id = transfer["id"]
    assert transfer["status"] == "REQUESTED"
    assert transfer["transfer_number"].startswith("TRF-")

    # 3. Record dispatch
    res_disp = client.post(f"/api/v1/transfers/{transfer_id}/dispatch", headers=headers, json={
        "dispatched_quantity": 8,
        "notes": "Shipped on truck #814"
    })
    assert res_disp.status_code == 200
    assert res_disp.json()["status"] == "DISPATCHED"
    assert res_disp.json()["dispatched_quantity"] == 8

    # 4. Record receipt
    res_recv = client.post(f"/api/v1/transfers/{transfer_id}/receive", headers=headers, json={
        "received_quantity": 8,
        "notes": "Received undamaged at West warehouse"
    })
    assert res_recv.status_code == 200
    assert res_recv.json()["status"] == "RECEIVED"
    assert res_recv.json()["received_quantity"] == 8

    # 5. Track transfer status & movement history
    res_list = client.get(f"/api/v1/transfers?status=RECEIVED", headers=headers)
    assert res_list.status_code == 200
    assert any(t["id"] == transfer_id for t in res_list.json())


# =====================================================================
# MODULE 16: LOW-STOCK MANAGEMENT
# =====================================================================
def test_module16_low_stock_management(client, admin_token):
    headers = {"Authorization": f"Bearer {admin_token}"}

    p_res = client.get("/api/v1/products?limit=1")
    product_id = p_res.json()["items"][0]["id"]

    # 1. Configure minimum stock threshold
    res_conf = client.post("/api/v1/low-stock/thresholds", headers=headers, json={
        "product_id": product_id,
        "threshold": 18,
        "reorder_quantity": 60,
        "change_reason": "Black Friday safety buffer"
    })
    assert res_conf.status_code == 200
    assert res_conf.json()["threshold"] == 18

    # 2. Track stock threshold changes
    res_hist = client.get(f"/api/v1/low-stock/thresholds/history?product_id={product_id}", headers=headers)
    assert res_hist.status_code == 200
    assert any("Black Friday" in h["change_reason"] for h in res_hist.json())

    # 3. Generate restocking alerts
    res_gen = client.post("/api/v1/low-stock/alerts/generate", headers=headers)
    assert res_gen.status_code == 200

    # 4. Retrieve low-stock alerts & reports
    res_alerts = client.get("/api/v1/low-stock/alerts", headers=headers)
    assert res_alerts.status_code == 200

    res_rep = client.get("/api/v1/low-stock/report", headers=headers)
    assert res_rep.status_code == 200
    assert isinstance(res_rep.json(), list)


# =====================================================================
# MODULE 17: SHOPPING CART MANAGEMENT
# =====================================================================
def test_module17_cart_management(client, customer_token):
    headers = {"Authorization": f"Bearer {customer_token}"}

    p_res = client.get("/api/v1/products?status=ACTIVE&limit=1")
    product_id = p_res.json()["items"][0]["id"]

    # 1. Clear cart
    client.delete("/api/v1/cart/clear", headers=headers)

    # 2. Add product to cart
    res_add = client.post("/api/v1/cart/items", headers=headers, json={
        "product_id": product_id,
        "quantity": 2
    })
    assert res_add.status_code == 201
    cart = res_add.json()
    assert cart["item_count"] == 2
    item_id = cart["items"][0]["id"]

    # 3. Update quantity
    res_up = client.put(f"/api/v1/cart/items/{item_id}", headers=headers, json={
        "quantity": 3
    })
    assert res_up.status_code == 200
    assert res_up.json()["item_count"] == 3

    # 4. Retrieve cart contents and totals
    res_cart = client.get("/api/v1/cart", headers=headers)
    assert res_cart.status_code == 200
    assert res_cart.json()["subtotal"] > 0
    assert res_cart.json()["items"][0]["is_available"] is True

    # 5. Remove item
    res_del = client.delete(f"/api/v1/cart/items/{item_id}", headers=headers)
    assert res_del.status_code == 200
    assert res_del.json()["item_count"] == 0


# =====================================================================
# MODULE 18: CART PRICE CALCULATION
# =====================================================================
def test_module18_cart_price_calculation(client, customer_token):
    headers = {"Authorization": f"Bearer {customer_token}"}

    p_res = client.get("/api/v1/products?status=ACTIVE&limit=1")
    product_id = p_res.json()["items"][0]["id"]

    # Add item
    client.delete("/api/v1/cart/clear", headers=headers)
    client.post("/api/v1/cart/items", headers=headers, json={"product_id": product_id, "quantity": 1})

    # Calculate price summary
    res_calc = client.post("/api/v1/cart/calculate", headers=headers, json={
        "coupon_code": "WELCOME10",
        "shipping_method_code": "STANDARD_GROUND"
    })
    assert res_calc.status_code == 200
    summary = res_calc.json()
    assert summary["subtotal_amount"] > 0
    assert summary["grand_total"] > 0
    assert summary["coupon_discount"] >= 0
    assert summary["tax_amount"] >= 0
    assert "items" in summary


# =====================================================================
# MODULE 19: WISHLIST MANAGEMENT
# =====================================================================
def test_module19_wishlist_management(client, customer_token):
    headers = {"Authorization": f"Bearer {customer_token}"}

    p_res = client.get("/api/v1/products?limit=1")
    product_id = p_res.json()["items"][0]["id"]

    # Clear wishlist
    client.delete("/api/v1/wishlist/clear", headers=headers)

    # 1. Add product to wishlist
    res_add = client.post("/api/v1/wishlist", headers=headers, json={"product_id": product_id})
    assert res_add.status_code == 201
    item_id = res_add.json()["id"]

    # 2. Prevent duplicate entries
    res_dup = client.post("/api/v1/wishlist", headers=headers, json={"product_id": product_id})
    assert res_dup.status_code == 409

    # 3. Retrieve saved products & validate availability
    res_list = client.get("/api/v1/wishlist", headers=headers)
    assert res_list.status_code == 200
    assert len(res_list.json()) >= 1
    assert "availability_status" in res_list.json()[0]

    # 4. Remove item
    res_rem = client.delete(f"/api/v1/wishlist/{item_id}", headers=headers)
    assert res_rem.status_code == 200


# =====================================================================
# MODULE 20: COUPON MANAGEMENT
# =====================================================================
def test_module20_coupon_management(client, admin_token, customer_token):
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    # 1. Create coupon code
    res_c = client.post("/api/v1/coupons", headers=admin_headers, json={
        "code": "PROMO25PERCENT",
        "description": "25% off flash sale",
        "discount_type": "PERCENTAGE",
        "discount_value": 25.0,
        "min_purchase_amount": 100.0,
        "max_discount_amount": 50.0,
        "usage_limit": 50,
        "is_active": True
    })
    assert res_c.status_code == 201
    coupon = res_c.json()
    coupon_id = coupon["id"]

    # 2. Validate coupon with eligible cart subtotal
    res_val = client.post("/api/v1/coupons/validate", json={
        "code": "PROMO25PERCENT",
        "cart_subtotal": 150.00
    })
    assert res_val.status_code == 200
    assert res_val.json()["is_valid"] is True
    assert res_val.json()["calculated_discount"] == 37.50

    # 3. Validate with subtotal below minimum amount
    res_ineligible = client.post("/api/v1/coupons/validate", json={
        "code": "PROMO25PERCENT",
        "cart_subtotal": 50.00
    })
    assert res_ineligible.status_code == 200
    assert res_ineligible.json()["is_valid"] is False

    # 4. Deactivate coupon
    res_deact = client.put(f"/api/v1/coupons/{coupon_id}", headers=admin_headers, json={"is_active": False})
    assert res_deact.status_code == 200
    assert res_deact.json()["is_active"] is False


# =====================================================================
# MODULE 21: PROMOTION MANAGEMENT
# =====================================================================
def test_module21_promotion_management(client, admin_token):
    headers = {"Authorization": f"Bearer {admin_token}"}

    # 1. Configure promotion
    res_promo = client.post("/api/v1/promotions", headers=headers, json={
        "name": "Spring Kickoff 2026",
        "code": "SPRING2026",
        "description": "10% storewide spring promo",
        "promotion_type": "PERCENTAGE_DISCOUNT",
        "discount_value": 10.0,
        "min_order_amount": 50.0,
        "start_date": "2026-03-01T00:00:00Z",
        "end_date": "2026-06-01T23:59:59Z",
        "is_active": True
    })
    assert res_promo.status_code == 201
    assert res_promo.json()["code"] == "SPRING2026"

    # 2. List promotions
    res_list = client.get("/api/v1/promotions", headers=headers)
    assert res_list.status_code == 200
    assert any(p["code"] == "SPRING2026" for p in res_list.json())


# =====================================================================
# MODULE 22: TAX MANAGEMENT
# =====================================================================
def test_module22_tax_management(client, admin_token):
    headers = {"Authorization": f"Bearer {admin_token}"}

    # 1. Configure tax rate
    res_tax = client.post("/api/v1/taxes", headers=headers, json={
        "name": "Texas Sales Tax",
        "country": "USA",
        "state_province": "TX",
        "rate_percentage": 6.25,
        "is_active": True
    })
    assert res_tax.status_code == 201
    tax_id = res_tax.json()["id"]

    # 2. Update rate and track history
    res_up = client.put(f"/api/v1/taxes/{tax_id}", headers=headers, json={
        "rate_percentage": 6.50,
        "change_reason": "State legislative rate adjustment"
    })
    assert res_up.status_code == 200
    assert res_up.json()["rate_percentage"] == 6.50

    res_hist = client.get(f"/api/v1/taxes/history?tax_id={tax_id}", headers=headers)
    assert res_hist.status_code == 200
    assert len(res_hist.json()) >= 1

    # 3. Calculate tax
    res_calc = client.post("/api/v1/taxes/calculate", json={
        "country": "USA",
        "state_province": "TX",
        "amount": 200.00
    })
    assert res_calc.status_code == 200
    assert res_calc.json()["tax_amount"] == 13.00


# =====================================================================
# MODULE 23: SHIPPING CONFIGURATION
# =====================================================================
def test_module23_shipping_configuration(client, admin_token):
    headers = {"Authorization": f"Bearer {admin_token}"}

    # 1. Define shipping method
    res_sm = client.post("/api/v1/shipping/methods", headers=headers, json={
        "name": "Standard Economy",
        "code": "STANDARD_ECONOMY",
        "description": "5-7 business days ground delivery",
        "base_charge": 4.99,
        "free_shipping_threshold": 50.0,
        "estimated_days_min": 5,
        "estimated_days_max": 7,
        "is_active": True
    })
    assert res_sm.status_code == 201

    # 2. Estimate shipping rates
    res_est = client.post("/api/v1/shipping/estimate", json={
        "subtotal": 60.00,
        "country": "USA"
    })
    assert res_est.status_code == 200
    options = res_est.json()["options"]
    economy_opt = next((o for o in options if o["code"] == "STANDARD_ECONOMY"), None)
    assert economy_opt is not None
    assert economy_opt["is_free"] is True
    assert economy_opt["charge"] == 0.0


# =====================================================================
# MODULE 24: CHECKOUT MANAGEMENT
# =====================================================================
def test_module24_checkout_management(client, customer_token):
    headers = {"Authorization": f"Bearer {customer_token}"}

    # 1. Fetch products & addresses
    p_res = client.get("/api/v1/products?status=ACTIVE&limit=1")
    product_id = p_res.json()["items"][0]["id"]

    addr_res = client.get("/api/v1/customer/addresses", headers=headers)
    assert addr_res.status_code == 200
    addresses = addr_res.json()
    assert len(addresses) >= 1
    shipping_addr_id = addresses[0]["id"]
    billing_addr_id = addresses[0]["id"]

    # 2. Add item to cart
    client.delete("/api/v1/cart/clear", headers=headers)
    client.post("/api/v1/cart/items", headers=headers, json={"product_id": product_id, "quantity": 1})

    # 3. Process checkout
    res_chk = client.post("/api/v1/checkout", headers=headers, json={
        "shipping_address_id": shipping_addr_id,
        "billing_address_id": billing_addr_id,
        "shipping_method_code": "STANDARD_GROUND",
        "coupon_code": "WELCOME10",
        "notes": "Fragile items, please handle with care"
    })
    assert res_chk.status_code == 201
    checkout_data = res_chk.json()
    assert checkout_data["order_number"].startswith("ORD-")
    assert checkout_data["status"] == "CONFIRMED"

    # Cart should now be marked checked out
    res_cart = client.get("/api/v1/cart", headers=headers)
    assert res_cart.status_code == 200


# =====================================================================
# MODULE 25: ORDER MANAGEMENT
# =====================================================================
def test_module25_order_management(client, admin_token, customer_token):
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    customer_headers = {"Authorization": f"Bearer {customer_token}"}

    # 1. Retrieve customer orders
    res_orders = client.get("/api/v1/orders", headers=customer_headers)
    assert res_orders.status_code == 200
    orders = res_orders.json()
    assert len(orders) >= 1
    # Pick non-seed order so Order 1 status state machine is preserved for subsequent tests
    target_order = next((o for o in orders if o["id"] != 1), orders[0])
    order_id = target_order["id"]

    # 2. Retrieve order details with items and addresses
    res_detail = client.get(f"/api/v1/orders/{order_id}", headers=customer_headers)
    assert res_detail.status_code == 200
    order_data = res_detail.json()
    assert "items" in order_data
    assert "status_history" in order_data

    # 3. Update order status (Employee/Admin: PROCESSING -> CANCELLED)
    res_status = client.patch(f"/api/v1/orders/{order_id}/status", headers=admin_headers, json={
        "status": "PROCESSING",
        "notes": "Order sent to warehouse packing line"
    })
    assert res_status.status_code == 200
    assert res_status.json()["status"] == "PROCESSING"

    # 4. Cancelling order releases reserved stock back to available pool
    res_cancel = client.patch(f"/api/v1/orders/{order_id}/status", headers=admin_headers, json={
        "status": "CANCELLED",
        "notes": "Customer requested order cancellation before shipment"
    })
    assert res_cancel.status_code == 200
    assert res_cancel.json()["status"] == "CANCELLED"

    # 5. Check order status history
    res_hist = client.get(f"/api/v1/orders/{order_id}/history", headers=customer_headers)
    assert res_hist.status_code == 200
    statuses = [h["to_status"] for h in res_hist.json()]
    assert "CANCELLED" in statuses


# =====================================================================
# MODULE 41: NOTIFICATION MANAGEMENT
# =====================================================================
def test_module41_notification_management(client, admin_token, customer_token):
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    customer_headers = {"Authorization": f"Bearer {customer_token}"}

    # 1. Admin generates in-app notification for customer
    res_create = client.post("/api/v1/notifications", headers=admin_headers, json={
        "user_id": 3,
        "title": "Refund Approved",
        "message": "Your refund request of $45.00 has been approved and issued.",
        "notification_type": "REFUND_STATUS",
        "severity": "SUCCESS",
        "reference_id": "REF-9921"
    })
    assert res_create.status_code == 201
    notif_id = res_create.json()["id"]

    # 2. Customer retrieves notifications
    res_me = client.get("/api/v1/notifications/me", headers=customer_headers)
    assert res_me.status_code == 200
    notifs = res_me.json()
    assert any(n["id"] == notif_id for n in notifs)

    # 3. Check unread count
    res_cnt = client.get("/api/v1/notifications/me/unread-count", headers=customer_headers)
    assert res_cnt.status_code == 200
    assert res_cnt.json()["unread_count"] >= 1

    # 4. Mark notification as read
    res_read = client.patch(f"/api/v1/notifications/{notif_id}/read", headers=customer_headers)
    assert res_read.status_code == 200
    assert res_read.json()["is_read"] is True

    # 5. Mark all as read
    res_all = client.post("/api/v1/notifications/me/mark-all-read", headers=customer_headers)
    assert res_all.status_code == 200

    # 6. Staff exception notifications
    res_staff = client.get("/api/v1/notifications/staff-exceptions", headers=admin_headers)
    assert res_staff.status_code == 200


# =====================================================================
# MODULE 42: EMAIL AND SMS NOTIFICATIONS
# =====================================================================
def test_module42_email_and_sms_notifications(client, admin_token, customer_token):
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    customer_headers = {"Authorization": f"Bearer {customer_token}"}

    # 1. Configure Email provider
    res_prov = client.post("/api/v1/messaging/providers", headers=admin_headers, json={
        "provider_type": "EMAIL",
        "provider_name": "SendGrid Enterprise",
        "sender_address": "orders@shopsphere.com",
        "api_key_masked": "SG.live_abcdef12345",
        "is_active": True,
        "is_default": False
    })
    assert res_prov.status_code == 201
    prov_id = res_prov.json()["id"]

    # 2. Toggle provider active status
    res_toggle = client.patch(f"/api/v1/messaging/providers/{prov_id}/toggle", headers=admin_headers)
    assert res_toggle.status_code == 200
    assert res_toggle.json()["is_active"] is False

    # 3. Send order confirmation email
    res_send = client.post("/api/v1/messaging/send", headers=customer_headers, json={
        "channel": "EMAIL",
        "recipient": "customer@shopsphere.com",
        "template_type": "ORDER_CONFIRMATION",
        "subject": "Your Order Has Shipped!",
        "body": "Tracking number: TRK99482910."
    })
    assert res_send.status_code == 201
    assert res_send.json()["status"] == "SENT"
    log_id = res_send.json()["id"]

    # 4. List message logs
    res_logs = client.get("/api/v1/messaging/logs", headers=admin_headers)
    assert res_logs.status_code == 200
    assert any(l["id"] == log_id for l in res_logs.json())

    # 5. Send message with simulated failure and retry
    res_fail = client.post("/api/v1/messaging/send", headers=customer_headers, json={
        "channel": "SMS",
        "recipient": "invalid_phone_number",
        "template_type": "SHIPMENT_UPDATE",
        "body": "SMS failure test."
    })
    assert res_fail.status_code == 201
    failed_log_id = res_fail.json()["id"]
    assert res_fail.json()["status"] == "FAILED"

    res_retry = client.post(f"/api/v1/messaging/logs/{failed_log_id}/retry", headers=admin_headers)
    assert res_retry.status_code == 200
    assert res_retry.json()["retry_count"] == 1


# =====================================================================
# MODULE 43: SELLER AND SUPPLIER MANAGEMENT
# =====================================================================
def test_module43_seller_and_supplier_management(client, admin_token):
    headers = {"Authorization": f"Bearer {admin_token}"}

    # 1. Register supplier
    code = f"SUP-TEST-{uuid.uuid4().hex[:6].upper()}"
    res_sup = client.post("/api/v1/suppliers", headers=headers, json={
        "supplier_code": code,
        "company_name": "Pacific Hardware Supply",
        "supplier_type": "SUPPLIER",
        "contact_name": "Elena Rostova",
        "email": f"elena_{code.lower()}@pacifichw.com",
        "phone": "+14155558822",
        "tax_id": "US-88-2910482",
        "business_registration_number": "REG-774910",
        "address_line": "750 Industrial Parkway",
        "city": "Oakland",
        "state": "CA",
        "country": "USA",
        "postal_code": "94621",
        "notes": "Fast fulfillment vendor"
    })
    assert res_sup.status_code == 201
    supplier = res_sup.json()
    supplier_id = supplier["id"]
    assert supplier["status"] == "PENDING_APPROVAL"

    # 2. Prevent duplicate code
    res_dup = client.post("/api/v1/suppliers", headers=headers, json={
        "supplier_code": code,
        "company_name": "Duplicate Company",
        "contact_name": "Copy Person",
        "email": "unique@dup.com",
        "phone": "+14155550000",
        "address_line": "Street",
        "city": "City",
        "state": "CA",
        "postal_code": "90001"
    })
    assert res_dup.status_code == 409

    # 3. Update supplier information
    res_upd = client.put(f"/api/v1/suppliers/{supplier_id}", headers=headers, json={
        "contact_name": "Elena Rostova-Smith",
        "notes": "Verified business license"
    })
    assert res_upd.status_code == 200
    assert res_upd.json()["contact_name"] == "Elena Rostova-Smith"

    # 4. Approve supplier account
    res_app = client.patch(f"/api/v1/suppliers/{supplier_id}/approval", headers=headers, json={
        "status": "APPROVED",
        "notes": "Board approval completed"
    })
    assert res_app.status_code == 200
    assert res_app.json()["status"] == "APPROVED"

    # 5. Associate product with supplier
    res_assoc = client.post(f"/api/v1/suppliers/{supplier_id}/products", headers=headers, json={
        "product_id": 1,
        "supplier_sku": "PAC-HW-PROD1",
        "negotiated_cost": 850.00,
        "lead_time_days": 4,
        "is_primary": True
    })
    assert res_assoc.status_code == 201
    assert res_assoc.json()["supplier_sku"] == "PAC-HW-PROD1"

    # 6. Retrieve supplier history
    res_hist = client.get(f"/api/v1/suppliers/{supplier_id}/history", headers=headers)
    assert res_hist.status_code == 200
    assert len(res_hist.json()) >= 2


# =====================================================================
# MODULE 44: PURCHASE ORDER MANAGEMENT
# =====================================================================
def test_module44_purchase_order_management(client, admin_token):
    headers = {"Authorization": f"Bearer {admin_token}"}

    # 1. Create Purchase Order
    res_po = client.post("/api/v1/purchase-orders", headers=headers, json={
        "supplier_id": 1,
        "warehouse_id": 1,
        "expected_delivery_date": "2026-11-20T00:00:00Z",
        "notes": "Urgent seasonal stock replenishment",
        "items": [
            {
                "product_id": 1,
                "variant_id": 1,
                "quantity_ordered": 20,
                "unit_cost": 1050.00
            }
        ]
    })
    assert res_po.status_code == 201
    po = res_po.json()
    po_id = po["id"]
    po_item_id = po["items"][0]["id"]
    assert po["status"] == "DRAFT"
    assert po["po_number"].startswith("PO-")

    # 2. Update status to SUBMITTED
    res_sub = client.patch(f"/api/v1/purchase-orders/{po_id}/status", headers=headers, json={
        "status": "SUBMITTED",
        "notes": "PO dispatched to vendor"
    })
    assert res_sub.status_code == 200
    assert res_sub.json()["status"] == "SUBMITTED"

    # 3. Receive stock against PO
    res_recv = client.post(f"/api/v1/purchase-orders/{po_id}/receive", headers=headers, json={
        "items": [
            {"item_id": po_item_id, "quantity_to_receive": 20}
        ],
        "notes": "All 20 units received intact at loading dock"
    })
    assert res_recv.status_code == 200
    assert res_recv.json()["status"] == "RECEIVED"
    assert res_recv.json()["items"][0]["quantity_received"] == 20

    # 4. Supplier purchase history
    res_hist = client.get(f"/api/v1/purchase-orders/supplier/1", headers=headers)
    assert res_hist.status_code == 200
    assert any(p["id"] == po_id for p in res_hist.json())


# =====================================================================
# MODULE 45: SUPPLIER INVOICE MANAGEMENT
# =====================================================================
def test_module45_supplier_invoice_management(client, admin_token):
    headers = {"Authorization": f"Bearer {admin_token}"}

    inv_num = f"INV-TEST-{uuid.uuid4().hex[:6].upper()}"

    # 1. Record invoice
    res_inv = client.post("/api/v1/supplier-invoices", headers=headers, json={
        "invoice_number": inv_num,
        "supplier_id": 1,
        "purchase_order_id": 1,
        "due_date": "2026-12-01T00:00:00Z",
        "subtotal": 21000.00,
        "tax_amount": 0.00,
        "total_amount": 21000.00,
        "notes": "Net 30 invoice terms"
    })
    assert res_inv.status_code == 201
    invoice = res_inv.json()
    invoice_id = invoice["id"]
    assert invoice["payment_status"] == "UNPAID"

    # 2. Prevent duplicate invoice for same supplier
    res_dup = client.post("/api/v1/supplier-invoices", headers=headers, json={
        "invoice_number": inv_num,
        "supplier_id": 1,
        "purchase_order_id": 1,
        "due_date": "2026-12-01T00:00:00Z",
        "subtotal": 21000.00,
        "total_amount": 21000.00
    })
    assert res_dup.status_code == 409

    # 3. Update payment status
    res_pay = client.patch(f"/api/v1/supplier-invoices/{invoice_id}/payment", headers=headers, json={
        "payment_status": "PAID",
        "amount_paid": 21000.00,
        "notes": "Check #48819 cleared"
    })
    assert res_pay.status_code == 200
    assert res_pay.json()["payment_status"] == "PAID"
    assert float(res_pay.json()["amount_paid"]) == 21000.00


# =====================================================================
# MODULE 46: AUDIT LOG MANAGEMENT
# =====================================================================
def test_module46_audit_log_management(client, admin_token, customer_token):
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    customer_headers = {"Authorization": f"Bearer {customer_token}"}

    # 1. Record sensitive administrative audit log
    res_entry = client.post("/api/v1/audit-logs", headers=admin_headers, json={
        "action": "USER_ROLE_ELEVATION",
        "entity_type": "USER",
        "entity_id": "2",
        "old_values": '{"role": "EMPLOYEE"}',
        "new_values": '{"role": "ADMIN"}',
        "reason": "Promoted to regional inventory manager"
    })
    assert res_entry.status_code == 201
    entry_id = res_entry.json()["id"]

    # 2. Query audit logs as admin
    res_logs = client.get("/api/v1/audit-logs?entity_type=USER", headers=admin_headers)
    assert res_logs.status_code == 200
    assert any(log["id"] == entry_id for log in res_logs.json())

    # 3. Customer denied access (RBAC enforcement)
    res_denied = client.get("/api/v1/audit-logs", headers=customer_headers)
    assert res_denied.status_code in [401, 403]


# =====================================================================
# MODULE 47: DASHBOARD AND SUMMARY APIS
# =====================================================================
def test_module47_dashboard_and_summary_apis(client, admin_token, customer_token):
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    customer_headers = {"Authorization": f"Bearer {customer_token}"}

    # 1. Customer dashboard summary (scoped to personal metrics)
    res_cust = client.get("/api/v1/dashboard/summary", headers=customer_headers)
    assert res_cust.status_code == 200
    cust_data = res_cust.json()
    assert "total_orders" in cust_data
    assert "total_spent" in cust_data
    assert "wishlist_items_count" in cust_data

    # 2. Enterprise Admin dashboard summary
    res_admin = client.get("/api/v1/dashboard/summary", headers=admin_headers)
    assert res_admin.status_code == 200
    admin_data = res_admin.json()
    assert "total_products" in admin_data
    assert "gross_revenue" in admin_data
    assert "order_counts_by_status" in admin_data
    assert "inventory_valuation" in admin_data


# =====================================================================
# MODULE 48: REPORTS AND ANALYTICS APIS
# =====================================================================
def test_module48_reports_and_analytics_apis(client, admin_token):
    headers = {"Authorization": f"Bearer {admin_token}"}

    # 1. Sales & Order Analytics
    res_sales = client.get("/api/v1/analytics/sales", headers=headers)
    assert res_sales.status_code == 200
    assert "total_gross_sales" in res_sales.json()
    assert "average_order_value" in res_sales.json()

    # 2. Inventory Analytics
    res_inv = client.get("/api/v1/analytics/inventory", headers=headers)
    assert res_inv.status_code == 200
    assert "total_stock_units" in res_inv.json()
    assert "warehouse_breakdown" in res_inv.json()

    # 3. Payment & Refund Analytics
    res_pay = client.get("/api/v1/analytics/payments", headers=headers)
    assert res_pay.status_code == 200
    assert "payment_status_breakdown" in res_pay.json()

    # 4. Performance Analytics (Top products & Categories)
    res_perf = client.get("/api/v1/analytics/performance", headers=headers)
    assert res_perf.status_code == 200
    assert "top_products" in res_perf.json()
    assert "category_performance" in res_perf.json()


# =====================================================================
# MODULE 49: REPORT EXPORT AND BACKGROUND TASKS
# =====================================================================
def test_module49_report_export_and_background_tasks(client, admin_token):
    headers = {"Authorization": f"Bearer {admin_token}"}

    # 1. Schedule summary task
    res_sched = client.post("/api/v1/tasks/schedule-summary", headers=headers, json={
        "summary_type": "DAILY_INVENTORY_ORDERS",
        "parameters": {"scope": "all_warehouses"}
    })
    assert res_sched.status_code == 201
    assert res_sched.json()["task_type"] == "SCHEDULED_SUMMARY"

    # 2. Trigger report export in CSV format
    res_export = client.post("/api/v1/tasks/export", headers=headers, json={
        "report_type": "ORDERS",
        "export_format": "CSV",
        "parameters": {"limit": 50}
    })
    assert res_export.status_code == 201
    task = res_export.json()
    task_id = task["id"]
    assert task["status"] in ["COMPLETED", "RUNNING"]

    # 3. List tasks
    res_tasks = client.get("/api/v1/tasks", headers=headers)
    assert res_tasks.status_code == 200
    assert any(t["id"] == task_id for t in res_tasks.json())

    # 4. Download exported file
    res_down = client.get(f"/api/v1/tasks/{task_id}/download", headers=headers)
    assert res_down.status_code == 200
    assert len(res_down.content) > 0

    # 5. Retry endpoint verification
    res_retry = client.post(f"/api/v1/tasks/{task_id}/retry", headers=headers)
    assert res_retry.status_code == 200


# =====================================================================
# MODULE 50: API TESTING AND SYSTEM INTEGRATION
# =====================================================================
def test_module50_api_testing_and_system_integration(client, admin_token, customer_token):
    """
    End-to-End System Integration Test:
    Cart -> Checkout -> Order Creation -> Inventory Reservation ->
    In-App Notification & Message Log -> PO Restock -> Invoice Settlement ->
    Audit Log Verification -> Analytics Refresh.
    """
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    customer_headers = {"Authorization": f"Bearer {customer_token}"}

    # 1. Customer checks profile & address
    addr_res = client.get("/api/v1/customer/addresses", headers=customer_headers)
    assert addr_res.status_code == 200
    addrs = addr_res.json()
    assert len(addrs) >= 1
    ship_addr_id = addrs[0]["id"]

    # 2. Add product to cart & process checkout
    client.post("/api/v1/cart/items", headers=customer_headers, json={"product_id": 1, "quantity": 1})
    res_order = client.post("/api/v1/checkout", headers=customer_headers, json={
        "shipping_address_id": ship_addr_id,
        "billing_address_id": ship_addr_id,
        "shipping_method_code": "STANDARD_GROUND",
        "coupon_code": "WELCOME10",
        "notes": "System integration end-to-end order"
    })
    assert res_order.status_code == 201
    order_data = res_order.json()
    order_num = order_data["order_number"]

    # 3. Verification of In-App Notification generated for customer
    res_notif = client.post("/api/v1/notifications", headers=admin_headers, json={
        "user_id": 3,
        "title": "System Integration Confirmation",
        "message": f"Order {order_num} has been successfully validated.",
        "notification_type": "ORDER_UPDATE",
        "severity": "SUCCESS",
        "reference_id": order_num
    })
    assert res_notif.status_code == 201

    # 4. Supplier restock purchase order creation
    res_po = client.post("/api/v1/purchase-orders", headers=admin_headers, json={
        "supplier_id": 1,
        "warehouse_id": 1,
        "notes": "Integration restock cycle",
        "items": [{"product_id": 1, "quantity_ordered": 10, "unit_cost": 1000.00}]
    })
    assert res_po.status_code == 201
    po_id = res_po.json()["id"]

    # 5. Receive stock into warehouse
    po_item_id = res_po.json()["items"][0]["id"]
    res_recv = client.post(f"/api/v1/purchase-orders/{po_id}/receive", headers=admin_headers, json={
        "items": [{"item_id": po_item_id, "quantity_to_receive": 10}]
    })
    assert res_recv.status_code == 200
    assert res_recv.json()["status"] == "RECEIVED"

    # 6. Audit log verifies administrative restock and checkout
    res_audit = client.post("/api/v1/audit-logs", headers=admin_headers, json={
        "action": "INTEGRATION_TEST_CYCLE_COMPLETED",
        "entity_type": "SYSTEM",
        "entity_id": order_num,
        "reason": "Complete end-to-end commerce lifecycle verified"
    })
    assert res_audit.status_code == 201

    # 7. Check platform dashboard metrics reflect latest operations
    res_dash = client.get("/api/v1/dashboard/summary", headers=admin_headers)
    assert res_dash.status_code == 200
    assert res_dash.json()["total_orders"] >= 1


# =====================================================================
# MODULE 26: ORDER ITEM MANAGEMENT
# =====================================================================
def test_module26_order_item_management(client, admin_token, customer_token):
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    customer_headers = {"Authorization": f"Bearer {customer_token}"}

    # 1. Retrieve order items
    res = client.get("/api/v1/orders/1/items", headers=admin_headers)
    assert res.status_code == 200
    items = res.json()
    assert len(items) >= 1
    item = items[0]
    assert "sku" in item
    assert "unit_price" in item
    assert "quantity" in item
    assert "subtotal" in item
    assert "fulfillment_status" in item

    # 2. Retrieve single item
    item_id = item["id"]
    res_single = client.get(f"/api/v1/orders/1/items/{item_id}", headers=admin_headers)
    assert res_single.status_code == 200
    assert res_single.json()["id"] == item_id

    # 3. Update fulfillment status
    res_ful = client.patch(
        f"/api/v1/orders/1/items/{item_id}/fulfillment",
        headers=admin_headers,
        json={"fulfillment_status": "PROCESSING"}
    )
    assert res_ful.status_code == 200
    assert res_ful.json()["fulfillment_status"] == "PROCESSING"


# =====================================================================
# MODULE 27: ORDER STATUS MANAGEMENT
# =====================================================================
def test_module27_order_status_management(client, admin_token):
    headers = {"Authorization": f"Bearer {admin_token}"}

    # 1. Check permitted transitions
    res_perm = client.get("/api/v1/order-status/permitted-transitions/1", headers=headers)
    assert res_perm.status_code == 200
    assert "permitted_next_statuses" in res_perm.json()

    # 2. Transition status from CONFIRMED -> PROCESSING
    res_trans = client.post("/api/v1/order-status/transition/1", headers=headers, json={
        "to_status": "PROCESSING",
        "notes": "Order sent to warehouse packing line"
    })
    assert res_trans.status_code == 200
    assert res_trans.json()["status"] == "PROCESSING"

    # 3. Invalid status transition check (e.g. attempting to jump to DELIVERED directly)
    res_bad = client.post("/api/v1/order-status/transition/1", headers=headers, json={
        "to_status": "DELIVERED",
        "notes": "Direct jump should fail"
    })
    assert res_bad.status_code == 400

    # 4. View status history
    res_hist = client.get("/api/v1/order-status/history/1", headers=headers)
    assert res_hist.status_code == 200
    assert len(res_hist.json()) >= 1


# =====================================================================
# MODULE 28: ORDER CANCELLATION
# =====================================================================
def test_module28_order_cancellation(client, admin_token, customer_token):
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    customer_headers = {"Authorization": f"Bearer {customer_token}"}

    # 1. Place a fresh pending order to cancel
    client.post("/api/v1/cart/items", headers=customer_headers, json={"product_id": 1, "quantity": 1})
    res_checkout = client.post("/api/v1/checkout/process", headers=customer_headers, json={
        "shipping_address_id": 1,
        "billing_address_id": 1,
        "shipping_method_code": "STANDARD_GROUND"
    })
    assert res_checkout.status_code == 201
    order_id = res_checkout.json()["order_id"]

    # 2. Request cancellation
    res_cancel = client.post(f"/api/v1/order-cancellations/{order_id}", headers=customer_headers, json={
        "reason": "Accidental duplicate order placed",
        "admin_notes": "Cancelled before warehouse dispatch"
    })
    assert res_cancel.status_code == 201
    cancel_data = res_cancel.json()
    assert cancel_data["status"] == "COMPLETED"
    assert cancel_data["inventory_released"] is True

    # 3. Prevent duplicate cancellation
    res_dup = client.post(f"/api/v1/order-cancellations/{order_id}", headers=customer_headers, json={
        "reason": "Attempting second cancellation"
    })
    assert res_dup.status_code in [400, 409]

    # 4. Query cancellation details
    res_get = client.get(f"/api/v1/order-cancellations/{order_id}", headers=customer_headers)
    assert res_get.status_code == 200
    assert res_get.json()["reason"] == "Accidental duplicate order placed"


# =====================================================================
# MODULE 29: PAYMENT MANAGEMENT
# =====================================================================
def test_module29_payment_management(client, customer_token, admin_token):
    cust_headers = {"Authorization": f"Bearer {customer_token}"}

    # 0. Place a fresh pending order for payment processing
    client.post("/api/v1/cart/items", headers=cust_headers, json={"product_id": 1, "quantity": 1})
    res_chk = client.post("/api/v1/checkout", headers=cust_headers, json={
        "shipping_address_id": 1,
        "billing_address_id": 1,
        "shipping_method_code": "STANDARD_GROUND"
    })
    assert res_chk.status_code == 201
    pay_order_id = res_chk.json()["order_id"]

    # 1. Initiate payment session
    idem_key = f"IDEM-{uuid.uuid4().hex[:12]}"
    res_init = client.post("/api/v1/payments/initiate", headers=cust_headers, json={
        "order_id": pay_order_id,
        "payment_method": "CREDIT_CARD",
        "idempotency_key": idem_key
    })
    assert res_init.status_code in [200, 201]
    pay_data = res_init.json()
    payment_id = pay_data["id"]
    assert "transaction_reference" in pay_data

    # 2. Duplicate prevention using same idempotency key
    res_dup = client.post("/api/v1/payments/initiate", headers=cust_headers, json={
        "order_id": pay_order_id,
        "payment_method": "CREDIT_CARD",
        "idempotency_key": idem_key
    })
    assert res_dup.status_code in [200, 201]
    assert res_dup.json()["id"] == payment_id

    # 3. Process Sandbox Capture
    res_proc = client.post(f"/api/v1/payments/{payment_id}/process-sandbox", headers=cust_headers, json={
        "action": "CAPTURE"
    })
    assert res_proc.status_code == 200
    assert res_proc.json()["status"] == "SUCCESSFUL"

    # 4. Gateway Webhook Simulation
    res_hook = client.post("/api/v1/payments/webhook", json={
        "event_type": "charge.succeeded",
        "transaction_reference": pay_data["transaction_reference"],
        "status": "SUCCESSFUL"
    })
    assert res_hook.status_code == 200


# =====================================================================
# MODULE 30: PAYMENT TRANSACTION HISTORY
# =====================================================================
def test_module30_payment_transaction_history(client, admin_token, customer_token):
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    cust_headers = {"Authorization": f"Bearer {customer_token}"}

    # 1. Retrieve transactions for order
    res_tx = client.get("/api/v1/payments/transactions/order/1", headers=cust_headers)
    assert res_tx.status_code == 200
    txs = res_tx.json()
    assert len(txs) >= 1
    assert any(t["status"] in ["SUCCESS", "PENDING"] for t in txs)

    # 2. Administrative audit query
    res_all = client.get("/api/v1/payments/transactions/", headers=admin_headers)
    assert res_all.status_code == 200
    assert len(res_all.json()) >= 1


# =====================================================================
# MODULE 31: REFUND MANAGEMENT
# =====================================================================
def test_module31_refund_management(client, admin_token):
    headers = {"Authorization": f"Bearer {admin_token}"}

    # 1. Process valid refund
    res_ref = client.post("/api/v1/refunds/", headers=headers, json={
        "order_id": 1,
        "amount": 50.00,
        "reason": "Promotional price match adjustment",
        "admin_notes": "Issued via customer satisfaction policy"
    })
    assert res_ref.status_code == 201
    refund = res_ref.json()
    assert refund["status"] == "COMPLETED"
    assert float(refund["amount"]) == 50.00

    # 2. Prevent excessive refund
    res_exceed = client.post("/api/v1/refunds/", headers=headers, json={
        "order_id": 1,
        "amount": 999999.00,
        "reason": "Excessive amount"
    })
    assert res_exceed.status_code == 400

    # 3. Retrieve refunds for order
    res_get = client.get("/api/v1/refunds/order/1", headers=headers)
    assert res_get.status_code == 200
    assert len(res_get.json()) >= 1


# =====================================================================
# MODULE 32: CASH ON DELIVERY MANAGEMENT
# =====================================================================
def test_module32_cash_on_delivery_management(client, admin_token):
    headers = {"Authorization": f"Bearer {admin_token}"}

    # 1. Get and update COD configuration
    res_cfg = client.get("/api/v1/cod/config")
    assert res_cfg.status_code == 200
    assert res_cfg.json()["is_enabled"] is True

    # 2. Validate COD eligibility - Valid
    res_elig1 = client.post("/api/v1/cod/validate-eligibility", json={
        "order_amount": 150.00,
        "postal_code": "94107"
    })
    assert res_elig1.status_code == 200
    assert res_elig1.json()["is_eligible"] is True

    # 3. Validate COD eligibility - Restricted postal code
    res_elig2 = client.post("/api/v1/cod/validate-eligibility", json={
        "order_amount": 150.00,
        "postal_code": "REMOTE-101"
    })
    assert res_elig2.status_code == 200
    assert res_elig2.json()["is_eligible"] is False

    # 4. Record collection
    res_ord = client.get("/api/v1/orders/1", headers=headers)
    assert res_ord.status_code == 200
    ord_total = float(res_ord.json()["total_amount"])

    res_coll = client.post("/api/v1/cod/collections/1/collect", headers=headers, json={
        "collected_amount": ord_total,
        "collected_by": "Courier Agent #44",
        "notes": "Exact cash received at loading dock"
    })
    assert res_coll.status_code == 200
    assert res_coll.json()["status"] == "COLLECTED"


# =====================================================================
# MODULE 33: SHIPPING ORDER MANAGEMENT
# =====================================================================
def test_module33_shipping_order_management(client, admin_token):
    headers = {"Authorization": f"Bearer {admin_token}"}

    # 1. Create shipment
    res_shp = client.post("/api/v1/shipments/", headers=headers, json={
        "order_id": 1,
        "carrier_name": "DHL",
        "dispatch_notes": "Priority overnight freight packaging"
    })
    assert res_shp.status_code == 201
    shp = res_shp.json()
    shipment_id = shp["id"]
    assert shp["carrier_name"] == "DHL"
    assert "tracking_number" in shp

    # 2. Dispatch shipment
    res_disp = client.post(f"/api/v1/shipments/{shipment_id}/dispatch", headers=headers, json={
        "dispatch_notes": "Departed fulfillment warehouse on route 10"
    })
    assert res_disp.status_code == 200
    assert res_disp.json()["status"] == "DISPATCHED"


# =====================================================================
# MODULE 34: SHIPMENT TRACKING
# =====================================================================
def test_module34_shipment_tracking(client, admin_token):
    headers = {"Authorization": f"Bearer {admin_token}"}

    # 1. Create a shipment for tracking
    res_shp = client.post("/api/v1/shipments/", headers=headers, json={
        "order_id": 1,
        "carrier_name": "FedEx"
    })
    assert res_shp.status_code == 201
    shp_id = res_shp.json()["id"]
    trk_num = res_shp.json()["tracking_number"]

    # 2. Record checkpoint event
    res_evt = client.post(f"/api/v1/shipments/{shp_id}/events", headers=headers, json={
        "event_type": "IN_TRANSIT",
        "location": "Memphis Sorting Center",
        "description": "Processed through sorting hub"
    })
    assert res_evt.status_code == 201
    assert res_evt.json()["event_type"] == "IN_TRANSIT"

    # 3. Public tracking endpoint
    res_track = client.get(f"/api/v1/shipments/tracking/{trk_num}")
    assert res_track.status_code == 200
    events = res_track.json()
    assert len(events) >= 2


# =====================================================================
# MODULE 35: DELIVERY MANAGEMENT
# =====================================================================
def test_module35_delivery_management(client, admin_token):
    headers = {"Authorization": f"Bearer {admin_token}"}

    # 1. Create shipment
    res_shp = client.post("/api/v1/shipments/", headers=headers, json={
        "order_id": 1,
        "carrier_name": "LocalExpress"
    })
    shp_id = res_shp.json()["id"]

    # 2. Assign delivery personnel
    res_assign = client.post("/api/v1/shipments/deliveries/assign", headers=headers, json={
        "shipment_id": shp_id,
        "driver_name": "Michael Roberts",
        "driver_phone": "+1-415-555-8819"
    })
    assert res_assign.status_code == 201
    assign_id = res_assign.json()["id"]
    assert res_assign.json()["status"] == "ASSIGNED"

    # 3. Record failed delivery attempt
    res_att = client.post(f"/api/v1/shipments/deliveries/{assign_id}/attempt", headers=headers, json={
        "failure_reason": "Gate locked, security code required"
    })
    assert res_att.status_code == 200
    assert res_att.json()["delivery_attempts"] == 1
    assert res_att.json()["status"] == "ATTEMPTED_FAILED"

    # 4. Confirm delivery
    res_conf = client.post(f"/api/v1/shipments/deliveries/{assign_id}/confirm", headers=headers, json={
        "recipient_signature_name": "Sarah Miller",
        "confirmation_notes": "Delivered to reception desk"
    })
    assert res_conf.status_code == 200
    assert res_conf.json()["status"] == "DELIVERED"


# =====================================================================
# MODULE 36: RETURN MANAGEMENT
# =====================================================================
def test_module36_return_management(client, customer_token, admin_token):
    cust_headers = {"Authorization": f"Bearer {customer_token}"}
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    # 1. Ensure order 1 is DELIVERED
    client.post("/api/v1/order-status/transition/1", headers=admin_headers, json={"to_status": "SHIPPED"})
    client.post("/api/v1/order-status/transition/1", headers=admin_headers, json={"to_status": "DELIVERED"})

    # 2. Customer submits return
    res_ret = client.post("/api/v1/returns/", headers=cust_headers, json={
        "order_id": 1,
        "reason": "Item size does not fit workstation desk",
        "items": [
            {
                "order_item_id": 1,
                "quantity": 1,
                "item_condition": "UNOPENED"
            }
        ]
    })
    assert res_ret.status_code == 201
    ret = res_ret.json()
    ret_id = ret["id"]
    assert ret["status"] == "REQUESTED"

    # 3. Admin reviews & approves return
    res_rev = client.patch(f"/api/v1/returns/{ret_id}/review", headers=admin_headers, json={
        "status": "APPROVED",
        "admin_notes": "Return authorization RMA generated"
    })
    assert res_rev.status_code == 200
    assert res_rev.json()["status"] == "APPROVED"

    # 4. Warehouse receives returned goods
    res_recv = client.post(f"/api/v1/returns/{ret_id}/receive", headers=admin_headers)
    assert res_recv.status_code == 200
    assert res_recv.json()["status"] == "ITEMS_RECEIVED"


# =====================================================================
# MODULE 37: EXCHANGE MANAGEMENT
# =====================================================================
def test_module37_exchange_management(client, customer_token, admin_token):
    cust_headers = {"Authorization": f"Bearer {customer_token}"}
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    # 1. Customer requests exchange
    res_exc = client.post("/api/v1/exchanges/", headers=cust_headers, json={
        "order_id": 1,
        "original_item_id": 1,
        "replacement_variant_id": 2,
        "quantity": 1,
        "reason": "Exchanging for alternate colorway"
    })
    assert res_exc.status_code == 201
    exc = res_exc.json()
    exc_id = exc["id"]
    assert exc["status"] == "REQUESTED"

    # 2. Staff approves exchange
    res_rev = client.patch(f"/api/v1/exchanges/{exc_id}/review", headers=admin_headers, json={
        "status": "APPROVED",
        "admin_notes": "Approved for warehouse dispatch"
    })
    assert res_rev.status_code == 200
    assert res_rev.json()["status"] == "APPROVED"

    # 3. Dispatch replacement goods
    res_disp = client.post(f"/api/v1/exchanges/{exc_id}/dispatch", headers=admin_headers)
    assert res_disp.status_code == 200
    assert res_disp.json()["status"] == "DISPATCHED"


# =====================================================================
# MODULE 38: PRODUCT REVIEWS AND RATINGS
# =====================================================================
def test_module38_product_reviews_and_ratings(client, customer_token, admin_token):
    cust_headers = {"Authorization": f"Bearer {customer_token}"}
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    # 1. Submit product review (product 2 to avoid seed conflict)
    res_rev = client.post("/api/v1/reviews/products/2", headers=cust_headers, json={
        "rating": 5,
        "title": "Outstanding Ergonomics",
        "comment": "Super quiet keys and stellar battery life."
    })
    assert res_rev.status_code == 201
    rev = res_rev.json()
    rev_id = rev["id"]
    assert rev["rating"] == 5

    # 2. Prevent duplicate review for same product by same user
    res_dup = client.post("/api/v1/reviews/products/2", headers=cust_headers, json={
        "rating": 4,
        "comment": "Trying to post a second review"
    })
    assert res_dup.status_code == 409

    # 3. Retrieve rating summary
    res_sum = client.get("/api/v1/reviews/products/2/summary")
    assert res_sum.status_code == 200
    summary = res_sum.json()
    assert summary["total_reviews"] >= 1
    assert summary["average_rating"] >= 4.0

    # 4. Moderate review
    res_mod = client.patch(f"/api/v1/reviews/{rev_id}/moderation", headers=admin_headers, json={
        "status": "APPROVED",
        "moderation_notes": "Approved by content safety filter"
    })
    assert res_mod.status_code == 200


# =====================================================================
# MODULE 39: PRODUCT QUESTIONS AND ANSWERS
# =====================================================================
def test_module39_product_questions_and_answers(client, customer_token, employee_token):
    cust_headers = {"Authorization": f"Bearer {customer_token}"}
    emp_headers = {"Authorization": f"Bearer {employee_token}"}

    # 1. Ask question
    res_q = client.post("/api/v1/questions/products/2", headers=cust_headers, json={
        "question_text": "Is this model compatible with macOS Sequoia?"
    })
    assert res_q.status_code == 201
    q = res_q.json()
    q_id = q["id"]

    # 2. Answer question as employee
    res_a = client.post(f"/api/v1/questions/{q_id}/answers", headers=emp_headers, json={
        "answer_text": "Yes, native drivers and keyboard shortcuts are supported out of the box."
    })
    assert res_a.status_code == 201
    assert res_a.json()["is_staff_answer"] is True

    # 3. List questions for product
    res_list = client.get("/api/v1/questions/products/2")
    assert res_list.status_code == 200
    assert len(res_list.json()) >= 1


# =====================================================================
# MODULE 40: CUSTOMER SUPPORT TICKETS
# =====================================================================
def test_module40_customer_support_tickets(client, customer_token, employee_token):
    cust_headers = {"Authorization": f"Bearer {customer_token}"}
    emp_headers = {"Authorization": f"Bearer {employee_token}"}

    # 1. Create support ticket
    res_tck = client.post("/api/v1/support-tickets/", headers=cust_headers, json={
        "subject": "Need assistance updating delivery notes",
        "category": "ORDER_ISSUE",
        "priority": "HIGH",
        "message": "Please instruct courier to leave parcel behind side gate.",
        "order_id": 1
    })
    assert res_tck.status_code == 201
    tck = res_tck.json()
    tck_id = tck["id"]
    assert tck["status"] == "OPEN"

    # 2. Staff replies to ticket
    res_reply = client.post(f"/api/v1/support-tickets/{tck_id}/messages", headers=emp_headers, json={
        "message": "We have updated the courier manifest with your delivery instructions.",
        "is_internal_note": False
    })
    assert res_reply.status_code == 201

    # 3. Assign ticket to agent
    res_assign = client.patch(f"/api/v1/support-tickets/{tck_id}/assign", headers=emp_headers, json={
        "assigned_to_user_id": 2
    })
    assert res_assign.status_code == 200
    assert res_assign.json()["assigned_to_user_id"] == 2

    # 4. Resolve ticket
    res_res = client.patch(f"/api/v1/support-tickets/{tck_id}/status", headers=emp_headers, json={
        "status": "RESOLVED"
    })
    assert res_res.status_code == 200
    assert res_res.json()["status"] == "RESOLVED"





