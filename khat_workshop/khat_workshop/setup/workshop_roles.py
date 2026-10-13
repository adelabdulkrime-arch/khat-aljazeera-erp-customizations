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

from khat_workshop import roles

# (frappe_role_name, arabic_display, english_display) — من khat_workshop/roles.py،
# حيث يُعرَّف كل مسمّى وظيفي مع ما يحمله من أدوار قياسية.
# frappe_role_name in Arabic  -> a workshop role we own; created if absent.
# frappe_role_name in English -> an existing built-in we reuse, never recreated.
ROLES = [(job[0], job[1], job[2]) for job in roles.JOBS]


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


# English role labels from before the Mazoon alignment. Their source texts are
# no longer used for display, so the leftover Translation rows are dead — remove
# them so nothing can render a role under an old name.
STALE_EN_LABELS = (
    "System Administrator", "Head of Sales", "Garage Manager",
    "Supervisor", "Staff", "Director",
)


def _purge_stale_translations():
    purged = 0
    for name in frappe.get_all(
        "Translation",
        filters={"language": "en", "translated_text": ["in", STALE_EN_LABELS]},
        pluck="name",
    ):
        frappe.delete_doc("Translation", name, force=1, ignore_permissions=True)
        purged += 1
    return purged


def _sync_users():
    """يمنح كل مستخدم قائم الأدوار القياسية التي يحملها مسمّاه الوظيفي.

    المستخدمون الجدد يمرّون بـ roles.sync_implied عند الحفظ (hooks.py)؛ هذه
    للحسابات التي أُنشئت قبل ذلك، ولأي تغيير في roles.IMPLIED بعد نشره.
    """
    synced = 0
    for name in frappe.get_all(
            "User", filters={"name": ["not in", ("Administrator", "Guest")]}, pluck="name"):
        doc = frappe.get_doc("User", name)
        before = sorted(row.role for row in doc.roles)
        roles.sync_implied(doc)
        if sorted(row.role for row in doc.roles) != before:
            doc.flags.ignore_permissions = True
            doc.flags.no_welcome_mail = True
            doc.save()
            synced += 1
    return synced


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

    purged = _purge_stale_translations()
    synced = _sync_users()

    frappe.db.commit()
    frappe.clear_cache()
    print("ROLES aligned=%d created=%d stale_purged=%d users_synced=%d"
          % (len(ROLES), created, purged, synced))
