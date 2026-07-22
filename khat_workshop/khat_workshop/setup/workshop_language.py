# -*- coding: utf-8 -*-
"""Make Arabic the site's language, not a per-user preference.

The workshop's labels are written in Arabic natively; workshop_translations
registers the *English* renderings under language "en" for anyone who prefers
them. So Arabic is the default the system was built around — but System
Settings has said "English" since the site was first created on 20 July, which
was never corrected when the country was moved from Yemen to Oman a few hours
later.

Nobody noticed because the account doing the work had Arabic set personally.
Administrator did not, so the same system showed Arabic or English depending on
who opened it — and a client seeing English on a system sold as Arabic reads it
as unfinished.

Users who have deliberately chosen a language keep it. Only the blanks, which
silently inherit the site default, are filled.
"""

import frappe

LANG = "ar"


def execute():
    changed = []

    if frappe.db.get_single_value("System Settings", "language") != LANG:
        frappe.db.set_single_value("System Settings", "language", LANG)
        changed.append("system_settings")

    if frappe.db.get_default("lang") != LANG:
        frappe.db.set_default("lang", LANG)
        changed.append("default_lang")

    # Only fill in users who never chose; never overwrite a stated preference.
    filled = 0
    for user in frappe.get_all(
        "User", filters={"enabled": 1, "user_type": "System User", "language": ["in", ["", None]]},
        pluck="name"
    ):
        frappe.db.set_value("User", user, "language", LANG)
        filled += 1

    frappe.db.commit()
    frappe.clear_cache()
    print("LANGUAGE target=%s changed=%s users_filled=%d"
          % (LANG, ",".join(changed) or "already set", filled))
