# -*- coding: utf-8 -*-
"""Warn before a part runs out, instead of discovering it on a lifted car.

Today the workshop learns a part is finished when a technician needs it. The
job stops, the customer waits, and someone drives to a supplier at retail
price. ERPNext can prevent that natively: give each item a reorder level and
the scheduler raises a Material Request the moment stock falls through it.

Three things must all be true or nothing fires — and each fails silently:

  1. Stock Settings.auto_indent enabled,
  2. a reorder row on every item,
  3. the scheduler actually running on the site.

The third is the one that bites. We already lost a full round of work to
server_script_enabled being off while everything *looked* healthy; a disabled
scheduler fails the same way, so it is checked and enabled here rather than
assumed.

Levels are derived from the seeded opening quantities rather than hard-coded,
so this file cannot drift out of step with the catalogue.
"""

import frappe

from khat_workshop.setup.workshop_seed_parts import PARTS, _warehouse

# Roughly two weeks of cover at the opening turnover. The floor matters more
# than the ratio: a radiator with 5 on hand would otherwise get a level of 1
# and reorder only after the shelf is bare.
COVER_RATIO = 0.3
MIN_LEVEL = 2


def _levels(opening_qty):
    """Return (reorder_level, reorder_qty) for a given opening quantity."""
    level = max(MIN_LEVEL, int(round(opening_qty * COVER_RATIO)))
    # Restock to about where we started; ordering less than the trigger level
    # just produces a second request days later.
    return level, max(opening_qty, level * 2)


def _enable_auto_reorder():
    settings = frappe.get_single("Stock Settings")
    changed = []

    if not settings.auto_indent:
        settings.auto_indent = 1
        changed.append("auto_indent")

    # Only switch on email if the site can actually send. Enabling it without
    # an outgoing account makes the daily reorder job raise instead of
    # creating the Material Requests, which would be worse than no email.
    if frappe.db.exists("Email Account", {"enable_outgoing": 1}):
        if not settings.reorder_email_notify:
            settings.reorder_email_notify = 1
            changed.append("reorder_email_notify")

    if changed:
        settings.save(ignore_permissions=True)
    return changed


def _enable_scheduler():
    """A stopped scheduler means reorder never runs — and says nothing.

    Frappe splits this across two places: `enable_scheduler` is a System
    Settings field we can set, while `pause_scheduler`, `disable_scheduler` and
    `maintenance_mode` live in site_config and can only be changed with
    `bench set-config`. Both halves must be clear, so the half we cannot fix is
    reported loudly instead of being assumed clean.
    """
    notes = []

    try:
        enabled = frappe.utils.cint(
            frappe.db.get_single_value("System Settings", "enable_scheduler"))
    except Exception:
        return "unsupported"

    if not enabled:
        frappe.db.set_single_value("System Settings", "enable_scheduler", 1)
        notes.append("enabled")

    for key in ("pause_scheduler", "disable_scheduler", "maintenance_mode"):
        if frappe.conf.get(key):
            notes.append("BLOCKED-BY conf.%s" % key)

    return ",".join(notes) or "already running"


def _set_reorder_levels(warehouse):
    added = updated = 0

    for code, _name, _cost, opening in PARTS:
        if not frappe.db.exists("Item", code):
            continue

        level, qty = _levels(opening)
        item = frappe.get_doc("Item", code)

        row = next((r for r in item.reorder_levels
                    if r.warehouse == warehouse), None)

        if row is None:
            item.append("reorder_levels", {
                "warehouse": warehouse,
                "warehouse_reorder_level": level,
                "warehouse_reorder_qty": qty,
                "material_request_type": "Purchase",
            })
            item.save(ignore_permissions=True)
            added += 1
            continue

        # Never overwrite a level the owner has tuned by hand — only fill in
        # rows that were left empty.
        if not row.warehouse_reorder_level:
            row.warehouse_reorder_level = level
            row.warehouse_reorder_qty = qty
            item.save(ignore_permissions=True)
            updated += 1

    return added, updated


def execute():
    warehouse = _warehouse()
    if not warehouse:
        print("STOCK_ALERTS no warehouse — skipped")
        return

    changed = _enable_auto_reorder()
    scheduler = _enable_scheduler()
    added, updated = _set_reorder_levels(warehouse)

    frappe.db.commit()
    print("STOCK_ALERTS warehouse=%s settings=%s scheduler=%s rows_added=%d rows_filled=%d"
          % (warehouse, ",".join(changed) or "already set", scheduler, added, updated))
