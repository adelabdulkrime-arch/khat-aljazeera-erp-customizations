# -*- coding: utf-8 -*-
"""Turns a Work Card's diagnosed services + parts into a Sales Invoice or
Quotation automatically -- the "آلية" (automatic) flow he asked for
(2026-08-25) after describing how Mazoon does it: diagnose -> parts get
identified and deducted from stock -> invoice appears from that, priced by
the rates the owner already set on each Item.

Half of this already existed and worked: submitting a Work Card creates a
real Stock Entry and deducts parts (see workshop_gl_stock_integration.py).
The other half was missing entirely -- there was no automatic path from a
Work Card into a customer-facing document at all after
workshop_retire_shadow.py removed the old (buggy) Repair Invoice mirror.

Deliberately built server-side, not as client-side JS field-copying like the
old Repair Invoice mirror was. Building it as doc.insert() on a real Sales
Invoice / Quotation means ERPNext's own controller computes item_name,
description, uom, taxes and totals -- the exact things that were buggy
before precisely because they were reimplemented by hand in JS instead of
left to the framework. That is also why these functions are plain
@frappe.whitelist() endpoints rather than another setup step: there is no
data to seed and nothing to migrate, only something to call from a button
(see the "إنشاء فاتورة" / "إنشاء عرض سعر" buttons workshop_scripts.py adds
to the Work Card form) -- so, unlike its sibling files, this one is not
registered in setup/__init__.py's STEPS.

Invoice creation is deliberately gated on the Work Card being submitted
(docstatus == 1): that is the point at which parts have actually left the
warehouse, matching the exact sequence he described -- diagnose, deduct,
then bill. A Quotation has no such gate, since it is normally produced
*before* work (and stock deduction) happens at all.
"""

import frappe

NAMING = {
    "Sales Invoice": "WI-.YYYY.-",
    "Quotation": "WQ-.YYYY.-",
}


def _series_available(doctype, series):
    field = frappe.get_meta(doctype).get_field("naming_series")
    options = [l.strip() for l in (field.options or "").split("\n") if l.strip()] if field else []
    return series in options


def _append_rows(target_doc, work_card):
    added = 0
    for row in (work_card.services or []):
        if not row.service or not row.qty:
            continue
        target_doc.append("items", {
            "item_code": row.service, "qty": row.qty, "rate": row.rate or 0,
        })
        added += 1
    for row in (work_card.parts or []):
        if not row.item or not row.qty:
            continue
        target_doc.append("items", {
            "item_code": row.item, "qty": row.qty, "rate": row.rate or 0,
        })
        added += 1
    return added


@frappe.whitelist()
def create_sales_invoice(work_card):
    wc = frappe.get_doc("Work Card", work_card)
    if not wc.has_permission("read"):
        frappe.throw(frappe._("ليس لديك صلاحية على بطاقة العمل هذه"))
    if wc.docstatus != 1:
        frappe.throw(frappe._("لازم تعتمد بطاقة العمل أولاً (لخصم القطع من المخزون) قبل إنشاء الفاتورة"))
    if not wc.customer:
        frappe.throw(frappe._("بطاقة العمل بدون عميل محدد"))

    existing = frappe.db.get_value(
        "Sales Invoice", {"work_card": work_card, "docstatus": ["!=", 2]}, "name")
    if existing:
        return existing

    inv = frappe.new_doc("Sales Invoice")
    inv.customer = wc.customer
    if hasattr(wc, "vehicle"):
        inv.vehicle = wc.vehicle
    inv.work_card = wc.name
    if _series_available("Sales Invoice", NAMING["Sales Invoice"]):
        inv.naming_series = NAMING["Sales Invoice"]

    if not _append_rows(inv, wc):
        frappe.throw(frappe._("لا توجد خدمات أو قطع مسجّلة على بطاقة العمل لإنشاء فاتورة منها"))

    if wc.discount:
        inv.apply_discount_on = "Grand Total"
        inv.discount_amount = wc.discount

    inv.insert(ignore_permissions=True)
    frappe.db.commit()
    return inv.name


@frappe.whitelist()
def create_quotation(work_card):
    wc = frappe.get_doc("Work Card", work_card)
    if not wc.has_permission("read"):
        frappe.throw(frappe._("ليس لديك صلاحية على بطاقة العمل هذه"))
    if not wc.customer:
        frappe.throw(frappe._("بطاقة العمل بدون عميل محدد"))

    existing = frappe.db.get_value(
        "Quotation", {"work_card": work_card, "docstatus": ["!=", 2]}, "name")
    if existing:
        return existing

    qtn = frappe.new_doc("Quotation")
    qtn.quotation_to = "Customer"
    qtn.party_name = wc.customer
    if hasattr(wc, "vehicle"):
        qtn.vehicle = wc.vehicle
    qtn.work_card = wc.name
    if _series_available("Quotation", NAMING["Quotation"]):
        qtn.naming_series = NAMING["Quotation"]

    if not _append_rows(qtn, wc):
        frappe.throw(frappe._("لا توجد خدمات أو قطع مسجّلة على بطاقة العمل لإنشاء عرض سعر منها"))

    if wc.discount:
        qtn.apply_discount_on = "Grand Total"
        qtn.discount_amount = wc.discount

    qtn.insert(ignore_permissions=True)
    frappe.db.commit()
    return qtn.name
