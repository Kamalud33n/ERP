// ── Enhanced Navigation System ──────────────────────────────
const navSystem = {
  currentPage: 'dashboard',
  breadcrumbs: [],
  favorites: JSON.parse(localStorage.getItem('navFavorites')) || [],

  setBreadcrumb(items) {
    this.breadcrumbs = items;
    this.renderBreadcrumb();
  },

  renderBreadcrumb() {
    const bc = document.getElementById('breadcrumb');
    if (!bc) return;
    bc.innerHTML = this.breadcrumbs.map((item, idx) => {
      const isLast = idx === this.breadcrumbs.length - 1;
      return `
        <span class="breadcrumb-item ${isLast ? 'active' : ''}">
          ${isLast ? item.label : `<a href="${item.href}">${item.label}</a>`}
          ${!isLast ? '<span class="breadcrumb-sep">/</span>' : ''}
        </span>
      `;
    }).join('');
  },

  toggleFavorite(pageName, label) {
    const idx = this.favorites.findIndex(f => f.name === pageName);
    if (idx > -1) {
      this.favorites.splice(idx, 1);
    } else {
      this.favorites.push({ name: pageName, label });
    }
    localStorage.setItem('navFavorites', JSON.stringify(this.favorites));
    this.renderFavorites();
  },

  renderFavorites() {
    const fav = document.getElementById('favoritesList');
    if (!fav) return;
    fav.innerHTML = this.favorites.length ?
      this.favorites.map(f => `
        <button class="favorite-item" onclick="navSystem.openPage('${f.name}', '${f.label}')">
          ⭐ ${f.label}
        </button>
      `).join('') :
      '<div style="color:#94a3b8;font-size:12px">No favorites yet</div>';
  },

  isFavorite(pageName) {
    return this.favorites.some(f => f.name === pageName);
  },

  openPage(section, label) {
    if (typeof showSection === 'function') {
      showSection(section, document.querySelector(`[onclick*="${section}"]`));
    }
  }
};

// ── Notification Bell System ────────────────────────────────
const notificationSystem = {
  unreadCount: 0,
  notifications: [],
  pollInterval: null,

  injectBell() {
    if (document.getElementById('notificationBell')) return;

    // Inject after favBtn — before pageTitle (confirmed from actual HTML)
    const favBtn = document.getElementById('favBtn');
    if (!favBtn) return;

    const bellHTML = `
      <div class="notif-bell-wrapper" id="notificationBell">
        <button class="notif-bell-btn" onclick="notificationSystem.toggleDropdown()" title="Notifications">
          🔔
          <span class="notif-badge" id="notifBadge" style="display:none">0</span>
        </button>
        <div class="notif-dropdown" id="notifDropdown" style="display:none">
          <div class="notif-header">
            <span>Notifications</span>
            <button class="notif-mark-all" onclick="notificationSystem.markAllRead()">Mark all read</button>
          </div>
          <div class="notif-list" id="notifList">
            <div class="notif-empty">No notifications</div>
          </div>
        </div>
      </div>
    `;

    favBtn.insertAdjacentHTML('afterend', bellHTML);

    document.addEventListener('click', (e) => {
      const bell = document.getElementById('notificationBell');
      if (bell && !bell.contains(e.target)) {
        this.closeDropdown();
      }
    });
  },

  toggleDropdown() {
    const dropdown = document.getElementById('notifDropdown');
    if (!dropdown) return;
    const isOpen = dropdown.style.display === 'block';
    if (isOpen) {
      this.closeDropdown();
    } else {
      dropdown.style.display = 'block';
      this.loadNotifications();
    }
  },

  closeDropdown() {
    const dropdown = document.getElementById('notifDropdown');
    if (dropdown) dropdown.style.display = 'none';
  },

  async fetchUnreadCount() {
    if (!getToken()) return;
    try {
      const data = await api('GET', '/notifications/count');
      if (data && typeof data.unread_count === 'number') {
        this.unreadCount = data.unread_count;
        this.updateBadge();
      }
    } catch (e) { /* silent */ }
  },

  updateBadge() {
    const badge = document.getElementById('notifBadge');
    if (!badge) return;
    if (this.unreadCount > 0) {
      badge.textContent = this.unreadCount > 99 ? '99+' : this.unreadCount;
      badge.style.display = 'flex';
    } else {
      badge.style.display = 'none';
    }
  },

  async loadNotifications() {
    if (!getToken()) return;
    const list = document.getElementById('notifList');
    if (list) list.innerHTML = '<div class="notif-empty">Loading...</div>';
    try {
      const data = await api('GET', '/notifications');
      this.notifications = Array.isArray(data) ? data : [];
      this.renderList();
    } catch (e) {
      if (list) list.innerHTML = '<div class="notif-empty">Failed to load</div>';
    }
  },

  renderList() {
    const list = document.getElementById('notifList');
    if (!list) return;
    if (this.notifications.length === 0) {
      list.innerHTML = '<div class="notif-empty">No notifications yet</div>';
      return;
    }
    const typeIcon = { success: '✅', warning: '⚠️', info: 'ℹ️', alert: '🔴' };
    list.innerHTML = this.notifications.map(n => `
      <div class="notif-item ${n.is_read ? '' : 'unread'}"
           onclick="notificationSystem.markRead(${n.id}, this)">
        <div class="notif-icon">${typeIcon[n.type] || 'ℹ️'}</div>
        <div class="notif-content">
          <div class="notif-title">${n.title}</div>
          <div class="notif-msg">${n.message}</div>
          <div class="notif-time">${this.timeAgo(n.created_at)}</div>
        </div>
        ${!n.is_read ? '<div class="notif-dot"></div>' : ''}
      </div>
    `).join('');
  },

  async markRead(id, el) {
    try {
      await api('PUT', `/notifications/${id}/read`);
      el.classList.remove('unread');
      const dot = el.querySelector('.notif-dot');
      if (dot) dot.remove();
      if (this.unreadCount > 0) {
        this.unreadCount--;
        this.updateBadge();
      }
    } catch (e) { /* silent */ }
  },

  async markAllRead() {
    try {
      await api('PUT', '/notifications/read-all');
      this.unreadCount = 0;
      this.updateBadge();
      document.querySelectorAll('.notif-item.unread').forEach(el => {
        el.classList.remove('unread');
        const dot = el.querySelector('.notif-dot');
        if (dot) dot.remove();
      });
    } catch (e) { /* silent */ }
  },

  timeAgo(dateStr) {
    if (!dateStr) return '';
    try {
      const diff = Math.floor((Date.now() - new Date(dateStr).getTime()) / 1000);
      if (isNaN(diff) || diff < 0) return '';
      if (diff < 60)    return 'Just now';
      if (diff < 3600)  return `${Math.floor(diff / 60)}m ago`;
      if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
      return `${Math.floor(diff / 86400)}d ago`;
    } catch (e) { return ''; }
  },

  startPolling() {
    this.fetchUnreadCount();
    this.pollInterval = setInterval(() => this.fetchUnreadCount(), 30000);
  },

  init() {
    if (!getToken()) return;
    this.injectBell();
    this.startPolling();
  }
};

// ── Global Search ───────────────────────────────────────────
const searchSystem = {
  items: [],

  init() {
    this.loadSearchItems();
    this.setupSearchBox();
  },

  loadSearchItems() {
    this.items = [
      { category: 'Admin',       name: 'Dashboard',         section: 'dashboard', icon: '📊' },
      { category: 'Admin',       name: 'Users',             section: 'users',     icon: '👤' },
      { category: 'Admin',       name: 'Roles',             section: 'roles',     icon: '🔐' },
      { category: 'HR',          name: 'Employees',         section: 'employees', icon: '👥' },
      { category: 'HR',          name: 'Leave Requests',    section: 'leaves',    icon: '📅' },
      { category: 'HR',          name: 'Attendance',        section: 'attendance',icon: '✅' },
      { category: 'HR',          name: 'Payroll',           section: 'payroll',   icon: '💰' },
      { category: 'Finance',     name: 'Expenses',          section: 'expenses',  icon: '🧾' },
      { category: 'Finance',     name: 'Budgets',           section: 'budgets',   icon: '📈' },
      { category: 'Finance',     name: 'General Ledger',    section: 'gl',        icon: '📒' },
      { category: 'Finance',     name: 'P&L Report',        section: 'pl',        icon: '💹' },
      { category: 'Procurement', name: 'Purchase Requests', section: 'pr',        icon: '📋' },
      { category: 'Procurement', name: 'Purchase Orders',   section: 'po',        icon: '📦' },
      { category: 'Procurement', name: 'Vendors',           section: 'vendors',   icon: '🏢' },
    ];
  },

  setupSearchBox() {
    const searchInput = document.getElementById('globalSearch');
    if (!searchInput) return;
    searchInput.addEventListener('input', (e) => {
      const query = e.target.value.toLowerCase();
      if (query.length < 2) { this.closeResults(); return; }
      this.showResults(query);
    });
    searchInput.addEventListener('blur', () => {
      setTimeout(() => this.closeResults(), 200);
    });
  },

  showResults(query) {
    const results = this.items.filter(item =>
      item.name.toLowerCase().includes(query) ||
      item.category.toLowerCase().includes(query)
    );
    const resultsDiv = document.getElementById('searchResults');
    if (!resultsDiv) return;
    if (results.length === 0) {
      resultsDiv.innerHTML = '<div style="padding:10px;color:#94a3b8;font-size:13px">No results found</div>';
      resultsDiv.style.display = 'block';
      return;
    }
    resultsDiv.innerHTML = results.map(item => `
      <div class="search-result-item"
           onclick="searchSystem.selectResult('${item.section}', '${item.name}')">
        <span class="search-icon">${item.icon}</span>
        <div class="search-info">
          <div class="search-name">${item.name}</div>
          <div class="search-category">${item.category}</div>
        </div>
      </div>
    `).join('');
    resultsDiv.style.display = 'block';
  },

  closeResults() {
    const resultsDiv = document.getElementById('searchResults');
    if (resultsDiv) resultsDiv.style.display = 'none';
  },

  selectResult(section, name) {
    const searchInput = document.getElementById('globalSearch');
    if (searchInput) searchInput.value = '';
    this.closeResults();
    if (typeof showSection === 'function') {
      const btn = document.querySelector(`[onclick*="${section}"]`);
      showSection(section, btn);
    }
  }
};

// ── Keyboard Shortcuts ──────────────────────────────────────
const keyboardShortcuts = {
  enabled: true,
  init() {
    document.addEventListener('keydown', (e) => {
      if (!this.enabled) return;
      if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault();
        document.getElementById('globalSearch')?.focus();
      }
      if (e.key === 'Escape') {
        document.querySelectorAll('.modal-overlay.open')
          .forEach(m => m.classList.remove('open'));
        const sr = document.getElementById('searchResults');
        if (sr) sr.style.display = 'none';
        notificationSystem.closeDropdown();
      }
      if ((e.ctrlKey || e.metaKey) && e.key === 'f') {
        e.preventDefault();
        document.getElementById('globalSearch')?.focus();
      }
    });
  }
};

// ── Mobile Menu ─────────────────────────────────────────────
function toggleMobileMenu() {
  const sidebar = document.querySelector('.sidebar');
  if (sidebar) sidebar.classList.toggle('mobile-open');
}

function toggleMenuSection(el) {
  const section = el.parentElement;
  const items = section.querySelectorAll('.menu-item');
  section.classList.toggle('collapsed');
  items.forEach(item => {
    item.style.display = section.classList.contains('collapsed') ? 'none' : 'block';
  });
}

// ── Init ────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  searchSystem.init();
  keyboardShortcuts.init();
  navSystem.renderFavorites();
  notificationSystem.init();
});

// ── Styles ──────────────────────────────────────────────────
const navStyles = document.createElement('style');
navStyles.innerHTML = `
  .search-results-container { position: relative; flex: 1; max-width: 400px; }
  #globalSearch {
    width: 100%; padding: 8px 12px;
    border: 1px solid #e2e8f0; border-radius: 8px;
    font-size: 14px; background: #f8fafc; transition: all 0.2s;
  }
  #globalSearch:focus {
    outline: none; background: white; border-color: #1a73e8;
    box-shadow: 0 0 0 3px rgba(26,115,232,0.1);
  }
  #searchResults {
    position: absolute; top: 100%; left: 0; right: 0;
    background: white; border: 1px solid #e2e8f0; border-radius: 8px;
    margin-top: 4px; max-height: 400px; overflow-y: auto;
    box-shadow: 0 10px 30px rgba(0,0,0,0.1); z-index: 1000; display: none;
  }
  .search-result-item {
    display: flex; align-items: center; padding: 12px;
    border-bottom: 1px solid #f1f5f9; cursor: pointer; transition: all 0.2s;
  }
  .search-result-item:hover { background: #f8fafc; }
  .search-result-item:last-child { border-bottom: none; }
  .search-icon { font-size: 20px; margin-right: 12px; }
  .search-name { font-weight: 600; font-size: 14px; color: #0f172a; }
  .search-category { font-size: 12px; color: #64748b; margin-top: 2px; }
  .breadcrumb-item { display: inline-flex; align-items: center; font-size: 13px; color: #64748b; }
  .breadcrumb-item a { color: #1a73e8; text-decoration: none; }
  .breadcrumb-item a:hover { color: #0f9d58; }
  .breadcrumb-item.active { color: #0f172a; font-weight: 600; }
  .breadcrumb-sep { margin: 0 6px; color: #cbd5e1; }
  .favorite-item {
    display: block; width: 100%; text-align: left; padding: 8px 12px;
    background: none; border: 1px solid #e2e8f0; border-radius: 6px;
    cursor: pointer; font-size: 13px; margin-bottom: 6px; transition: all 0.2s;
  }
  .favorite-item:hover { background: #f8fafc; border-color: #1a73e8; }

  /* ── Bell ── */
  .notif-bell-wrapper {
    position: relative; display: inline-flex;
    align-items: center; margin: 0 8px;
  }
  .notif-bell-btn {
    background: none; border: none; font-size: 20px; cursor: pointer;
    padding: 6px 8px; border-radius: 8px; position: relative;
    display: flex; align-items: center; transition: background 0.2s;
  }
  .notif-bell-btn:hover { background: rgba(0,0,0,0.06); }
  .notif-badge {
    position: absolute; top: 2px; right: 2px;
    background: #ef4444; color: white; border-radius: 10px;
    font-size: 10px; font-weight: 700; min-width: 16px; height: 16px;
    display: flex; align-items: center; justify-content: center;
    padding: 0 4px; pointer-events: none;
  }
  .notif-dropdown {
    position: absolute; top: calc(100% + 8px); right: 0;
    width: 340px; background: white; border: 1px solid #e2e8f0;
    border-radius: 12px; box-shadow: 0 10px 40px rgba(0,0,0,0.12);
    z-index: 2000; overflow: hidden;
  }
  .notif-header {
    display: flex; align-items: center; justify-content: space-between;
    padding: 14px 16px; border-bottom: 1px solid #f1f5f9;
    font-weight: 600; font-size: 14px; color: #0f172a;
  }
  .notif-mark-all {
    background: none; border: none; color: #1a73e8;
    font-size: 12px; cursor: pointer; padding: 0;
  }
  .notif-mark-all:hover { text-decoration: underline; }
  .notif-list { max-height: 360px; overflow-y: auto; }
  .notif-item {
    display: flex; align-items: flex-start; padding: 12px 16px;
    border-bottom: 1px solid #f8fafc; cursor: pointer;
    transition: background 0.15s; position: relative;
  }
  .notif-item:hover { background: #f8fafc; }
  .notif-item.unread { background: #eff6ff; }
  .notif-item:last-child { border-bottom: none; }
  .notif-icon { font-size: 18px; margin-right: 10px; margin-top: 1px; flex-shrink: 0; }
  .notif-content { flex: 1; min-width: 0; }
  .notif-title { font-weight: 600; font-size: 13px; color: #0f172a; margin-bottom: 2px; }
  .notif-msg {
    font-size: 12px; color: #475569; line-height: 1.4;
    white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
  }
  .notif-time { font-size: 11px; color: #94a3b8; margin-top: 4px; }
  .notif-dot {
    width: 8px; height: 8px; border-radius: 50%;
    background: #1a73e8; flex-shrink: 0; margin-top: 4px; margin-left: 6px;
  }
  .notif-empty { padding: 24px; text-align: center; color: #94a3b8; font-size: 13px; }

  /* ── Mobile ── */
  .mobile-menu-toggle { display: none; background: none; border: none; font-size: 24px; cursor: pointer; padding: 8px; }
  @media(max-width: 768px) {
    .mobile-menu-toggle { display: block; }
    .sidebar { position: fixed; left: -250px; top: 0; height: 100vh; z-index: 999; transition: left 0.3s; }
    .sidebar.mobile-open { left: 0; }
    .search-results-container { max-width: 100%; }
    .notif-dropdown { width: 300px; right: -10px; }
  }

  /* ── RTL ── */
  html[dir="rtl"] .breadcrumb-sep { margin: 0 6px; }
  html[dir="rtl"] .search-icon { margin-left: 12px; margin-right: 0; }
  html[dir="rtl"] .sidebar { left: auto; right: -250px; }
  html[dir="rtl"] .sidebar.mobile-open { right: 0; left: auto; }
  html[dir="rtl"] .notif-bell-wrapper { margin: 0 8px; }
  html[dir="rtl"] .notif-dropdown { right: auto; left: 0; }
  html[dir="rtl"] .notif-icon { margin-right: 0; margin-left: 10px; }
`;
document.head.appendChild(navStyles);