// ── Enhanced Navigation System ──────────────────────────────
const navSystem = {
  currentPage: 'dashboard',
  breadcrumbs: [],
  favorites: JSON.parse(localStorage.getItem('navFavorites')) || [],

  // Initialize breadcrumb navigation
  setBreadcrumb(items) {
    this.breadcrumbs = items;
    this.renderBreadcrumb();
  },

  // Render breadcrumb
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

  // Toggle favorite
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

  // Render favorites
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

  // Check if page is favorite
  isFavorite(pageName) {
    return this.favorites.some(f => f.name === pageName);
  },

  // Open page helper
  openPage(section, label) {
    if (typeof showSection === 'function') {
      showSection(section, document.querySelector(`[onclick*="${section}"]`));
    }
  }
};

// ── Global Search Function ──────────────────────────────────
const searchSystem = {
  items: [],
  
  init() {
    this.loadSearchItems();
    this.setupSearchBox();
  },

  loadSearchItems() {
    this.items = [
      // Admin
      { category: 'Admin', name: 'Dashboard', section: 'dashboard', icon: '📊' },
      { category: 'Admin', name: 'Users', section: 'users', icon: '👤' },
      { category: 'Admin', name: 'Roles', section: 'roles', icon: '🔐' },
      // HR
      { category: 'HR', name: 'Employees', section: 'employees', icon: '👥' },
      { category: 'HR', name: 'Leave Requests', section: 'leaves', icon: '📅' },
      { category: 'HR', name: 'Attendance', section: 'attendance', icon: '✅' },
      { category: 'HR', name: 'Payroll', section: 'payroll', icon: '💰' },
      // Finance
      { category: 'Finance', name: 'Expenses', section: 'expenses', icon: '🧾' },
      { category: 'Finance', name: 'Budgets', section: 'budgets', icon: '📈' },
      { category: 'Finance', name: 'General Ledger', section: 'gl', icon: '📒' },
      { category: 'Finance', name: 'P&L Report', section: 'pl', icon: '💹' },
      // Procurement
      { category: 'Procurement', name: 'Purchase Requests', section: 'pr', icon: '📋' },
      { category: 'Procurement', name: 'Purchase Orders', section: 'po', icon: '📦' },
      { category: 'Procurement', name: 'Vendors', section: 'vendors', icon: '🏢' },
    ];
  },

  setupSearchBox() {
    const searchInput = document.getElementById('globalSearch');
    if (!searchInput) return;

    searchInput.addEventListener('input', (e) => {
      const query = e.target.value.toLowerCase();
      if (query.length < 2) {
        this.closeResults();
        return;
      }
      this.showResults(query);
    });

    // Close on blur
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
      <div class="search-result-item" onclick="searchSystem.selectResult('${item.section}', '${item.name}')">
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
      
      // Ctrl+K (or Cmd+K) = Open search
      if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault();
        document.getElementById('globalSearch')?.focus();
      }
      
      // Esc = Close modals/search
      if (e.key === 'Escape') {
        document.querySelectorAll('.modal-overlay.open').forEach(m => m.classList.remove('open'));
        document.getElementById('searchResults').style.display = 'none';
      }
      
      // Ctrl+F = Focus search
      if ((e.ctrlKey || e.metaKey) && e.key === 'f') {
        e.preventDefault();
        document.getElementById('globalSearch')?.focus();
      }
    });
  }
};

// ── Mobile Menu Toggle ──────────────────────────────────────
function toggleMobileMenu() {
  const sidebar = document.querySelector('.sidebar');
  if (sidebar) {
    sidebar.classList.toggle('mobile-open');
  }
}

// ── Menu Collapse/Expand ────────────────────────────────────
function toggleMenuSection(el) {
  const section = el.parentElement;
  const items = section.querySelectorAll('.menu-item');
  section.classList.toggle('collapsed');
  items.forEach(item => {
    item.style.display = section.classList.contains('collapsed') ? 'none' : 'block';
  });
}

// Initialize on DOM load
document.addEventListener('DOMContentLoaded', () => {
  searchSystem.init();
  keyboardShortcuts.init();
  navSystem.renderFavorites();
});

// Style for search results
const searchStyle = document.createElement('style');
searchStyle.innerHTML = `
  .search-results-container {
    position: relative;
    flex: 1;
    max-width: 400px;
  }

  #globalSearch {
    width: 100%;
    padding: 8px 12px;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    font-size: 14px;
    background: #f8fafc;
    transition: all 0.2s;
  }

  #globalSearch:focus {
    outline: none;
    background: white;
    border-color: #1a73e8;
    box-shadow: 0 0 0 3px rgba(26, 115, 232, 0.1);
  }

  #searchResults {
    position: absolute;
    top: 100%;
    left: 0;
    right: 0;
    background: white;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    margin-top: 4px;
    max-height: 400px;
    overflow-y: auto;
    box-shadow: 0 10px 30px rgba(0,0,0,0.1);
    z-index: 1000;
    display: none;
  }

  .search-result-item {
    display: flex;
    align-items: center;
    padding: 12px;
    border-bottom: 1px solid #f1f5f9;
    cursor: pointer;
    transition: all 0.2s;
  }

  .search-result-item:hover {
    background: #f8fafc;
  }

  .search-result-item:last-child {
    border-bottom: none;
  }

  .search-icon {
    font-size: 20px;
    margin-right: 12px;
  }

  .search-info {
    flex: 1;
  }

  .search-name {
    font-weight: 600;
    font-size: 14px;
    color: #0f172a;
  }

  .search-category {
    font-size: 12px;
    color: #64748b;
    margin-top: 2px;
  }

  .breadcrumb-item {
    display: inline-flex;
    align-items: center;
    font-size: 13px;
    color: #64748b;
  }

  .breadcrumb-item a {
    color: #1a73e8;
    text-decoration: none;
    transition: color 0.2s;
  }

  .breadcrumb-item a:hover {
    color: #0f9d58;
  }

  .breadcrumb-item.active {
    color: #0f172a;
    font-weight: 600;
  }

  .breadcrumb-sep {
    margin: 0 6px;
    color: #cbd5e1;
  }

  .favorite-item {
    display: block;
    width: 100%;
    text-align: left;
    padding: 8px 12px;
    background: none;
    border: 1px solid #e2e8f0;
    border-radius: 6px;
    cursor: pointer;
    font-size: 13px;
    margin-bottom: 6px;
    transition: all 0.2s;
  }

  .favorite-item:hover {
    background: #f8fafc;
    border-color: #1a73e8;
  }

  .mobile-menu-toggle {
    display: none;
    background: none;
    border: none;
    font-size: 24px;
    cursor: pointer;
    padding: 8px;
  }

  @media(max-width: 768px) {
    .mobile-menu-toggle {
      display: block;
    }

    .sidebar {
      position: fixed;
      left: -250px;
      top: 0;
      height: 100vh;
      z-index: 999;
      transition: left 0.3s;
    }

    .sidebar.mobile-open {
      left: 0;
    }

    .search-results-container {
      max-width: 100%;
    }
  }

  /* RTL Support */
  html[dir="rtl"] .breadcrumb-sep {
    margin: 0 6px;
  }

  html[dir="rtl"] .search-icon {
    margin-left: 12px;
    margin-right: 0;
  }

  html[dir="rtl"] .sidebar {
    left: auto;
    right: -250px;
  }

  html[dir="rtl"] .sidebar.mobile-open {
    right: 0;
    left: auto;
  }
`;
document.head.appendChild(searchStyle);
