# -*- coding: utf-8 -*-
"""Make the Work Card a controlled document instead of a free-form record.

Audit finding #1: the Work Card was not submittable. It had no docstatus, so a
"closed" job card stayed editable by anyone, forever, with no lock — and every
financial figure derived from it inherited that weakness.

This turns submission into the act of approval, using Frappe's native
submit/cancel machinery rather than a bespoke workflow:

    Draft (docstatus 0)      estimate, edit freely
    Submitted (docstatus 1)  approved -> parts issue fires -> record LOCKED
    Cancelled (docstatus 2)  reversal -> linked Stock Entry cancelled

A small set of fields stays editable after submit, because a workshop must be
able to move a job through its operational states and push a delivery date
without unlocking the commercial content of the card.

Idempotent. Safe to re-run on every migrate.
"""

import frappe

DOCTYPE = "Work Card"

# Operational fields that must remain editable after approval. Deliberately
# excludes anything with financial meaning: parts, services, totals, discount.
ALLOW_ON_SUBMIT = (
    "status",
    "expected_delivery",
    "diagnosis",
    "notes",
    "stock_entry",
)


def execute():
    if not frappe.db.exists("DocType", DOCTYPE):
        print("WORK_CARD_CONTROL skipped — %s does not exist" % DOCTYPE)
        return

    # Refuse to change the document class underneath existing records. Flipping
    # is_submittable while drafts exist would leave them in an ambiguous state.
    existing = frappe.db.count(DOCTYPE)

    doc = frappe.get_doc("DocType", DOCTYPE)
    changed = []

    if not doc.is_submittable:
        if existing:
            print("WORK_CARD_CONTROL WARNING: %d existing %s records — not "
                  "flipping is_submittable automatically. Migrate them first."
                  % (existing, DOCTYPE))
        else:
            doc.is_submittable = 1
            changed.append("is_submittable=1")

    for field in doc.fields:
        if field.fieldname in ALLOW_ON_SUBMIT and not field.allow_on_submit:
            field.allow_on_submit = 1
            changed.append("allow_on_submit:%s" % field.fieldname)

    if changed:
        doc.save(ignore_permissions=True)
        frappe.db.commit()
        frappe.clear_cache(doctype=DOCTYPE)

    print("WORK_CARD_CONTROL submittable=%s changed=%s existing_records=%d"
          % (frappe.db.get_value("DocType", DOCTYPE, "is_submittable"),
             changed or "none", existing))
