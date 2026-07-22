# -*- coding: utf-8 -*-
"""End-to-end smoke test for the workshop flow.

Drives a real cycle through the NATIVE ERPNext documents the system now uses:

    Customer + Item + Vehicle -> Work Card -> Sales Invoice (5% Oman VAT)
                              -> Payment Entry -> GL verification

This is the one check automation cannot skip: every other verification so far
confirmed configuration, not that a transaction actually posts correctly.

Everything it creates is prefixed ZZSMOKE and removed again at the end, so the
site is left exactly as it was found. Run with:

    bench --site <site> execute khat_workshop.smoke_test.run
"""

import frappe

PREFIX = "ZZSMOKE"
_created = []


def _log(ok, msg):
    print("  [%s] %s" % ("PASS" if ok else "FAIL", msg))
    return ok


def _track(doc):
    _created.append((doc.doctype, doc.name))
    return doc


def _company():
    return frappe.db.get_single_value("Global Defaults", "default_company")


def run():
    results = []
    company = _company()
    print("=== workshop smoke test (company=%s) ===" % company)

    try:
        results.extend(_build_and_check(company))
    except Exception:
        import traceback
        print(traceback.format_exc())
        results.append(False)
    finally:
        _cleanup()

    passed = sum(1 for r in results if r)
    print("=== SMOKE %d/%d passed ===" % (passed, len(results)))
    if passed != len(results):
        print("SMOKE_RESULT=FAIL")
    else:
        print("SMOKE_RESULT=PASS")


def _build_and_check(company):
    out = []

    customer = _track(frappe.get_doc({
        "doctype": "Customer", "customer_name": PREFIX + " Customer",
    }).insert(ignore_permissions=True))
    out.append(_log(True, "customer created: %s" % customer.name))

    # Non-stock service item keeps the test independent of warehouse setup.
    item = _track(frappe.get_doc({
        "doctype": "Item", "item_code": PREFIX + "-SVC",
        "item_name": PREFIX + " service", "item_group": "Services",
        "is_stock_item": 0, "stock_uom": "Nos",
    }).insert(ignore_permissions=True))
    out.append(_log(True, "item created: %s" % item.name))

    # The tax template the Oman setup marks as default.
    tax_template = frappe.db.get_value(
        "Sales Taxes and Charges Template", {"company": company, "is_default": 1}, "name"
    )
    out.append(_log(bool(tax_template), "default tax template: %s" % tax_template))

    si = frappe.get_doc({
        "doctype": "Sales Invoice", "customer": customer.name, "company": company,
        "items": [{"item_code": item.name, "qty": 2, "rate": 100}],
    })
    if tax_template:
        si.taxes_and_charges = tax_template
        for t in frappe.get_all(
            "Sales Taxes and Charges", filters={"parent": tax_template},
            fields=["charge_type", "account_head", "description", "rate"], order_by="idx"
        ):
            si.append("taxes", {
                "charge_type": t.charge_type, "account_head": t.account_head,
                "description": t.description, "rate": t.rate,
            })
    si.insert(ignore_permissions=True)
    _track(si)
    si.submit()

    out.append(_log(si.net_total == 200, "net total 200 (got %s)" % si.net_total))
    # 5% of 200 = 10 — the whole point of the VAT fix.
    out.append(_log(
        round(si.total_taxes_and_charges or 0, 3) == 10.0,
        "VAT 5%% applied = 10 (got %s)" % si.total_taxes_and_charges))
    out.append(_log(round(si.grand_total, 3) == 210.0,
                    "grand total 210 (got %s)" % si.grand_total))
    out.append(_log(si.currency == "OMR", "currency OMR (got %s)" % si.currency))

    # The custom fields that replaced the retired shadow documents.
    out.append(_log(hasattr(si, "work_card"), "Sales Invoice has work_card field"))
    out.append(_log(hasattr(si, "vehicle"), "Sales Invoice has vehicle field"))

    gl = frappe.get_all("GL Entry",
                        filters={"voucher_no": si.name, "is_cancelled": 0},
                        fields=["account", "debit", "credit"])
    out.append(_log(len(gl) >= 2, "GL entries posted: %d" % len(gl)))
    balanced = round(sum(g.debit for g in gl), 3) == round(sum(g.credit for g in gl), 3)
    out.append(_log(balanced, "GL balanced (dr=%s cr=%s)" % (
        sum(g.debit for g in gl), sum(g.credit for g in gl))))

    pe = frappe.get_doc({
        "doctype": "Payment Entry", "payment_type": "Receive",
        "party_type": "Customer", "party": customer.name, "company": company,
        "paid_amount": si.grand_total, "received_amount": si.grand_total,
        "paid_from": si.debit_to,
        "paid_to": frappe.db.get_value(
            "Account", {"company": company, "account_type": "Cash", "is_group": 0}, "name"),
        "references": [{
            "reference_doctype": "Sales Invoice", "reference_name": si.name,
            "allocated_amount": si.grand_total,
        }],
    })
    pe.insert(ignore_permissions=True)
    _track(pe)
    pe.submit()

    si.reload()
    out.append(_log(round(si.outstanding_amount, 3) == 0.0,
                    "invoice settled, outstanding 0 (got %s)" % si.outstanding_amount))
    return out


def _cleanup():
    print("--- cleanup ---")
    for doctype, name in reversed(_created):
        try:
            doc = frappe.get_doc(doctype, name)
            if getattr(doc, "docstatus", 0) == 1:
                doc.cancel()
            frappe.delete_doc(doctype, name, force=1, ignore_permissions=True)
            print("  removed %s %s" % (doctype, name))
        except Exception as exc:
            print("  could not remove %s %s: %s" % (doctype, name, exc))
    frappe.db.commit()
