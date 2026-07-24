# -*- coding: utf-8 -*-
"""Track when each vehicle is next due for service.

The second operational feature our Workshop dashboard lacked against Mazoon:
knowing which cars are due soon so the workshop can call the owner back. Every
time a job card is submitted, the vehicle's last service is stamped today and
its next service is set a service-interval ahead. The Maintenance Reminders
report (see setup/workshop_maintenance) then lists whatever falls due.

The interval matches Mazoon's default of three months. It is a module constant
for now rather than a setting; making it configurable is a small follow-up.
"""

import frappe
from frappe.utils import add_months, nowdate

SERVICE_INTERVAL_MONTHS = 3


def set_next_service(doc, method=None):
    if not doc.get("vehicle"):
        return
    if not frappe.db.exists("Customer Vehicle", doc.vehicle):
        return

    today = nowdate()
    frappe.db.set_value(
        "Customer Vehicle", doc.vehicle,
        {
            "last_service_date": today,
            "next_service_date": add_months(today, SERVICE_INTERVAL_MONTHS),
        },
        update_modified=False,
    )
