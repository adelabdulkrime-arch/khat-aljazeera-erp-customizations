# -*- coding: utf-8 -*-
"""تنظيف النظام قبل تسليمه: يبدأ العميل على نظام لم يُدخَل فيه شيء.

أثناء البناء زُرعت بيانات نموذجية ليُجرَّب النظام عليها: 18 قطعة غيار برصيد
افتتاحي قيمته 3,815 ر.ع. مسجّلة في المخزون والحسابات، 30 خدمة وعملية بأسعار
مفترضة، ورقم ضريبي وهاتف وعنوان مبدئية في إعدادات الورشة. عميل يبدأ عليها
يبدأ دفاتره برصيد مخزون لا وجود له، ويطبع فواتيره برقم ضريبي ليس رقمه.

`clean` يزيل ذلك كله ويُبقي ما هو إعداد لا بيانات: الشركة ودليل الحسابات
وقالب الضريبة، المستودعات ووحدات القياس ومجموعات الأصناف، حالات بطاقة العمل
وقائمة الفحص وماركات المركبات وموديلاتها، قوالب الطباعة، الأدوار.

لا يعمل إلا على نظام لم تُسجَّل فيه معاملة حقيقية: إن وُجد عميل أو بطاقة عمل
أو فاتورة أو سند، أو حركة مخزون غير الرصيد الافتتاحي النموذجي، يتوقف دون أن
يمسّ شيئاً. ويُطلب اسم الموقع صراحةً، فلا يُشغَّل على موقع بالخطأ.

    bench --site <site> execute khat_workshop.handover.export_catalogue
    bench --site <site> execute khat_workshop.handover.clean --kwargs "{'site': '<site>'}"

البيانات النموذجية لا تعود مع النشر التالي: خطوات زرعها تعمل فقط حيث
`kaj_demo_data` مفعّل في إعدادات الموقع (setup.demo_data_enabled).
"""

import json

import frappe

from khat_workshop.setup import workshop_seed_parts

# مجموعات الأصناف التي زرعتها خطوات الإعداد. صنفان في «Services» يعتمد عليهما
# الكود (SRV-INSPECTION، WORKSHOP-SERVICE) ليسا منها ويبقيان.
DEMO_ITEM_GROUPS = ("قطع غيار", "خدمات الورشة", "عمليات الاستبدال")

# ما وجوده يعني أن النظام استُعمل فعلاً
REAL_DATA = (
    "Customer", "Supplier", "Customer Vehicle", "Work Card", "Quotation", "Sales Order",
    "Delivery Note", "Sales Invoice", "Payment Entry", "Journal Entry", "Material Request",
    "Purchase Order", "Purchase Receipt", "Purchase Invoice", "Stock Reconciliation",
    "Workshop Technician", "Commission Log", "Maintenance Reminder",
)

# عدّادات ترقيم تقدّمت بالتجارب؛ يبدأ العميل من الرقم 1
SERIES = ("WC-", "WQ-", "WI-", "MAT-STE-", "MAT-SLE-", "ACC-GLE-", "ACC-SINV-", "ACC-PINV-",
          "ACC-PAY-", "ACC-JV-", "SAL-QTN-", "SAL-ORD-", "PUR-ORD-", "MAT-PRE-", "MAT-DN-",
          "MAT-MR-", "MAT-RECO-", "SRV-")

# ما كانت خطوة الإعداد تملؤه بقيم مبدئية
SETTINGS_FIELDS = ("tax_number", "phone", "address")

# سجلات تراكمت من البناء والتجربة، لا من عمل العميل
LOGS = ("Activity Log", "Access Log", "Error Log", "Route History", "Notification Log",
        "Email Queue", "Deleted Document", "Scheduled Job Log", "View Log")


def _demo_items():
    return frappe.get_all(
        "Item", filters={"item_group": ["in", DEMO_ITEM_GROUPS]},
        fields=["name", "item_name", "item_group", "stock_uom", "is_stock_item", "valuation_rate"],
        order_by="item_group, name")


def export_catalogue():
    """الأصناف النموذجية بأسعارها وأرصدتها، JSON على الخرج — تُحفظ قبل الحذف."""
    rows = []
    for item in _demo_items():
        price = frappe.db.get_value(
            "Item Price", {"item_code": item.name, "selling": 1}, "price_list_rate")
        qty = frappe.db.sql(
            "select sum(actual_qty) from `tabBin` where item_code = %s", item.name)[0][0]
        rows.append({
            "item_code": item.name, "item_name": item.item_name, "item_group": item.item_group,
            "stock_uom": item.stock_uom, "is_stock_item": item.is_stock_item,
            "selling_rate": price or 0, "cost": item.valuation_rate or 0, "qty": qty or 0,
        })
    print("CATALOGUE_JSON " + json.dumps(rows, ensure_ascii=False))
    return rows


def _remove_orphan_drafts():
    """مسودات عروض سعر لعميل لم يعد موجوداً: بقايا فحص تشغيلي، لا عمل عميل."""
    removed = 0
    for q in frappe.get_all("Quotation", filters={"docstatus": 0}, fields=["name", "party_name"]):
        if not q.party_name or not (frappe.db.exists("Customer", q.party_name)
                                    or frappe.db.exists("Lead", q.party_name)):
            frappe.delete_doc("Quotation", q.name, force=1, ignore_permissions=True)
            removed += 1
    return removed


def _refuse_if_in_use():
    found = ["%s (%d)" % (dt, frappe.db.count(dt)) for dt in REAL_DATA
             if frappe.db.exists("DocType", dt) and frappe.db.count(dt)]
    other_stock = frappe.db.count("Stock Entry", {"remarks": ["!=", workshop_seed_parts.OPENING_REMARK]}) \
        + frappe.db.count("Stock Entry", {"remarks": ["is", "not set"]})
    if other_stock:
        found.append("Stock Entry غير الرصيد النموذجي (%d)" % other_stock)
    if found:
        frappe.throw("النظام فيه بيانات فعلية، لن يُنظَّف: " + "، ".join(found))


def _remove_opening_stock():
    removed = 0
    for name in frappe.get_all(
            "Stock Entry", filters={"remarks": workshop_seed_parts.OPENING_REMARK}, pluck="name"):
        doc = frappe.get_doc("Stock Entry", name)
        if doc.docstatus == 1:
            doc.flags.ignore_permissions = True
            doc.cancel()
        # الإلغاء يعكس القيد ويُبقي السطرين في الدفاتر ملغيَّين؛ نظام لم يبدأ
        # لا يحمل في دفتره قيداً ملغى لبضاعة لم توجد
        for ledger in ("GL Entry", "Stock Ledger Entry", "Repost Item Valuation"):
            frappe.db.delete(ledger, {"voucher_no": name})
        frappe.delete_doc("Stock Entry", name, force=1, ignore_permissions=True)
        removed += 1
    return removed


def _remove_items():
    codes = [item.name for item in _demo_items()]
    if not codes:
        return 0
    frappe.db.delete("Bin", {"item_code": ["in", codes]})
    frappe.db.delete("Item Price", {"item_code": ["in", codes]})
    for code in codes:
        frappe.delete_doc("Item", code, force=1, ignore_permissions=True)
    return len(codes)


def _clear_settings():
    doc = frappe.get_single("Workshop Settings")
    cleared = [f for f in SETTINGS_FIELDS if doc.meta.has_field(f) and doc.get(f)]
    for field in cleared:
        doc.set(field, None)
    if cleared:
        doc.flags.ignore_permissions = True
        doc.save()
    return cleared


def _reset_series():
    reset = 0
    for name, current in frappe.db.sql("select name, current from `tabSeries` where current > 0"):
        if name.startswith(SERIES):
            frappe.db.sql("update `tabSeries` set current = 0 where name = %s", name)
            reset += 1
    return reset


def _clear_logs():
    cleared = {}
    for doctype in LOGS:
        if frappe.db.exists("DocType", doctype):
            count = frappe.db.count(doctype)
            if count:
                frappe.db.delete(doctype)
                cleared[doctype] = count
    # تعليقات «حُذف» التي يتركها الإطار عن كل مستند حُذف أثناء البناء
    deleted = frappe.db.count("Comment", {"comment_type": "Deleted"})
    if deleted:
        frappe.db.delete("Comment", {"comment_type": "Deleted"})
        cleared["Comment (Deleted)"] = deleted
    return cleared


def _remove_orphan_contacts():
    removed = 0
    for contact in frappe.get_all("Contact", fields=["name", "user"]):
        linked = frappe.db.count("Dynamic Link", {"parenttype": "Contact", "parent": contact.name})
        if not contact.user and not linked:
            frappe.delete_doc("Contact", contact.name, force=1, ignore_permissions=True)
            removed += 1
    # جهة اتصال قديمة بقيت باسم الحساب السابق لمدير الورشة
    for name in frappe.get_all("Contact", filters={"email_id": "admin@khataljazeera.om"}, pluck="name"):
        frappe.delete_doc("Contact", name, force=1, ignore_permissions=True)
        removed += 1
    return removed


def clean(site=None):
    """ينظّف النظام للتسليم. `site` يجب أن يطابق اسم الموقع الجاري."""
    if site != frappe.local.site:
        frappe.throw("مرّر اسم الموقع صراحةً: site='%s'" % frappe.local.site)
    orphans = _remove_orphan_drafts()
    try:
        _refuse_if_in_use()
    except Exception:
        frappe.db.rollback()
        raise

    result = {
        "orphan_draft_quotations": orphans,
        "opening_stock_entries": _remove_opening_stock(),
        "items": _remove_items(),
        "settings_cleared": _clear_settings(),
        "contacts": _remove_orphan_contacts(),
        "series_reset": _reset_series(),
        "logs": _clear_logs(),
    }
    frappe.db.commit()
    frappe.clear_cache()

    left = {
        "Item": frappe.db.count("Item"),
        "Item Price": frappe.db.count("Item Price"),
        "Stock Entry": frappe.db.count("Stock Entry"),
        "GL Entry": frappe.db.count("GL Entry"),
        "Stock Ledger Entry": frappe.db.count("Stock Ledger Entry"),
        "Bin": frappe.db.count("Bin"),
    }
    print("HANDOVER_CLEAN " + json.dumps(result, ensure_ascii=False))
    print("HANDOVER_LEFT " + json.dumps(left, ensure_ascii=False))
    return result
