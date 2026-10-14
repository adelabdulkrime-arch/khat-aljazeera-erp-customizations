# -*- coding: utf-8 -*-
"""فاتورة مشتريات تُدخل القطع إلى المخزن: بلا رسالة «تغيّر حساب المصروف».

مع «تحديث المخزون» يقيَّد بند الصنف المخزني على حساب المخزون، لا على حساب
المصروفات الذي يملأ به النموذج البند. ERPNext يبدّل الحساب عند الحفظ ويعرض في كل
مرة نافذة: «Row 1: Expense Head changed to … because account … is not linked to
warehouse …» — رسالة محاسبية عن حقل لا يراه من يُدخل الفاتورة، عليه أن يغلقها مع
كل فاتورة.

الحساب يُضبط هنا قبل التحقق (before_validate) بالطريقة نفسها التي يحسبه بها
ERPNext، فلا يجد ما يبدّله ولا ما يقوله.
"""

import frappe


def inventory_expense_head(doc, method=None):
    if not doc.get("update_stock") or doc.get("is_opening") == "Yes":
        return
    try:
        import erpnext

        if not erpnext.is_perpetual_inventory_enabled(doc.company):
            return
        stock_items = doc.get_stock_items()
        accounts = doc.get_inventory_account_map()
        default = frappe.db.get_single_value("Stock Settings", "default_warehouse")
        for row in doc.get("items") or []:
            if row.item_code not in stock_items or row.get("from_warehouse") or row.get("is_fixed_asset"):
                continue
            # حُفظت الفاتورة قبل أن يجلب النموذج مخزن البند (اتصال بطيء): يُملأ
            # كما يملؤه ERPNext في التحقق، وإلا قيل «تغيّر حساب المصروف» على أي حال.
            if not row.warehouse:
                row.warehouse = (doc.get("set_warehouse") or frappe.db.get_value(
                    "Item Default", {"parent": row.item_code, "company": doc.company},
                    "default_warehouse") or default)
            if row.warehouse:
                account = (doc.get_inventory_account_dict(row, accounts) or {}).get("account")
                if account:
                    row.expense_account = account
    except Exception:
        # ما تعذّر هنا يضبطه ERPNext في التحقق، ويقول ما فعل
        frappe.clear_messages()
