// ── Section switcher ──────────────────────────────────
function showSection(name, el) {
  document.querySelectorAll(".section").forEach(s => s.classList.remove("active"));
  document.querySelectorAll(".menu-item").forEach(m => m.classList.remove("active"));
  document.getElementById("sec-" + name).classList.add("active");
  if (el) el.classList.add("active");
  const titleEl = document.getElementById("pageTitle");
  if (titleEl && window.PAGE_TITLES && window.PAGE_TITLES[name]) {
    titleEl.textContent = window.PAGE_TITLES[name];
  }
  if (typeof loadSection === "function") loadSection(name);
}

// ── Modal helpers ─────────────────────────────────────
function openModal(id)  { document.getElementById(id).classList.add("open"); }
function closeModal(id) { document.getElementById(id).classList.remove("open"); }

// Close modal on overlay click
document.addEventListener("click", e => {
  if (e.target.classList.contains("modal-overlay")) {
    e.target.classList.remove("open");
  }
});

// ── Table helpers ─────────────────────────────────────
function emptyRow(cols, msg = "No records found") {
  return `<tr><td colspan="${cols}" style="text-align:center;color:#64748b;padding:24px">${msg}</td></tr>`;
}

function statusBadge(status) {
  return `<span class="status ${status}">${status}</span>`;
}

// ── Init ──────────────────────────────────────────────
function initPage(role, titles) {
  requireAuth();
  if (getRole() !== role) redirectByRole(getRole());
  const nameEl = document.getElementById("sidebarName");
  if (nameEl) nameEl.textContent = getUsername();
  window.PAGE_TITLES = titles;
}