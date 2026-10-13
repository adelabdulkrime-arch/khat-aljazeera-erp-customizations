# -*- coding: utf-8 -*-
"""Exercise the commercial chain: Quotation -> Sales Invoice -> Payment Entry.

The workflow test proved the operational side (parts leave stock on submit and
come back on cancel). This proves the money side, on a REAL job card:

  * a Quotation carries the workshop context (work card, vehicle, service line)
  * a Sales Invoice applies Oman VAT 5% and posts balanced GL entries
  * a Payment Entry settles it to zero outstanding
  * technicians and commissions are recorded on the job card
"""

import frappe

PREFIX = "ورشة-اختبار"


def _tax_rows(company):
    tpl = frappe.db.get_value(
        "Sales Taxes and Charges Template", {"company": company, "is_default": 1}, "name")
    rows = []
    if tpl:
        for t in frappe.get_all(
            "Sales Taxes and Charges", filters={"parent": tpl},
            fields=["charge_type", "account_head", "description", "rate"], order_by="idx"
        ):
            rows.append({
                "charge_type": t.charge_type, "account_head": t.account_head,
                "description": t.description, "rate": t.rate,
            })
    return tpl, rows


def run():
    out = []
    company = frappe.db.get_single_value("Global Defaults", "default_company")
    wc = frappe.get_all("Work Card", filters={"docstatus": 1}, limit=1)
    if not wc:
        print("no submitted Work Card to bill — run workflow_test first")
        return
    src = frappe.get_doc("Work Card", wc[0].name)

    # A priced card of its own, with a technician. Technicians and commission
    # go on the DRAFT: a submitted card is locked (workshop_work_card_control),
    # so this is the only moment they can be entered. This test used to append
    # a technician to an already-submitted card, which the lock rightly
    # refuses — the test had gone stale, and "technicians recorded" was
    # asserted as `bool(...) or True`, i.e. it could not fail.
    tech = frappe.db.get_value("Workshop Technician", {}, "name")
    card = frappe.get_doc({
        "doctype": "Work Card", "customer": src.customer, "vehicle": src.vehicle,
        "service_line": src.service_line, "status": src.status,
        "warehouse": src.warehouse,
        "complaint": PREFIX + " — دورة تجارية", "no_visible_damage": 1,
        "services": [{"service": "WS-MECH-001", "qty": 1, "rate": 100}],
        "parts": [{"item": "SP-FLT-OIL", "part_name": "SP-FLT-OIL", "qty": 1, "rate": 4}],
        "technicians": [{"technician": tech, "task": "تنفيذ الأعمال",
                         "hours": 2, "commission": 5}] if tech else [],
    })
    card.insert(ignore_permissions=True)
    card.submit()
    card.reload()
    # Committed here: the lock probe below rolls back its refused edit, and
    # must not take the card with it.
    frappe.db.commit()
    print("=== commercial test on %s (%s) ===" % (card.name, card.service_line))

    out.append(("technicians recorded", len(card.technicians) == 1))
    out.append(("card revenue = 104 (got %s)" % card.grand_total,
                round(card.grand_total or 0, 3) == 104.0))
    out.append(("commission counted as cost (got %s)" % card.commission_total,
                round(card.commission_total or 0, 3) == 5.0))
    out.append(("profit = revenue - cost (got %s)" % card.gross_profit,
                round(card.gross_profit or 0, 3) == round(104.0 - (card.total_cost or 0), 3)))
    out.append(("margin %% computed (got %s)" % card.margin_pct,
                round(card.margin_pct or 0, 2)
                == round((card.gross_profit or 0) / 104.0 * 100, 2)))

    locked = False
    try:
        probe = frappe.get_doc("Work Card", card.name)
        probe.services[0].rate = 1
        probe.save(ignore_permissions=True)
    except frappe.UpdateAfterSubmitError:
        locked = True
        frappe.db.rollback()
    out.append(("submitted card refuses a price change", locked))

    tpl, taxes = _tax_rows(company)
    out.append(("default tax template found", bool(tpl)))

    # ---- Quotation ----
    q = frappe.get_doc({
        "doctype": "Quotation", "quotation_to": "Customer",
        "party_name": card.customer, "company": company,
        "work_card": card.name, "vehicle": card.vehicle,
        "service_line": card.service_line,
        "items": [{"item_code": "WS-MECH-001", "qty": 1, "rate": 100}],
        "taxes_and_charges": tpl, "taxes": list(taxes),
    })
    q.insert(ignore_permissions=True)
    q.submit()
    out.append(("quotation carries work card", q.work_card == card.name))
    out.append(("quotation VAT = 5.0", round(q.total_taxes_and_charges or 0, 3) == 5.0))

    # ---- Sales Invoice ----
    si = frappe.get_doc({
        "doctype": "Sales Invoice", "customer": card.customer, "company": company,
        "work_card": card.name, "vehicle": card.vehicle,
        "service_line": card.service_line,
        "items": [
            {"item_code": "WS-MECH-001", "qty": 1, "rate": 100},
            {"item_code": "SP-FLT-OIL", "qty": 1, "rate": 4},
        ],
        "taxes_and_charges": tpl, "taxes": list(taxes),
    })
    si.insert(ignore_permissions=True)
    si.submit()

    out.append(("invoice net = 104", round(si.net_total, 3) == 104.0))
    out.append(("invoice VAT 5% = 5.2", round(si.total_taxes_and_charges or 0, 3) == 5.2))
    out.append(("invoice grand = 109.2", round(si.grand_total, 3) == 109.2))
    out.append(("invoice keeps service line", si.service_line == card.service_line))

    gl = frappe.get_all("GL Entry", filters={"voucher_no": si.name, "is_cancelled": 0},
                        fields=["debit", "credit"])
    dr, cr = sum(g.debit for g in gl), sum(g.credit for g in gl)
    out.append(("GL balanced (%s/%s)" % (round(dr, 2), round(cr, 2)), round(dr, 3) == round(cr, 3)))

    # ---- Payment ----
    pe = frappe.get_doc({
        "doctype": "Payment Entry", "payment_type": "Receive",
        "party_type": "Customer", "party": card.customer, "company": company,
        "paid_amount": si.grand_total, "received_amount": si.grand_total,
        "paid_from": si.debit_to,
        "paid_to": frappe.db.get_value(
            "Account", {"company": company, "account_type": "Cash", "is_group": 0}, "name"),
        "references": [{"reference_doctype": "Sales Invoice",
                        "reference_name": si.name, "allocated_amount": si.grand_total}],
    })
    pe.insert(ignore_permissions=True)
    pe.submit()
    si.reload()
    out.append(("invoice settled to zero", round(si.outstanding_amount, 3) == 0.0))

    frappe.db.commit()
    for label, ok in out:
        print("  [%s] %s" % ("PASS" if ok else "FAIL", label))
    passed = sum(1 for _l, ok in out if ok)
    print("=== COMMERCIAL %d/%d passed ===" % (passed, len(out)))
    print("COMMERCIAL_RESULT=%s" % ("PASS" if passed == len(out) else "FAIL"))
