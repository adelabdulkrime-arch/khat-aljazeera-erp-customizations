# -*- coding: utf-8 -*-
"""Make the desk sidebar read as one product instead of three.

Two things gave the system away as an assembly of stock apps:

1. The sidebar header shows the *owning app* of whichever workspace is open.
   The workshop's own dashboards are stored against app "frappe", so opening
   them displayed "Frappe Framework"; the home page showed "ERPNext". A client
   looking at a system sold as "خط الجزيرة" saw two other product names before
   seeing ours. Reassigning the workshop workspaces to khat_workshop makes the
   header read the workshop's name throughout.

2. Ten workspaces the workshop never opens — Recruitment, Payroll, Leaves,
   Shift & Attendance, ERPNext Settings and the rest — sat in the sidebar
   between the ones it does. Each is a door to a module nobody configured, and
   on a small workshop they are noise that makes the real menu harder to scan.

Both are reversible: hiding a workspace does not delete it, and anyone who
later wants HR can unhide it from the workspace itself.
"""

import frappe

APP = "khat_workshop"

# The sidebar header reads frappe.current_app, which the desk derives from the
# open workspace's *module* — not from its `app` field. Our dashboards sat under
# module "Core", which belongs to frappe, so the header said "Frappe Framework".
# Moving them onto this app's own module is what actually changes it.
MODULE = "Khat Workshop"

# The dashboards this project builds. They live under module "Core"/app
# "frappe" simply because that is what Workspace defaults to on insert.
OWNED = [
    "Home",
    "Workshop",
    "Sales Dashboard",
    "Purchasing Dashboard",
    "Inventory Dashboard",
    "Accounting Dashboard",
    "General Settings",
]

# ترتيب الشريط الجانبي وأيقوناته — مطابق لترتيب بطاقات الصفحة الرئيسية.
#
# كان الشريط يعرض الوحدات بترتيب معكوس تقريباً عن الصفحة: الإعدادات العامة
# ثانياً في الشريط وأخيراً في الصفحة، والورشة أخيراً في الشريط وأولاً في
# الصفحة. فالمستخدم يبني خريطة ذهنية من إحداهما ثم لا تطابقه الأخرى.
#
# الأيقونات من مجموعة lucide التي يحمّلها الديسك. "sell" لم تكن موجودة فيها،
# فظهرت لوحة المبيعات بلا أيقونة — رُصد في الواجهة. "shopping-cart" موجودة
# وهي نفس أيقونة بطاقة المبيعات في الصفحة الرئيسية، فيتطابق الاثنان.
ORDER = [
    # (اسم مساحة العمل، الترتيب، الأيقونة)
    ("Home", 1, "home"),
    ("Workshop", 2, "tool"),
    ("Sales Dashboard", 3, "shopping-cart"),
    ("Purchasing Dashboard", 4, "package-plus"),
    ("Inventory Dashboard", 5, "layout-grid"),
    ("Accounting Dashboard", 6, "receipt"),
    ("General Settings", 7, "settings"),
]

# Hidden, not deleted. A workshop that later hires staff can bring HR back.
HIDE = [
    "Recruitment",
    "Payroll",
    "Leaves",
    "Expenses",
    "Performance",
    "Tenure",
    "Shift & Attendance",
    "Tax & Benefits",
    "HR Setup",
    "ERPNext Settings",
]


def execute():
    reassigned = []
    for name in OWNED:
        if not frappe.db.exists("Workspace", name):
            continue
        current = frappe.db.get_value(
            "Workspace", name, ["app", "module"], as_dict=True
        )
        changes = {}
        if current.app != APP:
            changes["app"] = APP
        if current.module != MODULE and frappe.db.exists("Module Def", MODULE):
            changes["module"] = MODULE
        if changes:
            # db.set_value rather than a full save: Workspace validation rebuilds
            # the block content, and a stray validation error on one dashboard
            # should not take the whole step down.
            frappe.db.set_value("Workspace", name, changes, update_modified=False)
            reassigned.append(name)

    # الترتيب والأيقونات: db.set_value لا save، كما أعلاه — حفظ كامل يُعيد
    # بناء محتوى مساحة العمل وقد يسقط على خطأ تحقّق في لوحة واحدة.
    ordered = []
    for name, seq, icon in ORDER:
        if not frappe.db.exists("Workspace", name):
            continue
        current = frappe.db.get_value(
            "Workspace", name, ["sequence_id", "icon"], as_dict=True
        )
        changes = {}
        if current.sequence_id != seq:
            changes["sequence_id"] = seq
        if current.icon != icon:
            changes["icon"] = icon
        if changes:
            frappe.db.set_value("Workspace", name, changes, update_modified=False)
            ordered.append(name)

    hidden = []
    for name in HIDE:
        if not frappe.db.exists("Workspace", name):
            continue
        if not frappe.db.get_value("Workspace", name, "is_hidden"):
            frappe.db.set_value("Workspace", name, "is_hidden", 1, update_modified=False)
            hidden.append(name)

    frappe.db.commit()
    frappe.clear_cache()
    print(
        "WORKSPACE_POLISH reassigned=%d ordered=%d hidden=%d"
        % (len(reassigned), len(ordered), len(hidden))
    )
