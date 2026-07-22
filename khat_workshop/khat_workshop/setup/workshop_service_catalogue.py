# -*- coding: utf-8 -*-
"""Replace free-text services with a real service catalogue.

Audit finding: `Work Card Service.service` was a plain Data field. Anyone could
type anything, which meant:

  * no standard pricing — the same job quoted differently by each advisor
  * no labour rate per operation
  * no analysis by service type, because "تغيير زيت" and "تغيير الزيت" and
    "تغير زيت" are three different strings

It becomes a Link to a real Item, so services are priced, reportable and
comparable — exactly like parts already were.

Done while Work Card Service holds ZERO rows. Converting a populated free-text
column into a Link later would mean reconciling every typo by hand.

Idempotent, and deliberately conservative: the field is only converted when the
child table is empty. If rows exist it reports and leaves the field alone
rather than orphaning data behind a Link that cannot resolve.
"""

import frappe

CHILD_DOCTYPE = "Work Card Service"
FIELD = "service"
ITEM_GROUP = "خدمات الورشة"

# A starting catalogue across the five service lines the workshop runs. Rates
# are left at zero on purpose: pricing is a commercial decision for the owner,
# not something a migration should invent.
SERVICES = [
    ("WS-MECH-001", "تغيير زيت وفلتر", "ميكانيكا"),
    ("WS-MECH-002", "فحص وصيانة الفرامل", "ميكانيكا"),
    ("WS-MECH-003", "صيانة نظام التعليق", "ميكانيكا"),
    ("WS-MECH-004", "فحص وصيانة المحرك", "ميكانيكا"),
    ("WS-BODY-001", "إصلاح صدمات وحوادث", "سمكرة وحوادث"),
    ("WS-BODY-002", "سحب وتقويم الهيكل", "سمكرة وحوادث"),
    ("WS-BODY-003", "استبدال قطع هيكل", "سمكرة وحوادث"),
    ("WS-PNT-001", "دهان قطعة", "دهان"),
    ("WS-PNT-002", "دهان كامل", "دهان"),
    ("WS-PNT-003", "تلميع وحماية", "دهان"),
    ("WS-ELEC-001", "فحص كهرباء عام", "كهرباء"),
    ("WS-ELEC-002", "إصلاح نظام الإضاءة", "كهرباء"),
    ("WS-ELEC-003", "بطارية ودينامو", "كهرباء"),
    ("WS-AC-001", "تعبئة غاز مكيف", "تكييف"),
    ("WS-AC-002", "إصلاح كمبروسر", "تكييف"),
    ("WS-AC-003", "تنظيف وصيانة دورة التبريد", "تكييف"),
]


def _ensure_item_group():
    if frappe.db.exists("Item Group", ITEM_GROUP):
        return
    parent = frappe.db.get_value("Item Group", {"is_group": 1, "parent_item_group": ""}, "name") \
        or "All Item Groups"
    frappe.get_doc({
        "doctype": "Item Group", "item_group_name": ITEM_GROUP,
        "parent_item_group": parent, "is_group": 0,
    }).insert(ignore_permissions=True)
    print("Created Item Group:", ITEM_GROUP)


def _seed_services():
    created = 0
    for code, name, line in SERVICES:
        if frappe.db.exists("Item", code):
            continue
        frappe.get_doc({
            "doctype": "Item", "item_code": code, "item_name": name,
            "item_group": ITEM_GROUP, "stock_uom": "Nos",
            "is_stock_item": 0,          # a service consumes no inventory
            "is_sales_item": 1,
            "is_purchase_item": 0,
            "description": "%s — %s" % (line, name),
        }).insert(ignore_permissions=True)
        created += 1
    return created


def _convert_field():
    """Data -> Link(Item), only while the child table is empty."""
    if not frappe.db.exists("DocType", CHILD_DOCTYPE):
        return "child doctype missing"

    rows = frappe.db.count(CHILD_DOCTYPE)
    doc = frappe.get_doc("DocType", CHILD_DOCTYPE)
    field = next((f for f in doc.fields if f.fieldname == FIELD), None)
    if field is None:
        return "field missing"
    if field.fieldtype == "Link" and field.options == "Item":
        return "already converted"
    if rows:
        return ("SKIPPED — %d existing rows hold free text; convert manually"
                % rows)

    field.fieldtype = "Link"
    field.options = "Item"
    doc.save(ignore_permissions=True)
    frappe.clear_cache(doctype=CHILD_DOCTYPE)
    return "converted Data -> Link(Item)"


def execute():
    _ensure_item_group()
    created = _seed_services()
    outcome = _convert_field()
    frappe.db.commit()
    print("SERVICE_CATALOGUE seeded=%d total=%d field=%s"
          % (created, len(SERVICES), outcome))
