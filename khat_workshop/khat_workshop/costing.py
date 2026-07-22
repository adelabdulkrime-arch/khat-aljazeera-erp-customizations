# -*- coding: utf-8 -*-
"""Work out what a job actually cost, and therefore what it earned.

Until now the workshop knew its revenue and nothing else. Parts left stock and
technicians did the work, but no figure anywhere answered "did we make money on
this card?" — so pricing was guesswork and no service line could be compared
against another.

Cost has three parts here:

  * labour   — hours x the technician's hourly cost
  * commission — already tracked per technician row; it is real money out
  * parts    — the ACTUAL valuation of what left the shelf, taken from the
               Stock Entry when one exists, not the price we charged for it

The parts figure matters most. Charging 10 for a part bought at 6 is a margin
of 4, and only the Stock Entry knows the 6. Before submit there is no Stock
Entry yet, so we fall back to each item's current valuation rate — an estimate
that becomes exact the moment the parts are issued.

Attached through doc_events rather than a Server Script: this needs to read
other doctypes and share one code path between save and submit, and it belongs
in version control next to the fields it fills.
"""

import frappe
from frappe.utils import flt


def _parts_cost(doc):
    """Actual cost of parts consumed — real valuation, never selling price."""
    if doc.get("stock_entry"):
        outgoing = frappe.db.get_value(
            "Stock Entry", doc.stock_entry, "total_outgoing_value")
        if outgoing:
            return flt(outgoing)

    # Not issued yet: estimate from current valuation.
    total = 0.0
    for row in doc.get("parts") or []:
        if not row.item:
            continue
        rate = frappe.db.get_value("Item", row.item, "valuation_rate") or 0
        total += flt(row.qty) * flt(rate)
    return total


def _revenue(doc):
    """What the card bills.

    grand_total is filled by a client script in the browser, so a card created
    through the API or a script arrives with it empty — and a margin computed
    against an empty revenue would silently read as a total loss. Fall back to
    the line items, which are always present, and repair grand_total while we
    are here so the rest of the system sees the same number.
    """
    if flt(doc.get("grand_total")):
        return flt(doc.grand_total)

    services = sum(flt(r.get("amount")) or flt(r.get("qty")) * flt(r.get("rate"))
                   for r in doc.get("services") or [])
    parts = sum(flt(r.get("amount")) or flt(r.get("qty")) * flt(r.get("rate"))
                for r in doc.get("parts") or [])
    total = flt(services + parts - flt(doc.get("discount")), 3)

    if total:
        doc.services_total = flt(services, 3)
        doc.parts_total = flt(parts, 3)
        doc.grand_total = total
    return total


def compute(doc, method=None):
    """Fill the costing block. Safe to call repeatedly."""
    labour_hours = labour_cost = commission_total = 0.0

    for row in doc.get("technicians") or []:
        # Rate defaults from the technician but stays editable: overtime and
        # trainees do not bill at the standard rate.
        if not row.get("hourly_cost") and row.get("technician"):
            row.hourly_cost = frappe.db.get_value(
                "Workshop Technician", row.technician, "hourly_cost") or 0

        hours = flt(row.get("hours"))
        row.labour_cost = flt(hours * flt(row.get("hourly_cost")), 3)

        labour_hours += hours
        labour_cost += flt(row.labour_cost)
        commission_total += flt(row.get("commission"))

    parts_cost = _parts_cost(doc)
    total_cost = flt(labour_cost + commission_total + parts_cost, 3)
    revenue = _revenue(doc)

    doc.labour_hours = flt(labour_hours, 2)
    doc.labour_cost = flt(labour_cost, 3)
    doc.commission_total = flt(commission_total, 3)
    doc.parts_cost = flt(parts_cost, 3)
    doc.total_cost = total_cost
    doc.gross_profit = flt(revenue - total_cost, 3)
    # Margin on zero revenue is undefined, not zero — leave it blank rather
    # than print a figure that invites a wrong conclusion.
    doc.margin_pct = flt(doc.gross_profit / revenue * 100, 2) if revenue else None


def recompute_on_submit(doc, method=None):
    """Refresh once the Stock Entry exists, so parts cost becomes exact.

    The parts issue runs on After Submit, and script ordering is not
    guaranteed, so the Stock Entry may or may not be there yet. Either way the
    figure written is the best one available at that moment, and any later save
    settles it.
    """
    compute(doc)
    for field in ("labour_hours", "labour_cost", "commission_total",
                  "parts_cost", "total_cost", "gross_profit", "margin_pct"):
        doc.db_set(field, doc.get(field), update_modified=False)
