# -*- coding: utf-8 -*-
"""Align the role list with Mazoon's fourteen, Arabic and English.

Mazoon's Roles screen lists exactly fourteen roles, each with an Arabic and an
English display name. Ours had grown piecemeal: six workshop roles (some named
in Arabic, one in English), the rest missing, and a few English translations
that did not match Mazoon ("System Administrator" vs "Super Admin", "Garage
Manager" vs "Workshop Manager", "Staff" vs "Employee"...).

This reconciles the two. Each row is (frappe_role, arabic, english):

  * frappe_role is the actual Role record. Where a suitable one already exists —
    the five Arabic workshop roles, and the built-ins HR Manager, Sales Manager,
    Workshop Manager, Employee — it is reused, so no duplicate is created and no
    existing permission assignment is disturbed.
  * arabic / english are the display names. They are registered as translations
    of the role name, so the same role reads correctly in either interface
    language — exactly the Arabic-name / English-name pair Mazoon shows.

Translations are upserted, not inserted-if-missing, so the earlier mismatched
English labels are corrected rather than left in place.

NOTE ON PERMISSIONS: this aligns the role *list and labels* only. What each role
is allowed to see and do — Mazoon's permission matrix — is a separate, deeper
piece of work (RBAC) and is deliberately not attempted here. A newly created
role grants nothing until its permissions are set; the real administrator power
stays with System Manager.
"""

import frappe

# (frappe_role_name, arabic_display, english_display)
# frappe_role_name in Arabic  -> a workshop role we own; created if absent.
# frappe_role_name in English -> an existing built-in we reuse, never recreated.
ROLES = [
    ("مدير النظام",          "مدير النظام",          "Super Admin"),
    ("محاسب",               "محاسب",               "Accountant"),
    ("HR Manager",          "مدير الموارد البشرية",  "HR Manager"),
    ("Sales Manager",       "مدير المبيعات",         "Sales Manager"),
    ("مندوب مبيعات",        "مندوب مبيعات",         "Sales Representative"),
    ("كاشير",               "كاشير",               "Cashier"),
    ("مدير المستودع",       "مدير المستودع",       "Warehouse Manager"),
    ("مسؤول المشتريات",     "مسؤول المشتريات",     "Purchasing Officer"),
    ("Workshop Manager",    "مدير الورشة",          "Workshop Manager"),
    ("فني ورشة",            "فني ورشة",            "Workshop Technician"),
    ("موظف استقبال الورشة", "موظف استقبال الورشة", "Workshop Receptionist"),
    ("مسؤول",               "مسؤول",               "Admin"),
    ("مدير",                "مدير",                "Manager"),
    ("Employee",            "موظف",                "Employee"),
]


def _has_arabic(text):
    return any("؀" <= ch <= "ۿ" for ch in text)


def _ensure_role(name):
    """Create a desk role if it is one of ours and not already present."""
    if frappe.db.exists("Role", name):
        return False
    frappe.get_doc({
        "doctype": "Role",
        "role_name": name,
        "desk_access": 1,
        "disabled": 0,
        "is_custom": 1,
    }).insert(ignore_permissions=True)
    return True


def _upsert_translation(source, language, target):
    """Set source->target for a language, correcting any stale value."""
    if source == target:
        return  # identity, nothing to translate
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


def execute():
    created = 0
    for name, ar, en in ROLES:
        # Only ever create roles that are ours (Arabic-named). Reused built-ins
        # (English-named) must already exist; if a rename upstream removed one,
        # skip rather than spawn a stray duplicate.
        if _has_arabic(name):
            created += _ensure_role(name)
        elif not frappe.db.exists("Role", name):
            # expected built-in missing — leave a trace, do not fabricate it
            print("ROLES warn: expected built-in role %r absent" % name)
            continue

        _upsert_translation(name, "en", en)
        _upsert_translation(name, "ar", ar)

    frappe.db.commit()
    frappe.clear_cache()
    print("ROLES aligned=%d created=%d" % (len(ROLES), created))
