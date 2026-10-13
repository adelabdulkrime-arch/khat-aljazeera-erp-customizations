# -*- coding: utf-8 -*-
"""أدوار النظام: المسمّيات الوظيفية وما يحمله كلٌّ منها. المصدر الوحيد.

في النظام نحو ستين دوراً قياسياً من Frappe وERPNext («Accounts User»،
«Stock Manager»، «Item Manager»…) وأربعة عشر مسمّى وظيفياً أُضيفت للورشة
(«محاسب»، «مدير المستودع»…). صاحب الورشة يعرف المسمّى الوظيفي، ولا يعنيه
الفرق بين «Accounts User» و«Accounts Manager».

المشكلة التي يعالجها هذا الملف: المسمّى الوظيفي كان يُمنح صلاحيات على عدد
قليل من المستندات (setup/workshop_permissions)، أما مئات المستندات المساندة
التي تحتاجها أي فاتورة — الشركة، العملة، الحسابات، قوائم الأسعار، الوحدات،
قوالب الضريبة، طرق الدفع — فصلاحياتها في ERPNext معلّقة بأدواره القياسية
وحدها. فحامل «محاسب» يفتح قائمة الفواتير ثم لا يجد حساباً يختاره ولا
تقريراً يفتحه.

الحل: كل مسمّى وظيفي «يحمل» الأدوار القياسية التي تؤدي عمله. تُضاف للمستخدم
تلقائياً عند حفظه وتُزال بإزالة المسمّى (sync_implied، مربوط بحفظ User في
hooks.py). مصفوفة صلاحيات ERPNext القياسية تبقى كما اختبرها أصحابها، وتتبع
تحديثاته، بدل نسخة منها نصونها نحن.

في الواجهة لا يظهر إلا المسمّى الوظيفي: في حوار «إضافة مستخدم»، في تبويب
الأدوار بنموذج المستخدم، وفي عمود «الأدوار» بقائمة المستخدمين.
"""

import frappe

# الدور، العربية، الإنجليزية، ما يفعله (ع)، ما يفعله (إ)، الأدوار القياسية التي يحملها
JOBS = [
    ("مدير النظام", "مدير النظام", "Super Admin",
     "كل شيء: المستخدمون والإعدادات وجميع اللوحات",
     "Everything: users, settings and every dashboard",
     ["System Manager", "Website Manager", "Accounts Manager", "Accounts User", "Sales Master Manager",
      "Sales User", "Purchase Manager", "Purchase Master Manager", "Purchase User",
      "Stock Manager", "Stock User", "Item Manager"]),
    ("Workshop Manager", "مدير الورشة", "Workshop Manager",
     "دورة الورشة كاملة: البطاقات والعملاء وعروض الأسعار والفواتير والتحصيل",
     "The whole workshop cycle: work cards, customers, quotations, invoices, collection",
     ["Sales Master Manager", "Sales User", "Stock User", "Accounts User"]),
    ("موظف استقبال الورشة", "موظف استقبال الورشة", "Workshop Receptionist",
     "استلام المركبات: العملاء والمركبات وبطاقات العمل وعروض الأسعار",
     "Vehicle intake: customers, vehicles, work cards and quotations",
     ["Sales User"]),
    ("فني ورشة", "فني ورشة", "Workshop Technician",
     "العمل على بطاقات العمل المسندة، بلا أسعار ولا حذف",
     "Works the job cards; no pricing, no deleting",
     []),
    ("محاسب", "محاسب", "Accountant",
     "الفواتير والسندات والقيود والتقارير المالية",
     "Invoices, vouchers, journals and financial reports",
     ["Accounts Manager", "Accounts User", "Sales User", "Purchase User"]),
    ("كاشير", "كاشير", "Cashier",
     "إصدار فواتير المبيعات وقبض قيمتها",
     "Raises sales invoices and takes payment",
     ["Sales User"]),
    ("Sales Manager", "مدير المبيعات", "Sales Manager",
     "عروض الأسعار وأوامر البيع والفواتير والعملاء وتقارير المبيعات",
     "Quotations, sales orders, invoices, customers and sales reports",
     ["Sales Master Manager", "Sales User", "Stock User"]),
    ("مندوب مبيعات", "مندوب مبيعات", "Sales Representative",
     "عروض الأسعار وأوامر البيع والعملاء",
     "Quotations, sales orders and customers",
     ["Sales User"]),
    ("مسؤول المشتريات", "مسؤول المشتريات", "Purchasing Officer",
     "الموردون وأوامر الشراء والاستلام وفواتير المشتريات",
     "Suppliers, purchase orders, receipts and purchase invoices",
     ["Purchase Manager", "Purchase Master Manager", "Purchase User", "Stock User"]),
    ("مدير المستودع", "مدير المستودع", "Warehouse Manager",
     "الأصناف والمستودعات وحركات المخزون والجرد",
     "Items, warehouses, stock movements and stock counts",
     ["Stock Manager", "Stock User", "Item Manager"]),
    ("HR Manager", "مدير الموارد البشرية", "HR Manager",
     "الموظفون وشؤونهم",
     "Employees and HR",
     []),
    ("مسؤول", "مسؤول", "Admin",
     "اطّلاع فقط: بطاقات العمل والفواتير والسندات والعملاء والأصناف",
     "Read-only: work cards, invoices, vouchers, customers and items",
     []),
    ("مدير", "مدير", "Manager",
     "اطّلاع فقط: بطاقات العمل والفواتير والسندات والعملاء والأصناف",
     "Read-only: work cards, invoices, vouchers, customers and items",
     []),
    ("Employee", "موظف", "Employee",
     "حساب موظف بلا صلاحيات تشغيل",
     "A staff account with no operating permissions",
     []),
]

JOB_ROLES = [job[0] for job in JOBS]
IMPLIED = {job[0]: job[5] for job in JOBS}

# الأدوار القياسية التي يديرها هذا الملف: تُمنح وتُسحب تبعاً للمسمّى الوظيفي.
# ليس بينها مسمّى وظيفي — لو حمل مسمّى مسمّى آخر لظهر للمستخدم دورٌ لم يُختَر له.
MANAGED = sorted({role for implied in IMPLIED.values() for role in implied})
assert not set(MANAGED) & set(JOB_ROLES)


def wanted_for(job_roles):
    """الأدوار القياسية التي تحملها مجموعة مسمّيات وظيفية."""
    return {role for job in job_roles if job in IMPLIED for role in IMPLIED[job]}


def sync_implied(doc, method=None):
    """يطابق أدوار المستخدم القياسية مع مسمّياته الوظيفية. يُستدعى قبل حفظه.

    Administrator وGuest خارج هذا: الأول يحمل كل الأدوار بحكم تعريفه.
    """
    if doc.name in ("Administrator", "Guest"):
        return
    held = [row.role for row in doc.get("roles") or []]
    wanted = wanted_for(held)
    for row in list(doc.get("roles") or []):
        if row.role in MANAGED and row.role not in wanted:
            doc.remove(row)
    for role in sorted(wanted - set(held)):
        if frappe.db.exists("Role", role):
            doc.append("roles", {"role": role})


def for_boot():
    """المسمّيات الوظيفية للواجهة: حوار إضافة مستخدم وتبويب الأدوار."""
    return [{"role": role, "ar": ar, "en": en, "desc": desc, "desc_en": desc_en}
            for role, ar, en, desc, desc_en, _implied in JOBS
            if frappe.db.exists("Role", role)]
