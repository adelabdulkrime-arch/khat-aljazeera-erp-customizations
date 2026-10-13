# -*- coding: utf-8 -*-
"""يطبّق khat_workshop.forms: إخفاء حقول، قيم افتراضية، تسميات وترتيب.

كل تعديل Property Setter — ما يكتبه «تخصيص النموذج» في الإطار نفسه — أو
Custom Field لفاصل جديد. لا يُعدَّل تعريف أي مستند قياسي.

تصريحي: ما في forms.py هو ما يُطبَّق، لا أكثر. تُحفظ قائمة ما أنشأته هذه
الخطوة، وفي كل تشغيل يُحذف منها ما لم يعد مذكوراً — فحذف اسم حقل من forms.py
يُعيده إلى النموذج، ولا يتراكم إخفاءٌ قديم لا يعرف أحد مصدره.

ثلاثة فحوص تُفشل الخطوة بدل أن تمرّ بصمت:
  • اسم حقل في forms.py غير موجود في مستنده (خطأ إملائي، أو حقل أزاله تحديث)؛
  • حقل في ترتيب نموذج (layout) غير موجود؛
  • حقل إلزامي يُخفى وليس له قيمة افتراضية ولا يملؤه النظام: النموذج سيرفض
    الحفظ بسبب حقل لا يراه المستخدم.
"""

import json

import frappe
from frappe.utils import cint

from khat_workshop import forms

STATE_KEY = "kaj_forms_managed"

# حقول إلزامية يملؤها النظام عند فتح المستند أو حفظه، فإخفاؤها آمن.
# تُحقِّق من كلٍّ منها بإنشاء مستنده من الواجهة على نسخة الاختبار.
FILLED_BY_SYSTEM = {
    "naming_series", "company", "currency", "conversion_rate", "selling_price_list",
    "price_list_currency", "plc_conversion_rate", "posting_time", "order_type",
    "quotation_to", "base_net_total", "base_grand_total", "status",
    "paid_from_account_currency", "paid_to_account_currency", "source_exchange_rate",
    "target_exchange_rate", "base_paid_amount", "base_received_amount", "received_amount",
    # صفوف البنود: تُجلب من الصنف عند اختياره، وتُحسب من الكمية والسعر
    "stock_uom", "conversion_factor", "stock_qty", "base_rate", "base_amount",
}


def _setter(doctype, fieldname, prop, value, ptype):
    """ينشئ الخاصية أو يحدّثها؛ يعيد 1 إن تغيّر شيء."""
    filters = {"doc_type": doctype, "property": prop,
               "field_name": fieldname if fieldname else ["is", "not set"]}
    current = frappe.db.get_value("Property Setter", filters, "value")
    if current is not None and str(current) == str(value):
        return 0
    frappe.make_property_setter({
        "doctype": doctype,
        "doctype_or_field": "DocField" if fieldname else "DocType",
        "fieldname": fieldname, "property": prop, "value": value, "property_type": ptype,
    }, validate_fields_for_doctype=False)
    return 1


def _make_breaks(doctype, layout):
    """ينشئ الفواصل الجديدة المذكورة في الترتيب (تبويبات، أقسام، أعمدة)."""
    made, previous = 0, None
    for item in layout:
        if isinstance(item, str):
            previous = item
            continue
        fieldname, fieldtype, label = item
        if not frappe.db.exists("Custom Field", {"dt": doctype, "fieldname": fieldname}):
            frappe.get_doc({
                "doctype": "Custom Field", "dt": doctype, "fieldname": fieldname,
                "fieldtype": fieldtype, "label": label, "insert_after": previous,
            }).insert(ignore_permissions=True)
            made += 1
        else:
            name = frappe.db.get_value("Custom Field", {"dt": doctype, "fieldname": fieldname})
            if frappe.db.get_value("Custom Field", name, "label") != label:
                frappe.db.set_value("Custom Field", name, "label", label)
                made += 1
        previous = fieldname
    return made


def _apply_layout(doctype, layout, problems):
    changed = _make_breaks(doctype, layout)
    if changed:
        frappe.clear_cache(doctype=doctype)

    wanted = [item if isinstance(item, str) else item[0] for item in layout]
    existing = [df.fieldname for df in frappe.get_meta(doctype).fields]
    for name in wanted:
        if name not in existing:
            problems.append("%s: الترتيب يذكر «%s» وهو غير موجود" % (doctype, name))
    # حقل لم يُذكر في الترتيب (أضافه تحديث لاحق) يُلحق بالآخر ولا يختفي
    order = [f for f in wanted if f in existing] + [f for f in existing if f not in wanted]
    changed += _setter(doctype, None, "field_order", json.dumps(order), "Data")
    return changed, [f for f in existing if f not in wanted]


def _check_hidden_mandatory(doctype, problems):
    """حقل إلزامي مخفي — مباشرة أو تحت قسم/تبويب مخفي — بلا ما يملؤه."""
    section_hidden = tab_hidden = False
    for df in frappe.get_meta(doctype).fields:
        if df.fieldtype == "Tab Break":
            tab_hidden, section_hidden = bool(cint(df.hidden)), False
        elif df.fieldtype == "Section Break":
            section_hidden = bool(cint(df.hidden))
        hidden = cint(df.hidden) or section_hidden or tab_hidden
        if hidden and cint(df.reqd) and not df.default and not df.fetch_from \
                and df.fieldname not in FILLED_BY_SYSTEM:
            problems.append("%s: «%s» إلزامي ومخفي بلا قيمة افتراضية" % (doctype, df.fieldname))


def execute():
    problems, managed, changed, appended = [], [], 0, {}

    for doctype in forms.doctypes():
        if not frappe.db.exists("DocType", doctype):
            continue
        conf = forms.FORMS.get(doctype, {})

        if conf.get("layout"):
            c, extra = _apply_layout(doctype, conf["layout"], problems)
            changed += c
            managed.append([doctype, "", "field_order"])
            if extra:
                appended[doctype] = extra

        names = {df.fieldname for df in frappe.get_meta(doctype).fields}
        own = set(conf.get("hide", []))

        for fieldname in forms.hidden_fields(doctype):
            if fieldname not in names:
                # المشترك يُطبَّق حيث وُجد؛ الخاص بالنموذج يجب أن يوجد
                if fieldname in own:
                    problems.append("%s: «%s» في hide وهو غير موجود" % (doctype, fieldname))
                continue
            changed += _setter(doctype, fieldname, "hidden", 1, "Check")
            managed.append([doctype, fieldname, "hidden"])

        for fieldname, value in (conf.get("defaults") or {}).items():
            if fieldname not in names:
                problems.append("%s: «%s» في defaults وهو غير موجود" % (doctype, fieldname))
                continue
            changed += _setter(doctype, fieldname, "default", value, "Text")
            managed.append([doctype, fieldname, "default"])

        for fieldname, label in (conf.get("labels") or {}).items():
            if fieldname not in names:
                problems.append("%s: «%s» في labels وهو غير موجود" % (doctype, fieldname))
                continue
            changed += _setter(doctype, fieldname, "label", label, "Data")
            managed.append([doctype, fieldname, "label"])

        for fieldname, props in (conf.get("props") or {}).items():
            if fieldname not in names:
                problems.append("%s: «%s» في props وهو غير موجود" % (doctype, fieldname))
                continue
            for prop, value in props.items():
                ptype = ("Int" if prop == "columns" else "Check") if isinstance(value, int) else "Data"
                changed += _setter(doctype, fieldname, prop, value, ptype)
                managed.append([doctype, fieldname, prop])

        frappe.clear_cache(doctype=doctype)
        _check_hidden_mandatory(doctype, problems)

    # ما أنشأته تشغيلة سابقة ولم يعد في forms.py يُزال
    previous = json.loads(frappe.db.get_default(STATE_KEY) or "[]")
    current = {tuple(m) for m in managed}
    removed = 0
    for doctype, fieldname, prop in previous:
        if (doctype, fieldname, prop) in current:
            continue
        frappe.db.delete("Property Setter", {
            "doc_type": doctype, "property": prop,
            "field_name": fieldname if fieldname else ["is", "not set"]})
        frappe.clear_cache(doctype=doctype)
        removed += 1
    frappe.db.set_default(STATE_KEY, json.dumps(managed))

    frappe.db.commit()
    print("FORMS doctypes=%d managed=%d changed=%d removed=%d"
          % (len(forms.doctypes()), len(managed), changed, removed))
    for doctype, extra in appended.items():
        print("FORMS %s: حقول خارج الترتيب أُلحقت بآخره: %s" % (doctype, ", ".join(extra)))
    if problems:
        frappe.throw("forms.py:\n" + "\n".join(problems))
