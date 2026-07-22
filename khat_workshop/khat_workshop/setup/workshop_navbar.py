# -*- coding: utf-8 -*-
"""Put the language switch where v16 actually keeps its menu items.

The old switcher was injected into the navbar by desk.js, which looked for
`.page-icon-group` — a v15 element. v16 replaced the top navbar with a sidebar,
that class no longer exists, and the script returned on its second line. It
failed exactly the way we keep getting caught: silently, leaving something that
looks implemented but does nothing.

Navbar Settings is the supported route. It is a DocType, so the item survives
whatever the interface looks like next, and no selector can go stale.

One toggle rather than two entries: it always offers the language you are not
using, so it needs no condition logic and reads the same in either direction.
"""

import frappe

LABEL = "العربية / English"

# Reads the live language from boot rather than being baked per-user, so one
# item serves everyone. Navbar Item.action caps at 140 characters, hence the
# terse form — it does not have room to be readable.
ACTION = (
    "frappe.db.set_value('User',frappe.session.user,'language',"
    "frappe.boot.lang=='ar'?'en':'ar').then(()=>location.reload())"
)

# Offering a client a button labelled "Delete Demo Data" is at best confusing
# and at worst exactly what it says. Hidden, not deleted — it is a standard
# ERPNext item and migrate would put it back anyway.
HIDE = ["Delete Demo Data"]


def execute():
    settings = frappe.get_single("Navbar Settings")
    changed = []

    existing = next((r for r in settings.settings_dropdown
                     if r.item_label == LABEL), None)
    if existing is None:
        settings.append("settings_dropdown", {
            "item_label": LABEL,
            "item_type": "Action",
            "action": ACTION,
            "icon": "globe",
        })
        changed.append("added")
    elif existing.action != ACTION or existing.hidden:
        existing.action = ACTION
        existing.hidden = 0
        changed.append("updated")

    for row in settings.settings_dropdown:
        if row.item_label in HIDE and not row.hidden:
            row.hidden = 1
            changed.append("hid:%s" % row.item_label)

    if changed:
        settings.save(ignore_permissions=True)
        frappe.db.commit()

    frappe.clear_cache()
    print("NAVBAR %s items=%d"
          % (",".join(changed) or "already set", len(settings.settings_dropdown)))
