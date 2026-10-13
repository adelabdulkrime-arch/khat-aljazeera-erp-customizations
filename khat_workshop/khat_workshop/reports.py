# -*- coding: utf-8 -*-
"""مرشّحات التقارير: ما يبقى ظاهراً منها. المصدر الوحيد.

تقارير ERPNext تعرض فوق الجدول كل مرشّح ممكن: «مديونيات العملاء» خمسة وعشرون،
«دفتر الأستاذ العام» أربعة وعشرون — دفاتر مالية متعددة، عملة العرض، أبعاد
محاسبية، شركاء مبيعات، دفاتر إعادة تقييم. صاحب ورشة يريد من التقرير: أي فترة،
وأي عميل أو صنف أو حساب.

لكل تقرير هنا المرشّحات التي تبقى، بأسمائها في تعريف التقرير. الباقي يُخفى
ويحتفظ بقيمته الافتراضية (public/js/kaj_reports.js) — التقرير يُحسب كما كان.
تقرير غير مذكور يُعرض بمرشّحاته كلها.

اسم مرشّح هنا لم يعد في تعريف تقريره (غيّره تحديث) لا يكسر شيئاً: يبقى التقرير
بما وُجد من القائمة. `tools/desk-check` (سيناريو reports) يفتح كل تقرير ويعدّ
مرشّحاته الظاهرة.
"""

PERIOD = ["filter_based_on", "period_start_date", "period_end_date",
          "from_fiscal_year", "to_fiscal_year", "periodicity"]

REPORTS = {
    # ── المبيعات والمشتريات ──
    "Sales Analytics": ["tree_type", "doc_type", "value_quantity", "from_date", "to_date",
                        "range"],
    "Purchase Analytics": ["tree_type", "doc_type", "value_quantity", "from_date",
                           "to_date", "range"],
    "Accounts Receivable": ["report_date", "party_type", "party", "ageing_based_on",
                            "group_by_party"],
    "Accounts Payable": ["report_date", "party_type", "party", "ageing_based_on",
                         "group_by_party"],

    # ── المخزون ──
    "Stock Balance": ["from_date", "to_date", "item_group", "item_code", "warehouse",
                      "include_zero_stock_items"],
    "Stock Ledger": ["from_date", "to_date", "warehouse", "item_code", "item_group",
                     "voucher_no"],
    "Stock Projected Qty": ["warehouse", "item_code", "item_group", "brand"],

    # ── المحاسبة ──
    "General Ledger": ["from_date", "to_date", "account", "voucher_no", "party_type",
                       "party", "categorize_by", "show_remarks"],
    "Trial Balance": ["fiscal_year", "from_date", "to_date", "show_zero_values",
                      "show_group_accounts"],
    "Profit and Loss Statement": PERIOD + ["accumulated_values"],
    "Balance Sheet": PERIOD + ["accumulated_values"],
    "Cash Flow": PERIOD,
}

# أعمدة تُخفى: ما أُخفي حقله في النماذج (forms.py) لا يعود عموداً في التقرير.
# "*" لكل التقارير.
HIDDEN_COLUMNS = {
    "*": ["cost_center", "project", "company", "finance_book"],
    "Accounts Receivable": ["currency", "po_no", "territory", "customer_group",
                            "customer_primary_contact"],
    "Accounts Payable": ["currency", "supplier_group"],
    "Stock Projected Qty": ["planned_qty", "reserved_qty_for_production",
                            "reserved_qty_for_production_plan",
                            "reserved_qty_for_sub_contract", "reserved_qty_for_pos"],
    "General Ledger": ["voucher_subtype", "against_voucher_type", "against_voucher"],
}


def for_boot():
    return {"filters": REPORTS, "hidden_columns": HIDDEN_COLUMNS}
