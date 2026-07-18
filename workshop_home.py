# -*- coding: utf-8 -*-
"""Rebuild the 'Home' workspace to match Mazoon ERP's landing page: 6 big
module tiles (Workshop, Sales, Purchases, Stock, Accounting, General Settings)
+ a Latest Updates tile. Reuses ERPNext's own native modules (Selling, Buying,
Stock, Invoicing already ship with ERPNext) — we only add the landing tiles."""
import json
import frappe
from frappe.workshop_futuristic import FUTURISTIC_CSS, FUTURISTIC_JS

HOME_BLOCK_NAME = "Home Dashboard Tiles"

# (label, route_csv, icon, description, gradient) — modern card per module
HOME_TILES = [
    ("ورشة صيانة السيارات", "workshop", "wrench", "بطاقات العمل والفنيون والصيانة", "linear-gradient(135deg,#16304d,#8b1a1f)"),
    ("المبيعات", "sales-dashboard", "shopping-cart", "الفواتير والعملاء ونقاط البيع", "linear-gradient(135deg,#1f9d55,#27c06b)"),
    ("المشتريات", "purchasing-dashboard", "package-plus", "الموردون وأوامر الشراء", "linear-gradient(135deg,#e67e22,#f39c12)"),
    ("المخزون", "inventory-dashboard", "layout-grid", "المنتجات والمستودعات والجرد", "linear-gradient(135deg,#8e44ad,#a55eea)"),
    ("المحاسبة", "accounting-dashboard", "receipt", "القيود والتقارير المالية", "linear-gradient(135deg,#2d6cdf,#4a90e2)"),
    ("الإعدادات العامة", "general-settings", "settings", "المستخدمون والأدوار والإعدادات", "linear-gradient(135deg,#5b6472,#7c8697)"),
]

LATEST_UPDATES_TILE = ("آخر التحديثات", "List,Notification Log", "bell", "الإشعارات وآخر المستجدات", "linear-gradient(135deg,#c0392b,#e63946)")


def _home_tiles_html():
    cells = []
    for label, route_csv, icon, desc, grad in HOME_TILES + [LATEST_UPDATES_TILE]:
        cells.append(
            '<a class="hm-card" href="#" data-route="%s">'
            '<span class="hm-icon" style="background:%s;">'
            '<svg class="icon"><use href="#icon-%s"></use></svg></span>'
            '<span class="hm-text">'
            '<span class="hm-title" data-i18n="%s">%s</span>'
            '<span class="hm-desc" data-i18n="%s">%s</span>'
            '</span>'
            '<svg class="icon hm-arrow"><use href="#icon-chevron-left"></use></svg>'
            '</a>'
            % (route_csv, grad, icon,
               frappe.utils.escape_html(label), label,
               frappe.utils.escape_html(desc), desc)
        )
    return '<div class="hm-grid">' + "".join(cells) + '</div>'


HOME_STYLE = """
.hm-wrap { direction:rtl; }
/* ---- Welcome header ---- */
.hm-header { background:linear-gradient(120deg,#16304d 0%,#1e3a5f 55%,#7a1a1f 100%);
  border-radius:18px; padding:26px 30px; color:#fff; margin-bottom:24px;
  display:flex; justify-content:space-between; align-items:center; gap:20px;
  box-shadow:0 10px 30px rgba(22,48,77,.22); position:relative; overflow:hidden; }
.hm-header::after { content:""; position:absolute; inset-inline-start:-40px; top:-40px;
  width:220px; height:220px; border-radius:50%; background:rgba(255,255,255,.06); }
.hm-hello { font-size:22px; font-weight:800; margin:0; letter-spacing:-.2px; }
.hm-sub { font-size:13.5px; opacity:.85; margin-top:6px; }
.hm-logo { height:66px; width:auto; background:#fff; border-radius:14px; padding:6px; flex-shrink:0; }
/* ---- Section title ---- */
.hm-sectitle { font-size:14px; font-weight:700; color:var(--text-color,#1a2b4a);
  letter-spacing:.15px; text-transform:uppercase;
  margin:4px 0 14px; display:flex; align-items:center; gap:8px; }
.hm-sectitle::before { content:""; width:4px; height:18px; background:#e63946; border-radius:3px; }
/* ---- Module cards grid ---- */
@keyframes kajFadeUp { from { opacity:0; transform:translateY(10px); } to { opacity:1; transform:translateY(0); } }
.hm-grid { display:grid; grid-template-columns:repeat(3,1fr); gap:16px; }
.hm-card { display:flex; align-items:center; gap:15px; background:var(--card-bg,#fff);
  border:1px solid var(--border-color,#eef0f4); border-radius:16px; padding:20px 22px;
  text-decoration:none !important; cursor:pointer; min-height:88px;
  box-shadow:0 1px 3px rgba(16,30,54,.06);
  animation:kajFadeUp .45s cubic-bezier(.2,.8,.2,1) backwards;
  transition:transform .22s cubic-bezier(.2,.8,.2,1), box-shadow .22s, border-color .22s; }
.hm-card:hover { transform:translateY(-4px); box-shadow:0 10px 24px rgba(16,30,54,.12); border-color:#dfe3ea; }
.hm-grid > .hm-card:nth-child(1){ animation-delay:.02s; } .hm-grid > .hm-card:nth-child(2){ animation-delay:.06s; }
.hm-grid > .hm-card:nth-child(3){ animation-delay:.10s; } .hm-grid > .hm-card:nth-child(4){ animation-delay:.14s; }
.hm-grid > .hm-card:nth-child(5){ animation-delay:.18s; } .hm-grid > .hm-card:nth-child(6){ animation-delay:.22s; }
.hm-grid > .hm-card:nth-child(7){ animation-delay:.26s; }
.hm-icon { width:56px; height:56px; border-radius:15px; flex-shrink:0;
  display:flex; align-items:center; justify-content:center; box-shadow:0 6px 16px rgba(0,0,0,.14); }
.hm-icon .icon { width:26px; height:26px; color:#fff; }
.hm-icon svg use { stroke:#fff; }
.hm-text { display:flex; flex-direction:column; flex:1; min-width:0; }
.hm-title { font-size:16px; font-weight:700; color:var(--text-color,#1a2b4a); }
.hm-desc { font-size:12.5px; color:var(--text-muted,#8a94a6); margin-top:3px; }
.hm-arrow { width:18px; height:18px; color:var(--text-muted,#c4ccd8); flex-shrink:0; transition:transform .2s; }
.hm-card:hover .hm-arrow { transform:translateX(-4px); color:#e63946; }
/* ---- Tablet & phone (touch-friendly) ---- */
@media (max-width:1024px){
  .hm-grid{ grid-template-columns:repeat(2,1fr); gap:14px; }
  .hm-card{ min-height:92px; padding:20px; }
  .hm-header{ padding:22px; }
}
@media (max-width:640px){
  .hm-grid{ grid-template-columns:1fr; }
  .hm-header{ flex-direction:column; text-align:center; }
  .hm-hello{ font-size:19px; }
}
/* ---- Quick search by phone number ---- */
.hm-search-box { background:var(--card-bg,#fff); border:1px solid var(--border-color,#eef0f4);
  border-radius:16px; padding:18px 20px; margin-bottom:22px; box-shadow:0 1px 3px rgba(16,30,54,.06); position:relative; }
.hm-search-title { font-size:14px; font-weight:700; color:var(--text-color,#1a2b4a); margin-bottom:10px;
  display:flex; align-items:center; gap:8px; }
.hm-search-title .icon { width:16px; height:16px; color:#e63946; }
.hm-search-row { display:flex; gap:10px; }
.hm-search-input { flex:1; border:1px solid var(--border-color,#e5e7eb); border-radius:10px;
  padding:11px 14px; font-size:14px; outline:none; background:var(--control-bg,#fff); color:var(--text-color); direction:ltr; text-align:right; }
.hm-search-input:focus { border-color:#e63946; box-shadow:0 0 0 3px rgba(230,57,70,.10); }
.hm-search-btn { border:none; background:linear-gradient(135deg,#c0392b,#e63946); color:#fff;
  padding:0 22px; border-radius:10px; font-size:14px; font-weight:700; cursor:pointer;
  display:flex; align-items:center; gap:6px; box-shadow:0 6px 16px rgba(230,57,70,.24); }
.hm-search-btn:hover { box-shadow:0 8px 20px rgba(230,57,70,.32); }
.hm-search-btn .icon { width:15px; height:15px; }
.hm-search-results { margin-top:10px; }
.hm-search-res { padding:9px 12px; font-size:13.5px; cursor:pointer; border-radius:8px;
  display:flex; justify-content:space-between; gap:10px; }
.hm-search-res:hover { background:var(--bg-light-gray,#f5f7fa); }
.hm-search-res-phone { color:var(--text-muted,#8a94a6); direction:ltr; }
.hm-search-empty { padding:10px 12px; font-size:13px; color:var(--text-muted,#8a94a6); }
.hm-profile-loading { padding:14px 0; font-size:13px; color:var(--text-muted,#8a94a6); }
.hm-customer-profile { margin-top:14px; border-top:1px solid var(--border-color,#eef0f4); padding-top:14px; }
.hm-profile-head { display:flex; align-items:center; justify-content:space-between; gap:10px; flex-wrap:wrap; margin-bottom:12px; }
.hm-profile-name { font-size:16px; font-weight:700; color:var(--text-color,#1a2b4a); }
.hm-profile-phone { font-size:13px; color:var(--text-muted,#8a94a6); direction:ltr; margin-inline-start:8px; }
.hm-profile-open { font-size:12.5px; color:#e63946; font-weight:700; text-decoration:none; cursor:pointer; }
.hm-profile-stats { display:grid; grid-template-columns:repeat(4,1fr); gap:10px; margin-bottom:16px; }
.hm-stat { background:var(--bg-light-gray,#f8f9fb); border-radius:10px; padding:10px 8px; text-align:center; }
.hm-stat-val { display:block; font-size:15px; font-weight:800; color:var(--text-color,#1a2b4a); font-variant-numeric:tabular-nums; }
.hm-stat-lbl { display:block; font-size:11px; color:var(--text-muted,#8a94a6); margin-top:3px; }
.hm-stat-danger .hm-stat-val { color:#e63946; }
.hm-profile-section-title { font-size:12.5px; font-weight:700; color:var(--text-muted,#8a94a6); margin:12px 0 6px; }
.hm-profile-chips { display:flex; flex-wrap:wrap; gap:6px; }
.hm-chip { background:var(--bg-light-gray,#f5f7fa); border:1px solid var(--border-color,#eef0f4);
  border-radius:8px; padding:5px 10px; font-size:12px; color:var(--text-color,#1a2b4a); }
.hm-profile-list { display:flex; flex-direction:column; gap:2px; }
.hm-profile-row { display:flex; align-items:center; justify-content:space-between; gap:10px;
  padding:8px 10px; border-radius:8px; cursor:pointer; font-size:13px; }
.hm-profile-row:hover { background:var(--bg-light-gray,#f5f7fa); }
.hm-badge { background:#eef1fb; color:#1a2b4a; border-radius:999px; padding:2px 10px; font-size:11.5px; font-weight:600; }
@media (max-width:640px){
  .hm-profile-stats{ grid-template-columns:repeat(2,1fr); }
  .hm-search-row{ flex-direction:column; }
}
""" + FUTURISTIC_CSS

ICON_SPRITE_JS = r"""
// SVG <use href="#icon-x"> can't resolve across a Shadow DOM boundary — fetch
// a copy of the icon sprite once (cached on window) and inject it locally.
(async function(){
  if(root.querySelector('#wsd-icon-sprite-holder')) return;
  try {
    if(!window.__wsd_icon_sprite_text){
      const resp = await fetch('/assets/frappe/icons/lucide/icons.svg');
      window.__wsd_icon_sprite_text = await resp.text();
    }
    const holder = document.createElement('div');
    holder.id = 'wsd-icon-sprite-holder';
    holder.style.display = 'none';
    holder.innerHTML = window.__wsd_icon_sprite_text;
    root.insertBefore(holder, root.firstChild);
  } catch(e){ console.error('icon sprite inject failed', e); }
})();
"""

NAV_LANG_JS = r"""
(function(){
  if(document.getElementById('kaj-lang-nav-item')) return;
  var navRight = document.querySelector('.page-icon-group') || document.querySelector('.standard-items-section');
  if(!navRight) return;

  if(!document.getElementById('kaj-lang-style')){
    var style = document.createElement('style');
    style.id = 'kaj-lang-style';
    style.textContent =
      '#kaj-lang-nav-item { position: relative; display: flex; align-items: center; }' +
      '#kaj-lang-toggle { cursor: pointer; display: flex; align-items: center; gap: 4px; ' +
      '  padding: 0 10px; height: 100%; color: var(--text-color,#333); font-size: 13px; font-weight: 600; }' +
      '#kaj-lang-toggle:hover { color: #e63946; }' +
      '#kaj-lang-menu { display:none; position:absolute; top:calc(100% + 6px); inset-inline-end:0; ' +
      '  background:var(--card-bg,#fff); border:1px solid var(--border-color,#e5e7eb); border-radius:10px; ' +
      '  box-shadow:0 10px 26px rgba(0,0,0,.15); min-width:130px; z-index:1050; overflow:hidden; }' +
      '#kaj-lang-menu a { display:block; padding:9px 16px; font-size:13px; color:var(--text-color,#333); ' +
      '  text-decoration:none; cursor:pointer; }' +
      '#kaj-lang-menu a:hover { background:var(--bg-light-gray,#f5f7fa); }' +
      '#kaj-lang-menu a.active { color:#e63946; font-weight:700; }' +
      '#kaj-logout-item { display: flex; align-items: center; }' +
      '#kaj-logout-btn { cursor: pointer; display: flex; align-items: center; gap: 5px; ' +
      '  padding: 0 10px; height: 100%; color: var(--text-color,#333); font-size: 13px; font-weight: 600; }' +
      '#kaj-logout-btn:hover { color: #e63946; }' +
      '.kaj-ico { width: 14px; height: 14px; flex-shrink: 0; }' +
      '.sidebar-header { display: none !important; }';
    document.head.appendChild(style);
  }

  function current_lang(){ return (frappe.boot && frappe.boot.lang) || 'ar'; }
  var isEn = current_lang().startsWith('en');

  var li = document.createElement('span');
  li.id = 'kaj-lang-nav-item';
  li.innerHTML =
    '<a id="kaj-lang-toggle"><span>' + (isEn ? 'English' : 'العربية') + '</span></a>' +
    '<div id="kaj-lang-menu">' +
    '  <a data-lang="ar" class="' + (isEn ? '' : 'active') + '">العربية</a>' +
    '  <a data-lang="en" class="' + (isEn ? 'active' : '') + '">English</a>' +
    '</div>';
  navRight.insertBefore(li, navRight.firstChild);

  var toggle = li.querySelector('#kaj-lang-toggle');
  var menu = li.querySelector('#kaj-lang-menu');
  toggle.addEventListener('click', function(e){
    e.preventDefault(); e.stopPropagation();
    menu.style.display = (menu.style.display === 'block') ? 'none' : 'block';
  });
  document.addEventListener('click', function(){ menu.style.display = 'none'; });
  li.querySelectorAll('[data-lang]').forEach(function(a){
    a.addEventListener('click', function(e){
      e.preventDefault();
      var lang = a.dataset.lang;
      if(lang === current_lang()) return;
      toggle.style.opacity = '0.5';
      frappe.db.set_value('User', frappe.session.user, 'language', lang).then(function(){
        window.location.reload();
      }).catch(function(){ toggle.style.opacity = '1'; });
    });
  });

  var logoutItem = document.createElement('span');
  logoutItem.id = 'kaj-logout-item';
  logoutItem.innerHTML = '<a id="kaj-logout-btn"><svg class="icon kaj-ico"><use href="#icon-log-out"></use></svg><span>' +
    (isEn ? 'Logout' : 'تسجيل الخروج') + '</span></a>';
  li.parentNode.insertBefore(logoutItem, li.nextSibling);
  logoutItem.querySelector('#kaj-logout-btn').addEventListener('click', function(e){
    e.preventDefault(); e.stopPropagation();
    frappe.confirm(
      isEn ? 'Are you sure you want to log out?' : 'هل أنت متأكد أنك تريد تسجيل الخروج؟',
      function(){
        frappe.call('logout').then(function(){ window.location.href = '/login'; });
      }
    );
  });
})();
"""

HOME_SCRIPT = """
const root = (typeof root_element !== 'undefined' && root_element) ? root_element : document;
""" + ICON_SPRITE_JS + NAV_LANG_JS + FUTURISTIC_JS + """
function translateAll(){
  root.querySelectorAll('[data-i18n]').forEach(function(el){ el.textContent = __(el.dataset.i18n); });
  root.querySelectorAll('[data-i18n-placeholder]').forEach(function(el){
    el.placeholder = __(el.dataset.i18nPlaceholder);
  });
}
translateAll();
// greeting + date + logo
try {
  const nameEl = root.querySelector('.hm-hello-name');
  if(nameEl){ nameEl.textContent = (frappe.session.user_fullname || frappe.session.user || ''); }
  const dateEl = root.querySelector('.hm-date');
  if(dateEl){ dateEl.textContent = frappe.datetime.str_to_user(frappe.datetime.now_date()); }
  const logoEl = root.querySelector('.hm-logo');
  if(logoEl){
    const lg = (frappe.boot && frappe.boot.website_settings && frappe.boot.website_settings.app_logo)
      || (frappe.boot && frappe.boot.app_logo_url) || '/files/kaj-logo1fe402.png';
    logoEl.src = lg;
  }
} catch(e){ console.error(e); }
root.querySelectorAll('.hm-card').forEach(function(a){
  a.addEventListener('click', function(e){
    e.preventDefault();
    frappe.set_route.apply(frappe, a.dataset.route.split(','));
  });
});

// ---- Quick search by phone number -> full customer profile ----
(function(){
  const input = root.querySelector('.hm-search-input');
  const btn = root.querySelector('.hm-search-btn');
  const resultsEl = root.querySelector('.hm-search-results');
  const profileEl = root.querySelector('.hm-customer-profile');
  if(!input || !btn || !resultsEl || !profileEl) return;

  function fmt(v){
    try { return frappe.format_currency(v || 0); } catch(e){ return (v || 0); }
  }

  async function showProfile(customer){
    resultsEl.innerHTML = '';
    profileEl.style.display = 'block';
    profileEl.innerHTML = '<div class="hm-profile-loading">' + __('جاري التحميل...') + '</div>';
    try {
      const [vehicles, workCards, invoices] = await Promise.all([
        frappe.db.get_list('Customer Vehicle', { filters: { customer: customer.name }, fields: ['name', 'plate_number', 'brand', 'model'], limit: 20 }),
        frappe.db.get_list('Work Card', { filters: { customer: customer.name }, fields: ['name', 'status', 'entry_date', 'plate_number'], order_by: 'creation desc', limit: 5 }),
        frappe.db.get_list('Repair Invoice', { filters: { customer: customer.name }, fields: ['name', 'grand_total', 'paid_amount', 'outstanding', 'status', 'date'], order_by: 'creation desc', limit: 10 }),
      ]);
      const totalInvoiced = invoices.reduce(function(s, i){ return s + (i.grand_total || 0); }, 0);
      const totalPaid = invoices.reduce(function(s, i){ return s + (i.paid_amount || 0); }, 0);
      const totalOutstanding = invoices.reduce(function(s, i){ return s + (i.outstanding || 0); }, 0);

      let html = '';
      html += '<div class="hm-profile-head">';
      html += '  <div><span class="hm-profile-name">' + frappe.utils.escape_html(customer.customer_name || customer.name) + '</span>';
      html += '  <span class="hm-profile-phone">' + (customer.mobile_no ? frappe.utils.escape_html(customer.mobile_no) : '') + '</span></div>';
      html += '  <a class="hm-profile-open" data-name="' + encodeURIComponent(customer.name) + '">' + __('فتح ملف العميل') + '</a>';
      html += '</div>';

      html += '<div class="hm-profile-stats">';
      html += '  <div class="hm-stat"><span class="hm-stat-val">' + vehicles.length + '</span><span class="hm-stat-lbl">' + __('المركبات') + '</span></div>';
      html += '  <div class="hm-stat"><span class="hm-stat-val">' + fmt(totalInvoiced) + '</span><span class="hm-stat-lbl">' + __('إجمالي الفواتير') + '</span></div>';
      html += '  <div class="hm-stat"><span class="hm-stat-val">' + fmt(totalPaid) + '</span><span class="hm-stat-lbl">' + __('المدفوع') + '</span></div>';
      html += '  <div class="hm-stat' + (totalOutstanding > 0 ? ' hm-stat-danger' : '') + '"><span class="hm-stat-val">' + fmt(totalOutstanding) + '</span><span class="hm-stat-lbl">' + __('المتبقي') + '</span></div>';
      html += '</div>';

      if(vehicles.length){
        html += '<div class="hm-profile-section-title">' + __('المركبات') + '</div>';
        html += '<div class="hm-profile-chips">' + vehicles.map(function(v){
          return '<span class="hm-chip">' + frappe.utils.escape_html(v.plate_number || v.name) +
            (v.brand ? ' — ' + frappe.utils.escape_html(v.brand) : '') +
            (v.model ? ' ' + frappe.utils.escape_html(v.model) : '') + '</span>';
        }).join('') + '</div>';
      }
      if(workCards.length){
        html += '<div class="hm-profile-section-title">' + __('أحدث بطاقات العمل') + '</div>';
        html += '<div class="hm-profile-list">' + workCards.map(function(w){
          return '<div class="hm-profile-row" data-dt="Work Card" data-name="' + encodeURIComponent(w.name) + '">' +
            '<span>' + w.name + (w.plate_number ? ' · ' + frappe.utils.escape_html(w.plate_number) : '') + '</span>' +
            '<span class="hm-badge">' + frappe.utils.escape_html(w.status || '') + '</span></div>';
        }).join('') + '</div>';
      }
      if(invoices.length){
        html += '<div class="hm-profile-section-title">' + __('الفواتير') + '</div>';
        html += '<div class="hm-profile-list">' + invoices.map(function(i){
          return '<div class="hm-profile-row" data-dt="Repair Invoice" data-name="' + encodeURIComponent(i.name) + '">' +
            '<span>' + i.name + ' · ' + fmt(i.grand_total) + '</span>' +
            '<span class="hm-badge">' + frappe.utils.escape_html(i.status || '') + '</span></div>';
        }).join('') + '</div>';
      }
      if(!vehicles.length && !workCards.length && !invoices.length){
        html += '<div class="hm-search-empty">' + __('لا توجد بيانات إضافية لهذا العميل بعد') + '</div>';
      }
      profileEl.innerHTML = html;

      const openLink = profileEl.querySelector('.hm-profile-open');
      if(openLink) openLink.addEventListener('click', function(e){
        e.preventDefault();
        frappe.set_route('Form', 'Customer', decodeURIComponent(openLink.dataset.name));
      });
      profileEl.querySelectorAll('.hm-profile-row').forEach(function(row){
        row.addEventListener('click', function(){
          frappe.set_route('Form', row.dataset.dt, decodeURIComponent(row.dataset.name));
        });
      });
    } catch(e){ console.error('customer profile', e); }
  }

  async function runSearch(){
    const q = (input.value || '').trim();
    resultsEl.innerHTML = '';
    profileEl.style.display = 'none';
    profileEl.innerHTML = '';
    if(!q) return;
    try {
      const [byPhone, matchingVehicles] = await Promise.all([
        frappe.db.get_list('Customer', {
          filters: [['mobile_no', 'like', '%' + q + '%']],
          fields: ['name', 'customer_name', 'mobile_no'],
          limit: 10,
        }),
        frappe.db.get_list('Customer Vehicle', {
          filters: [['plate_number', 'like', '%' + q + '%']],
          fields: ['name', 'plate_number', 'customer'],
          limit: 10,
        }),
      ]);

      let byPlate = [];
      const vehicleCustomerNames = [...new Set(matchingVehicles.map(function(v){ return v.customer; }).filter(Boolean))];
      if(vehicleCustomerNames.length){
        byPlate = await frappe.db.get_list('Customer', {
          filters: [['name', 'in', vehicleCustomerNames]],
          fields: ['name', 'customer_name', 'mobile_no'],
          limit: 10,
        });
      }

      // merge + dedupe by customer name, keep matched plate number for display
      const plateByCustomer = {};
      matchingVehicles.forEach(function(v){ if(v.customer) plateByCustomer[v.customer] = v.plate_number; });
      const merged = {};
      byPhone.forEach(function(c){ merged[c.name] = Object.assign({}, c, { matchedPlate: null }); });
      byPlate.forEach(function(c){
        merged[c.name] = Object.assign({}, merged[c.name] || c, { matchedPlate: plateByCustomer[c.name] || null });
      });
      const customers = Object.values(merged);

      if(!customers.length){
        resultsEl.innerHTML = '<div class="hm-search-empty">' + __('لا يوجد عميل أو مركبة بهذا الرقم') + '</div>';
        return;
      }
      if(customers.length === 1){
        showProfile(customers[0]);
        return;
      }
      resultsEl.innerHTML = customers.map(function(c){
        return '<div class="hm-search-res" data-name="' + encodeURIComponent(c.name) + '">' +
          '<b>' + frappe.utils.escape_html(c.customer_name || c.name) + '</b>' +
          '<span class="hm-search-res-phone">' + (c.matchedPlate ? frappe.utils.escape_html(c.matchedPlate) : (c.mobile_no ? frappe.utils.escape_html(c.mobile_no) : '')) + '</span></div>';
      }).join('');
      resultsEl.querySelectorAll('.hm-search-res').forEach(function(el){
        el.addEventListener('click', function(){
          const found = customers.find(function(c){ return c.name === decodeURIComponent(el.dataset.name); });
          if(found) showProfile(found);
        });
      });
    } catch(e){ console.error('phone/plate search', e); }
  }

  btn.addEventListener('click', runSearch);
  input.addEventListener('keydown', function(e){ if(e.key === 'Enter'){ e.preventDefault(); runSearch(); } });
})();
"""


def _make_home_block():
    html = (
        '<div class="hm-wrap" dir="rtl">'
        '  <div class="hm-header">'
        '    <div>'
        '      <div class="hm-hello"><span data-i18n="أهلاً">أهلاً</span> '
        '        <span class="hm-hello-name"></span></div>'
        '      <div class="hm-sub"><span data-i18n="مرحباً بعودتك إلى نظام خط الجزيرة">'
        'مرحباً بعودتك إلى نظام خط الجزيرة</span> · <span class="hm-date"></span></div>'
        '    </div>'
        '    <img class="hm-logo" src="/files/kaj-logo1fe402.png" alt="logo">'
        '  </div>'
        '  <div class="hm-search-box">'
        '    <div class="hm-search-title"><svg class="icon"><use href="#icon-phone"></use></svg>'
        '      <span data-i18n="بحث سريع بالجوال أو رقم اللوحة">بحث سريع بالجوال أو رقم اللوحة</span></div>'
        '    <div class="hm-search-row">'
        '      <input class="hm-search-input" type="text" data-i18n-placeholder="أدخل رقم الجوال أو رقم لوحة المركبة..." placeholder="أدخل رقم الجوال أو رقم لوحة المركبة...">'
        '      <button class="hm-search-btn"><svg class="icon"><use href="#icon-search"></use></svg>'
        '        <span data-i18n="بحث">بحث</span></button>'
        '    </div>'
        '    <div class="hm-search-results"></div>'
        '    <div class="hm-customer-profile" style="display:none"></div>'
        '  </div>'
        '  <div class="hm-sectitle" data-i18n="الوحدات الرئيسية">الوحدات الرئيسية</div>'
        + _home_tiles_html() +
        '</div>'
    )
    if frappe.db.exists("Custom HTML Block", HOME_BLOCK_NAME):
        frappe.delete_doc("Custom HTML Block", HOME_BLOCK_NAME, force=1, ignore_permissions=True)
    d = frappe.get_doc({
        "doctype": "Custom HTML Block", "name": HOME_BLOCK_NAME,
        "html": html, "style": HOME_STYLE, "script": HOME_SCRIPT,
    })
    d.insert(ignore_permissions=True)
    # An empty roles table on Custom HTML Block hides it from everyone
    # (opt-in allow-list) — must explicitly grant, same as the Workshop block.
    d.append("roles", {"role": "System Manager"})
    d.append("roles", {"role": "All"})
    d.save(ignore_permissions=True)
    frappe.db.commit()
    return d.name


def execute():
    block_name = _make_home_block()

    home = frappe.get_doc("Workspace", "Home")
    content = [
        {"id": "hwd_hdr", "type": "header",
         "data": {"text": '<span class="h4"><b>لوحة التحكم</b></span>', "col": 12}},
        {"id": "hwd_cb", "type": "custom_block",
         "data": {"custom_block_name": block_name, "col": 12}},
    ]
    home.content = json.dumps(content, ensure_ascii=False)
    home.shortcuts = []
    home.number_cards = []
    home.links = []
    home.quick_lists = []
    home.charts = []
    # IMPORTANT: block.js matches data.custom_block_name against this row's
    # `label` field (not custom_block_name) — they must be equal.
    home.custom_blocks = []
    home.append("custom_blocks", {"custom_block_name": block_name, "label": block_name})
    home.sequence_id = 1
    home.title = "لوحة التحكم"
    home.save(ignore_permissions=True)

    # Reorder sidebar to match Mazoon: Home, Settings, Accounting, Stock,
    # Buying, Selling, Workshop — then push everything else further down.
    order = [
        ("Home", 1),
        ("General Settings", 2),
        ("Accounting Dashboard", 3),
        ("Inventory Dashboard", 4),
        ("Purchasing Dashboard", 5),
        ("Sales Dashboard", 6),
        ("Workshop", 7),
    ]
    for name, seq in order:
        if frappe.db.exists("Workspace", name):
            frappe.db.set_value("Workspace", name, "sequence_id", seq)

    others = frappe.get_all("Workspace", filters={
        "public": 1, "name": ["not in", [n for n, _ in order]]
    }, pluck="name")
    for i, name in enumerate(others):
        frappe.db.set_value("Workspace", name, "sequence_id", 20 + i)

    frappe.db.commit()
    frappe.clear_cache()
    print("HOME_DONE tiles=%d others_deprioritized=%d" % (len(HOME_TILES) + 1, len(others)))
