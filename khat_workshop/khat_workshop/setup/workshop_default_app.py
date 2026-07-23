# -*- coding: utf-8 -*-
"""Make a fresh login land on the dashboard, not the module grid.

See the add_to_apps_screen hook for the mechanism. In short: frappe's login
picks get_default_path() before get_home_page(), and get_default_path() returns
the bare /desk grid when several desk apps are installed and no default_app is
set. Setting the default_app to khat_workshop — whose registered route is
/desk/home — makes get_default_path() return the dashboard instead.

System-level, not per-user, so it holds for every account including ones
created later. A user who deliberately sets their own default_app still wins,
because get_default_path() checks the user value first.
"""

import frappe

DEFAULT_APP = "khat_workshop"


def execute():
    if "khat_workshop" not in frappe.get_installed_apps():
        print("DEFAULT_APP skipped — khat_workshop not installed")
        return

    current = frappe.get_system_settings("default_app")
    if current == DEFAULT_APP:
        print("DEFAULT_APP already %s" % DEFAULT_APP)
        return

    frappe.db.set_single_value("System Settings", "default_app", DEFAULT_APP)
    frappe.db.commit()
    frappe.clear_cache()
    print("DEFAULT_APP set %r -> %r" % (current, DEFAULT_APP))
