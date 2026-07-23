# -*- coding: utf-8 -*-
"""The print-template screen: header, footer and stamp uploads on a Letter Head.

Adds the three Attach fields that khat_workshop.print_template composes into the
printed header and footer, and makes sure a default letter head exists so the
owner has a row to edit — the same "القالب الافتراضي" starting point Mazoon
shows. The "قوالب الطباعة" tile in General Settings already opens the Letter
Head list, so no new navigation is needed.

The upload of the actual artwork stays with the owner; this only builds the
place to put it.
"""

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

DEFAULT_NAME = "القالب الافتراضي"


def _fields():
    return {"Letter Head": [
        {"fieldname": "kaj_print_sec", "label": "قالب الطباعة (خط الجزيرة)",
         "fieldtype": "Section Break", "insert_after": "disabled",
         "description": "ارفع صور الترويسة العلوية والسفلية والختم — تظهر على كل مستند مطبوع."},
        {"fieldname": "kaj_header_img", "label": "صورة الترويسة العلوية (الهيدر)",
         "fieldtype": "Attach Image", "insert_after": "kaj_print_sec"},
        {"fieldname": "kaj_stamp_img", "label": "صورة الختم الرسمي",
         "fieldtype": "Attach Image", "insert_after": "kaj_header_img"},
        {"fieldname": "kaj_cb_print", "fieldtype": "Column Break",
         "insert_after": "kaj_stamp_img"},
        {"fieldname": "kaj_footer_img", "label": "صورة الترويسة السفلية (الفوتر)",
         "fieldtype": "Attach Image", "insert_after": "kaj_cb_print"},
    ]}


def _ensure_default_letter_head():
    """Give the owner a default letter head to edit, if none exists at all."""
    if frappe.db.count("Letter Head"):
        return "exists"
    frappe.get_doc({
        "doctype": "Letter Head",
        "letter_head_name": DEFAULT_NAME,
        "is_default": 1,
        "disabled": 0,
        # source/footer_source stay HTML; print_template.compose fills the
        # content once the owner uploads images.
        "source": "HTML",
        "footer_source": "HTML",
    }).insert(ignore_permissions=True)
    return "created"


def execute():
    create_custom_fields(_fields(), update=True)
    state = _ensure_default_letter_head()
    frappe.db.commit()
    frappe.clear_cache()
    print("PRINT_TEMPLATE fields=ok default_letter_head=%s" % state)
