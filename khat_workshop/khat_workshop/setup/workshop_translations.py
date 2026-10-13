# -*- coding: utf-8 -*-
"""Translations, both directions.

PAIRS: English renderings of the Arabic labels this app authors (custom
doctype fields, statuses, reports) — applied when a user's language is English.

Arabic renderings of English sources — document names, list and form chrome,
statuses — live in khat_workshop/glossary.py, the single Arabic vocabulary for
the system, and are applied from there.
"""
import frappe

from khat_workshop import glossary

# (arabic, english)
PAIRS = [
    # Role-name translations were removed from here: workshop_roles now owns
    # them, aligned to Mazoon (Super Admin, Sales Manager, Workshop Manager,
    # Admin, Employee...). This step runs AFTER workshop_roles, so keeping the
    # old pairs here silently overwrote the correct labels with stale ones
    # (Garage Manager, Head of Sales, Supervisor, Staff, System Administrator) —
    # caught by post-deploy verification when "Super Admin" came back empty.

    # --- Module / Workspace ---
    ("الرئيسية", "Home"),
    ("بحث سريع برقم الجوال", "Quick Search by Phone Number"),
    ("أدخل رقم جوال العميل...", "Enter customer's phone number..."),
    ("بحث سريع بالجوال أو رقم اللوحة", "Quick Search by Phone or Plate Number"),
    ("أدخل رقم الجوال أو رقم لوحة المركبة...", "Enter phone number or vehicle plate number..."),
    ("لا يوجد عميل أو مركبة بهذا الرقم", "No customer or vehicle found with this number"),
    ("بحث", "Search"),
    ("لا يوجد عميل بهذا الرقم", "No customer found with this number"),
    ("فتح ملف العميل", "Open Customer Profile"),
    ("إجمالي الفواتير", "Total Invoices"),
    ("الفواتير", "Invoices"),
    ("لا توجد بيانات إضافية لهذا العميل بعد", "No additional data for this customer yet"),
    ("ورشة الصيانة", "Workshop"),
    ("إدارة ورشة الصيانة", "Workshop Management"),
    ("الإحصائيات", "Statistics"),
    ("الإجراءات السريعة", "Quick Actions"),
    ("أحدث بطاقات العمل", "Latest Work Cards"),
    ("القائمة", "Menu"),
    ("عرض الكل", "View All"),

    # --- Tiles / menu groups ---
    ("إضافة عميل", "Add Customer"),
    ("العملاء", "Customers"),
    ("إضافة مركبة", "Add Vehicle"),
    ("مركبات العملاء", "Customer Vehicles"),
    ("براندات المركبات", "Vehicle Brands"),
    ("موديلات المركبات", "Vehicle Models"),
    ("بطاقات العمل", "Work Cards"),
    ("حالات بطاقة العمل", "Work Card Statuses"),
    ("عروض الأسعار", "Quotations"),
    ("فواتير الإصلاح", "Repair Invoices"),
    ("الدفعات", "Payments"),
    ("الباقات", "Packages"),
    ("الفنيون", "Technicians"),
    ("إعدادات الورشة", "Workshop Settings"),
    ("التقارير", "Reports"),
    ("تقرير الفنيين", "Technicians Report"),
    ("سجل صرف العمولات", "Commission Log"),
    ("تذكرات الصيانة", "Maintenance Reminders"),
    ("العملاء والمركبات", "Customers & Vehicles"),
    ("المبيعات والمالية", "Sales & Finance"),
    ("المتابعة والإعدادات", "Follow-up & Settings"),
    ("تقرير العمولات", "Commissions Report"),
    ("تقرير الإيرادات", "Revenue Report"),
    ("تقرير بطاقات العمل", "Work Cards Report"),

    # --- Search boxes ---
    ("بحث العملاء", "Search Customers"),
    ("بحث المركبات", "Search Vehicles"),
    ("بحث الفواتير", "Search Invoices"),
    ("ابحث بالاسم أو رقم الهاتف...", "Search by name or phone..."),
    ("ابحث برقم اللوحة أو اسم/هاتف العميل...", "Search by plate number or customer name/phone..."),
    ("ابحث برقم الفاتورة أو اسم/هاتف العميل...", "Search by invoice number or customer name/phone..."),
    ("رقم البطاقة", "Card No."),
    ("العميل", "Customer"),
    ("الهاتف", "Phone"),
    ("رقم اللوحة", "Plate Number"),
    ("الماركة / الموديل", "Brand / Model"),
    ("تاريخ الدخول", "Entry Date"),
    ("الحالة", "Status"),
    ("لا توجد سجلات", "No records found"),
    ("جاري التحميل...", "Loading..."),
    ("تعذّر التحميل", "Failed to load"),

    # --- Home landing page tiles ---
    ("لوحة التحكم", "Dashboard"),
    ("ورشة صيانة السيارات", "Vehicle Repair Workshop"),
    ("المبيعات", "Sales"),
    ("المشتريات", "Purchases"),
    ("المخزون", "Stock"),
    ("المحاسبة", "Accounting"),
    ("آخر التحديثات", "Latest Updates"),
    ("الإعدادات العامة", "General Settings"),
    ("لا توجد نتائج", "No results found"),
    ("أهلاً", "Hi"),
    ("مرحباً بعودتك إلى نظام خط الجزيرة", "Welcome back to the Khat Al Jazeera system"),
    ("الوحدات الرئيسية", "Main Modules"),
    ("بطاقات العمل والفنيون والصيانة", "Work cards, technicians, and maintenance"),
    ("الفواتير والعملاء ونقاط البيع", "Invoices, customers, and point of sale"),
    ("الموردون وأوامر الشراء", "Suppliers and purchase orders"),
    ("المنتجات والمستودعات والجرد", "Items, warehouses, and stock reconciliation"),
    ("القيود والتقارير المالية", "Journal entries and financial reports"),
    ("المستخدمون والأدوار والإعدادات", "Users, roles, and settings"),
    ("الإشعارات وآخر المستجدات", "Notifications and recent updates"),

    # --- Statistic card labels ---
    ("المركبات", "Vehicles"),
    ("إجمالي المدفوعات", "Total Payments"),
    ("المتبقيات", "Outstanding"),

    # --- Field labels (shared across doctypes) ---
    ("اسم البراند", "Brand Name"),
    ("البراند", "Brand"),
    ("اسم الموديل", "Model Name"),
    ("اسم الفني", "Technician Name"),
    ("التخصص", "Specialization"),
    ("نسبة العمولة %", "Commission Rate %"),
    ("نشط", "Active"),
    ("الموظف (ربط)", "Employee (Link)"),
    ("اسم الحالة", "Status Name"),
    ("اللون", "Color"),
    ("حالة إغلاق (منتهية)", "Closed Status"),
    ("المركبة", "Vehicle"),
    ("الموديل", "Model"),
    ("سنة الصنع", "Year"),
    ("رقم الشاصي (VIN)", "Chassis No. (VIN)"),
    ("رقم المحرك", "Engine No."),
    ("قراءة العداد", "Mileage"),
    ("ملاحظات", "Notes"),
    ("المهمة", "Task"),
    ("العمولة", "Commission"),
    ("الخدمة / العمل", "Service / Work"),
    ("الوصف", "Description"),
    ("الكمية", "Qty"),
    ("السعر", "Rate"),
    ("الإجمالي", "Total"),
    ("قطعة الغيار (صنف)", "Spare Part (Item)"),
    ("اسم القطعة", "Part Name"),
    ("التسلسل", "Series"),
    ("هاتف العميل", "Customer Phone"),
    ("موعد التسليم المتوقع", "Expected Delivery"),
    ("البلاغ والتشخيص", "Complaint & Diagnosis"),
    ("شكوى العميل / البلاغ", "Customer Complaint"),
    ("التشخيص", "Diagnosis"),
    ("الأعمال والخدمات", "Work & Services"),
    ("الخدمات", "Services"),
    ("قطع الغيار", "Spare Parts"),
    ("الإجماليات", "Totals"),
    ("إجمالي الأعمال", "Services Total"),
    ("إجمالي القطع", "Parts Total"),
    ("الخصم", "Discount"),
    ("الإجمالي النهائي", "Grand Total"),
    ("البيان", "Item / Description"),
    ("صالح حتى", "Valid Till"),
    ("مسودة", "Draft"),
    ("مرسل", "Sent"),
    ("مقبول", "Accepted"),
    ("مرفوض", "Rejected"),
    ("البنود", "Items"),
    ("التاريخ", "Date"),
    ("غير مدفوعة", "Unpaid"),
    ("مدفوعة جزئياً", "Partially Paid"),
    ("مدفوعة", "Paid"),
    ("المدفوع", "Paid Amount"),
    ("المتبقي", "Outstanding"),
    ("فاتورة الإصلاح", "Repair Invoice"),
    ("طريقة الدفع", "Mode of Payment"),
    ("مرجع", "Reference"),
    ("اسم الباقة", "Package Name"),
    ("نشطة", "Active"),
    ("الخدمات المشمولة", "Included Services"),
    ("نوع الصيانة", "Service Type"),
    ("تاريخ الاستحقاق", "Due Date"),
    ("العداد المستحق", "Due Mileage"),
    ("بانتظار", "Pending"),
    ("تم", "Done"),
    ("ملغاة", "Cancelled"),
    ("عدد البطاقات", "Card Count"),
    ("بانتظار الصرف", "Pending Payout"),
    ("تم الصرف", "Paid Out"),
    ("اسم الورشة", "Workshop Name"),
    ("الرقم الضريبي", "Tax Number"),
    ("الحالة الافتراضية للبطاقة", "Default Card Status"),
    ("الشعار", "Logo"),
    ("العنوان", "Address"),
    ("شروط الفاتورة", "Invoice Terms"),
    ("شروط وملاحظات الفاتورة", "Invoice Terms & Notes"),
    ("بطاقة عمل", "Work Card"),

    # --- Work Card Status seed values ---
    ("بانتظار الفحص", "Awaiting Inspection"),
    ("قيد الإصلاح", "Under Repair"),
    ("بانتظار قطع الغيار", "Awaiting Parts"),
    ("بانتظار موافقة العميل", "Awaiting Customer Approval"),
    ("جاهزة للتسليم", "Ready for Delivery"),
    ("تم التسليم", "Delivered"),

    # --- الصفحة الرئيسية والشريط الجانبي ---
    # تسميات بطاقات «نظرة سريعة» حُذفت مع القسم نفسه. ما بقي هنا مستخدَم
    # فعلاً: عنوان قسم البطاقات، وتحية الصفحة، وتلميحات شريط النشاط.
    ("الوحدات الرئيسية", "Main Modules"),
    ("مدير النظام", "System Administrator"),
    ("إظهار المحتويات", "Show contents"),
    # شريط النشاط واللوح الفرعي
    ("إغلاق", "Close"),
    ("جارٍ التحميل", "Loading"),
    ("لا توجد عناصر", "No items"),

    # --- Vehicle intake (body condition) ---
    # Added 2026-10-06 after an audit found 53 of the 146 Arabic labels on the
    # custom doctypes (36%) had no English rendering at all. Switching a user to
    # English left those fields in Arabic, so the form came out half-translated
    # — which reads as unfinished on a system sold as bilingual.
    ("حالة المركبة عند الاستلام", "Vehicle Condition on Intake"),
    ("مستوى الوقود", "Fuel Level"),
    ("لا توجد أضرار ظاهرة", "No Visible Damage"),
    ("الأضرار المسجّلة", "Recorded Damage"),
    ("صور الاستلام", "Intake Photos"),
    ("ملاحظات الاستلام", "Intake Notes"),
    ("توقيع العميل بالاستلام", "Customer Signature on Intake"),
    ("المنطقة", "Zone"),
    ("الصورة", "Image"),
    ("صورة", "Photo"),

    # --- Mechanical inspection ---
    ("الفحص الفني للمركبة", "Vehicle Technical Inspection"),
    ("بنود الفحص", "Inspection Items"),
    ("نتيجة الفحص", "Inspection Result"),
    ("ملاحظات الفحص", "Inspection Notes"),
    ("عداد الكيلومترات", "Odometer (km)"),
    ("المجموعة", "Group"),
    ("البند", "Item"),
    ("النتيجة", "Result"),
    ("ملاحظة", "Note"),
    ("جيد", "Good"),
    ("يحتاج متابعة", "Needs Monitoring"),
    ("يحتاج استبدال", "Needs Replacement"),
    ("يحتاج إصلاح", "Needs Repair"),

    # --- Costing & profitability ---
    ("التكلفة والربحية", "Cost & Profitability"),
    ("تكلفة العمالة", "Labour Cost"),
    ("تكلفة العمل", "Job Cost"),
    ("تكلفة القطع (فعلية)", "Parts Cost (Actual)"),
    ("إجمالي التكلفة", "Total Cost"),
    ("الربح الإجمالي", "Gross Profit"),
    ("هامش الربح %", "Profit Margin %"),
    ("ساعات العمل", "Work Hours"),
    ("إجمالي ساعات العمل", "Total Work Hours"),
    ("تكلفة الساعة", "Hourly Rate"),
    ("إجمالي العمولات", "Total Commissions"),

    # --- Packages ---
    ("اسم الباقة (عربي)", "Package Name (Arabic)"),
    ("اسم الباقة (إنجليزي)", "Package Name (English)"),
    ("مفعّلة", "Enabled"),
    ("المجموع الفرعي", "Subtotal"),
    ("نسبة الخصم %", "Discount %"),
    ("قيمة الخصم", "Discount Amount"),
    ("الصنف / الخدمة", "Item / Service"),
    ("الاسم", "Name"),
    ("خط الخدمة", "Service Line"),

    # --- Misc fields ---
    ("اسم الدور", "Role Name"),
    ("رمز الدولة (لواتساب)", "Country Code (for WhatsApp)"),
    ("الرابط العام للنظام", "System Public URL"),
    ("المستودع (لصرف القطع)", "Warehouse (for Parts Issue)"),
    ("حركة المخزون المرتبطة", "Linked Stock Entry"),
    ("جوال العميل", "Customer Mobile"),
    ("الفني", "Technician"),
    ("بطاقة العمل", "Work Card"),
    ("المبلغ", "Amount"),
    ("تاريخ آخر صيانة", "Last Service Date"),
    ("تاريخ الصيانة القادمة", "Next Service Date"),
]

def _apply(pairs, language):
    """Arabic source -> English rendering (no context: these are our own labels)."""
    created, updated = 0, 0
    for src, tgt in pairs:
        c, u = _upsert(src, tgt, language, None)
        created += c
        updated += u
    return created, updated


def _upsert(source, target, language, context):
    """One Translation row per (source, language, context).

    The lookup used to ignore context, so a plain "Add {0}" translation was
    written while the list button — which the framework translates with the
    context "Primary action in list view" — kept the framework's own wording.
    Rows left over from earlier runs with the same key are folded into one.

    The source is compared in Python, not by the database: the column's
    collation ignores case, so "Categorize by" matched the row for
    "Categorize By" and never got a row of its own — while the framework
    looks translations up by the exact string.
    """
    rows = [r for r in frappe.get_all(
        "Translation", filters={"source_text": source, "language": language},
        fields=["name", "source_text", "translated_text", "context"])
        if r.source_text == source and (r.context or "") == (context or "")]
    if not rows:
        frappe.get_doc({
            "doctype": "Translation", "language": language, "source_text": source,
            "translated_text": target, "context": context or None,
        }).insert(ignore_permissions=True)
        return 1, 0
    updated = 0
    if rows[0].translated_text != target:
        frappe.db.set_value("Translation", rows[0].name, "translated_text", target,
                            update_modified=False)
        updated = 1
    for extra in rows[1:]:
        frappe.delete_doc("Translation", extra.name, force=1, ignore_permissions=True)
    return 0, updated


def execute():
    en_created, en_updated = _apply(PAIRS, "en")

    # English source -> Arabic: the whole glossary (khat_workshop/glossary.py).
    ar_created = ar_updated = 0
    for source, arabic, context in glossary.entries():
        c, u = _upsert(source, arabic, "ar", context)
        ar_created += c
        ar_updated += u

    frappe.db.commit()
    frappe.clear_cache()
    print("TRANSLATIONS_DONE en_created=%d en_updated=%d ar_created=%d ar_updated=%d glossary=%d"
          % (en_created, en_updated, ar_created, ar_updated, len(glossary.entries())))
