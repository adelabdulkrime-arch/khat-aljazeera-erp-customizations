# -*- coding: utf-8 -*-
"""Granular replacement-operation catalogue — requested directly by the owner
in two voice notes (2026-08-23), then re-coded (2026-08-25) after he shared
real Mazoon screenshots showing how a competing system does it.

`workshop_service_catalogue` already seeds five broad service *lines*
(engine check, brake check, suspension service...) — good for grouping and
departmental reporting, but too coarse for what he actually asked for: every
job that leaves the workshop must show, itemised, exactly which operations
were performed (تبديل بطارية، تبديل فلتر هواء...) because the invoice/
quotation is submitted to government offices, and a lump total with no line
items is not acceptable there.

Seeds a second Item Group, "عمليات الاستبدال" (Replacement Operations),
nested under the existing "خدمات الورشة", with one Item per operation he
named across both recordings. Each is a non-stock, sellable Item — same
mechanism as workshop_service_catalogue — so it can be picked directly in a
Quotation or Sales Invoice's items table and prints as its own row.

CODING SCHEME (2026-08-25 change) — matches the Mazoon screenshots he sent:
their quotation showed a service line coded "SRV-0001" and a part line coded
"PRD-0012", each a running number with no manual input. The first version of
this file hand-picked "WS-OP-001".."WS-OP-014" — safe *within this one file*
(nobody else used that prefix), but manual numbers do not scale: the moment
staff or another script add items by hand, nothing stops two different items
from ending up with the same code.

Codes here are now generated with frappe.model.naming.make_autoname, the
same primitive Frappe's own Naming Series field uses. It increments a single
counter row per prefix inside a DB transaction, so two items can never be
assigned the same "SRV-####" number no matter how many scripts, sessions or
people create items concurrently — the guarantee holds by construction, not
by convention. Real stock parts the owner adds later (batteries by size,
filters by size...) should use the sibling prefix "PRD-.####" the same way,
for the same reason.

MIGRATION: if this script already ran against the old WS-OP-* codes, re-running
detects each by its old fixed code and renames it to a fresh SRV-#### rather
than creating a duplicate. Safe because these items cannot have been used on
any submitted document yet (they were only just introduced).

Terms as heard on the recordings, for reference (Gulf workshop slang -> item):
  أيل فلتر            -> Oil Filter + Oil itself
  السفايف             -> Wiper Blades
  البلكات             -> Ball Joint
  البوشات / Bush       -> Bush
  Battery / Brake Pad / Light / Link Rod / Rod End / Rack End / Filter /
  Air Filter / سير المحرك (2nd note) -> as named below
"""

import frappe
from frappe.model.naming import make_autoname

PARENT_ITEM_GROUP = "خدمات الورشة"      # created by workshop_service_catalogue
ITEM_GROUP = "عمليات الاستبدال"          # Replacement Operations
NAMING_PREFIX = "SRV-.####"              # matches Mazoon's SRV-0001 pattern

# legacy fixed codes from the first version of this file — kept ONLY so a
# re-run can find and migrate anything already created under them.
LEGACY_CODES = [
    "WS-OP-001", "WS-OP-002", "WS-OP-003", "WS-OP-004", "WS-OP-005",
    "WS-OP-006", "WS-OP-007", "WS-OP-008", "WS-OP-009", "WS-OP-010",
    "WS-OP-011", "WS-OP-012", "WS-OP-013", "WS-OP-014",
]

# Arabic name (shown on the invoice), English note (kept only in the
# description, for the owner's own reference)
OPERATIONS = [
    ("تبديل زيت المحرك", "Engine Oil Change"),
    ("تبديل فلتر الزيت", "Oil Filter Replacement"),
    ("تبديل فلتر الهواء", "Air Filter Replacement"),
    ("تبديل فلتر (عام)", "Filter Replacement (General)"),
    ("تبديل مساحات (سفايف)", "Wiper Blades Replacement"),
    ("تبديل تيل الفرامل", "Brake Pad Replacement"),
    ("تبديل بطارية", "Battery Replacement"),
    ("تبديل لمبة إضاءة / كشاف", "Light Bulb Replacement"),
    ("تبديل بوش (جلبة مطاطية)", "Bush Replacement"),
    ("تبديل بلية (كرة مفصل التعليق)", "Ball Joint Replacement"),
    ("تبديل رابط طرف التوجيه (لينك رود)", "Link Rod Replacement"),
    ("تبديل رأس التيرس (رود إند)", "Rod End / Tie Rod End Replacement"),
    ("تبديل رأس الدركسون (راك إند)", "Rack End Replacement"),
    ("تبديل سير المحرك", "Engine Belt Replacement"),
]


def _ensure_item_group():
    if frappe.db.exists("Item Group", ITEM_GROUP):
        return "exists"
    parent = PARENT_ITEM_GROUP if frappe.db.exists("Item Group", PARENT_ITEM_GROUP) else (
        frappe.db.get_value("Item Group", {"is_group": 1, "parent_item_group": ""}, "name")
        or "All Item Groups"
    )
    frappe.get_doc({
        "doctype": "Item Group", "item_group_name": ITEM_GROUP,
        "parent_item_group": parent, "is_group": 0,
    }).insert(ignore_permissions=True)
    return "created under %s" % parent


def _seed_operations():
    created, migrated, skipped = 0, 0, 0
    legacy_by_index = dict(enumerate(LEGACY_CODES))

    for idx, (name_ar, name_en) in enumerate(OPERATIONS):
        description = "%s — %s" % (name_ar, name_en)

        # Already seeded under the NEW scheme specifically (code already
        # SRV-prefixed) -> nothing to do. Checking the prefix here, not just
        # name+group, is what stops a stale WS-OP-* row from being mistaken
        # for "already migrated" and left un-renamed.
        existing = frappe.db.get_value(
            "Item", {"item_name": name_ar, "item_group": ITEM_GROUP}, "item_code")
        if existing and existing.startswith("SRV-"):
            skipped += 1
            continue

        legacy_code = legacy_by_index.get(idx)
        if legacy_code and frappe.db.exists("Item", legacy_code):
            # Already created by the old WS-OP-* version of this script —
            # rename in place to the new collision-proof SRV-#### code
            # instead of creating a second, duplicate Item.
            new_code = make_autoname(NAMING_PREFIX)
            frappe.rename_doc("Item", legacy_code, new_code, force=True)
            doc = frappe.get_doc("Item", new_code)
            doc.description = description
            doc.save(ignore_permissions=True)
            migrated += 1
            continue

        code = make_autoname(NAMING_PREFIX)
        frappe.get_doc({
            "doctype": "Item", "item_code": code, "item_name": name_ar,
            "item_group": ITEM_GROUP, "stock_uom": "Nos",
            "is_stock_item": 0,          # an operation/labour line, not stock
            "is_sales_item": 1,
            "is_purchase_item": 0,
            "description": description,
        }).insert(ignore_permissions=True)
        created += 1

    return created, migrated, skipped


def execute():
    group_state = _ensure_item_group()
    created, migrated, skipped = _seed_operations()
    frappe.db.commit()
    frappe.clear_cache()
    print("REPLACEMENT_OPERATIONS item_group=%s created=%d migrated=%d skipped=%d total=%d"
          % (group_state, created, migrated, skipped, len(OPERATIONS)))
