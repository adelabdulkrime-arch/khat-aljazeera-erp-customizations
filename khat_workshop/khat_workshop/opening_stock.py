# -*- coding: utf-8 -*-
"""الرصيد الافتتاحي للصنف يُقيَّد رصيداً افتتاحياً، لا ربحاً.

حوار «صنف جديد» يأخذ «رصيد افتتاحي»، وERPNext يحوّله إلى حركة «استلام مواد»
عادية طرفها الآخر «تسويات المخزون» — حساب مصروفات. فكل قطعة يُدخَل رصيدها عند
بدء العمل تُنقص مصروفات الفترة بقيمتها: ورشة تُدخل مخزوناً قيمته خمسة آلاف ريال
ترى في قائمة الدخل ربحاً زائداً بخمسة آلاف لم تكسبه.

الصواب المحاسبي أن الطرف الآخر حساب الافتتاح المؤقت، والحركة موسومة «رصيد
افتتاحي»: تظهر في المركز المالي ولا تمسّ قائمة الدخل. فتُؤخذ الكمية هنا قبل أن
يراها ERPNext (before_insert) وتُقيَّد بهذه الصورة بعد إنشاء الصنف (after_insert).
"""

import frappe
from frappe import _
from frappe.utils import flt, getdate, nowtime


def hold(doc, method=None):
    """Item.before_insert: الكمية تُرفع عن الحقل، فلا يقيّدها ERPNext بطريقته."""
    if not flt(doc.get("opening_stock")):
        return
    if not doc.is_stock_item or doc.has_serial_no or doc.has_batch_no:
        return
    doc.flags.kaj_opening_stock = flt(doc.opening_stock)
    doc.opening_stock = 0


def post(doc, method=None):
    """Item.after_insert: حركة استلام موسومة «رصيد افتتاحي» على حساب الافتتاح المؤقت."""
    qty = doc.flags.get("kaj_opening_stock")
    if not qty:
        return
    if doc.valuation_rate is None and not doc.is_customer_provided_item:
        frappe.throw(_("Valuation Rate is mandatory if Opening Stock entered"))

    from erpnext.stock.doctype.stock_entry.stock_entry_utils import make_stock_entry

    for default in doc.item_defaults or [frappe._dict({"company": frappe.defaults.get_defaults().company})]:
        warehouse = default.default_warehouse or frappe.db.get_single_value("Stock Settings", "default_warehouse")
        if not warehouse or frappe.db.get_value("Warehouse", warehouse, "company") != default.company:
            continue
        account = frappe.db.get_value(
            "Account", {"company": default.company, "account_type": "Temporary", "is_group": 0}, "name")
        entry = make_stock_entry(
            item_code=doc.name, target=warehouse, qty=qty, rate=flt(doc.valuation_rate),
            company=default.company, posting_date=getdate(), posting_time=nowtime(),
            # بلا حساب افتتاح (دليل حسابات عُدِّل) تبقى الحركة كما يقيّدها ERPNext
            is_opening="Yes" if account else "No", expense_account=account,
            do_not_save=True,
        )
        if not flt(doc.valuation_rate):
            for row in entry.items:
                row.allow_zero_valuation_rate = 1
        entry.insert()
        entry.submit()
        entry.add_comment("Comment", _("Opening Stock"))
        frappe.msgprint(
            _("Opening Stock entry created: {0}").format(frappe.utils.get_link_to_form("Stock Entry", entry.name)),
            alert=True,
        )
    doc.db_set("opening_stock", qty, update_modified=False)
