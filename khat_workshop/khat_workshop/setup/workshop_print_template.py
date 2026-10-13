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

# ترويستا ERPNext الجاهزتان: مربّع رمادي فيه شعار الشركة، وشعارها غير مرفوع
# فيُطبع مكانه «None». كانتا الافتراضي على كل مستند مطبوع.
STOCK = ("Company Letterhead", "Company Letterhead - Grey")

# علامة أن المحتوى من هذا الملف لا من صاحب الورشة: يُحدَّث ما دامت فيه
MARK = "<!-- kaj-letterhead -->"

# رأس كل مستند مطبوع، من «إعدادات الورشة». يُقرأ عند كل طباعة، فتعديل الاسم أو
# الهاتف أو الرقم الضريبي هناك يظهر على المطبوعات فوراً. Jinja: الإطار يصيّر
# محتوى الترويسة قالباً ويمرّر له المستند. تنسيق داخل الوسوم لأن القوالب
# القياسية لا تحمل أنماطنا.
HEADER_HTML = MARK + u"""
{%- set ws = frappe.get_doc("Workshop Settings") -%}
{%- set logo = ws.logo or frappe.db.get_value("Website Settings", "Website Settings", "app_logo") -%}
<table style="width: 100%; border-collapse: collapse; direction: rtl; margin-bottom: 8px;">
  <tr>
    <td style="text-align: right; vertical-align: top; line-height: 1.6;">
      <div style="font-size: 20px; font-weight: bold; color: #1a2b4a;">{{ ws.workshop_name or (doc.company if doc else "") or "خط الجزيرة" }}</div>
      {%- if ws.address %}<div style="font-size: 12px; color: #5b6675;">{{ ws.address }}</div>{% endif %}
      {%- if ws.phone %}<div style="font-size: 12px; color: #5b6675;">الهاتف: <span style="direction: ltr; unicode-bidi: embed; display: inline-block;">{{ ws.phone }}</span></div>{% endif %}
      {%- if ws.tax_number %}<div style="font-size: 12px;">الرقم الضريبي: <span style="direction: ltr; unicode-bidi: embed; display: inline-block;">{{ ws.tax_number }}</span></div>{% endif %}
    </td>
    <td style="width: 180px; text-align: left; vertical-align: top;">
      {%- if logo %}<img src="{{ logo }}" alt="" style="max-height: 70px; max-width: 170px;">{% endif %}
    </td>
  </tr>
</table>
"""


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
    """ترويسة افتراضية تحمل بيانات الورشة، إلى أن يرفع صاحبها صورة ترويسته.

    لا يُمسّ ما وضعه صاحب الورشة: صورة مرفوعة (print_template.compose يبني
    المحتوى منها)، أو محتوى كتبه بيده، أو ترويسة أخرى اختارها افتراضية.
    """
    state = []
    if frappe.db.exists("Letter Head", DEFAULT_NAME):
        doc = frappe.get_doc("Letter Head", DEFAULT_NAME)
    else:
        doc = frappe.new_doc("Letter Head")
        doc.letter_head_name = DEFAULT_NAME
        doc.disabled = 0
        doc.footer_source = "HTML"
        state.append("created")

    changed = doc.is_new()
    owners = doc.get("kaj_header_img") or (doc.content and MARK not in doc.content)
    if not owners and ((doc.content or "").strip() != HEADER_HTML.strip() or doc.source != "HTML"):
        doc.source = "HTML"
        doc.content = HEADER_HTML
        changed = True
        state.append("content")

    current = frappe.db.get_value("Letter Head", {"is_default": 1, "disabled": 0}, "name")
    if (not current or current in STOCK) and not doc.is_default:
        doc.is_default = 1
        changed = True
        state.append("default")

    if changed:
        doc.flags.ignore_permissions = True
        doc.save()

    # مستند أُنشئ قبل هذه الخطوة يحمل اسم إحدى الترويستين الجاهزتين في حقله،
    # فيُطبع بها أياً كان الافتراضي. تُعطيان المحتوى نفسه.
    for name in STOCK:
        if frappe.db.exists("Letter Head", name) and \
                (frappe.db.get_value("Letter Head", name, "content") or "").strip() != HEADER_HTML.strip():
            frappe.db.set_value("Letter Head", name, {"source": "HTML", "content": HEADER_HTML})
            state.append("stock")

    for company in frappe.get_all("Company", fields=["name", "default_letter_head"]):
        if not company.default_letter_head or company.default_letter_head in STOCK:
            frappe.db.set_value("Company", company.name, "default_letter_head", DEFAULT_NAME)
            state.append("company")
    return "+".join(state) or "ok"


def execute():
    create_custom_fields(_fields(), update=True)
    state = _ensure_default_letter_head()
    frappe.db.commit()
    frappe.clear_cache()
    print("PRINT_TEMPLATE fields=ok default_letter_head=%s" % state)
