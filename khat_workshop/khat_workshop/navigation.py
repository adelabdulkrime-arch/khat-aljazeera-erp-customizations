# -*- coding: utf-8 -*-
"""خريطة النظام: اللوحات السبع وما في كلٍّ منها. المصدر الوحيد.

كل ما يعرض «أين يوجد ماذا» يقرأ من هنا: بلاطات اللوحات، الشريط الجانبي،
البحث (Ctrl+K)، وأي شريط يظهر مع أي شاشة. قبل هذا الملف كانت القائمة نفسها
مكتوبة باليد في ثمانية مواضع — ستة بُناة لوحات، وقائمة لوحة الأوامر، وروابط
أسفل لوحة الورشة — فتباعدت: «الدفعات» كانت اسم بلاطتين مختلفتين (سندات القبض
وتشغيلات المخزون)، و«الأصناف» تفتح مجموعات الأصناف بينما الصنف نفسه
«المنتجات»، وفاتورة المبيعات تُسمّى فاتورة إصلاح في لوحة وفاتورة بيع في
ثانية وفاتورة خدمات في ثالثة.

قاعدتان لكل بلاطة:
  ١) اسمها هو اسم ما تفتحه — بالمسرد نفسه الذي تُترجم به الشاشة
     (setup/workshop_translations)، فلا يضغط أحد «الأصناف» ليجد شاشة عنوانها
     شيء آخر.
  ٢) تفتح ما تقوله. بلاطة لا يقابلها في النظام شيء حقيقي لا توجد: نسخة سابقة
     عرضت «الشيكات» و«فواتير المصروفات» و«تسوية الرسوم والضرائب» و«الأقساط»،
     وكلها تفتح قائمة القيود أو الفواتير كاملةً بلا أي تصفية.
"""

import frappe


def tile(label, label_en, kind, target, icon, filters=None):
    """بلاطة واحدة.

    kind: list | new | report | page | form | tree | company
      list/new/tree → target اسم DocType   ·  report → اسم التقرير
      form → DocType مفرد (Single)          ·  page → مسار الصفحة
      company → نموذج الشركة الافتراضية
    """
    t = {"label": label, "label_en": label_en, "kind": kind,
         "target": target, "icon": icon}
    if filters:
        t["filters"] = filters
    return t


def section(title, title_en, *tiles):
    return {"title": title, "title_en": title_en, "tiles": list(tiles)}


# ── بلاطات تتكرر في أكثر من لوحة: تُعرَّف مرة فتحمل الاسم نفسه أينما ظهرت ──
CUSTOMERS = tile("العملاء", "Customers", "list", "Customer", "users")
SUPPLIERS = tile("الموردون", "Suppliers", "list", "Supplier", "truck")
QUOTATIONS = tile("عروض الأسعار", "Quotations", "list", "Quotation", "file-text")
SALES_INVOICES = tile("فواتير المبيعات", "Sales Invoices", "list", "Sales Invoice",
                      "receipt", {"is_return": 0})
SALES_RETURNS = tile("مرتجعات المبيعات", "Sales Returns", "list", "Sales Invoice",
                     "trending-down", {"is_return": 1})
RECEIPTS = tile("سندات القبض", "Receipt Vouchers", "list", "Payment Entry",
                "banknote", {"payment_type": "Receive"})
PAYMENTS = tile("سندات الصرف", "Payment Vouchers", "list", "Payment Entry",
                "wallet", {"payment_type": "Pay"})
PURCHASE_INVOICES = tile("فواتير المشتريات", "Purchase Invoices", "list",
                         "Purchase Invoice", "receipt", {"is_return": 0})
RECEIVABLES = tile("مديونيات العملاء", "Customer Receivables", "report",
                   "Accounts Receivable", "hand-coins")
PAYABLES = tile("مستحقات الموردين", "Supplier Payables", "report",
                "Accounts Payable", "hand-coins")


MODULES = [
    {
        "key": "home", "workspace": "Home", "icon": "home",
        "title": "الرئيسية", "title_en": "Home",
        "sections": [],
    },
    {
        "key": "workshop", "workspace": "Workshop", "icon": "wrench",
        "color": "#c62839",
        "title": "الورشة", "title_en": "Workshop",
        "desc": "بطاقات العمل والعملاء والمركبات",
        "desc_en": "Work cards, customers and vehicles",
        "quick": [
            tile("بطاقة عمل جديدة", "New Work Card", "new", "Work Card", "plus"),
            tile("عميل جديد", "New Customer", "new", "Customer", "user-plus"),
            tile("مركبة جديدة", "New Vehicle", "new", "Customer Vehicle", "car-front"),
        ],
        "stats": ["open_cards", "cards_today", "receivables", "collected_month"],
        "widgets": ["lookup", "recent_cards"],
        "sections": [
            section("العملاء والمركبات", "Customers & Vehicles",
                    CUSTOMERS,
                    tile("المركبات", "Vehicles", "list", "Customer Vehicle", "car-front")),
            section("العمل والفوترة", "Jobs & Billing",
                    tile("بطاقات العمل", "Work Cards", "list", "Work Card", "clipboard-list"),
                    QUOTATIONS, SALES_INVOICES, RECEIPTS),
            section("الفنيون", "Technicians",
                    tile("الفنيون", "Technicians", "list", "Workshop Technician", "wrench"),
                    tile("سجل العمولات", "Commission Log", "list", "Commission Log",
                         "badge-percent")),
            section("المتابعة", "Follow-up",
                    tile("تذكيرات الصيانة", "Maintenance Reminders", "list",
                         "Maintenance Reminder", "bell")),
            section("التقارير", "Reports",
                    tile("تقرير بطاقات العمل", "Work Cards Report", "report",
                         "تقرير بطاقات العمل", "chart-bar"),
                    tile("تقرير الإيرادات", "Revenue Report", "report",
                         "تقرير الإيرادات", "trending-up"),
                    tile("تقرير الفنيين", "Technicians Report", "report",
                         "تقرير الفنيين", "chart-bar"),
                    tile("تقرير العمولات", "Commissions Report", "report",
                         "تقرير العمولات", "chart-bar")),
            section("الإعداد", "Setup",
                    tile("حالات بطاقة العمل", "Work Card Statuses", "list",
                         "Work Card Status", "tag"),
                    tile("ماركات المركبات", "Vehicle Brands", "list", "Vehicle Brand", "tag"),
                    tile("موديلات المركبات", "Vehicle Models", "list", "Vehicle Model",
                         "layout-grid"),
                    # كانت «الباقات» تفتح Product Bundle، وهو غير شاشة الباقات
                    # التي بُنيت للورشة (setup/workshop_packages).
                    tile("باقات الخدمات", "Service Packages", "list", "Workshop Package",
                         "gift"),
                    tile("إعدادات الورشة", "Workshop Settings", "form",
                         "Workshop Settings", "settings")),
        ],
    },
    {
        "key": "sales", "workspace": "Sales Dashboard", "icon": "shopping-cart",
        "color": "#1f8a4c",
        "title": "المبيعات", "title_en": "Sales",
        "desc": "عروض الأسعار والفواتير والتحصيل",
        "desc_en": "Quotations, invoices and collection",
        "quick": [
            tile("فاتورة مبيعات جديدة", "New Sales Invoice", "new", "Sales Invoice", "plus"),
            tile("عرض سعر جديد", "New Quotation", "new", "Quotation", "file-text"),
        ],
        "stats": ["sales_month", "receivables", "open_quotations", "customers"],
        "sections": [
            section("المستندات", "Documents",
                    QUOTATIONS,
                    tile("أوامر البيع", "Sales Orders", "list", "Sales Order",
                         "shopping-cart"),
                    tile("إشعارات التسليم", "Delivery Notes", "list", "Delivery Note", "truck"),
                    SALES_INVOICES, SALES_RETURNS, RECEIPTS),
            # نقطة البيع ليست هنا: لم يُعدّ لها ملف (POS Profile) ولا وردية، فكانت
            # بلاطاتها الثلاث تفتح شاشة تطلب إعداداً لا يعرفه موظف المبيعات. البيع
            # المباشر من الرف فاتورة مبيعات مع «تحديث المخزون». تُعاد البلاطات
            # هنا متى أُعدّت نقطة بيع فعلاً.
            section("العملاء", "Customers", CUSTOMERS),
            section("التقارير", "Reports",
                    tile("تحليل المبيعات", "Sales Analytics", "report", "Sales Analytics",
                         "chart-bar"),
                    RECEIVABLES),
        ],
    },
    {
        "key": "purchasing", "workspace": "Purchasing Dashboard", "icon": "package-plus",
        "color": "#c77a14",
        "title": "المشتريات", "title_en": "Purchasing",
        "desc": "أوامر الشراء والاستلام والموردون",
        "desc_en": "Purchase orders, receipts and suppliers",
        "quick": [
            tile("أمر شراء جديد", "New Purchase Order", "new", "Purchase Order", "plus"),
            tile("فاتورة مشتريات جديدة", "New Purchase Invoice", "new", "Purchase Invoice",
                 "receipt"),
        ],
        "stats": ["purchases_month", "payables", "open_purchase_orders", "suppliers"],
        "sections": [
            section("المستندات", "Documents",
                    tile("طلبات الشراء", "Purchase Requests", "list", "Material Request",
                         "file-text", {"material_request_type": "Purchase"}),
                    tile("أوامر الشراء", "Purchase Orders", "list", "Purchase Order",
                         "shopping-cart"),
                    tile("إشعارات الاستلام", "Purchase Receipts", "list", "Purchase Receipt",
                         "truck"),
                    PURCHASE_INVOICES,
                    tile("مرتجعات المشتريات", "Purchase Returns", "list", "Purchase Invoice",
                         "trending-down", {"is_return": 1}),
                    PAYMENTS),
            section("الموردون", "Suppliers", SUPPLIERS),
            section("التقارير", "Reports",
                    tile("تحليل المشتريات", "Purchase Analytics", "report",
                         "Purchase Analytics", "chart-bar"),
                    PAYABLES),
        ],
    },
    {
        "key": "inventory", "workspace": "Inventory Dashboard", "icon": "warehouse",
        "color": "#7a4cc2",
        "title": "المخزون", "title_en": "Inventory",
        "desc": "الأصناف والمستودعات والجرد",
        "desc_en": "Items, warehouses and stock counts",
        "quick": [
            tile("حركة مخزون جديدة", "New Stock Entry", "new", "Stock Entry", "plus"),
            tile("صنف جديد", "New Item", "new", "Item", "package"),
        ],
        "stats": ["stock_items", "stock_value", "low_stock", "stock_entries_month"],
        "sections": [
            section("الأصناف", "Items",
                    tile("الأصناف", "Items", "list", "Item", "package"),
                    tile("مجموعات الأصناف", "Item Groups", "list", "Item Group",
                         "layout-grid"),
                    tile("العلامات التجارية", "Brands", "list", "Brand", "tag"),
                    tile("وحدات القياس", "Units of Measure", "list", "UOM", "ruler")),
            section("المستودعات والحركات", "Warehouses & Movements",
                    tile("المستودعات", "Warehouses", "list", "Warehouse", "warehouse"),
                    tile("حركات المخزون", "Stock Entries", "list", "Stock Entry", "truck"),
                    tile("تحويلات بين المستودعات", "Warehouse Transfers", "list",
                         "Stock Entry", "arrow-left-right",
                         {"stock_entry_type": "Material Transfer"}),
                    tile("الصرف والإتلاف", "Issues & Write-offs", "list", "Stock Entry",
                         "trash-2", {"stock_entry_type": "Material Issue"}),
                    # «التشغيلات» (Batch) حُذفت: لا صنف يُتتبَّع بتشغيلة، وإعدادها
                    # في نموذج الصنف مخفي — كانت قائمة تبقى فارغة أبداً.
                    tile("الجرد", "Stock Reconciliation", "list", "Stock Reconciliation",
                         "file-check")),
            section("التقارير", "Reports",
                    tile("رصيد المخزون", "Stock Balance", "report", "Stock Balance",
                         "chart-bar"),
                    tile("دفتر حركة المخزون", "Stock Ledger", "report", "Stock Ledger",
                         "book-open"),
                    tile("الكميات المتوقعة وإعادة الطلب", "Projected Qty & Reorder",
                         "report", "Stock Projected Qty", "trending-up")),
        ],
    },
    {
        "key": "accounting", "workspace": "Accounting Dashboard", "icon": "landmark",
        "color": "#2f6fd6",
        "title": "المحاسبة", "title_en": "Accounting",
        "desc": "القيود والحسابات والتقارير المالية",
        "desc_en": "Journals, accounts and financial reports",
        "quick": [
            tile("قيد يومية جديد", "New Journal Entry", "new", "Journal Entry", "plus"),
            tile("سند قبض أو صرف جديد", "New Payment Voucher", "new", "Payment Entry",
                 "banknote"),
        ],
        "stats": ["cash_bank", "receivables", "payables", "sales_month"],
        "sections": [
            section("المبيعات والتحصيل", "Sales & Collection",
                    SALES_INVOICES, SALES_RETURNS, RECEIPTS),
            section("المشتريات والسداد", "Purchases & Payment",
                    PURCHASE_INVOICES, PAYMENTS),
            section("القيود والحسابات", "Journals & Accounts",
                    tile("قيود اليومية", "Journal Entries", "list", "Journal Entry",
                         "book-open"),
                    tile("دليل الحسابات", "Chart of Accounts", "tree", "Account", "list-tree"),
                    tile("الحسابات البنكية", "Bank Accounts", "list", "Bank Account",
                         "landmark"),
                    # «الأصول الثابتة» حُذفت: تسجيل أصل يتطلب فئات أصول ومواقع
                    # وأصنافاً من نوع أصل ثابت لم يُعدّ شيء منها.
                    tile("طرق الدفع", "Payment Methods", "list", "Mode of Payment",
                         "credit-card")),
            section("الإقفال والتسوية", "Closing & Reconciliation",
                    tile("الفترات المحاسبية", "Accounting Periods", "list",
                         "Accounting Period", "calendar"),
                    tile("الأرصدة الافتتاحية", "Opening Balances", "form",
                         "Opening Invoice Creation Tool", "file-plus"),
                    tile("التسوية البنكية", "Bank Reconciliation", "form",
                         "Bank Reconciliation Tool", "scale")),
            section("التقارير المالية", "Financial Reports",
                    tile("دفتر الأستاذ العام", "General Ledger", "report", "General Ledger",
                         "book-open"),
                    tile("ميزان المراجعة", "Trial Balance", "report", "Trial Balance",
                         "scale"),
                    tile("قائمة الدخل", "Profit and Loss", "report",
                         "Profit and Loss Statement", "trending-up"),
                    tile("قائمة المركز المالي", "Balance Sheet", "report", "Balance Sheet",
                         "chart-bar"),
                    tile("التدفقات النقدية", "Cash Flow", "report", "Cash Flow",
                         "arrow-left-right"),
                    RECEIVABLES, PAYABLES),
        ],
    },
    {
        "key": "settings", "workspace": "General Settings", "icon": "settings",
        "color": "#55627a",
        "title": "الإعدادات العامة", "title_en": "General Settings",
        "desc": "المستخدمون والأدوار وبيانات المنشأة",
        "desc_en": "Users, roles and company details",
        "sections": [
            section("المستخدمون والصلاحيات", "Users & Permissions",
                    tile("المستخدمون", "Users", "list", "User", "users"),
                    tile("الأدوار", "Roles", "list", "Role", "shield-user")),
            section("المنشأة", "Company",
                    tile("بيانات الشركة", "Company Details", "company", "Company",
                         "building-2"),
                    tile("الشعار والهوية", "Logo & Identity", "form", "Website Settings",
                         "image"),
                    tile("ترويسات الطباعة", "Print Letterheads", "list", "Letter Head",
                         "printer"),
                    tile("إعدادات الورشة", "Workshop Settings", "form", "Workshop Settings",
                         "settings")),
            section("النظام", "System",
                    tile("سجل النشاط", "Activity Log", "list", "Activity Log", "history"),
                    tile("النسخ الاحتياطي", "Backups", "page", "backups",
                         "database-backup")),
        ],
    },
]

# شاشات تُفتح من داخل شاشات أخرى لا من بلاطة، ومع ذلك يجب أن يبقى معها شريط
# لوحتها لا شريط Frappe الخاص بها.
RELATED = {
    "Company": "General Settings",
    "Address": "Workshop",
    "Contact": "Workshop",
    "Item Price": "Inventory Dashboard",
    "Price List": "Inventory Dashboard",
    "Workshop Package": "Workshop",
    "Sales Taxes and Charges Template": "Accounting Dashboard",
    "Purchase Taxes and Charges Template": "Accounting Dashboard",
    "Cost Center": "Accounting Dashboard",
    "Fiscal Year": "Accounting Dashboard",
    "GL Entry": "Accounting Dashboard",
    "Stock Ledger Entry": "Inventory Dashboard",
    "Bin": "Inventory Dashboard",
    "Notification Log": "Home",
}

WORKSPACES = [m["workspace"] for m in MODULES]


def nav_map():
    """اسم الشاشة (DocType، تقرير، صفحة) → اللوحة التي يُعرض شريطها معها.

    شاشة تظهر في أكثر من لوحة تُنسب لأولاها ترتيباً. هذا للدخول المباشر فقط
    (رابط محفوظ، تحديث الصفحة)؛ في التنقّل العادي يبقى شريط اللوحة التي جاء
    منها المستخدم كما هو.
    """
    out = {}
    for module in MODULES:
        groups = [s["tiles"] for s in module.get("sections", [])]
        groups.append(module.get("quick", []))
        for group in groups:
            for t in group:
                out.setdefault(t["target"], module["workspace"])
    for name, workspace in RELATED.items():
        out.setdefault(name, workspace)
    return out


def all_tiles():
    """كل بلاطة مع لوحتها، بلا تكرار — للبحث وللفحص."""
    seen, out = set(), []
    for module in MODULES:
        for group in [module.get("quick", [])] + [s["tiles"] for s in module.get("sections", [])]:
            for t in group:
                key = (t["kind"], t["target"], frappe.as_json(t.get("filters") or {}))
                if key in seen:
                    continue
                seen.add(key)
                out.append(dict(t, module=module["key"]))
    return out


def for_boot():
    """ما يحتاجه المتصفح، يُرسَل مرة مع بيانات الإقلاع."""
    return {
        "modules": MODULES,
        "workspaces": WORKSPACES,
        "nav": nav_map(),
    }
