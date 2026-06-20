// ── i18n System - Load from JSON files ─────────────────────
const i18n = {
  currentLang: localStorage.getItem("appLang") || "en",
  translations: {},

  // Initialize i18n
  async init() {
    try {
      const [en, ar] = await Promise.all([
        fetch("/i18n/en.json").then(r => r.json()),
        fetch("/i18n/ar.json").then(r => r.json())
      ]);
      this.translations.en = en;
      this.translations.ar = ar;
      this.applyLanguage(this.currentLang);
    } catch (e) {
      console.warn("i18n: Could not load translation files, using fallback");
      this.translations = this.getFallbackTranslations();
      this.applyLanguage(this.currentLang);
    }
  },

  // Get translation
  t(key, fallback = key) {
    const lang = this.translations[this.currentLang] || this.translations.en || {};
    return lang[key] || fallback;
  },

  // Switch language
  switchLanguage(lang) {
    if (lang !== "en" && lang !== "ar") return;
    this.currentLang = lang;
    localStorage.setItem("appLang", lang);
    this.applyLanguage(lang);
  },

  // Apply language to page
  applyLanguage(lang) {
    const root = document.documentElement;
    root.lang = lang;
    root.dir = lang === "ar" ? "rtl" : "ltr";

    // Apply RTL CSS if Arabic
    const rtlStyle = document.getElementById("rtl-styles");
    if (lang === "ar") {
      if (!rtlStyle) {
        const style = document.createElement("style");
        style.id = "rtl-styles";
        style.innerHTML = `
          html, body { direction: rtl; text-align: right; }
          .sidebar, .navbar, .header { direction: rtl; }
          .btn, button { margin: 0 2px; }
          input, textarea, select { text-align: right; direction: rtl; }
          .modal-content, .card { direction: rtl; }
          table { direction: rtl; }
          .text-left { text-align: right; }
          .text-right { text-align: left; }
          .float-left { float: right; }
          .float-right { float: left; }
          .ml-auto { margin-left: 0; margin-right: auto; }
          .mr-auto { margin-right: 0; margin-left: auto; }
        `;
        document.head.appendChild(style);
      }
    } else {
      if (rtlStyle) rtlStyle.remove();
    }

    // Translate all elements
    document.querySelectorAll("[data-i18n]").forEach(el => {
      const key = el.getAttribute("data-i18n");
      const type = el.getAttribute("data-i18n-type") || "text";
      const trans = this.t(key);
      
      if (type === "placeholder") el.placeholder = trans;
      else if (type === "title") el.title = trans;
      else if (type === "value") el.value = trans;
      else el.textContent = trans;
    });

    // Update lang toggle button
    const langBtn = document.getElementById("langToggle");
    if (langBtn) langBtn.textContent = lang === "ar" ? "EN" : "AR";

    // Dispatch event for dynamic translations
    window.dispatchEvent(new Event("i18n-changed"));
  },

  // Fallback translations (inline)
  getFallbackTranslations() {
    return {
      en: { logout: "Logout", save: "Save", cancel: "Cancel", loading: "Loading..." },
      ar: { logout: "تسجيل الخروج", save: "حفظ", cancel: "إلغاء", loading: "جاري التحميل..." }
    };
  }
};

// ── Backward compatibility functions ───────────────────────
function applyTranslations() {
  i18n.applyLanguage(i18n.currentLang);
}

function toggleLanguage() {
  const next = i18n.currentLang === "en" ? "ar" : "en";
  i18n.switchLanguage(next);
  location.reload();
}

function t(key) {
  return i18n.t(key);
}

// Initialize on DOMContentLoaded
if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", () => i18n.init());
} else {
  i18n.init();
}