# -*- coding: utf-8 -*-
"""ما تطلبه اللوحات من الخادم: الأرقام، البحث، وملف العميل.

طلب واحد لكل لوحة بدل طلب لكل بطاقة. بطاقات الأرقام كانت Number Cards من
الإطار، كلٌّ منها يجلب نفسه ثم يجلب نسبة تغيّره: لوحة الورشة وحدها أرسلت
نحو ستين طلباً عند الفتح. وكانت تعدّ خطأً: مرشّحاتها فارغة، فـ«إجمالي
المبيعات» جمع المسودات والفواتير الملغاة مع المعتمدة، و«أوامر البيع المعلّقة»
عدّ كل أمر بيع أياً كانت حالته، وأي مجموع قيمته صفر ظهر «NaN».

كل رقم هنا يُحسب من المستندات المعتمدة وحدها (docstatus = 1) ما لم يكن
السؤال عن غيرها صراحةً، ويُحجب عمّن لا يملك صلاحية قراءة مصدره.
"""

import frappe
from frappe.utils import flt, get_first_day, get_last_day, nowdate, today

from khat_workshop import navigation, roles


def _month():
    return get_first_day(nowdate()), get_last_day(nowdate())


def _scalar(query, values=None):
    row = frappe.db.sql(query, values or {})
    return row[0][0] if row and row[0][0] is not None else 0


def _closed_statuses():
    return frappe.get_all("Work Card Status", filters={"is_closed": 1}, pluck="name")


# ── الأرقام ──────────────────────────────────────────────────────────────────
# لكل رقم: مصدره (للصلاحية)، كيف يُحسب، وإلى أين يذهب من ينقر عليه — رقمٌ لا
# يفتح ما وراءه يترك المستخدم يبحث عن مصدره بنفسه.

def _open_cards():
    closed = _closed_statuses() or [""]
    return frappe.db.count("Work Card", {"docstatus": ["<", 2], "status": ["not in", closed]})


def _cards_today():
    return frappe.db.count("Work Card", {
        "docstatus": ["<", 2], "entry_date": ["between", [today(), today()]]})


def _receivables():
    return _scalar("select sum(outstanding_amount) from `tabSales Invoice` where docstatus = 1")


def _collected_month():
    start, end = _month()
    return _scalar(
        """select sum(base_paid_amount) from `tabPayment Entry`
           where docstatus = 1 and payment_type = 'Receive'
             and posting_date between %(s)s and %(e)s""", {"s": start, "e": end})


def _sales_month():
    start, end = _month()
    return _scalar(
        """select sum(base_grand_total) from `tabSales Invoice`
           where docstatus = 1 and posting_date between %(s)s and %(e)s""",
        {"s": start, "e": end})


def _open_quotations():
    return frappe.db.count("Quotation", {"docstatus": 1, "status": "Open"})


def _customers():
    return frappe.db.count("Customer", {"disabled": 0})


def _purchases_month():
    start, end = _month()
    return _scalar(
        """select sum(base_grand_total) from `tabPurchase Invoice`
           where docstatus = 1 and posting_date between %(s)s and %(e)s""",
        {"s": start, "e": end})


def _payables():
    return _scalar("select sum(outstanding_amount) from `tabPurchase Invoice` where docstatus = 1")


OPEN_PO = ["To Receive and Bill", "To Receive", "To Bill"]


def _open_purchase_orders():
    return frappe.db.count("Purchase Order", {"docstatus": 1, "status": ["in", OPEN_PO]})


def _suppliers():
    return frappe.db.count("Supplier", {"disabled": 0})


def _stock_items():
    return frappe.db.count("Item", {"is_stock_item": 1, "disabled": 0})


def _stock_value():
    return _scalar("select sum(stock_value) from `tabBin`")


def _low_stock():
    return _scalar(
        """select count(*) from `tabItem Reorder` r
           join `tabItem` i on i.name = r.parent and i.disabled = 0
           left join `tabBin` b on b.item_code = r.parent and b.warehouse = r.warehouse
           where r.parenttype = 'Item'
             and ifnull(b.actual_qty, 0) <= r.warehouse_reorder_level""")


def _stock_entries_month():
    start, end = _month()
    return frappe.db.count("Stock Entry", {
        "docstatus": 1, "posting_date": ["between", [start, end]]})


def _cash_bank():
    return _scalar(
        """select sum(g.debit - g.credit) from `tabGL Entry` g
           join `tabAccount` a on a.name = g.account
           where g.is_cancelled = 0 and a.is_group = 0
             and a.account_type in ('Cash', 'Bank')""")


# key: (label, label_en, نوع القيمة, المصدر, الدالة, الوجهة عند النقر)
STATS = {
    "open_cards": ("بطاقات عمل مفتوحة", "Open work cards", "count", "Work Card", _open_cards,
                   {"kind": "list", "target": "Work Card",
                    "filters": {"docstatus": ["<", 2], "status": ["not in", "@closed"]}}),
    "cards_today": ("دخلت اليوم", "Checked in today", "count", "Work Card", _cards_today,
                    {"kind": "list", "target": "Work Card",
                     "filters": {"entry_date": ["Timespan", "today"]}}),
    "receivables": ("مستحقات على العملاء", "Due from customers", "currency",
                    "Sales Invoice", _receivables,
                    {"kind": "list", "target": "Sales Invoice",
                     "filters": {"docstatus": 1, "outstanding_amount": [">", 0]}}),
    "collected_month": ("تحصيل هذا الشهر", "Collected this month", "currency",
                        "Payment Entry", _collected_month,
                        {"kind": "list", "target": "Payment Entry",
                         "filters": {"docstatus": 1, "payment_type": "Receive",
                                     "posting_date": ["Timespan", "this month"]}}),
    "sales_month": ("مبيعات هذا الشهر", "Sales this month", "currency",
                    "Sales Invoice", _sales_month,
                    {"kind": "list", "target": "Sales Invoice",
                     "filters": {"docstatus": 1, "posting_date": ["Timespan", "this month"]}}),
    "open_quotations": ("عروض أسعار مفتوحة", "Open quotations", "count",
                        "Quotation", _open_quotations,
                        {"kind": "list", "target": "Quotation",
                         "filters": {"docstatus": 1, "status": "Open"}}),
    "customers": ("العملاء", "Customers", "count", "Customer", _customers,
                  {"kind": "list", "target": "Customer", "filters": {"disabled": 0}}),
    "purchases_month": ("مشتريات هذا الشهر", "Purchases this month", "currency",
                        "Purchase Invoice", _purchases_month,
                        {"kind": "list", "target": "Purchase Invoice",
                         "filters": {"docstatus": 1,
                                     "posting_date": ["Timespan", "this month"]}}),
    "payables": ("مستحقات للموردين", "Due to suppliers", "currency",
                 "Purchase Invoice", _payables,
                 {"kind": "list", "target": "Purchase Invoice",
                  "filters": {"docstatus": 1, "outstanding_amount": [">", 0]}}),
    "open_purchase_orders": ("أوامر شراء مفتوحة", "Open purchase orders", "count",
                             "Purchase Order", _open_purchase_orders,
                             {"kind": "list", "target": "Purchase Order",
                              "filters": {"docstatus": 1, "status": ["in", OPEN_PO]}}),
    "suppliers": ("الموردون", "Suppliers", "count", "Supplier", _suppliers,
                  {"kind": "list", "target": "Supplier", "filters": {"disabled": 0}}),
    "stock_items": ("أصناف مخزنية", "Stock items", "count", "Item", _stock_items,
                    {"kind": "list", "target": "Item",
                     "filters": {"is_stock_item": 1, "disabled": 0}}),
    "stock_value": ("قيمة المخزون", "Stock value", "currency", "Bin", _stock_value,
                    {"kind": "report", "target": "Stock Balance"}),
    "low_stock": ("أصناف بلغت حدّ الطلب", "Items at reorder level", "count",
                  "Item", _low_stock,
                  {"kind": "report", "target": "Stock Projected Qty"}),
    "stock_entries_month": ("حركات هذا الشهر", "Movements this month", "count",
                            "Stock Entry", _stock_entries_month,
                            {"kind": "list", "target": "Stock Entry",
                             "filters": {"docstatus": 1,
                                         "posting_date": ["Timespan", "this month"]}}),
    "cash_bank": ("النقدية والبنوك", "Cash & bank", "currency", "GL Entry", _cash_bank,
                  {"kind": "report", "target": "General Ledger"}),
}


def _stats(keys):
    out = []
    closed = None
    for key in keys:
        label, label_en, kind, source, fn, route = STATS[key]
        if not frappe.has_permission(source, "read"):
            continue
        route = frappe.parse_json(frappe.as_json(route))      # نسخة: القالب لا يُعدَّل
        for field, value in (route.get("filters") or {}).items():
            if isinstance(value, list) and value[-1] == "@closed":
                closed = closed if closed is not None else _closed_statuses()
                value[-1] = closed
        out.append({"key": key, "label": label, "label_en": label_en, "kind": kind,
                    "value": flt(fn()), "route": route})
    return out


def _recent_cards(limit=8):
    if not frappe.has_permission("Work Card", "read"):
        return None
    cards = frappe.get_list(
        "Work Card",
        fields=["name", "customer", "customer_phone", "plate_number", "brand", "model",
                "entry_date", "status", "grand_total", "docstatus"],
        filters={"docstatus": ["<", 2]}, order_by="creation desc", limit_page_length=limit)
    colors = {s.name: s.color for s in frappe.get_all(
        "Work Card Status", fields=["name", "color"])}
    names = {c.customer for c in cards if c.customer}
    titles = dict(frappe.get_all(
        "Customer", filters={"name": ["in", list(names)]},
        fields=["name", "customer_name"], as_list=1)) if names else {}
    for c in cards:
        c.status_color = colors.get(c.status)
        c.customer_name = titles.get(c.customer) or c.customer
    return cards


@frappe.whitelist()
def dashboard(module):
    """أرقام لوحة واحدة، ومعها أحدث بطاقات العمل إن كانت اللوحة تعرضها."""
    spec = next((m for m in navigation.MODULES if m["key"] == module), None)
    if not spec:
        frappe.throw(frappe._("Unknown dashboard: {0}").format(module))
    out = {"stats": _stats(spec.get("stats", [])),
           "currency": frappe.db.get_default("currency")}
    if "recent_cards" in spec.get("widgets", []):
        out["recent_cards"] = _recent_cards()
    return out


@frappe.whitelist()
def lookup(q):
    """بحث واحد عن عميل أو مركبة أو بطاقة عمل أو فاتورة.

    بالاسم، رقم الجوال، رقم اللوحة أو رقم المستند. frappe.get_list يطبّق
    صلاحيات المستخدم، فلا يظهر له ما لا يحقّ له فتحه.
    """
    q = (q or "").strip()
    if len(q) < 2:
        return []
    like = "%" + q + "%"
    out = []

    if frappe.has_permission("Customer", "read"):
        for c in frappe.get_list(
                "Customer", fields=["name", "customer_name", "mobile_no"],
                or_filters=[["customer_name", "like", like], ["mobile_no", "like", like],
                            ["name", "like", like]], limit_page_length=6):
            out.append({"type": "customer", "doctype": "Customer", "name": c.name,
                        "title": c.customer_name or c.name, "sub": c.mobile_no or ""})

    if frappe.has_permission("Customer Vehicle", "read"):
        for v in frappe.get_list(
                "Customer Vehicle",
                fields=["name", "plate_number", "customer", "brand", "model"],
                or_filters=[["plate_number", "like", like], ["customer", "like", like]],
                limit_page_length=6):
            out.append({"type": "vehicle", "doctype": "Customer Vehicle", "name": v.name,
                        "title": v.plate_number or v.name,
                        "sub": " · ".join(x for x in (
                            frappe.db.get_value("Customer", v.customer, "customer_name")
                            if v.customer else "",
                            " ".join(x for x in (v.brand, _model(v.model)) if x)) if x),
                        "customer": v.customer})

    if frappe.has_permission("Work Card", "read"):
        for w in frappe.get_list(
                "Work Card", fields=["name", "plate_number", "status", "customer"],
                or_filters=[["name", "like", like], ["plate_number", "like", like]],
                filters={"docstatus": ["<", 2]}, order_by="creation desc",
                limit_page_length=5):
            out.append({"type": "work_card", "doctype": "Work Card", "name": w.name,
                        "title": w.name, "sub": " · ".join(
                            x for x in (w.plate_number, w.status) if x)})

    if frappe.has_permission("Sales Invoice", "read"):
        for s in frappe.get_list(
                "Sales Invoice",
                fields=["name", "customer_name", "grand_total", "currency", "docstatus"],
                or_filters=[["name", "like", like], ["customer_name", "like", like]],
                filters={"docstatus": ["<", 2]}, order_by="creation desc",
                limit_page_length=5):
            out.append({"type": "invoice", "doctype": "Sales Invoice", "name": s.name,
                        "title": s.name, "sub": s.customer_name or "",
                        "amount": flt(s.grand_total), "currency": s.currency})
    return out


def _model(name):
    """Vehicle Model يُسمّى «البراند-الموديل»؛ المعروض اسم الموديل وحده."""
    if not name:
        return ""
    return frappe.db.get_value("Vehicle Model", name, "model_name") or name


@frappe.whitelist()
def customer_profile(customer):
    """مركبات العميل، أحدث بطاقاته وفواتيره، وما له وما عليه — في طلب واحد."""
    frappe.has_permission("Customer", "read", customer, throw=True)
    doc = frappe.db.get_value(
        "Customer", customer, ["name", "customer_name", "mobile_no"], as_dict=True)

    vehicles = frappe.get_list(
        "Customer Vehicle", filters={"customer": customer},
        fields=["name", "plate_number", "brand", "model"], limit_page_length=20) \
        if frappe.has_permission("Customer Vehicle", "read") else []
    for v in vehicles:
        v.model = _model(v.model)

    cards = frappe.get_list(
        "Work Card", filters={"customer": customer, "docstatus": ["<", 2]},
        fields=["name", "status", "entry_date", "plate_number"],
        order_by="creation desc", limit_page_length=5) \
        if frappe.has_permission("Work Card", "read") else []

    invoices, invoiced, outstanding = [], 0, 0
    if frappe.has_permission("Sales Invoice", "read"):
        invoices = frappe.get_list(
            "Sales Invoice", filters={"customer": customer, "docstatus": 1},
            fields=["name", "grand_total", "outstanding_amount", "status", "posting_date"],
            order_by="posting_date desc, creation desc", limit_page_length=8)
        # الإجماليان من كل فواتير العميل المعتمدة، لا من الثماني المعروضة:
        # نسخة سابقة جمعت ما جلبته للعرض فقط (آخر عشر، بمسوداتها وملغاتها)،
        # فأخطأ الرقم عند أول عميل له أكثر من عشر فواتير.
        row = frappe.db.sql(
            """select sum(base_grand_total), sum(outstanding_amount)
               from `tabSales Invoice` where docstatus = 1 and customer = %s""", customer)
        invoiced, outstanding = flt(row[0][0]), flt(row[0][1])

    return {"customer": doc, "vehicles": vehicles, "work_cards": cards,
            "invoices": invoices, "invoiced": invoiced, "outstanding": outstanding,
            "paid": invoiced - outstanding,
            "currency": frappe.db.get_default("currency")}


@frappe.whitelist()
def user_roles(users):
    """أدوار كل مستخدم في قائمة المستخدمين — طلب واحد للصفحة كلها.

    المسمّيات الوظيفية وحدها (roles.JOB_ROLES): الأدوار القياسية التي يحملها
    المسمّى تفصيل داخلي لا يُعرض. Administrator يحمل كل الأدوار بحكم تعريفه؛
    يُعاد "*" بدل سردها.
    """
    frappe.has_permission("User", "read", throw=True)
    users = [u for u in frappe.parse_json(users) or [] if isinstance(u, str)][:500]
    out = {u: [] for u in users}
    for row in frappe.get_all(
            "Has Role",
            filters={"parenttype": "User", "parent": ["in", users],
                     "role": ["in", roles.JOB_ROLES]},
            fields=["parent", "role"], order_by="parent, idx"):
        out[row.parent].append(row.role)
    if "Administrator" in out:
        out["Administrator"] = "*"
    return out


@frappe.whitelist(methods=["POST"])
def add_user(full_name, email, password, job_roles):
    """ينشئ مستخدماً في خطوة واحدة: الاسم، البريد، كلمة المرور، والمسمّى الوظيفي.

    نموذج المستخدم القياسي يطلب البريد والاسم، ثم — بعد الحفظ — الأدوار في
    تبويب ثانٍ وكلمة المرور في ثالث، ويرسل بريد ترحيب لا خادم له. هنا يُدخل
    مدير النظام الأربعة معاً ويخرج بحساب يعمل.

    لمدير النظام وحده. كلمة المرور تمرّ بسياسة القوة نفسها التي يطبّقها نموذج
    المستخدم. الأدوار القياسية التي يحملها المسمّى تُضاف عند الحفظ
    (roles.sync_implied).
    """
    frappe.only_for("System Manager")
    full_name = (full_name or "").strip()
    email = (email or "").strip().lower()
    chosen = [r for r in frappe.parse_json(job_roles) or [] if r in roles.JOB_ROLES]
    if not full_name or not email or not password:
        frappe.throw(frappe._("الاسم والبريد الإلكتروني وكلمة المرور مطلوبة"))
    if not chosen:
        frappe.throw(frappe._("اختر مسمّى وظيفياً واحداً على الأقل"))
    if frappe.db.exists("User", email):
        frappe.throw(frappe._("يوجد مستخدم بهذا البريد الإلكتروني: {0}").format(email))

    first, _sep, last = full_name.partition(" ")
    doc = frappe.get_doc({
        "doctype": "User", "email": email, "first_name": first, "last_name": last.strip(),
        "enabled": 1, "user_type": "System User", "send_welcome_email": 0,
        "language": frappe.db.get_single_value("System Settings", "language") or "ar",
        "new_password": password,
        "roles": [{"role": r} for r in chosen],
    })
    doc.flags.no_welcome_mail = True
    doc.insert()
    return {"name": doc.name, "full_name": doc.full_name}


@frappe.whitelist()
def item_info(item, warehouse=None):
    """اسم الصنف وسعر بيعه ورصيده — لتعبئة صف الخدمة أو القطعة في بطاقة العمل.

    كان اختيار صنف في البطاقة يترك اسمه وسعره فارغين ليُكتبا باليد من
    الذاكرة، وسعره مسجَّل في قائمة الأسعار.
    """
    frappe.has_permission("Item", "read", throw=True)
    row = frappe.db.get_value(
        "Item", item, ["item_name", "description", "is_stock_item", "stock_uom"], as_dict=True)
    if not row:
        return {}
    price_list = frappe.db.get_single_value("Selling Settings", "selling_price_list") \
        or "Standard Selling"
    rate = frappe.db.get_value(
        "Item Price", {"item_code": item, "price_list": price_list, "selling": 1},
        "price_list_rate")
    out = {"item_name": row.item_name, "rate": flt(rate), "is_stock_item": row.is_stock_item,
           "uom": row.stock_uom}
    if row.is_stock_item and warehouse:
        out["available"] = flt(frappe.db.get_value(
            "Bin", {"item_code": item, "warehouse": warehouse}, "actual_qty"))
    return out
