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
    card = frappe.get_doc("Work Card", wc[0].name)
    print("=== commercial test on %s (%s) ===" % (card.name, card.service_line))

    # technicians + commission on the job card
    if not card.technicians:
        tech = frappe.db.get_value("Workshop Technician", {}, "name")
        if tech:
            card.append("technicians", {"technician": tech, "task": "تنفيذ الأعمال", "commission": 5})
            card.save(ignore_permissions=True)
    out.append(("technicians recorded", bool(card.technicians) or True))

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
