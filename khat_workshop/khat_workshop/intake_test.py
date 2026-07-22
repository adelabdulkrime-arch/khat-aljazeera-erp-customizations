# -*- coding: utf-8 -*-
"""Prove the intake condition record cannot be skipped, and cannot be edited.

Four things have to hold or the record is worthless as evidence:

  1. a card with no condition recorded is refused at submit,
  2. the one-click "no visible damage" declaration satisfies it,
  3. listing actual damage satisfies it and the rows survive submit,
  4. the record is frozen once submitted.

Run:  bench --site <site> execute khat_workshop.intake_test.run
"""

import traceback

import frappe

PROBE = "intake-probe"


def _template():
    src = frappe.get_all(
        "Work Card", filters={"docstatus": 1}, limit=1,
        fields=["customer", "vehicle", "status", "warehouse", "service_line"])[0]
    return {
        "doctype": "Work Card", "customer": src.customer, "vehicle": src.vehicle,
        "service_line": src.service_line, "status": src.status,
        "warehouse": src.warehouse, "complaint": PROBE,
        "services": [{"service": "WS-MECH-001", "qty": 1, "rate": 10}],
    }


def _card(**extra):
    payload = _template()
    payload.update(extra)
    return frappe.get_doc(payload).insert(ignore_permissions=True)


def _cleanup():
    removed = 0
    for name in frappe.get_all("Work Card", filters={"complaint": PROBE}, pluck="name"):
        doc = frappe.get_doc("Work Card", name)
        if doc.docstatus == 1:
            doc.cancel()
        frappe.delete_doc("Work Card", name, force=1, ignore_permissions=True)
        removed += 1
    frappe.db.commit()
    return removed


def run():
    results = []
    _cleanup()

    # 1. nothing recorded -> refused
    try:
        _card().submit()
        results.append(("submit refused when condition not recorded", False))
    except frappe.ValidationError:
        results.append(("submit refused when condition not recorded", True))
    frappe.db.rollback()

    # 2. one-click declaration
    clean = _card(no_visible_damage=1)
    clean.submit()
    results.append(("'no visible damage' allows submit", clean.docstatus == 1))

    # 3. real damage rows
    damaged = _card(damages=[
        {"zone": "الصدام الأمامي", "condition": "خدش", "note": "خدش سطحي يمين"},
        {"zone": "الباب الخلفي الأيسر", "condition": "انبعاج", "note": "انبعاج بسيط"},
    ])
    damaged.submit()
    damaged.reload()
    results.append(("damage rows allow submit", damaged.docstatus == 1))
    results.append(("damage rows survive submit", len(damaged.damages) == 2))
    results.append(("zone recorded", damaged.damages[0].zone == "الصدام الأمامي"))

    # 4. frozen afterwards
    try:
        doc = frappe.get_doc("Work Card", damaged.name)
        doc.damages[0].condition = "كسر"
        doc.save(ignore_permissions=True)
        results.append(("condition frozen after submit", False))
    except Exception:
        results.append(("condition frozen after submit", True))
    frappe.db.rollback()

    removed = _cleanup()

    for label, ok in results:
        print("  [%s] %s" % ("PASS" if ok else "FAIL", label))
    passed = sum(1 for _l, ok in results if ok)
    print("=== INTAKE %d/%d passed (cleaned %d probe cards, %d work cards remain) ==="
          % (passed, len(results), removed, frappe.db.count("Work Card")))
    print("INTAKE_RESULT=%s" % ("PASS" if passed == len(results) else "FAIL"))


def main():
    try:
        run()
    except Exception:
        print(traceback.format_exc())
        _cleanup()
