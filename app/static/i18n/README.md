# i18n (Internationalization) Setup Guide

## Overview
The ERP system now supports Arabic and English languages with full RTL (Right-to-Left) support for Arabic.

## Files Created

1. **app/static/i18n/en.json** - English translations
2. **app/static/i18n/ar.json** - Arabic translations  
3. **app/static/js/i18n.js** - i18n engine (loads translations from JSON)
4. **app/static/components/lang-switcher.html** - Language toggle button component

## How to Integrate

### Step 1: Include i18n in HTML Head
Add this to the `<head>` of every HTML page:

```html
<script src="/js/i18n.js"></script>
```

### Step 2: Add Language Switcher Button
Add this in your navbar/header (inside your existing header HTML):

```html
<!-- Language Switcher -->
<button id="langToggle" onclick="toggleLanguage()" 
  style="position: fixed; top: 12px; right: 12px; z-index: 1000; 
    background: linear-gradient(135deg, #1a73e8 0%, #0f9d58 100%);
    color: white; border: none; padding: 8px 14px; border-radius: 20px;
    cursor: pointer; font-weight: 600; font-size: 13px;">EN</button>
```

### Step 3: Mark Translatable Text with data-i18n

For any text you want to translate, add the `data-i18n` attribute with the translation key:

```html
<!-- Static text -->
<h1 data-i18n="dashboard">Dashboard</h1>
<button data-i18n="save">Save</button>

<!-- Input placeholders -->
<input type="text" data-i18n="search" data-i18n-type="placeholder" placeholder="Search">

<!-- Button titles -->
<button title="Add new record" data-i18n="add" data-i18n-type="title">+</button>

<!-- Form labels -->
<label data-i18n="email">Email</label>
```

### Step 4: Dynamic Content in JavaScript

For content generated dynamically in JavaScript, use the `t()` function:

```javascript
// Simple translation
const title = t("dashboard");
console.log(title); // "Dashboard" or "لوحة التحكم"

// In HTML string templates
document.getElementById("container").innerHTML = `
  <h2>${t("myProfile")}</h2>
  <p>${t("loading")}</p>
`;
```

### Step 5: RTL Support

The system automatically applies RTL CSS when Arabic is selected. However, you may need to adjust:

**For navbar/sidebar alignment in Arabic:**
```css
html[dir="rtl"] .navbar {
  direction: rtl;
  /* Your RTL adjustments */
}

html[dir="rtl"] .sidebar {
  float: right;
}
```

## Available Translation Keys

Common keys already included in translations:

- **Navigation**: dashboard, employee, hr, finance, procurement, inventory, asset, admin
- **Actions**: add, edit, delete, save, cancel, close, submit, approve, reject
- **Status**: pending, approved, rejected, loading
- **Modules**: allNotifications, myProfile, myAttendance, leaveManagement, payroll, etc.
- **Finance**: generalLedger, journalEntries, expenses, budgets, financialReports
- **HR**: employeeManagement, attendance, leaveManagement, contracts, performance

See `app/static/i18n/en.json` and `app/static/i18n/ar.json` for complete key list.

## Adding New Translations

1. Add the key and English text to `app/static/i18n/en.json`
2. Add the key and Arabic text to `app/static/i18n/ar.json`
3. Use `data-i18n="key"` in HTML or `t("key")` in JavaScript

Example:
```json
// en.json
{ "myNewFeature": "My New Feature" }

// ar.json
{ "myNewFeature": "ميزتي الجديدة" }

// HTML
<h2 data-i18n="myNewFeature">My New Feature</h2>

// JavaScript
alert(t("myNewFeature"));
```

## Language Storage

Current language preference is saved in `localStorage.appLang` and persists across sessions.

Default: English ("en")

## Event Listeners

When language changes, a custom event is fired:

```javascript
window.addEventListener("i18n-changed", () => {
  console.log("Language changed to:", i18n.currentLang);
  // Reload charts, refresh data if needed
});
```

## Testing

1. Open any page with i18n integrated
2. Click the language toggle button (top right)
3. Page direction should switch (LTR ↔ RTL)
4. All marked text should translate
5. Language preference persists on page reload

## Troubleshooting

**Translations not showing?**
- Ensure `data-i18n` attribute key matches exactly (case-sensitive)
- Check browser console for any errors
- Verify JSON files load: DevTools → Network → en.json, ar.json

**RTL layout broken?**
- Check CSS selectors use `html[dir="rtl"]`
- Verify flexbox/grid uses `flex-direction: row-reverse` for RTL
- Test in both languages

**Language toggle button not working?**
- Ensure `toggleLanguage()` function is available (i18n.js loaded)
- Check button's `onclick` handler
- Verify `langToggle` button ID exists

## Future Enhancements

- [ ] Add more languages (French, Spanish, etc.)
- [ ] Implement lazy loading for large translation files
- [ ] Add translation key verification script
- [ ] Implement plural forms (ar: singular, dual, plural)
- [ ] Date/number formatting per locale
