# -*- coding: utf-8 -*-
"""Add the one field Frappe is missing for branding: the login background.

Logo, favicon and splash already exist on Website Settings; only the full-page
login background does not. This adds it, right after splash_image so the whole
branding set sits together on one screen. khat_workshop.branding paints it onto
the login page.

The upload itself stays the owner's job — we cannot invent their logo — but by
adding the field and surfacing Website Settings through an Arabic tile
(workshop_general_settings), everything a workshop needs to brand the system
lives in one reachable place instead of two English settings pages.
"""

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def _fields():
    return {"Website Settings": [{
        "fieldname": "login_background",
        "label": "خلفية صفحة تسجيل الدخول",
        "fieldtype": "Attach Image",
        "insert_after": "splash_image",
        "description": "صورة تملأ خلفية صفحة الدخول. اختياري — يُترك فارغًا للمظهر الافتراضي.",
    }]}


# The PWA icons already ship with the app, so the workshop's own mark can be
# wired up without waiting for an upload. Before this, the login screen showed
# Frappe's generic box icon and the browser tab read "Frappe" / "ERPNext" —
# nothing identified the system as the workshop's, which reads as unfinished to
# a client being shown the product.
LOGO = "/assets/khat_workshop/icons/icon-192.png"
FAVICON = "/assets/khat_workshop/icons/icon-192.png"
SPLASH = "/assets/khat_workshop/icons/icon-512.png"
APP_NAME = "خط الجزيرة"


def _identity():
    """Point Website/System Settings at the workshop's own name and mark.

    Only fills blanks: anything the owner has already set — their real logo,
    a chosen app name — is left alone, so re-running never undoes their work.
    """
    applied = []

    ws = frappe.get_single("Website Settings")
    for field, value in (("app_logo", LOGO), ("favicon", FAVICON),
                         ("splash_image", SPLASH), ("app_name", APP_NAME)):
        if not ws.get(field) or (field == "app_name" and ws.get(field) == "Frappe"):
            ws.set(field, value)
            applied.append(field)
    if applied:
        ws.flags.ignore_permissions = True
        ws.save()

    # System Settings.app_name is what the desk header and browser title show;
    # it defaults to "ERPNext" and is separate from the Website Settings one.
    current = frappe.db.get_single_value("System Settings", "app_name")
    if not current or current in ("ERPNext", "Frappe"):
        frappe.db.set_single_value("System Settings", "app_name", APP_NAME)
        applied.append("system_app_name")

    return applied


def execute():
    create_custom_fields(_fields(), update=True)
    applied = _identity()
    frappe.db.commit()
    frappe.clear_cache()
    print("BRANDING login_background field=ok identity=%s" % (applied or "already set"))
