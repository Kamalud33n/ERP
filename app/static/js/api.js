const BASE_URL = "/api/v1";

function getToken()    { return localStorage.getItem("erp_token"); }
function getRole()     { return localStorage.getItem("erp_role"); }
function getUsername() { return localStorage.getItem("erp_username"); }

function setAuth(token, role, username) {
  localStorage.clear();
  localStorage.setItem("erp_token",    token);
  localStorage.setItem("erp_role",     role);
  localStorage.setItem("erp_username", username);
}

function clearAuth() {
  localStorage.removeItem("erp_token");
  localStorage.removeItem("erp_role");
  localStorage.removeItem("erp_username");
}

async function api(method, endpoint, body = null) {
  const headers = { "Content-Type": "application/json" };
  const token = getToken();
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const options = { method, headers };
  if (body) options.body = JSON.stringify(body);

  const res = await fetch(`${BASE_URL}${endpoint}`, options);
  const data = await res.json();

  if (res.status === 401) {
    clearAuth();
    window.location.href = "/";
    return;
  }

  if (!res.ok) throw new Error(data.detail || "Something went wrong");
  return data;
}

function redirectByRole(role) {
  const routes = {
    admin:      "/admin.html",
    hr_manager: "/hr.html",
    finance:    "/finance.html",
    employee:   "/employee.html"
  };
  window.location.href = routes[role] || "/";
}

function requireAuth() {
  if (!getToken()) window.location.href = "/";
}

function logout() {
  clearAuth();
  window.location.href = "/";
}