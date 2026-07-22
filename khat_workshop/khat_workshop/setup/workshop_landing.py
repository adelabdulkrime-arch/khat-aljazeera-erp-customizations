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

Idempotent. Hiding is reversible: nothing is deleted, only flagged.
"""

import frappe

LANDING = "Home"

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

    frappe.db.commit()
    frappe.clear_cache()
    print("LANDING order_fixed=%d hidden=%d users_landed=%d target=%s"
          % (fixed, hidden, landed, LANDING))
