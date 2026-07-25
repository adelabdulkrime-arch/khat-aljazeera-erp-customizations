# -*- coding: utf-8 -*-
"""Make the standard Role list read in one language, whichever is chosen.

Frappe's Role list shows each role by its identifier name and does not translate
it, so Arabic-named workshop roles and English-named platform roles appear
side by side no matter the interface language. Two pieces fix that:

  1. an Arabic translation for every platform role (the fourteen workshop roles
     already carry both languages via workshop_roles), so __() has something to
     return in Arabic;
  2. a List client script on Role that rewrites each displayed name to __(name)
     — reading the real name from the row's link so it is never guessed — which
     the list itself will not do.

Result: Arabic interface → every role in Arabic; English interface → every role
in English. This also removes the earlier custom Roles page, now that the
standard list is used again.
"""

import frappe

from khat_workshop.setup.workshop_roles import ROLES

# Platform (English-named) roles -> Arabic. The workshop's own fourteen already
# have both languages from workshop_roles, so they are not repeated here.
AR = {
    "Academics User": "مستخدم أكاديمي",
    "Accounts Manager": "مدير الحسابات",
    "Accounts User": "مستخدم الحسابات",
    "Administrator": "المسؤول العام",
    "All": "الكل",
    "Analytics": "التحليلات",
    "Auditor": "المدقّق",
    "Customer": "عميل",
    "Dashboard Manager": "مدير اللوحات",
    "Delivery Manager": "مدير التوصيل",
    "Delivery User": "مستخدم التوصيل",
    "Desk User": "مستخدم النظام",
    "Expense Approver": "معتمِد المصروفات",
    "Fleet Manager": "مدير الأسطول",
    "Fulfillment User": "مستخدم التجهيز",
    "Guest": "ضيف",
    "HR User": "مستخدم الموارد البشرية",
    "Inbox User": "مستخدم البريد",
    "Interviewer": "مُحاوِر",
    "Item Manager": "مدير الأصناف",
    "Knowledge Base Contributor": "مساهم قاعدة المعرفة",
    "Knowledge Base Editor": "محرّر قاعدة المعرفة",
    "Leave Approver": "معتمِد الإجازات",
    "Maintenance Manager": "مدير الصيانة",
    "Maintenance User": "مستخدم الصيانة",
    "Manufacturing Manager": "مدير التصنيع",
    "Manufacturing User": "مستخدم التصنيع",
    "Marketing Manager": "مدير التسويق",
    "Newsletter Manager": "مدير النشرات البريدية",
    "Prepared Report User": "مستخدم التقارير الجاهزة",
    "Projects Manager": "مدير المشاريع",
    "Projects User": "مستخدم المشاريع",
    "Purchase Manager": "مدير المشتريات",
    "Purchase Master Manager": "المدير الرئيسي للمشتريات",
    "Purchase User": "مستخدم المشتريات",
    "Quality Manager": "مدير الجودة",
    "Report Manager": "مدير التقارير",
    "Sales Master Manager": "المدير الرئيسي للمبيعات",
    "Sales User": "مستخدم المبيعات",
    "Script Manager": "مدير البرمجة",
    "Stock Manager": "مدير المخزون",
    "Stock User": "مستخدم المخزون",
    "Supplier": "مورّد",
    "Support Team": "فريق الدعم",
    "System Manager": "مسؤول النظام",
    "Translator": "مترجم",
    "Website Manager": "مدير الموقع",
    "Workspace Manager": "مدير مساحات العمل",
}

CLIENT_SCRIPT_NAME = "Role List — Arabic/English Names"

# Reads the real role name from each row's link (…/role/<name>) and rewrites the
# shown text to __(name), so the list follows the interface language. Re-run on
# a short delay because rows render asynchronously and on scroll/refresh.
LIST_SCRIPT = r"""
frappe.listview_settings['Role'] = {
    refresh(listview) {
        function relabel() {
            const rows = (listview && listview.$result) ? listview.$result : $(document);
            rows.find('a[href*="/role/"]').each(function () {
                const el = $(this);
                const m = (el.attr('href') || '').match(/\/role\/([^?#]+)/);
                if (!m) return;
                const raw = decodeURIComponent(m[1]);
                const t = __(raw);
                if (t && t !== el.text().trim()) el.text(t);
            });
        }
        setTimeout(relabel, 150);
        setTimeout(relabel, 500);
        if (listview && listview.$result) {
            listview.$result.off('scroll.kajrole').on('scroll.kajrole', function () {
                setTimeout(relabel, 50);
            });
        }
    }
};
"""


def _upsert(source, language, target):
    if not target or source == target:
        return
    existing = frappe.db.get_value(
        "Translation", {"source_text": source, "language": language}, "name")
    if existing:
        if frappe.db.get_value("Translation", existing, "translated_text") != target:
            frappe.db.set_value("Translation", existing, "translated_text", target)
        return
    frappe.get_doc({
        "doctype": "Translation", "language": language,
        "source_text": source, "translated_text": target,
    }).insert(ignore_permissions=True)


def _translations():
    n = 0
    # platform roles -> Arabic
    for en_name, ar in AR.items():
        if frappe.db.exists("Role", en_name):
            _upsert(en_name, "ar", ar)
            n += 1
    # make sure the fourteen workshop roles carry both directions too
    for role, ar, en in ROLES:
        _upsert(role, "ar", ar)
        _upsert(role, "en", en)
    return n


def _client_script():
    if frappe.db.exists("Client Script", CLIENT_SCRIPT_NAME):
        doc = frappe.get_doc("Client Script", CLIENT_SCRIPT_NAME)
        changed = False
        if (doc.script or "").strip() != LIST_SCRIPT.strip():
            doc.script = LIST_SCRIPT
            changed = True
        if not doc.enabled:
            doc.enabled = 1
            changed = True
        if changed:
            doc.save(ignore_permissions=True)
        return "updated"
    frappe.get_doc({
        "doctype": "Client Script", "name": CLIENT_SCRIPT_NAME,
        "dt": "Role", "view": "List", "enabled": 1, "script": LIST_SCRIPT,
    }).insert(ignore_permissions=True)
    return "created"


def _remove_custom_page():
    """Tear down the earlier custom Roles page — the standard list is used now."""
    for dt, name in (("Workspace", "Workshop Roles"),
                     ("Workspace Sidebar", "Workshop Roles"),
                     ("Custom HTML Block", "Workshop Roles Table")):
        if frappe.db.exists(dt, name):
            frappe.delete_doc(dt, name, force=1, ignore_permissions=True)


def execute():
    translated = _translations()
    state = _client_script()
    _remove_custom_page()
    frappe.db.commit()
    frappe.clear_cache()
    print("ROLE_I18N ar_translations=%d client_script=%s custom_page=removed"
          % (translated, state))
