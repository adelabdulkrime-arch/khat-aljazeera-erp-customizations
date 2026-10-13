# -*- coding: utf-8 -*-
"""كل مسمّى وظيفي يرى لوحاته ويملك ما يحتاجه عمله.

يحرس خللين لا يظهران لمن يختبر بحساب Administrator، وقد وصل كلاهما إلى نسخة
الاختبار قبل أن يُكتب هذا الفحص:

  • اللوحات السبع ظهرت لـAdministrator وحده، ورأى غيره «غير مسموح به»، لأن
    مساحات العمل وُضعت في وحدة لا يقرأ أحد منها مستنداً.
  • حامل «محاسب» أو «مدير الورشة» فتح قائمة الفواتير ثم لم يجد شركة ولا حساباً
    ولا وحدة قياس يختارها: صلاحيات تلك المستندات معلّقة بأدوار ERPNext
    القياسية التي لم يكن المسمّى يحملها (khat_workshop/roles.py).

لكل مسمّى يُنشأ مستخدم مؤقت يحمله وحده، ويُسأل النظام بحسابه: أي لوحات يرى،
وهل يملك كل صلاحية في NEEDS. لا يبقى شيء بعد الفحص: كل ما أُنشئ يُتراجع عنه.

    bench --site <site> execute khat_workshop.access_test.run
"""

import frappe

from khat_workshop import navigation, roles

READ, CREATE, SUBMIT = "read", "create", "submit"

# ما تتطلبه أي معاملة بيع أو شراء من مستندات مساندة: حقول اختيار في نماذجها
SELLING = ["Company", "Currency", "Account", "Cost Center", "Price List", "UOM",
           "Warehouse", "Item", "Item Group", "Sales Taxes and Charges Template"]
BUYING = ["Company", "Currency", "Account", "Cost Center", "Price List", "UOM",
          "Warehouse", "Item", "Item Group"]
WORKSHOP = ["Vehicle Brand", "Vehicle Model", "Work Card Status", "Workshop Technician"]

# المسمّى: {الصلاحية: [المستندات]}
NEEDS = {
    "Workshop Manager": {
        CREATE: ["Work Card", "Customer", "Customer Vehicle", "Quotation", "Sales Invoice",
                 "Payment Entry"],
        SUBMIT: ["Work Card", "Quotation", "Sales Invoice", "Payment Entry"],
        READ: SELLING + WORKSHOP + ["Mode of Payment", "Bin"],
    },
    "موظف استقبال الورشة": {
        CREATE: ["Customer", "Customer Vehicle", "Work Card", "Quotation"],
        READ: SELLING + WORKSHOP,
    },
    "فني ورشة": {
        "write": ["Work Card"],
        READ: ["Customer", "Customer Vehicle", "Item", "Warehouse", "Work Card Status",
               "Workshop Technician", "Vehicle Brand", "Vehicle Model"],
    },
    "محاسب": {
        SUBMIT: ["Sales Invoice", "Purchase Invoice", "Payment Entry", "Journal Entry"],
        CREATE: ["Customer", "Supplier", "Account"],
        READ: SELLING + ["Mode of Payment", "GL Entry", "Bank Account"],
    },
    "كاشير": {
        SUBMIT: ["Sales Invoice", "Payment Entry"],
        READ: SELLING + ["Customer", "Mode of Payment"],
    },
    "Sales Manager": {
        SUBMIT: ["Quotation", "Sales Order"],
        CREATE: ["Customer"],
        READ: SELLING,
    },
    "مندوب مبيعات": {
        CREATE: ["Quotation", "Sales Order", "Customer"],
        READ: SELLING,
    },
    "مسؤول المشتريات": {
        SUBMIT: ["Purchase Order", "Purchase Receipt", "Purchase Invoice", "Material Request"],
        CREATE: ["Supplier"],
        READ: BUYING + ["Purchase Taxes and Charges Template"],
    },
    "مدير المستودع": {
        SUBMIT: ["Stock Entry", "Stock Reconciliation", "Purchase Receipt", "Material Request"],
        CREATE: ["Item", "Warehouse", "Item Group"],
        READ: ["Company", "UOM", "Bin", "Stock Ledger Entry"],
    },
    "مدير النظام": {
        CREATE: ["User", "Work Card", "Sales Invoice", "Purchase Invoice", "Item",
                 "Journal Entry"],
        READ: SELLING + WORKSHOP + ["Workshop Settings", "Website Settings", "Letter Head"],
    },
}

# لوحات يجب أن يراها كل مستخدم أياً كان مسمّاه
ALWAYS_VISIBLE = set(navigation.WORKSPACES)


def _temp_user(role, index):
    email = "kaj-access-%d@example.com" % index
    doc = frappe.get_doc({
        "doctype": "User", "email": email, "first_name": "فحص صلاحيات",
        "enabled": 1, "user_type": "System User", "send_welcome_email": 0,
        "roles": [{"role": role}],
    })
    doc.flags.no_welcome_mail = True
    doc.insert(ignore_permissions=True)
    return email


def _workspaces():
    from frappe.desk.desktop import get_workspaces
    pages = get_workspaces()
    pages = pages.get("pages") if isinstance(pages, dict) else pages
    return {p.get("name") for p in pages or []}


def _check(role, index):
    problems = []
    user = _temp_user(role, index)
    frappe.set_user(user)
    try:
        missing = ALWAYS_VISIBLE - _workspaces()
        if missing:
            problems.append("لا يرى اللوحات: %s" % "، ".join(sorted(missing)))
        for ptype, doctypes in NEEDS.get(role, {}).items():
            for doctype in doctypes:
                if not frappe.db.exists("DocType", doctype):
                    continue
                if not frappe.has_permission(doctype, ptype):
                    problems.append("لا يملك %s على %s" % (ptype, doctype))
    finally:
        frappe.set_user("Administrator")
    return problems


def run():
    failures = {}
    try:
        for index, role in enumerate(roles.JOB_ROLES):
            if not frappe.db.exists("Role", role):
                failures[role] = ["الدور غير موجود"]
                continue
            problems = _check(role, index)
            print("%s  %s" % ("OK  " if not problems else "FAIL", role))
            for p in problems:
                print("        " + p)
            if problems:
                failures[role] = problems
    finally:
        frappe.set_user("Administrator")
        frappe.db.rollback()
        frappe.clear_cache()

    if failures:
        frappe.throw("access_test: %d مسمّى وظيفي ينقصه شيء: %s"
                     % (len(failures), "، ".join(failures)))
    print("ACCESS_TEST all %d job roles OK" % len(roles.JOB_ROLES))
