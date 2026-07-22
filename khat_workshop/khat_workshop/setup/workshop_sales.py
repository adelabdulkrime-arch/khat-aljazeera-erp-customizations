# -*- coding: utf-8 -*-
"""Build 'المبيعات' (Sales) dashboard matching Mazoon's screen — stat cards +
flat tile grid, all routed to native ERPNext Selling module features
(Quotation/Sales Order/Delivery Note/Sales Invoice/POS/Customer)."""
import json
import frappe
from khat_workshop.setup.workshop_futuristic import FUTURISTIC_CSS, FUTURISTIC_JS

WS_NAME = "Sales Dashboard"
WS_TITLE = "المبيعات"
BLOCK_NAME = "Sales Dashboard Tiles"

# action: list | page | report
TILES = [
    ("عروض الأسعار", "list", "Quotation", "file", None),
    ("أوامر البيع", "list", "Sales Order", "shopping-cart", None),
    ("أذون التسليم", "list", "Delivery Note", "truck", None),
    ("فواتير البيع", "list", "Sales Invoice", "receipt", {"is_return": 0}),
    ("سندات القبض", "list", "Payment Entry", "dollar-sign", {"payment_type": "Receive"}),
    ("مرتجعات المبيعات", "list", "Sales Invoice", "trending-down", {"is_return": 1}),
    ("التقارير", "report", "Sales Analytics", "chart-bar", None),
    ("نقطة البيع", "page", "point-of-sale", "credit-card", None),
    ("عرض الفواتير", "list", "Sales Invoice", "receipt", None),
    ("إدارة الورديات", "list", "POS Opening Entry", "history", None),
    ("العملاء", "list", "Customer", "users", None),
]

NUMBER_CARDS = [
    ("Sales Pending Orders", "أوامر البيع المعلقة", "Sales Order", "Count", None, "#cb2929"),
    ("Sales Receivables", "الذمم المدينة", "Sales Invoice", "Sum", "outstanding_amount", "#e67e22"),
    ("Sales Total Amount", "إجمالي المبيعات", "Sales Invoice", "Sum", "grand_total", "#1f9d55"),
    ("Sales Total Customers", "العملاء", "Customer", "Count", None, "#7c7c7c"),
]

TRANSLATIONS = [
    ("المبيعات", "Sales"),
    ("عروض الأسعار", "Quotations"),
    ("أوامر البيع", "Sales Orders"),
    ("أذون التسليم", "Delivery Notes"),
    ("فواتير البيع", "Sales Invoices"),
    ("سندات القبض", "Receipt Vouchers"),
    ("مرتجعات المبيعات", "Sales Returns"),
    ("نقطة البيع", "Point of Sale"),
    ("عرض الفواتير", "View Invoices"),
    ("إدارة الورديات", "Shift Management"),
    ("أوامر البيع المعلقة", "Pending Sales Orders"),
    ("الذمم المدينة", "Receivables"),
]

STYLE = """
@keyframes kajFadeUp { from { opacity:0; transform:translateY(10px); } to { opacity:1; transform:translateY(0); } }
.acd { direction:rtl; }
.acd-grid { display:grid; grid-template-columns:repeat(4,1fr); gap:14px; margin-bottom: 6px; }
.acd-tile { display:flex; align-items:center; justify-content:space-between; gap:10px;
  background:var(--card-bg,#fff); border:1px solid var(--border-color,#eef0f4); border-radius:14px;
  padding:16px 18px; min-height:58px; cursor:pointer; box-shadow:0 1px 3px rgba(16,30,54,.06);
  animation:kajFadeUp .4s cubic-bezier(.2,.8,.2,1) backwards;
  transition:transform .2s cubic-bezier(.2,.8,.2,1), box-shadow .2s, border-color .2s; }
.acd-tile:hover { transform:translateY(-3px); box-shadow:0 10px 24px rgba(16,30,54,.12); border-color:#dfe3ea; }
.acd-tile-lbl { font-size:13.5px; font-weight:600; color:var(--text-color,#1a2b4a); }
.acd-grid > .acd-tile:nth-child(1){ animation-delay:.01s; } .acd-grid > .acd-tile:nth-child(2){ animation-delay:.03s; }
.acd-grid > .acd-tile:nth-child(3){ animation-delay:.05s; } .acd-grid > .acd-tile:nth-child(4){ animation-delay:.07s; }
.acd-grid > .acd-tile:nth-child(n+5){ animation-delay:.09s; }
.acd-tile-ico { width:20px; height:20px; flex-shrink:0; opacity:.92; }
@media (max-width:1200px){ .acd-grid{ grid-template-columns:repeat(3,1fr);} }
@media (max-width:1024px){ .acd-grid{ grid-template-columns:repeat(2,1fr); gap:12px;} }
@media (max-width:560px){ .acd-grid{ grid-template-columns:1fr;} }
""" + FUTURISTIC_CSS

ICON_SPRITE_JS = r"""
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

SCRIPT = """
const root = (typeof root_element !== 'undefined' && root_element) ? root_element : document;
""" + ICON_SPRITE_JS + NAV_LANG_JS + FUTURISTIC_JS + """
function translateAll(){
  root.querySelectorAll('[data-i18n]').forEach(function(el){ el.textContent = __(el.dataset.i18n); });
}
translateAll();
root.querySelectorAll('.acd-tile').forEach(function(t){
  t.addEventListener('click', function(){
    var a = t.dataset.action, tg = t.dataset.target;
    var filters = t.dataset.filters ? JSON.parse(t.dataset.filters) : null;
    if(a === 'list') {
      frappe.set_route('List', tg).then(function(){
        if(filters && cur_list && cur_list.doctype === tg){
          Object.keys(filters).forEach(function(k){ cur_list.filter_area.add(tg, k, '=', filters[k]); });
        }
      });
    }
    else if(a === 'page') frappe.set_route(tg);
    else if(a === 'report') frappe.set_route('query-report', tg);
  });
});
"""


def _tiles_html():
    cells = []
    for label, action, target, icon, filters in TILES:
        filt_attr = (' data-filters=\'%s\'' % json.dumps(filters)) if filters else ''
        cells.append(
            '<div class="acd-tile" data-action="%s" data-target="%s"%s>'
            '<span class="acd-tile-lbl" data-i18n="%s">%s</span>'
            '<svg class="icon icon-sm acd-tile-ico" style="color:#e63946;">'
            '<use href="#icon-%s"></use></svg></div>'
            % (action, frappe.utils.escape_html(target), filt_attr,
               frappe.utils.escape_html(label), label, icon)
        )
    return '<div class="acd"><div class="acd-grid">' + "".join(cells) + '</div></div>'


def _make_number_cards():
    result = []
    for name, label, dt, func, based_on, color in NUMBER_CARDS:
        for existing in frappe.get_all("Number Card", filters={"label": label}, pluck="name"):
            frappe.delete_doc("Number Card", existing, force=1, ignore_permissions=True)
        doc = {
            "doctype": "Number Card", "label": label, "type": "Document Type",
            "document_type": dt, "function": func, "is_public": 1,
            "show_percentage_stats": 1, "stats_time_interval": "Daily",
            "color": color, "filters_json": "[]",
        }
        if func == "Sum" and based_on:
            doc["aggregate_function_based_on"] = based_on
        d = frappe.get_doc(doc)
        d.insert(ignore_permissions=True)
        result.append((d.name, label))
    frappe.db.commit()
    return result


def _make_block():
    html = _tiles_html()
    if frappe.db.exists("Custom HTML Block", BLOCK_NAME):
        frappe.delete_doc("Custom HTML Block", BLOCK_NAME, force=1, ignore_permissions=True)
    d = frappe.get_doc({
        "doctype": "Custom HTML Block", "name": BLOCK_NAME,
        "html": html, "style": STYLE, "script": SCRIPT,
    })
    d.insert(ignore_permissions=True)
    d.append("roles", {"role": "System Manager"})
    d.append("roles", {"role": "Sales User"})
    d.append("roles", {"role": "مندوب مبيعات"})
    d.append("roles", {"role": "كاشير"})
    d.save(ignore_permissions=True)
    frappe.db.commit()
    return d.name


def _make_translations():
    for src, tgt in TRANSLATIONS:
        if not frappe.db.exists("Translation", {"source_text": src, "language": "en"}):
            frappe.get_doc({"doctype": "Translation", "language": "en",
                            "source_text": src, "translated_text": tgt}).insert(ignore_permissions=True)
    frappe.db.commit()


def execute():
    _make_translations()
    block_name = _make_block()
    made_cards = _make_number_cards()

    if frappe.db.exists("Workspace", WS_NAME):
        frappe.delete_doc("Workspace", WS_NAME, force=1, ignore_permissions=True)
        frappe.db.commit()

    content = [
        {"id": "sal_hdr", "type": "header",
         "data": {"text": '<span class="h4"><b>المبيعات</b></span>', "col": 12}},
    ]
    number_cards = []
    for idx, (name, label) in enumerate(made_cards):
        content.append({"id": "sal_nc_%d" % idx, "type": "number_card",
                        "data": {"number_card_name": name, "col": 3}})
        number_cards.append({"number_card_name": name, "label": label})

    content.append({"id": "sal_cb", "type": "custom_block",
                    "data": {"custom_block_name": block_name, "col": 12}})

    ws = frappe.get_doc({
        "doctype": "Workspace", "name": WS_NAME, "label": WS_NAME, "title": WS_TITLE,
        "public": 1, "is_hidden": 0, "icon": "sell", "module": "Core",
        "content": json.dumps(content, ensure_ascii=False),
        "shortcuts": [], "links": [], "number_cards": number_cards,
        "quick_lists": [], "charts": [],
        "custom_blocks": [{"custom_block_name": block_name, "label": block_name}],
        "sequence_id": 6,
    })
    ws.insert(ignore_permissions=True)

    if frappe.db.exists("Workspace Sidebar", WS_NAME):
        frappe.delete_doc("Workspace Sidebar", WS_NAME, force=1, ignore_permissions=True)
    frappe.get_doc({
        "doctype": "Workspace Sidebar", "name": WS_NAME, "title": WS_NAME,
        "header_icon": "sell", "module": "Core", "standard": 0, "items": [],
    }).insert(ignore_permissions=True)

    if frappe.db.exists("Workspace", "Selling"):
        frappe.db.set_value("Workspace", "Selling", "sequence_id", 34)

    frappe.db.commit()
    frappe.clear_cache()
    print("SALES_DASHBOARD_DONE tiles=%d cards=%d" % (len(TILES), len(number_cards)))
