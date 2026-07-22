# -*- coding: utf-8 -*-
"""Retire the parallel ("shadow") bookkeeping doctypes.

Repair Invoice, Workshop Quotation, Workshop Payment and Service Package
duplicated documents ERPNext already provides. Every transaction was recorded
twice — once in the shadow doctype and once, via a one-way bridge, in the real
one. That bridge is where the serious defects lived: invoices posted with no
tax, every line collapsed to a single WORKSHOP-SERVICE item, no cancellation
handling, and submit() inside a Before Save hook that could leave orphaned
submitted documents behind.

Users now work directly in Quotation, Sales Invoice and Payment Entry, with the
workshop link carried by custom fields on those documents.

SAFETY: a doctype is only dropped when it holds ZERO documents. If anyone has
entered real data, this step reports it and leaves the doctype untouched rather
than destroying it — recovering the data matters more than finishing the
migration on schedule.

Idempotent: once a doctype is gone the step simply reports nothing to do.
"""

import frappe

# Child tables first — a parent cannot be dropped while its table doctype is
# still referenced.
RETIRED = [
    "Repair Invoice Item",
    "Repair Invoice",
    "Workshop Quotation Item",
    "Workshop Quotation",
    "Workshop Payment",
    "Service Package Item",
    "Service Package",
]

# Custom fields that pointed at the shadow documents. Leaving them behind would
# mean dangling Link fields to doctypes that no longer exist.
STALE_CUSTOM_FIELDS = [
    "Repair Invoice-sales_invoice",
    "Workshop Payment-payment_entry",
]


def _row_count(doctype):
    """Document count, tolerating a table that was already dropped."""
    try:
        return frappe.db.count(doctype)
    except Exception:
        return 0


def execute():
    for name in STALE_CUSTOM_FIELDS:
        if frappe.db.exists("Custom Field", name):
            frappe.delete_doc("Custom Field", name, force=1, ignore_permissions=True)
            print("removed stale Custom Field:", name)

    dropped, kept, absent = [], [], []

    for doctype in RETIRED:
        if not frappe.db.exists("DocType", doctype):
            absent.append(doctype)
            continue

        count = _row_count(doctype)
        if count:
            # Real data exists — refuse to destroy it.
            kept.append("%s (%d docs)" % (doctype, count))
            continue

        frappe.delete_doc("DocType", doctype, force=1, ignore_permissions=True)
        dropped.append(doctype)

    frappe.db.commit()
    frappe.clear_cache()

    print("RETIRE_SHADOW dropped=%s kept_with_data=%s already_absent=%s"
          % (dropped or "none", kept or "none", len(absent)))

    if kept:
        print("WARNING: the above still hold documents and were NOT dropped. "
              "Migrate that data onto the native ERPNext documents first.")
