# -*- coding: utf-8 -*-
"""
Workshop (ورشة الصيانة) — full replica of the Mazoon ERP vehicle-workshop module
built as Custom DocTypes inside ERPNext (stored in DB, survive image updates).
Idempotent: safe to re-run.
"""
import frappe

MODULE = "Workshop"


def _ensure_module():
    if not frappe.db.exists("Module Def", MODULE):
        frappe.get_doc({
            "doctype": "Module Def",
            "module_name": MODULE,
            "custom": 1,
            "app_name": "frappe",
        }).insert(ignore_permissions=True)


def _perms():
    return [
        {"role": "System Manager", "read": 1, "write": 1, "create": 1,
         "delete": 1, "report": 1, "export": 1, "print": 1, "email": 1,
         "share": 1, "submit": 0},
        {"role": "Workshop Manager", "read": 1, "write": 1, "create": 1,
         "delete": 1, "report": 1, "export": 1, "print": 1, "email": 1,
         "share": 1},
    ]


def make_dt(name, fields, autoname=None, naming_rule=None, istable=0,
            issingle=0, title_field=None, search_fields=None, track=1):
    if frappe.db.exists("DocType", name):
        return "exists"
    doc = {
        "doctype": "DocType",
        "name": name,
        "module": MODULE,
        "custom": 1,
        "istable": istable,
        "issingle": issingle,
        "fields": fields,
    }
    if autoname:
        doc["autoname"] = autoname
    if naming_rule:
        doc["naming_rule"] = naming_rule
    if title_field:
        doc["title_field"] = title_field
    if search_fields:
        doc["search_fields"] = search_fields
    if not istable:
        doc["permissions"] = _perms()
        doc["track_changes"] = track
    frappe.get_doc(doc).insert(ignore_permissions=True)
    return "created"


def f(fieldname, label, fieldtype, **kw):
    d = {"fieldname": fieldname, "label": label, "fieldtype": fieldtype}
    d.update(kw)
    return d


def execute():
    _ensure_module()

    # Ensure the Workshop Manager role exists
    if not frappe.db.exists("Role", "Workshop Manager"):
        frappe.get_doc({
            "doctype": "Role", "role_name": "Workshop Manager",
            "desk_access": 1,
        }).insert(ignore_permissions=True)

    log = {}

    # ---------------------------------------------------------------
    # 1. Vehicle Brand — براند المركبة  (already may exist from probe)
    # ---------------------------------------------------------------
    log["Vehicle Brand"] = make_dt(
        "Vehicle Brand",
        [f("brand_name", "اسم البراند", "Data", reqd=1, in_list_view=1, unique=1)],
        autoname="field:brand_name", naming_rule="By fieldname",
    )

    # ---------------------------------------------------------------
    # 2. Vehicle Model — موديل المركبة
    # ---------------------------------------------------------------
    log["Vehicle Model"] = make_dt(
        "Vehicle Model",
        [
            f("brand", "البراند", "Link", options="Vehicle Brand", reqd=1, in_list_view=1),
            f("model_name", "اسم الموديل", "Data", reqd=1, in_list_view=1),
        ],
        autoname="format:{brand}-{model_name}",
    )

    # ---------------------------------------------------------------
    # 3. Workshop Technician — الفني
    # ---------------------------------------------------------------
    log["Workshop Technician"] = make_dt(
        "Workshop Technician",
        [
            f("technician_name", "اسم الفني", "Data", reqd=1, in_list_view=1, unique=1),
            f("phone", "الهاتف", "Data", in_list_view=1),
            f("specialization", "التخصص", "Data", in_list_view=1),
            f("cb1", "", "Column Break"),
            f("commission_rate", "نسبة العمولة %", "Percent"),
            f("is_active", "نشط", "Check", default="1"),
            f("employee", "الموظف (ربط)", "Link", options="Employee"),
        ],
        autoname="field:technician_name", naming_rule="By fieldname",
    )

    # ---------------------------------------------------------------
    # 4. Work Card Status — حالة بطاقة العمل
    # ---------------------------------------------------------------
    log["Work Card Status"] = make_dt(
        "Work Card Status",
        [
            f("status_name", "اسم الحالة", "Data", reqd=1, in_list_view=1, unique=1),
            f("color", "اللون", "Color", in_list_view=1),
            f("is_closed", "حالة إغلاق (منتهية)", "Check", default="0"),
        ],
        autoname="field:status_name", naming_rule="By fieldname",
    )

    # ---------------------------------------------------------------
    # 5. Customer Vehicle — مركبة العميل
    # ---------------------------------------------------------------
    log["Customer Vehicle"] = make_dt(
        "Customer Vehicle",
        [
            f("customer", "العميل", "Link", options="Customer", reqd=1, in_list_view=1),
            f("plate_number", "رقم اللوحة", "Data", reqd=1, in_list_view=1, unique=1),
            f("brand", "البراند", "Link", options="Vehicle Brand", in_list_view=1),
            f("model", "الموديل", "Link", options="Vehicle Model", in_list_view=1),
            f("cb1", "", "Column Break"),
            f("year", "سنة الصنع", "Data"),
            f("color", "اللون", "Data"),
            f("chassis_no", "رقم الشاصي (VIN)", "Data"),
            f("engine_no", "رقم المحرك", "Data"),
            f("mileage", "قراءة العداد", "Int"),
            f("sec1", "ملاحظات", "Section Break"),
            f("notes", "ملاحظات", "Small Text"),
        ],
        autoname="field:plate_number", naming_rule="By fieldname",
        title_field="plate_number",
        search_fields="customer,brand,model",
    )

    # ---------------------------------------------------------------
    # Child tables for Work Card
    # ---------------------------------------------------------------
    log["Work Card Technician"] = make_dt(
        "Work Card Technician",
        [
            f("technician", "الفني", "Link", options="Workshop Technician", reqd=1, in_list_view=1),
            f("task", "المهمة", "Data", in_list_view=1),
            f("commission", "العمولة", "Currency", in_list_view=1),
        ],
        istable=1,
    )

    log["Work Card Service"] = make_dt(
        "Work Card Service",
        [
            f("service", "الخدمة / العمل", "Data", reqd=1, in_list_view=1),
            f("description", "الوصف", "Small Text"),
            f("qty", "الكمية", "Float", default="1", in_list_view=1),
            f("rate", "السعر", "Currency", in_list_view=1),
            f("amount", "الإجمالي", "Currency", in_list_view=1, read_only=1),
        ],
        istable=1,
    )

    log["Work Card Part"] = make_dt(
        "Work Card Part",
        [
            f("item", "قطعة الغيار (صنف)", "Link", options="Item", in_list_view=1),
            f("part_name", "اسم القطعة", "Data", in_list_view=1),
            f("qty", "الكمية", "Float", default="1", in_list_view=1),
            f("rate", "السعر", "Currency", in_list_view=1),
            f("amount", "الإجمالي", "Currency", in_list_view=1, read_only=1),
        ],
        istable=1,
    )

    # ---------------------------------------------------------------
    # 6. Work Card — بطاقة العمل  (core)
    # ---------------------------------------------------------------
    log["Work Card"] = make_dt(
        "Work Card",
        [
            f("naming_series", "التسلسل", "Select", options="WC-.YYYY.-", default="WC-.YYYY.-", reqd=1),
            f("customer", "العميل", "Link", options="Customer", reqd=1, in_list_view=1),
            f("customer_phone", "الهاتف", "Data", in_list_view=1),
            f("vehicle", "المركبة", "Link", options="Customer Vehicle", reqd=1, in_list_view=1),
            f("plate_number", "رقم اللوحة", "Data", fetch_from="vehicle.plate_number", read_only=1, in_list_view=1),
            f("cb1", "", "Column Break"),
            f("brand", "البراند", "Link", options="Vehicle Brand", fetch_from="vehicle.brand", read_only=1),
            f("model", "الموديل", "Link", options="Vehicle Model", fetch_from="vehicle.model", read_only=1),
            f("mileage", "قراءة العداد", "Int"),
            f("entry_date", "تاريخ الدخول", "Datetime", default="Now", in_list_view=1),
            f("expected_delivery", "موعد التسليم المتوقع", "Datetime"),
            f("status", "الحالة", "Link", options="Work Card Status", in_list_view=1),
            f("sec_complaint", "البلاغ والتشخيص", "Section Break"),
            f("complaint", "شكوى العميل / البلاغ", "Small Text"),
            f("cb2", "", "Column Break"),
            f("diagnosis", "التشخيص", "Small Text"),
            f("sec_tech", "الفنيون", "Section Break"),
            f("technicians", "الفنيون", "Table", options="Work Card Technician"),
            f("sec_services", "الأعمال والخدمات", "Section Break"),
            f("services", "الخدمات", "Table", options="Work Card Service"),
            f("sec_parts", "قطع الغيار", "Section Break"),
            f("parts", "قطع الغيار", "Table", options="Work Card Part"),
            f("sec_totals", "الإجماليات", "Section Break"),
            f("services_total", "إجمالي الأعمال", "Currency", read_only=1),
            f("parts_total", "إجمالي القطع", "Currency", read_only=1),
            f("cb3", "", "Column Break"),
            f("discount", "الخصم", "Currency"),
            f("grand_total", "الإجمالي النهائي", "Currency", read_only=1, in_list_view=1),
            f("sec_notes", "ملاحظات", "Section Break"),
            f("notes", "ملاحظات", "Text"),
        ],
        autoname="naming_series:", naming_rule="By \"Naming Series\" field",
        search_fields="customer,plate_number,status",
    )

    # ---------------------------------------------------------------
    # 7. Workshop Quotation — عرض السعر
    # ---------------------------------------------------------------
    log["Workshop Quotation Item"] = make_dt(
        "Workshop Quotation Item",
        [
            f("description", "البيان", "Data", reqd=1, in_list_view=1),
            f("qty", "الكمية", "Float", default="1", in_list_view=1),
            f("rate", "السعر", "Currency", in_list_view=1),
            f("amount", "الإجمالي", "Currency", in_list_view=1, read_only=1),
        ],
        istable=1,
    )
    log["Workshop Quotation"] = make_dt(
        "Workshop Quotation",
        [
            f("naming_series", "التسلسل", "Select", options="WQTN-.YYYY.-", default="WQTN-.YYYY.-", reqd=1),
            f("customer", "العميل", "Link", options="Customer", reqd=1, in_list_view=1),
            f("vehicle", "المركبة", "Link", options="Customer Vehicle", in_list_view=1),
            f("cb1", "", "Column Break"),
            f("date", "التاريخ", "Date", default="Today", in_list_view=1),
            f("valid_till", "صالح حتى", "Date"),
            f("status", "الحالة", "Select", options="مسودة\nمرسل\nمقبول\nمرفوض", default="مسودة", in_list_view=1),
            f("sec1", "البنود", "Section Break"),
            f("items", "البنود", "Table", options="Workshop Quotation Item"),
            f("sec2", "الإجماليات", "Section Break"),
            f("total", "الإجمالي", "Currency", read_only=1),
            f("cb2", "", "Column Break"),
            f("discount", "الخصم", "Currency"),
            f("grand_total", "الإجمالي النهائي", "Currency", read_only=1, in_list_view=1),
        ],
        autoname="naming_series:", naming_rule="By \"Naming Series\" field",
    )

    # ---------------------------------------------------------------
    # 8. Repair Invoice — فاتورة الإصلاح
    # ---------------------------------------------------------------
    log["Repair Invoice Item"] = make_dt(
        "Repair Invoice Item",
        [
            f("description", "البيان", "Data", reqd=1, in_list_view=1),
            f("qty", "الكمية", "Float", default="1", in_list_view=1),
            f("rate", "السعر", "Currency", in_list_view=1),
            f("amount", "الإجمالي", "Currency", in_list_view=1, read_only=1),
        ],
        istable=1,
    )
    log["Repair Invoice"] = make_dt(
        "Repair Invoice",
        [
            f("naming_series", "التسلسل", "Select", options="RINV-.YYYY.-", default="RINV-.YYYY.-", reqd=1),
            f("work_card", "بطاقة العمل", "Link", options="Work Card", in_list_view=1),
            f("customer", "العميل", "Link", options="Customer", reqd=1, in_list_view=1),
            f("vehicle", "المركبة", "Link", options="Customer Vehicle", in_list_view=1),
            f("cb1", "", "Column Break"),
            f("date", "التاريخ", "Date", default="Today", in_list_view=1),
            f("status", "الحالة", "Select", options="غير مدفوعة\nمدفوعة جزئياً\nمدفوعة", default="غير مدفوعة", in_list_view=1),
            f("sec1", "البنود", "Section Break"),
            f("items", "البنود", "Table", options="Repair Invoice Item"),
            f("sec2", "الإجماليات", "Section Break"),
            f("total", "الإجمالي", "Currency", read_only=1),
            f("discount", "الخصم", "Currency"),
            f("grand_total", "الإجمالي النهائي", "Currency", read_only=1, in_list_view=1),
            f("cb2", "", "Column Break"),
            f("paid_amount", "المدفوع", "Currency", read_only=1),
            f("outstanding", "المتبقي", "Currency", read_only=1, in_list_view=1),
        ],
        autoname="naming_series:", naming_rule="By \"Naming Series\" field",
    )

    # ---------------------------------------------------------------
    # 9. Workshop Payment — الدفعة
    # ---------------------------------------------------------------
    log["Workshop Payment"] = make_dt(
        "Workshop Payment",
        [
            f("naming_series", "التسلسل", "Select", options="WPAY-.YYYY.-", default="WPAY-.YYYY.-", reqd=1),
            f("invoice", "فاتورة الإصلاح", "Link", options="Repair Invoice", reqd=1, in_list_view=1),
            f("customer", "العميل", "Link", options="Customer", fetch_from="invoice.customer", read_only=1, in_list_view=1),
            f("cb1", "", "Column Break"),
            f("date", "التاريخ", "Date", default="Today", in_list_view=1),
            f("amount", "المبلغ", "Currency", reqd=1, in_list_view=1),
            f("mode_of_payment", "طريقة الدفع", "Link", options="Mode of Payment", in_list_view=1),
            f("reference", "مرجع", "Data"),
        ],
        autoname="naming_series:", naming_rule="By \"Naming Series\" field",
    )

    # ---------------------------------------------------------------
    # 10. Service Package — الباقة
    # ---------------------------------------------------------------
    log["Service Package Item"] = make_dt(
        "Service Package Item",
        [
            f("service", "الخدمة", "Data", reqd=1, in_list_view=1),
            f("qty", "الكمية", "Float", default="1", in_list_view=1),
            f("rate", "السعر", "Currency", in_list_view=1),
        ],
        istable=1,
    )
    log["Service Package"] = make_dt(
        "Service Package",
        [
            f("package_name", "اسم الباقة", "Data", reqd=1, in_list_view=1, unique=1),
            f("price", "السعر", "Currency", in_list_view=1),
            f("is_active", "نشطة", "Check", default="1"),
            f("description", "الوصف", "Small Text"),
            f("sec1", "الخدمات المشمولة", "Section Break"),
            f("items", "الخدمات", "Table", options="Service Package Item"),
        ],
        autoname="field:package_name", naming_rule="By fieldname",
    )

    # ---------------------------------------------------------------
    # 11. Maintenance Reminder — تذكرة الصيانة
    # ---------------------------------------------------------------
    log["Maintenance Reminder"] = make_dt(
        "Maintenance Reminder",
        [
            f("customer", "العميل", "Link", options="Customer", reqd=1, in_list_view=1),
            f("vehicle", "المركبة", "Link", options="Customer Vehicle", reqd=1, in_list_view=1),
            f("service_type", "نوع الصيانة", "Data", in_list_view=1),
            f("cb1", "", "Column Break"),
            f("due_date", "تاريخ الاستحقاق", "Date", in_list_view=1),
            f("due_mileage", "العداد المستحق", "Int"),
            f("status", "الحالة", "Select", options="بانتظار\nتم\nملغاة", default="بانتظار", in_list_view=1),
            f("sec1", "ملاحظات", "Section Break"),
            f("notes", "ملاحظات", "Small Text"),
        ],
        autoname="hash",
    )

    # ---------------------------------------------------------------
    # 12. Commission Log — سجل صرف العمولات
    # ---------------------------------------------------------------
    log["Commission Log"] = make_dt(
        "Commission Log",
        [
            f("technician", "الفني", "Link", options="Workshop Technician", reqd=1, in_list_view=1),
            f("work_card", "بطاقة العمل", "Link", options="Work Card", in_list_view=1),
            f("amount", "المبلغ", "Currency", reqd=1, in_list_view=1),
            f("cb1", "", "Column Break"),
            f("date", "التاريخ", "Date", default="Today", in_list_view=1),
            f("status", "الحالة", "Select", options="بانتظار الصرف\nتم الصرف", default="بانتظار الصرف", in_list_view=1),
            f("notes", "ملاحظات", "Data"),
        ],
        autoname="hash",
    )

    # ---------------------------------------------------------------
    # 13. Workshop Settings — إعدادات الورشة (Single)
    # ---------------------------------------------------------------
    log["Workshop Settings"] = make_dt(
        "Workshop Settings",
        [
            f("workshop_name", "اسم الورشة", "Data"),
            f("phone", "الهاتف", "Data"),
            f("tax_number", "الرقم الضريبي", "Data"),
            f("cb1", "", "Column Break"),
            f("default_status", "الحالة الافتراضية للبطاقة", "Link", options="Work Card Status"),
            f("logo", "الشعار", "Attach Image"),
            f("sec1", "العنوان", "Section Break"),
            f("address", "العنوان", "Small Text"),
            f("sec2", "شروط الفاتورة", "Section Break"),
            f("invoice_terms", "شروط وملاحظات الفاتورة", "Text"),
        ],
        issingle=1,
    )

    frappe.db.commit()
    frappe.clear_cache()

    # ---------------------------------------------------------------
    # Seed default Work Card Statuses
    # ---------------------------------------------------------------
    statuses = [
        ("بانتظار الفحص", "#ffa00a", 0),
        ("قيد الإصلاح", "#318ad8", 0),
        ("بانتظار قطع الغيار", "#cb2929", 0),
        ("بانتظار موافقة العميل", "#8e44ad", 0),
        ("جاهزة للتسليم", "#1f9d55", 0),
        ("تم التسليم", "#98d85b", 1),
        ("ملغاة", "#7c7c7c", 1),
    ]
    for nm, color, closed in statuses:
        if not frappe.db.exists("Work Card Status", nm):
            frappe.get_doc({
                "doctype": "Work Card Status", "status_name": nm,
                "color": color, "is_closed": closed,
            }).insert(ignore_permissions=True)

    frappe.db.commit()
    print("WORKSHOP_SETUP_DONE " + str(log))
