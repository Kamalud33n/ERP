// ── Translation Dictionary ──────────────────────────────
const translations = {
  en: {
    // Common
    app_name:        "ERP System",
    app_tagline:     "Enterprise Resource Planning",
    logout:          "Logout",
    save:            "Save",
    cancel:          "Cancel",
    update:          "Update",
    delete:          "Delete",
    edit:            "Edit",
    add:             "Add",
    submit:          "Submit",
    close:           "Close",
    loading:         "Loading...",
    actions:         "Actions",
    status:          "Status",
    date:            "Date",
    description:     "Description",

    // Login Page
    sign_in:         "Sign in to your account",
    email_address:   "Email Address",
    password:        "Password",
    sign_in_btn:     "Sign In",
    no_account:      "Don't have an account?",
    register_link:   "Register",

    // Register Page
    create_account:  "Create an account",
    username:        "Username",
    role:            "Role",
    create_account_btn: "Create Account",
    have_account:    "Already have an account?",
    sign_in_link:    "Sign In",
    role_employee:   "Employee",
    role_hr:         "HR Manager",
    role_finance:    "Finance",
    role_admin:      "Admin",

    // Sidebar / Navigation
    dashboard:       "Dashboard",
    employees:       "Employees",
    leave_requests:  "Leave Requests",
    attendance:      "Attendance",
    payroll:         "Payroll",
    contracts:       "Contracts",
    performance:     "Performance",
    documents:       "Documents",
    expenses:        "Expenses",
    budgets:         "Budgets",
    general_ledger:  "General Ledger",
    journal_entries: "Journal Entries",
    pl_report:       "P&L Report",
    cash_flow:       "Cash Flow",
    expense_analysis:"Expense Analysis",
    procurement:     "Procurement",
    inventory:       "Inventory",
    assets:          "Assets",
    user_management: "User Management",
    audit_log:       "Audit Log",
  },

  ar: {
    // Common
    app_name:        "نظام تخطيط الموارد",
    app_tagline:     "تخطيط موارد المؤسسة",
    logout:          "تسجيل الخروج",
    save:            "حفظ",
    cancel:          "إلغاء",
    update:          "تحديث",
    delete:          "حذف",
    edit:            "تعديل",
    add:             "إضافة",
    submit:          "إرسال",
    close:           "إغلاق",
    loading:         "جار التحميل...",
    actions:         "الإجراءات",
    status:          "الحالة",
    date:            "التاريخ",
    description:     "الوصف",

    // Login Page
    sign_in:         "تسجيل الدخول إلى حسابك",
    email_address:   "البريد الإلكتروني",
    password:        "كلمة المرور",
    sign_in_btn:      "تسجيل الدخول",
    no_account:      "ليس لديك حساب؟",
    register_link:   "تسجيل جديد",

    // Register Page
    create_account:  "إنشاء حساب جديد",
    username:        "اسم المستخدم",
    role:            "الوظيفة",
    create_account_btn: "إنشاء الحساب",
    have_account:    "لديك حساب بالفعل؟",
    sign_in_link:    "تسجيل الدخول",
    role_employee:   "موظف",
    role_hr:         "مدير الموارد البشرية",
    role_finance:    "المالية",
    role_admin:      "مدير النظام",

    // Sidebar / Navigation
    dashboard:       "لوحة التحكم",
    employees:       "الموظفون",
    leave_requests:  "طلبات الإجازة",
    attendance:      "الحضور",
    payroll:         "الرواتب",
    contracts:       "العقود",
    performance:     "تقييم الأداء",
    documents:       "المستندات",
    expenses:        "المصروفات",
    budgets:         "الموازنات",
    general_ledger:  "دفتر الأستاذ العام",
    journal_entries: "القيود اليومية",
    pl_report:       "تقرير الأرباح والخسائر",
    cash_flow:       "التدفق النقدي",
    expense_analysis:"تحليل المصروفات",
    procurement:     "المشتريات",
    inventory:       "المخزون",
    assets:          "الأصول",
    user_management: "إدارة المستخدمين",
    audit_log:       "سجل النشاطات",
  }
};

// ── Apply Translations to Page ───────────────────────────
function applyTranslations() {
  const lang = localStorage.getItem("erp_lang") || "en";
  const dict = translations[lang] || translations.en;

  // Set direction
  document.documentElement.setAttribute("dir", lang === "ar" ? "rtl" : "ltr");
  document.documentElement.setAttribute("lang", lang);

  // Translate all elements with data-i18n attribute
  document.querySelectorAll("[data-i18n]").forEach(el => {
    const key = el.getAttribute("data-i18n");
    if (dict[key]) {
      el.textContent = dict[key];
    }
  });

  // Translate placeholders
  document.querySelectorAll("[data-i18n-placeholder]").forEach(el => {
    const key = el.getAttribute("data-i18n-placeholder");
    if (dict[key]) {
      el.placeholder = dict[key];
    }
  });

  // Update toggle button label
  const toggleBtn = document.getElementById("langToggle");
  if (toggleBtn) {
    toggleBtn.textContent = lang === "ar" ? "EN" : "AR";
  }
}

// ── Toggle Language ───────────────────────────────────────
function toggleLanguage() {
  const current = localStorage.getItem("erp_lang") || "en";
  const next    = current === "en" ? "ar" : "en";
  localStorage.setItem("erp_lang", next);
  applyTranslations();
}

// Get current translation for use in JS (e.g., dynamic content)
function t(key) {
  const lang = localStorage.getItem("erp_lang") || "en";
  const dict = translations[lang] || translations.en;
  return dict[key] || key;
}

// Apply on page load
document.addEventListener("DOMContentLoaded", applyTranslations);