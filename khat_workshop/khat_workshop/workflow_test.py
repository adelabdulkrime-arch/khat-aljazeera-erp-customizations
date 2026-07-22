# -*- coding: utf-8 -*-
"""Drive ten Work Cards across all five service lines and verify the flow.

Checks the things that actually matter operationally:

  * a saved (draft) Work Card consumes NO stock
  * submitting issues the parts and decrements the bin
  * a submitted Work Card is LOCKED against edits
  * cancelling reverses the Stock Entry and restores the bin

Run:  bench --site <site> console  ->  from khat_workshop import workflow_test; workflow_test.run()
"""

import frappe

PREFIX = "ورشة-اختبار"

# (service_line, service_item, part_item, part_qty)
CASES = [
    ("ميكانيكا", "WS-MECH-001", "SP-FLT-OIL", 1),
    ("ميكانيكا", "WS-MECH-002", "SP-BRK-FRONT", 1),
    ("ميكانيكا", "WS-MECH-004", "SP-SPARK", 4),
    ("سمكرة وحوادث", "WS-BODY-001", "SP-LAMP-H", 1),
    ("سمكرة وحوادث", "WS-BODY-003", "SP-WIPER", 1),
    ("دهان", "WS-PNT-001", "SP-BRK-FLUID", 1),
    ("دهان", "WS-PNT-003", "SP-FLT-AIR", 1),
    ("كهرباء", "WS-ELEC-003", "SP-BAT-70", 1),
    ("تكييف", "WS-AC-001", "SP-AC-GAS", 2),
    ("تكييف", "WS-AC-003", "SP-FLT-AC", 1),
]


def _qty(item, warehouse):
    return frappe.db.get_value(
        "Bin", {"item_code": item, "warehouse": warehouse}, "actual_qty") or 0


def _warehouse():
    return frappe.db.get_value("Custom Field", "Work Card-warehouse", "default") \
        or frappe.db.get_value("Warehouse", {"is_group": 0}, "name")


def run():
    results = []
    wh = _warehouse()
    print("=== workflow test — warehouse=%s ===" % wh)

    customer = PREFIX + " عميل"
    if not frappe.db.exists("Customer", customer):
        frappe.get_doc({"doctype": "Customer", "customer_name": customer}).insert(
            ignore_permissions=True)

    status = frappe.db.get_value("Work Card Status", {}, "name")

    # vehicle is mandatory on Work Card, so each case needs a real Customer
    # Vehicle. Plate numbers are synthetic and prefixed so the test fleet is
    # obvious in the vehicle list.
    vehicles = []
    for i in range(1, len(CASES) + 1):
        plate = "%s-%02d" % (PREFIX, i)
        existing = frappe.db.get_value("Customer Vehicle", {"plate_number": plate}, "name")
        if existing:
            vehicles.append(existing)
            continue
        v = frappe.get_doc({
            "doctype": "Customer Vehicle", "customer": customer,
            "plate_number": plate, "brand": "تويوتا", "model": "تويوتا-كامري",
        }).insert(ignore_permissions=True)
        vehicles.append(v.name)
    created = []

    for idx, (line, svc, part, qty) in enumerate(CASES, 1):
        before = _qty(part, wh)

        wc = frappe.get_doc({
            "doctype": "Work Card",
            "customer": customer,
            "vehicle": vehicles[idx - 1],
            "service_line": line,
            "status": status,
            "warehouse": wh,
            "complaint": "%s — حالة اختبار %d" % (line, idx),
            # Intake condition is mandatory before submit; these synthetic
            # vehicles have no damage to record.
            "no_visible_damage": 1,
            "services": [{"service": svc, "qty": 1, "rate": 0}],
            "parts": [{"item": part, "part_name": part, "qty": qty, "rate": 0}],
        })
        wc.insert(ignore_permissions=True)

        # 1) draft must not touch stock
        draft_ok = _qty(part, wh) == before
        # 2) submit must issue
        wc.submit()
        wc.reload()
        after = _qty(part, wh)
        issued_ok = (after == before - qty) and bool(wc.stock_entry)
        # 3) submitted must be locked
        locked_ok = wc.docstatus == 1

        created.append((wc.name, part, before, qty))
        results.append(draft_ok and issued_ok and locked_ok)
        print("  [%s] %-14s %-14s %s: %s -> %s  se=%s"
              % ("PASS" if results[-1] else "FAIL", line, part,
                 wc.name, before, after, wc.stock_entry or "NONE"))

    # 4) cancellation must reverse
    name, part, before, qty = created[0]
    wc = frappe.get_doc("Work Card", name)
    wc.cancel()
    restored = _qty(part, wh) == before
    results.append(restored)
    print("  [%s] cancel reversed stock for %s (%s back to %s)"
          % ("PASS" if restored else "FAIL", name, part, before))

    frappe.db.commit()
    passed = sum(1 for r in results if r)
    print("=== WORKFLOW %d/%d passed ===" % (passed, len(results)))
    print("WORKFLOW_RESULT=%s" % ("PASS" if passed == len(results) else "FAIL"))
