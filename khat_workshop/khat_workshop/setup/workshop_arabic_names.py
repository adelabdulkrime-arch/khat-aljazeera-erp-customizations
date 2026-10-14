# -*- coding: utf-8 -*-
"""أسماء عربية لدليل الحسابات والمستودعات ومركز التكلفة وقائمتَي الأسعار.

ERPNext ينشئ دليل حساباته القياسي ومستودعاته بالإنجليزية أياً كانت لغة الواجهة:
«Cash - KHAT»، «Sales - KHAT»، «Stores - KHAT». وهذه أسماء سجلّات لا تسميات
حقول، فلا يصلها المسرد: تظهر كما هي في قيد اليومية ودفتر الأستاذ وتقرير رصيد
المخزون وكل قائمة اختيار — إنجليزية في نظام كله عربي، أمام محاسب يبحث عن
«الصندوق» فلا يجده.

تُعاد تسميتها هنا (إعادة تسمية حقيقية: كل مستند يشير إلى الحساب يتبعه). ما
غيّر المستخدم اسمه أو أضافه لا يُمسّ: يُعاد تسمية ما يحمل الاسم القياسي وحده،
ولا يُدمج حساب في حساب. تعمل مرة؛ في التشغيلات التالية لا تجد اسماً قياسياً.

تسبق في الترتيب كل خطوة تبحث عن مستودع أو حساب (workshop_gl_stock_integration
يجد المخزن بـ«%مخزن%»، وworkshop_oman_setup يجد «الرسوم والضرائب»).
"""

import frappe

ACCOUNTS = {
    # الأصول
    "Application of Funds (Assets)": u"الأصول",
    "Current Assets": u"الأصول المتداولة",
    "Accounts Receivable": u"الذمم المدينة",
    "Debtors": u"العملاء (مدينون)",
    "Bank Accounts": u"الحسابات البنكية",
    "Cash In Hand": u"النقدية",
    "Cash": u"الصندوق",
    "Loans and Advances (Assets)": u"قروض وسلف (أصول)",
    "Employee Advances": u"سلف الموظفين",
    "Prepaid Expenses": u"مصروفات مدفوعة مقدماً",
    "Securities and Deposits": u"أوراق مالية وودائع",
    "Earnest Money": u"تأمينات مستردة",
    "Short-term Investments": u"استثمارات قصيرة الأجل",
    "Stock Assets": u"أصول المخزون",
    "Stock In Hand": u"المخزون",
    "Tax Assets": u"أصول ضريبية",
    "Fixed Assets": u"الأصول الثابتة",
    "Accumulated Depreciation": u"مجمع الإهلاك",
    "Buildings": u"المباني",
    "Capital Equipment": u"المعدات الرأسمالية",
    "CWIP Account": u"أعمال رأسمالية تحت التنفيذ",
    "Electronic Equipment": u"الأجهزة الإلكترونية",
    "Furniture and Fixtures": u"الأثاث والتجهيزات",
    "Office Equipment": u"المعدات المكتبية",
    "Plants and Machineries": u"الآلات والمعدات",
    "Software": u"البرمجيات",
    "Investments": u"الاستثمارات",
    "Temporary Accounts": u"حسابات مؤقتة",
    "Temporary Opening": u"حساب الافتتاح المؤقت",
    # حقوق الملكية
    "Equity": u"حقوق الملكية",
    "Capital Stock": u"رأس المال",
    "Dividends Paid": u"أرباح موزعة",
    "Opening Balance Equity": u"أرصدة افتتاحية (حقوق ملكية)",
    "Retained Earnings": u"أرباح مبقاة",
    "Revaluation Surplus": u"فائض إعادة التقييم",
    # المصروفات
    "Expenses": u"المصروفات",
    "Direct Expenses": u"مصروفات مباشرة",
    "Stock Expenses": u"مصروفات المخزون",
    "Cost of Goods Sold": u"تكلفة البضاعة المباعة",
    "Expenses Included In Asset Valuation": u"مصروفات محمّلة على تقييم الأصول",
    "Expenses Included In Valuation": u"مصروفات محمّلة على تقييم المخزون",
    "Stock Adjustment": u"تسويات المخزون",
    "Indirect Expenses": u"مصروفات غير مباشرة",
    "Administrative Expenses": u"مصروفات إدارية",
    "Bank Charges": u"عمولات بنكية",
    "Commission on Sales": u"عمولات المبيعات",
    "Depreciation": u"الإهلاك",
    "Entertainment Expenses": u"مصروفات ضيافة",
    "Exchange Gain/Loss": u"فروق العملة",
    "Freight and Forwarding Charges": u"مصروفات الشحن والنقل",
    "Gain/Loss on Asset Disposal": u"أرباح وخسائر بيع الأصول",
    "Impairment": u"انخفاض قيمة الأصول",
    "Interest Expense": u"مصروف الفوائد",
    "Legal Expenses": u"مصروفات قانونية",
    "Marketing Expenses": u"مصروفات التسويق",
    "Miscellaneous Expenses": u"مصروفات متنوعة",
    "Office Maintenance Expenses": u"صيانة المقر",
    "Office Rent": u"إيجار المقر",
    "Postal Expenses": u"مصروفات البريد",
    "Print and Stationery": u"مطبوعات وقرطاسية",
    "Round Off": u"فروق التقريب",
    "Salary": u"الرواتب",
    "Sales Expenses": u"مصروفات البيع",
    "Tax Expense": u"مصروف الضرائب",
    "Telephone Expenses": u"الهاتف والإنترنت",
    "Travel Expenses": u"السفر والتنقل",
    "Utility Expenses": u"الكهرباء والماء",
    "Write Off": u"ديون معدومة",
    # الإيرادات
    "Income": u"الإيرادات",
    "Direct Income": u"إيرادات مباشرة",
    "Sales": u"المبيعات",
    "Service": u"إيرادات الخدمات",
    "Indirect Income": u"إيرادات غير مباشرة",
    "Interest Income": u"إيرادات الفوائد",
    "Interest on Fixed Deposits": u"فوائد الودائع الثابتة",
    # الالتزامات
    "Source of Funds (Liabilities)": u"الالتزامات",
    "Current Liabilities": u"الالتزامات المتداولة",
    "Accounts Payable": u"الذمم الدائنة",
    "Creditors": u"الموردون (دائنون)",
    "Payroll Payable": u"رواتب مستحقة",
    "Accrued Expenses": u"مصروفات مستحقة",
    "Customer Advances": u"دفعات مقدمة من العملاء",
    # workshop_oman_setup يبحث عن هذا الاسم بعينه
    "Duties and Taxes": u"الرسوم والضرائب",
    "Loans (Liabilities)": u"القروض",
    "Bank Overdraft Account": u"السحب على المكشوف",
    "Secured Loans": u"قروض مضمونة",
    "Unsecured Loans": u"قروض غير مضمونة",
    "Short-term Provisions": u"مخصصات قصيرة الأجل",
    "Stock Liabilities": u"التزامات المخزون",
    "Asset Received But Not Billed": u"أصول مستلمة لم تُفوتر",
    "Stock Received But Not Billed": u"بضاعة مستلمة لم تُفوتر",
    "Non-Current Liabilities": u"الالتزامات غير المتداولة",
    "Employee Benefits Obligation": u"التزامات مزايا الموظفين",
    "Long-term Provisions": u"مخصصات طويلة الأجل",
}

WAREHOUSES = {
    "All Warehouses": u"كل المستودعات",
    # «مخزن» لا «مستودع»: به تجد الخطوات التالية المخزن الافتراضي
    "Stores": u"المخزن الرئيسي",
    "Work In Progress": u"تحت التشغيل",
    "Finished Goods": u"بضاعة تامة الصنع",
    "Goods In Transit": u"بضاعة في الطريق",
}

COST_CENTERS = {
    "Main": u"المركز الرئيسي",
}

# قائمتا الأسعار القياسيتان. اسماهما يُكتبان كما هما في رسائل النظام («أُضيف سعر
# الصنف إلى قائمة الأسعار Standard Buying»)، والترجمة لا تصل إلا إلى عرضهما في الحقول.
PRICE_LISTS = {
    "Standard Buying": u"أسعار الشراء",
    "Standard Selling": u"أسعار البيع",
}

# (نوع المستند، حقل الاسم، الخريطة)
MASTERS = (
    ("Account", "account_name", ACCOUNTS),
    ("Warehouse", "warehouse_name", WAREHOUSES),
    ("Cost Center", "cost_center_name", COST_CENTERS),
)


def execute():
    done = {}
    for company in frappe.get_all("Company", fields=["name", "abbr"]):
        for doctype, field, names in MASTERS:
            if not frappe.db.exists("DocType", doctype):
                continue
            rows = frappe.get_all(doctype, filters={"company": company.name, field: ["in", list(names)]},
                                  fields=["name", field])
            for row in rows:
                arabic = names.get(row[field])
                if not arabic:                      # ترتيب قاعدة البيانات يتجاهل حالة الحروف
                    continue
                new = u"%s - %s" % (arabic, company.abbr)
                if frappe.db.exists(doctype, new):  # الاسم العربي مأخوذ: لا دمج
                    continue
                frappe.rename_doc(doctype, row.name, new, force=True, show_alert=False,
                                  rebuild_search=False)
                frappe.db.set_value(doctype, new, field, arabic, update_modified=False)
                done[doctype] = done.get(doctype, 0) + 1
    for old, arabic in PRICE_LISTS.items():
        if frappe.db.exists("Price List", old) and not frappe.db.exists("Price List", arabic):
            frappe.rename_doc("Price List", old, arabic, force=True, show_alert=False,
                              rebuild_search=False)
            frappe.db.set_value("Price List", arabic, "price_list_name", arabic, update_modified=False)
            done["Price List"] = done.get("Price List", 0) + 1
    if done:
        frappe.db.commit()
        frappe.clear_cache()
    print("ARABIC_NAMES renamed=%s" % (done or "none"))
