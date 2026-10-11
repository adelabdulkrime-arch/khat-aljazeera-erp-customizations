# -*- coding: utf-8 -*-
"""English translations for every Arabic label used by the Workshop module:
DocType/field labels, Workspace tiles/menu/cards, Work Card Statuses, Reports.
Frappe auto-applies these when a user's Language = English (My Settings)."""
import frappe

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

    # --- بطاقات «نظرة سريعة» على الصفحة الرئيسية ---
    # خمس من ست تسميات لم يكن لها مقابل إنجليزي، بينما «جاهزة للتسليم» لها
    # ترجمة لأنها حالة بطاقة عمل. والنتيجة أن القسم كان يظهر مختلطاً: بطاقة
    # واحدة بالإنجليزية وخمس بالعربية في الوضعين معاً — رُصد في الواجهة.
    # تسمية البطاقة هنا متميّزة عن اسم الحالة عمداً («جاهزة» لا «جاهزة
    # للتسليم») حتى لا يرث العنصران ترجمة واحدة.
    ("بطاقات مفتوحة", "Open Cards"),
    ("بانتظار قطع", "Awaiting Parts"),
    ("جاهزة", "Ready"),
    ("دخلت اليوم", "In Today"),
    ("فواتير غير مسدّدة", "Unpaid Invoices"),
    ("إيراد اليوم", "Today's Revenue"),
    ("بطاقات متعثّرة", "Stalled Cards"),
    ("مخزون منخفض", "Low Stock"),
    ("نظرة سريعة", "Quick Glance"),
    ("الوحدات الرئيسية", "Main Modules"),
    ("مدير النظام", "System Administrator"),
    ("إظهار المحتويات", "Show contents"),

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

# Frappe core UI strings that ship WITHOUT a built-in Arabic translation
# (site language is "ar" by default, but these still render in English).
# Direction here is reversed: English source -> Arabic target.
AR_FIXES = [
    # --- Workspace names (2026-10-06) ---
    # PAIRS registers these Arabic->English, which translates the desk when a
    # user picks English. But the workspaces themselves are *named* in English
    # by ERPNext, so on the Arabic desk — the default — the sidebar read
    # "Sales Dashboard", "Workshop", "Payroll". The reverse direction was never
    # registered, so the Arabic system showed an English sidebar.
    ("Workshop", "الورشة"),
    ("Sales Dashboard", "لوحة المبيعات"),
    ("Purchasing Dashboard", "لوحة المشتريات"),
    ("Inventory Dashboard", "لوحة المخزون"),
    ("Accounting Dashboard", "لوحة المحاسبة"),
    ("Financial Reports", "التقارير المالية"),
    ("Home", "الرئيسية"),
    # HR workspaces ship with hrms and stay visible to a workshop that uses it.
    ("Payroll", "الرواتب"),
    ("Leaves", "الإجازات"),
    ("Expenses", "المصروفات"),
    ("Performance", "الأداء"),
    ("Tenure", "الخدمة الوظيفية"),
    ("Shift & Attendance", "الورديات والحضور"),
    ("Tax & Benefits", "الضرائب والمزايا"),

    # --- Login page (2026-10-06) ---
    # The login screen is the first thing anyone sees, and these four strings
    # stayed English on an Arabic site — caught by screenshotting the rendered
    # page rather than trusting the language setting.
    ("Sign In", "تسجيل الدخول"),
    ("Welcome! Please sign in to continue.", "أهلاً بك! سجّل الدخول للمتابعة."),
    ("Email or Username", "البريد الإلكتروني أو اسم المستخدم"),
    ("Forgot password?", "نسيت كلمة السر؟"),
    ("Login with Email Link", "الدخول عبر رابط البريد"),
    ("Continue", "متابعة"),
    ("Password", "كلمة السر"),
    ("Back to Login", "العودة لتسجيل الدخول"),
    ("Send Password Reset Email", "إرسال رابط إعادة التعيين"),

    ("ID", "المعرّف"),
    ("Status", "الحالة"),
    ("Add User", "إضافة مستخدم"),
    ("Add {0}", "إضافة {0}"),
    ("Saved Filters", "المرشحات المحفوظة"),
    ("List View", "عرض القائمة"),
    ("Created On", "تاريخ الإنشاء"),
    ("Filters", "عوامل التصفية"),
    ("Active", "نشط"),
    ("Disabled", "معطّل"),
    ("User Type", "نوع المستخدم"),

    # --- User form fields (Add/Edit User) — match Mazoon's exact labels ---
    ("Full Name", "الاسم"),
    ("Email", "البريد الإلكتروني"),
    ("Set New Password", "كلمة المرور"),
    ("Roles Assigned", "الأدوار"),
    ("Enabled", "حالة الحساب"),
    ("First Name", "الاسم الأول"),
    ("Last Name", "اسم العائلة"),
    ("Send Welcome Email", "إرسال بريد ترحيبي"),
    ("New User", "إضافة مستخدم"),

    # --- Workspace breadcrumb title (raw English label, opposite direction
    # of the "الرئيسية"->"Home" PAIRS entry used for English mode) ---
    ("Home", "الرئيسية"),

    # --- Empty list-view state (list_view.js) — appears on EVERY empty list ---
    ("You haven't created a {0} yet", "لم تقم بإنشاء {0} حتى الآن"),
    ("No {0} found with matching filters. Clear filters to see all {0}.",
     "لم يتم العثور على {0} مطابقة للمرشحات. امسح المرشحات لرؤية جميع {0}."),
    ("Create your first {0}", "أنشئ أول {0}"),
    ("Create a new {0}", "أنشئ {0} جديد"),
    ("Create New", "إنشاء جديد"),
    ("Need Help?", "بحاجة إلى مساعدة؟"),

    # --- Common document form tab labels (Sales/Purchase Invoice etc.) ---
    ("Address & Contact", "معلومات الاتصال والعنوان"),
    ("Payments", "المدفوعات"),
    ("More Info", "معلومات إضافية"),
    ("Terms", "الشروط"),
    ("Connections", "الارتباطات"),

    # --- Common grid/table column headers ---
    ("Warehouse", "المخزن"),
    ("No.", "الرقم"),
    ("Qty", "الكمية"),
    ("Rate", "السعر"),
    ("Amount", "المبلغ"),
    ("Item", "الصنف"),
    ("Item Code", "رمز الصنف"),
    ("Item Name", "اسم الصنف"),
    ("UOM", "وحدة القياس"),

    # --- Core DocType display names (search results, breadcrumbs, list titles) ---
    # Uses standard professional Arabic accounting terminology, not literal calques.
    ("Accounting Period", "الفترة المحاسبية"),
    ("Journal Entry", "قيد اليومية"),
    ("Payment Entry", "سند الدفع"),
    ("Account", "حساب"),
    ("Accounts Receivable", "الذمم المدينة"),
    ("Accounts Payable", "الذمم الدائنة"),
    ("Sales Invoice", "فاتورة مبيعات"),
    ("Purchase Invoice", "فاتورة مشتريات"),
    ("Purchase Order", "أمر شراء"),
    ("Sales Order", "أمر بيع"),
    ("Quotation", "عرض سعر"),
    ("Customer", "عميل"),
    ("Supplier", "مورد"),
    ("Stock Entry", "حركة مخزون"),
    ("Delivery Note", "إشعار تسليم"),
    ("Purchase Receipt", "إشعار استلام"),
    ("Material Request", "طلب مواد"),
    ("Company", "شركة"),
    ("Chart of Accounts", "دليل الحسابات"),
    ("Cost Center", "مركز التكلفة"),
    ("Fiscal Year", "السنة المالية"),
    ("Mode of Payment", "طريقة الدفع"),
    ("Price List", "قائمة الأسعار"),
    ("Bank Account", "حساب بنكي"),
    ("General Ledger", "دفتر الأستاذ العام"),
    ("Trial Balance", "ميزان المراجعة"),
    ("Profit and Loss Statement", "قائمة الدخل"),
    ("Balance Sheet", "قائمة المركز المالي"),

    # --- Login page (frappe/www/login.html) — no shipped Arabic translation,
    # left in English which produced a jarring bidi-mixed "خط الجزيرة Login to" ---
    ("Login to {0}", "تسجيل الدخول إلى {0}"),
    ("Forgot Password?", "هل نسيت كلمة المرور؟"),
    ("Login with Email Link", "تسجيل الدخول عبر رابط البريد الإلكتروني"),
    ("Or login with", "أو سجّل الدخول عبر"),
    ("Remember Me", "تذكرني"),
]


def _apply(pairs, language):
    created, updated = 0, 0
    for src, tgt in pairs:
        existing = frappe.db.get_value(
            "Translation", {"source_text": src, "language": language}, "name")
        if existing:
            doc = frappe.get_doc("Translation", existing)
            if doc.translated_text != tgt:
                doc.translated_text = tgt
                doc.save(ignore_permissions=True)
                updated += 1
        else:
            frappe.get_doc({
                "doctype": "Translation", "language": language,
                "source_text": src, "translated_text": tgt,
            }).insert(ignore_permissions=True)
            created += 1
    return created, updated


def execute():
    en_created, en_updated = _apply(PAIRS, "en")
    ar_created, ar_updated = _apply(AR_FIXES, "ar")

    frappe.db.commit()
    frappe.clear_cache()
    print("TRANSLATIONS_DONE en_created=%d en_updated=%d ar_created=%d ar_updated=%d"
          % (en_created, en_updated, ar_created, ar_updated))
