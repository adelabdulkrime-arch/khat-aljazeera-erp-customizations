# -*- coding: utf-8 -*-
"""Complete ERPNext's setup wizard so a fresh site has a usable foundation.

`bench new-site --install-app erpnext` installs the *code* but leaves the site
un-onboarded: System Settings.setup_complete stays 0, and ERPNext's own
after-wizard install never runs. That install is what creates the Company, the
chart of accounts, the default UOMs (Nos, Unit, Box…) and the base Item Groups.

Without it every later step that creates an Item dies on a link error —
"Could not find Default Unit of Measure: Nos" — because UOM has literally zero
records. Six setup steps failed exactly this way on the first deploy:
service_catalogue, replacement_operations, inspection, seed_parts,
gl_stock_integration and document_numbering.

Running the wizard programmatically here makes a fresh deploy self-sufficient:
no human has to open the browser and click through onboarding before the
workshop customisations can install. It is idempotent — once setup_complete is
1, it returns immediately.

Ordered FIRST in STEPS, before workshop_setup, since everything else assumes a
company and a chart of accounts already exist.
"""

import frappe

COMPANY = "خط الجزيرة"
ABBR = "KHAT"
COUNTRY = "Oman"
CURRENCY = "OMR"
TIMEZONE = "Asia/Muscat"


def _already_done():
    return bool(frappe.db.get_single_value("System Settings", "setup_complete"))


def execute():
    if _already_done():
        print("COMPANY_SETUP already complete — skipping")
        return

    from frappe.desk.page.setup_wizard.setup_wizard import setup_complete

    # The payload mirrors what the browser wizard posts. Only the fields ERPNext
    # actually reads are set; anything omitted falls back to its default.
    payload = {
        "language": "English",          # UI language is switched to Arabic later
        "country": COUNTRY,             # by workshop_language; the wizard itself
        "timezone": TIMEZONE,           # rejects a non-English value here.
        "currency": CURRENCY,
        "company_name": COMPANY,
        "company_abbr": ABBR,
        "chart_of_accounts": "Standard",
        "fy_start_date": "2026-01-01",
        "fy_end_date": "2026-12-31",
        "bank_account": "الحساب البنكي",
    }

    setup_complete(payload)
    frappe.db.commit()

    company = frappe.db.exists("Company", COMPANY)
    uoms = frappe.db.count("UOM")
    groups = frappe.db.count("Item Group")
    accounts = frappe.db.count("Account")
    print(
        "COMPANY_SETUP company=%s uoms=%d item_groups=%d accounts=%d"
        % (company, uoms, groups, accounts)
    )

    # A hard stop rather than a silent pass: if the wizard reported success but
    # produced no UOMs, every Item-creating step after this would fail the same
    # way it did before, and a confusing error six steps later is worse than a
    # clear one here.
    if not uoms:
        frappe.throw("setup wizard finished but created no UOM records")
