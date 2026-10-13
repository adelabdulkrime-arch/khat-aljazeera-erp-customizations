# -*- coding: utf-8 -*-
"""خانات البحث السريع فوق القوائم، من khat_workshop.lists.

فوق كل قائمة صفّ خانات يبحث بها المستخدم دون فتح نافذة التصفية. الإطار يضع
فيه كل حقل معلَّم «in_standard_filter» في تعريف المستند: قائمة العملاء عرضت
«مجموعة العميل» و«الإقليم» — تصنيفان لا تستعملهما الورشة — ولم تعرض رقم
الجوال الذي يُبحث به عن العميل فعلاً.

هذه الخطوة تجعل الخانات ما في lists.py بالضبط، بخاصية Property Setter على
الحقل (الطريقة التي يدعمها الإطار، وتبقى بعد تحديثه).

وتتحقق في الطريق من أن كل حقل مذكور في lists.py — عموداً أو خانة بحث — موجود
فعلاً في مستنده، وتفشل إن لم يكن: اسم حقل خاطئ هناك لا يُظهر خطأً في
الواجهة، يختفي العمود بصمت.
"""

import frappe
from frappe.utils import cint

from khat_workshop.lists import LISTS

# أعمدة ليست حقولاً في تعريف المستند
SPECIAL = ("name", "creation", "modified")


def _set(doctype, fieldname, value):
    frappe.make_property_setter({
        "doctype": doctype, "doctype_or_field": "DocField", "fieldname": fieldname,
        "property": "in_standard_filter", "value": value, "property_type": "Check",
    }, validate_fields_for_doctype=False)


def execute():
    changed, unknown = 0, []

    for doctype, conf in LISTS.items():
        if not frappe.db.exists("DocType", doctype):
            continue
        meta = frappe.get_meta(doctype)
        names = {df.fieldname for df in meta.fields}
        wanted = set(conf.get("filters") or [])

        referenced = set(wanted) | {conf["subject"]} if conf.get("subject") else set(wanted)
        referenced |= {c for c in conf.get("columns") or []
                       if c not in SPECIAL and not c.startswith("@")}
        unknown += ["%s.%s" % (doctype, f) for f in sorted(referenced - names)]

        for df in meta.fields:
            want = 1 if df.fieldname in wanted else 0
            if cint(df.in_standard_filter) != want:
                _set(doctype, df.fieldname, want)
                changed += 1
        if changed:
            frappe.clear_cache(doctype=doctype)

    frappe.db.commit()
    print("LISTS doctypes=%d quick_filters_changed=%d" % (len(LISTS), changed))
    if unknown:
        frappe.throw("lists.py يذكر حقولاً غير موجودة: " + ", ".join(unknown))
