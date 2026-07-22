# -*- coding: utf-8 -*-
"""Workshop dashboard — Mazoon-style: 18 action tiles + 3 colored search boxes
+ latest work cards table (all in one Custom HTML Block), then stat cards and
the grouped menu. All DB-persisted."""
import json
import frappe
from khat_workshop.setup.workshop_futuristic import FUTURISTIC_CSS, FUTURISTIC_JS

LABEL = "Workshop"
TITLE = "ورشة الصيانة"
BLOCK_NAME = "Workshop Dashboard Search"

# 18 tiles: (label, action, target, icon, color) — action: list | new | report | single
# icon = real Frappe/Lucide icon id (rendered via <use href="#icon-NAME">, resolves
# against the sprite Frappe already injects inline into the page DOM).
# Order = RTL rows (right to left) exactly like Mazoon.
TILES = [
    ("إضافة عميل", "new", "Customer", "user-plus", "#2196f3"),
    ("العملاء", "list", "Customer", "users", "#2196f3"),
    ("إضافة مركبة", "new", "Customer Vehicle", "plus", "#00b8d9"),
    ("مركبات العملاء", "list", "Customer Vehicle", "car-front", "#00b8d9"),
    ("براندات المركبات", "list", "Vehicle Brand", "tag", "#9c27b0"),
    ("موديلات المركبات", "list", "Vehicle Model", "grid-2x2", "#9c27b0"),

    ("بطاقات العمل", "list", "Work Card", "file-text", "#318ad8"),
    ("حالات بطاقة العمل", "list", "Work Card Status", "toggle-right", "#318ad8"),
    ("عروض الأسعار", "list", "Quotation", "file", "#f4a900"),
    ("فواتير الإصلاح", "list", "Sales Invoice", "receipt", "#e67e22"),
    ("الدفعات", "list", "Payment Entry", "credit-card", "#1f9d55"),
    ("الباقات", "list", "Product Bundle", "gift", "#9c27b0"),

    ("الفنيون", "list", "Workshop Technician", "wrench", "#7c7c7c"),
    ("إعدادات الورشة", "single", "Workshop Settings", "settings", "#7c7c7c"),
    ("التقارير", "report", "تقرير الإيرادات", "chart-bar", "#318ad8"),
    ("تقرير الفنيين", "report", "تقرير الفنيين", "trending-up", "#318ad8"),
    ("سجل صرف العمولات", "list", "Commission Log", "dollar-sign", "#1f9d55"),
    ("تذكرات الصيانة", "list", "Maintenance Reminder", "bell", "#cb2929"),
]

NUMBER_CARDS = [
    ("Workshop Total Work Cards", "بطاقات العمل", "Work Card", "Count", None, "#318ad8"),
    ("Workshop Total Customers", "العملاء", "Customer", "Count", None, "#7c7c7c"),
    ("Workshop Total Vehicles", "المركبات", "Customer Vehicle", "Count", None, "#00b8d9"),
    ("Workshop Total Invoices", "فواتير الإصلاح", "Sales Invoice", "Count", None, "#e67e22"),
    # Field names follow the NATIVE doctypes now, not the retired shadow ones:
    # Workshop Payment.amount -> Payment Entry.paid_amount
    # Repair Invoice.outstanding -> Sales Invoice.outstanding_amount
    ("Workshop Total Payments", "إجمالي المدفوعات", "Payment Entry", "Sum", "paid_amount", "#1f9d55"),
    ("Workshop Outstanding", "المتبقيات", "Sales Invoice", "Sum", "outstanding_amount", "#cb2929"),
]

LINK_GROUPS = [
    ("العملاء والمركبات", [
        ("العملاء", "Customer"), ("مركبات العملاء", "Customer Vehicle"),
        ("براندات المركبات", "Vehicle Brand"), ("موديلات المركبات", "Vehicle Model"),
    ]),
    ("بطاقات العمل", [
        ("بطاقات العمل", "Work Card"), ("حالات بطاقة العمل", "Work Card Status"),
        ("الفنيون", "Workshop Technician"), ("سجل صرف العمولات", "Commission Log"),
    ]),
    ("المبيعات والمالية", [
        ("عروض الأسعار", "Quotation"), ("فواتير الإصلاح", "Sales Invoice"),
        ("الدفعات", "Payment Entry"), ("الباقات", "Product Bundle"),
    ]),
    ("المتابعة والإعدادات", [
        ("تذكرات الصيانة", "Maintenance Reminder"), ("إعدادات الورشة", "Workshop Settings"),
    ]),
]

REPORTS = ["تقرير الفنيين", "تقرير العمولات", "تقرير الإيرادات", "تقرير بطاقات العمل"]


def _tiles_html():
    cells = []
    for label, action, target, icon, color in TILES:
        cells.append(
            '<div class="wsd-tile" data-action="%s" data-target="%s">'
            '<span class="wsd-tile-lbl" data-i18n="%s">%s</span>'
            '<svg class="icon icon-sm wsd-tile-ico" style="color:%s;">'
            '<use href="#icon-%s"></use></svg></div>'
            % (action, frappe.utils.escape_html(target),
               frappe.utils.escape_html(label), label, color, icon)
        )
    return '<div class="wsd-tiles">' + "".join(cells) + '</div>'


BLOCK_SEARCH_HTML = """
  <div class="wsd-searchrow">
    <div class="wsd-box wsd-red">
      <div class="wsd-title"><svg class="icon wsd-title-ico"><use href="#icon-user"></use></svg> <span data-i18n="بحث العملاء">بحث العملاء</span></div>
      <div class="wsd-ig">
        <button class="wsd-btn wsd-btn-red" data-kind="customer"><svg class="icon wsd-btn-ico"><use href="#icon-search"></use></svg></button>
        <input class="wsd-input" data-kind="customer" data-i18n-placeholder="ابحث بالاسم أو رقم الهاتف..." placeholder="ابحث بالاسم أو رقم الهاتف...">
      </div>
      <div class="wsd-results" data-for="customer"></div>
    </div>
    <div class="wsd-box wsd-green">
      <div class="wsd-title"><svg class="icon wsd-title-ico"><use href="#icon-car-front"></use></svg> <span data-i18n="بحث المركبات">بحث المركبات</span></div>
      <div class="wsd-ig">
        <button class="wsd-btn wsd-btn-green" data-kind="vehicle"><svg class="icon wsd-btn-ico"><use href="#icon-search"></use></svg></button>
        <input class="wsd-input" data-kind="vehicle" data-i18n-placeholder="ابحث برقم اللوحة أو اسم/هاتف العميل..." placeholder="ابحث برقم اللوحة أو اسم/هاتف العميل...">
      </div>
      <div class="wsd-results" data-for="vehicle"></div>
    </div>
    <div class="wsd-box wsd-yellow">
      <div class="wsd-title"><svg class="icon wsd-title-ico"><use href="#icon-receipt"></use></svg> <span data-i18n="بحث الفواتير">بحث الفواتير</span></div>
      <div class="wsd-ig">
        <button class="wsd-btn wsd-btn-yellow" data-kind="invoice"><svg class="icon wsd-btn-ico"><use href="#icon-search"></use></svg></button>
        <input class="wsd-input" data-kind="invoice" data-i18n-placeholder="ابحث برقم الفاتورة أو اسم/هاتف العميل..." placeholder="ابحث برقم الفاتورة أو اسم/هاتف العميل...">
      </div>
      <div class="wsd-results" data-for="invoice"></div>
    </div>
  </div>
  <div class="wsd-recent">
    <div class="wsd-recent-head">
      <span><svg class="icon wsd-title-ico"><use href="#icon-clipboard-list"></use></svg> <span data-i18n="أحدث بطاقات العمل">أحدث بطاقات العمل</span></span>
      <button class="wsd-showall" data-i18n="عرض الكل">عرض الكل</button>
    </div>
    <div class="wsd-table-wrap">
    <table class="wsd-table">
      <thead><tr>
        <th data-i18n="رقم البطاقة">رقم البطاقة</th><th data-i18n="العميل">العميل</th><th data-i18n="الهاتف">الهاتف</th><th data-i18n="رقم اللوحة">رقم اللوحة</th>
        <th data-i18n="الماركة / الموديل">الماركة / الموديل</th><th data-i18n="تاريخ الدخول">تاريخ الدخول</th><th data-i18n="الحالة">الحالة</th>
      </tr></thead>
      <tbody class="wsd-tbody"><tr><td colspan="7" class="wsd-empty" data-i18n="جاري التحميل...">جاري التحميل...</td></tr></tbody>
    </table>
    </div>
  </div>
"""

BLOCK_STYLE = """
.wsd { margin: 6px 0 2px; }
@keyframes kajFadeUp { from { opacity:0; transform:translateY(10px); } to { opacity:1; transform:translateY(0); } }
.wsd-tiles { display:grid; grid-template-columns:repeat(6,1fr); gap:10px; margin-bottom:18px; direction:rtl; }
.wsd-tile { display:flex; align-items:center; justify-content:space-between; gap:8px;
  background:var(--card-bg,#fff); border:1px solid var(--border-color,#eef0f4); border-radius:13px;
  padding:14px 16px; min-height:52px; cursor:pointer; box-shadow:0 1px 3px rgba(16,30,54,.06);
  animation:kajFadeUp .4s cubic-bezier(.2,.8,.2,1) backwards;
  transition:transform .2s cubic-bezier(.2,.8,.2,1), box-shadow .2s, border-color .2s;
  -webkit-tap-highlight-color: transparent; touch-action: manipulation; }
.wsd-tile:hover, .wsd-tile:active { transform:translateY(-3px); box-shadow:0 10px 24px rgba(16,30,54,.12); border-color:#dfe3ea; }
.wsd-tile-lbl { font-size:13px; font-weight:600; color:var(--text-color,#1a2b4a); }
.wsd-tile-ico { width:19px; height:19px; flex-shrink:0; }
.wsd-title-ico { width:14px; height:14px; vertical-align:-2px; }
.wsd-btn-ico { width:15px; height:15px; }
.wsd-tiles > .wsd-tile:nth-child(1){ animation-delay:.01s; } .wsd-tiles > .wsd-tile:nth-child(2){ animation-delay:.03s; }
.wsd-tiles > .wsd-tile:nth-child(3){ animation-delay:.05s; } .wsd-tiles > .wsd-tile:nth-child(4){ animation-delay:.07s; }
.wsd-tiles > .wsd-tile:nth-child(5){ animation-delay:.09s; } .wsd-tiles > .wsd-tile:nth-child(6){ animation-delay:.11s; }
.wsd-tiles > .wsd-tile:nth-child(n+7){ animation-delay:.13s; }

/* --- Responsive breakpoints: desktop -> tablet landscape -> tablet portrait -> phone --- */
@media (max-width:1200px){ .wsd-tiles{ grid-template-columns:repeat(4,1fr);} }
@media (max-width:1024px){
  .wsd-tiles{ grid-template-columns:repeat(3,1fr); gap:8px; }
  .wsd-searchrow{ grid-template-columns:repeat(2,1fr); gap:10px; }
  .wsd-tile{ padding:14px; }
  .wsd-input, .wsd-btn{ min-height:44px; font-size:14px; }
}
@media (max-width:768px){
  .wsd-tiles{ grid-template-columns:repeat(2,1fr); }
  .wsd-searchrow{ grid-template-columns:1fr; }
  .wsd-recent-head{ flex-wrap:wrap; gap:8px; }
}
@media (max-width:480px){
  .wsd-tiles{ grid-template-columns:repeat(2,1fr); gap:6px; }
  .wsd-tile{ padding:10px; }
  .wsd-tile-lbl{ font-size:12px; }
}
.wsd-searchrow { display: grid; grid-template-columns: repeat(3, 1fr); gap: 14px; }
.wsd-box { background: var(--card-bg,#fff); border: 1px solid var(--border-color,#e5e7eb);
  border-radius: 10px; padding: 12px 14px; box-shadow: 0 1px 2px rgba(0,0,0,.04); position: relative; }
.wsd-title { font-weight: 600; font-size: 13px; margin-bottom: 8px; color: var(--text-muted,#6b7280); }
.wsd-ig { display: flex; gap: 0; }
.wsd-input { flex: 1; border: 1px solid var(--border-color,#e5e7eb); border-radius: 0 8px 8px 0;
  padding: 8px 10px; font-size: 13px; outline: none; background: var(--control-bg,#fff); color: var(--text-color); }
.wsd-btn { border: none; color: #fff; padding: 0 16px; border-radius: 8px 0 0 8px; cursor: pointer; font-size: 15px; }
.wsd-btn-red { background: #e63946; } .wsd-btn-green { background: #1f9d55; } .wsd-btn-yellow { background: #f4a900; }
.wsd-red { border-top: 3px solid #e63946; } .wsd-green { border-top: 3px solid #1f9d55; } .wsd-yellow { border-top: 3px solid #f4a900; }
.wsd-results { position: absolute; z-index: 20; right: 14px; left: 14px; background: var(--card-bg,#fff);
  border: 1px solid var(--border-color,#e5e7eb); border-top: none; border-radius: 0 0 8px 8px;
  max-height: 260px; overflow-y: auto; box-shadow: 0 6px 16px rgba(0,0,0,.10); }
.wsd-results:empty { display: none; }
.wsd-res { padding: 8px 10px; font-size: 13px; cursor: pointer; border-bottom: 1px solid var(--border-color,#f0f0f0); }
.wsd-res:hover { background: var(--bg-light-gray,#f5f7fa); }
.wsd-nores { padding: 8px 10px; font-size: 12px; color: var(--text-muted,#9ca3af); }
.wsd-recent { margin-top: 16px; background: var(--card-bg,#fff); border: 1px solid var(--border-color,#e5e7eb); border-radius: 10px; overflow: hidden; }
.wsd-recent-head { display: flex; justify-content: space-between; align-items: center; padding: 10px 14px;
  border-bottom: 1px solid var(--border-color,#e5e7eb); font-weight: 600; font-size: 14px; letter-spacing:.1px; }
.wsd-showall { border: 1px solid var(--border-color,#d1d5db); background: transparent; color: var(--text-color);
  border-radius: 6px; padding: 4px 12px; font-size: 12px; cursor: pointer; }
.wsd-showall:hover { background: var(--bg-light-gray,#f5f7fa); }
.wsd-table-wrap { width: 100%; overflow-x: auto; -webkit-overflow-scrolling: touch; }
.wsd-table { width: 100%; min-width: 640px; border-collapse: collapse; font-size: 13px; }
.wsd-table th { background: var(--bg-light-gray,#f3e8ff); text-align: right; padding: 9px 12px;
  font-weight: 600; color: var(--text-color); border-bottom: 1px solid var(--border-color,#e5e7eb); white-space: nowrap; }
.wsd-table td { padding: 9px 12px; border-bottom: 1px solid var(--border-color,#f0f0f0); text-align: right; }
.wsd-tbody tr { cursor: pointer; }
.wsd-tbody tr:hover { background: var(--bg-light-gray,#f5f7fa); }
.wsd-empty { text-align: center !important; color: var(--text-muted,#9ca3af); padding: 18px !important; }
""" + FUTURISTIC_CSS

ICON_SPRITE_JS = r"""
// SVG <use href="#icon-x"> can't resolve across a Shadow DOM boundary — the
// icon sprite Frappe injects lives in the main document, invisible to this
// block's shadow root. Fetch a copy once (cached on window) and inject it
// locally so our <use> references resolve.
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

# Injects a real language dropdown INTO Frappe's own top navbar (.navbar-right,
# the same container Frappe itself uses for the bell/help/theme/settings
# icons) — escapes this block's Shadow DOM by writing straight to
# document, so it appears beside the native icons (matching Mazoon) and,
# since the navbar is part of the persistent SPA shell (not re-rendered on
# route change), it survives in-app navigation to any other page. Guarded
# by an id check so it only gets created once no matter how many of our
# custom blocks (Home/General Settings/Accounting/.../Workshop) run it.

# Adds a "إخفاء الإحصائيات" / "عرض الإحصائيات" toggle next to the
# Statistics section header (Mazoon-style), collapsing/expanding the 6
# Number Card widgets below it. The header and the number cards are native
# Frappe Workspace blocks rendered OUTSIDE this Custom HTML Block's shadow
# root, so this reaches into `document` the same way public/js/desk.js does.
# Retries briefly since the header may render after this block's own script
# runs (Editor.js blocks mount independently, in no guaranteed order).
STATS_TOGGLE_JS = r"""
(function(){
  function tryInject(attempts){
    if(document.getElementById('kaj-stats-toggle-btn')) return;
    var header = Array.from(document.querySelectorAll('.h5')).find(function(e){ return e.textContent.trim() === 'الإحصائيات'; });
    if(!header){
      if(attempts > 0) setTimeout(function(){ tryInject(attempts - 1); }, 300);
      return;
    }
    var ceBlock = header.closest('.ce-block');
    if(!ceBlock) return;
    var cardBlocks = [];
    var sib = ceBlock.nextElementSibling;
    while(sib){
      var cls = sib.className || '';
      if(!/\bce-block\b/.test(cls)) break;
      if(cls.indexOf('col-md-4') === -1 && cls.indexOf('col-sm-6') === -1) break;
      cardBlocks.push(sib);
      sib = sib.nextElementSibling;
    }
    if(!cardBlocks.length) return;

    var STORE_KEY = 'kaj_stats_collapsed';
    var collapsed = localStorage.getItem(STORE_KEY) === '1';

    var btn = document.createElement('button');
    btn.id = 'kaj-stats-toggle-btn';
    btn.type = 'button';
    btn.style.cssText = 'margin-inline-start:12px;border:1px solid var(--border-color,#d1d5db);'
      + 'background:transparent;color:var(--text-color,#333);border-radius:6px;padding:3px 12px;'
      + 'font-size:12px;font-weight:500;cursor:pointer;vertical-align:middle;';
    function apply(){
      cardBlocks.forEach(function(b){ b.style.display = collapsed ? 'none' : ''; });
      btn.textContent = collapsed ? __('عرض الإحصائيات') : __('إخفاء الإحصائيات');
    }
    apply();
    btn.addEventListener('click', function(){
      collapsed = !collapsed;
      localStorage.setItem(STORE_KEY, collapsed ? '1' : '0');
      apply();
    });
    header.parentElement.appendChild(btn);
  }
  tryInject(15);
})();
"""

BLOCK_SCRIPT = r"""
const root = (typeof root_element !== 'undefined' && root_element) ? root_element : document;
""" + ICON_SPRITE_JS + STATS_TOGGLE_JS + FUTURISTIC_JS + r"""
function go(dt, name){ frappe.set_route('Form', dt, name); }

// ---- Action tiles navigation ----
root.querySelectorAll('.wsd-tile').forEach(function(t){
  t.addEventListener('click', function(){
    var a = t.dataset.action, tg = t.dataset.target;
    if(a === 'list') frappe.set_route('List', tg);
    else if(a === 'new') frappe.new_doc(tg);
    else if(a === 'report') frappe.set_route('query-report', tg);
    else if(a === 'single') frappe.set_route('Form', tg);
  });
});

// ---- Search boxes ----
// ---- i18n: translate this block's static text using Frappe's existing
// Translation records (same __() lookup the rest of the desk uses). ----
function translateAll(){
  root.querySelectorAll('[data-i18n]').forEach(function(el){
    el.textContent = __(el.dataset.i18n);
  });
  root.querySelectorAll('[data-i18n-placeholder]').forEach(function(el){
    el.placeholder = __(el.dataset.i18nPlaceholder);
  });
}
translateAll();

function renderResults(kind, rows){
  const box = root.querySelector('.wsd-results[data-for="'+kind+'"]');
  if(!box) return;
  if(!rows.length){ box.innerHTML = '<div class="wsd-nores">'+__('لا توجد نتائج')+'</div>'; return; }
  box.innerHTML = rows.map(function(r){
    return '<div class="wsd-res" data-dt="'+r._dt+'" data-name="'+encodeURIComponent(r._name)+'">'+frappe.utils.escape_html(r._label)+'</div>';
  }).join('');
  box.querySelectorAll('.wsd-res').forEach(function(d){
    d.addEventListener('click', function(){ go(d.dataset.dt, decodeURIComponent(d.dataset.name)); });
  });
}
async function doSearch(kind, q){
  q = (q||'').trim();
  const box = root.querySelector('.wsd-results[data-for="'+kind+'"]');
  if(!q){ if(box) box.innerHTML=''; return; }
  try {
    let rows = [];
    if(kind === 'customer'){
      const r = await frappe.db.get_list('Customer', { or_filters: [['customer_name','like','%'+q+'%'],['mobile_no','like','%'+q+'%'],['name','like','%'+q+'%']], fields:['name','customer_name','mobile_no'], limit:10 });
      rows = r.map(function(x){ return {_dt:'Customer', _name:x.name, _label:(x.customer_name||x.name)+(x.mobile_no?(' — '+x.mobile_no):'')}; });
    } else if(kind === 'vehicle'){
      const r = await frappe.db.get_list('Customer Vehicle', { or_filters: [['plate_number','like','%'+q+'%'],['customer','like','%'+q+'%']], fields:['name','plate_number','customer','brand','model'], limit:10 });
      rows = r.map(function(x){ return {_dt:'Customer Vehicle', _name:x.name, _label:(x.plate_number||x.name)+' — '+(x.customer||'')+' '+(x.brand||'')+' '+(x.model||'')}; });
    } else if(kind === 'invoice'){
      const r = await frappe.db.get_list('Sales Invoice', { or_filters: [['name','like','%'+q+'%'],['customer','like','%'+q+'%']], fields:['name','customer','grand_total','status'], limit:10 });
      rows = r.map(function(x){ return {_dt:'Sales Invoice', _name:x.name, _label:x.name+' — '+(x.customer||'')+' — '+(x.grand_total||0)+' ('+(x.status||'')+')'}; });
    }
    renderResults(kind, rows);
  } catch(e){ console.error('workshop search', e); }
}
root.querySelectorAll('.wsd-input').forEach(function(inp){
  let t;
  inp.addEventListener('input', function(){ clearTimeout(t); t = setTimeout(function(){ doSearch(inp.dataset.kind, inp.value); }, 300); });
  inp.addEventListener('keydown', function(e){ if(e.key === 'Enter'){ doSearch(inp.dataset.kind, inp.value); } });
});
root.querySelectorAll('.wsd-btn').forEach(function(b){
  b.addEventListener('click', function(){ const inp = root.querySelector('.wsd-input[data-kind="'+b.dataset.kind+'"]'); doSearch(b.dataset.kind, inp ? inp.value : ''); });
});

// ---- Latest work cards ----
async function loadRecent(){
  const tb = root.querySelector('.wsd-tbody');
  if(!tb) return;
  try {
    const r = await frappe.db.get_list('Work Card', { fields:['name','customer','customer_phone','plate_number','brand','model','entry_date','status'], order_by:'creation desc', limit:10 });
    if(!r.length){ tb.innerHTML = '<tr><td colspan="7" class="wsd-empty">'+__('لا توجد سجلات')+'</td></tr>'; return; }
    tb.innerHTML = r.map(function(x){
      const dt = x.entry_date ? frappe.datetime.str_to_user(x.entry_date) : '';
      const bm = [x.brand, x.model].filter(Boolean).join(' / ');
      const esc = frappe.utils.escape_html;
      return '<tr data-name="'+encodeURIComponent(x.name)+'">'
        + '<td>'+esc(x.name)+'</td><td>'+esc(x.customer||'')+'</td><td>'+esc(x.customer_phone||'')+'</td>'
        + '<td>'+esc(x.plate_number||'')+'</td><td>'+esc(bm)+'</td><td>'+esc(dt)+'</td>'
        + '<td>'+esc(__(x.status||''))+'</td></tr>';
    }).join('');
    tb.querySelectorAll('tr').forEach(function(tr){
      tr.addEventListener('click', function(){ go('Work Card', decodeURIComponent(tr.dataset.name)); });
    });
  } catch(e){ tb.innerHTML = '<tr><td colspan="7" class="wsd-empty">'+__('تعذّر التحميل')+'</td></tr>'; console.error(e); }
}
const showall = root.querySelector('.wsd-showall');
if(showall){ showall.addEventListener('click', function(){ frappe.set_route('List', 'Work Card'); }); }
loadRecent();
"""


def _make_number_cards():
    result = []
    for name, label, dt, func, based_on, color in NUMBER_CARDS:
        # Number Card auto-names from `label`; delete ALL existing (incl. -1/-2
        # duplicates from previous runs) to stay idempotent.
        for existing in frappe.get_all("Number Card", filters={"label": label}, pluck="name"):
            frappe.delete_doc("Number Card", existing, force=1, ignore_permissions=True)
        doc = {
            "doctype": "Number Card", "label": label,
            "type": "Document Type", "document_type": dt, "function": func,
            "is_public": 1, "show_percentage_stats": 1,
            "stats_time_interval": "Daily", "color": color, "filters_json": "[]",
        }
        if func == "Sum" and based_on:
            doc["aggregate_function_based_on"] = based_on
        d = frappe.get_doc(doc)
        d.insert(ignore_permissions=True)
        result.append((d.name, label))
    frappe.db.commit()
    return result


def _make_custom_block():
    html = ('<div class="wsd" dir="rtl">'
            + _tiles_html() + BLOCK_SEARCH_HTML + '</div>')
    if frappe.db.exists("Custom HTML Block", BLOCK_NAME):
        frappe.delete_doc("Custom HTML Block", BLOCK_NAME, force=1, ignore_permissions=True)
    d = frappe.get_doc({
        "doctype": "Custom HTML Block", "name": BLOCK_NAME,
        "html": html, "style": BLOCK_STYLE, "script": BLOCK_SCRIPT,
    })
    d.insert(ignore_permissions=True)
    try:
        d.append("roles", {"role": "System Manager"})
        d.append("roles", {"role": "Workshop Manager"})
        d.save(ignore_permissions=True)
    except Exception:
        pass
    frappe.db.commit()
    return d.name


def execute():
    if frappe.db.exists("Workspace", LABEL):
        frappe.delete_doc("Workspace", LABEL, force=1, ignore_permissions=True)
        frappe.db.commit()

    made_cards = _make_number_cards()
    block_name = _make_custom_block()

    content = [
        {"id": "hdr1", "type": "header",
         "data": {"text": '<span class="h4"><b>إدارة ورشة الصيانة</b></span>', "col": 12}},
        {"id": "cb1", "type": "custom_block",
         "data": {"custom_block_name": block_name, "col": 12}},
        {"id": "hdr_stats", "type": "header",
         "data": {"text": '<span class="h5">الإحصائيات</span>', "col": 12}},
    ]

    number_cards = []
    for idx, (name, label) in enumerate(made_cards):
        content.append({"id": "nc_%d" % idx, "type": "number_card",
                        "data": {"number_card_name": name, "col": 4}})
        number_cards.append({"number_card_name": name, "label": label})

    content.append({"id": "hdr_menu", "type": "header",
                    "data": {"text": '<span class="h5">القائمة</span>', "col": 12}})
    links = []
    for group_label, items in LINK_GROUPS:
        links.append({"type": "Card Break", "label": group_label, "hidden": 0, "onboard": 0})
        for label, dt in items:
            links.append({"type": "Link", "label": label, "link_type": "DocType",
                          "link_to": dt, "hidden": 0, "onboard": 0, "is_query_report": 0})
        content.append({"id": "card_" + frappe.scrub(group_label), "type": "card",
                        "data": {"card_name": group_label, "col": 4}})

    # Only link Reports that actually exist. These four were never created, so
    # the whole Workspace insert failed with LinkValidationError and the main
    # dashboard disappeared entirely — losing the dashboard is far worse than
    # losing four report shortcuts.
    available_reports = [r for r in REPORTS if frappe.db.exists("Report", r)]
    if available_reports:
        links.append({"type": "Card Break", "label": "التقارير", "hidden": 0, "onboard": 0})
        for rep in available_reports:
            links.append({"type": "Link", "label": rep, "link_type": "Report",
                          "link_to": rep, "is_query_report": 1, "hidden": 0, "onboard": 0})
        content.append({"id": "card_reports", "type": "card",
                        "data": {"card_name": "التقارير", "col": 4}})

    ws = frappe.get_doc({
        "doctype": "Workspace", "name": LABEL, "label": LABEL, "title": TITLE,
        "public": 1, "is_hidden": 0, "icon": "tool", "module": "Core",
        "content": json.dumps(content, ensure_ascii=False),
        "number_cards": number_cards, "shortcuts": [], "links": links,
        # IMPORTANT: block.js matches content's data.custom_block_name against
        # this row's `label` field (not custom_block_name) — they must be equal.
        "custom_blocks": [{"custom_block_name": block_name, "label": block_name}],
        "sequence_id": 1.0,
    })
    ws.insert(ignore_permissions=True)
    frappe.db.commit()
    frappe.clear_cache()
    print("FULL_DASHBOARD_DONE tiles=%d cards=%d links=%d"
          % (len(TILES), len(number_cards), len(links)))
