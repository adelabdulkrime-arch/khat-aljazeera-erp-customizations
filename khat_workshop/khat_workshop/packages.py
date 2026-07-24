# -*- coding: utf-8 -*-
"""Total a Workshop Package from its lines, applying the package discount.

Kept out of a Server Script for the same reason as costing: it reads the linked
Item and shares one code path, and belongs in version control beside the fields
it fills (see khat_workshop.setup.workshop_packages).
"""

import frappe
from frappe.utils import flt


def compute(doc, method=None):
    subtotal = 0.0
    for row in doc.get("items") or []:
        # Default a line's rate from the item's selling price when left blank,
        # so a package can be built by picking items without retyping prices.
        if not row.get("rate") and row.get("item"):
            row.rate = frappe.db.get_value("Item", row.item, "standard_rate") or 0
        row.amount = flt(flt(row.get("qty")) * flt(row.get("rate")), 3)
        subtotal += flt(row.amount)

    discount = flt(subtotal * flt(doc.get("discount_percentage")) / 100, 3)
    doc.subtotal = flt(subtotal, 3)
    doc.discount_amount = discount
    doc.total = flt(subtotal - discount, 3)
