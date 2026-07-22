# -*- coding: utf-8 -*-
"""Build 'المخزون' (Inventory) dashboard matching Mazoon's screen — 3 grouped
sections, ~18 tiles, all routed to native ERPNext Stock module features."""
import json
import frappe
from khat_workshop.setup.workshop_futuristic import FUTURISTIC_CSS, FUTURISTIC_JS

WS_NAME = "Inventory Dashboard"
WS_TITLE = "المخزون"
BLOCK_NAME = "Inventory Dashboard Tiles"

# action: list | new | report
GROUPS = [
    ("الإعداد", [
        ("المستودعات", "list", "Warehouse", "warehouse", None),
        ("البراندات", "list", "Brand", "tag", None),
        ("الأصناف", "list", "Item Group", "layout-grid", None),
        ("الوحدات", "list", "UOM", "wrench", None),
        ("المنتجات", "list", "Item", "package-plus", None),
        ("نقاط البيع", "list", "POS Profile", "credit-card", None),
    ]),
    ("العمليات", [
        ("سياسات إعادة الطلب", "list", "Item", "settings", None),
        ("أوامر الإتلاف", "list", "Stock Entry", "trash", {"stock_entry_type": "Material Issue"}),
        ("تحويلات المخزون", "list", "Stock Entry", "truck", {"stock_entry_type": "Material Transfer"}),
        ("الجرد", "list", "Stock Reconciliation", "file-check", None),
        ("الدفعات", "list", "Batch", "layout-grid", None),
        ("دفتر المخزون", "report", "Stock Ledger", "file-text", None),
    ]),
    ("التقارير", [
        ("تقرير الإتلاف والفاقد", "list", "Stock Entry", "trash",
         {"stock_entry_type": "Material Issue"}),
        ("المخزون حسب الفرع", "report", "Stock Balance", "warehouse", None),
        ("تقرير إعادة الطلب", "report", "Stock Projected Qty", "trending-up", None),
        ("بطاقة الصنف", "list", "Item", "id-card", None),
        ("تقرير الرصيد", "report", "Stock Balance", "chart-bar", None),
    ]),
]

TRANSLATIONS = [
    ("المخزون", "Inventory"),
    ("الإعداد", "Setup"),
    ("المستودعات", "Warehouses"),
    ("البراندات", "Brands"),
    ("الوحدات", "Units"),
    ("المنتجات", "Products"),
    ("نقاط البيع", "Points of Sale"),
    ("العمليات", "Operations"),
    ("سياسات إعادة الطلب", "Reorder Policies"),
    ("أوامر الإتلاف", "Disposal Orders"),
    ("تحويلات المخزون", "Stock Transfers"),
    ("الجرد", "Stock Reconciliation"),
    ("الدفعات", "Batches"),
    ("دفتر المخزون", "Stock Ledger"),
    ("التقارير", "Reports"),
    ("تقرير الإتلاف والفاقد", "Waste & Loss Report"),
    ("المخزون حسب الفرع", "Stock by Warehouse"),
    ("تقرير إعادة الطلب", "Reorder Report"),
    ("بطاقة الصنف", "Item Card"),
    ("تقرير الرصيد", "Balance Report"),
]

STYLE = """
@keyframes kajFadeUp { from { opacity:0; transform:translateY(10px); } to { opacity:1; transform:translateY(0); } }
.acd { direction:rtl; }
.acd-group { margin-bottom: 26px; }
.acd-group-title { font-size:14px; font-weight:700; color:var(--text-color,#1a2b4a);
  letter-spacing:.15px; text-transform:uppercase;
  margin:4px 0 14px; display:flex; align-items:center; gap:8px; }
.acd-group-title::before { content:""; width:4px; height:18px; background:#e63946; border-radius:3px; }
.acd-grid { display:grid; grid-template-columns:repeat(4,1fr); gap:14px; }
.acd-tile { display:flex; align-items:center; justify-content:space-between; gap:10px;
  background:var(--card-bg,#fff); border:1px solid var(--border-color,#eef0f4); border-radius:14px;
  padding:16px 18px; min-height:58px; cursor:pointer; box-shadow:0 1px 3px rgba(16,30,54,.06);
  animation:kajFadeUp .4s cubic-bezier(.2,.8,.2,1) backwards;
  transition:transform .2s cubic-bezier(.2,.8,.2,1), box-shadow .2s, border-color .2s; }
.acd-tile:hover { transform:translateY(-3px); box-shadow:0 10px 24px rgba(16,30,54,.12); border-color:#dfe3ea; }
.acd-grid > .acd-tile:nth-child(1){ animation-delay:.01s; } .acd-grid > .acd-tile:nth-child(2){ animation-delay:.03s; }
.acd-grid > .acd-tile:nth-child(3){ animation-delay:.05s; } .acd-grid > .acd-tile:nth-child(4){ animation-delay:.07s; }
.acd-grid > .acd-tile:nth-child(n+5){ animation-delay:.09s; }
.acd-tile.acd-primary { background:linear-gradient(135deg,#c0392b,#e63946); border-color:transparent;
  box-shadow:0 8px 20px rgba(230,57,70,.28); }
.acd-tile.acd-primary .acd-tile-lbl { color:#fff; }
.acd-tile.acd-primary .acd-tile-ico { color:#fff !important; }
.acd-tile-lbl { font-size:13.5px; font-weight:600; color:var(--text-color,#1a2b4a); }
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


SCRIPT = """
const root = (typeof root_element !== 'undefined' && root_element) ? root_element : document;
""" + ICON_SPRITE_JS + FUTURISTIC_JS + """
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
    else if(a === 'new') frappe.new_doc(tg);
    else if(a === 'report') frappe.set_route('query-report', tg);
  });
});
"""


def _tiles_html():
    groups_html = []
    for group_title, tiles in GROUPS:
        cells = []
        for label, action, target, icon, filters in tiles:
            filt_attr = (' data-filters=\'%s\'' % json.dumps(filters)) if filters else ''
            cells.append(
                '<div class="acd-tile" data-action="%s" data-target="%s"%s>'
                '<span class="acd-tile-lbl" data-i18n="%s">%s</span>'
                '<svg class="icon icon-sm acd-tile-ico" style="color:#e63946;">'
                '<use href="#icon-%s"></use></svg></div>'
                % (action, frappe.utils.escape_html(target), filt_attr,
                   frappe.utils.escape_html(label), label, icon)
            )
        groups_html.append(
            '<div class="acd-group"><div class="acd-group-title" data-i18n="%s">%s</div>'
            '<div class="acd-grid">%s</div></div>'
            % (frappe.utils.escape_html(group_title), group_title, "".join(cells))
        )
    return '<div class="acd">' + "".join(groups_html) + '</div>'


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
    d.append("roles", {"role": "Stock Manager"})
    d.append("roles", {"role": "مدير المستودع"})
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

    if frappe.db.exists("Workspace", WS_NAME):
        frappe.delete_doc("Workspace", WS_NAME, force=1, ignore_permissions=True)
        frappe.db.commit()

    content = [
        {"id": "inv_hdr", "type": "header",
         "data": {"text": '<span class="h4"><b>المخزون</b></span>', "col": 12}},
        {"id": "inv_cb", "type": "custom_block",
         "data": {"custom_block_name": block_name, "col": 12}},
    ]

    ws = frappe.get_doc({
        "doctype": "Workspace", "name": WS_NAME, "label": WS_NAME, "title": WS_TITLE,
        "public": 1, "is_hidden": 0, "icon": "stock", "module": "Core",
        "content": json.dumps(content, ensure_ascii=False),
        "shortcuts": [], "links": [], "number_cards": [], "quick_lists": [], "charts": [],
        "sequence_id": 4,
    })
    ws.append("custom_blocks", {"custom_block_name": block_name, "label": block_name})
    ws.insert(ignore_permissions=True)

    if frappe.db.exists("Workspace Sidebar", WS_NAME):
        frappe.delete_doc("Workspace Sidebar", WS_NAME, force=1, ignore_permissions=True)
    frappe.get_doc({
        "doctype": "Workspace Sidebar", "name": WS_NAME, "title": WS_NAME,
        "header_icon": "stock", "module": "Core", "standard": 0, "items": [],
    }).insert(ignore_permissions=True)

    # Deprioritize native "Stock" workspace (we still keep it reachable)
    if frappe.db.exists("Workspace", "Stock"):
        frappe.db.set_value("Workspace", "Stock", "sequence_id", 32)

    frappe.db.commit()
    frappe.clear_cache()
    total_tiles = sum(len(t) for _, t in GROUPS)
    print("INVENTORY_DASHBOARD_DONE groups=%d tiles=%d" % (len(GROUPS), total_tiles))
