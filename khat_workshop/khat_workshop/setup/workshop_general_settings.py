# -*- coding: utf-8 -*-
"""Build 'General Settings' (الإعدادات العامة) workspace matching Mazoon's
General Settings screen — 11 tiles (Branches intentionally excluded per user
request), reusing ERPNext's own native doctypes/pages wherever they exist."""
import json
import frappe
from khat_workshop.setup.workshop_futuristic import FUTURISTIC_CSS, FUTURISTIC_JS

WS_NAME = "General Settings"
WS_TITLE = "الإعدادات العامة"
BLOCK_NAME = "General Settings Tiles"

# (label, action, target, icon, color)
# action: list | form | page | myaccount
# Order and naming follow Mazoon's General Settings, minus Branches (excluded
# for a single-site workshop) and the dashboard overview. "حسابي/My Account"
# was dropped — Mazoon has no such tile; the account is reached from the avatar
# menu. Users and Roles come first, as in Mazoon. Routes reuse ERPNext's own
# native list/single views wherever they exist.
TILES = [
    ("المستخدمون", "list", "User", "users", "#e63946"),
    # Not the raw Role list (60+ mixed-language platform roles) — our clean
    # fourteen-role screen. See workshop_roles_page.
    ("الأدوار", "workspace", "workshop-roles", "shield-user", "#e63946"),
    ("الإعدادات", "company", "Company", "settings", "#e63946"),
    # Logo, favicon and login background in one place — Website Settings is a
    # Single, so it routes by doctype name with no document name. Mazoon folds
    # these into Settings; kept separate here until the Settings form is curated.
    ("الشعار والهوية", "single", "Website Settings", "image", "#e63946"),
    ("الحقول المخصصة", "list", "Custom Field", "list-plus", "#e63946"),
    ("جهات الاتصال", "list", "Contact", "contact", "#e63946"),
    ("أدوار جهات الاتصال", "list", "Contact Role", "id-card", "#e63946"),
    ("الدول", "list", "Country", "globe", "#e63946"),
    ("قوالب الطباعة", "list", "Letter Head", "printer", "#e63946"),
    ("سجل النشاط", "list", "Activity Log", "history", "#e63946"),
    ("نسخة احتياطية", "page", "backups", "file-down", "#e63946"),
]

TRANSLATIONS = [
    ("الإعدادات العامة", "General Settings"),
    ("الإعدادات", "Settings"),
    ("الشعار والهوية", "Logo & Identity"),
    # Must match the tile label exactly (TILES row 2 is "الأدوار"). It said
    # "الأدوار والصلاحيات" before, which no tile uses, so __("الأدوار") found
    # nothing and that one tile stayed Arabic while every other translated.
    ("الأدوار", "Roles"),
    ("المستخدمون", "Users"),
    ("أدوار جهات الاتصال", "Contact Roles"),
    ("جهات الاتصال", "Contacts"),
    ("الحقول المخصصة", "Custom Fields"),
    ("نسخة احتياطية", "Backup"),
    ("قوالب الطباعة", "Print Templates"),
    ("الدول", "Countries"),
    ("سجل النشاط", "Activity Log"),
]


def _ensure_contact_role_doctype():
    """Mazoon has a small 'Contact Roles' master with no direct ERPNext
    equivalent — add a minimal custom DocType for it."""
    if frappe.db.exists("DocType", "Contact Role"):
        return
    if not frappe.db.exists("Module Def", "Workshop"):
        frappe.get_doc({"doctype": "Module Def", "module_name": "Workshop",
                        "custom": 1, "app_name": "frappe"}).insert(ignore_permissions=True)
    frappe.get_doc({
        "doctype": "DocType", "name": "Contact Role", "module": "Workshop", "custom": 1,
        "autoname": "field:role_name", "naming_rule": "By fieldname",
        "fields": [
            {"fieldname": "role_name", "label": "اسم الدور", "fieldtype": "Data",
             "reqd": 1, "in_list_view": 1, "unique": 1},
            {"fieldname": "description", "label": "الوصف", "fieldtype": "Small Text"},
        ],
        "permissions": [
            {"role": "System Manager", "read": 1, "write": 1, "create": 1,
             "delete": 1, "report": 1, "export": 1, "print": 1, "share": 1},
        ],
    }).insert(ignore_permissions=True)


def _tiles_html():
    cells = []
    for label, action, target, icon, color in TILES:
        cells.append(
            '<div class="gsd-tile" data-action="%s" data-target="%s">'
            '<span class="gsd-tile-ico-wrap">'
            '<svg class="icon icon-sm gsd-tile-ico" style="color:%s;">'
            '<use href="#icon-%s"></use></svg></span>'
            '<span class="gsd-tile-lbl" data-i18n="%s">%s</span></div>'
            % (action, frappe.utils.escape_html(target), color, icon,
               frappe.utils.escape_html(label), label)
        )
    return '<div class="gsd-grid">' + "".join(cells) + '</div>'


STYLE = """
@keyframes kajFadeUp { from { opacity:0; transform:translateY(10px); } to { opacity:1; transform:translateY(0); } }
.gsd-grid { display:grid; grid-template-columns:repeat(4,1fr); gap:14px; direction:rtl; }
.gsd-tile { display:flex; align-items:center; gap:13px; background:var(--card-bg,#fff);
  border:1px solid var(--border-color,#eef0f4); border-radius:14px; padding:18px 20px;
  cursor:pointer; min-height:60px; box-shadow:0 1px 3px rgba(16,30,54,.06);
  animation:kajFadeUp .4s cubic-bezier(.2,.8,.2,1) backwards;
  transition:transform .2s cubic-bezier(.2,.8,.2,1), box-shadow .2s, border-color .2s; }
.gsd-tile:hover { transform:translateY(-3px); box-shadow:0 10px 24px rgba(16,30,54,.12); border-color:#dfe3ea; }
.gsd-tile-ico-wrap { width:42px; height:42px; border-radius:11px; flex-shrink:0;
  display:flex; align-items:center; justify-content:center;
  background:linear-gradient(135deg,rgba(230,57,70,.10),rgba(192,57,43,.16)); }
.gsd-tile-ico { width:20px; height:20px; flex-shrink:0; }
.gsd-tile-lbl { font-size:13.5px; font-weight:700; color:var(--text-color,#1a2b4a); letter-spacing:.1px; }
.gsd-grid > .gsd-tile:nth-child(1){ animation-delay:.01s; } .gsd-grid > .gsd-tile:nth-child(2){ animation-delay:.03s; }
.gsd-grid > .gsd-tile:nth-child(3){ animation-delay:.05s; } .gsd-grid > .gsd-tile:nth-child(4){ animation-delay:.07s; }
.gsd-grid > .gsd-tile:nth-child(n+5){ animation-delay:.09s; }
@media (max-width:1024px){ .gsd-grid{ grid-template-columns:repeat(3,1fr);} }
@media (max-width:768px){ .gsd-grid{ grid-template-columns:repeat(2,1fr); gap:12px;} }
@media (max-width:520px){ .gsd-grid{ grid-template-columns:1fr;} }
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
root.querySelectorAll('.gsd-tile').forEach(function(t){
  t.addEventListener('click', function(){
    var a = t.dataset.action, tg = t.dataset.target;
    if(a === 'list') frappe.set_route('List', tg);
    else if(a === 'workspace') window.location.href = '/app/' + tg;
    else if(a === 'single') frappe.set_route('Form', tg, tg);
    else if(a === 'form') frappe.set_route('Form', tg);
    else if(a === 'page') frappe.set_route(tg);
    else if(a === 'report') frappe.set_route('query-report', tg);
    else if(a === 'myaccount') frappe.set_route('Form', tg, frappe.session.user);
    else if(a === 'company') {
      frappe.db.get_single_value('Global Defaults', 'default_company').then(function(c){
        frappe.set_route('Form', tg, c || '');
      });
    }
  });
});
"""


def _make_block():
    html = '<div class="gsd" dir="rtl">' + _tiles_html() + '</div>'
    if frappe.db.exists("Custom HTML Block", BLOCK_NAME):
        frappe.delete_doc("Custom HTML Block", BLOCK_NAME, force=1, ignore_permissions=True)
    d = frappe.get_doc({
        "doctype": "Custom HTML Block", "name": BLOCK_NAME,
        "html": html, "style": STYLE, "script": SCRIPT,
    })
    d.insert(ignore_permissions=True)
    d.append("roles", {"role": "System Manager"})
    d.append("roles", {"role": "All"})
    d.save(ignore_permissions=True)
    frappe.db.commit()
    return d.name


def _make_translations():
    for src, tgt in TRANSLATIONS:
        if not frappe.db.exists("Translation", {"source_text": src, "language": "en"}):
            frappe.get_doc({
                "doctype": "Translation", "language": "en",
                "source_text": src, "translated_text": tgt,
            }).insert(ignore_permissions=True)
    frappe.db.commit()


def execute():
    _ensure_contact_role_doctype()
    _make_translations()
    block_name = _make_block()

    if frappe.db.exists("Workspace", WS_NAME):
        frappe.delete_doc("Workspace", WS_NAME, force=1, ignore_permissions=True)
        frappe.db.commit()

    content = [
        {"id": "gs_hdr", "type": "header",
         "data": {"text": '<span class="h4"><b>الإعدادات العامة</b></span>', "col": 12}},
        {"id": "gs_cb", "type": "custom_block",
         "data": {"custom_block_name": block_name, "col": 12}},
    ]

    ws = frappe.get_doc({
        "doctype": "Workspace", "name": WS_NAME, "label": WS_NAME, "title": WS_TITLE,
        "public": 1, "is_hidden": 0, "icon": "setting", "module": "Core",
        "content": json.dumps(content, ensure_ascii=False),
        "shortcuts": [], "links": [], "number_cards": [], "quick_lists": [], "charts": [],
        "sequence_id": 2,
    })
    ws.append("custom_blocks", {"custom_block_name": block_name, "label": block_name})
    ws.insert(ignore_permissions=True)

    # Explicit clean Workspace Sidebar override (learned from the Home bug —
    # standard fixtures ship hardcoded sidebar items regardless of DB content).
    if frappe.db.exists("Workspace Sidebar", WS_NAME):
        frappe.delete_doc("Workspace Sidebar", WS_NAME, force=1, ignore_permissions=True)
    frappe.get_doc({
        "doctype": "Workspace Sidebar", "name": WS_NAME, "title": WS_NAME,
        "header_icon": "setting", "module": "Core", "standard": 0, "items": [],
    }).insert(ignore_permissions=True)

    frappe.db.commit()
    frappe.clear_cache()
    print("GENERAL_SETTINGS_DONE tiles=%d" % len(TILES))
