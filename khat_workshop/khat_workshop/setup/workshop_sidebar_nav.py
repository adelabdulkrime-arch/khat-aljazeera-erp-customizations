# -*- coding: utf-8 -*-
"""Give every dashboard the same left-rail: a persistent nav to all seven.

v16 drives the left rail from the Workspace Sidebar doctype, one record per
workspace, independent of the tiles shown in the body. Out of the box these
were inconsistent — Home carried five leftover ERPNext quick-links (Item,
Customer, Supplier, Sales Invoice, and a self-link), while the other five
dashboards had none — so the rail looked half-built and changed as you moved
between dashboards.

This writes the identical seven-item navigation onto all seven, so the rail
reads the same everywhere and doubles as the primary way to move between
dashboards, the way Mazoon's left menu does. The items use link_type
"Workspace", which the framework routes inside the SPA (no reload) and
highlights as active — more idiomatic and robust than a hardcoded URL.

Rebuilt wholesale each run rather than appended, so a changed label or order in
NAV is reflected exactly and the record cannot accumulate stale rows.
"""

import frappe

# (workspace name, arabic label, lucide icon)
NAV = [
    ("Home", "الرئيسية", "home"),
    ("General Settings", "الإعدادات العامة", "setting"),
    ("Accounting Dashboard", "لوحة المحاسبة", "accounting"),
    ("Inventory Dashboard", "لوحة المخزون", "stock"),
    ("Purchasing Dashboard", "لوحة المشتريات", "buying"),
    ("Sales Dashboard", "لوحة المبيعات", "selling"),
    ("Workshop", "الورشة", "tool"),
]


def _items():
    rows = []
    for name, label, icon in NAV:
        if not frappe.db.exists("Workspace", name):
            continue
        rows.append({
            "label": label,
            "type": "Link",
            "link_type": "Workspace",
            "link_to": name,
            "icon": icon,
        })
    return rows


def execute():
    items = _items()
    touched = 0

    for name, _label, icon in NAV:
        if not frappe.db.exists("Workspace", name):
            continue

        if frappe.db.exists("Workspace Sidebar", name):
            sb = frappe.get_doc("Workspace Sidebar", name)
        else:
            sb = frappe.new_doc("Workspace Sidebar")
            sb.title = name
            sb.module = frappe.db.get_value("Workspace", name, "module") or "Core"

        sb.header_icon = icon
        sb.set("items", [])
        for row in items:
            sb.append("items", row)
        sb.flags.ignore_permissions = True
        sb.save(ignore_permissions=True)
        touched += 1

    frappe.db.commit()
    frappe.clear_cache()
    print("SIDEBAR_NAV items=%d applied_to=%d dashboards" % (len(items), touched))
