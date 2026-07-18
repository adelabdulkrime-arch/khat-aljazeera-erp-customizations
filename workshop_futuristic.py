# -*- coding: utf-8 -*-
"""Shared 'futuristic 2035' design layer: glass/neon hover glow + mouse-tracked
3D tilt on our custom tiles, plus a global Ctrl+/ command palette that jumps
to any tile across all 7 dashboards. Imported (not duplicated) by every
workshop_*.py dashboard builder, since they all live in the same package."""
import json

COMMANDS = [
    {"label": "ورشة صيانة السيارات", "label_en": "Vehicle Repair Workshop", "action": "page", "target": "workshop", "icon": "wrench", "source": "الرئيسية", "source_en": "Home"},
    {"label": "المبيعات", "label_en": "Sales", "action": "page", "target": "sales-dashboard", "icon": "shopping-cart", "source": "الرئيسية", "source_en": "Home"},
    {"label": "المشتريات", "label_en": "Purchases", "action": "page", "target": "purchasing-dashboard", "icon": "package-plus", "source": "الرئيسية", "source_en": "Home"},
    {"label": "المخزون", "label_en": "Stock", "action": "page", "target": "inventory-dashboard", "icon": "layout-grid", "source": "الرئيسية", "source_en": "Home"},
    {"label": "المحاسبة", "label_en": "Accounting", "action": "page", "target": "accounting-dashboard", "icon": "receipt", "source": "الرئيسية", "source_en": "Home"},
    {"label": "الإعدادات العامة", "label_en": "General Settings", "action": "page", "target": "general-settings", "icon": "settings", "source": "الرئيسية", "source_en": "Home"},
    {"label": "آخر التحديثات", "label_en": "Latest Updates", "action": "list", "target": "Notification Log", "icon": "bell", "source": "الرئيسية", "source_en": "Home"},

    {"label": "إضافة عميل", "label_en": "Add Customer", "action": "new", "target": "Customer", "icon": "user-plus", "source": "الورشة", "source_en": "Workshop"},
    {"label": "العملاء", "label_en": "Customers", "action": "list", "target": "Customer", "icon": "users", "source": "الورشة", "source_en": "Workshop"},
    {"label": "إضافة مركبة", "label_en": "Add Vehicle", "action": "new", "target": "Customer Vehicle", "icon": "plus", "source": "الورشة", "source_en": "Workshop"},
    {"label": "مركبات العملاء", "label_en": "Customer Vehicles", "action": "list", "target": "Customer Vehicle", "icon": "car-front", "source": "الورشة", "source_en": "Workshop"},
    {"label": "براندات المركبات", "label_en": "Vehicle Brands", "action": "list", "target": "Vehicle Brand", "icon": "tag", "source": "الورشة", "source_en": "Workshop"},
    {"label": "موديلات المركبات", "label_en": "Vehicle Models", "action": "list", "target": "Vehicle Model", "icon": "grid-2x2", "source": "الورشة", "source_en": "Workshop"},
    {"label": "بطاقات العمل", "label_en": "Work Cards", "action": "list", "target": "Work Card", "icon": "file-text", "source": "الورشة", "source_en": "Workshop"},
    {"label": "حالات بطاقة العمل", "label_en": "Work Card Statuses", "action": "list", "target": "Work Card Status", "icon": "toggle-right", "source": "الورشة", "source_en": "Workshop"},
    {"label": "عروض الأسعار", "label_en": "Quotations", "action": "list", "target": "Workshop Quotation", "icon": "file", "source": "الورشة", "source_en": "Workshop"},
    {"label": "فواتير الإصلاح", "label_en": "Repair Invoices", "action": "list", "target": "Repair Invoice", "icon": "receipt", "source": "الورشة", "source_en": "Workshop"},
    {"label": "الدفعات", "label_en": "Payments", "action": "list", "target": "Workshop Payment", "icon": "credit-card", "source": "الورشة", "source_en": "Workshop"},
    {"label": "الباقات", "label_en": "Packages", "action": "list", "target": "Service Package", "icon": "gift", "source": "الورشة", "source_en": "Workshop"},
    {"label": "الفنيون", "label_en": "Technicians", "action": "list", "target": "Workshop Technician", "icon": "wrench", "source": "الورشة", "source_en": "Workshop"},
    {"label": "إعدادات الورشة", "label_en": "Workshop Settings", "action": "single", "target": "Workshop Settings", "icon": "settings", "source": "الورشة", "source_en": "Workshop"},
    {"label": "سجل صرف العمولات", "label_en": "Commission Log", "action": "list", "target": "Commission Log", "icon": "dollar-sign", "source": "الورشة", "source_en": "Workshop"},
    {"label": "تذكرات الصيانة", "label_en": "Maintenance Reminders", "action": "list", "target": "Maintenance Reminder", "icon": "bell", "source": "الورشة", "source_en": "Workshop"},

    {"label": "الأدوار", "label_en": "Roles", "action": "page", "target": "roles-dashboard", "icon": "shield-user", "source": "الإعدادات", "source_en": "Settings"},
    {"label": "المستخدمون", "label_en": "Users", "action": "page", "target": "users-dashboard", "icon": "users", "source": "الإعدادات", "source_en": "Settings"},
    {"label": "أدوار جهات الاتصال", "label_en": "Contact Roles", "action": "list", "target": "Contact Role", "icon": "id-card", "source": "الإعدادات", "source_en": "Settings"},
    {"label": "جهات الاتصال", "label_en": "Contacts", "action": "list", "target": "Contact", "icon": "contact", "source": "الإعدادات", "source_en": "Settings"},
    {"label": "الحقول المخصصة", "label_en": "Custom Fields", "action": "list", "target": "Custom Field", "icon": "list-plus", "source": "الإعدادات", "source_en": "Settings"},
    {"label": "نسخة احتياطية", "label_en": "Backup", "action": "page", "target": "backups", "icon": "file-down", "source": "الإعدادات", "source_en": "Settings"},
    {"label": "قوالب الطباعة", "label_en": "Print Templates", "action": "list", "target": "Letter Head", "icon": "printer", "source": "الإعدادات", "source_en": "Settings"},
    {"label": "الدول", "label_en": "Countries", "action": "list", "target": "Country", "icon": "globe", "source": "الإعدادات", "source_en": "Settings"},
    {"label": "سجل نشاط النظام", "label_en": "System Activity Log", "action": "list", "target": "Activity Log", "icon": "history", "source": "الإعدادات", "source_en": "Settings"},

    {"label": "عروض أسعار الخدمات", "label_en": "Service Quotations", "action": "list", "target": "Quotation", "icon": "file", "source": "المحاسبة", "source_en": "Accounting"},
    {"label": "إشعارات الدائن", "label_en": "Credit Notes", "action": "list", "target": "Sales Invoice", "icon": "receipt", "source": "المحاسبة", "source_en": "Accounting"},
    {"label": "مدفوعات فواتير الخدمات", "label_en": "Service Invoice Payments", "action": "list", "target": "Payment Entry", "icon": "credit-card", "source": "المحاسبة", "source_en": "Accounting"},
    {"label": "فواتير الخدمات", "label_en": "Service Invoices", "action": "list", "target": "Sales Invoice", "icon": "receipt", "source": "المحاسبة", "source_en": "Accounting"},
    {"label": "إضافة فاتورة خدمات", "label_en": "Add Service Invoice", "action": "new", "target": "Sales Invoice", "icon": "plus", "source": "المحاسبة", "source_en": "Accounting"},
    {"label": "الشيكات", "label_en": "Cheques", "action": "list", "target": "Journal Entry", "icon": "credit-card", "source": "المحاسبة", "source_en": "Accounting"},
    {"label": "فئات المصروفات", "label_en": "Expense Categories", "action": "list", "target": "Account", "icon": "tag", "source": "المحاسبة", "source_en": "Accounting"},
    {"label": "سندات الصرف", "label_en": "Payment Vouchers", "action": "list", "target": "Payment Entry", "icon": "dollar-sign", "source": "المحاسبة", "source_en": "Accounting"},
    {"label": "سندات القبض", "label_en": "Receipt Vouchers", "action": "list", "target": "Payment Entry", "icon": "dollar-sign", "source": "المحاسبة", "source_en": "Accounting"},
    {"label": "فواتير المصروفات", "label_en": "Expense Invoices", "action": "list", "target": "Journal Entry", "icon": "file-text", "source": "المحاسبة", "source_en": "Accounting"},
    {"label": "مدفوعات المشتريات", "label_en": "Purchase Payments", "action": "list", "target": "Payment Entry", "icon": "credit-card", "source": "المحاسبة", "source_en": "Accounting"},
    {"label": "المشتريات", "label_en": "Purchases", "action": "list", "target": "Purchase Invoice", "icon": "receipt", "source": "المحاسبة", "source_en": "Accounting"},
    {"label": "الموردون", "label_en": "Suppliers", "action": "list", "target": "Supplier", "icon": "truck", "source": "المحاسبة", "source_en": "Accounting"},
    {"label": "الرصيد الافتتاحي", "label_en": "Opening Balance", "action": "page", "target": "opening-invoice-creation-tool", "icon": "file-plus", "source": "المحاسبة", "source_en": "Accounting"},
    {"label": "الشجرة المحاسبية", "label_en": "Chart of Accounts", "action": "tree", "target": "Account", "icon": "chart-bar", "source": "المحاسبة", "source_en": "Accounting"},
    {"label": "إضافة قيد يدوي", "label_en": "Add Manual Journal Entry", "action": "new", "target": "Journal Entry", "icon": "plus", "source": "المحاسبة", "source_en": "Accounting"},
    {"label": "القيود", "label_en": "Journal Entries", "action": "list", "target": "Journal Entry", "icon": "file-text", "source": "المحاسبة", "source_en": "Accounting"},
    {"label": "التسويات البنكية", "label_en": "Bank Reconciliation", "action": "page", "target": "bank-reconciliation-tool", "icon": "credit-card", "source": "المحاسبة", "source_en": "Accounting"},
    {"label": "الفترات المحاسبية", "label_en": "Accounting Periods", "action": "list", "target": "Accounting Period", "icon": "calendar", "source": "المحاسبة", "source_en": "Accounting"},
    {"label": "طرق الدفع", "label_en": "Payment Methods", "action": "list", "target": "Mode of Payment", "icon": "credit-card", "source": "المحاسبة", "source_en": "Accounting"},
    {"label": "الأصول", "label_en": "Assets", "action": "list", "target": "Asset", "icon": "wrench", "source": "المحاسبة", "source_en": "Accounting"},
    {"label": "أرصدة النقدية والبنوك", "label_en": "Cash & Bank Balances", "action": "list", "target": "Bank Account", "icon": "dollar-sign", "source": "المحاسبة", "source_en": "Accounting"},
    {"label": "التدفقات النقدية", "label_en": "Cash Flow", "action": "report", "target": "Cash Flow", "icon": "trending-up", "source": "المحاسبة", "source_en": "Accounting"},
    {"label": "مستحقات الموردين", "label_en": "Supplier Payables", "action": "report", "target": "Accounts Payable", "icon": "receipt", "source": "المحاسبة", "source_en": "Accounting"},
    {"label": "مديونيات العملاء", "label_en": "Customer Receivables", "action": "report", "target": "Accounts Receivable", "icon": "receipt", "source": "المحاسبة", "source_en": "Accounting"},
    {"label": "المركز المالي", "label_en": "Balance Sheet", "action": "report", "target": "Balance Sheet", "icon": "chart-bar", "source": "المحاسبة", "source_en": "Accounting"},

    {"label": "المستودعات", "label_en": "Warehouses", "action": "list", "target": "Warehouse", "icon": "warehouse", "source": "المخزون", "source_en": "Stock"},
    {"label": "البراندات", "label_en": "Brands", "action": "list", "target": "Brand", "icon": "tag", "source": "المخزون", "source_en": "Stock"},
    {"label": "مجموعات الأصناف", "label_en": "Item Groups", "action": "list", "target": "Item Group", "icon": "layout-grid", "source": "المخزون", "source_en": "Stock"},
    {"label": "وحدات القياس", "label_en": "Units of Measure", "action": "list", "target": "UOM", "icon": "wrench", "source": "المخزون", "source_en": "Stock"},
    {"label": "الأصناف", "label_en": "Items", "action": "list", "target": "Item", "icon": "package-plus", "source": "المخزون", "source_en": "Stock"},
    {"label": "نقاط البيع", "label_en": "POS Profiles", "action": "list", "target": "POS Profile", "icon": "credit-card", "source": "المخزون", "source_en": "Stock"},
    {"label": "حركات المخزون", "label_en": "Stock Entries", "action": "list", "target": "Stock Entry", "icon": "truck", "source": "المخزون", "source_en": "Stock"},
    {"label": "تسوية المخزون", "label_en": "Stock Reconciliation", "action": "list", "target": "Stock Reconciliation", "icon": "file-check", "source": "المخزون", "source_en": "Stock"},
    {"label": "الدفعات (Batch)", "label_en": "Batches", "action": "list", "target": "Batch", "icon": "layout-grid", "source": "المخزون", "source_en": "Stock"},
    {"label": "تقرير رصيد المخزون", "label_en": "Stock Balance Report", "action": "report", "target": "Stock Balance", "icon": "chart-bar", "source": "المخزون", "source_en": "Stock"},

    {"label": "طلبات الشراء", "label_en": "Material Requests", "action": "list", "target": "Material Request", "icon": "file-text", "source": "المشتريات", "source_en": "Purchasing"},
    {"label": "أوامر الشراء", "label_en": "Purchase Orders", "action": "list", "target": "Purchase Order", "icon": "shopping-cart", "source": "المشتريات", "source_en": "Purchasing"},
    {"label": "إشعارات الاستلام", "label_en": "Purchase Receipts", "action": "list", "target": "Purchase Receipt", "icon": "truck", "source": "المشتريات", "source_en": "Purchasing"},
    {"label": "فواتير المورد", "label_en": "Supplier Invoices", "action": "list", "target": "Purchase Invoice", "icon": "receipt", "source": "المشتريات", "source_en": "Purchasing"},
    {"label": "مدفوعات الموردين", "label_en": "Supplier Payments", "action": "list", "target": "Payment Entry", "icon": "credit-card", "source": "المشتريات", "source_en": "Purchasing"},
    {"label": "مرتجعات الشراء", "label_en": "Purchase Returns", "action": "list", "target": "Purchase Invoice", "icon": "trending-down", "source": "المشتريات", "source_en": "Purchasing"},
    {"label": "الموردون", "label_en": "Suppliers", "action": "list", "target": "Supplier", "icon": "users", "source": "المشتريات", "source_en": "Purchasing"},
    {"label": "تقارير المشتريات", "label_en": "Purchase Reports", "action": "report", "target": "Purchase Analytics", "icon": "chart-bar", "source": "المشتريات", "source_en": "Purchasing"},

    {"label": "عروض الأسعار", "label_en": "Quotations", "action": "list", "target": "Quotation", "icon": "file", "source": "المبيعات", "source_en": "Sales"},
    {"label": "أوامر البيع", "label_en": "Sales Orders", "action": "list", "target": "Sales Order", "icon": "shopping-cart", "source": "المبيعات", "source_en": "Sales"},
    {"label": "أذون التسليم", "label_en": "Delivery Notes", "action": "list", "target": "Delivery Note", "icon": "truck", "source": "المبيعات", "source_en": "Sales"},
    {"label": "فواتير البيع", "label_en": "Sales Invoices", "action": "list", "target": "Sales Invoice", "icon": "receipt", "source": "المبيعات", "source_en": "Sales"},
    {"label": "سندات القبض", "label_en": "Receipt Vouchers", "action": "list", "target": "Payment Entry", "icon": "dollar-sign", "source": "المبيعات", "source_en": "Sales"},
    {"label": "مرتجعات المبيعات", "label_en": "Sales Returns", "action": "list", "target": "Sales Invoice", "icon": "trending-down", "source": "المبيعات", "source_en": "Sales"},
    {"label": "تقارير المبيعات", "label_en": "Sales Reports", "action": "report", "target": "Sales Analytics", "icon": "chart-bar", "source": "المبيعات", "source_en": "Sales"},
    {"label": "نقطة البيع", "label_en": "Point of Sale", "action": "page", "target": "point-of-sale", "icon": "credit-card", "source": "المبيعات", "source_en": "Sales"},
    {"label": "إدارة الورديات", "label_en": "Shift Management", "action": "list", "target": "POS Opening Entry", "icon": "history", "source": "المبيعات", "source_en": "Sales"},
    {"label": "العملاء", "label_en": "Customers", "action": "list", "target": "Customer", "icon": "users", "source": "المبيعات", "source_en": "Sales"},
]

FUTURISTIC_CSS = """
/* ==== Futuristic 2035 design layer ==== */
.hm-card, .acd-tile, .wsd-tile, .gsd-tile {
  position: relative; transform-style: preserve-3d;
  transition: transform .18s cubic-bezier(.2,.8,.2,1), box-shadow .25s;
  will-change: transform;
}
.hm-card::before, .acd-tile::before, .wsd-tile::before, .gsd-tile::before {
  content:""; position:absolute; inset:0; border-radius:inherit; z-index:0;
  background: radial-gradient(220px circle at var(--mx,50%) var(--my,50%), rgba(230,57,70,.16), transparent 65%);
  opacity:0; transition:opacity .3s; pointer-events:none;
}
.hm-card:hover::before, .acd-tile:hover::before, .wsd-tile:hover::before, .gsd-tile:hover::before { opacity:1; }
.hm-card:hover, .acd-tile:hover, .wsd-tile:hover, .gsd-tile:hover {
  box-shadow: 0 16px 36px rgba(16,30,54,.18), 0 0 0 1px rgba(230,57,70,.22), 0 0 26px rgba(230,57,70,.22) !important;
}
.hm-card > *, .acd-tile > *, .wsd-tile > *, .gsd-tile > * { position:relative; z-index:1; }
"""

# NOTE: the command palette overlay lives in the MAIN document (document.body),
# not inside the Custom HTML Block's shadow root -- so its CSS can't go in
# FUTURISTIC_CSS above (that only reaches the shadow root). It's injected via
# a real <style> tag appended to document.head instead, same pattern as
# NAV_LANG_JS's #kaj-lang-style, inside FUTURISTIC_JS_TEMPLATE below.
CMDK_HEAD_CSS = """
#kaj-cmdk-trigger { display:flex; align-items:center; }
#kaj-cmdk-trigger-btn { cursor:pointer; display:flex; align-items:center; gap:5px;
  padding:0 10px; height:100%; color:var(--text-color,#333); font-size:13px; font-weight:600; }
#kaj-cmdk-trigger-btn:hover { color:#e63946; }
#kaj-cmdk-overlay { position:fixed; inset:0; background:rgba(10,16,28,.55); backdrop-filter:blur(4px);
  z-index:99999; display:none; align-items:flex-start; justify-content:center; padding-top:12vh; }
#kaj-cmdk-overlay.active { display:flex; }
#kaj-cmdk-box { width:min(560px, 90vw); background:rgba(20,28,45,.92); backdrop-filter:blur(18px);
  border:1px solid rgba(230,57,70,.35); border-radius:16px;
  box-shadow:0 30px 80px rgba(0,0,0,.5), 0 0 40px rgba(230,57,70,.15);
  overflow:hidden; color:#fff; }
#kaj-cmdk-input-wrap { display:flex; align-items:center; gap:10px; padding:14px 18px;
  border-bottom:1px solid rgba(255,255,255,.08); }
#kaj-cmdk-input { flex:1; background:transparent; border:none; outline:none; color:#fff;
  font-size:15px; direction:rtl; }
#kaj-cmdk-input::placeholder { color:rgba(255,255,255,.4); }
#kaj-cmdk-list { max-height:360px; overflow-y:auto; padding:8px; }
.kaj-cmdk-item { display:flex; align-items:center; gap:10px; padding:10px 12px; border-radius:10px;
  cursor:pointer; font-size:13.5px; }
.kaj-cmdk-item.active, .kaj-cmdk-item:hover { background:rgba(230,57,70,.22); }
.kaj-cmdk-item .kaj-cmdk-src { margin-inline-start:auto; font-size:11px; color:rgba(255,255,255,.4); }
.kaj-cmdk-icon { width:16px; height:16px; flex-shrink:0; color:#e63946; }
#kaj-cmdk-empty { padding:24px; text-align:center; color:rgba(255,255,255,.4); font-size:13px; }
#kaj-cmdk-hint { padding:8px 18px; font-size:11px; color:rgba(255,255,255,.35);
  border-top:1px solid rgba(255,255,255,.08); }
"""

FUTURISTIC_JS_TEMPLATE = r"""
(function(){
  // ---- 3D tilt on hover (mouse-tracked, works inside shadow root or document) ----
  var tiltSel = '.hm-card, .acd-tile, .wsd-tile, .gsd-tile';
  function attachTilt(el){
    if(el.dataset.kajTilt) return; el.dataset.kajTilt = '1';
    el.addEventListener('mousemove', function(e){
      var r = el.getBoundingClientRect();
      var x = (e.clientX - r.left) / r.width;
      var y = (e.clientY - r.top) / r.height;
      el.style.setProperty('--mx', (x*100)+'%');
      el.style.setProperty('--my', (y*100)+'%');
      var rx = (0.5 - y) * 7;
      var ry = (x - 0.5) * 7;
      el.style.transform = 'perspective(700px) rotateX('+rx.toFixed(2)+'deg) rotateY('+ry.toFixed(2)+'deg) translateY(-3px)';
    });
    el.addEventListener('mouseleave', function(){ el.style.transform = ''; });
  }
  function scanTilt(){
    var scope = (typeof root !== 'undefined' && root && root.querySelectorAll) ? root : document;
    scope.querySelectorAll(tiltSel).forEach(attachTilt);
  }
  scanTilt();
  setTimeout(scanTilt, 400);
  setTimeout(scanTilt, 1200);

  // ---- Command palette (build once globally, lives in main document) ----
  if(document.getElementById('kaj-cmdk-overlay')) return;

  if(!document.getElementById('kaj-cmdk-head-style')){
    var cmdkStyle = document.createElement('style');
    cmdkStyle.id = 'kaj-cmdk-head-style';
    cmdkStyle.textContent = __CMDK_CSS_JSON__;
    document.head.appendChild(cmdkStyle);
  }

  var COMMANDS = __COMMANDS_JSON__;
  function kajLang(){ return ((frappe.boot && frappe.boot.lang) || 'ar').startsWith('en') ? 'en' : 'ar'; }

  var overlay = document.createElement('div');
  overlay.id = 'kaj-cmdk-overlay';
  overlay.dir = kajLang() === 'en' ? 'ltr' : 'rtl';
  overlay.innerHTML =
    '<div id="kaj-cmdk-box">' +
    '  <div id="kaj-cmdk-input-wrap">' +
    '    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#e63946" stroke-width="2"><circle cx="11" cy="11" r="7"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>' +
    '    <input id="kaj-cmdk-input" placeholder="' + (kajLang()==='en' ? 'Search for any action or page...' : 'ابحث عن أي إجراء أو صفحة...') + '" autocomplete="off">' +
    '  </div>' +
    '  <div id="kaj-cmdk-list"></div>' +
    '  <div id="kaj-cmdk-hint">' + (kajLang()==='en'
      ? '&uarr;&darr; to navigate &middot; Enter to open &middot; Esc to close'
      : '↑↓ للتنقل &middot; Enter للفتح &middot; Esc للإغلاق') + '</div>' +
    '</div>';
  document.body.appendChild(overlay);

  var input = overlay.querySelector('#kaj-cmdk-input');
  var listEl = overlay.querySelector('#kaj-cmdk-list');
  var activeIndex = 0;
  var filtered = [];

  function render(query){
    var isEn = kajLang() === 'en';
    var q = (query || '').trim();
    filtered = !q ? COMMANDS.slice(0, 30) : COMMANDS.filter(function(c){
      var text = isEn ? c.label_en : c.label;
      return text.toLowerCase().indexOf(q.toLowerCase()) !== -1;
    }).slice(0, 30);
    activeIndex = 0;
    if(!filtered.length){
      listEl.innerHTML = '<div id="kaj-cmdk-empty">' + (isEn ? 'No results found' : 'لا توجد نتائج') + '</div>';
      return;
    }
    listEl.innerHTML = filtered.map(function(c, i){
      return '<div class="kaj-cmdk-item' + (i===0 ? ' active' : '') + '" data-idx="'+i+'">' +
        '<svg class="kaj-cmdk-icon" viewBox="0 0 24 24"><use href="#icon-' + (c.icon||'chevron-left') + '"></use></svg>' +
        '<span>' + (isEn ? c.label_en : c.label) + '</span>' +
        '<span class="kaj-cmdk-src">' + (isEn ? c.source_en : c.source) + '</span>' +
      '</div>';
    }).join('');
  }

  function highlight(){
    listEl.querySelectorAll('.kaj-cmdk-item').forEach(function(el, i){
      el.classList.toggle('active', i === activeIndex);
    });
    var activeEl = listEl.querySelector('.kaj-cmdk-item.active');
    if(activeEl) activeEl.scrollIntoView({block:'nearest'});
  }

  function runCommand(cmd){
    if(!cmd) return;
    close();
    if(cmd.action === 'list') frappe.set_route('List', cmd.target);
    else if(cmd.action === 'new') frappe.new_doc(cmd.target);
    else if(cmd.action === 'report') frappe.set_route('query-report', cmd.target);
    else if(cmd.action === 'tree') frappe.set_route('Tree', cmd.target);
    else if(cmd.action === 'page') frappe.set_route(cmd.target);
    else if(cmd.action === 'single') frappe.set_route('Form', cmd.target, cmd.target);
  }

  function open(){
    overlay.classList.add('active');
    input.value = '';
    render('');
    setTimeout(function(){ input.focus(); }, 30);
  }
  function close(){ overlay.classList.remove('active'); }

  input.addEventListener('input', function(){ render(input.value); highlight(); });
  listEl.addEventListener('click', function(e){
    var item = e.target.closest('.kaj-cmdk-item');
    if(item) runCommand(filtered[+item.dataset.idx]);
  });
  overlay.addEventListener('click', function(e){ if(e.target === overlay) close(); });

  document.addEventListener('keydown', function(e){
    if((e.ctrlKey || e.metaKey) && e.key === '/'){
      e.preventDefault();
      overlay.classList.contains('active') ? close() : open();
      return;
    }
    if(!overlay.classList.contains('active')) return;
    if(e.key === 'Escape'){ close(); }
    else if(e.key === 'ArrowDown'){ e.preventDefault(); activeIndex = Math.min(activeIndex+1, filtered.length-1); highlight(); }
    else if(e.key === 'ArrowUp'){ e.preventDefault(); activeIndex = Math.max(activeIndex-1, 0); highlight(); }
    else if(e.key === 'Enter'){ e.preventDefault(); runCommand(filtered[activeIndex]); }
  });

  var navRight = document.querySelector('.page-icon-group') || document.querySelector('.standard-items-section');
  if(navRight && !document.getElementById('kaj-cmdk-trigger')){
    var btn = document.createElement('span');
    btn.id = 'kaj-cmdk-trigger';
    btn.title = kajLang() === 'en' ? 'Command Palette (Ctrl+/)' : 'لوحة الأوامر (Ctrl+/)';
    btn.innerHTML = '<a id="kaj-cmdk-trigger-btn">⚡ <span>Ctrl+/</span></a>';
    navRight.insertBefore(btn, navRight.firstChild);
    btn.querySelector('#kaj-cmdk-trigger-btn').addEventListener('click', function(e){
      e.preventDefault(); open();
    });
  }
})();
"""

# Global (not tied to any one form): the Customer "Quick Entry" popup (the
# lightweight +New dialog opened from a Customer Link field, e.g. on Work
# Card) is a plain frappe.ui.Dialog with NO frm behind it -- a Client Script
# on 'Customer' via frappe.ui.form.on never fires inside it. So this hooks
# in at the DOM level instead: once the typed name exactly matches an
# existing customer, pull their phone + primary address into this dialog
# too (per explicit user choice -- yes, saving still creates a second
# Customer record; they preferred convenience over blocking a duplicate).
CUSTOMER_QUICKENTRY_JS = r"""
(function(){
  if(window.__kaj_customer_qe_hooked) return;
  window.__kaj_customer_qe_hooked = true;
  document.addEventListener('blur', function(e){
    var input = e.target;
    if(!input || input.tagName !== 'INPUT') return;
    if(!input.closest('[data-fieldname="customer_name"]')) return;
    var d = window.cur_dialog;
    if(!d || !d.fields_dict || !d.fields_dict.mobile_number) return;
    var name = (d.get_value('customer_name') || '').trim();
    if(!name || name.length < 2) return;
    frappe.db.get_list('Customer', {
      filters: [['customer_name', 'like', '%' + name + '%']],
      fields: ['name', 'customer_name'], limit: 2,
    }).then(function(matches){
      if(!matches || !matches.length) return;
      // Only auto-fill when the partial name resolves to exactly ONE existing
      // customer -- if it's ambiguous (e.g. multiple "محمد"s), don't guess.
      if(matches.length > 1) return;
      var existingName = matches[0].name;
      frappe.db.get_value('Customer', existingName, 'mobile_no').then(function(r){
        var phone = r.message && r.message.mobile_no;
        if(phone) d.set_value('mobile_number', phone);
      });
      frappe.db.get_list('Address', {
        filters: [
          ['Dynamic Link', 'link_doctype', '=', 'Customer'],
          ['Dynamic Link', 'link_name', '=', existingName],
        ],
        fields: ['address_line1', 'address_line2', 'city', 'state', 'pincode', 'country'],
        limit: 1,
      }).then(function(addrs){
        if(!addrs || !addrs.length) return;
        var a = addrs[0];
        if(a.address_line1) d.set_value('address_line1', a.address_line1);
        if(a.address_line2) d.set_value('address_line2', a.address_line2);
        if(a.city) d.set_value('city', a.city);
        if(a.state) d.set_value('state', a.state);
        if(a.pincode) d.set_value('pincode', a.pincode);
        if(a.country) d.set_value('country_address', a.country);
        frappe.show_alert({message: __('تم جلب بيانات عميل موجود مسبقاً بنفس الاسم'), indicator: 'blue'});
      });
    });
  }, true);
})();
"""

FUTURISTIC_JS = (
    FUTURISTIC_JS_TEMPLATE
    .replace("__COMMANDS_JSON__", json.dumps(COMMANDS, ensure_ascii=False))
    .replace("__CMDK_CSS_JSON__", json.dumps(CMDK_HEAD_CSS, ensure_ascii=False))
) + CUSTOMER_QUICKENTRY_JS
