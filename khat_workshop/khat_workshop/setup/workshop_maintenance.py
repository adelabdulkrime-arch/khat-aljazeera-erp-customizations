# -*- coding: utf-8 -*-
"""Maintenance reminders: which vehicles are due for service soon.

Adds the two dates that khat_workshop.maintenance stamps on each vehicle, and a
report that lists everything due inside the next 30 days — the workshop's
call-back list, and Mazoon's Maintenance Reminders screen. The report name is
registered in Arabic so it reads تذكيرات الصيانة on the desk.
"""

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

REPORT = "Maintenance Reminders"

# Plain SQL query report: due within 30 days, soonest first. Column headers use
# Frappe's "Label:Type:Width" form and are Arabic so the report reads natively.
QUERY = """
SELECT
    cv.plate_number                          AS "رقم اللوحة:Data:110",
    cv.customer                              AS "العميل:Data:170",
    cv.customer_phone                        AS "الهاتف:Data:120",
    cv.brand                                 AS "البراند:Data:120",
    cv.last_service_date                     AS "آخر صيانة:Date:110",
    cv.next_service_date                     AS "الصيانة القادمة:Date:120",
    DATEDIFF(cv.next_service_date, CURDATE()) AS "باقٍ (يوم):Int:90"
FROM `tabCustomer Vehicle` cv
WHERE cv.next_service_date IS NOT NULL
  AND cv.next_service_date <= DATE_ADD(CURDATE(), INTERVAL 30 DAY)
ORDER BY cv.next_service_date ASC
"""

ROLES = ("System Manager", "Workshop Manager", "محاسب")


def _fields():
    return {"Customer Vehicle": [
        {"fieldname": "last_service_date", "label": "تاريخ آخر صيانة",
         "fieldtype": "Date", "insert_after": "mileage", "read_only": 1},
        {"fieldname": "next_service_date", "label": "تاريخ الصيانة القادمة",
         "fieldtype": "Date", "insert_after": "last_service_date"},
    ]}


def _report():
    if frappe.db.exists("Report", REPORT):
        doc = frappe.get_doc("Report", REPORT)
        if (doc.query or "").strip() != QUERY.strip():
            doc.query = QUERY
            doc.save(ignore_permissions=True)
        return "updated"

    doc = frappe.get_doc({
        "doctype": "Report", "report_name": REPORT,
        "ref_doctype": "Customer Vehicle", "report_type": "Query Report",
        "is_standard": "No", "query": QUERY,
    })
    for role in ROLES:
        if frappe.db.exists("Role", role):
            doc.append("roles", {"role": role})
    doc.insert(ignore_permissions=True)
    return "created"


def _translate():
    if frappe.db.exists("Translation", {"source_text": REPORT, "language": "ar"}):
        return
    frappe.get_doc({
        "doctype": "Translation", "language": "ar",
        "source_text": REPORT, "translated_text": "تذكيرات الصيانة",
    }).insert(ignore_permissions=True)


def execute():
    create_custom_fields(_fields(), update=True)
    state = _report()
    _translate()
    frappe.db.commit()
    frappe.clear_cache()
    print("MAINTENANCE fields=ok report=%s" % state)
