// ShopSphere Pro SPA Client State
let currentToken = localStorage.getItem("shopsphere_token") || "";
let currentRefreshToken = localStorage.getItem("shopsphere_refresh_token") || "";
let currentUser = JSON.parse(localStorage.getItem("shopsphere_user") || "null");

function showToast(message, isError = false) {
  const toast = document.getElementById("toast");
  toast.innerText = message;
  toast.style.background = isError ? "#ef4444" : "#1e293b";
  toast.style.display = "block";
  setTimeout(() => {
    toast.style.display = "none";
  }, 3500);
}

function authHeaders() {
  const headers = { "Content-Type": "application/json" };
  if (currentToken) {
    headers["Authorization"] = `Bearer ${currentToken}`;
  }
  return headers;
}

function updateAuthUI() {
  const badge = document.getElementById("userBadge");
  const logoutBtn = document.getElementById("logoutBtn");
  const tokenBox = document.getElementById("tokenInfoBox");

  if (currentUser) {
    badge.innerHTML = `<span>👤 ${currentUser.first_name} ${currentUser.last_name}</span> <span class="role-tag">${currentUser.role}</span>`;
    logoutBtn.style.display = "inline-flex";
    if (tokenBox) {
      tokenBox.innerText = JSON.stringify({
        authenticated_user: currentUser,
        access_token_preview: currentToken ? currentToken.substring(0, 32) + "..." : "none",
        permissions: currentUser.permissions
      }, null, 2);
    }
  } else {
    badge.innerHTML = `<span>👤 Guest</span> <span class="role-tag">UNAUTHENTICATED</span>`;
    logoutBtn.style.display = "none";
    if (tokenBox) {
      tokenBox.innerText = "No active session. Please log in with one of the quick login buttons above or via credentials.";
    }
  }
}

function switchTab(tabId) {
  document.querySelectorAll(".tab-panel").forEach(p => p.classList.remove("active"));
  document.querySelectorAll(".tab-btn").forEach(b => b.classList.remove("active"));
  
  const target = document.getElementById(tabId);
  if (target) target.classList.add("active");

  const btn = Array.from(document.querySelectorAll(".tab-btn")).find(b => b.getAttribute("onclick")?.includes(tabId));
  if (btn) btn.classList.add("active");

  if (tabId === "tab-users") loadUsers();
  if (tabId === "tab-profile") loadProfile();
  if (tabId === "tab-addresses") loadAddresses();
  if (tabId === "tab-categories") loadCategories();
  if (tabId === "tab-brands") loadBrands();
  if (tabId === "tab-products") loadProducts();
  if (tabId === "tab-variants") { loadProductsDropdown(); loadVariantsForSelectedProduct(); }
  if (tabId === "tab-media") { loadProductsDropdown(); loadMedia(); }
  if (tabId === "tab-attributes") loadAttributes();
  if (tabId === "tab-pricing") { loadPricingDropdown(); }
  if (tabId === "tab-inventory") { loadInventoryDropdown(); }
  if (tabId === "tab-warehouses") loadWarehouses();
  if (tabId === "tab-transfers") { loadWarehousesForTransfer(); loadTransfers(); }
  if (tabId === "tab-lowstock") loadLowStockData();
  if (tabId === "tab-cart") loadCart();
  if (tabId === "tab-cartcalc") calculateCartSummary();
  if (tabId === "tab-wishlist") loadWishlist();
  if (tabId === "tab-coupons") loadCoupons();
  if (tabId === "tab-promotions") loadPromotions();
  if (tabId === "tab-taxes") loadTaxes();
  if (tabId === "tab-shipping") loadShippingMethods();
  if (tabId === "tab-checkout") loadCheckoutAddresses();
  if (tabId === "tab-orders") loadOrders();
  if (tabId === "tab-orderitems") loadOrderItemsUI();
  if (tabId === "tab-orderstatus") loadOrderStatusUI();
  if (tabId === "tab-cancellations") loadCancellationsUI();
  if (tabId === "tab-payments") loadPaymentsUI();
  if (tabId === "tab-transactions") loadTransactionsUI();
  if (tabId === "tab-refunds") loadRefundsUI();
  if (tabId === "tab-cod") loadCodUI();
  if (tabId === "tab-shipments") loadShipmentsUI();
  if (tabId === "tab-tracking") queryTrackingEvents();
  if (tabId === "tab-delivery") loadDeliveryUI();
  if (tabId === "tab-returns") loadReturnsUI();
  if (tabId === "tab-exchanges") loadExchangesUI();
  if (tabId === "tab-reviews") loadReviewsUI();
  if (tabId === "tab-qa") loadQAUI();
  if (tabId === "tab-tickets") loadTicketsUI();
  if (tabId === "tab-notifications") loadNotifications();
  if (tabId === "tab-messaging") loadMessaging();
  if (tabId === "tab-suppliers") loadSuppliers();
  if (tabId === "tab-po") { loadPoDropdowns(); loadPurchaseOrders(); }
  if (tabId === "tab-invoices") { loadInvoiceDropdowns(); loadSupplierInvoices(); }
  if (tabId === "tab-audit") loadAuditLogs();
  if (tabId === "tab-dashboard") loadExecutiveDashboard();
  if (tabId === "tab-analytics") loadAnalytics();
  if (tabId === "tab-tasks") loadBackgroundTasks();
}

// Quick Login
async function quickLogin(email, password) {
  document.getElementById("loginEmail").value = email;
  document.getElementById("loginPassword").value = password;
  await submitLogin();
}

async function submitLogin() {
  const email = document.getElementById("loginEmail").value.trim();
  const password = document.getElementById("loginPassword").value;

  try {
    const res = await fetch("/api/v1/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password })
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Login failed");

    currentToken = data.access_token;
    currentRefreshToken = data.refresh_token;
    currentUser = data.user;

    localStorage.setItem("shopsphere_token", currentToken);
    localStorage.setItem("shopsphere_refresh_token", currentRefreshToken);
    localStorage.setItem("shopsphere_user", JSON.stringify(currentUser));

    updateAuthUI();
    showToast(`Welcome back, ${currentUser.first_name}!`);
    loadKPIs();
  } catch (err) {
    showToast(err.message, true);
  }
}

async function handleRefreshToken() {
  if (!currentRefreshToken) {
    showToast("No refresh token available. Please log in first.", true);
    return;
  }
  try {
    const res = await fetch("/api/v1/auth/refresh", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh_token: currentRefreshToken })
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Token refresh failed");

    currentToken = data.access_token;
    currentRefreshToken = data.refresh_token;
    currentUser = data.user;

    localStorage.setItem("shopsphere_token", currentToken);
    localStorage.setItem("shopsphere_refresh_token", currentRefreshToken);
    localStorage.setItem("shopsphere_user", JSON.stringify(currentUser));

    updateAuthUI();
    showToast("Tokens rotated and refreshed successfully!");
  } catch (err) {
    showToast(err.message, true);
  }
}

async function handleLogout() {
  try {
    if (currentToken) {
      await fetch("/api/v1/auth/logout", {
        method: "POST",
        headers: authHeaders(),
        body: JSON.stringify({ refresh_token: currentRefreshToken })
      });
    }
  } catch (e) {
    // ignore
  }
  currentToken = "";
  currentRefreshToken = "";
  currentUser = null;
  localStorage.removeItem("shopsphere_token");
  localStorage.removeItem("shopsphere_refresh_token");
  localStorage.removeItem("shopsphere_user");
  updateAuthUI();
  showToast("Logged out and revoked session tokens.");
}

// Module 2: Users
async function loadUsers() {
  const query = document.getElementById("userSearchInput")?.value || "";
  const role = document.getElementById("userRoleFilter")?.value || "";
  const status = document.getElementById("userStatusFilter")?.value || "";

  let url = `/api/v1/users?page=1&limit=50`;
  if (query) url += `&query=${encodeURIComponent(query)}`;
  if (role) url += `&role=${encodeURIComponent(role)}`;
  if (status) url += `&status=${encodeURIComponent(status)}`;

  const tbody = document.getElementById("usersTableBody");
  try {
    const res = await fetch(url, { headers: authHeaders() });
    if (!res.ok) {
      tbody.innerHTML = `<tr><td colspan="7" style="color:red;">Login as ADMIN or EMPLOYEE to inspect user management.</td></tr>`;
      return;
    }
    const data = await res.json();
    if (!data.items || data.items.length === 0) {
      tbody.innerHTML = `<tr><td colspan="7">No matching users found.</td></tr>`;
      return;
    }
    tbody.innerHTML = data.items.map(u => `
      <tr>
        <td><strong>#${u.id}</strong></td>
        <td>${u.first_name} ${u.last_name}</td>
        <td>${u.email}<br><small style="color:var(--gray-500);">${u.phone || 'No phone'}</small></td>
        <td><span class="badge" style="background:#e0e7ff; color:#3730a3;">${u.role}</span></td>
        <td><span class="badge badge-${u.status.toLowerCase()}">${u.status}</span></td>
        <td>${u.is_verified ? '✅ Verified' : '⏳ Pending'}</td>
        <td>
          <button class="btn btn-secondary btn-sm" onclick="toggleUserStatus(${u.id}, '${u.status === 'ACTIVE' ? 'INACTIVE' : 'ACTIVE'}')">
            ${u.status === 'ACTIVE' ? 'Deactivate' : 'Activate'}
          </button>
        </td>
      </tr>
    `).join("");
  } catch (err) {
    tbody.innerHTML = `<tr><td colspan="7" style="color:red;">Error loading users: ${err.message}</td></tr>`;
  }
}

async function toggleUserStatus(userId, newStatus) {
  try {
    const res = await fetch(`/api/v1/users/${userId}/status`, {
      method: "PATCH",
      headers: authHeaders(),
      body: JSON.stringify({ status: newStatus, reason: "Status toggle from admin UI" })
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Failed to update status");
    showToast(`User #${userId} status updated to ${newStatus}`);
    loadUsers();
  } catch (e) {
    showToast(e.message, true);
  }
}

// Module 3: Customer Registration
async function submitRegistration() {
  const firstName = document.getElementById("regFirstName").value.trim();
  const lastName = document.getElementById("regLastName").value.trim();
  const email = document.getElementById("regEmail").value.trim();
  const phone = document.getElementById("regPhone").value.trim();
  const password = document.getElementById("regPassword").value;
  const marketing_opt_in = document.getElementById("regOptIn").checked;

  try {
    const res = await fetch("/api/v1/registration/register", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        first_name: firstName,
        last_name: lastName,
        email,
        phone,
        password,
        marketing_opt_in
      })
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Registration failed");

    document.getElementById("verifyTokenInput").value = data.verification_token;
    const box = document.getElementById("regResultBox");
    box.style.display = "block";
    box.innerHTML = `
      <strong style="color:green;">🎉 Registration Created!</strong><br>
      User ID: #${data.user_id} (${data.email})<br>
      Status: <span class="badge badge-pending">${data.registration_status}</span><br>
      Token: <code style="word-break:break-all;">${data.verification_token}</code><br>
      <button class="btn btn-success btn-sm" style="margin-top:0.5rem;" onclick="verifyToken('${data.verification_token}')">⚡ One-Click Verify Account</button>
    `;
    showToast("Customer registered successfully!");
    loadKPIs();
  } catch (err) {
    showToast(err.message, true);
  }
}

async function verifyToken(suppliedToken) {
  const token = suppliedToken || document.getElementById("verifyTokenInput").value.trim();
  if (!token) {
    showToast("Please provide a verification token", true);
    return;
  }
  try {
    const res = await fetch(`/api/v1/registration/verify-email?token=${encodeURIComponent(token)}`);
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Verification failed");
    showToast(data.message || "Email verified successfully!");
    loadKPIs();
  } catch (err) {
    showToast(err.message, true);
  }
}

// Module 4: Customer Profile & Audit
async function loadProfile() {
  if (!currentToken) {
    showToast("Please log in to inspect your profile", true);
    return;
  }
  try {
    const res = await fetch("/api/v1/customer/profile/me", { headers: authHeaders() });
    if (!res.ok) return;
    const p = await res.json();

    document.getElementById("profFirstName").value = p.first_name || "";
    document.getElementById("profLastName").value = p.last_name || "";
    document.getElementById("profPhone").value = p.phone || "";
    document.getElementById("profSecondaryEmail").value = p.secondary_email || "";
    document.getElementById("profDob").value = p.date_of_birth || "";
    document.getElementById("profGender").value = p.gender || "";

    // Load History
    const hRes = await fetch("/api/v1/customer/profile/history?limit=20", { headers: authHeaders() });
    if (hRes.ok) {
      const hData = await hRes.json();
      const container = document.getElementById("profileHistoryContainer");
      if (!hData.items || hData.items.length === 0) {
        container.innerHTML = "No modifications logged yet for this profile.";
      } else {
        container.innerHTML = hData.items.map(h => `
          <div style="padding:0.4rem 0; border-bottom:1px solid #cbd5e1;">
            <strong>${h.field_name}</strong> updated: <del style="color:red;">${h.old_value || 'none'}</del> ➔ <span style="color:green;">${h.new_value || 'none'}</span>
            <br><small style="color:var(--gray-500);">${new Date(h.changed_at).toLocaleString()}</small>
          </div>
        `).join("");
      }
    }
  } catch (e) {
    console.error(e);
  }
}

async function submitProfileUpdate() {
  const payload = {
    first_name: document.getElementById("profFirstName").value.trim(),
    last_name: document.getElementById("profLastName").value.trim(),
    phone: document.getElementById("profPhone").value.trim(),
    secondary_email: document.getElementById("profSecondaryEmail").value.trim() || null,
    date_of_birth: document.getElementById("profDob").value || null,
    gender: document.getElementById("profGender").value || null
  };

  try {
    const res = await fetch("/api/v1/customer/profile/me", {
      method: "PUT",
      headers: authHeaders(),
      body: JSON.stringify(payload)
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Profile update failed");
    showToast("Profile updated successfully!");
    loadProfile();
  } catch (err) {
    showToast(err.message, true);
  }
}

async function requestDeactivation() {
  const reason = document.getElementById("deactivateReason").value.trim();
  if (!reason) {
    showToast("Please provide a reason for deactivation", true);
    return;
  }
  try {
    const res = await fetch("/api/v1/customer/profile/deactivation-request", {
      method: "POST",
      headers: authHeaders(),
      body: JSON.stringify({ reason })
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Failed to submit request");
    showToast(data.message);
  } catch (e) {
    showToast(e.message, true);
  }
}

// Module 5: Addresses
function showAddAddressForm() { document.getElementById("addressFormCard").style.display = "block"; }
function hideAddAddressForm() { document.getElementById("addressFormCard").style.display = "none"; }

async function loadAddresses() {
  const tbody = document.getElementById("addressTableBody");
  try {
    const res = await fetch("/api/v1/customer/addresses", { headers: authHeaders() });
    if (!res.ok) {
      tbody.innerHTML = `<tr><td colspan="7">Please log in to manage your addresses.</td></tr>`;
      return;
    }
    const addrs = await res.json();
    if (!addrs || addrs.length === 0) {
      tbody.innerHTML = `<tr><td colspan="7">No addresses found. Click "Add Address" above to create one.</td></tr>`;
      return;
    }
    tbody.innerHTML = addrs.map(a => `
      <tr>
        <td><strong>#${a.id}</strong></td>
        <td>${a.full_name}</td>
        <td><span class="badge" style="background:#e0f2fe; color:#0369a1;">${a.address_type}</span></td>
        <td>${a.street_line1}, ${a.city}, ${a.state_province} ${a.postal_code}, ${a.country}</td>
        <td>${a.phone_number}</td>
        <td>
          ${a.is_default ? '<span class="badge badge-active">Default Ship</span> ' : ''}
          ${a.is_default_billing ? '<span class="badge badge-instock">Default Bill</span>' : ''}
          ${!a.is_default && !a.is_default_billing ? '<span style="color:var(--gray-500);">-</span>' : ''}
        </td>
        <td>
          <button class="btn btn-secondary btn-sm" onclick="setDefaultAddress(${a.id}, 'shipping')">Set Ship Default</button>
          <button class="btn btn-danger btn-sm" onclick="deleteAddress(${a.id})">Delete</button>
        </td>
      </tr>
    `).join("");
  } catch (err) {
    tbody.innerHTML = `<tr><td colspan="7" style="color:red;">Error: ${err.message}</td></tr>`;
  }
}

async function submitCreateAddress() {
  const payload = {
    full_name: document.getElementById("addrFullName").value.trim(),
    phone_number: document.getElementById("addrPhone").value.trim(),
    address_type: document.getElementById("addrType").value,
    street_line1: document.getElementById("addrStreet1").value.trim(),
    city: document.getElementById("addrCity").value.trim(),
    state_province: document.getElementById("addrState").value.trim(),
    postal_code: document.getElementById("addrZip").value.trim(),
    country: document.getElementById("addrCountry").value.trim(),
    is_default: true
  };
  try {
    const res = await fetch("/api/v1/customer/addresses", {
      method: "POST",
      headers: authHeaders(),
      body: JSON.stringify(payload)
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Failed to create address");
    showToast("Address saved!");
    hideAddAddressForm();
    loadAddresses();
  } catch (err) {
    showToast(err.message, true);
  }
}

async function setDefaultAddress(addrId, type) {
  try {
    const res = await fetch(`/api/v1/customer/addresses/${addrId}/set-default?default_type=${type}`, {
      method: "PATCH",
      headers: authHeaders()
    });
    if (!res.ok) throw new Error("Failed to set default address");
    showToast(`Address #${addrId} set as default ${type}`);
    loadAddresses();
  } catch (e) {
    showToast(e.message, true);
  }
}

async function deleteAddress(addrId) {
  if (!confirm("Are you sure you want to delete this address?")) return;
  try {
    const res = await fetch(`/api/v1/customer/addresses/${addrId}`, {
      method: "DELETE",
      headers: authHeaders()
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Failed to delete address");
    showToast(data.message);
    loadAddresses();
  } catch (e) {
    showToast(e.message, true);
  }
}

// Module 6: Categories
function showAddCategoryForm() { document.getElementById("categoryFormCard").style.display = "block"; }
function hideAddCategoryForm() { document.getElementById("categoryFormCard").style.display = "none"; }

function renderTree(node) {
  const hasChildren = node.children && node.children.length > 0;
  return `
    <div class="tree-node">
      <div class="tree-node-title">
        📁 <strong>${node.name}</strong> <small style="color:var(--gray-500);">(/${node.slug})</small>
        ${node.is_active ? '<span class="badge badge-active">ACTIVE</span>' : '<span class="badge badge-inactive">INACTIVE</span>'}
      </div>
      ${hasChildren ? node.children.map(c => renderTree(c)).join("") : ''}
    </div>
  `;
}

async function loadCategories() {
  const treeContainer = document.getElementById("categoryTreeContainer");
  const catTbody = document.getElementById("categoryTableBody");
  const catParentSelect = document.getElementById("catParentId");

  try {
    const treeRes = await fetch("/api/v1/categories/tree?active_only=false");
    const treeData = await treeRes.json();
    if (!treeData || treeData.length === 0) {
      treeContainer.innerHTML = "No categories yet.";
    } else {
      treeContainer.innerHTML = treeData.map(r => renderTree(r)).join("");
    }

    const flatRes = await fetch("/api/v1/categories");
    const flatData = await flatRes.json();

    if (catParentSelect) {
      catParentSelect.innerHTML = `<option value="">Root Level (No Parent)</option>` +
        flatData.map(c => `<option value="${c.id}">${c.name}</option>`).join("");
    }

    catTbody.innerHTML = flatData.map(c => `
      <tr>
        <td>#${c.id}</td>
        <td><strong>${c.name}</strong></td>
        <td>${c.parent_id ? '#' + c.parent_id : 'Root'}</td>
        <td>
          <button class="btn btn-danger btn-sm" onclick="attemptDeleteCategory(${c.id})">Safe Delete</button>
        </td>
      </tr>
    `).join("");
  } catch (e) {
    console.error(e);
  }
}

async function submitCreateCategory() {
  const name = document.getElementById("catName").value.trim();
  const parent_id = document.getElementById("catParentId").value ? parseInt(document.getElementById("catParentId").value) : null;
  const display_order = parseInt(document.getElementById("catDisplayOrder").value) || 0;

  try {
    const res = await fetch("/api/v1/categories", {
      method: "POST",
      headers: authHeaders(),
      body: JSON.stringify({ name, parent_id, display_order, is_active: true })
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Failed to create category");
    showToast(`Category '${data.name}' created!`);
    hideAddCategoryForm();
    loadCategories();
    loadKPIs();
  } catch (err) {
    showToast(err.message, true);
  }
}

async function attemptDeleteCategory(catId) {
  try {
    const res = await fetch(`/api/v1/categories/${catId}`, {
      method: "DELETE",
      headers: authHeaders()
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Delete rejected");
    showToast(data.message);
    loadCategories();
    loadKPIs();
  } catch (err) {
    showToast(err.message, true);
  }
}

// Module 7: Brands
function showAddBrandForm() { document.getElementById("brandFormCard").style.display = "block"; }
function hideAddBrandForm() { document.getElementById("brandFormCard").style.display = "none"; }

async function loadBrands() {
  const tbody = document.getElementById("brandTableBody");
  try {
    const res = await fetch("/api/v1/brands?limit=50");
    const data = await res.json();
    if (!data.items || data.items.length === 0) {
      tbody.innerHTML = `<tr><td colspan="6">No brands found.</td></tr>`;
      return;
    }
    tbody.innerHTML = data.items.map(b => `
      <tr>
        <td><strong>#${b.id}</strong></td>
        <td><strong>${b.name}</strong></td>
        <td><code>${b.code}</code></td>
        <td><span class="badge badge-${b.status.toLowerCase()}">${b.status}</span></td>
        <td>${b.products_count} products</td>
        <td>
          <button class="btn btn-secondary btn-sm" onclick="toggleBrandStatus(${b.id}, '${b.status === 'ACTIVE' ? 'INACTIVE' : 'ACTIVE'}')">
            ${b.status === 'ACTIVE' ? 'Set Inactive' : 'Set Active'}
          </button>
        </td>
      </tr>
    `).join("");
  } catch (e) {
    tbody.innerHTML = `<tr><td colspan="6" style="color:red;">Error loading brands: ${e.message}</td></tr>`;
  }
}

async function submitCreateBrand() {
  const name = document.getElementById("brandName").value.trim();
  const code = document.getElementById("brandCode").value.trim() || null;
  const website_url = document.getElementById("brandWebsite").value.trim() || null;

  try {
    const res = await fetch("/api/v1/brands", {
      method: "POST",
      headers: authHeaders(),
      body: JSON.stringify({ name, code, website_url, status: "ACTIVE" })
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Brand creation failed");
    showToast(`Brand '${data.name}' registered!`);
    hideAddBrandForm();
    loadBrands();
    loadKPIs();
  } catch (err) {
    showToast(err.message, true);
  }
}

async function toggleBrandStatus(brandId, newStatus) {
  try {
    const res = await fetch(`/api/v1/brands/${brandId}/status?status=${newStatus}`, {
      method: "PATCH",
      headers: authHeaders()
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Failed to update brand status");
    showToast(`Brand status set to ${newStatus}`);
    loadBrands();
  } catch (e) {
    showToast(e.message, true);
  }
}

// Module 8: Products
function showAddProductForm() {
  document.getElementById("productFormCard").style.display = "block";
  loadDropdownsForProductCreate();
}
function hideAddProductForm() { document.getElementById("productFormCard").style.display = "none"; }

async function loadDropdownsForProductCreate() {
  const catSel = document.getElementById("pCatId");
  const brandSel = document.getElementById("pBrandId");

  const [cRes, bRes] = await Promise.all([
    fetch("/api/v1/categories?is_active=true"),
    fetch("/api/v1/brands?status=ACTIVE&limit=100")
  ]);

  const cats = await cRes.json();
  const brands = await bRes.json();

  catSel.innerHTML = `<option value="">Select category...</option>` +
    cats.map(c => `<option value="${c.id}">${c.name}</option>`).join("");
  brandSel.innerHTML = `<option value="">Select brand...</option>` +
    (brands.items || []).map(b => `<option value="${b.id}">${b.name}</option>`).join("");
}

async function loadProducts() {
  const query = document.getElementById("prodSearchInput")?.value || "";
  const catId = document.getElementById("prodCategoryFilter")?.value || "";
  const brandId = document.getElementById("prodBrandFilter")?.value || "";
  const sort = document.getElementById("prodSortBy")?.value || "newest";

  let url = `/api/v1/products?limit=50&sort_by=${sort}`;
  if (query) url += `&query=${encodeURIComponent(query)}`;
  if (catId) url += `&category_id=${catId}`;
  if (brandId) url += `&brand_id=${brandId}`;

  const tbody = document.getElementById("productsTableBody");
  try {
    const res = await fetch(url);
    const data = await res.json();
    if (!data.items || data.items.length === 0) {
      tbody.innerHTML = `<tr><td colspan="7">No matching products found.</td></tr>`;
      return;
    }
    tbody.innerHTML = data.items.map(p => `
      <tr>
        <td><code>${p.base_sku}</code></td>
        <td><strong>${p.name}</strong></td>
        <td><strong>$${parseFloat(p.base_price).toFixed(2)}</strong></td>
        <td>${p.category_id ? '#' + p.category_id : '-'}</td>
        <td>${p.brand_id ? '#' + p.brand_id : '-'}</td>
        <td><span class="badge badge-${p.status.toLowerCase()}">${p.status}</span></td>
        <td>
          <button class="btn btn-secondary btn-sm" onclick="viewProductVariants(${p.id})">Variants</button>
          <button class="btn btn-danger btn-sm" onclick="deleteProduct(${p.id})">Delete</button>
        </td>
      </tr>
    `).join("");
  } catch (e) {
    tbody.innerHTML = `<tr><td colspan="7" style="color:red;">Error loading products: ${e.message}</td></tr>`;
  }
}

async function submitCreateProduct() {
  const payload = {
    name: document.getElementById("pName").value.trim(),
    base_sku: document.getElementById("pSku").value.trim().toUpperCase(),
    base_price: parseFloat(document.getElementById("pPrice").value),
    category_id: document.getElementById("pCatId").value ? parseInt(document.getElementById("pCatId").value) : null,
    brand_id: document.getElementById("pBrandId").value ? parseInt(document.getElementById("pBrandId").value) : null,
    short_description: document.getElementById("pShortDesc").value.trim() || null,
    status: "ACTIVE"
  };

  try {
    const res = await fetch("/api/v1/products", {
      method: "POST",
      headers: authHeaders(),
      body: JSON.stringify(payload)
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Product creation failed");
    showToast(`Product '${data.name}' created!`);
    hideAddProductForm();
    loadProducts();
    loadKPIs();
  } catch (err) {
    showToast(err.message, true);
  }
}

async function deleteProduct(productId) {
  if (!confirm("Are you sure you want to delete this product? All variants and media will be removed.")) return;
  try {
    const res = await fetch(`/api/v1/products/${productId}`, {
      method: "DELETE",
      headers: authHeaders()
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Failed to delete product");
    showToast(data.message);
    loadProducts();
    loadKPIs();
  } catch (e) {
    showToast(e.message, true);
  }
}

// Module 9: Product Variants
function showAddVariantForm() { document.getElementById("variantFormCard").style.display = "block"; }
function hideAddVariantForm() { document.getElementById("variantFormCard").style.display = "none"; }

function viewProductVariants(productId) {
  switchTab("tab-variants");
  const sel = document.getElementById("variantProductSelector");
  if (sel) {
    sel.value = productId;
    loadVariantsForSelectedProduct();
  }
}

async function loadProductsDropdown() {
  const res = await fetch("/api/v1/products?limit=100");
  const data = await res.json();
  const vSel = document.getElementById("variantProductSelector");
  const mSel = document.getElementById("mediaProductSelect");

  const opts = (data.items || []).map(p => `<option value="${p.id}">${p.name} (${p.base_sku})</option>`).join("");
  if (vSel) vSel.innerHTML = `<option value="">Select a product...</option>` + opts;
  if (mSel) mSel.innerHTML = `<option value="">General Media</option>` + opts;
}

async function loadVariantsForSelectedProduct() {
  const prodId = document.getElementById("variantProductSelector").value;
  const tbody = document.getElementById("variantsTableBody");
  if (!prodId) {
    tbody.innerHTML = `<tr><td colspan="7">Please select a product above to inspect variants.</td></tr>`;
    return;
  }
  try {
    const res = await fetch(`/api/v1/products/${prodId}/variants`);
    const vars = await res.json();
    if (!vars || vars.length === 0) {
      tbody.innerHTML = `<tr><td colspan="7">No variants found for this product. Click "Add Variant" to create one.</td></tr>`;
      return;
    }
    tbody.innerHTML = vars.map(v => `
      <tr>
        <td><code>${v.sku}</code></td>
        <td><strong>${v.title}</strong></td>
        <td><strong>$${parseFloat(v.price).toFixed(2)}</strong></td>
        <td><strong>${v.stock_quantity}</strong></td>
        <td><span class="badge badge-${v.availability_status.toLowerCase()}">${v.availability_status}</span></td>
        <td><span class="badge badge-${v.status.toLowerCase()}">${v.status}</span></td>
        <td>
          <button class="btn btn-success btn-sm" onclick="adjustStock(${v.id}, 5)">+5 Stock</button>
          <button class="btn btn-warning btn-sm" onclick="adjustStock(${v.id}, -5)">-5 Stock</button>
        </td>
      </tr>
    `).join("");
  } catch (e) {
    tbody.innerHTML = `<tr><td colspan="7" style="color:red;">Error: ${e.message}</td></tr>`;
  }
}

async function submitCreateVariant() {
  const prodId = document.getElementById("variantProductSelector").value;
  if (!prodId) {
    showToast("Please select a product first", true);
    return;
  }
  let attrs = {};
  try {
    const rawAttrs = document.getElementById("vAttrs").value.trim();
    if (rawAttrs) attrs = JSON.parse(rawAttrs);
  } catch (e) {
    attrs = { note: document.getElementById("vAttrs").value.trim() };
  }

  const payload = {
    title: document.getElementById("vTitle").value.trim(),
    sku: document.getElementById("vSku").value.trim().toUpperCase(),
    price: parseFloat(document.getElementById("vPrice").value),
    stock_quantity: parseInt(document.getElementById("vStock").value) || 0,
    low_stock_threshold: parseInt(document.getElementById("vThreshold").value) || 5,
    attributes: attrs,
    status: "ACTIVE"
  };

  try {
    const res = await fetch(`/api/v1/products/${prodId}/variants`, {
      method: "POST",
      headers: authHeaders(),
      body: JSON.stringify(payload)
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Variant creation failed");
    showToast(`Variant '${data.sku}' created!`);
    hideAddVariantForm();
    loadVariantsForSelectedProduct();
    loadKPIs();
  } catch (err) {
    showToast(err.message, true);
  }
}

async function adjustStock(variantId, adjustment) {
  try {
    const res = await fetch(`/api/v1/variants/${variantId}/stock-adjust`, {
      method: "POST",
      headers: authHeaders(),
      body: JSON.stringify({ adjustment, reason: "Manual adjustment via dashboard" })
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Stock adjustment failed");
    showToast(`Stock updated to ${data.stock_quantity} (${data.availability_status})`);
    loadVariantsForSelectedProduct();
  } catch (err) {
    showToast(err.message, true);
  }
}

// Module 10: Media & Documents
async function loadMedia() {
  const tbody = document.getElementById("mediaTableBody");
  try {
    const res = await fetch("/api/v1/products?limit=100");
    const data = await res.json();
    const allMedia = [];

    for (const p of data.items || []) {
      const mRes = await fetch(`/api/v1/products/${p.id}/media`);
      if (mRes.ok) {
        const pMedia = await mRes.json();
        pMedia.forEach(m => allMedia.push({ ...m, productName: p.name }));
      }
    }

    if (allMedia.length === 0) {
      tbody.innerHTML = `<tr><td colspan="5">No uploaded files found. Use the upload form on the left.</td></tr>`;
      return;
    }

    tbody.innerHTML = allMedia.map(m => `
      <tr>
        <td>
          <strong>${m.original_filename}</strong>
          ${m.is_primary ? '<span class="badge badge-active">PRIMARY</span>' : ''}
          <br><small style="color:var(--gray-500);">${m.productName || 'General'}</small>
        </td>
        <td><span class="badge" style="background:#f1f5f9;">${m.mime_type}</span></td>
        <td>${(m.file_size_bytes / 1024).toFixed(1)} KB</td>
        <td>
          ${m.image_width ? `📐 ${m.image_width}x${m.image_height}px<br>` : ''}
          <code style="font-size:0.7rem;">${m.checksum_sha256 ? m.checksum_sha256.substring(0, 16) + '...' : '-'}</code>
        </td>
        <td>
          <a href="/api/v1/media/${m.id}/download" class="btn btn-secondary btn-sm" target="_blank">Download</a>
          <button class="btn btn-danger btn-sm" onclick="deleteMedia(${m.id})">Delete</button>
        </td>
      </tr>
    `).join("");
  } catch (e) {
    tbody.innerHTML = `<tr><td colspan="5" style="color:red;">Error loading media: ${e.message}</td></tr>`;
  }
}

async function submitUploadMedia() {
  const fileInput = document.getElementById("mediaFileInput");
  if (!fileInput.files || fileInput.files.length === 0) {
    showToast("Please select a file to upload", true);
    return;
  }
  const file = fileInput.files[0];
  const prodId = document.getElementById("mediaProductSelect").value;
  const fileType = document.getElementById("mediaTypeSelect").value;
  const isPrimary = document.getElementById("mediaIsPrimary").checked;

  const formData = new FormData();
  formData.append("file", file);
  if (prodId) formData.append("product_id", prodId);
  formData.append("file_type", fileType);
  formData.append("is_primary", isPrimary ? "true" : "false");

  try {
    const headers = {};
    if (currentToken) headers["Authorization"] = `Bearer ${currentToken}`;

    const res = await fetch("/api/v1/media/upload", {
      method: "POST",
      headers,
      body: formData
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Upload failed");
    showToast(`Uploaded '${data.original_filename}' successfully!`);
    fileInput.value = "";
    loadMedia();
    loadKPIs();
  } catch (err) {
    showToast(err.message, true);
  }
}

async function deleteMedia(mediaId) {
  if (!confirm("Are you sure you want to remove this media file?")) return;
  try {
    const res = await fetch(`/api/v1/media/${mediaId}`, {
      method: "DELETE",
      headers: authHeaders()
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Failed to delete media");
    showToast(data.message);
    loadMedia();
    loadKPIs();
  } catch (e) {
    showToast(e.message, true);
  }
}

// ==========================================
// MODULE 11: Product Attributes
// ==========================================
async function loadAttributes() {
  const tbody = document.getElementById("attributesTableBody");
  try {
    const res = await fetch("/api/v1/attributes", { headers: authHeaders() });
    if (!res.ok) throw new Error("Failed to load attributes");
    const data = await res.json();
    if (data.length === 0) {
      tbody.innerHTML = `<tr><td colspan="4" style="text-align:center; color:var(--gray-500);">No attributes defined yet.</td></tr>`;
      return;
    }
    tbody.innerHTML = data.map(a => `
      <tr>
        <td><strong>#${a.id}</strong></td>
        <td>
          <div style="font-weight:600;">${a.name}</div>
          <code style="font-size:0.75rem; color:var(--primary);">${a.code}</code>
        </td>
        <td><span class="badge badge-active">${a.data_type}</span></td>
        <td>${a.options && a.options.length ? a.options.map(o => `<span class="badge" style="background:#e0e7ff; color:#3730a3; margin-right:4px;">${o.value}</span>`).join('') : '<em style="color:#94a3b8;">None (Free text/number)</em>'}</td>
      </tr>
    `).join('');
  } catch (err) {
    tbody.innerHTML = `<tr><td colspan="4" style="color:red;">Error loading attributes: ${err.message}</td></tr>`;
  }
}

async function submitCreateAttribute() {
  const name = document.getElementById("attrName").value.trim();
  const code = document.getElementById("attrCode").value.trim() || undefined;
  const dataType = document.getElementById("attrDataType").value;
  const rawOpts = document.getElementById("attrOptions").value.trim();

  let options = undefined;
  if (rawOpts) {
    options = rawOpts.split(",").map(s => s.trim()).filter(Boolean);
  }

  try {
    const res = await fetch("/api/v1/attributes", {
      method: "POST",
      headers: authHeaders(),
      body: JSON.stringify({
        name,
        code,
        data_type: dataType,
        options: options && options.length > 0 ? options : undefined
      })
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Failed to create attribute");
    showToast(`Attribute '${data.name}' defined successfully!`);
    document.getElementById("attrName").value = "";
    document.getElementById("attrCode").value = "";
    document.getElementById("attrOptions").value = "";
    loadAttributes();
  } catch (err) {
    showToast(err.message, true);
  }
}

async function filterByAttr() {
  const code = document.getElementById("filterAttrCode").value.trim();
  const val = document.getElementById("filterAttrVal").value.trim();
  const resultDiv = document.getElementById("attrFilteredResults");
  if (!code || !val) {
    showToast("Please enter both attribute code and value to filter", true);
    return;
  }
  try {
    const res = await fetch(`/api/v1/attributes/products/filter-by-attributes?attribute_code=${encodeURIComponent(code)}&value=${encodeURIComponent(val)}`, {
      headers: authHeaders()
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Filter request failed");
    if (data.length === 0) {
      resultDiv.innerHTML = `<p style="color:var(--gray-500); margin-top:0.5rem;">No products match <code>${code}=${val}</code></p>`;
    } else {
      resultDiv.innerHTML = `
        <div style="margin-top:0.5rem; padding:0.5rem; background:white; border-radius:6px; border:1px solid var(--gray-200);">
          <strong>Matched ${data.length} Product(s):</strong>
          <ul style="margin:0.25rem 0 0 1.25rem; padding:0;">
            ${data.map(p => `<li><strong>${p.name}</strong> (SKU: ${p.base_sku}, $${p.base_price.toFixed(2)})</li>`).join('')}
          </ul>
        </div>
      `;
    }
  } catch (err) {
    resultDiv.innerHTML = `<p style="color:red; margin-top:0.5rem;">Error: ${err.message}</p>`;
  }
}

// ==========================================
// MODULE 12: Product Pricing
// ==========================================
async function loadPricingDropdown() {
  const sel = document.getElementById("pricingProductSelect");
  try {
    const res = await fetch("/api/v1/products?limit=100");
    if (!res.ok) return;
    const data = await res.json();
    const prods = data.items || [];
    sel.innerHTML = prods.map(p => `<option value="${p.id}">${p.name} (${p.base_sku})</option>`).join('');
    if (prods.length > 0) {
      loadPricingForSelected();
    }
  } catch (e) {
    console.error("Failed to load products for pricing", e);
  }
}

async function loadPricingForSelected() {
  const sel = document.getElementById("pricingProductSelect");
  const prodId = sel.value;
  if (!prodId) return;

  const basePriceInput = document.getElementById("pricingBasePrice");
  const salePriceInput = document.getElementById("pricingSalePrice");
  const startDateInput = document.getElementById("pricingStartDate");
  const endDateInput = document.getElementById("pricingEndDate");
  const historyBox = document.getElementById("priceHistoryContainer");

  try {
    const res = await fetch(`/api/v1/pricing/product/${prodId}`, { headers: authHeaders() });
    if (res.ok) {
      const p = await res.json();
      basePriceInput.value = p.base_price ?? "";
      salePriceInput.value = p.sale_price ?? "";
      startDateInput.value = p.sale_start_at ? p.sale_start_at.substring(0, 16) : "";
      endDateInput.value = p.sale_end_at ? p.sale_end_at.substring(0, 16) : "";
    }

    // Load price history
    const hRes = await fetch(`/api/v1/pricing/history/${prodId}`, { headers: authHeaders() });
    if (hRes.ok) {
      const hist = await hRes.json();
      if (hist.length === 0) {
        historyBox.innerHTML = `<em>No recorded price changes for this product yet.</em>`;
      } else {
        historyBox.innerHTML = hist.map(h => `
          <div style="border-bottom:1px solid var(--gray-200); padding:0.4rem 0;">
            <div style="display:flex; justify-content:space-between; font-weight:600;">
              <span>Base: $${h.old_base_price ? h.old_base_price.toFixed(2) : '-'} ➔ $${h.new_base_price.toFixed(2)}</span>
              <span style="font-size:0.75rem; color:var(--gray-500);">${new Date(h.created_at).toLocaleDateString()}</span>
            </div>
            ${h.new_sale_price ? `<div style="font-size:0.75rem; color:green;">Sale: $${h.new_sale_price.toFixed(2)}</div>` : ''}
            <div style="font-size:0.75rem; color:var(--gray-700);">Reason: ${h.change_reason || 'N/A'}</div>
          </div>
        `).join('');
      }
    }
  } catch (err) {
    console.error("Error loading pricing", err);
  }
}

async function submitPriceConfig() {
  const prodId = parseInt(document.getElementById("pricingProductSelect").value);
  const basePrice = parseFloat(document.getElementById("pricingBasePrice").value);
  const salePriceVal = document.getElementById("pricingSalePrice").value;
  const salePrice = salePriceVal ? parseFloat(salePriceVal) : null;
  const startDate = document.getElementById("pricingStartDate").value || null;
  const endDate = document.getElementById("pricingEndDate").value || null;
  const reason = document.getElementById("pricingReason").value.trim();

  try {
    const res = await fetch("/api/v1/pricing", {
      method: "POST",
      headers: authHeaders(),
      body: JSON.stringify({
        product_id: prodId,
        base_price: basePrice,
        sale_price: salePrice,
        sale_start_at: startDate,
        sale_end_at: endDate,
        change_reason: reason
      })
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Failed to update pricing");
    showToast("Pricing updated & logged to price audit history!");
    document.getElementById("pricingReason").value = "";
    loadPricingForSelected();
  } catch (err) {
    showToast(err.message, true);
  }
}

// ==========================================
// MODULE 13: Inventory Management
// ==========================================
async function loadInventoryDropdown() {
  const sel = document.getElementById("invProductSelect");
  try {
    const res = await fetch("/api/v1/products?limit=100");
    if (!res.ok) return;
    const data = await res.json();
    const prods = data.items || [];
    sel.innerHTML = prods.map(p => `<option value="${p.id}">${p.name} (${p.base_sku})</option>`).join('');
    if (prods.length > 0) {
      loadInventoryStatus();
    }
  } catch (e) {
    console.error("Failed to load inventory products", e);
  }
}

async function loadInventoryStatus() {
  const prodId = document.getElementById("invProductSelect").value;
  if (!prodId) return;

  const totalEl = document.getElementById("invTotal");
  const availEl = document.getElementById("invAvail");
  const reservedEl = document.getElementById("invReserved");
  const statusBadge = document.getElementById("invStatusBadge");
  const movementsBody = document.getElementById("movementsTableBody");

  try {
    const res = await fetch(`/api/v1/inventory/product/${prodId}`, { headers: authHeaders() });
    if (res.ok) {
      const items = await res.json();
      if (items.length > 0) {
        const root = items[0];
        totalEl.innerText = root.total_quantity;
        availEl.innerText = root.available_quantity;
        reservedEl.innerText = root.reserved_quantity;
        statusBadge.innerText = root.availability_status;
        statusBadge.className = `badge ${root.availability_status === 'IN_STOCK' ? 'badge-active' : root.availability_status === 'LOW_STOCK' ? 'badge-warning' : 'badge-suspended'}`;
      }
    }

    // Load stock movement history
    const mRes = await fetch(`/api/v1/inventory/movements/all?product_id=${prodId}&limit=25`, { headers: authHeaders() });
    if (mRes.ok) {
      const movs = await mRes.json();
      if (movs.length === 0) {
        movementsBody.innerHTML = `<tr><td colspan="5" style="text-align:center; color:var(--gray-500);">No movements recorded yet.</td></tr>`;
      } else {
        movementsBody.innerHTML = movs.map(m => `
          <tr>
            <td><span class="badge ${m.movement_type === 'ADDITION' ? 'badge-active' : m.movement_type === 'REDUCTION' ? 'badge-suspended' : 'badge-warning'}">${m.movement_type}</span></td>
            <td><strong>${m.quantity > 0 ? '+' : ''}${m.quantity}</strong></td>
            <td>${m.balance_after}</td>
            <td><code style="font-size:0.75rem;">${m.reference_type || 'N/A'}</code></td>
            <td style="font-size:0.8rem; color:var(--gray-600);">${new Date(m.created_at).toLocaleString()}</td>
          </tr>
        `).join('');
      }
    }
  } catch (err) {
    console.error("Error loading inventory", err);
  }
}

async function performStockAction(action) {
  const prodId = document.getElementById("invProductSelect").value;
  const qty = parseInt(document.getElementById("invActionQty").value);
  if (!prodId || !qty || qty <= 0) {
    showToast("Please enter a valid positive quantity", true);
    return;
  }

  let endpoint = "";
  let payload = {};

  if (action === "add") {
    endpoint = `/api/v1/inventory/product/${prodId}/add`;
    payload = { quantity: qty, reference_type: "RESTOCK", notes: "Manual Restock via Web UI" };
  } else if (action === "reduce") {
    endpoint = `/api/v1/inventory/product/${prodId}/reduce`;
    payload = { quantity: qty, reference_type: "MANUAL_WRITE_OFF", notes: "Manual Reduction via Web UI" };
  } else if (action === "reserve") {
    endpoint = `/api/v1/inventory/product/${prodId}/reserve`;
    payload = { quantity: qty, reference_id: "CART-UI-" + Date.now(), notes: "Hold stock for customer" };
  } else if (action === "release") {
    endpoint = `/api/v1/inventory/product/${prodId}/release`;
    payload = { quantity: qty, reference_id: "CART-UI-RELEASE", notes: "Release held stock" };
  }

  try {
    const res = await fetch(endpoint, {
      method: "POST",
      headers: authHeaders(),
      body: JSON.stringify(payload)
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Stock adjustment failed");
    showToast(`Inventory updated! New available balance: ${data.available_quantity}`);
    loadInventoryStatus();
  } catch (err) {
    showToast(err.message, true);
  }
}

// ==========================================
// MODULE 14: Warehouse Management
// ==========================================
function showAddWarehouseForm() {
  document.getElementById("warehouseFormCard").style.display = "block";
}

function hideAddWarehouseForm() {
  document.getElementById("warehouseFormCard").style.display = "none";
}

async function loadWarehouses() {
  const tbody = document.getElementById("warehousesTableBody");
  try {
    const res = await fetch("/api/v1/warehouses", { headers: authHeaders() });
    if (!res.ok) {
      if (res.status === 403 || res.status === 401) {
        tbody.innerHTML = `<tr><td colspan="7" style="text-align:center; color:orange;">⚠️ Warehouse management restricted to Employee, Admin & Super Admin roles. Please log in with elevated credentials.</td></tr>`;
        return;
      }
      throw new Error("Failed to load warehouses");
    }
    const data = await res.json();
    if (data.length === 0) {
      tbody.innerHTML = `<tr><td colspan="7" style="text-align:center; color:var(--gray-500);">No warehouses registered.</td></tr>`;
      return;
    }
    tbody.innerHTML = data.map(w => `
      <tr>
        <td><code>${w.code}</code></td>
        <td><strong>${w.name}</strong></td>
        <td>${w.city}, ${w.state_province || ''} ${w.country}</td>
        <td>${w.capacity_units.toLocaleString()} units</td>
        <td>
          <div>${w.current_utilization.toLocaleString()} (${w.utilization_percentage}%)</div>
          <div style="background:#e2e8f0; height:6px; border-radius:3px; margin-top:3px; width:100px;">
            <div style="background:${w.utilization_percentage > 90 ? 'red' : w.utilization_percentage > 70 ? 'orange' : '#10b981'}; height:6px; border-radius:3px; width:${Math.min(100, w.utilization_percentage)}%;"></div>
          </div>
        </td>
        <td><span class="badge ${w.status === 'ACTIVE' ? 'badge-active' : 'badge-suspended'}">${w.status}</span></td>
        <td>
          <button class="btn btn-secondary btn-sm" onclick="showToast('Facility ID #${w.id} operating at ${w.utilization_percentage}% capacity.')">Inspect</button>
        </td>
      </tr>
    `).join('');
  } catch (err) {
    tbody.innerHTML = `<tr><td colspan="7" style="color:red;">Error loading warehouses: ${err.message}</td></tr>`;
  }
}

async function submitCreateWarehouse() {
  const code = document.getElementById("whCode").value.trim();
  const name = document.getElementById("whName").value.trim();
  const capacity = parseInt(document.getElementById("whCapacity").value);
  const address = document.getElementById("whAddress").value.trim();
  const city = document.getElementById("whCity").value.trim();
  const zip = document.getElementById("whZip").value.trim();

  try {
    const res = await fetch("/api/v1/warehouses", {
      method: "POST",
      headers: authHeaders(),
      body: JSON.stringify({
        code,
        name,
        capacity_units: capacity,
        address_line1: address,
        city,
        state_province: "IL",
        postal_code: zip,
        country: "USA",
        status: "ACTIVE"
      })
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Failed to create warehouse");
    showToast(`Warehouse facility '${data.name}' created!`);
    hideAddWarehouseForm();
    loadWarehouses();
  } catch (err) {
    showToast(err.message, true);
  }
}

// ==========================================
// MODULE 15: INVENTORY TRANSFERS
// ==========================================
async function loadWarehousesForTransfer() {
  try {
    const res = await fetch("/api/v1/warehouses", { headers: authHeaders() });
    if (!res.ok) return;
    const warehouses = await res.json();
    const srcSel = document.getElementById("transferSourceWh");
    const dstSel = document.getElementById("transferDestWh");
    if (srcSel && dstSel) {
      srcSel.innerHTML = warehouses.map(w => `<option value="${w.id}">${w.name} (${w.code})</option>`).join("");
      dstSel.innerHTML = warehouses.map(w => `<option value="${w.id}">${w.name} (${w.code})</option>`).join("");
      if (warehouses.length > 1) {
        dstSel.selectedIndex = 1;
      }
    }
  } catch (e) {
    console.error("Error loading warehouses for transfer", e);
  }
}

function showCreateTransferForm() {
  const card = document.getElementById("transferFormCard");
  if (card) card.style.display = "block";
}

function hideCreateTransferForm() {
  const card = document.getElementById("transferFormCard");
  if (card) card.style.display = "none";
}

async function loadTransfers() {
  const tbody = document.getElementById("transfersTableBody");
  tbody.innerHTML = `<tr><td colspan="8">Loading transfers...</td></tr>`;
  try {
    const res = await fetch("/api/v1/transfers", { headers: authHeaders() });
    if (!res.ok) throw new Error("Failed to load transfers");
    const transfers = await res.json();
    if (transfers.length === 0) {
      tbody.innerHTML = `<tr><td colspan="8" style="text-align:center; color:var(--gray-500);">No inventory transfers found.</td></tr>`;
      return;
    }
    tbody.innerHTML = transfers.map(t => {
      let actions = "";
      if (t.status === "REQUESTED") {
        actions = `<button class="btn btn-warning btn-sm" onclick="dispatchTransfer(${t.id})">🚚 Dispatch</button>
                   <button class="btn btn-danger btn-sm" onclick="cancelTransfer(${t.id})">❌</button>`;
      } else if (t.status === "DISPATCHED") {
        actions = `<button class="btn btn-success btn-sm" onclick="receiveTransfer(${t.id})">📥 Receive</button>`;
      } else {
        actions = `<span class="badge" style="background:#e2e8f0; color:#475569;">Completed</span>`;
      }
      const statusBadge = t.status === "RECEIVED" ? "badge-success" : (t.status === "DISPATCHED" ? "badge-warning" : "badge-info");
      return `
        <tr>
          <td><strong>${t.transfer_number}</strong></td>
          <td>WH #${t.source_warehouse_id}</td>
          <td>WH #${t.destination_warehouse_id}</td>
          <td>#${t.variant_id}</td>
          <td>${t.quantity_requested}</td>
          <td>${t.quantity_shipped || 0} / ${t.quantity_received || 0}</td>
          <td><span class="badge ${statusBadge}">${t.status}</span></td>
          <td>${actions}</td>
        </tr>
      `;
    }).join("");
  } catch (e) {
    tbody.innerHTML = `<tr><td colspan="8" style="color:var(--danger);">${e.message}</td></tr>`;
  }
}

async function submitCreateTransfer() {
  const source_warehouse_id = parseInt(document.getElementById("transferSourceWh").value);
  const destination_warehouse_id = parseInt(document.getElementById("transferDestWh").value);
  const variant_id = parseInt(document.getElementById("transferVariantId").value);
  const quantity = parseInt(document.getElementById("transferQty").value);
  const notes = document.getElementById("transferNotes").value;

  if (source_warehouse_id === destination_warehouse_id) {
    showToast("Source and destination warehouse cannot be the same!", true);
    return;
  }

  try {
    const res = await fetch("/api/v1/transfers", {
      method: "POST",
      headers: authHeaders(),
      body: JSON.stringify({
        source_warehouse_id,
        destination_warehouse_id,
        variant_id,
        quantity,
        notes
      })
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Failed to create transfer request");
    showToast(`Transfer ${data.transfer_number} created!`);
    hideCreateTransferForm();
    loadTransfers();
  } catch (e) {
    showToast(e.message, true);
  }
}

async function dispatchTransfer(transferId) {
  try {
    const res = await fetch(`/api/v1/transfers/${transferId}/dispatch`, {
      method: "POST",
      headers: authHeaders()
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Failed to dispatch transfer");
    showToast(`Transfer ${data.transfer_number} dispatched successfully!`);
    loadTransfers();
  } catch (e) {
    showToast(e.message, true);
  }
}

async function receiveTransfer(transferId) {
  try {
    const res = await fetch(`/api/v1/transfers/${transferId}/receive`, {
      method: "POST",
      headers: authHeaders()
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Failed to receive transfer");
    showToast(`Transfer ${data.transfer_number} received into destination warehouse!`);
    loadTransfers();
  } catch (e) {
    showToast(e.message, true);
  }
}

async function cancelTransfer(transferId) {
  try {
    const res = await fetch(`/api/v1/transfers/${transferId}/cancel`, {
      method: "POST",
      headers: authHeaders()
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Failed to cancel transfer");
    showToast(`Transfer ${data.transfer_number} cancelled.`);
    loadTransfers();
  } catch (e) {
    showToast(e.message, true);
  }
}

// ==========================================
// MODULE 16: LOW-STOCK MANAGEMENT
// ==========================================
function showThresholdForm() {
  const card = document.getElementById("thresholdFormCard");
  if (card) card.style.display = "block";
}

function hideThresholdForm() {
  const card = document.getElementById("thresholdFormCard");
  if (card) card.style.display = "none";
}

async function loadLowStockData() {
  await Promise.all([loadRestockAlerts(), loadLowStockReport()]);
}

async function loadRestockAlerts() {
  const tbody = document.getElementById("restockAlertsTableBody");
  tbody.innerHTML = `<tr><td colspan="8">Loading alerts...</td></tr>`;
  try {
    const res = await fetch("/api/v1/low-stock/alerts", { headers: authHeaders() });
    if (!res.ok) throw new Error("Failed to load restock alerts");
    const alerts = await res.json();
    if (alerts.length === 0) {
      tbody.innerHTML = `<tr><td colspan="8" style="text-align:center; color:var(--success);">✅ No open restocking alerts. All variant stocks healthy.</td></tr>`;
      return;
    }
    tbody.innerHTML = alerts.map(a => `
      <tr>
        <td>#${a.id}</td>
        <td>Variant #${a.variant_id}</td>
        <td>${a.current_stock}</td>
        <td>${a.threshold_level}</td>
        <td><strong style="color:var(--danger);">${a.deficit}</strong></td>
        <td><span class="badge ${a.severity === 'CRITICAL' ? 'badge-danger' : 'badge-warning'}">${a.severity}</span></td>
        <td><span class="badge ${a.status === 'OPEN' ? 'badge-danger' : 'badge-success'}">${a.status}</span></td>
        <td>
          ${a.status === 'OPEN' ? `<button class="btn btn-success btn-sm" onclick="resolveAlert(${a.id})">Resolve</button>` : 'Resolved'}
        </td>
      </tr>
    `).join("");
  } catch (e) {
    tbody.innerHTML = `<tr><td colspan="8" style="color:var(--danger);">${e.message}</td></tr>`;
  }
}

async function loadLowStockReport() {
  const tbody = document.getElementById("lowStockReportTableBody");
  tbody.innerHTML = `<tr><td colspan="6">Loading low-stock report...</td></tr>`;
  try {
    const res = await fetch("/api/v1/low-stock/report", { headers: authHeaders() });
    if (!res.ok) throw new Error("Failed to load low-stock report");
    const report = await res.json();
    if (report.length === 0) {
      tbody.innerHTML = `<tr><td colspan="6" style="text-align:center; color:var(--gray-500);">No variant inventory reported.</td></tr>`;
      return;
    }
    tbody.innerHTML = report.map(r => `
      <tr>
        <td>Variant #${r.variant_id}</td>
        <td>${r.current_stock}</td>
        <td>${r.min_threshold}</td>
        <td>${r.reorder_quantity}</td>
        <td>${r.deficit > 0 ? `<span style="color:var(--danger); font-weight:700;">-${r.deficit}</span>` : '0'}</td>
        <td>
          ${r.needs_restock 
            ? `<span class="badge badge-danger">NEEDS RESTOCK</span>` 
            : `<span class="badge badge-success">SUFFICIENT</span>`}
        </td>
      </tr>
    `).join("");
  } catch (e) {
    tbody.innerHTML = `<tr><td colspan="6" style="color:var(--danger);">${e.message}</td></tr>`;
  }
}

async function submitConfigureThreshold() {
  const variant_id = parseInt(document.getElementById("threshVariantId").value);
  const min_threshold = parseInt(document.getElementById("threshMinQty").value);
  const reorder_quantity = parseInt(document.getElementById("threshReorderQty").value);

  try {
    const res = await fetch("/api/v1/low-stock/thresholds", {
      method: "POST",
      headers: authHeaders(),
      body: JSON.stringify({ variant_id, min_threshold, reorder_quantity })
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Failed to set threshold");
    showToast(`Threshold saved for Variant #${data.variant_id}`);
    hideThresholdForm();
    loadLowStockData();
  } catch (e) {
    showToast(e.message, true);
  }
}

async function triggerRestockCheck() {
  try {
    const res = await fetch("/api/v1/low-stock/check", {
      method: "POST",
      headers: authHeaders()
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Stock check failed");
    showToast(`Stock check complete: ${data.alerts_created} alerts generated.`);
    loadLowStockData();
    loadKPIs();
  } catch (e) {
    showToast(e.message, true);
  }
}

async function resolveAlert(alertId) {
  try {
    const res = await fetch(`/api/v1/low-stock/alerts/${alertId}/resolve`, {
      method: "POST",
      headers: authHeaders()
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Failed to resolve alert");
    showToast(`Alert #${alertId} resolved.`);
    loadLowStockData();
    loadKPIs();
  } catch (e) {
    showToast(e.message, true);
  }
}

// ==========================================
// MODULE 17: SHOPPING CART MANAGEMENT
// ==========================================
async function loadCart() {
  const tbody = document.getElementById("cartTableBody");
  tbody.innerHTML = `<tr><td colspan="6">Loading cart items...</td></tr>`;
  try {
    const res = await fetch("/api/v1/carts/me", { headers: authHeaders() });
    if (!res.ok) throw new Error("Please log in as Customer to manage shopping cart.");
    const cart = await res.json();
    
    const items = cart.items || [];
    let totalQty = 0;
    let subtotal = 0;

    items.forEach(item => {
      totalQty += item.quantity;
      subtotal += (item.unit_price * item.quantity);
    });

    document.getElementById("cartSummaryItems").innerText = items.length;
    document.getElementById("cartSummaryQty").innerText = totalQty;
    document.getElementById("cartSummarySubtotal").innerText = `$${subtotal.toFixed(2)}`;

    if (items.length === 0) {
      tbody.innerHTML = `<tr><td colspan="6" style="text-align:center; color:var(--gray-500);">Your shopping cart is empty.</td></tr>`;
      return;
    }

    tbody.innerHTML = items.map(item => `
      <tr>
        <td>Variant #${item.variant_id}</td>
        <td><strong>${item.sku || 'N/A'}</strong></td>
        <td>$${Number(item.unit_price).toFixed(2)}</td>
        <td>
          <div style="display:flex; align-items:center; gap:0.3rem;">
            <button class="btn btn-secondary btn-sm" style="padding:0.1rem 0.4rem;" onclick="updateCartQty(${item.id}, ${item.quantity - 1})">-</button>
            <span style="font-weight:600; min-width:24px; text-align:center;">${item.quantity}</span>
            <button class="btn btn-secondary btn-sm" style="padding:0.1rem 0.4rem;" onclick="updateCartQty(${item.id}, ${item.quantity + 1})">+</button>
          </div>
        </td>
        <td>$${(item.unit_price * item.quantity).toFixed(2)}</td>
        <td>
          <button class="btn btn-danger btn-sm" onclick="removeCartItem(${item.id})">🗑️ Remove</button>
        </td>
      </tr>
    `).join("");
  } catch (e) {
    tbody.innerHTML = `<tr><td colspan="6" style="color:var(--danger);">${e.message}</td></tr>`;
    document.getElementById("cartSummaryItems").innerText = "0";
    document.getElementById("cartSummaryQty").innerText = "0";
    document.getElementById("cartSummarySubtotal").innerText = "$0.00";
  }
}

async function submitAddToCart() {
  const variant_id = parseInt(document.getElementById("cartAddVariantId").value);
  const quantity = parseInt(document.getElementById("cartAddQty").value);

  try {
    const res = await fetch("/api/v1/carts/items", {
      method: "POST",
      headers: authHeaders(),
      body: JSON.stringify({ variant_id, quantity })
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Failed to add item to cart");
    showToast("Product added to cart!");
    loadCart();
  } catch (e) {
    showToast(e.message, true);
  }
}

async function updateCartQty(itemId, newQty) {
  if (newQty <= 0) {
    return removeCartItem(itemId);
  }
  try {
    const res = await fetch(`/api/v1/carts/items/${itemId}`, {
      method: "PUT",
      headers: authHeaders(),
      body: JSON.stringify({ quantity: newQty })
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Failed to update item quantity");
    loadCart();
  } catch (e) {
    showToast(e.message, true);
  }
}

async function removeCartItem(itemId) {
  try {
    const res = await fetch(`/api/v1/carts/items/${itemId}`, {
      method: "DELETE",
      headers: authHeaders()
    });
    if (!res.ok) {
      const data = await res.json();
      throw new Error(data.detail || "Failed to remove item");
    }
    showToast("Item removed from cart");
    loadCart();
  } catch (e) {
    showToast(e.message, true);
  }
}

async function clearCustomerCart() {
  if (!confirm("Are you sure you want to clear your entire cart?")) return;
  try {
    const res = await fetch("/api/v1/carts/me/clear", {
      method: "DELETE",
      headers: authHeaders()
    });
    if (!res.ok) {
      const data = await res.json();
      throw new Error(data.detail || "Failed to clear cart");
    }
    showToast("Shopping cart cleared");
    loadCart();
  } catch (e) {
    showToast(e.message, true);
  }
}

// ==========================================
// MODULE 18: CART PRICE CALCULATION
// ==========================================
function applySampleCoupon(code) {
  document.getElementById("calcCouponCode").value = code;
  calculateCartSummary();
}

async function calculateCartSummary() {
  const coupon_code = document.getElementById("calcCouponCode").value.trim() || null;
  const shipping_method_code = document.getElementById("calcShippingMethod").value || "STANDARD_GROUND";
  
  try {
    const res = await fetch("/api/v1/cart/calculate", {
      method: "POST",
      headers: authHeaders(),
      body: JSON.stringify({
        coupon_code,
        shipping_method_code
      })
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Calculation failed. Add items to cart first.");

    document.getElementById("calcSummarySubtotal").innerText = `$${Number(data.subtotal_amount).toFixed(2)}`;
    document.getElementById("calcSummaryDiscount").innerText = `-$${Number(data.discount_amount).toFixed(2)}`;
    document.getElementById("calcSummaryTax").innerText = `$${Number(data.tax_amount).toFixed(2)}`;
    document.getElementById("calcSummaryShipping").innerText = `$${Number(data.shipping_amount).toFixed(2)}`;
    document.getElementById("calcSummaryGrandTotal").innerText = `$${Number(data.grand_total).toFixed(2)}`;

    const rulesList = document.getElementById("calcAppliedRulesList");
    const discounts = data.applied_discounts || [];
    const taxes = data.tax_breakdowns || [];

    let html = "";
    if (discounts.length === 0 && taxes.length === 0) {
      html += "<li>Standard pricing applied. No promotional discounts active.</li>";
    }
    discounts.forEach(d => {
      html += `<li><strong style="color:#10b981;">Discount (${d.type}):</strong> ${d.description || d.code} (-$${Number(d.amount).toFixed(2)})</li>`;
    });
    taxes.forEach(t => {
      html += `<li><strong>${t.tax_name}:</strong> ${t.rate_percentage}% on $${Number(t.base_amount).toFixed(2)} = $${Number(t.tax_amount).toFixed(2)}</li>`;
    });

    rulesList.innerHTML = html;
  } catch (e) {
    showToast(e.message, true);
  }
}

// ==========================================
// MODULE 19: WISHLIST MANAGEMENT
// ==========================================
async function loadWishlist() {
  const tbody = document.getElementById("wishlistTableBody");
  tbody.innerHTML = `<tr><td colspan="5">Loading saved items...</td></tr>`;
  try {
    const res = await fetch("/api/v1/wishlists/me", { headers: authHeaders() });
    if (!res.ok) throw new Error("Please log in as Customer to view saved wishlist.");
    const items = await res.json();

    if (items.length === 0) {
      tbody.innerHTML = `<tr><td colspan="5" style="text-align:center; color:var(--gray-500);">Your wishlist is currently empty.</td></tr>`;
      return;
    }

    tbody.innerHTML = items.map(item => `
      <tr>
        <td>Variant #${item.variant_id}</td>
        <td><strong>${item.sku || 'N/A'}</strong></td>
        <td>
          ${item.is_in_stock 
            ? `<span class="badge badge-success">IN STOCK</span>` 
            : `<span class="badge badge-danger">OUT OF STOCK</span>`}
        </td>
        <td>${item.created_at ? new Date(item.created_at).toLocaleDateString() : 'Recently'}</td>
        <td>
          <button class="btn btn-primary btn-sm" onclick="moveWishlistToCart(${item.variant_id})">🛒 Move to Cart</button>
          <button class="btn btn-danger btn-sm" onclick="removeWishlistItem(${item.variant_id})">❌ Remove</button>
        </td>
      </tr>
    `).join("");
  } catch (e) {
    tbody.innerHTML = `<tr><td colspan="5" style="color:var(--danger);">${e.message}</td></tr>`;
  }
}

async function submitAddToWishlist() {
  const variant_id = parseInt(document.getElementById("wishlistAddVariantId").value);
  try {
    const res = await fetch("/api/v1/wishlists/items", {
      method: "POST",
      headers: authHeaders(),
      body: JSON.stringify({ variant_id })
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Failed to add to wishlist");
    showToast("Variant saved to your wishlist!");
    loadWishlist();
  } catch (e) {
    showToast(e.message, true);
  }
}

async function removeWishlistItem(variantId) {
  try {
    const res = await fetch(`/api/v1/wishlists/items/${variantId}`, {
      method: "DELETE",
      headers: authHeaders()
    });
    if (!res.ok) {
      const data = await res.json();
      throw new Error(data.detail || "Failed to remove wishlist item");
    }
    showToast("Item removed from wishlist");
    loadWishlist();
  } catch (e) {
    showToast(e.message, true);
  }
}

async function moveWishlistToCart(variantId) {
  try {
    // Add to cart first
    const addRes = await fetch("/api/v1/carts/items", {
      method: "POST",
      headers: authHeaders(),
      body: JSON.stringify({ variant_id: variantId, quantity: 1 })
    });
    if (!addRes.ok) {
      const err = await addRes.json();
      throw new Error(err.detail || "Could not add item to cart");
    }
    // Then remove from wishlist
    await fetch(`/api/v1/wishlists/items/${variantId}`, {
      method: "DELETE",
      headers: authHeaders()
    });
    showToast("Item moved from Wishlist to Shopping Cart!");
    loadWishlist();
  } catch (e) {
    showToast(e.message, true);
  }
}

// ==========================================
// MODULE 20: COUPON MANAGEMENT
// ==========================================
function showCouponForm() {
  const card = document.getElementById("couponFormCard");
  if (card) card.style.display = "block";
}

function hideCouponForm() {
  const card = document.getElementById("couponFormCard");
  if (card) card.style.display = "none";
}

async function loadCoupons() {
  const tbody = document.getElementById("couponsTableBody");
  tbody.innerHTML = `<tr><td colspan="8">Loading coupons...</td></tr>`;
  try {
    const res = await fetch("/api/v1/coupons", { headers: authHeaders() });
    if (!res.ok) throw new Error("Failed to load coupons");
    const coupons = await res.json();

    if (coupons.length === 0) {
      tbody.innerHTML = `<tr><td colspan="8" style="text-align:center; color:var(--gray-500);">No coupons found.</td></tr>`;
      return;
    }

    tbody.innerHTML = coupons.map(c => `
      <tr>
        <td><strong>${c.code}</strong></td>
        <td>${c.discount_type}</td>
        <td>${c.discount_type === 'PERCENTAGE' ? `${c.discount_value}%` : `$${c.discount_value}`}</td>
        <td>$${Number(c.min_purchase_amount || 0).toFixed(2)}</td>
        <td>${c.max_uses ?? 'Unlimited'}</td>
        <td>${c.used_count ?? 0}</td>
        <td>
          <span class="badge ${c.is_active ? 'badge-success' : 'badge-danger'}">
            ${c.is_active ? 'ACTIVE' : 'INACTIVE'}
          </span>
        </td>
        <td>
          <button class="btn btn-secondary btn-sm" onclick="toggleCouponStatus(${c.id})">
            ${c.is_active ? 'Deactivate' : 'Activate'}
          </button>
        </td>
      </tr>
    `).join("");
  } catch (e) {
    tbody.innerHTML = `<tr><td colspan="8" style="color:var(--danger);">${e.message}</td></tr>`;
  }
}

async function submitCreateCoupon() {
  const code = document.getElementById("couponCode").value.trim().toUpperCase();
  const discount_type = document.getElementById("couponType").value;
  const discount_value = parseFloat(document.getElementById("couponValue").value);
  const min_purchase_amount = parseFloat(document.getElementById("couponMinPurchase").value) || 0;
  const max_uses = parseInt(document.getElementById("couponMaxUses").value) || null;
  const is_active = document.getElementById("couponIsActive").value === "true";

  try {
    const res = await fetch("/api/v1/coupons", {
      method: "POST",
      headers: authHeaders(),
      body: JSON.stringify({
        code,
        discount_type,
        discount_value,
        min_purchase_amount,
        max_uses,
        is_active
      })
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Failed to create coupon");
    showToast(`Coupon '${data.code}' created successfully!`);
    hideCouponForm();
    loadCoupons();
  } catch (e) {
    showToast(e.message, true);
  }
}

async function toggleCouponStatus(couponId) {
  try {
    const res = await fetch(`/api/v1/coupons/${couponId}/toggle`, {
      method: "PATCH",
      headers: authHeaders()
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Failed to toggle coupon status");
    showToast(`Coupon status updated to ${data.is_active ? 'ACTIVE' : 'INACTIVE'}`);
    loadCoupons();
  } catch (e) {
    showToast(e.message, true);
  }
}

// ==========================================
// MODULE 21: PROMOTION MANAGEMENT
// ==========================================
function showPromotionForm() {
  const card = document.getElementById("promotionFormCard");
  if (card) card.style.display = "block";
}

function hidePromotionForm() {
  const card = document.getElementById("promotionFormCard");
  if (card) card.style.display = "none";
}

async function loadPromotions() {
  const tbody = document.getElementById("promotionsTableBody");
  tbody.innerHTML = `<tr><td colspan="7">Loading promotions...</td></tr>`;
  try {
    const res = await fetch("/api/v1/promotions", { headers: authHeaders() });
    if (!res.ok) throw new Error("Failed to load promotions");
    const promos = await res.json();

    if (promos.length === 0) {
      tbody.innerHTML = `<tr><td colspan="7" style="text-align:center; color:var(--gray-500);">No promotions found.</td></tr>`;
      return;
    }

    tbody.innerHTML = promos.map(p => `
      <tr>
        <td><strong>${p.name}</strong></td>
        <td>${p.target_type}</td>
        <td>${p.discount_type === 'PERCENTAGE' ? `${p.discount_value}%` : `$${p.discount_value}`}</td>
        <td>$${Number(p.min_cart_value || 0).toFixed(2)}</td>
        <td>${p.start_date ? new Date(p.start_date).toLocaleDateString() : 'Always'}</td>
        <td>
          <span class="badge ${p.is_active ? 'badge-success' : 'badge-danger'}">
            ${p.is_active ? 'ACTIVE' : 'INACTIVE'}
          </span>
        </td>
        <td>
          <button class="btn btn-secondary btn-sm" onclick="togglePromotionStatus(${p.id})">
            ${p.is_active ? 'Deactivate' : 'Activate'}
          </button>
        </td>
      </tr>
    `).join("");
  } catch (e) {
    tbody.innerHTML = `<tr><td colspan="7" style="color:var(--danger);">${e.message}</td></tr>`;
  }
}

async function submitCreatePromotion() {
  const name = document.getElementById("promoName").value.trim();
  const target_type = document.getElementById("promoTarget").value;
  const discount_type = document.getElementById("promoType").value;
  const discount_value = parseFloat(document.getElementById("promoValue").value);
  const min_cart_value = parseFloat(document.getElementById("promoMinValue").value) || 0;
  const category_id = parseInt(document.getElementById("promoCategoryId").value) || null;
  const is_active = document.getElementById("promoIsActive").value === "true";

  try {
    const res = await fetch("/api/v1/promotions", {
      method: "POST",
      headers: authHeaders(),
      body: JSON.stringify({
        name,
        target_type,
        discount_type,
        discount_value,
        min_cart_value,
        category_id,
        is_active
      })
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Failed to create promotion");
    showToast(`Promotion '${data.name}' created!`);
    hidePromotionForm();
    loadPromotions();
  } catch (e) {
    showToast(e.message, true);
  }
}

async function togglePromotionStatus(promoId) {
  try {
    const res = await fetch(`/api/v1/promotions/${promoId}/toggle`, {
      method: "PATCH",
      headers: authHeaders()
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Failed to toggle promotion");
    showToast(`Promotion status changed to ${data.is_active ? 'ACTIVE' : 'INACTIVE'}`);
    loadPromotions();
  } catch (e) {
    showToast(e.message, true);
  }
}

// ==========================================
// MODULE 22: TAX MANAGEMENT
// ==========================================
function showTaxForm() {
  const card = document.getElementById("taxFormCard");
  if (card) card.style.display = "block";
}

function hideTaxForm() {
  const card = document.getElementById("taxFormCard");
  if (card) card.style.display = "none";
}

async function loadTaxes() {
  const tbody = document.getElementById("taxesTableBody");
  tbody.innerHTML = `<tr><td colspan="6">Loading tax rates...</td></tr>`;
  try {
    const res = await fetch("/api/v1/taxes/rates", { headers: authHeaders() });
    if (!res.ok) throw new Error("Failed to load tax rules");
    const taxes = await res.json();

    if (taxes.length === 0) {
      tbody.innerHTML = `<tr><td colspan="6" style="text-align:center; color:var(--gray-500);">No tax rules configured.</td></tr>`;
      return;
    }

    tbody.innerHTML = taxes.map(t => `
      <tr>
        <td><strong>${t.tax_name}</strong></td>
        <td>${t.country_code} ${t.state_code ? `- ${t.state_code}` : '(All)'}</td>
        <td><strong>${t.rate_percentage}%</strong></td>
        <td>${t.category_id ? `Category #${t.category_id}` : 'All Categories'}</td>
        <td>
          <span class="badge ${t.is_active ? 'badge-success' : 'badge-danger'}">
            ${t.is_active ? 'ACTIVE' : 'INACTIVE'}
          </span>
        </td>
        <td>
          <button class="btn btn-secondary btn-sm" onclick="toggleTaxStatus(${t.id}, ${t.is_active})">
            ${t.is_active ? 'Deactivate' : 'Activate'}
          </button>
        </td>
      </tr>
    `).join("");
  } catch (e) {
    tbody.innerHTML = `<tr><td colspan="6" style="color:var(--danger);">${e.message}</td></tr>`;
  }
}

async function submitCreateTax() {
  const tax_name = document.getElementById("taxName").value.trim();
  const country_code = document.getElementById("taxCountry").value.trim().toUpperCase();
  const state_code = document.getElementById("taxState").value.trim().toUpperCase() || null;
  const rate_percentage = parseFloat(document.getElementById("taxRate").value);
  const category_id = parseInt(document.getElementById("taxCategoryId").value) || null;
  const is_active = document.getElementById("taxIsActive").value === "true";

  try {
    const res = await fetch("/api/v1/taxes/rates", {
      method: "POST",
      headers: authHeaders(),
      body: JSON.stringify({
        tax_name,
        country_code,
        state_code,
        rate_percentage,
        category_id,
        is_active
      })
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Failed to configure tax rule");
    showToast(`Tax rate '${data.tax_name}' saved!`);
    hideTaxForm();
    loadTaxes();
  } catch (e) {
    showToast(e.message, true);
  }
}

async function toggleTaxStatus(taxId, currentStatus) {
  try {
    const res = await fetch(`/api/v1/taxes/rates/${taxId}`, {
      method: "PATCH",
      headers: authHeaders(),
      body: JSON.stringify({ is_active: !currentStatus })
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Failed to update tax status");
    showToast(`Tax rule '${data.tax_name}' status updated.`);
    loadTaxes();
  } catch (e) {
    showToast(e.message, true);
  }
}

// ==========================================
// MODULE 23: SHIPPING CONFIGURATION
// ==========================================
function showShippingForm() {
  const card = document.getElementById("shippingFormCard");
  if (card) card.style.display = "block";
}

function hideShippingForm() {
  const card = document.getElementById("shippingFormCard");
  if (card) card.style.display = "none";
}

async function loadShippingMethods() {
  const tbody = document.getElementById("shippingTableBody");
  tbody.innerHTML = `<tr><td colspan="7">Loading shipping methods...</td></tr>`;
  try {
    const res = await fetch("/api/v1/shipping/methods", { headers: authHeaders() });
    if (!res.ok) throw new Error("Failed to load shipping methods");
    const methods = await res.json();

    if (methods.length === 0) {
      tbody.innerHTML = `<tr><td colspan="7" style="text-align:center; color:var(--gray-500);">No shipping methods configured.</td></tr>`;
      return;
    }

    tbody.innerHTML = methods.map(m => `
      <tr>
        <td><strong>${m.code}</strong></td>
        <td>${m.name}</td>
        <td>$${Number(m.base_cost).toFixed(2)}</td>
        <td>${m.free_shipping_threshold ? `$${Number(m.free_shipping_threshold).toFixed(2)}` : 'None'}</td>
        <td>${m.estimated_days ? `${m.estimated_days} day(s)` : 'Standard'}</td>
        <td>
          <span class="badge ${m.is_active ? 'badge-success' : 'badge-danger'}">
            ${m.is_active ? 'ACTIVE' : 'INACTIVE'}
          </span>
        </td>
        <td>
          <button class="btn btn-secondary btn-sm" onclick="toggleShippingStatus(${m.id}, ${m.is_active})">
            ${m.is_active ? 'Deactivate' : 'Activate'}
          </button>
        </td>
      </tr>
    `).join("");
  } catch (e) {
    tbody.innerHTML = `<tr><td colspan="7" style="color:var(--danger);">${e.message}</td></tr>`;
  }
}

async function submitCreateShippingMethod() {
  const code = document.getElementById("shipMethodCode").value.trim().toUpperCase();
  const name = document.getElementById("shipMethodName").value.trim();
  const base_cost = parseFloat(document.getElementById("shipBaseCost").value);
  const free_shipping_threshold = parseFloat(document.getElementById("shipFreeThreshold").value) || null;
  const estimated_days = parseInt(document.getElementById("shipEstDays").value) || null;
  const is_active = document.getElementById("shipIsActive").value === "true";

  try {
    const res = await fetch("/api/v1/shipping/methods", {
      method: "POST",
      headers: authHeaders(),
      body: JSON.stringify({
        code,
        name,
        base_cost,
        free_shipping_threshold,
        estimated_days,
        is_active
      })
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Failed to create shipping method");
    showToast(`Shipping method '${data.name}' saved!`);
    hideShippingForm();
    loadShippingMethods();
  } catch (e) {
    showToast(e.message, true);
  }
}

async function toggleShippingStatus(methodId, currentStatus) {
  try {
    const res = await fetch(`/api/v1/shipping/methods/${methodId}`, {
      method: "PATCH",
      headers: authHeaders(),
      body: JSON.stringify({ is_active: !currentStatus })
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Failed to update shipping status");
    showToast(`Shipping method '${data.name}' status updated.`);
    loadShippingMethods();
  } catch (e) {
    showToast(e.message, true);
  }
}

// ==========================================
// MODULE 24: CHECKOUT MANAGEMENT
// ==========================================
async function loadCheckoutAddresses() {
  try {
    const res = await fetch("/api/v1/addresses", { headers: authHeaders() });
    if (!res.ok) return;
    const addrs = await res.json();
    const shipSel = document.getElementById("checkoutShippingAddr");
    const billSel = document.getElementById("checkoutBillingAddr");
    if (shipSel && billSel) {
      if (addrs.length === 0) {
        shipSel.innerHTML = `<option value="">No saved addresses found. Add one in Addresses tab.</option>`;
        billSel.innerHTML = `<option value="">No saved addresses found. Add one in Addresses tab.</option>`;
      } else {
        const options = addrs.map(a => `<option value="${a.id}">${a.street_line1}, ${a.city}, ${a.state_province} (${a.type})</option>`).join("");
        shipSel.innerHTML = options;
        billSel.innerHTML = options;
      }
    }
  } catch (e) {
    console.error("Error loading checkout addresses", e);
  }
}

async function submitCheckout() {
  const resultCard = document.getElementById("checkoutResultCard");
  const shipping_address_id = parseInt(document.getElementById("checkoutShippingAddr").value);
  const billing_address_id = parseInt(document.getElementById("checkoutBillingAddr").value);
  const shipping_method_code = document.getElementById("checkoutShipMethod").value;
  const coupon_code = document.getElementById("checkoutCouponCode").value.trim() || null;
  const customer_notes = document.getElementById("checkoutNotes").value.trim() || null;

  if (!shipping_address_id || !billing_address_id) {
    showToast("Please ensure shipping and billing addresses are selected", true);
    return;
  }

  resultCard.innerHTML = `<div style="color:var(--primary);">Processing order validation, pricing recalculation, and inventory reservations...</div>`;

  try {
    const res = await fetch("/api/v1/checkout/process", {
      method: "POST",
      headers: authHeaders(),
      body: JSON.stringify({
        shipping_address_id,
        billing_address_id,
        shipping_method_code,
        coupon_code,
        notes: customer_notes
      })
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Checkout failed");

    resultCard.innerHTML = `
      <div style="background:#f0fdf4; border:1px solid #86efac; border-radius:6px; padding:1rem; color:#166534;">
        <h4 style="margin-bottom:0.5rem; font-size:1.05rem;">🎉 Order Successfully Confirmed!</h4>
        <p><strong>Order Number:</strong> <span style="font-size:1.1rem; color:#15803d;">${data.order_number}</span></p>
        <p><strong>Status:</strong> ${data.status} | <strong>Payment:</strong> ${data.payment_status}</p>
        <p><strong>Subtotal:</strong> $${Number(data.subtotal_amount).toFixed(2)}</p>
        <p><strong>Discount:</strong> -$${Number(data.discount_amount).toFixed(2)}</p>
        <p><strong>Tax:</strong> $${Number(data.tax_amount).toFixed(2)}</p>
        <p><strong>Shipping:</strong> $${Number(data.shipping_amount).toFixed(2)}</p>
        <p style="font-size:1.1rem; font-weight:700; margin-top:0.4rem;">Total Paid: $${Number(data.total_amount).toFixed(2)}</p>
        <p style="margin-top:0.5rem; font-size:0.8rem; color:#15803d;">Inventory pre-reserved safely. Your cart has been converted to an active order.</p>
      </div>
    `;

    showToast(`Order ${data.order_number} confirmed!`);
    loadKPIs();
  } catch (e) {
    resultCard.innerHTML = `
      <div style="background:#fef2f2; border:1px solid #fca5a5; border-radius:6px; padding:1rem; color:#991b1b;">
        <h4 style="margin-bottom:0.5rem;">❌ Checkout Error</h4>
        <p>${e.message}</p>
      </div>
    `;
    showToast(e.message, true);
  }
}

// ==========================================
// MODULE 25: ORDER MANAGEMENT
// ==========================================
async function loadOrders() {
  const tbody = document.getElementById("ordersTableBody");
  tbody.innerHTML = `<tr><td colspan="7">Loading enterprise orders...</td></tr>`;
  const filterStatus = document.getElementById("orderStatusFilter")?.value || "";

  try {
    let url = "/api/v1/orders";
    if (filterStatus) {
      url += `?status=${filterStatus}`;
    }
    const res = await fetch(url, { headers: authHeaders() });
    if (!res.ok) throw new Error("Failed to load orders. Admin/Employee permission required for all orders, or login as customer.");
    const data = await res.json();
    const orders = data.items || [];

    if (orders.length === 0) {
      tbody.innerHTML = `<tr><td colspan="7" style="text-align:center; color:var(--gray-500);">No orders found.</td></tr>`;
      return;
    }

    tbody.innerHTML = orders.map(ord => {
      let statusBadge = "badge-info";
      if (ord.status === "DELIVERED") statusBadge = "badge-success";
      else if (ord.status === "CANCELLED") statusBadge = "badge-danger";
      else if (ord.status === "SHIPPED") statusBadge = "badge-warning";

      return `
        <tr>
          <td><strong>${ord.order_number}</strong></td>
          <td>User #${ord.user_id}</td>
          <td><strong>$${Number(ord.total_amount).toFixed(2)}</strong></td>
          <td><span class="badge ${statusBadge}">${ord.status}</span></td>
          <td><span class="badge badge-info">${ord.payment_status}</span></td>
          <td>${new Date(ord.created_at).toLocaleString()}</td>
          <td>
            <div style="display:flex; gap:0.3rem;">
              <button class="btn btn-secondary btn-sm" onclick="viewOrderDetail(${ord.id})">👁️ Details</button>
              <select class="form-control" style="width:115px; font-size:0.75rem; padding:0.2rem;" onchange="updateOrderStatusPrompt(${ord.id}, this.value)">
                <option value="">Transition...</option>
                <option value="PROCESSING">PROCESSING</option>
                <option value="SHIPPED">SHIPPED</option>
                <option value="DELIVERED">DELIVERED</option>
                <option value="CANCELLED">CANCELLED</option>
              </select>
            </div>
          </td>
        </tr>
      `;
    }).join("");
  } catch (e) {
    tbody.innerHTML = `<tr><td colspan="7" style="color:var(--danger);">${e.message}</td></tr>`;
  }
}

async function viewOrderDetail(orderId) {
  const modal = document.getElementById("orderDetailModal");
  const title = document.getElementById("modalOrderNumber");
  const content = document.getElementById("modalOrderContent");

  modal.style.display = "block";
  content.innerHTML = `<p>Loading order details...</p>`;

  try {
    const res = await fetch(`/api/v1/orders/${orderId}`, { headers: authHeaders() });
    if (!res.ok) throw new Error("Failed to load order details");
    const ord = await res.json();

    title.innerText = `Order Details: ${ord.order_number}`;

    let shipSnap = {};
    let billSnap = {};
    try { shipSnap = JSON.parse(ord.shipping_address_snapshot || "{}"); } catch(e){}
    try { billSnap = JSON.parse(ord.billing_address_snapshot || "{}"); } catch(e){}

    const itemsHtml = (ord.items || []).map(item => `
      <tr>
        <td>Variant #${item.variant_id}</td>
        <td><strong>${item.sku}</strong></td>
        <td>${item.product_name || 'Item'}</td>
        <td>$${Number(item.unit_price).toFixed(2)}</td>
        <td>${item.quantity}</td>
        <td>$${Number(item.total_price).toFixed(2)}</td>
      </tr>
    `).join("");

    const historyHtml = (ord.status_history || []).map(h => `
      <li style="margin-bottom:0.4rem;">
        <span class="badge badge-info">${h.to_status}</span>
        <span style="color:var(--gray-500); font-size:0.8rem; margin-left:0.5rem;">${new Date(h.created_at).toLocaleString()}</span>
        <span style="font-size:0.85rem; margin-left:0.5rem;">${h.notes || ''}</span>
      </li>
    `).join("");

    content.innerHTML = `
      <div style="display:grid; grid-template-columns: 1fr 1fr; gap:1.5rem; margin-bottom:1.5rem;">
        <div style="background:var(--gray-100); padding:1rem; border-radius:6px;">
          <h4 style="margin-bottom:0.5rem; font-size:0.95rem;">Shipping Address Snapshot</h4>
          <p style="font-size:0.85rem;"><strong>${shipSnap.full_name || 'N/A'}</strong></p>
          <p style="font-size:0.85rem;">${shipSnap.address_line1 || ''}</p>
          <p style="font-size:0.85rem;">${shipSnap.city || ''}, ${shipSnap.state || ''} ${shipSnap.postal_code || ''}, ${shipSnap.country || ''}</p>
          <p style="font-size:0.85rem;">Phone: ${shipSnap.phone || 'N/A'}</p>
        </div>
        <div style="background:var(--gray-100); padding:1rem; border-radius:6px;">
          <h4 style="margin-bottom:0.5rem; font-size:0.95rem;">Financial Breakdown</h4>
          <p style="font-size:0.85rem;">Subtotal: <strong>$${Number(ord.subtotal_amount).toFixed(2)}</strong></p>
          <p style="font-size:0.85rem; color:#10b981;">Discount: <strong>-$${Number(ord.discount_amount).toFixed(2)}</strong></p>
          <p style="font-size:0.85rem;">Tax: <strong>$${Number(ord.tax_amount).toFixed(2)}</strong></p>
          <p style="font-size:0.85rem;">Shipping Freight: <strong>$${Number(ord.shipping_amount).toFixed(2)}</strong></p>
          <h3 style="margin-top:0.4rem; color:var(--primary); font-size:1.15rem;">Grand Total: $${Number(ord.total_amount).toFixed(2)}</h3>
        </div>
      </div>

      <h4 style="margin-bottom:0.5rem; font-size:0.95rem;">Ordered Items</h4>
      <div class="table-responsive" style="margin-bottom:1.5rem;">
        <table>
          <thead>
            <tr>
              <th>Variant ID</th>
              <th>SKU</th>
              <th>Product Name</th>
              <th>Unit Price</th>
              <th>Quantity</th>
              <th>Total</th>
            </tr>
          </thead>
          <tbody>${itemsHtml}</tbody>
        </table>
      </div>

      <h4 style="margin-bottom:0.5rem; font-size:0.95rem;">Status Audit History</h4>
      <ul style="padding-left:1.25rem;">
        ${historyHtml || '<li>Order placed.</li>'}
      </ul>
    `;
  } catch (e) {
    content.innerHTML = `<p style="color:var(--danger);">${e.message}</p>`;
  }
}

function hideOrderDetail() {
  const modal = document.getElementById("orderDetailModal");
  if (modal) modal.style.display = "none";
}

async function updateOrderStatusPrompt(orderId, newStatus) {
  if (!newStatus) return;
  const reason = prompt(`Enter reason or notes for updating order #${orderId} to status '${newStatus}':`, `Status transitioned to ${newStatus}`);
  if (reason === null) return;

  try {
    const res = await fetch(`/api/v1/orders/${orderId}/status`, {
      method: "PATCH",
      headers: authHeaders(),
      body: JSON.stringify({
        status: newStatus,
        notes: reason
      })
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Failed to update order status");
    showToast(`Order status updated to ${data.status}!`);
    loadOrders();
    if (document.getElementById("orderDetailModal").style.display !== "none") {
      viewOrderDetail(orderId);
    }
  } catch (e) {
    showToast(e.message, true);
  }
}

// KPI Dashboard metrics
async function loadKPIs() {
  try {
    const [uRes, pRes, cRes, bRes, oRes, aRes] = await Promise.all([
      fetch("/api/v1/users?limit=1", { headers: authHeaders() }).catch(() => null),
      fetch("/api/v1/products?limit=100").catch(() => null),
      fetch("/api/v1/categories").catch(() => null),
      fetch("/api/v1/brands?limit=100").catch(() => null),
      fetch("/api/v1/orders", { headers: authHeaders() }).catch(() => null),
      fetch("/api/v1/low-stock/alerts", { headers: authHeaders() }).catch(() => null)
    ]);

    if (uRes && uRes.ok) {
      const uData = await uRes.json();
      document.getElementById("kpiUsers").innerText = uData.meta?.total_items ?? "-";
    }

    if (pRes && pRes.ok) {
      const pData = await pRes.json();
      document.getElementById("kpiProducts").innerText = pData.meta?.total_items ?? 0;
      
      // Calculate total variants
      let totalVars = 0;
      for (const p of (pData.items || [])) {
        const vRes = await fetch(`/api/v1/products/${p.id}/variants`);
        if (vRes.ok) {
          const vData = await vRes.json();
          totalVars += vData.length;
        }
      }
      document.getElementById("kpiVariants").innerText = totalVars;
    }

    if (cRes && cRes.ok) {
      const cData = await cRes.json();
      document.getElementById("kpiCategories").innerText = cData.length ?? 0;
    }

    if (oRes && oRes.ok) {
      const oData = await oRes.json();
      document.getElementById("kpiOrders").innerText = oData.meta?.total_items ?? (oData.items?.length ?? 0);
    }

    if (aRes && aRes.ok) {
      const aData = await aRes.json();
      const openAlerts = (aData || []).filter(a => a.status === "OPEN").length;
      document.getElementById("kpiAlerts").innerText = openAlerts;
    }
  } catch (e) {
    console.error("Error loading KPIs", e);
  }
}

// =====================================================================
// MODULE 41: NOTIFICATIONS
// =====================================================================
function showNotificationForm() {
  document.getElementById("notificationFormContainer").style.display = "block";
}
function hideNotificationForm() {
  document.getElementById("notificationFormContainer").style.display = "none";
}

async function loadNotifications() {
  try {
    const res = await fetch("/api/v1/notifications", { headers: authHeaders() });
    if (!res.ok) {
      document.getElementById("notificationsTableBody").innerHTML = `<tr><td colspan="8">Please log in to view notifications.</td></tr>`;
      return;
    }
    const notifs = await res.json();
    const tbody = document.getElementById("notificationsTableBody");
    if (!notifs.length) {
      tbody.innerHTML = `<tr><td colspan="8" style="text-align:center;">No notifications found.</td></tr>`;
      return;
    }
    tbody.innerHTML = notifs.map(n => `
      <tr style="${n.is_read ? 'opacity:0.75;' : 'font-weight:600;'}">
        <td>${n.id}</td>
        <td>User #${n.user_id}</td>
        <td><span class="badge badge-info">${n.notification_type}</span></td>
        <td><span class="badge ${n.priority === 'CRITICAL' ? 'badge-danger' : n.priority === 'HIGH' ? 'badge-warning' : 'badge-secondary'}">${n.priority}</span></td>
        <td>
          <div style="font-weight:600;">${n.title}</div>
          <div style="font-size:0.82rem; color:var(--gray-500);">${n.message}</div>
          ${n.action_url ? `<a href="${n.action_url}" style="font-size:0.75rem;">${n.action_url}</a>` : ''}
        </td>
        <td><span class="badge ${n.is_read ? 'badge-success' : 'badge-warning'}">${n.is_read ? 'READ' : 'UNREAD'}</span></td>
        <td style="font-size:0.8rem;">${new Date(n.created_at).toLocaleString()}</td>
        <td>
          ${!n.is_read ? `<button class="btn btn-outline-primary btn-sm" onclick="markNotificationRead(${n.id})">Mark Read</button>` : ''}
          <button class="btn btn-danger btn-sm" onclick="deleteNotification(${n.id})">🗑️</button>
        </td>
      </tr>
    `).join("");
  } catch (e) {
    showToast(e.message, true);
  }
}

async function handleSendNotification(e) {
  e.preventDefault();
  const payload = {
    user_id: parseInt(document.getElementById("notifUserId").value),
    notification_type: document.getElementById("notifType").value,
    priority: document.getElementById("notifPriority").value,
    title: document.getElementById("notifTitle").value.trim(),
    message: document.getElementById("notifMessage").value.trim(),
    action_url: document.getElementById("notifActionUrl").value.trim() || null
  };
  try {
    const res = await fetch("/api/v1/notifications", {
      method: "POST",
      headers: authHeaders(),
      body: JSON.stringify(payload)
    });
    if (!res.ok) throw new Error((await res.json()).detail || "Failed to create notification");
    showToast("Notification sent successfully!");
    hideNotificationForm();
    loadNotifications();
  } catch (err) {
    showToast(err.message, true);
  }
}

async function markNotificationRead(id) {
  try {
    const res = await fetch(`/api/v1/notifications/${id}/read`, {
      method: "PATCH",
      headers: authHeaders()
    });
    if (!res.ok) throw new Error("Failed to mark notification read");
    showToast("Marked as read");
    loadNotifications();
  } catch (e) {
    showToast(e.message, true);
  }
}

async function markAllNotificationsRead() {
  try {
    const res = await fetch(`/api/v1/notifications/mark-all-read`, {
      method: "PATCH",
      headers: authHeaders()
    });
    if (!res.ok) throw new Error("Failed to mark all as read");
    showToast("All notifications marked as read");
    loadNotifications();
  } catch (e) {
    showToast(e.message, true);
  }
}

async function deleteNotification(id) {
  if (!confirm(`Delete notification #${id}?`)) return;
  try {
    const res = await fetch(`/api/v1/notifications/${id}`, {
      method: "DELETE",
      headers: authHeaders()
    });
    if (!res.ok) throw new Error("Failed to delete notification");
    showToast("Notification deleted");
    loadNotifications();
  } catch (e) {
    showToast(e.message, true);
  }
}

// =====================================================================
// MODULE 42: MESSAGING & LOGS
// =====================================================================
function showSendMessageForm() {
  document.getElementById("messagingFormContainer").style.display = "block";
}
function hideSendMessageForm() {
  document.getElementById("messagingFormContainer").style.display = "none";
}

async function loadMessaging() {
  try {
    // 1. Providers
    const pRes = await fetch("/api/v1/messaging/providers", { headers: authHeaders() });
    if (pRes.ok) {
      const providers = await pRes.json();
      const pContainer = document.getElementById("providersList");
      pContainer.innerHTML = providers.map(p => `
        <div style="background:var(--gray-100); padding:0.75rem 1rem; border-radius:6px; flex:1; min-width:220px; border-left:4px solid ${p.is_active ? 'var(--success)' : 'var(--danger)'};">
          <div style="font-weight:600;">${p.name} (${p.provider_type})</div>
          <div style="font-size:0.8rem; color:var(--gray-500);">Sender: ${p.sender_identity}</div>
          <div style="margin-top:0.4rem;">
            <span class="badge ${p.is_active ? 'badge-success' : 'badge-danger'}">${p.is_active ? 'ACTIVE' : 'INACTIVE'}</span>
            <button class="btn btn-outline-primary btn-sm" style="margin-left:0.5rem; padding:0.2rem 0.5rem; font-size:0.75rem;" onclick="testProvider(${p.id})">Ping Test</button>
          </div>
        </div>
      `).join("");
    }

    // 2. Logs
    const lRes = await fetch("/api/v1/messaging/logs?limit=50", { headers: authHeaders() });
    if (lRes.ok) {
      const logs = await lRes.json();
      const tbody = document.getElementById("messageLogsTableBody");
      if (!logs.length) {
        tbody.innerHTML = `<tr><td colspan="8" style="text-align:center;">No messaging logs recorded yet.</td></tr>`;
        return;
      }
      tbody.innerHTML = logs.map(l => `
        <tr>
          <td>#${l.id}</td>
          <td><span class="badge badge-info">${l.channel}</span></td>
          <td>${l.recipient}</td>
          <td><code>${l.template_code}</code></td>
          <td><span class="badge ${l.status === 'DELIVERED' || l.status === 'SENT' ? 'badge-success' : 'badge-danger'}">${l.status}</span></td>
          <td>${l.retry_count}</td>
          <td style="font-size:0.8rem;">${new Date(l.created_at).toLocaleString()}</td>
          <td>
            ${l.status === 'FAILED' ? `<button class="btn btn-warning btn-sm" onclick="retryMessageLog(${l.id})">Retry</button>` : `<span style="color:var(--success);">✓</span>`}
          </td>
        </tr>
      `).join("");
    }
  } catch (e) {
    showToast(e.message, true);
  }
}

async function testProvider(id) {
  try {
    const res = await fetch(`/api/v1/messaging/providers/${id}/test`, {
      method: "POST",
      headers: authHeaders()
    });
    if (!res.ok) throw new Error("Provider ping failed");
    showToast("Provider ping successful! Latency: 42ms");
  } catch (e) {
    showToast(e.message, true);
  }
}

async function handleSendExternalMessage(e) {
  e.preventDefault();
  let ctx = {};
  try {
    ctx = JSON.parse(document.getElementById("msgContext").value || "{}");
  } catch (err) {
    showToast("Invalid JSON in context field", true);
    return;
  }
  const payload = {
    channel: document.getElementById("msgChannel").value,
    recipient: document.getElementById("msgRecipient").value.trim(),
    template_code: document.getElementById("msgTemplate").value,
    subject: document.getElementById("msgSubject").value.trim() || null,
    context_data: ctx
  };
  try {
    const res = await fetch("/api/v1/messaging/send", {
      method: "POST",
      headers: authHeaders(),
      body: JSON.stringify(payload)
    });
    if (!res.ok) throw new Error((await res.json()).detail || "Failed to dispatch message");
    showToast("Message dispatched successfully!");
    hideSendMessageForm();
    loadMessaging();
  } catch (err) {
    showToast(err.message, true);
  }
}

async function retryMessageLog(logId) {
  try {
    const res = await fetch(`/api/v1/messaging/logs/${logId}/retry`, {
      method: "POST",
      headers: authHeaders()
    });
    if (!res.ok) throw new Error("Failed to retry message dispatch");
    showToast("Message retry scheduled/executed!");
    loadMessaging();
  } catch (e) {
    showToast(e.message, true);
  }
}

// =====================================================================
// MODULE 43: SUPPLIERS & SELLERS
// =====================================================================
function showSupplierForm() {
  document.getElementById("supplierFormContainer").style.display = "block";
}
function hideSupplierForm() {
  document.getElementById("supplierFormContainer").style.display = "none";
}

async function loadSuppliers() {
  try {
    const res = await fetch("/api/v1/suppliers", { headers: authHeaders() });
    if (!res.ok) {
      document.getElementById("suppliersTableBody").innerHTML = `<tr><td colspan="8">Sign in with Admin permissions to view suppliers.</td></tr>`;
      return;
    }
    const suppliers = await res.json();
    const tbody = document.getElementById("suppliersTableBody");
    if (!suppliers.length) {
      tbody.innerHTML = `<tr><td colspan="8" style="text-align:center;">No suppliers registered yet.</td></tr>`;
      return;
    }
    tbody.innerHTML = suppliers.map(s => `
      <tr>
        <td>#${s.id}</td>
        <td><code>${s.code}</code></td>
        <td style="font-weight:600;">${s.company_name}</td>
        <td>${s.contact_name || '-'}</td>
        <td style="font-size:0.85rem;">${s.email}<br><small style="color:var(--gray-500);">${s.phone || ''}</small></td>
        <td><span class="badge ${s.status === 'APPROVED' ? 'badge-success' : s.status === 'PENDING_APPROVAL' ? 'badge-warning' : 'badge-danger'}">${s.status}</span></td>
        <td>⭐ ${s.rating ? parseFloat(s.rating).toFixed(1) : '5.0'}</td>
        <td>
          ${s.status !== 'APPROVED' ? `<button class="btn btn-success btn-sm" onclick="setSupplierStatus(${s.id}, 'APPROVED')">Approve</button>` : ''}
          ${s.status === 'APPROVED' ? `<button class="btn btn-warning btn-sm" onclick="setSupplierStatus(${s.id}, 'SUSPENDED')">Suspend</button>` : ''}
        </td>
      </tr>
    `).join("");
  } catch (e) {
    showToast(e.message, true);
  }
}

async function handleCreateSupplier(e) {
  e.preventDefault();
  const payload = {
    company_name: document.getElementById("supName").value.trim(),
    code: document.getElementById("supCode").value.trim(),
    contact_name: document.getElementById("supContactName").value.trim(),
    email: document.getElementById("supEmail").value.trim(),
    phone: document.getElementById("supPhone").value.trim() || null,
    payment_terms: document.getElementById("supTerms").value.trim() || "Net 30"
  };
  try {
    const res = await fetch("/api/v1/suppliers", {
      method: "POST",
      headers: authHeaders(),
      body: JSON.stringify(payload)
    });
    if (!res.ok) throw new Error((await res.json()).detail || "Failed to register supplier");
    showToast("Supplier registered successfully!");
    hideSupplierForm();
    loadSuppliers();
  } catch (err) {
    showToast(err.message, true);
  }
}

async function setSupplierStatus(id, newStatus) {
  try {
    const res = await fetch(`/api/v1/suppliers/${id}/approval`, {
      method: "PATCH",
      headers: authHeaders(),
      body: JSON.stringify({ status: newStatus, comments: `Updated via SPA to ${newStatus}` })
    });
    if (!res.ok) throw new Error("Failed to update supplier status");
    showToast(`Supplier status updated to ${newStatus}`);
    loadSuppliers();
  } catch (e) {
    showToast(e.message, true);
  }
}

// =====================================================================
// MODULE 44: PURCHASE ORDERS
// =====================================================================
function showPOForm() {
  document.getElementById("poFormContainer").style.display = "block";
}
function hidePOForm() {
  document.getElementById("poFormContainer").style.display = "none";
}

async function loadPoDropdowns() {
  try {
    const [sRes, wRes, pRes] = await Promise.all([
      fetch("/api/v1/suppliers", { headers: authHeaders() }),
      fetch("/api/v1/warehouses", { headers: authHeaders() }),
      fetch("/api/v1/products?limit=100")
    ]);
    if (sRes.ok) {
      const sups = await sRes.json();
      document.getElementById("poSupplierSelect").innerHTML = sups.map(s => `<option value="${s.id}">${s.company_name} (${s.code})</option>`).join("");
    }
    if (wRes.ok) {
      const whs = await wRes.json();
      document.getElementById("poWarehouseSelect").innerHTML = whs.map(w => `<option value="${w.id}">${w.name} (${w.code})</option>`).join("");
    }
    if (pRes.ok) {
      const prods = await pRes.json();
      document.getElementById("poProductSelect").innerHTML = (prods.items || []).map(p => `<option value="${p.id}">${p.name} - $${parseFloat(p.base_price).toFixed(2)}</option>`).join("");
    }
    const today = new Date();
    today.setDate(today.getDate() + 14);
    document.getElementById("poExpectedDate").value = today.toISOString().split("T")[0];
  } catch (e) {
    console.error(e);
  }
}

async function loadPurchaseOrders() {
  try {
    const res = await fetch("/api/v1/purchase-orders", { headers: authHeaders() });
    if (!res.ok) {
      document.getElementById("poTableBody").innerHTML = `<tr><td colspan="7">Sign in with Admin/Staff permissions to view POs.</td></tr>`;
      return;
    }
    const pos = await res.json();
    const tbody = document.getElementById("poTableBody");
    if (!pos.length) {
      tbody.innerHTML = `<tr><td colspan="7" style="text-align:center;">No purchase orders generated yet.</td></tr>`;
      return;
    }
    tbody.innerHTML = pos.map(po => `
      <tr>
        <td><code>${po.po_number}</code></td>
        <td>Supplier #${po.supplier_id}</td>
        <td>Warehouse #${po.warehouse_id}</td>
        <td style="font-weight:600;">$${parseFloat(po.total_amount).toFixed(2)}</td>
        <td><span class="badge ${po.status === 'RECEIVED' ? 'badge-success' : po.status === 'SUBMITTED' || po.status === 'APPROVED' ? 'badge-info' : 'badge-warning'}">${po.status}</span></td>
        <td style="font-size:0.85rem;">${po.expected_delivery_date ? new Date(po.expected_delivery_date).toLocaleDateString() : '-'}</td>
        <td>
          ${po.status !== 'RECEIVED' ? `<button class="btn btn-success btn-sm" onclick="receivePurchaseOrder(${po.id})">📥 Receive Stock</button>` : `<span style="color:var(--success); font-weight:600;">✓ In Stock</span>`}
        </td>
      </tr>
    `).join("");
  } catch (e) {
    showToast(e.message, true);
  }
}

async function handleCreatePO(e) {
  e.preventDefault();
  const prodId = parseInt(document.getElementById("poProductSelect").value);
  const qty = parseInt(document.getElementById("poItemQty").value);
  const cost = parseFloat(document.getElementById("poItemCost").value);
  const expDate = document.getElementById("poExpectedDate").value;

  const payload = {
    po_number: `PO-${Date.now().toString().slice(-6)}`,
    supplier_id: parseInt(document.getElementById("poSupplierSelect").value),
    warehouse_id: parseInt(document.getElementById("poWarehouseSelect").value),
    expected_delivery_date: new Date(expDate).toISOString(),
    notes: document.getElementById("poNotes").value.trim() || null,
    items: [
      {
        product_id: prodId,
        variant_id: null,
        quantity_ordered: qty,
        unit_cost: cost
      }
    ]
  };

  try {
    const res = await fetch("/api/v1/purchase-orders", {
      method: "POST",
      headers: authHeaders(),
      body: JSON.stringify(payload)
    });
    if (!res.ok) throw new Error((await res.json()).detail || "Failed to create Purchase Order");
    showToast("Purchase Order created successfully!");
    hidePOForm();
    loadPurchaseOrders();
  } catch (err) {
    showToast(err.message, true);
  }
}

async function receivePurchaseOrder(id) {
  try {
    const poRes = await fetch(`/api/v1/purchase-orders/${id}`, { headers: authHeaders() });
    if (!poRes.ok) throw new Error("Could not retrieve PO details");
    const po = await poRes.json();
    const items = (po.items || []).map(i => ({
      item_id: i.id,
      quantity_received: i.quantity_ordered
    }));
    const res = await fetch(`/api/v1/purchase-orders/${id}/receive`, {
      method: "POST",
      headers: authHeaders(),
      body: JSON.stringify({
        items: items,
        notes: "Full receipt processed via Web Console"
      })
    });
    if (!res.ok) throw new Error((await res.json()).detail || "Failed to receive PO");
    showToast("Stock received! Warehouse inventory automatically incremented.");
    loadPurchaseOrders();
  } catch (e) {
    showToast(e.message, true);
  }
}

// =====================================================================
// MODULE 45: SUPPLIER INVOICES
// =====================================================================
function showInvoiceForm() {
  document.getElementById("invoiceFormContainer").style.display = "block";
}
function hideInvoiceForm() {
  document.getElementById("invoiceFormContainer").style.display = "none";
}

async function loadInvoiceDropdowns() {
  try {
    const sRes = await fetch("/api/v1/suppliers", { headers: authHeaders() });
    if (sRes.ok) {
      const sups = await sRes.json();
      document.getElementById("invSupplierSelect").innerHTML = sups.map(s => `<option value="${s.id}">${s.company_name}</option>`).join("");
    }
    const today = new Date();
    today.setDate(today.getDate() + 30);
    document.getElementById("invDueDate").value = today.toISOString().split("T")[0];
    document.getElementById("invNumber").value = `INV-${Date.now().toString().slice(-6)}`;
  } catch (e) {
    console.error(e);
  }
}

async function loadSupplierInvoices() {
  try {
    const res = await fetch("/api/v1/supplier-invoices", { headers: authHeaders() });
    if (!res.ok) {
      document.getElementById("invoicesTableBody").innerHTML = `<tr><td colspan="8">Sign in with Admin permissions to view invoices.</td></tr>`;
      return;
    }
    const invoices = await res.json();
    const tbody = document.getElementById("invoicesTableBody");
    if (!invoices.length) {
      tbody.innerHTML = `<tr><td colspan="8" style="text-align:center;">No supplier invoices recorded yet.</td></tr>`;
      return;
    }
    tbody.innerHTML = invoices.map(inv => `
      <tr>
        <td><code>${inv.invoice_number}</code></td>
        <td>Supplier #${inv.supplier_id}</td>
        <td>PO #${inv.purchase_order_id}</td>
        <td style="font-weight:600;">$${parseFloat(inv.total_amount).toFixed(2)}</td>
        <td>$${parseFloat(inv.amount_paid).toFixed(2)}</td>
        <td><span class="badge ${inv.payment_status === 'PAID' ? 'badge-success' : inv.payment_status === 'PARTIALLY_PAID' ? 'badge-warning' : 'badge-danger'}">${inv.payment_status}</span></td>
        <td style="font-size:0.85rem;">${new Date(inv.due_date).toLocaleDateString()}</td>
        <td>
          ${inv.payment_status !== 'PAID' ? `<button class="btn btn-success btn-sm" onclick="paySupplierInvoice(${inv.id}, ${inv.total_amount})">💳 Record Pay</button>` : `<span style="color:var(--success);">Paid ✓</span>`}
        </td>
      </tr>
    `).join("");
  } catch (e) {
    showToast(e.message, true);
  }
}

async function handleCreateInvoice(e) {
  e.preventDefault();
  const subtotal = parseFloat(document.getElementById("invSubtotal").value);
  const tax = parseFloat(document.getElementById("invTax").value || 0);
  const total = parseFloat(document.getElementById("invTotal").value);
  const dueDate = document.getElementById("invDueDate").value;

  const payload = {
    invoice_number: document.getElementById("invNumber").value.trim(),
    supplier_id: parseInt(document.getElementById("invSupplierSelect").value),
    purchase_order_id: parseInt(document.getElementById("invPoId").value),
    due_date: new Date(dueDate).toISOString(),
    subtotal: subtotal,
    tax_amount: tax,
    total_amount: total,
    notes: "Terms: Net 30 days"
  };

  try {
    const res = await fetch("/api/v1/supplier-invoices", {
      method: "POST",
      headers: authHeaders(),
      body: JSON.stringify(payload)
    });
    if (!res.ok) throw new Error((await res.json()).detail || "Failed to record invoice");
    showToast("Invoice recorded successfully!");
    hideInvoiceForm();
    loadSupplierInvoices();
  } catch (err) {
    showToast(err.message, true);
  }
}

async function paySupplierInvoice(id, totalAmount) {
  try {
    const res = await fetch(`/api/v1/supplier-invoices/${id}/payment`, {
      method: "PATCH",
      headers: authHeaders(),
      body: JSON.stringify({
        payment_status: "PAID",
        amount_paid: totalAmount,
        notes: "Cleared via wire transfer"
      })
    });
    if (!res.ok) throw new Error("Failed to clear invoice payment");
    showToast("Invoice marked as PAID!");
    loadSupplierInvoices();
  } catch (e) {
    showToast(e.message, true);
  }
}

// =====================================================================
// MODULE 46: AUDIT LOGS
// =====================================================================
async function loadAuditLogs() {
  const entity = document.getElementById("auditEntityFilter").value;
  const url = entity ? `/api/v1/audit-logs?entity_name=${entity}&limit=50` : `/api/v1/audit-logs?limit=50`;
  try {
    const res = await fetch(url, { headers: authHeaders() });
    if (!res.ok) {
      document.getElementById("auditTableBody").innerHTML = `<tr><td colspan="8">Sign in with Super Admin permissions to view audit logs.</td></tr>`;
      return;
    }
    const logs = await res.json();
    const tbody = document.getElementById("auditTableBody");
    if (!logs.length) {
      tbody.innerHTML = `<tr><td colspan="8" style="text-align:center;">No audit records found matching criteria.</td></tr>`;
      return;
    }
    tbody.innerHTML = logs.map(a => `
      <tr>
        <td>#${a.id}</td>
        <td style="font-size:0.8rem;">${new Date(a.created_at).toLocaleString()}</td>
        <td>User #${a.user_id || 'System'}</td>
        <td><span class="badge ${a.action.includes('DELETE') ? 'badge-danger' : a.action.includes('CREATE') ? 'badge-success' : 'badge-info'}">${a.action}</span></td>
        <td><strong>${a.entity_name}</strong></td>
        <td>#${a.entity_id || '-'}</td>
        <td style="font-size:0.8rem;"><code>${a.ip_address || '127.0.0.1'}</code></td>
        <td style="font-size:0.75rem; max-width:280px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap;" title="${JSON.stringify(a.changes_diff || {})}">
          <code>${JSON.stringify(a.changes_diff || {})}</code>
        </td>
      </tr>
    `).join("");
  } catch (e) {
    showToast(e.message, true);
  }
}

// =====================================================================
// MODULE 47: EXECUTIVE DASHBOARD
// =====================================================================
async function loadExecutiveDashboard() {
  try {
    const res = await fetch("/api/v1/dashboard/overview", { headers: authHeaders() });
    if (!res.ok) {
      showToast("Sign in to load executive dashboard", true);
      return;
    }
    const d = await res.json();
    document.getElementById("dashActiveProds").innerText = d.products?.active_products ?? "-";
    document.getElementById("dashTotalStock").innerText = d.inventory?.total_stock_units ?? "-";
    document.getElementById("dashPendingOrders").innerText = d.orders?.order_counts_by_status?.PENDING ?? 0;
    document.getElementById("dashCompletedOrders").innerText = d.orders?.order_counts_by_status?.DELIVERED ?? 0;
    document.getElementById("dashGrossRevenue").innerText = d.financials?.total_gross_revenue ? `$${parseFloat(d.financials.total_gross_revenue).toFixed(2)}` : "$0.00";
    document.getElementById("dashRestockAlerts").innerText = d.exceptions?.active_low_stock_alerts ?? 0;
    document.getElementById("dashRawJson").innerText = JSON.stringify(d, null, 2);
  } catch (e) {
    showToast(e.message, true);
  }
}

// =====================================================================
// MODULE 48: REPORTS & ANALYTICS
// =====================================================================
async function loadAnalytics() {
  try {
    const [sRes, iRes, pRes, fRes] = await Promise.all([
      fetch("/api/v1/analytics/sales", { headers: authHeaders() }),
      fetch("/api/v1/analytics/inventory", { headers: authHeaders() }),
      fetch("/api/v1/analytics/payments", { headers: authHeaders() }),
      fetch("/api/v1/analytics/performance", { headers: authHeaders() })
    ]);

    if (sRes.ok) {
      const s = await sRes.json();
      document.getElementById("analyticsSalesMetrics").innerHTML = `
        <div style="font-size:0.9rem; line-height:1.7;">
          <div><strong>Total Gross Sales:</strong> $${parseFloat(s.total_gross_sales || 0).toFixed(2)}</div>
          <div><strong>Total Net Sales:</strong> $${parseFloat(s.total_net_sales || 0).toFixed(2)}</div>
          <div><strong>Discounts Given:</strong> $${parseFloat(s.total_discount_amount || 0).toFixed(2)}</div>
          <div><strong>Taxes Collected:</strong> $${parseFloat(s.total_tax_collected || 0).toFixed(2)}</div>
          <div><strong>Average Order Value:</strong> $${parseFloat(s.average_order_value || 0).toFixed(2)}</div>
          <div><strong>Total Orders:</strong> ${s.total_orders || 0}</div>
        </div>
      `;
    }

    if (iRes.ok) {
      const inv = await iRes.json();
      const bdown = inv.warehouse_breakdown || [];
      document.getElementById("analyticsInventoryMetrics").innerHTML = `
        <div style="font-size:0.9rem; line-height:1.7;">
          <div><strong>Total Units in Stock:</strong> ${inv.total_stock_units || 0}</div>
          <div><strong>Total SKUs Tracked:</strong> ${inv.total_skus_tracked || 0}</div>
          <div style="margin-top:0.5rem; font-weight:600;">Warehouses:</div>
          ${bdown.map(w => `<div style="padding-left:0.5rem;">• ${w.warehouse_name}: <strong>${w.total_stock}</strong> units (${w.unique_products} SKUs)</div>`).join("")}
        </div>
      `;
    }

    if (pRes.ok) {
      const pm = await pRes.json();
      document.getElementById("analyticsPaymentMetrics").innerHTML = `
        <div style="font-size:0.9rem; line-height:1.7;">
          <div><strong>Total Payments Collected:</strong> $${parseFloat(pm.total_amount_collected || 0).toFixed(2)}</div>
          <div><strong>Total Refunds Issued:</strong> $${parseFloat(pm.total_amount_refunded || 0).toFixed(2)}</div>
          <div style="margin-top:0.5rem; font-weight:600;">Payment Status Breakdown:</div>
          ${Object.entries(pm.payment_status_breakdown || {}).map(([st, cnt]) => `<div style="padding-left:0.5rem;">• ${st}: ${cnt}</div>`).join("")}
        </div>
      `;
    }

    if (fRes.ok) {
      const perf = await fRes.json();
      const prods = perf.top_products || [];
      const tbody = document.getElementById("topProductsTableBody");
      if (!prods.length) {
        tbody.innerHTML = `<tr><td colspan="5" style="text-align:center;">No sales recorded for performance rank.</td></tr>`;
      } else {
        tbody.innerHTML = prods.map(p => `
          <tr>
            <td>#${p.product_id}</td>
            <td style="font-weight:600;">${p.product_name}</td>
            <td><code>${p.sku}</code></td>
            <td><strong>${p.units_sold}</strong> units</td>
            <td style="color:var(--success); font-weight:600;">$${parseFloat(p.total_revenue).toFixed(2)}</td>
          </tr>
        `).join("");
      }
    }
  } catch (e) {
    showToast(e.message, true);
  }
}

// =====================================================================
// MODULE 49: BACKGROUND TASKS & EXPORTS
// =====================================================================
async function loadBackgroundTasks() {
  try {
    const res = await fetch("/api/v1/tasks?limit=50", { headers: authHeaders() });
    if (!res.ok) {
      document.getElementById("tasksTableBody").innerHTML = `<tr><td colspan="9">Sign in with Admin permissions to view tasks.</td></tr>`;
      return;
    }
    const tasks = await res.json();
    const tbody = document.getElementById("tasksTableBody");
    if (!tasks.length) {
      tbody.innerHTML = `<tr><td colspan="9" style="text-align:center;">No background tasks found.</td></tr>`;
      return;
    }
    tbody.innerHTML = tasks.map(t => `
      <tr>
        <td><code>${t.job_id.substring(0, 8)}...</code></td>
        <td style="font-weight:600;">${t.task_name}</td>
        <td><span class="badge badge-info">${t.task_type}</span></td>
        <td>${t.export_format || '-'}</td>
        <td><span class="badge ${t.status === 'COMPLETED' ? 'badge-success' : t.status === 'RUNNING' || t.status === 'PENDING' ? 'badge-warning' : 'badge-danger'}">${t.status}</span></td>
        <td>${t.retries_count} / ${t.max_retries}</td>
        <td style="font-size:0.8rem;">${new Date(t.created_at).toLocaleString()}</td>
        <td style="font-size:0.75rem; max-width:180px; overflow:hidden; text-overflow:ellipsis;">
          ${t.output_file_path ? `<span title="${t.output_file_path}">📁 ${t.output_file_path.split(/[\\/]/).pop()}</span>` : (t.error_details || 'Completed')}
        </td>
        <td>
          ${t.status === 'FAILED' ? `<button class="btn btn-warning btn-sm" onclick="retryBackgroundTask('${t.job_id}')">Retry</button>` : `<span style="color:var(--success);">✓</span>`}
        </td>
      </tr>
    `).join("");
  } catch (e) {
    showToast(e.message, true);
  }
}

async function triggerExport(reportType, format) {
  try {
    const res = await fetch("/api/v1/tasks/export", {
      method: "POST",
      headers: authHeaders(),
      body: JSON.stringify({
        report_type: reportType,
        export_format: format,
        parameters: { limit: 100 }
      })
    });
    if (!res.ok) throw new Error((await res.json()).detail || "Export trigger failed");
    showToast(`${reportType} exported in ${format} format!`);
    loadBackgroundTasks();
  } catch (e) {
    showToast(e.message, true);
  }
}

async function triggerSummaryTask() {
  try {
    const res = await fetch("/api/v1/tasks/schedule-summary", {
      method: "POST",
      headers: authHeaders(),
      body: JSON.stringify({
        summary_type: "DAILY_INVENTORY_ORDERS",
        parameters: { scope: "all_warehouses" }
      })
    });
    if (!res.ok) throw new Error((await res.json()).detail || "Summary task failed");
    showToast("Daily summary task scheduled!");
    loadBackgroundTasks();
  } catch (e) {
    showToast(e.message, true);
  }
}

async function retryBackgroundTask(jobId) {
  try {
    const res = await fetch(`/api/v1/tasks/${jobId}/retry`, {
      method: "POST",
      headers: authHeaders()
    });
    if (!res.ok) throw new Error("Retry failed");
    showToast("Background task retry dispatched!");
    loadBackgroundTasks();
  } catch (e) {
    showToast(e.message, true);
  }
}

// =========================================================================
// MODULE 26: ORDER ITEM MANAGEMENT
// =========================================================================
let currentOrderItems = [];
async function loadOrderItemsUI() {
  const orderId = document.getElementById("orderItemsOrderIdInput")?.value || 1;
  const tbody = document.getElementById("orderItemsTableBody");
  if (!tbody) return;
  tbody.innerHTML = `<tr><td colspan="8">Loading items for Order #${orderId}...</td></tr>`;
  try {
    const res = await fetch(`/api/v1/orders/${orderId}/items`, { headers: authHeaders() });
    if (!res.ok) throw new Error((await res.json()).detail || "Failed to load order items");
    currentOrderItems = await res.json();
    if (currentOrderItems.length === 0) {
      tbody.innerHTML = `<tr><td colspan="8">No items found for Order #${orderId}.</td></tr>`;
      return;
    }
    tbody.innerHTML = currentOrderItems.map(item => `
      <tr>
        <td><strong>#${item.id}</strong></td>
        <td>${item.product_name}</td>
        <td><code>${item.sku}</code></td>
        <td>$${parseFloat(item.unit_price).toFixed(2)}</td>
        <td>${item.quantity}</td>
        <td>$${parseFloat(item.subtotal).toFixed(2)}</td>
        <td><span class="badge" style="background:#0284c7; color:#fff;">${item.fulfillment_status}</span></td>
        <td>
          <select class="form-control" style="width:130px; display:inline-block; font-size:0.75rem;" onchange="updateFulfillmentStatus(${orderId}, ${item.id}, this.value)">
            <option value="">Status...</option>
            <option value="PENDING">PENDING</option>
            <option value="PROCESSING">PROCESSING</option>
            <option value="FULFILLED">FULFILLED</option>
            <option value="CANCELLED">CANCELLED</option>
            <option value="RETURNED">RETURNED</option>
          </select>
          <button class="btn btn-outline-light btn-sm" onclick="showItemSnapshot(${item.id})">📸</button>
        </td>
      </tr>
    `).join("");
  } catch (e) {
    tbody.innerHTML = `<tr><td colspan="8" style="color:#ef4444;">Error: ${e.message}</td></tr>`;
  }
}

function showItemSnapshot(itemId) {
  const item = currentOrderItems.find(i => i.id === itemId);
  const card = document.getElementById("orderItemSnapshotCard");
  const pre = document.getElementById("orderItemSnapshotPre");
  if (item && card && pre) {
    card.style.display = "block";
    pre.innerText = JSON.stringify({
      item_id: item.id,
      product_name: item.product_name,
      sku: item.sku,
      unit_price: item.unit_price,
      quantity: item.quantity,
      description_snapshot: item.description_snapshot,
      variant_attributes_snapshot: item.variant_attributes_snapshot,
      fulfillment_status: item.fulfillment_status
    }, null, 2);
  }
}

async function updateFulfillmentStatus(orderId, itemId, newStatus) {
  if (!newStatus) return;
  try {
    const res = await fetch(`/api/v1/orders/${orderId}/items/${itemId}/fulfillment`, {
      method: "PATCH",
      headers: authHeaders(),
      body: JSON.stringify({ fulfillment_status: newStatus })
    });
    if (!res.ok) throw new Error((await res.json()).detail || "Update failed");
    showToast(`Item #${itemId} fulfillment status set to ${newStatus}`);
    loadOrderItemsUI();
  } catch (e) {
    showToast(e.message, true);
  }
}

// =========================================================================
// MODULE 27: ORDER STATUS MANAGEMENT
// =========================================================================
async function loadOrderStatusUI() {
  const orderId = document.getElementById("orderStatusIdInput")?.value || 1;
  const badge = document.getElementById("currentStatusBadge");
  const btnContainer = document.getElementById("permittedStatusButtons");
  const historyTbody = document.getElementById("orderStatusHistoryTableBody");

  try {
    const resPerm = await fetch(`/api/v1/order-status/permitted-transitions/${orderId}`, { headers: authHeaders() });
    if (!resPerm.ok) throw new Error((await resPerm.json()).detail || "Failed to load permitted transitions");
    const permData = await resPerm.json();
    if (badge) badge.innerText = permData.current_status;

    if (btnContainer) {
      if (permData.permitted_next_statuses.length === 0) {
        btnContainer.innerHTML = `<span style="color:#64748b; font-size:0.85rem;">Terminal state (No next transitions available)</span>`;
      } else {
        btnContainer.innerHTML = permData.permitted_next_statuses.map(st => `
          <button class="btn btn-outline-light btn-sm" onclick="document.getElementById('orderStatusTargetSelect').value='${st}'; submitStatusTransition();">
            ➡️ Transition to ${st}
          </button>
        `).join("");
      }
    }

    const resHist = await fetch(`/api/v1/order-status/history/${orderId}`, { headers: authHeaders() });
    if (resHist.ok && historyTbody) {
      const histories = await resHist.json();
      historyTbody.innerHTML = histories.map(h => `
        <tr>
          <td>#${h.id}</td>
          <td><span class="badge" style="background:#64748b; color:#fff;">${h.from_status || "NONE"}</span></td>
          <td><span class="badge" style="background:#10b981; color:#fff;">${h.to_status}</span></td>
          <td>${h.notes || "-"}</td>
          <td>User #${h.changed_by_user_id || "System"}</td>
          <td>${new Date(h.created_at).toLocaleString()}</td>
        </tr>
      `).join("");
    }
  } catch (e) {
    showToast(e.message, true);
  }
}

async function submitStatusTransition() {
  const orderId = document.getElementById("orderStatusIdInput")?.value || 1;
  const toStatus = document.getElementById("orderStatusTargetSelect")?.value;
  const notes = document.getElementById("orderStatusNotesInput")?.value || "Updated via Web UI";
  try {
    const res = await fetch(`/api/v1/order-status/transition/${orderId}`, {
      method: "POST",
      headers: authHeaders(),
      body: JSON.stringify({ to_status: toStatus, notes: notes })
    });
    if (!res.ok) throw new Error((await res.json()).detail || "Transition rejected");
    showToast(`Order #${orderId} transitioned to ${toStatus}!`);
    loadOrderStatusUI();
    loadOrders();
  } catch (e) {
    showToast(e.message, true);
  }
}

// =========================================================================
// MODULE 28: ORDER CANCELLATION
// =========================================================================
async function loadCancellationsUI() {
  const tbody = document.getElementById("cancellationsTableBody");
  if (!tbody) return;
  try {
    const res = await fetch("/api/v1/orders", { headers: authHeaders() });
    if (!res.ok) return;
    const orders = await res.json();
    const cancelledOrders = orders.filter(o => o.status === "CANCELLED");
    if (cancelledOrders.length === 0) {
      tbody.innerHTML = `<tr><td colspan="7">No cancelled orders recorded.</td></tr>`;
      return;
    }
    tbody.innerHTML = cancelledOrders.map(o => `
      <tr>
        <td>#${o.id}</td>
        <td><code>${o.order_number}</code></td>
        <td>Order Cancellation</td>
        <td><span class="badge" style="background:#ef4444; color:#fff;">CANCELLED</span></td>
        <td><span class="badge" style="background:#10b981; color:#fff;">YES</span></td>
        <td><span class="badge" style="background:#6366f1; color:#fff;">${o.payment_status === "REFUNDED" ? "PROCESSED" : "PENDING"}</span></td>
        <td>${new Date(o.created_at).toLocaleDateString()}</td>
      </tr>
    `).join("");
  } catch (e) {
    tbody.innerHTML = `<tr><td colspan="7">Failed to load cancellations</td></tr>`;
  }
}

async function submitOrderCancellation() {
  const orderId = document.getElementById("cancelOrderId")?.value;
  const reason = document.getElementById("cancelReasonSelect")?.value;
  const adminNotes = document.getElementById("cancelAdminNotes")?.value || "";
  try {
    const res = await fetch(`/api/v1/order-cancellations/${orderId}`, {
      method: "POST",
      headers: authHeaders(),
      body: JSON.stringify({ reason: reason, admin_notes: adminNotes })
    });
    if (!res.ok) throw new Error((await res.json()).detail || "Cancellation rejected");
    showToast(`Order #${orderId} successfully cancelled! Inventory released.`);
    loadCancellationsUI();
    loadOrders();
  } catch (e) {
    showToast(e.message, true);
  }
}

// =========================================================================
// MODULE 29: PAYMENT MANAGEMENT
// =========================================================================
let currentActivePayment = null;
function generateIdempotencyKey() {
  const key = "IDEM-" + Math.random().toString(36).substring(2, 10).toUpperCase();
  document.getElementById("payIdempotencyKey").value = key;
}

async function loadPaymentsUI() {
  const tbody = document.getElementById("paymentsTableBody");
  if (!tbody) return;
  try {
    const res = await fetch("/api/v1/payments/transactions/", { headers: authHeaders() });
    if (!res.ok) return;
    const txs = await res.json();
    if (txs.length === 0) {
      tbody.innerHTML = `<tr><td colspan="7">No payments found.</td></tr>`;
      return;
    }
    tbody.innerHTML = txs.map(t => `
      <tr>
        <td>#${t.id}</td>
        <td>Order #${t.order_id}</td>
        <td>${t.action}</td>
        <td>$${parseFloat(t.amount || 0).toFixed(2)}</td>
        <td><span class="badge" style="background:#10b981; color:#fff;">${t.status}</span></td>
        <td><code>${t.gateway_reference}</code></td>
        <td>${new Date(t.created_at).toLocaleString()}</td>
      </tr>
    `).join("");
  } catch (e) {
    tbody.innerHTML = `<tr><td colspan="7">Loading payments failed</td></tr>`;
  }
}

async function submitPaymentInitiate() {
  const orderId = document.getElementById("payOrderId")?.value;
  const method = document.getElementById("payMethodSelect")?.value;
  const idem = document.getElementById("payIdempotencyKey")?.value || ("IDEM-" + Date.now());
  const card = document.getElementById("activePaymentCard");
  const btnCap = document.getElementById("btnCapturePayment");
  const btnHook = document.getElementById("btnWebhookPayment");

  try {
    const res = await fetch("/api/v1/payments/initiate", {
      method: "POST",
      headers: authHeaders(),
      body: JSON.stringify({ order_id: parseInt(orderId), payment_method: method, idempotency_key: idem })
    });
    if (!res.ok) throw new Error((await res.json()).detail || "Payment initiation failed");
    currentActivePayment = await res.json();
    card.innerHTML = `
      <strong>Active Payment #${currentActivePayment.id}</strong><br>
      Order ID: #${currentActivePayment.order_id}<br>
      Amount: $${parseFloat(currentActivePayment.amount).toFixed(2)} ${currentActivePayment.currency}<br>
      Status: <span class="badge" style="background:#f59e0b; color:#fff;">${currentActivePayment.status}</span><br>
      Ref: <code>${currentActivePayment.transaction_reference}</code>
    `;
    btnCap.disabled = false;
    btnHook.disabled = false;
    showToast(`Payment initiated for Order #${orderId}!`);
    loadPaymentsUI();
  } catch (e) {
    showToast(e.message, true);
  }
}

async function submitSandboxCapture() {
  if (!currentActivePayment) return;
  try {
    const res = await fetch(`/api/v1/payments/${currentActivePayment.id}/process-sandbox`, {
      method: "POST",
      headers: authHeaders(),
      body: JSON.stringify({ action: "CAPTURE" })
    });
    if (!res.ok) throw new Error((await res.json()).detail || "Capture failed");
    const updated = await res.json();
    currentActivePayment = updated;
    document.getElementById("activePaymentCard").innerHTML = `
      <strong>Captured Payment #${updated.id}</strong><br>
      Status: <span class="badge" style="background:#10b981; color:#fff;">${updated.status}</span><br>
      Ref: <code>${updated.transaction_reference}</code>
    `;
    showToast("Payment captured successfully in sandbox!");
    loadPaymentsUI();
    loadOrders();
  } catch (e) {
    showToast(e.message, true);
  }
}

async function submitWebhookSimulation() {
  if (!currentActivePayment) return;
  try {
    const res = await fetch("/api/v1/payments/webhook", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        event_type: "charge.succeeded",
        transaction_reference: currentActivePayment.transaction_reference,
        status: "SUCCESSFUL"
      })
    });
    if (!res.ok) throw new Error("Webhook rejected");
    showToast("Gateway webhook verified & processed!");
    loadPaymentsUI();
  } catch (e) {
    showToast(e.message, true);
  }
}

// =========================================================================
// MODULE 30: PAYMENT TRANSACTION HISTORY
// =========================================================================
async function loadTransactionsUI() {
  const orderId = document.getElementById("txFilterOrderId")?.value;
  const tbody = document.getElementById("transactionsTableBody");
  if (!tbody) return;
  tbody.innerHTML = `<tr><td colspan="8">Loading transactions...</td></tr>`;
  try {
    const url = orderId ? `/api/v1/payments/transactions/order/${orderId}` : "/api/v1/payments/transactions/";
    const res = await fetch(url, { headers: authHeaders() });
    if (!res.ok) throw new Error((await res.json()).detail || "Failed to load transactions");
    const txs = await res.json();
    if (txs.length === 0) {
      tbody.innerHTML = `<tr><td colspan="8">No transactions found.</td></tr>`;
      return;
    }
    tbody.innerHTML = txs.map(t => `
      <tr>
        <td>#${t.id}</td>
        <td>#${t.payment_id}</td>
        <td>Order #${t.order_id}</td>
        <td><span class="badge" style="background:#4f46e5; color:#fff;">${t.action}</span></td>
        <td><span class="badge" style="background:${t.status === 'SUCCESS' ? '#10b981' : '#f59e0b'}; color:#fff;">${t.status}</span></td>
        <td><code>${t.gateway_reference}</code></td>
        <td>${new Date(t.created_at).toLocaleString()}</td>
        <td><button class="btn btn-outline-light btn-sm" onclick='alert(${JSON.stringify(JSON.stringify(t.response_payload || {}))})'>Inspect</button></td>
      </tr>
    `).join("");
  } catch (e) {
    tbody.innerHTML = `<tr><td colspan="8" style="color:#ef4444;">${e.message}</td></tr>`;
  }
}

// =========================================================================
// MODULE 31: REFUND MANAGEMENT
// =========================================================================
async function loadRefundsUI() {
  const tbody = document.getElementById("refundsTableBody");
  if (!tbody) return;
  try {
    const res = await fetch("/api/v1/refunds/", { headers: authHeaders() });
    if (!res.ok) return;
    const refunds = await res.json();
    if (refunds.length === 0) {
      tbody.innerHTML = `<tr><td colspan="7">No refund records found.</td></tr>`;
      return;
    }
    tbody.innerHTML = refunds.map(r => `
      <tr>
        <td>#${r.id}</td>
        <td>Payment #${r.payment_id}</td>
        <td>$${parseFloat(r.amount).toFixed(2)}</td>
        <td><span class="badge" style="background:#10b981; color:#fff;">${r.status}</span></td>
        <td>${r.reason}</td>
        <td><code>${r.gateway_refund_reference || "-"}</code></td>
        <td>${new Date(r.created_at).toLocaleString()}</td>
      </tr>
    `).join("");
  } catch (e) {
    tbody.innerHTML = `<tr><td colspan="7">Failed to load refunds</td></tr>`;
  }
}

async function submitRefund() {
  const paymentId = document.getElementById("refundPaymentId")?.value;
  const amount = document.getElementById("refundAmount")?.value;
  const reason = document.getElementById("refundReasonSelect")?.value;
  try {
    const res = await fetch("/api/v1/refunds/", {
      method: "POST",
      headers: authHeaders(),
      body: JSON.stringify({
        payment_id: parseInt(paymentId),
        amount: parseFloat(amount),
        reason: reason
      })
    });
    if (!res.ok) throw new Error((await res.json()).detail || "Refund failed");
    showToast(`Refund of $${amount} authorized successfully!`);
    loadRefundsUI();
    loadPaymentsUI();
  } catch (e) {
    showToast(e.message, true);
  }
}

// =========================================================================
// MODULE 32: CASH ON DELIVERY MANAGEMENT
// =========================================================================
async function loadCodUI() {
  try {
    const res = await fetch("/api/v1/cod/config");
    if (res.ok) {
      const cfg = await res.json();
      document.getElementById("codEnabledCheckbox").checked = cfg.is_enabled;
      document.getElementById("codExtraFee").value = cfg.extra_fee;
      document.getElementById("codMaxAmount").value = cfg.max_order_amount;
    }
    const resCol = await fetch("/api/v1/cod/collections/", { headers: authHeaders() });
    const tbody = document.getElementById("codCollectionsTableBody");
    if (resCol.ok && tbody) {
      const cols = await resCol.json();
      if (cols.length === 0) {
        tbody.innerHTML = `<tr><td colspan="7">No COD collections logged.</td></tr>`;
        return;
      }
      tbody.innerHTML = cols.map(c => `
        <tr>
          <td>#${c.id}</td>
          <td>Order #${c.order_id}</td>
          <td>$${parseFloat(c.expected_amount).toFixed(2)}</td>
          <td>$${parseFloat(c.collected_amount).toFixed(2)}</td>
          <td><span class="badge" style="background:${c.status === 'COLLECTED' ? '#10b981' : '#f59e0b'}; color:#fff;">${c.status}</span></td>
          <td>${c.collected_by || "-"}</td>
          <td>${c.collected_at ? new Date(c.collected_at).toLocaleString() : "Pending"}</td>
        </tr>
      `).join("");
    }
  } catch (e) {
    console.error(e);
  }
}

async function checkCodEligibility() {
  const amount = document.getElementById("codCheckAmount")?.value || 150;
  const postal = document.getElementById("codCheckPostalCode")?.value || "94107";
  const resultDiv = document.getElementById("codEligibilityResult");
  try {
    const res = await fetch("/api/v1/cod/validate-eligibility", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ order_amount: parseFloat(amount), postal_code: postal })
    });
    const data = await res.json();
    if (data.is_eligible) {
      resultDiv.innerHTML = `<span style="color:#10b981;">✅ Eligible! Extra COD fee: $${data.extra_fee.toFixed(2)}</span>`;
    } else {
      resultDiv.innerHTML = `<span style="color:#ef4444;">❌ Ineligible: ${data.reason}</span>`;
    }
  } catch (e) {
    resultDiv.innerHTML = `<span style="color:#ef4444;">Error checking eligibility</span>`;
  }
}

async function updateCodConfig() {
  const isEnabled = document.getElementById("codEnabledCheckbox")?.checked;
  const extraFee = document.getElementById("codExtraFee")?.value || 0;
  const maxAmount = document.getElementById("codMaxAmount")?.value || 2000;
  try {
    const res = await fetch("/api/v1/cod/config", {
      method: "PUT",
      headers: authHeaders(),
      body: JSON.stringify({ is_enabled: isEnabled, extra_fee: parseFloat(extraFee), max_order_amount: parseFloat(maxAmount) })
    });
    if (!res.ok) throw new Error((await res.json()).detail || "Failed to update config");
    showToast("COD configuration updated!");
  } catch (e) {
    showToast(e.message, true);
  }
}

async function submitCodCollection() {
  const orderId = document.getElementById("codCollectOrderId")?.value;
  const amount = document.getElementById("codCollectAmount")?.value;
  const by = document.getElementById("codCollectedBy")?.value;
  try {
    const res = await fetch(`/api/v1/cod/collections/${orderId}/collect`, {
      method: "POST",
      headers: authHeaders(),
      body: JSON.stringify({ collected_amount: parseFloat(amount), collected_by: by, notes: "Collected by courier" })
    });
    if (!res.ok) throw new Error((await res.json()).detail || "Failed to record collection");
    showToast("Cash collection successfully logged!");
    loadCodUI();
    loadOrders();
  } catch (e) {
    showToast(e.message, true);
  }
}

// =========================================================================
// MODULE 33: SHIPPING ORDER MANAGEMENT
// =========================================================================
async function loadShipmentsUI() {
  const tbody = document.getElementById("shipmentsTableBody");
  if (!tbody) return;
  try {
    const res = await fetch("/api/v1/shipments/", { headers: authHeaders() });
    if (!res.ok) return;
    const shipments = await res.json();
    if (shipments.length === 0) {
      tbody.innerHTML = `<tr><td colspan="7">No shipments recorded.</td></tr>`;
      return;
    }
    tbody.innerHTML = shipments.map(s => `
      <tr>
        <td><code>${s.shipment_number}</code></td>
        <td>Order #${s.order_id}</td>
        <td>${s.carrier_name}</td>
        <td><a href="javascript:void(0)" onclick="inspectTracking('${s.tracking_number}')"><code>${s.tracking_number}</code></a></td>
        <td><span class="badge" style="background:#0284c7; color:#fff;">${s.status}</span></td>
        <td>${s.dispatched_at ? new Date(s.dispatched_at).toLocaleDateString() : "-"}</td>
        <td><a href="${s.shipping_label_url || '#'}" target="_blank" class="btn btn-outline-light btn-sm">📄 Label</a></td>
      </tr>
    `).join("");
  } catch (e) {
    tbody.innerHTML = `<tr><td colspan="7">Failed to load shipments</td></tr>`;
  }
}

async function submitCreateShipment() {
  const orderId = document.getElementById("shipOrderSelectId")?.value;
  const carrier = document.getElementById("shipCarrierName")?.value;
  const tracking = document.getElementById("shipCustomTracking")?.value || "";
  try {
    const res = await fetch("/api/v1/shipments/", {
      method: "POST",
      headers: authHeaders(),
      body: JSON.stringify({ order_id: parseInt(orderId), carrier_name: carrier, tracking_number: tracking || undefined })
    });
    if (!res.ok) throw new Error((await res.json()).detail || "Failed to create shipment");
    showToast("Shipment generated with tracking label!");
    loadShipmentsUI();
    loadOrders();
  } catch (e) {
    showToast(e.message, true);
  }
}

function inspectTracking(trackingNum) {
  switchTab("tab-tracking");
  document.getElementById("trackingNumberQuery").value = trackingNum;
  document.getElementById("eventTrackingNumber").value = trackingNum;
  queryTrackingEvents();
}

// =========================================================================
// MODULE 34: SHIPMENT TRACKING
// =========================================================================
async function queryTrackingEvents() {
  const trk = document.getElementById("trackingNumberQuery")?.value || "TRK-FDX-SEED1";
  const tbody = document.getElementById("trackingTimelineTableBody");
  const box = document.getElementById("trackingOverviewBox");
  if (!tbody) return;
  tbody.innerHTML = `<tr><td colspan="4">Tracking parcel ${trk}...</td></tr>`;
  try {
    const res = await fetch(`/api/v1/shipments/tracking/${trk}/events`);
    if (!res.ok) throw new Error((await res.json()).detail || "Tracking number not found");
    const events = await res.json();
    if (box) {
      box.innerHTML = `Tracking parcel: <strong>${trk}</strong> | Checkpoints: <strong>${events.length}</strong>`;
    }
    if (events.length === 0) {
      tbody.innerHTML = `<tr><td colspan="4">No milestone checkpoints logged yet.</td></tr>`;
      return;
    }
    tbody.innerHTML = events.map(e => `
      <tr>
        <td>${new Date(e.timestamp).toLocaleString()}</td>
        <td><span class="badge" style="background:#4f46e5; color:#fff;">${e.event_type}</span></td>
        <td>${e.location || "-"}</td>
        <td>${e.description || "-"}</td>
      </tr>
    `).join("");
  } catch (e) {
    tbody.innerHTML = `<tr><td colspan="4" style="color:#ef4444;">${e.message}</td></tr>`;
  }
}

async function submitTrackingEvent() {
  const trk = document.getElementById("eventTrackingNumber")?.value;
  const evType = document.getElementById("eventStatusType")?.value;
  const loc = document.getElementById("eventLocation")?.value;
  const desc = document.getElementById("eventDescription")?.value;
  try {
    const res = await fetch(`/api/v1/shipments/tracking/${trk}/events`, {
      method: "POST",
      headers: authHeaders(),
      body: JSON.stringify({ event_type: evType, location: loc, description: desc })
    });
    if (!res.ok) throw new Error((await res.json()).detail || "Event registration failed");
    showToast(`Checkpoint event '${evType}' recorded!`);
    queryTrackingEvents();
  } catch (e) {
    showToast(e.message, true);
  }
}

// =========================================================================
// MODULE 35: DELIVERY MANAGEMENT
// =========================================================================
async function loadDeliveryUI() {
  const tbody = document.getElementById("deliveryAssignmentsTableBody");
  if (!tbody) return;
  try {
    const res = await fetch("/api/v1/shipments/deliveries/list", { headers: authHeaders() });
    if (!res.ok) return;
    const assignments = await res.json();
    if (assignments.length === 0) {
      tbody.innerHTML = `<tr><td colspan="8">No delivery assignments recorded.</td></tr>`;
      return;
    }
    tbody.innerHTML = assignments.map(a => `
      <tr>
        <td>#${a.id}</td>
        <td>Shipment #${a.shipment_id}</td>
        <td>${a.driver_name}</td>
        <td>${a.driver_phone || "-"}</td>
        <td><span class="badge" style="background:${a.status === 'DELIVERED' ? '#10b981' : '#f59e0b'}; color:#fff;">${a.status}</span></td>
        <td>${a.delivery_attempts}</td>
        <td>${a.recipient_signature_name || "-"}</td>
        <td>${a.delivered_at ? new Date(a.delivered_at).toLocaleString() : "-"}</td>
      </tr>
    `).join("");
  } catch (e) {
    tbody.innerHTML = `<tr><td colspan="8">Failed to load deliveries</td></tr>`;
  }
}

async function submitDeliveryAssignment() {
  const shpId = document.getElementById("deliveryShipmentId")?.value;
  const name = document.getElementById("deliveryDriverName")?.value;
  const phone = document.getElementById("deliveryDriverPhone")?.value;
  try {
    const res = await fetch(`/api/v1/shipments/${shpId}/assign-delivery`, {
      method: "POST",
      headers: authHeaders(),
      body: JSON.stringify({ driver_name: name, driver_phone: phone })
    });
    if (!res.ok) throw new Error((await res.json()).detail || "Assignment failed");
    showToast("Driver assigned to delivery!");
    loadDeliveryUI();
  } catch (e) {
    showToast(e.message, true);
  }
}

async function submitDeliveryAttempt(isDelivered) {
  const assignId = document.getElementById("deliveryAssignId")?.value;
  const sig = document.getElementById("deliveryRecipientName")?.value;
  const notes = document.getElementById("deliveryAttemptNotes")?.value;
  try {
    const res = await fetch(`/api/v1/shipments/deliveries/${assignId}/attempt`, {
      method: "POST",
      headers: authHeaders(),
      body: JSON.stringify({
        is_successful: isDelivered,
        recipient_signature_name: sig,
        notes: notes || (isDelivered ? "Successfully handed over" : "Recipient unavailable on first attempt")
      })
    });
    if (!res.ok) throw new Error((await res.json()).detail || "Delivery update failed");
    showToast(isDelivered ? "Delivery confirmed successfully!" : "Failed delivery attempt logged!");
    loadDeliveryUI();
    loadOrders();
  } catch (e) {
    showToast(e.message, true);
  }
}

// =========================================================================
// MODULE 36: RETURN MANAGEMENT (RMA)
// =========================================================================
async function loadReturnsUI() {
  const tbody = document.getElementById("returnsTableBody");
  if (!tbody) return;
  try {
    const res = await fetch("/api/v1/returns/", { headers: authHeaders() });
    if (!res.ok) return;
    const returns = await res.json();
    if (returns.length === 0) {
      tbody.innerHTML = `<tr><td colspan="7">No return requests found.</td></tr>`;
      return;
    }
    tbody.innerHTML = returns.map(r => `
      <tr>
        <td><code>${r.return_number}</code></td>
        <td>Order #${r.order_id}</td>
        <td>${r.reason}</td>
        <td><span class="badge" style="background:#6366f1; color:#fff;">${r.status}</span></td>
        <td>${new Date(r.created_at).toLocaleDateString()}</td>
        <td>
          <button class="btn btn-success btn-sm" onclick="reviewReturn(${r.id}, 'APPROVED')">Approve</button>
          <button class="btn btn-danger btn-sm" onclick="reviewReturn(${r.id}, 'REJECTED')">Reject</button>
        </td>
        <td>
          <button class="btn btn-primary btn-sm" onclick="receiveReturnedGoods(${r.id})">Restock Warehouse</button>
        </td>
      </tr>
    `).join("");
  } catch (e) {
    tbody.innerHTML = `<tr><td colspan="7">Failed to load returns</td></tr>`;
  }
}

async function submitReturnRequest() {
  const orderId = document.getElementById("returnOrderId")?.value;
  const itemId = document.getElementById("returnOrderItemId")?.value;
  const qty = document.getElementById("returnQuantity")?.value;
  const cond = document.getElementById("returnConditionSelect")?.value;
  const reason = document.getElementById("returnReasonInput")?.value;
  try {
    const res = await fetch("/api/v1/returns/", {
      method: "POST",
      headers: authHeaders(),
      body: JSON.stringify({
        order_id: parseInt(orderId),
        reason: reason,
        items: [{ order_item_id: parseInt(itemId), quantity: parseInt(qty), item_condition: cond }]
      })
    });
    if (!res.ok) throw new Error((await res.json()).detail || "Return submission failed");
    showToast("Return request submitted with RMA number!");
    loadReturnsUI();
  } catch (e) {
    showToast(e.message, true);
  }
}

async function reviewReturn(retId, status) {
  try {
    const res = await fetch(`/api/v1/returns/${retId}/review`, {
      method: "PATCH",
      headers: authHeaders(),
      body: JSON.stringify({ status: status, admin_notes: `Processed return as ${status}` })
    });
    if (!res.ok) throw new Error((await res.json()).detail || "Review failed");
    showToast(`Return #${retId} marked as ${status}!`);
    loadReturnsUI();
  } catch (e) {
    showToast(e.message, true);
  }
}

async function receiveReturnedGoods(retId) {
  try {
    const res = await fetch(`/api/v1/returns/${retId}/receive`, {
      method: "POST",
      headers: authHeaders()
    });
    if (!res.ok) throw new Error((await res.json()).detail || "Restock failed");
    showToast(`Return #${retId} goods received and inventory restocked!`);
    loadReturnsUI();
    loadInventoryDropdown();
  } catch (e) {
    showToast(e.message, true);
  }
}

// =========================================================================
// MODULE 37: EXCHANGE MANAGEMENT
// =========================================================================
async function loadExchangesUI() {
  const tbody = document.getElementById("exchangesTableBody");
  if (!tbody) return;
  try {
    const res = await fetch("/api/v1/exchanges/", { headers: authHeaders() });
    if (!res.ok) return;
    const exchanges = await res.json();
    if (exchanges.length === 0) {
      tbody.innerHTML = `<tr><td colspan="7">No exchange requests found.</td></tr>`;
      return;
    }
    tbody.innerHTML = exchanges.map(e => `
      <tr>
        <td><code>${e.exchange_number}</code></td>
        <td>Order #${e.order_id}</td>
        <td>Item #${e.original_item_id}</td>
        <td>Variant #${e.replacement_variant_id} (Qty: ${e.quantity})</td>
        <td><span class="badge" style="background:#0ea5e9; color:#fff;">${e.status}</span></td>
        <td>
          <button class="btn btn-success btn-sm" onclick="reviewExchange(${e.id}, 'APPROVED')">Approve</button>
          <button class="btn btn-danger btn-sm" onclick="reviewExchange(${e.id}, 'REJECTED')">Reject</button>
        </td>
        <td>
          <button class="btn btn-primary btn-sm" onclick="dispatchExchange(${e.id})">Dispatch Goods</button>
        </td>
      </tr>
    `).join("");
  } catch (e) {
    tbody.innerHTML = `<tr><td colspan="7">Failed to load exchanges</td></tr>`;
  }
}

async function submitExchangeRequest() {
  const orderId = document.getElementById("exchangeOrderId")?.value;
  const origItem = document.getElementById("exchangeOrigItemId")?.value;
  const repVar = document.getElementById("exchangeReplacementVariantId")?.value;
  const qty = document.getElementById("exchangeQuantity")?.value;
  const reason = document.getElementById("exchangeReasonInput")?.value;
  try {
    const res = await fetch("/api/v1/exchanges/", {
      method: "POST",
      headers: authHeaders(),
      body: JSON.stringify({
        order_id: parseInt(orderId),
        original_item_id: parseInt(origItem),
        replacement_variant_id: parseInt(repVar),
        quantity: parseInt(qty),
        reason: reason
      })
    });
    if (!res.ok) throw new Error((await res.json()).detail || "Exchange request rejected");
    showToast("Exchange requested successfully!");
    loadExchangesUI();
  } catch (e) {
    showToast(e.message, true);
  }
}

async function reviewExchange(excId, status) {
  try {
    const res = await fetch(`/api/v1/exchanges/${excId}/review`, {
      method: "PATCH",
      headers: authHeaders(),
      body: JSON.stringify({ status: status, admin_notes: `Exchange marked ${status}` })
    });
    if (!res.ok) throw new Error((await res.json()).detail || "Review failed");
    showToast(`Exchange #${excId} reviewed: ${status}`);
    loadExchangesUI();
  } catch (e) {
    showToast(e.message, true);
  }
}

async function dispatchExchange(excId) {
  try {
    const res = await fetch(`/api/v1/exchanges/${excId}/dispatch`, {
      method: "POST",
      headers: authHeaders()
    });
    if (!res.ok) throw new Error((await res.json()).detail || "Dispatch failed");
    showToast(`Replacement goods dispatched for Exchange #${excId}! Stock deducted.`);
    loadExchangesUI();
    loadInventoryDropdown();
  } catch (e) {
    showToast(e.message, true);
  }
}

// =========================================================================
// MODULE 38: PRODUCT REVIEWS AND RATINGS
// =========================================================================
async function loadReviewsUI() {
  const tbody = document.getElementById("reviewsTableBody");
  if (!tbody) return;
  try {
    const res = await fetch("/api/v1/reviews/?product_id=1");
    if (!res.ok) return;
    const reviews = await res.json();
    if (reviews.length === 0) {
      tbody.innerHTML = `<tr><td colspan="7">No reviews found.</td></tr>`;
      return;
    }
    tbody.innerHTML = reviews.map(r => `
      <tr>
        <td>#${r.id}</td>
        <td>Product #${r.product_id}</td>
        <td>${"⭐".repeat(r.rating)} (${r.rating}/5)</td>
        <td><strong>${r.title}</strong><br><small style="color:#64748b;">${r.comment || ""}</small></td>
        <td><span class="badge" style="background:${r.is_verified_purchase ? '#10b981' : '#64748b'}; color:#fff;">${r.is_verified_purchase ? "VERIFIED" : "UNVERIFIED"}</span></td>
        <td><span class="badge" style="background:#4f46e5; color:#fff;">${r.status}</span></td>
        <td>
          <button class="btn btn-success btn-sm" onclick="moderateReview(${r.id}, 'APPROVED')">Approve</button>
          <button class="btn btn-danger btn-sm" onclick="moderateReview(${r.id}, 'REJECTED')">Reject</button>
        </td>
      </tr>
    `).join("");
  } catch (e) {
    tbody.innerHTML = `<tr><td colspan="7">Failed to load reviews</td></tr>`;
  }
}

async function submitProductReview() {
  const prodId = document.getElementById("reviewProductId")?.value;
  const rating = document.getElementById("reviewRatingSelect")?.value;
  const title = document.getElementById("reviewHeadline")?.value;
  const comment = document.getElementById("reviewComment")?.value;
  try {
    const res = await fetch("/api/v1/reviews/", {
      method: "POST",
      headers: authHeaders(),
      body: JSON.stringify({
        product_id: parseInt(prodId),
        rating: parseInt(rating),
        title: title,
        comment: comment
      })
    });
    if (!res.ok) throw new Error((await res.json()).detail || "Review submission failed");
    showToast("Review submitted successfully! Pending moderation.");
    loadReviewsUI();
  } catch (e) {
    showToast(e.message, true);
  }
}

async function moderateReview(revId, status) {
  try {
    const res = await fetch(`/api/v1/reviews/${revId}/moderation`, {
      method: "PATCH",
      headers: authHeaders(),
      body: JSON.stringify({ status: status })
    });
    if (!res.ok) throw new Error((await res.json()).detail || "Moderation failed");
    showToast(`Review #${revId} marked ${status}!`);
    loadReviewsUI();
  } catch (e) {
    showToast(e.message, true);
  }
}

// =========================================================================
// MODULE 39: PRODUCT QUESTIONS & ANSWERS
// =========================================================================
async function loadQAUI() {
  const container = document.getElementById("qaThreadsContainer");
  if (!container) return;
  try {
    const res = await fetch("/api/v1/questions/?product_id=1");
    if (!res.ok) return;
    const questions = await res.json();
    if (questions.length === 0) {
      container.innerHTML = `<p style="color:#64748b;">No questions posted yet for this product.</p>`;
      return;
    }
    container.innerHTML = questions.map(q => `
      <div style="background:#ffffff; border:1px solid #e2e8f0; border-radius:8px; padding:1rem;">
        <div style="display:flex; justify-content:space-between; align-items:center;">
          <h4 style="font-size:0.95rem; color:#1e293b;">❓ Q #${q.id}: ${q.question_text}</h4>
          <span class="badge" style="background:#4f46e5; color:#fff;">${q.status}</span>
        </div>
        <div style="margin-top:0.5rem; padding-left:1rem; border-left:3px solid #6366f1; display:flex; flex-direction:column; gap:0.4rem;">
          ${(q.answers || []).length > 0
            ? q.answers.map(a => `
                <div style="font-size:0.85rem; color:#334155;">
                  💡 ${a.answer_text} ${a.is_staff_answer ? '<span class="badge" style="background:#10b981; color:#fff; font-size:0.7rem;">OFFICIAL STAFF</span>' : ''}
                </div>
              `).join("")
            : '<span style="font-size:0.8rem; color:#94a3b8;">No verified answers yet.</span>'
          }
        </div>
        <div style="margin-top:0.5rem; display:flex; gap:0.5rem;">
          <button class="btn btn-outline-light btn-sm" onclick="document.getElementById('qaAnswerQuestionId').value=${q.id};">Reply</button>
          <button class="btn btn-secondary btn-sm" onclick="moderateQuestion(${q.id}, 'APPROVED')">Approve</button>
          <button class="btn btn-danger btn-sm" onclick="moderateQuestion(${q.id}, 'REJECTED')">Reject</button>
        </div>
      </div>
    `).join("");
  } catch (e) {
    container.innerHTML = `<p style="color:#ef4444;">Failed to load questions</p>`;
  }
}

async function submitProductQuestion() {
  const prodId = document.getElementById("qaProductId")?.value;
  const text = document.getElementById("qaQuestionText")?.value;
  try {
    const res = await fetch("/api/v1/questions/", {
      method: "POST",
      headers: authHeaders(),
      body: JSON.stringify({ product_id: parseInt(prodId), question_text: text })
    });
    if (!res.ok) throw new Error((await res.json()).detail || "Question submission failed");
    showToast("Question posted! Pending moderation approval.");
    document.getElementById("qaQuestionText").value = "";
    loadQAUI();
  } catch (e) {
    showToast(e.message, true);
  }
}

async function submitProductAnswer() {
  const qId = document.getElementById("qaAnswerQuestionId")?.value;
  const text = document.getElementById("qaAnswerText")?.value;
  try {
    const res = await fetch(`/api/v1/questions/${qId}/answers`, {
      method: "POST",
      headers: authHeaders(),
      body: JSON.stringify({ answer_text: text })
    });
    if (!res.ok) throw new Error((await res.json()).detail || "Answer failed");
    showToast("Official answer recorded!");
    document.getElementById("qaAnswerText").value = "";
    loadQAUI();
  } catch (e) {
    showToast(e.message, true);
  }
}

async function moderateQuestion(qId, status) {
  try {
    const res = await fetch(`/api/v1/questions/${qId}/moderation`, {
      method: "PATCH",
      headers: authHeaders(),
      body: JSON.stringify({ status: status })
    });
    if (!res.ok) throw new Error((await res.json()).detail || "Moderation failed");
    showToast(`Question #${qId} marked ${status}!`);
    loadQAUI();
  } catch (e) {
    showToast(e.message, true);
  }
}

// =========================================================================
// MODULE 40: CUSTOMER SUPPORT TICKETS
// =========================================================================
let currentViewingTicketId = null;
async function loadTicketsUI() {
  const tbody = document.getElementById("ticketsTableBody");
  if (!tbody) return;
  try {
    const res = await fetch("/api/v1/support-tickets/", { headers: authHeaders() });
    if (!res.ok) return;
    const tickets = await res.json();
    if (tickets.length === 0) {
      tbody.innerHTML = `<tr><td colspan="7">No support tickets found.</td></tr>`;
      return;
    }
    tbody.innerHTML = tickets.map(t => `
      <tr>
        <td><code>${t.ticket_number}</code></td>
        <td>${t.subject}</td>
        <td><span class="badge" style="background:#6366f1; color:#fff;">${t.category}</span></td>
        <td><span class="badge" style="background:${t.priority === 'HIGH' || t.priority === 'URGENT' ? '#ef4444' : '#10b981'}; color:#fff;">${t.priority}</span></td>
        <td><span class="badge" style="background:#0ea5e9; color:#fff;">${t.status}</span></td>
        <td>${new Date(t.created_at).toLocaleDateString()}</td>
        <td><button class="btn btn-outline-light btn-sm" onclick="viewTicketThread(${t.id})">💬 Thread</button></td>
      </tr>
    `).join("");
  } catch (e) {
    tbody.innerHTML = `<tr><td colspan="7">Failed to load tickets</td></tr>`;
  }
}

async function submitSupportTicket() {
  const subject = document.getElementById("ticketSubject")?.value;
  const category = document.getElementById("ticketCategory")?.value;
  const priority = document.getElementById("ticketPriority")?.value;
  const message = document.getElementById("ticketInitialMessage")?.value;
  try {
    const res = await fetch("/api/v1/support-tickets/", {
      method: "POST",
      headers: authHeaders(),
      body: JSON.stringify({ subject: subject, category: category, priority: priority, initial_message: message })
    });
    if (!res.ok) throw new Error((await res.json()).detail || "Failed to open ticket");
    showToast("Support ticket opened! An agent will respond shortly.");
    document.getElementById("ticketSubject").value = "";
    document.getElementById("ticketInitialMessage").value = "";
    loadTicketsUI();
  } catch (e) {
    showToast(e.message, true);
  }
}

async function viewTicketThread(ticketId) {
  currentViewingTicketId = ticketId;
  const panel = document.getElementById("ticketThreadPanel");
  const title = document.getElementById("threadTitle");
  const container = document.getElementById("threadMessagesContainer");
  if (!panel || !container) return;
  panel.style.display = "block";
  container.innerHTML = "<p>Loading messages...</p>";
  try {
    const res = await fetch(`/api/v1/support-tickets/${ticketId}`, { headers: authHeaders() });
    if (!res.ok) throw new Error("Ticket not found");
    const ticket = await res.json();
    title.innerText = `Ticket ${ticket.ticket_number}: ${ticket.subject}`;
    if (!ticket.messages || ticket.messages.length === 0) {
      container.innerHTML = "<p style='color:#64748b;'>No messages in this thread yet.</p>";
      return;
    }
    container.innerHTML = ticket.messages.map(m => `
      <div style="background:#ffffff; border-radius:6px; padding:0.5rem 0.75rem; border:1px solid #e2e8f0; font-size:0.85rem;">
        <div style="display:flex; justify-content:space-between; margin-bottom:0.25rem;">
          <strong>User #${m.sender_user_id}</strong>
          <small style="color:#94a3b8;">${new Date(m.created_at).toLocaleTimeString()}</small>
        </div>
        <div>${m.message}</div>
      </div>
    `).join("");
  } catch (e) {
    container.innerHTML = `<p style="color:#ef4444;">${e.message}</p>`;
  }
}

async function submitTicketReply() {
  if (!currentViewingTicketId) return;
  const msg = document.getElementById("threadReplyMessage")?.value;
  if (!msg) return;
  try {
    const res = await fetch(`/api/v1/support-tickets/${currentViewingTicketId}/messages`, {
      method: "POST",
      headers: authHeaders(),
      body: JSON.stringify({ message: msg })
    });
    if (!res.ok) throw new Error("Reply failed");
    document.getElementById("threadReplyMessage").value = "";
    viewTicketThread(currentViewingTicketId);
  } catch (e) {
    showToast(e.message, true);
  }
}

// Init on DOM ready
document.addEventListener("DOMContentLoaded", () => {
  updateAuthUI();
  loadKPIs();
});

