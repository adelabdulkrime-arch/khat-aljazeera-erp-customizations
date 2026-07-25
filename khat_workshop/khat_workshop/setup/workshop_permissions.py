# -*- coding: utf-8 -*-
"""Give the workshop roles the permissions their job needs — Mazoon's matrix,
done the Frappe way.

Until now the fourteen roles were labels only: a user holding just "كاشير"
could see nothing. This grants each operational role a sensible set of doctype
permissions so a staff member can do their work and no more.

Purely additive. Frappe unions permissions across a user's roles, so granting a
role access never removes anyone's: the owner (System Manager) is unaffected,
and a role-restricted staff member simply gains what their role allows. Fine
tuning — "a technician sees only his own cards" and the like — is a later pass;
this establishes the baseline.

Idempotent: add_permission creates the rule if absent, and the properties are
set each run so a changed matrix re-applies cleanly.
"""

import frappe
from frappe.permissions import add_permission, update_permission_property

# Permission tiers, widening outward.
READ = {"read": 1, "report": 1, "export": 1, "print": 1}
EDIT = dict(READ, write=1, create=1)
SUBMIT = dict(EDIT, submit=1, cancel=1, amend=1)
FULL = dict(SUBMIT, delete=1, email=1, share=1)

# (role, doctype, tier). Doctypes that may be absent are guarded at apply time.
MATRIX = [
    # ── مدير الورشة / Workshop Manager — runs the workshop end to end ──
    ("Workshop Manager", "Work Card", SUBMIT),
    ("Workshop Manager", "Customer Vehicle", FULL),
    ("Workshop Manager", "Workshop Technician", FULL),
    ("Workshop Manager", "Workshop Package", FULL),
    ("Workshop Manager", "Work Card Status", EDIT),
    ("Workshop Manager", "Customer", EDIT),
    ("Workshop Manager", "Quotation", SUBMIT),
    ("Workshop Manager", "Sales Invoice", SUBMIT),
    ("Workshop Manager", "Payment Entry", SUBMIT),
    ("Workshop Manager", "Item", READ),
    ("Workshop Manager", "Letter Head", READ),

    # ── موظف استقبال الورشة / Workshop Receptionist — intake only ──
    ("موظف استقبال الورشة", "Customer", EDIT),
    ("موظف استقبال الورشة", "Customer Vehicle", EDIT),
    ("موظف استقبال الورشة", "Work Card", EDIT),
    ("موظف استقبال الورشة", "Quotation", EDIT),
    ("موظف استقبال الورشة", "Item", READ),

    # ── فني ورشة / Workshop Technician — works the cards, no money, no delete ──
    ("فني ورشة", "Work Card", EDIT),
    ("فني ورشة", "Customer Vehicle", READ),
    ("فني ورشة", "Workshop Technician", READ),
    ("فني ورشة", "Item", READ),

    # ── محاسب / Accountant ──
    ("محاسب", "Sales Invoice", SUBMIT),
    ("محاسب", "Purchase Invoice", SUBMIT),
    ("محاسب", "Payment Entry", SUBMIT),
    ("محاسب", "Journal Entry", SUBMIT),
    ("محاسب", "Customer", EDIT),
    ("محاسب", "Supplier", EDIT),
    ("محاسب", "Item", READ),

    # ── كاشير / Cashier — takes payments, raises invoices, no cancel/delete ──
    ("كاشير", "Payment Entry", EDIT),
    ("كاشير", "Sales Invoice", EDIT),
    ("كاشير", "Customer", READ),

    # ── مدير المستودع / Warehouse Manager ──
    ("مدير المستودع", "Item", FULL),
    ("مدير المستودع", "Warehouse", EDIT),
    ("مدير المستودع", "Stock Entry", SUBMIT),
    ("مدير المستودع", "Purchase Receipt", SUBMIT),
    ("مدير المستودع", "Material Request", SUBMIT),
    ("مدير المستودع", "Stock Reconciliation", SUBMIT),

    # ── مسؤول المشتريات / Purchasing Officer ──
    ("مسؤول المشتريات", "Purchase Order", SUBMIT),
    ("مسؤول المشتريات", "Purchase Receipt", SUBMIT),
    ("مسؤول المشتريات", "Purchase Invoice", SUBMIT),
    ("مسؤول المشتريات", "Material Request", SUBMIT),
    ("مسؤول المشتريات", "Supplier", EDIT),
    ("مسؤول المشتريات", "Item", READ),

    # ── مندوب مبيعات / Sales Representative ──
    ("مندوب مبيعات", "Quotation", EDIT),
    ("مندوب مبيعات", "Sales Order", EDIT),
    ("مندوب مبيعات", "Customer", EDIT),
    ("مندوب مبيعات", "Item", READ),

    # ── مدير المبيعات / Sales Manager ──
    ("Sales Manager", "Quotation", SUBMIT),
    ("Sales Manager", "Sales Order", SUBMIT),
    ("Sales Manager", "Sales Invoice", SUBMIT),
    ("Sales Manager", "Customer", EDIT),
    ("Sales Manager", "Item", READ),
]

# Roles left to Frappe's own configuration on purpose:
#   مدير النظام / Super Admin  → real power is System Manager
#   HR Manager                → configured by the hrms app
#   Employee                  → Frappe's self-service role
#   مسؤول / Admin, مدير / Manager → generic; given read-only oversight below
OVERSIGHT_ROLES = ("مسؤول", "مدير")
OVERSIGHT_DOCTYPES = ("Work Card", "Sales Invoice", "Payment Entry",
                      "Customer", "Item")


def _grant(role, doctype, tier):
    if not (frappe.db.exists("Role", role) and frappe.db.exists("DocType", doctype)):
        return False
    add_permission(doctype, role, 0)
    for ptype, value in tier.items():
        update_permission_property(doctype, role, 0, ptype, value, validate=False)
    return True


def execute():
    granted = skipped = 0
    for role, doctype, tier in MATRIX:
        if _grant(role, doctype, tier):
            granted += 1
        else:
            skipped += 1

    for role in OVERSIGHT_ROLES:
        for doctype in OVERSIGHT_DOCTYPES:
            if _grant(role, doctype, READ):
                granted += 1

    frappe.db.commit()
    frappe.clear_cache()
    print("PERMISSIONS granted=%d skipped=%d" % (granted, skipped))
