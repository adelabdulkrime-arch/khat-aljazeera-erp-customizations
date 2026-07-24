# -*- coding: utf-8 -*-
"""The four workshop reports the dashboard links to.

The Workshop dashboard has tiles for تقرير الإيرادات and تقرير الفنيين, and a
links card for those plus تقرير العمولات and تقرير بطاقات العمل. The reports
themselves were never created, so clicking a tile opened /query-report/<name>
for a report that does not exist and threw a server error. The links card was
already filtered to existing reports, but the tiles were not — so this creates
the reports rather than stripping the tiles, which also gives us the reporting
Mazoon shows.

Plain Query Reports (SQL), same mechanism as Maintenance Reminders. Column
headers use Frappe's "Label:Type:Width" form, Arabic so they read natively.
"""

import frappe

ROLES = ("System Manager", "Workshop Manager", "محاسب")

# name -> (ref_doctype, query)
REPORTS = {
    "تقرير بطاقات العمل": ("Work Card", """
        SELECT wc.name              AS "البطاقة:Link/Work Card:140",
               wc.customer          AS "العميل:Data:150",
               wc.service_line      AS "خط الخدمة:Data:110",
               wc.status            AS "الحالة:Data:110",
               wc.grand_total       AS "الإجمالي:Currency:110",
               wc.total_cost        AS "التكلفة:Currency:100",
               wc.gross_profit      AS "الربح:Currency:100",
               wc.entry_date        AS "تاريخ الدخول:Date:110"
        FROM `tabWork Card` wc
        WHERE wc.docstatus < 2
        ORDER BY wc.entry_date DESC
    """),
    "تقرير الإيرادات": ("Sales Invoice", """
        SELECT si.name                    AS "الفاتورة:Link/Sales Invoice:160",
               si.customer                AS "العميل:Data:150",
               si.posting_date            AS "التاريخ:Date:100",
               si.net_total               AS "الصافي:Currency:100",
               si.total_taxes_and_charges AS "الضريبة:Currency:90",
               si.grand_total             AS "الإجمالي:Currency:110",
               si.status                  AS "الحالة:Data:100"
        FROM `tabSales Invoice` si
        WHERE si.docstatus = 1
        ORDER BY si.posting_date DESC
    """),
    "تقرير الفنيين": ("Workshop Technician", """
        SELECT t.technician_name              AS "الفني:Data:160",
               t.specialization               AS "التخصص:Data:110",
               COUNT(DISTINCT wct.parent)     AS "عدد البطاقات:Int:100",
               COALESCE(SUM(wct.hours), 0)    AS "الساعات:Float:90",
               COALESCE(SUM(wct.commission),0) AS "إجمالي العمولات:Currency:130"
        FROM `tabWorkshop Technician` t
        LEFT JOIN `tabWork Card Technician` wct ON wct.technician = t.name
        LEFT JOIN `tabWork Card` wc ON wc.name = wct.parent AND wc.docstatus = 1
        GROUP BY t.name
        ORDER BY 5 DESC
    """),
    "تقرير العمولات": ("Work Card", """
        SELECT wct.technician  AS "الفني:Data:160",
               wct.parent      AS "البطاقة:Link/Work Card:140",
               wct.task        AS "المهمة:Data:160",
               wct.hours       AS "الساعات:Float:80",
               wct.commission  AS "العمولة:Currency:110"
        FROM `tabWork Card Technician` wct
        INNER JOIN `tabWork Card` wc ON wc.name = wct.parent AND wc.docstatus = 1
        ORDER BY wct.parent DESC
    """),
}


def _upsert(name, ref_doctype, query):
    query = query.strip()
    if frappe.db.exists("Report", name):
        doc = frappe.get_doc("Report", name)
        changed = False
        if (doc.query or "").strip() != query:
            doc.query = query
            changed = True
        if doc.ref_doctype != ref_doctype:
            doc.ref_doctype = ref_doctype
            changed = True
        if changed:
            doc.save(ignore_permissions=True)
        return "updated" if changed else "ok"

    doc = frappe.get_doc({
        "doctype": "Report", "report_name": name,
        "ref_doctype": ref_doctype, "report_type": "Query Report",
        "is_standard": "No", "query": query,
    })
    for role in ROLES:
        if frappe.db.exists("Role", role):
            doc.append("roles", {"role": role})
    doc.insert(ignore_permissions=True)
    return "created"


def execute():
    states = {}
    for name, (ref, query) in REPORTS.items():
        states[name] = _upsert(name, ref, query)
    frappe.db.commit()
    frappe.clear_cache()
    print("WORKSHOP_REPORTS %s" % ", ".join("%s=%s" % (k[-6:], v) for k, v in states.items()))
