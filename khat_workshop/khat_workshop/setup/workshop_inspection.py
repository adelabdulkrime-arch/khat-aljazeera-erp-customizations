# -*- coding: utf-8 -*-
"""Multi-point mechanical inspection carried out when a vehicle is received.

Distinct from workshop_vehicle_intake, which records *body* condition — dents
and scratches, as evidence against a later dispute. This records *mechanical*
condition: engine, cooling, gearbox, brakes, suspension, tyres, electrics,
fluids and A/C. The two answer different questions and sit side by side on the
Work Card.

The form is the workshop's own paper sheet, item for item. Keeping the owner's
groups and wording (instead of inventing a tidier list) is what makes it usable
by technicians who already fill this in on paper — they find the same lines in
the same order, and the printed output matches what the customer is used to.

The payoff is the last step: every line marked "يحتاج استبدال" becomes a
quotation line in one click, via create_quotation_from_inspection below. That
turns the inspection from a record into the thing that actually sells the work,
which is why the sheet exists in the first place.
"""

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

from khat_workshop.setup.workshop_setup import f, make_dt

# ── The sheet ────────────────────────────────────────────────────────────────
# (group label ar, group label en, [(item ar, item en), ...])
# English is kept alongside Arabic because the owner's sheet is bilingual, and
# the English term is often what is written on the part itself.
GROUPS = [
    ("المحرك واستبدال العناصر", "ENGINE / REPLACE ITEMS", [
        ("فحص مستوى زيت المحرك", "ENGINE OIL FILTER"),
        ("فحص حالة ولون زيت المحرك", "OIL COLOR"),
        ("فحص وجود تهريب زيت من المحرك", "OIL LEAK"),
        ("فحص قواعد المحرك", "MOUNTING"),
        ("فحص فلتر هواء المحرك", "AIR FILTER"),
        ("فحص سير المحرك", "ENGINE BELT"),
        ("فحص شداد وبكرات السير", "ADJUSTER BELT"),
        ("فحص نظام سحب الهواء", "AIR INTAKE SYSTEM"),
        ("فحص دخان العادم", "EXHAUST SMOKE"),
    ]),
    ("نظام التبريد", "COOLING SYSTEM", [
        ("فحص مستوى سائل التبريد", "CHECK COOLANT LEVEL"),
        ("فحص حالة سائل التبريد", "CHECK COOLANT CONDITION"),
        ("فحص الرديتر", "RADIATOR INSPECTION"),
        ("فحص خراطيم التبريد", "COOLING HOSES"),
        ("فحص تهريب سائل التبريد", "COOLANT LEAK"),
        ("فحص مروحة التبريد", "CHECK FAN COOLING"),
        ("فحص حرارة تشغيل المحرك", "ENGINE TEMPERATURE"),
    ]),
    ("ناقل الحركة والجير", "GEAR BOX", [
        ("فحص مستوى زيت الجير", "OIL LEVEL"),
        ("فحص حالة زيت الجير", "OIL GEAR"),
        ("فحص وجود تهريب زيت الجير", "GEAR LEAK"),
        ("فحص تبديلات الجير", "GEARBOX CHECK"),
        ("فحص وجود نعمة", "GEAR JERKING"),
        ("فحص قواعد الجير", "GEAR MOUNTING"),
    ]),
    ("الفرامل", "BRAKE PAD", [
        ("فحص الفحمات الأمامية", "FRONT BRAKE PAD"),
        ("فحص الفحمات الخلفية", "REAR BRAKE PAD"),
        ("فحص ديسكات الفرامل الأمامية", "FRONT DISC"),
        ("فحص ديسكات الفرامل الخلفية", "REAR DISC"),
        ("فحص مستوى زيت الفرامل", "OIL BRAKE"),
        ("فحص وجود تهريب في نظام الفرامل", "OIL BRAKE LEAKE"),
        ("فحص فرامل اليد / EPB", "HANDBRAKE CHECK"),
        ("فحص أداء الفرامل أثناء التجربة", "BRAKE NOISE"),
    ]),
    ("التعليق والتوجيه", "SUSPENSION SYSTEM", [
        ("فحص المساعدات الأمامية", "FRONT SHOCK ABSORBERS"),
        ("فحص المساعدات الخلفية", "REAR SHOCK ABSORBERS"),
        ("فحص المقصات والجلب", "UPPER ARM"),
        ("فحص Ball Joints", "BALL JOINT"),
        ("فحص Tie Rod Ends", "TIER ROD"),
        ("فحص علبة الدركسون", "STEERING RACK"),
        ("فحص وجود تهريب في نظام الباور", "POWER OIL LEAKE"),
        ("فحص رمانات العجلات", "HUB"),
        ("فحص أصوات نظام التعليق", "SUSPENSION NOISE"),
    ]),
    ("الإطارات والعجلات", "CHCEK TIRES", [
        ("فحص حالة الإطارات", "TIRE CONDITION"),
        ("فحص عمق نقشة الإطارات", "TIRE TREAD DEPTH"),
        ("فحص ضغط الإطارات", "TIRE PRESSURE"),
        ("فحص التآكل غير المنتظم", "CHECK TIRE WEAR"),
        ("فحص الإطار الاحتياطي", "SPARE TIRE"),
        ("فحص الرنجات ظاهريًا", "WHEELS (RIMS)"),
    ]),
    ("الكهرباء والبطارية", "ELECTRICAL AND BATTERY", [
        ("فحص حالة البطارية", "BATTERY CONDITUON"),
        ("فحص أقطاب وتوصيلات البطارية", "BATTERY TERMINALS"),
        ("فحص شحن الدينمو", "CHARGING SESTEM"),
        ("فحص تشغيل السلف", "STARTAR MOTOT"),
        ("فحص الأنوار الأمامية", "CHECK LIGHTS"),
        ("فحص الأنوار الخلفية وإشارات الانعطاف", "REAR LIGHT"),
        ("فحص أنوار الفرامل", "BRAKE LIGHT"),
    ]),
    ("السوائل والتجهيزات", "LIQUIDS", [
        ("فحص زيت الباور إن وجد", "POWER OIL"),
        ("فحص سائل تنظيف الزجاج", "WIPER WATER"),
        ("فحص المساحات وشفرات الزجاج", "WIPER CHECK"),
    ]),
    ("الفحص الإلكتروني والتكييف", "A/C", [
        ("فحص كمبيوتر السيارة بجهاز التشخيص OBD", "OBD CHECK"),
        ("فحص أكواد الأعطال DTC", "DTC"),
        ("فحص لمبات التحذير في لوحة العدادات", "LIGHT ON"),
        ("فحص أداء المكيف والتبريد", "CHECK AC COOLING"),
    ]),
]

# The owner's sheet carries three marks. "يحتاج متابعة" is the one that earns
# its place: it is how a technician flags something that is not a sale today
# but will be on the next visit, instead of silently passing it as good.
RESULTS = ["", "جيد", "يحتاج متابعة", "يحتاج استبدال"]

OVERALL = ["", "جيد", "يحتاج متابعة", "يحتاج إصلاح"]

# The result that feeds a quotation. Named once so the button, the checklist
# and any later report cannot drift apart on a typo.
REPLACE = "يحتاج استبدال"

# The generic service item every inspection finding hangs off.
INSPECTION_ITEM = "SRV-INSPECTION"


def _rows():
    """Flatten the sheet into the rows stamped onto a new inspection."""
    out = []
    for group_ar, group_en, items in GROUPS:
        for label_ar, label_en in items:
            out.append((group_ar, group_en, label_ar, label_en))
    return out


def _doctypes():
    make_dt("Work Card Inspection Item", istable=1, fields=[
        f("group_label", "المجموعة", "Data", read_only=1, in_list_view=1, columns=2),
        f("item_label", "البند", "Data", read_only=1, in_list_view=1, columns=3),
        f("item_label_en", "Item", "Data", read_only=1, print_hide=1),
        f("result", "النتيجة", "Select", options="\n".join(RESULTS),
          in_list_view=1, columns=2),
        f("note", "ملاحظة", "Data", in_list_view=1, columns=3),
    ])


def _fields():
    # Anchored to the intake section's last field so the mechanical inspection
    # reads directly after the body-condition block, matching the order the
    # vehicle is actually received in.
    return {"Work Card": [
        {"fieldname": "sec_inspection", "label": "الفحص الفني للمركبة",
         "fieldtype": "Section Break", "insert_after": "customer_signature",
         "collapsible": 1},
        {"fieldname": "odometer_km", "label": "عداد الكيلومترات",
         "fieldtype": "Int", "insert_after": "sec_inspection"},
        {"fieldname": "cb_inspection", "fieldtype": "Column Break",
         "insert_after": "odometer_km"},
        {"fieldname": "inspection_result", "label": "نتيجة الفحص",
         "fieldtype": "Select", "options": "\n".join(OVERALL),
         "insert_after": "cb_inspection"},
        {"fieldname": "sec_inspection_items", "fieldtype": "Section Break",
         "insert_after": "inspection_result"},
        {"fieldname": "inspection_items", "label": "بنود الفحص",
         "fieldtype": "Table", "options": "Work Card Inspection Item",
         "insert_after": "sec_inspection_items"},
        {"fieldname": "inspection_notes", "label": "ملاحظات الفحص",
         "fieldtype": "Small Text", "insert_after": "inspection_items",
         "description": "هذا الفحص مبدئي لحالة السيارة، وقد تتطلب بعض الأعطال "
                        "فحصًا تفصيليًا إضافيًا"},
    ]}


# ── Filling a blank sheet ────────────────────────────────────────────────────
# Sixty rows is far too many to add by hand, so the button stamps the whole
# sheet on at once and the technician only sets results.

@frappe.whitelist()
def load_checklist(work_card):
    """Populate an empty inspection table with the full sheet."""
    wc = frappe.get_doc("Work Card", work_card)
    if not wc.has_permission("write"):
        frappe.throw(frappe._("ليس لديك صلاحية على بطاقة العمل هذه"))

    # Never wipe results someone already recorded.
    if wc.get("inspection_items"):
        return {"added": 0, "message": "قائمة الفحص محمّلة مسبقًا"}

    for group_ar, _group_en, label_ar, label_en in _rows():
        wc.append("inspection_items", {
            "group_label": group_ar,
            "item_label": label_ar,
            "item_label_en": label_en,
        })
    wc.save(ignore_permissions=True)
    frappe.db.commit()
    return {"added": len(wc.inspection_items), "message": "تم تحميل قائمة الفحص"}


@frappe.whitelist()
def create_quotation_from_inspection(work_card):
    """Turn every line marked REPLACE into a draft quotation.

    Rates are left at zero deliberately. The inspection establishes *what*
    needs doing; what it is worth is a pricing decision, and inventing a number
    here would put a figure in front of the customer that nobody chose.
    """
    wc = frappe.get_doc("Work Card", work_card)
    if not wc.has_permission("read"):
        frappe.throw(frappe._("ليس لديك صلاحية على بطاقة العمل هذه"))

    flagged = [r for r in (wc.get("inspection_items") or []) if r.result == REPLACE]
    if not flagged:
        frappe.throw(frappe._("لا توجد بنود مؤشّرة بـ«يحتاج استبدال» في الفحص"))

    if not wc.get("customer"):
        frappe.throw(frappe._("بطاقة العمل بلا عميل — لا يمكن إنشاء عرض سعر"))

    quotation = frappe.new_doc("Quotation")
    quotation.quotation_to = "Customer"
    quotation.party_name = wc.customer

    # The `vehicle` field comes from workshop_gl_stock_integration; guarded so
    # a partial install cannot take the whole button down.
    meta = frappe.get_meta("Quotation")
    if wc.get("vehicle") and meta.has_field("vehicle"):
        quotation.vehicle = wc.vehicle

        # The WQ- series is normally applied by the client script in
        # workshop_document_numbering, which watches the `vehicle` field on the
        # *form*. Inserting server-side never fires it, so a quotation raised
        # from an inspection would silently fall back to the plain counter-sale
        # series. Set it here so it is numbered like every other
        # vehicle-linked document.
        series = "WQ-.YYYY.-"
        series_field = meta.get_field("naming_series")
        options = [l.strip() for l in (series_field.options or "").split("\n")
                   if l.strip()] if series_field else []
        if series in options:
            quotation.naming_series = series

    # Each flagged line becomes a description-carrying row against one generic
    # service item, so the customer reads the actual finding rather than a
    # catalogue code that means nothing to them.
    item_code = _inspection_item()
    for row in flagged:
        text = row.item_label
        if row.note:
            text = "%s — %s" % (text, row.note)
        quotation.append("items", {
            "item_code": item_code,
            "qty": 1,
            "rate": 0,
            "description": text,
        })

    quotation.flags.ignore_permissions = True
    quotation.insert()
    frappe.db.commit()
    return {"name": quotation.name, "items": len(flagged)}


def _inspection_item():
    """The generic service item inspection findings are billed against."""
    if frappe.db.exists("Item", INSPECTION_ITEM):
        return INSPECTION_ITEM

    group = "الخدمات" if frappe.db.exists("Item Group", "الخدمات") else "Services"
    if not frappe.db.exists("Item Group", group):
        group = frappe.db.get_value("Item Group", {"is_group": 0}, "name")

    frappe.get_doc({
        "doctype": "Item",
        "item_code": INSPECTION_ITEM,
        "item_name": "بند فحص فني",
        "item_group": group,
        "stock_uom": "Nos",
        "is_stock_item": 0,
        "is_sales_item": 1,
        "is_purchase_item": 0,
        "description": "بند ناتج عن الفحص الفني للمركبة",
    }).insert(ignore_permissions=True)
    return INSPECTION_ITEM


# ── The two buttons ─────────────────────────────────────────────────────────
# Deliberately in the "الفحص" group rather than loose on the toolbar, so they
# do not crowd the إنشاء فاتورة / عرض سعر buttons workshop_scripts already puts
# there.

INSPECTION_JS = r"""
frappe.ui.form.on('Work Card', {
    refresh: (frm)=>{
        if(frm.is_new()) return;

        if(!(frm.doc.inspection_items || []).length){
            frm.add_custom_button(__('تحميل قائمة الفحص'), ()=>{
                frappe.call({
                    method: 'khat_workshop.setup.workshop_inspection.load_checklist',
                    args: {work_card: frm.doc.name},
                    freeze: true, freeze_message: __('جاري تحميل بنود الفحص...'),
                }).then(r=>{
                    if(!r.message) return;
                    frappe.show_alert({message: r.message.message, indicator: 'green'});
                    frm.reload_doc();
                });
            }, __('الفحص'));
        }

        // Only offer the quotation once something is actually flagged, so the
        // button never appears just to answer with an error.
        let flagged = (frm.doc.inspection_items || [])
            .filter(r=>r.result === 'يحتاج استبدال').length;
        if(flagged){
            frm.add_custom_button(__('عرض سعر من الفحص') + ' (' + flagged + ')', ()=>{
                frappe.call({
                    method: 'khat_workshop.setup.workshop_inspection.create_quotation_from_inspection',
                    args: {work_card: frm.doc.name},
                    freeze: true, freeze_message: __('جاري إنشاء عرض السعر...'),
                }).then(r=>{
                    if(r.message) frappe.set_route('Form', 'Quotation', r.message.name);
                });
            }, __('الفحص'));
        }
    },
});
"""


def _client_script():
    name = "Work Card Inspection Actions"
    if frappe.db.exists("Client Script", name):
        frappe.delete_doc("Client Script", name, force=1, ignore_permissions=True)
    frappe.get_doc({
        "doctype": "Client Script", "name": name,
        "dt": "Work Card", "view": "Form", "enabled": 1,
        "script": INSPECTION_JS,
    }).insert(ignore_permissions=True)


def execute():
    _doctypes()
    create_custom_fields(_fields(), update=True)
    _inspection_item()
    _client_script()
    frappe.db.commit()
    frappe.clear_cache()
    print("INSPECTION groups=%d items=%d" % (len(GROUPS), len(_rows())))
