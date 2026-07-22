# -*- coding: utf-8 -*-
"""Populate realistic data across every module, then verify each dashboard.

Fills in what earlier tests left empty — real customer names and Omani phone
numbers, fully-described vehicles, named technicians with commissions, and a
complete purchase cycle (Supplier -> Purchase Order -> Receipt -> Invoice) that
had never been exercised at all.

Then checks that each of the seven dashboards has data behind it, because a
dashboard that renders perfectly while showing zeros is still a broken
dashboard.
"""

import frappe

CUSTOMERS = [
    ("أسامة الحارثي", "+968 9123 4567"),
    ("خالد البلوشي", "+968 9234 5678"),
    ("سالم الشعيلي", "+968 9345 6789"),
    ("ناصر الكندي", "+968 9456 7890"),
    ("فاطمة السيابية", "+968 9567 8901"),
    ("محمد الرواحي", "+968 9678 9012"),
]

TECHNICIANS = [
    ("أحمد المعمري", "+968 9111 2222", "ميكانيكا", 8),
    ("يوسف الهنائي", "+968 9222 3333", "سمكرة", 10),
    ("راشد العامري", "+968 9333 4444", "دهان", 10),
    ("سعيد الغافري", "+968 9444 5555", "كهرباء", 7),
    ("بدر المقبالي", "+968 9555 6666", "تكييف", 7),
]

VEHICLES = [
    ("أسامة الحارثي", "١٢٣٤٥ أ ب", "تويوتا", "تويوتا-لاندكروزر", "2021", "أبيض", 85000),
    ("خالد البلوشي", "٢٣٤٥٦ ج د", "نيسان", "نيسان-باترول", "2019", "أسود", 120000),
    ("سالم الشعيلي", "٣٤٥٦٧ ه و", "لكزس", "لكزس-LX570", "2022", "فضي", 45000),
    ("ناصر الكندي", "٤٥٦٧٨ ز ح", "تويوتا", "تويوتا-كامري", "2020", "رمادي", 96000),
    ("فاطمة السيابية", "٥٦٧٨٩ ط ي", "هوندا", "هوندا-أكورد", "2023", "أزرق", 22000),
    ("محمد الرواحي", "٦٧٨٩٠ ك ل", "ميتسوبيشي", "ميتسوبيشي-باجيرو", "2018", "أخضر", 150000),
]

SUPPLIERS = [("مؤسسة الخليج لقطع الغيار", "+968 2411 1111"),
             ("شركة مسقط للزيوت", "+968 2422 2222")]


def _mk(doctype, filters, payload):
    existing = frappe.db.get_value(doctype, filters, "name")
    if existing:
        return existing
    return frappe.get_doc(dict(payload, doctype=doctype)).insert(ignore_permissions=True).name


def seed():
    n = {}
    for name, phone in CUSTOMERS:
        _mk("Customer", {"customer_name": name},
            {"customer_name": name, "mobile_no": phone})
    n["customers"] = frappe.db.count("Customer")

    for name, phone, spec, rate in TECHNICIANS:
        _mk("Workshop Technician", {"technician_name": name},
            {"technician_name": name, "phone": phone, "specialization": spec,
             "commission_rate": rate, "is_active": 1})
    n["technicians"] = frappe.db.count("Workshop Technician")

    for cust, plate, brand, model, year, color, km in VEHICLES:
        _mk("Customer Vehicle", {"plate_number": plate},
            {"customer": cust, "plate_number": plate, "brand": brand, "model": model,
             "year": year, "color": color, "mileage": km,
             "chassis_no": "CH%s" % plate[:5], "engine_no": "EN%s" % plate[:5],
             "customer_phone": dict(CUSTOMERS).get(cust, "")})
    n["vehicles"] = frappe.db.count("Customer Vehicle")

    for name, phone in SUPPLIERS:
        _mk("Supplier", {"supplier_name": name},
            {"supplier_name": name, "mobile_no": phone})
    n["suppliers"] = frappe.db.count("Supplier")
    return n


def purchase_cycle():
    """The one flow never tested: buying parts into stock."""
    if frappe.db.count("Purchase Invoice", {"docstatus": 1}):
        return "already run"
    company = frappe.db.get_single_value("Global Defaults", "default_company")
    supplier = frappe.db.get_value("Supplier", {}, "name")
    wh = frappe.db.get_value("Custom Field", "Work Card-warehouse", "default")
    items = [{"item_code": "SP-FLT-OIL", "qty": 20, "rate": 2.0, "warehouse": wh},
             {"item_code": "SP-OIL-5W30", "qty": 30, "rate": 12.0, "warehouse": wh}]

    po = frappe.get_doc({"doctype": "Purchase Order", "supplier": supplier,
                         "company": company, "schedule_date": frappe.utils.nowdate(),
                         "items": items}).insert(ignore_permissions=True)
    po.submit()

    pr = frappe.get_doc({"doctype": "Purchase Receipt", "supplier": supplier,
                         "company": company,
                         "items": [dict(i, purchase_order=po.name,
                                        purchase_order_item=po.items[idx].name)
                                   for idx, i in enumerate(items)]}).insert(ignore_permissions=True)
    pr.submit()

    pi = frappe.get_doc({"doctype": "Purchase Invoice", "supplier": supplier,
                         "company": company,
                         "items": [dict(i, purchase_receipt=pr.name,
                                        pr_detail=pr.items[idx].name)
                                   for idx, i in enumerate(items)]}).insert(ignore_permissions=True)
    pi.submit()
    return "%s -> %s -> %s" % (po.name, pr.name, pi.name)


def verify_dashboards():
    """Each dashboard needs data behind it, not just a page that renders."""
    checks = [
        ("الورشة", frappe.db.count("Work Card")),
        ("المبيعات", frappe.db.count("Sales Invoice", {"docstatus": 1})),
        ("المشتريات", frappe.db.count("Purchase Invoice", {"docstatus": 1})),
        ("المخزون", frappe.db.count("Bin", {"actual_qty": [">", 0]})),
        ("المحاسبة", frappe.db.count("GL Entry", {"is_cancelled": 0})),
        ("الإعدادات العامة", frappe.db.count("User", {"enabled": 1})),
        ("الرئيسية/العملاء", frappe.db.count("Customer")),
    ]
    ok = True
    for label, count in checks:
        good = count > 0
        ok = ok and good
        print("  [%s] %-18s %s" % ("PASS" if good else "FAIL", label, count))
    return ok


def run():
    n = seed()
    print("seeded:", n)
    print("purchase cycle:", purchase_cycle())
    print("=== dashboard data ===")
    ok = verify_dashboards()
    frappe.db.commit()
    print("FULL_RESULT=%s" % ("PASS" if ok else "FAIL"))
