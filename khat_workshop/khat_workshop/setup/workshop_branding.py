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


def execute():
    create_custom_fields(_fields(), update=True)
    frappe.db.commit()
    frappe.clear_cache()
    print("BRANDING login_background field=ok")
