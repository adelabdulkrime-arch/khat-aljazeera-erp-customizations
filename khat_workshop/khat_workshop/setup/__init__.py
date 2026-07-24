"""Ordered, idempotent setup steps for the Khat Workshop app.

Invoked by the `after_migrate` hook, so every `bench migrate` re-applies the
full customisation set — the same behaviour init.sh used to provide by copying
scripts into apps/frappe/frappe/ and executing them one at a time.
"""

import importlib
import traceback

import frappe

# Order matters:
#   - workshop_setup creates the custom DocTypes and roles everything else
#     references, so it MUST be first.
#   - workshop_oman_setup2 retags the chart of accounts to OMR and must run
#     BEFORE workshop_oman_setup performs the currency switch.
#
# workshop_futuristic is deliberately absent: it is a shared CSS/JS library
# imported by the dashboard builders and exposes no execute(). Listing it here
# is what previously produced an "has no attribute 'execute'" failure on every
# single deploy.
STEPS = [
    "workshop_setup",
    # Right after setup, which creates the first roles: align the full list and
    # labels with Mazoon's fourteen before anything else references them.
    "workshop_roles",
    "workshop_home",
    "workshop_dashboard",
    # Creates the four reports the dashboard tiles link to, so clicking a
    # report tile opens a report instead of a server error.
    "workshop_reports",
    "workshop_accounting",
    "workshop_inventory",
    "workshop_purchasing",
    "workshop_sales",
    "workshop_general_settings",
    # After general_settings (its tile points here) and after workshop_roles
    # (its ROLES list is the data source).
    "workshop_roles_page",
    "workshop_scripts",
    # Must precede gl_stock_integration: the parts-issue script binds to the
    # On Submit event, which only exists once the doctype is submittable.
    "workshop_work_card_control",
    "workshop_service_catalogue",
    "workshop_packages",
    # Needs Work Card Technician to exist, so it follows work_card_control.
    "workshop_labour_costing",
    "workshop_vehicle_intake",
    "workshop_maintenance",
    "workshop_seed_data",
    "workshop_seed_parts",
    # Reads the seeded catalogue to derive its levels, so it must follow it.
    "workshop_stock_alerts",
    "workshop_gl_stock_integration",
    # Must come AFTER gl_stock_integration, which deletes the mirroring Server
    # Scripts. Dropping a doctype while a Server Script still references it
    # would leave the script pointing at nothing.
    "workshop_retire_shadow",
    "workshop_invoice_whatsapp",
    "workshop_translations",
    # After translations: the English renderings must exist before anyone can
    # switch to English and find half a screen untranslated.
    "workshop_language",
    "workshop_navbar",
    "workshop_branding",
    "workshop_default_app",
    # After every dashboard exists, so the nav can link to all seven.
    "workshop_sidebar_nav",
    "workshop_print_template",
    "workshop_oman_setup2",
    "workshop_landing",
    "workshop_oman_setup",
]


def run_all():
    """Run every setup step in order.

    A failing step is logged and skipped rather than aborting the run: losing
    one dashboard is better than losing every customisation after it. Each step
    is committed on success and rolled back on failure, so a partial failure
    cannot leave half-written state behind.
    """
    failures = []

    for name in STEPS:
        try:
            module = importlib.import_module("khat_workshop.setup.%s" % name)
            module.execute()
            frappe.db.commit()
            print("[khat_workshop]   OK    %s" % name)
        except Exception:
            frappe.db.rollback()
            failures.append(name)
            print("[khat_workshop]   FAIL  %s" % name)
            print(traceback.format_exc())

    if failures:
        print(
            "[khat_workshop] finished with %d failure(s): %s"
            % (len(failures), ", ".join(failures))
        )
    else:
        print("[khat_workshop] all %d steps OK" % len(STEPS))

    frappe.clear_cache()
