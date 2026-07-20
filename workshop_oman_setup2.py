# -*- coding: utf-8 -*-
"""Fix: company accounts are still tagged SAR from setup wizard. Since this is
a fresh site (no real GL Entries posted — our Repair Invoice/Payment are
separate custom doctypes, not accounting entries), it's safe to retag all of
the company's Chart of Accounts to OMR before switching the company currency."""
import frappe


def execute():
    for cname in frappe.get_all("Company", pluck="name"):
        gl_count = frappe.db.count("GL Entry", {"company": cname})
        print("Company %s — existing GL Entries: %d" % (cname, gl_count))
        if gl_count:
            print("  SKIPPED (has real accounting entries — must migrate manually)")
            continue
        frappe.db.sql(
            "update `tabAccount` set account_currency=%s where company=%s",
            ("OMR", cname))
    frappe.db.commit()
    print("ACCOUNTS_RETAGGED")
