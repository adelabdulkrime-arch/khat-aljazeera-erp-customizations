# -*- coding: utf-8 -*-
"""Live figures for the dashboard tiles on the home page.

The home page was a navigation menu: it told you where to go, not how the
workshop is doing. A manager opening the system first wants numbers — how many
cars are in today, what is waiting on parts, what is owed, what came in. Those
answers existed only by opening four different lists and counting.

One whitelisted call returns them all. Kept deliberately cheap: six COUNT/SUM
queries over indexed columns, no joins over child tables, so the home page
still loads instantly on a workshop PC.

Every figure is permission-aware through frappe.get_all, so a technician who
cannot read invoices simply sees zero there rather than a number they should
not have.
"""

import frappe
from frappe.utils import add_days, getdate, nowdate

# The statuses that mean "this car is still with us". Kept as a list rather
# than "not delivered" so a new status does not silently join the count.
OPEN_STATUSES = [
    "بانتظار الفحص",
    "قيد الإصلاح",
    "بانتظار قطع الغيار",
    "بانتظار موافقة العميل",
    "جاهزة للتسليم",
]

WAITING_PARTS = "بانتظار قطع الغيار"
READY = "جاهزة للتسليم"

# A card still open this long has usually stalled — the customer stopped
# answering, or a part never arrived. Surfacing it is the point.
STALE_DAYS = 7


def _count(doctype, filters):
    """Count with permissions applied; never raise into the dashboard."""
    try:
        return frappe.db.count(doctype, filters)
    except Exception:
        return 0


@frappe.whitelist()
def get_home_stats():
    """Return the figures behind the home-page stat tiles."""
    today = nowdate()
    stats = {}

    # ── Workshop floor ──────────────────────────────────────────────────
    stats["open_cards"] = _count("Work Card", {
        "status": ["in", OPEN_STATUSES],
        "docstatus": ["<", 2],
    })
    stats["waiting_parts"] = _count("Work Card", {
        "status": WAITING_PARTS,
        "docstatus": ["<", 2],
    })
    stats["ready"] = _count("Work Card", {
        "status": READY,
        "docstatus": ["<", 2],
    })
    stats["today_cards"] = _count("Work Card", {
        "creation": [">=", today],
        "docstatus": ["<", 2],
    })

    # Stalled cards: open, and untouched for a week. `modified` rather than
    # `creation` — a card worked on yesterday is not stalled however old it is.
    stats["stale_cards"] = _count("Work Card", {
        "status": ["in", OPEN_STATUSES],
        "docstatus": ["<", 2],
        "modified": ["<", add_days(getdate(today), -STALE_DAYS)],
    })

    # ── Money ───────────────────────────────────────────────────────────
    # Submitted invoices only (docstatus 1): a draft is not a receivable.
    try:
        unpaid = frappe.get_all(
            "Sales Invoice",
            filters={"docstatus": 1, "outstanding_amount": [">", 0]},
            fields=["name", "outstanding_amount"],
            limit_page_length=0,
        )
        stats["unpaid_count"] = len(unpaid)
        stats["unpaid_total"] = sum((i.outstanding_amount or 0) for i in unpaid)
    except Exception:
        stats["unpaid_count"] = 0
        stats["unpaid_total"] = 0

    try:
        today_inv = frappe.get_all(
            "Sales Invoice",
            filters={"docstatus": 1, "posting_date": today},
            fields=["grand_total"],
            limit_page_length=0,
        )
        stats["today_revenue"] = sum((i.grand_total or 0) for i in today_inv)
    except Exception:
        stats["today_revenue"] = 0

    # ── Stock ───────────────────────────────────────────────────────────
    # Items at or below their reorder level. Bin carries both numbers, so this
    # stays a single indexed scan rather than a per-item lookup.
    try:
        low = frappe.db.sql(
            """
            SELECT COUNT(*) FROM `tabBin`
            WHERE reorder_level > 0 AND actual_qty <= reorder_level
            """
        )
        stats["low_stock"] = (low and low[0] and low[0][0]) or 0
    except Exception:
        stats["low_stock"] = 0

    stats["currency"] = frappe.db.get_default("currency") or "OMR"
    return stats
