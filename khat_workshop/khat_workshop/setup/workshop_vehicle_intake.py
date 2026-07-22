# -*- coding: utf-8 -*-
"""Record the condition of a vehicle the moment it enters the workshop.

The dispute this prevents is routine and expensive: the customer collects the
car, points at a scratch, and says it happened here. With nothing on file the
workshop either pays or argues, and for a body and paint shop that argument
arrives regularly. Every panel checked and photographed at intake, with the
customer's signature against it, ends the argument before it starts.

Deliberately NOT allow_on_submit. Everything else we made editable after
submit because the job evolves — this must not. A condition record that can be
changed after the fact is worth nothing as evidence, which is the entire
reason it exists.

Enforcement lives in khat_workshop.intake: a card cannot be submitted until
someone states the condition. Ticking "no visible damage" satisfies it in one
click, so a clean car costs nobody any time — but it is now a deliberate
statement rather than an empty field.
"""

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

from khat_workshop.setup.workshop_setup import f, make_dt

# Walk the car clockwise from the front. Matching the order someone actually
# inspects in keeps the form quick to fill and hard to skip a panel.
ZONES = [
    "الصدام الأمامي", "الكبوت", "الرفرف الأمامي الأيمن", "الباب الأمامي الأيمن",
    "الباب الخلفي الأيمن", "الجناح الخلفي الأيمن", "الصدام الخلفي", "الشنطة",
    "الجناح الخلفي الأيسر", "الباب الخلفي الأيسر", "الباب الأمامي الأيسر",
    "الرفرف الأمامي الأيسر", "السقف", "الزجاج الأمامي", "المرايا", "الجنوط",
]

CONDITIONS = ["خدش", "انبعاج", "كسر", "صدأ", "مفقود", "دهان سابق"]

FUEL_LEVELS = ["", "فارغ", "ربع", "نصف", "ثلاثة أرباع", "ممتلئ"]


def _doctypes():
    make_dt("Work Card Damage", istable=1, fields=[
        f("zone", "المنطقة", "Select", options="\n".join(ZONES),
          reqd=1, in_list_view=1, columns=3),
        f("condition", "الحالة", "Select", options="\n".join(CONDITIONS),
          reqd=1, in_list_view=1, columns=2),
        f("note", "ملاحظة", "Data", in_list_view=1, columns=4),
        f("photo", "صورة", "Attach Image"),
    ])

    make_dt("Work Card Intake Photo", istable=1, fields=[
        f("image", "الصورة", "Attach Image", reqd=1, in_list_view=1, columns=4),
        f("caption", "الوصف", "Data", in_list_view=1, columns=5),
    ])


def _fields():
    return {"Work Card": [
        {"fieldname": "sec_intake", "label": "حالة المركبة عند الاستلام",
         "fieldtype": "Section Break", "insert_after": "status"},
        {"fieldname": "fuel_level", "label": "مستوى الوقود",
         "fieldtype": "Select", "options": "\n".join(FUEL_LEVELS),
         "insert_after": "sec_intake"},
        {"fieldname": "cb_intake", "fieldtype": "Column Break",
         "insert_after": "fuel_level"},
        {"fieldname": "no_visible_damage", "label": "لا توجد أضرار ظاهرة",
         "fieldtype": "Check", "insert_after": "cb_intake",
         "description": "أقرّ الفاحص بعدم وجود أي ضرر ظاهر عند الاستلام"},
        {"fieldname": "damages", "label": "الأضرار المسجّلة",
         "fieldtype": "Table", "options": "Work Card Damage",
         "insert_after": "no_visible_damage"},
        {"fieldname": "intake_photos", "label": "صور الاستلام",
         "fieldtype": "Table", "options": "Work Card Intake Photo",
         "insert_after": "damages"},
        {"fieldname": "intake_notes", "label": "ملاحظات الاستلام",
         "fieldtype": "Small Text", "insert_after": "intake_photos"},
        {"fieldname": "customer_signature", "label": "توقيع العميل بالاستلام",
         "fieldtype": "Signature", "insert_after": "intake_notes",
         "description": "توقيع العميل إقرارًا بالحالة المسجّلة أعلاه"},
    ]}


def execute():
    _doctypes()
    create_custom_fields(_fields(), update=True)
    frappe.db.commit()
    frappe.clear_cache()
    print("VEHICLE_INTAKE zones=%d conditions=%d fields=ok"
          % (len(ZONES), len(CONDITIONS)))
