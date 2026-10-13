# -*- coding: utf-8 -*-
"""أعمدة شاشات القوائم. المصدر الوحيد.

قائمة Frappe القياسية تعرض الأعمدة المعلَّمة «في القائمة» في تعريف المستند
بالترتيب الذي وُضعت به، ثم عمود «المعرّف»، ثم وقت آخر تعديل وعدد التعليقات
وقلب الإعجاب. لمستخدم ورشة هذا خليط: قائمة المستخدمين مثلاً عرضت نوع
المستخدم والمعرّف، ولم تعرض الأدوار ولا تاريخ الإنشاء.

هنا يُكتب لكل قائمة ما يحتاج المستخدم أن يراه فيها، بالترتيب. يُرسَل مع
بيانات الإقلاع ويطبّقه public/js/kaj_list.js. قائمة غير مذكورة تُعرض
بأعمدتها القياسية (بلا عمود المعرّف، وبعمود الإجراءات).

لكل قائمة:
  columns   أسماء الحقول بالترتيب. "name" = رقم المستند، "creation" = تاريخ
            الإنشاء، و"@roles" عمود محسوب (أدوار المستخدم).
  subject   حقل العمود الأول إن لم يكن عنوان المستند مناسباً — للمستندات
            التي اسمها رمز عشوائي (سجل العمولات، تذكيرات الصيانة).
  status    False لإخفاء عمود الحالة القياسي، أو نصّ لتسميته.
  exclude   صفوف لا تُعرض أبداً، بصيغة مرشّحات.
  filters   خانات البحث السريع فوق القائمة: الحقول التي يبحث بها المستخدم
            فعلاً. تُطبَّق في setup/workshop_lists (خاصية in_standard_filter).
            خانة «الرقم» تظهر تلقائياً حيث "name" ضمن الأعمدة.
"""

from khat_workshop import roles

LISTS = {
    # ── الإعدادات العامة ──
    "User": {
        "filters": ["full_name"],
        "columns": ["email", "@roles", "creation"],
        # Guest حساب داخلي يمثّل الزائر غير المسجَّل، لا مستخدماً يُدار
        "exclude": [["User", "name", "!=", "Guest"]],
    },
    "Role": {
        "filters": [],
        "columns": ["desk_access"],
        # المسمّيات الوظيفية وحدها؛ الأدوار القياسية الستون التي تحملها تفصيل
        # داخلي (khat_workshop/roles.py)
        "exclude": [["Role", "name", "in", roles.JOB_ROLES]],
    },
    "Letter Head": {
        "filters": [],
        "columns": ["is_default"]},
    "Activity Log": {
        "filters": [],
        "columns": ["full_name", "creation"]},

    # ── الورشة ──
    "Customer": {
        "filters": ["customer_name", "mobile_no"],
        "columns": ["mobile_no", "customer_type", "creation"]},
    "Customer Vehicle": {
        "filters": ["plate_number", "customer", "brand"],
        # اسم الموديل يحمل الماركة («تويوتا-كامري»)، فلا عمود لها
        "columns": ["customer", "model", "year", "mileage"]},
    "Vehicle Model": {
        "filters": ["brand"],
        "columns": ["brand", "model_name"]},
    "Work Card": {
        "filters": ["customer", "plate_number", "status"],
        "columns": ["customer", "plate_number", "entry_date", "status", "grand_total"],
        # «الحالة» هنا حالة العمل (بانتظار الفحص، قيد الإصلاح…) بلونها. عمود
        # الإطار للاعتماد (مسودة/معتمدة) يُخفى: عمودان باسم «الحالة» يربكان،
        # والاعتماد يظهر من أيقونة الصف — قلم للمسودة، عين للمعتمدة.
        "status": False,
    },
    "Work Card Status": {
        "filters": [],
        "columns": ["color", "is_closed"]},
    "Workshop Technician": {
        "filters": ["technician_name"],
        "columns": ["phone", "specialization", "commission_rate", "is_active"]},
    "Commission Log": {
        "filters": ["technician", "status"],
        "subject": "technician",
        "columns": ["work_card", "amount", "date", "status"], "status": False},
    "Maintenance Reminder": {
        "filters": ["customer", "status"],
        "subject": "customer",
        "columns": ["vehicle", "service_type", "due_date", "status"], "status": False},
    "Workshop Package": {
        "filters": ["package_name"],
        "columns": ["package_name_en", "is_active", "total"]},

    # ── المبيعات ──
    "Quotation": {
        "filters": ["status"],
        "columns": ["name", "transaction_date", "grand_total"]},
    "Sales Order": {
        "filters": ["status"],
        "columns": ["name", "transaction_date", "delivery_date", "grand_total"]},
    "Delivery Note": {
        "filters": ["status"],
        "columns": ["name", "posting_date", "grand_total"]},
    "Sales Invoice": {
        "filters": ["status"],
        "columns": ["name", "posting_date", "grand_total", "outstanding_amount"]},
    "Payment Entry": {
        "filters": ["payment_type"],
        "columns": ["name", "payment_type", "posting_date", "paid_amount"]},

    # ── المشتريات ──
    "Supplier": {
        "filters": ["supplier_name"],
        "columns": ["mobile_no", "email_id", "creation"]},
    "Material Request": {
        "filters": ["status"],
        "columns": ["name", "material_request_type", "transaction_date", "schedule_date"]},
    "Purchase Order": {
        "filters": ["status"],
        "columns": ["name", "transaction_date", "grand_total"]},
    "Purchase Receipt": {
        "filters": ["status"],
        "columns": ["name", "posting_date", "grand_total"]},
    "Purchase Invoice": {
        "filters": ["status"],
        "columns": ["name", "posting_date", "grand_total", "outstanding_amount"]},

    # ── المخزون ──
    "Item": {
        "filters": ["item_name", "item_group"],
        "columns": ["name", "item_group", "stock_uom", "valuation_rate"]},
    "Item Group": {
        "filters": [],
        "columns": ["parent_item_group", "is_group"]},
    "Warehouse": {
        "filters": [],
        "columns": ["warehouse_type", "is_group"]},
    "Stock Entry": {
        "filters": ["stock_entry_type"],
        "columns": ["name", "posting_date", "total_amount"]},
    "Stock Reconciliation": {
        "filters": [],
        "columns": ["posting_date", "purpose"]},

    # ── المحاسبة ──
    "Journal Entry": {
        "filters": ["voucher_type"],
        "columns": ["name", "voucher_type", "posting_date", "total_debit"]},
    "Account": {
        "filters": ["account_name", "root_type"],
        "columns": ["root_type", "account_type", "is_group"], "status": False},
    "Bank Account": {
        "filters": [],
        "columns": ["bank", "bank_account_no", "is_company_account"]},
    "Mode of Payment": {
        "filters": [],
        "columns": ["type", "enabled"], "status": False},
    "Accounting Period": {
        "filters": [],
        "columns": ["start_date", "end_date"]},
}
