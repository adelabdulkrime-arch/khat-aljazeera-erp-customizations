# -*- coding: utf-8 -*-
"""Seed indicative pricing and the master data the workflow needs to run.

The service catalogue shipped with zero rates on purpose, but a workshop cannot
be exercised end to end without prices, a warehouse and vehicle masters. This
puts sensible Omani-market starting figures in place so the flow can actually be
tested.

IMPORTANT — these rates are INDICATIVE, not authoritative. They are labour/
service charges in OMR based on typical Omani workshop ranges, excluding parts.
The owner must review them before the system carries real customer money.

Conservative by design: a rate is only written when the item has none. Once
anyone edits a price, this step never overwrites it, so a redeploy can never
silently undo a commercial decision.
"""

import frappe

# (item_code, indicative OMR labour rate) — service charge only, parts excluded.
SERVICE_RATES = {
    "WS-MECH-001": 18,    # oil + filter change
    "WS-MECH-002": 30,    # brake service
    "WS-MECH-003": 55,    # suspension
    "WS-MECH-004": 45,    # engine inspection/service
    "WS-BODY-001": 120,   # accident/dent repair
    "WS-BODY-002": 200,   # chassis pulling/alignment
    "WS-BODY-003": 90,    # body panel replacement (labour)
    "WS-PNT-001": 35,     # single panel paint
    "WS-PNT-002": 350,    # full respray
    "WS-PNT-003": 45,     # polish + protection
    "WS-ELEC-001": 20,    # general electrical check
    "WS-ELEC-002": 30,    # lighting system
    "WS-ELEC-003": 35,    # battery / alternator
    "WS-AC-001": 20,      # A/C gas refill
    "WS-AC-002": 110,     # compressor repair
    "WS-AC-003": 45,      # cooling circuit service
}

VEHICLE_BRANDS = [
    "تويوتا", "نيسان", "لكزس", "ميتسوبيشي", "هوندا",
    "فورد", "شيفروليه", "هيونداي", "كيا", "مرسيدس", "بي إم دبليو",
]

# Kept short on purpose — the workshop will add its own real mix over time.
VEHICLE_MODELS = {
    "تويوتا": ["لاندكروزر", "كامري", "هايلكس", "كورولا"],
    "نيسان": ["باترول", "صني", "التيما"],
    "لكزس": ["LX570", "ES350"],
    "ميتسوبيشي": ["باجيرو", "لانسر"],
    "هوندا": ["أكورد", "سيفيك"],
}


def _price_services():
    priced = 0
    for code, rate in SERVICE_RATES.items():
        if not frappe.db.exists("Item", code):
            continue
        # Never overwrite a rate someone has already set.
        if frappe.db.get_value("Item", code, "standard_rate"):
            continue
        frappe.db.set_value("Item", code, "standard_rate", rate)
        priced += 1
    return priced


def _ensure_brands_models():
    brands = models = 0
    for brand in VEHICLE_BRANDS:
        if frappe.db.exists("Vehicle Brand", brand):
            continue
        frappe.get_doc({"doctype": "Vehicle Brand", "brand_name": brand}).insert(
            ignore_permissions=True)
        brands += 1

    for brand, names in VEHICLE_MODELS.items():
        for model in names:
            if frappe.db.exists("Vehicle Model", {"brand": brand, "model_name": model}):
                continue
            frappe.get_doc({
                "doctype": "Vehicle Model", "brand": brand, "model_name": model,
            }).insert(ignore_permissions=True)
            models += 1
    return brands, models


def _report_warehouse():
    """The parts-issue script needs a warehouse; report whether one is usable."""
    wh = frappe.db.get_value("Warehouse", {"is_group": 0}, "name")
    return wh or "NONE — parts issue will be skipped until a warehouse exists"


def execute():
    priced = _price_services()
    brands, models = _ensure_brands_models()
    warehouse = _report_warehouse()
    frappe.db.commit()
    print("SEED_DATA priced=%d brands=+%d models=+%d warehouse=%s"
          % (priced, brands, models, warehouse))
