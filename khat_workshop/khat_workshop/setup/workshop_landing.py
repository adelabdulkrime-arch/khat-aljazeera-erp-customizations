# -*- coding: utf-8 -*-
"""Make the workshop dashboard the first thing anyone sees.

Three problems this fixes, all first-impression issues:

1. Logging in landed on the generic ERPNext module grid — Manufacturing,
   Subcontracting, Projects, Quality — so the branded dashboard we built was
   hidden behind a click, and the first screen looked like a stock install
   rather than the client's own system.

2. "Workshop" and "Home" both carried sequence_id 1.0, so sidebar order was
   non-deterministic.

3. Modules irrelevant to a vehicle workshop were on display, which makes the
   system feel unfitted and gives staff places to wander into.

4. Opening the bare domain landed on the legacy /desk module grid instead of
   the desk. That page is built from Module Def records, so it ignores
   workspace ordering and hiding entirely and shows none of our dashboards —
   the customisation looked absent when it was in fact applied.

   NOTE, learned by breaking the site: this is NOT fixed by setting
   Website Settings.home_page to "app". home_page must name a *website route*,
   and "app" is not one, so the router 404s and the root URL dies for everyone.
   A redirect is the correct mechanism.

Idempotent. Every change here is reversible: nothing is deleted, workspaces
are only flagged, and the redirect row can be removed from Website Settings.
"""

import frappe

LANDING = "Home"

# Where "/" should land. Frappe strips surrounding slashes from a redirect
# source, so source "/" becomes the pattern "$", which matches the empty path —
# the root URL — and nothing else. Guests following it are bounced on to /login
# by the desk itself; there is no public portal on this site.
#
# v16 moved the desk from /app to /desk and 301s the old path onward, so /app
# still resolves and keeps this working on either version. The workspace is
# named explicitly rather than relying on User.default_workspace, because bare
# /desk opens v16's module launcher instead of honouring it.
DESK_ROUTE = "/app/home"

# Ordered exactly as the workshop should read it.
ORDER = [
    ("Home", 1),
    ("General Settings", 2),
    ("Accounting Dashboard", 3),
    ("Inventory Dashboard", 4),
    ("Purchasing Dashboard", 5),
    ("Sales Dashboard", 6),
    ("Workshop", 7),
]

# Not deleted — hidden. A workshop has no use for these, and leaving them on
# screen makes the system look generic.
HIDE = [
    "Manufacturing", "Subcontracting", "Quality", "Projects", "Assets",
    "Support", "Build", "Welcome Workspace", "CRM", "Website", "Integrations",
]


def execute():
    # 1. deterministic sidebar order
    fixed = 0
    for name, seq in ORDER:
        if frappe.db.exists("Workspace", name):
            if frappe.db.get_value("Workspace", name, "sequence_id") != seq:
                frappe.db.set_value("Workspace", name, "sequence_id", seq)
                fixed += 1

    # 2. hide what a workshop never opens
    hidden = 0
    for name in HIDE:
        if frappe.db.exists("Workspace", name) and \
                not frappe.db.get_value("Workspace", name, "is_hidden"):
            frappe.db.set_value("Workspace", name, "is_hidden", 1)
            hidden += 1

    # 3. land every real user on the dashboard, not the module grid
    landed = 0
    if frappe.db.exists("Workspace", LANDING):
        for user in frappe.get_all(
            "User", filters={"enabled": 1, "user_type": "System User"}, pluck="name"
        ):
            if frappe.db.get_value("User", user, "default_workspace") != LANDING:
                frappe.db.set_value("User", user, "default_workspace", LANDING)
                landed += 1
        # applies to users created later too
        frappe.db.set_default("default_workspace", LANDING)

    redirected = _redirect_root_to_desk()

    frappe.db.commit()
    frappe.clear_cache()
    print("LANDING order_fixed=%d hidden=%d users_landed=%d target=%s root_redirect=%s"
          % (fixed, hidden, landed, LANDING, redirected))


def _redirect_root_to_desk():
    """Point "/" at the desk via Website Settings' redirect table.

    home_page cannot do this — see the module docstring. Leaving home_page
    empty keeps Frappe's own default behaviour intact as a fallback.
    """
    settings = frappe.get_single("Website Settings")
    if not hasattr(settings, "route_redirects"):
        # field renamed upstream; skip rather than fail the whole setup run
        return "unsupported"

    for row in settings.route_redirects:
        if (row.source or "").strip() == "/":
            if (row.target or "").strip() == DESK_ROUTE:
                return "already set"
            row.target = DESK_ROUTE
            settings.save(ignore_permissions=True)
            return "retargeted"

    settings.append("route_redirects", {"source": "/", "target": DESK_ROUTE})
    settings.save(ignore_permissions=True)
    return "created"
