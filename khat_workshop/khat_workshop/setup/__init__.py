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
    # FIRST, before anything else: completes ERPNext's setup wizard on a fresh
    # site. `bench new-site --install-app erpnext` leaves setup_complete = 0,
    # so the Company, chart of accounts, default UOMs and base Item Groups are
    # never created — and every step below that creates an Item then dies on
    # "Could not find Default Unit of Measure: Nos". Idempotent: a no-op once
    # the site is already onboarded.
    "workshop_company",
    "workshop_setup",
    # Right after setup, which creates the first roles: align the full list and
    # labels with Mazoon's fourteen before anything else references them.
    "workshop_roles",
    # Needs the roles above to exist before it can hand them to the client's
    # trial account. Early rather than late on purpose: workshop_landing, near
    # the end, stamps a default workspace onto every enabled System User, so
    # creating the account here means it is picked up by that pass.
    "workshop_demo_user",
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
    # Translate every role name to Arabic and English + a list client script,
    # so the standard Role list reads consistently in the chosen language. Also
    # tears down the earlier custom Roles page. After workshop_roles (its ROLES
    # provide the workshop labels) and general_settings (owns the tile).
    "workshop_role_i18n",
    "workshop_scripts",
    # Must precede gl_stock_integration: the parts-issue script binds to the
    # On Submit event, which only exists once the doctype is submittable.
    "workshop_work_card_control",
    "workshop_service_catalogue",
    # Same item-group mechanism as the line above, one level more granular —
    # the specific "تبديل X" operations the owner asked for by name.
    "workshop_replacement_operations",
    "workshop_packages",
    # Needs Work Card Technician to exist, so it follows work_card_control.
    "workshop_labour_costing",
    "workshop_vehicle_intake",
    # The mechanical counterpart to the intake check above, and it must follow
    # it: its section is anchored to `customer_signature`, the last field
    # vehicle_intake adds.
    "workshop_inspection",
    "workshop_maintenance",
    "workshop_seed_data",
    "workshop_seed_parts",
    # Reads the seeded catalogue to derive its levels, so it must follow it.
    "workshop_stock_alerts",
    "workshop_gl_stock_integration",
    # Needs the `vehicle` field the step above adds to Sales Invoice/Quotation.
    # WI-/WQ- series so a workshop job is numbered differently from a plain
    # counter sale, matching what the owner has seen in Mazoon.
    "workshop_document_numbering",
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
    # Needs the `vehicle` custom field gl_stock_integration put on Sales
    # Invoice/Quotation, and the Items workshop_replacement_operations seeds.
    "workshop_operations_print_format",
    # Late: every doctype the matrix references (Work Card, packages, sales,
    # stock…) and every role must already exist before permissions attach.
    "workshop_permissions",
    "workshop_oman_setup2",
    "workshop_landing",
    # After landing, which is the last step that creates or reorders workspaces:
    # this one reassigns them to khat_workshop (so the sidebar header stops
    # reading "Frappe Framework" / "ERPNext") and hides the unused HR ones.
    "workshop_workspace_polish",
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
