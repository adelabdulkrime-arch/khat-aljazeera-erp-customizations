# -*- coding: utf-8 -*-
"""A clean Roles screen showing only the fourteen workshop roles, like Mazoon.

Frappe's own Role list shows all sixty-plus platform roles by their identifier
name, untranslated, so it reads as a mixed Arabic/English wall that can never
match Mazoon's tidy fourteen. That is a property of the standard list, not a
bug — so instead of fighting it, this builds a dedicated screen.

A Custom HTML Block renders the fourteen roles as a table — Arabic name, English
name, live user count, and an edit link — hosted in its own hidden workspace.
The "الأدوار" tile in General Settings is repointed here, so opening Roles lands
on this instead of the raw list. The underlying Role records are untouched; this
is purely a cleaner way to view and reach them.

Role names and their Arabic/English display come straight from workshop_roles,
so the two can never drift apart.
"""

import json

import frappe

from khat_workshop.setup.workshop_futuristic import FUTURISTIC_CSS, FUTURISTIC_JS
from khat_workshop.setup.workshop_roles import ROLES

WS_NAME = "Workshop Roles"
WS_TITLE = "الأدوار"
BLOCK_NAME = "Workshop Roles Table"


def _rows_html():
    rows = []
    for i, (role, ar, en) in enumerate(ROLES, 1):
        r = frappe.utils.escape_html(role)
        rows.append(
            '<tr class="wr-row">'
            '<td class="wr-num">%d</td>'
            '<td class="wr-ar">%s</td>'
            '<td class="wr-en">%s</td>'
            '<td class="wr-count" data-role="%s"><span class="wr-dot">…</span></td>'
            '<td class="wr-act">'
            '<a class="wr-btn wr-edit" data-role="%s">تعديل</a>'
            '</td></tr>'
            % (i, frappe.utils.escape_html(ar), frappe.utils.escape_html(en), r, r)
        )
    return (
        '<div class="wr-wrap" dir="rtl"><table class="wr-table"><thead><tr>'
        '<th class="wr-num">#</th><th>الاسم بالعربية</th>'
        '<th>الاسم بالإنجليزية</th><th class="wr-count">المستخدمون</th>'
        '<th class="wr-act">إجراءات</th>'
        '</tr></thead><tbody>' + "".join(rows) + '</tbody></table></div>'
    )


STYLE = """
.wr-wrap { direction:rtl; }
.wr-table { width:100%; border-collapse:separate; border-spacing:0 8px; font-size:13.5px; }
.wr-table thead th { text-align:right; color:var(--text-muted,#6b7280); font-weight:600;
  font-size:12px; padding:4px 14px; letter-spacing:.2px; }
.wr-table th.wr-num, .wr-table td.wr-num { width:48px; text-align:center; color:var(--text-muted,#98a2b3); }
.wr-table th.wr-count, .wr-table td.wr-count { width:120px; text-align:center; }
.wr-table th.wr-act, .wr-table td.wr-act { width:110px; text-align:center; }
.wr-row td { background:var(--card-bg,#fff); padding:14px; border-top:1px solid var(--border-color,#eef0f4);
  border-bottom:1px solid var(--border-color,#eef0f4); vertical-align:middle; }
.wr-row td:first-child { border-right:1px solid var(--border-color,#eef0f4);
  border-top-right-radius:12px; border-bottom-right-radius:12px; }
.wr-row td:last-child { border-left:1px solid var(--border-color,#eef0f4);
  border-top-left-radius:12px; border-bottom-left-radius:12px; }
.wr-row:hover td { background:var(--bg-light-gray,#f8fafc); }
.wr-ar { font-weight:700; color:var(--text-color,#1a2b4a); }
.wr-en { color:var(--text-muted,#6b7280); direction:ltr; text-align:right; }
.wr-count .wr-dot { display:inline-block; min-width:30px; padding:3px 10px; border-radius:20px;
  background:rgba(230,57,70,.10); color:#e63946; font-weight:700; font-size:12.5px; }
.wr-btn { cursor:pointer; padding:5px 14px; border-radius:8px; font-size:12.5px; font-weight:600;
  border:1px solid var(--border-color,#e5e7eb); color:var(--text-color,#334155); text-decoration:none; }
.wr-btn:hover { border-color:#e63946; color:#e63946; }
""" + FUTURISTIC_CSS


SCRIPT = """
const root = (typeof root_element !== 'undefined' && root_element) ? root_element : document;
""" + FUTURISTIC_JS + """
// live user count per role, via Has Role child rows on User
root.querySelectorAll('.wr-count').forEach(function(cell){
  var role = cell.dataset.role;
  frappe.db.count('Has Role', { filters: { role: role, parenttype: 'User' } })
    .then(function(n){ cell.querySelector('.wr-dot').textContent = n || 0; })
    .catch(function(){ cell.querySelector('.wr-dot').textContent = '0'; });
});
root.querySelectorAll('.wr-edit').forEach(function(a){
  a.addEventListener('click', function(){ frappe.set_route('Form', 'Role', a.dataset.role); });
});
"""


def _make_block():
    if frappe.db.exists("Custom HTML Block", BLOCK_NAME):
        frappe.delete_doc("Custom HTML Block", BLOCK_NAME, force=1, ignore_permissions=True)
    html = '<div class="wr" dir="rtl">' + _rows_html() + '</div>'
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


def execute():
    block = _make_block()

    if frappe.db.exists("Workspace", WS_NAME):
        frappe.delete_doc("Workspace", WS_NAME, force=1, ignore_permissions=True)
        frappe.db.commit()

    content = [
        {"id": "wr_hdr", "type": "header",
         "data": {"text": '<span class="h4"><b>الأدوار</b></span>', "col": 12}},
        {"id": "wr_cb", "type": "custom_block",
         "data": {"custom_block_name": block, "col": 12}},
    ]
    ws = frappe.get_doc({
        "doctype": "Workspace", "name": WS_NAME, "label": WS_NAME, "title": WS_TITLE,
        # public so it resolves by route, hidden so it does not clutter the rail
        "public": 1, "is_hidden": 1, "icon": "users", "module": "Core",
        "content": json.dumps(content, ensure_ascii=False),
        "shortcuts": [], "links": [], "number_cards": [], "quick_lists": [], "charts": [],
        "sequence_id": 90,
    })
    ws.append("custom_blocks", {"custom_block_name": block, "label": block})
    ws.insert(ignore_permissions=True)

    frappe.db.commit()
    frappe.clear_cache()
    print("ROLES_PAGE workspace=%s block=%s roles=%d" % (WS_NAME, block, len(ROLES)))
