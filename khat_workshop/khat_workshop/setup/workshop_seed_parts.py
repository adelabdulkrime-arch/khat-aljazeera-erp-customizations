# -*- coding: utf-8 -*-
"""Seed a sample spare-parts catalogue with opening stock.

Without stock items carrying a real balance the workshop flow cannot be tested
end to end: a Work Card can be submitted, but the parts issue has nothing to
consume and the Stock Entry proves nothing.

Covers fast-moving parts for the Japanese/Korean fleet that dominates Oman,
with indicative OMR cost prices. Like the service rates, these are STARTING
FIGURES for the owner to review — not authoritative purchase costs.

Conservative by design:
  * an item is only created if absent,
  * opening stock is only received ONCE (guarded by a known remark), so a
    redeploy can never inflate inventory by repeatedly re-receiving it.

That second guard matters: a step that re-runs on every migrate and posts stock
each time would quietly corrupt both quantity and valuation.
"""

import frappe

ITEM_GROUP = "قطع غيار"
OPENING_REMARK = "KHAT-OPENING-STOCK-V1"

# (code, arabic name, cost OMR, opening qty)
PARTS = [
    ("SP-FLT-OIL", "فلتر زيت", 2.0, 40),
    ("SP-FLT-AIR", "فلتر هواء", 3.5, 30),
    ("SP-FLT-FUEL", "فلتر بنزين", 5.0, 20),
    ("SP-FLT-AC", "فلتر مكيف", 4.0, 25),
    ("SP-OIL-5W30", "زيت محرك 5W-30 (4 لتر)", 12.0, 50),
    ("SP-BAT-70", "بطارية 70 أمبير", 22.0, 10),
    ("SP-BRK-FRONT", "تيل فرامل أمامي", 15.0, 20),
    ("SP-BRK-REAR", "تيل فرامل خلفي", 13.0, 20),
    ("SP-BRK-DISC", "ديسك فرامل", 25.0, 12),
    ("SP-SPARK", "بوجيه (شمعة إشعال)", 3.0, 60),
    ("SP-BELT", "سير مكينة", 8.0, 15),
    ("SP-WIPER", "مساحات زجاج (طقم)", 5.0, 25),
    ("SP-LAMP-H", "لمبة أمامية", 6.0, 30),
    ("SP-RAD", "ردياتير", 45.0, 5),
    ("SP-AC-COMP", "كمبروسر مكيف", 85.0, 4),
    ("SP-AC-GAS", "غاز مكيف R134a", 8.0, 30),
    ("SP-BRK-FLUID", "زيت فرامل", 4.0, 25),
    ("SP-SUSP-ARM", "مقص / عفشة", 30.0, 8),
]


def _ensure_group():
    if frappe.db.exists("Item Group", ITEM_GROUP):
        return
    parent = frappe.db.get_value(
        "Item Group", {"is_group": 1, "parent_item_group": ""}, "name") or "All Item Groups"
    frappe.get_doc({
        "doctype": "Item Group", "item_group_name": ITEM_GROUP,
        "parent_item_group": parent, "is_group": 0,
    }).insert(ignore_permissions=True)


def _ensure_items():
    created = 0
    for code, name, cost, _qty in PARTS:
        if frappe.db.exists("Item", code):
            continue
        frappe.get_doc({
            "doctype": "Item", "item_code": code, "item_name": name,
            "item_group": ITEM_GROUP, "stock_uom": "Nos",
            "is_stock_item": 1, "is_sales_item": 1, "is_purchase_item": 1,
            "valuation_rate": cost,
            # Selling at cost by default; the owner sets the real margin.
            "standard_rate": cost,
        }).insert(ignore_permissions=True)
        created += 1
    return created


def _warehouse():
    for pattern in ("%Stores%", "%مخازن%", "%مخزن%"):
        wh = frappe.db.get_value(
            "Warehouse", {"warehouse_name": ["like", pattern], "is_group": 0}, "name")
        if wh:
            return wh
    return frappe.db.get_value("Warehouse", {"is_group": 0}, "name")


def _receive_opening(warehouse):
    """Post opening stock exactly once."""
    if frappe.db.exists("Stock Entry", {"remarks": OPENING_REMARK, "docstatus": 1}):
        return "already received"
    if not warehouse:
        return "no warehouse — skipped"

    se = frappe.get_doc({
        "doctype": "Stock Entry",
        "stock_entry_type": "Material Receipt",
        "company": frappe.db.get_single_value("Global Defaults", "default_company"),
        "posting_date": frappe.utils.nowdate(),
        "remarks": OPENING_REMARK,
        "items": [
            {"item_code": c, "qty": q, "t_warehouse": warehouse, "basic_rate": r}
            for c, _n, r, q in PARTS
        ],
    })
    se.insert(ignore_permissions=True)
    se.submit()
    return se.name


def execute():
    _ensure_group()
    created = _ensure_items()
    warehouse = _warehouse()
    entry = _receive_opening(warehouse)
    frappe.db.commit()
    print("SEED_PARTS items=+%d warehouse=%s opening=%s"
          % (created, warehouse, entry))
