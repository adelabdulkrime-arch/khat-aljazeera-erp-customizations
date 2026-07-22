# -*- coding: utf-8 -*-
"""Build 'المحاسبة' (Accounting) dashboard matching Mazoon's screen — 5
grouped sections, ~30 tiles, ALL routed to native ERPNext Accounts module
features (Sales/Purchase Invoice, Payment Entry, Journal Entry, standard
financial reports etc.) — nothing rebuilt from scratch, this module is
ERPNext's own core strength."""
import json
import frappe
from khat_workshop.setup.workshop_futuristic import FUTURISTIC_CSS, FUTURISTIC_JS, NAV_LANG_JS

WS_NAME = "Accounting Dashboard"
WS_TITLE = "المحاسبة"
BLOCK_NAME = "Accounting Dashboard Tiles"

# Each group: (group_title, [(label, action, target, icon, extra_route_options)])
# action: list | new | page | tree | report
GROUPS = [
    ("فواتير الخدمات والإيرادات", [
        ("عروض أسعار الخدمات", "list", "Quotation", "file", None),
        ("إشعارات الدائن", "list", "Sales Invoice", "receipt", {"is_return": 1}),
        ("الأقساط", "list", "Sales Invoice", "calendar", None),
        ("مدفوعات فواتير الخدمات", "list", "Payment Entry", "credit-card", {"payment_type": "Receive"}),
        ("فواتير الخدمات", "list", "Sales Invoice", "receipt", {"is_return": 0}),
        ("إضافة فاتورة خدمات", "new", "Sales Invoice", "plus", None),
    ]),
    ("المصروفات والمدفوعات", [
        ("الشيكات", "list", "Journal Entry", "credit-card", None),
        ("فئات المصروفات", "list", "Account", "tag", {"root_type": "Expense", "is_group": 0}),
        ("سندات الصرف", "list", "Payment Entry", "dollar-sign", {"payment_type": "Pay"}),
        ("سندات القبض", "list", "Payment Entry", "dollar-sign", {"payment_type": "Receive"}),
        ("دفعات المصروفات", "list", "Payment Entry", "credit-card",
         {"payment_type": "Pay", "party_type": "Supplier"}),
        ("فواتير المصروفات", "list", "Journal Entry", "file-text", None),
    ]),
    ("المشتريات", [
        ("مدفوعات المشتريات", "list", "Payment Entry", "credit-card",
         {"payment_type": "Pay", "party_type": "Supplier"}),
        ("المشتريات", "list", "Purchase Invoice", "receipt", None),
        ("الموردون", "list", "Supplier", "truck", None),
    ]),
    ("المحاسبة والتقارير", [
        ("التحويلات", "list", "Journal Entry", "trending-up", {"voucher_type": "Bank Entry"}),
        ("الرصيد الافتتاحي", "page", "opening-invoice-creation-tool", "file-plus", None),
        ("الشجرة المحاسبية", "tree", "Account", "chart-bar", None),
        ("تسوية الرسوم والضرائب", "list", "Journal Entry", "settings", None),
        ("إضافة قيد يدوي", "new", "Journal Entry", "plus", None),
        ("القيود", "list", "Journal Entry", "file-text", None),
        ("التسويات البنكية", "page", "bank-reconciliation-tool", "credit-card", None),
        ("الفترات المحاسبية", "list", "Accounting Period", "calendar", None),
        ("طرق الدفع", "list", "Mode of Payment", "credit-card", None),
        ("الأصول", "list", "Asset", "wrench", None),
        ("أرصدة النقدية والبنوك", "list", "Bank Account", "dollar-sign", None),
        ("التدفقات النقدية", "report", "Cash Flow", "trending-up", None),
        ("مستحقات الموردين", "report", "Accounts Payable", "receipt", None),
        ("مديونيات العملاء", "report", "Accounts Receivable", "receipt", None),
        ("التقارير", "report", "Balance Sheet", "chart-bar", None),
    ]),
    ("العملاء", [
        ("العملاء", "list", "Customer", "users", None),
    ]),
]

TRANSLATIONS = [
    ("المحاسبة", "Accounting"),
    ("فواتير الخدمات والإيرادات", "Service Invoices & Revenue"),
    ("عروض أسعار الخدمات", "Service Quotations"),
    ("إشعارات الدائن", "Credit Notes"),
    ("الأقساط", "Installments"),
    ("مدفوعات فواتير الخدمات", "Service Invoice Payments"),
    ("فواتير الخدمات", "Service Invoices"),
    ("إضافة فاتورة خدمات", "Add Service Invoice"),
    ("المصروفات والمدفوعات", "Expenses & Payments"),
    ("الشيكات", "Cheques"),
    ("فئات المصروفات", "Expense Categories"),
    ("سندات الصرف", "Payment Vouchers"),
    ("سندات القبض", "Receipt Vouchers"),
    ("دفعات المصروفات", "Expense Payments"),
    ("فواتير المصروفات", "Expense Invoices"),
    ("مدفوعات المشتريات", "Purchase Payments"),
    ("المشتريات", "Purchases"),
    ("الموردون", "Suppliers"),
    ("المحاسبة والتقارير", "Accounting & Reports"),
    ("التحويلات", "Transfers"),
    ("الرصيد الافتتاحي", "Opening Balance"),
    ("الشجرة المحاسبية", "Chart of Accounts"),
    ("تسوية الرسوم والضرائب", "Tax & Fee Reconciliation"),
    ("إضافة قيد يدوي", "Add Manual Journal Entry"),
    ("القيود", "Journal Entries"),
    ("التسويات البنكية", "Bank Reconciliation"),
    ("الفترات المحاسبية", "Accounting Periods"),
    ("طرق الدفع", "Payment Methods"),
    ("الأصول", "Assets"),
    ("أرصدة النقدية والبنوك", "Cash & Bank Balances"),
    ("التدفقات النقدية", "Cash Flow"),
    ("مستحقات الموردين", "Supplier Payables"),
    ("مديونيات العملاء", "Customer Receivables"),
    ("التقارير", "Reports"),
    ("العملاء", "Customers"),
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
.acd-tile.acd-primary:hover { box-shadow:0 12px 28px rgba(230,57,70,.36); }
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
      if(filters) frappe.set_route('List', tg).then(function(){
        var lv = cur_list;
        if(lv && lv.doctype === tg){ Object.keys(filters).forEach(function(k){ lv.filter_area.add(tg, k, '=', filters[k]); }); }
      });
      else frappe.set_route('List', tg);
    }
    else if(a === 'new') frappe.new_doc(tg);
    else if(a === 'page') frappe.set_route(tg);
    else if(a === 'tree') frappe.set_route('Tree', tg);
    else if(a === 'report') frappe.set_route('query-report', tg);
  });
});
"""


def _tiles_html():
    groups_html = []
    for group_title, tiles in GROUPS:
        cells = []
        for label, action, target, icon, filters in tiles:
            primary = ' acd-primary' if action == 'new' else ''
            filt_attr = (' data-filters=\'%s\'' % json.dumps(filters)) if filters else ''
            cells.append(
                '<div class="acd-tile%s" data-action="%s" data-target="%s"%s>'
                '<span class="acd-tile-lbl" data-i18n="%s">%s</span>'
                '<svg class="icon icon-sm acd-tile-ico" style="color:%s;">'
                '<use href="#icon-%s"></use></svg></div>'
                % (primary, action, frappe.utils.escape_html(target), filt_attr,
                   frappe.utils.escape_html(label), label,
                   '#fff' if action == 'new' else '#e63946', icon)
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
    d.append("roles", {"role": "Accounts Manager"})
    d.append("roles", {"role": "محاسب"})
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
        {"id": "ac_hdr", "type": "header",
         "data": {"text": '<span class="h4"><b>المحاسبة</b></span>', "col": 12}},
        {"id": "ac_cb", "type": "custom_block",
         "data": {"custom_block_name": block_name, "col": 12}},
    ]

    ws = frappe.get_doc({
        "doctype": "Workspace", "name": WS_NAME, "label": WS_NAME, "title": WS_TITLE,
        "public": 1, "is_hidden": 0, "icon": "accounting", "module": "Core",
        "content": json.dumps(content, ensure_ascii=False),
        "shortcuts": [], "links": [], "number_cards": [], "quick_lists": [], "charts": [],
        "sequence_id": 3,
    })
    ws.append("custom_blocks", {"custom_block_name": block_name, "label": block_name})
    ws.insert(ignore_permissions=True)

    if frappe.db.exists("Workspace Sidebar", WS_NAME):
        frappe.delete_doc("Workspace Sidebar", WS_NAME, force=1, ignore_permissions=True)
    frappe.get_doc({
        "doctype": "Workspace Sidebar", "name": WS_NAME, "title": WS_NAME,
        "header_icon": "accounting", "module": "Core", "standard": 0, "items": [],
    }).insert(ignore_permissions=True)

    # Deprioritize the native "Invoicing"/"Financial Reports" workspaces so
    # our own Accounting dashboard is the primary entry point (kept, not
    # hidden — still reachable, just not competing for top sidebar slot).
    for wsname, seq in [("Invoicing", 30), ("Financial Reports", 31)]:
        if frappe.db.exists("Workspace", wsname):
            frappe.db.set_value("Workspace", wsname, "sequence_id", seq)

    frappe.db.commit()
    frappe.clear_cache()
    total_tiles = sum(len(t) for _, t in GROUPS)
    print("ACCOUNTING_DASHBOARD_DONE groups=%d tiles=%d" % (len(GROUPS), total_tiles))
