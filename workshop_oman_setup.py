# -*- coding: utf-8 -*-
"""Localize the system for Oman: currency (OMR, 3 decimals), country, timezone,
VAT 5% tax template. Idempotent."""
import frappe


def execute():
    # 1. Currency: OMR uses 3 decimal places (1 OMR = 1000 Baisa)
    if not frappe.db.exists("Currency", "OMR"):
        frappe.get_doc({
            "doctype": "Currency", "currency_name": "OMR", "enabled": 1,
            "fraction": "Baisa", "fraction_units": 1000,
            "symbol": "ر.ع.", "number_format": "#,###.###",
            "smallest_currency_fraction_value": 0.001,
        }).insert(ignore_permissions=True)
    else:
        c = frappe.get_doc("Currency", "OMR")
        c.enabled = 1
        c.fraction = "Baisa"
        c.fraction_units = 1000
        c.number_format = "#,###.###"
        c.smallest_currency_fraction_value = 0.001
        c.save(ignore_permissions=True)

    # 2. Country check (Oman ships with Frappe by default)
    print("Oman country master exists:", frappe.db.exists("Country", "Oman"))

    # 3. Update all Companies to Oman/OMR
    for cname in frappe.get_all("Company", pluck="name"):
        comp = frappe.get_doc("Company", cname)
        comp.country = "Oman"
        comp.default_currency = "OMR"
        comp.save(ignore_permissions=True)
        abbr = comp.abbr

        # 4. Oman VAT 5% - create tax account + sales taxes template
        # Chart of accounts may be Arabic ("الرسوم والضرائب") or English
        # ("Duties and Taxes") depending on the language used during setup.
        parent_tax_acc = frappe.db.get_value(
            "Account", {"account_name": "Duties and Taxes", "company": cname}, "name"
        ) or frappe.db.get_value(
            "Account", {"account_name": "الرسوم والضرائب", "company": cname}, "name"
        )
        if parent_tax_acc:
            vat_acc_name = "ضريبة القيمة المضافة - %s" % abbr
            if not frappe.db.exists("Account", vat_acc_name):
                frappe.get_doc({
                    "doctype": "Account", "account_name": "ضريبة القيمة المضافة",
                    "parent_account": parent_tax_acc, "company": cname,
                    "account_type": "Tax", "is_group": 0,
                }).insert(ignore_permissions=True)

            template_name = "ضريبة القيمة المضافة عمان 5%% - %s" % abbr
            if not frappe.db.exists("Sales Taxes and Charges Template", template_name):
                frappe.get_doc({
                    "doctype": "Sales Taxes and Charges Template",
                    "title": "ضريبة القيمة المضافة عمان 5%",
                    "company": cname, "is_default": 1,
                    "taxes": [{
                        "charge_type": "On Net Total",
                        "account_head": vat_acc_name,
                        "description": "ضريبة القيمة المضافة (عُمان) 5%",
                        "rate": 5,
                    }],
                }).insert(ignore_permissions=True)

    # 5. System-wide defaults
    gd = frappe.get_single("Global Defaults")
    gd.default_currency = "OMR"
    gd.country = "Oman"
    gd.save(ignore_permissions=True)

    ss = frappe.get_single("System Settings")
    ss.country = "Oman"
    ss.time_zone = "Asia/Muscat"
    ss.save(ignore_permissions=True)

    # 6. Workshop Settings: Oman-style VAT number placeholder + phone format
    ws = frappe.get_single("Workshop Settings")
    ws.tax_number = "OM1000000000"
    ws.phone = "+968 9000 0000"
    ws.address = "مسقط، سلطنة عُمان"
    ws.save(ignore_permissions=True)

    frappe.db.commit()
    frappe.clear_cache()
    print("OMAN_SETUP_DONE")
