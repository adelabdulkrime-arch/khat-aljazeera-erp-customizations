# -*- coding: utf-8 -*-
"""Add the fields that make a Work Card's cost and margin visible.

Pairs with khat_workshop.costing, which fills them. Nothing here computes —
this only creates the fields and seeds indicative hourly costs so the feature
is usable the moment it lands rather than showing zeros until someone types
rates in by hand.

The costing fields are read-only and allow_on_submit: a card is locked after
submit, but its parts cost is only known once the Stock Entry exists, which
happens after submit. Without allow_on_submit the exact figure could never be
written and every card would keep its pre-submit estimate forever.
"""

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

# Indicative Omani workshop rates in OMR per hour, by trade. Starting figures
# for the owner to review — same status as the service prices and part costs.
HOURLY_COST = {
    "ميكانيكا": 2.500,
    "سمكرة": 3.000,
    "دهان": 3.000,
    "كهرباء": 2.750,
    "تكييف": 2.750,
}
DEFAULT_HOURLY_COST = 2.500


def _fields():
    money = {"fieldtype": "Currency", "read_only": 1, "allow_on_submit": 1}

    return {
        "Workshop Technician": [{
            "fieldname": "hourly_cost", "label": "تكلفة الساعة",
            "fieldtype": "Currency", "insert_after": "commission_rate",
            "description": "التكلفة الحقيقية للساعة على الورشة — لا سعر البيع",
        }],
        "Work Card Technician": [
            {"fieldname": "hours", "label": "ساعات العمل",
             "fieldtype": "Float", "insert_after": "task", "in_list_view": 1},
            {"fieldname": "hourly_cost", "label": "تكلفة الساعة",
             "fieldtype": "Currency", "insert_after": "hours",
             "fetch_from": "technician.hourly_cost", "fetch_if_empty": 1},
            {"fieldname": "labour_cost", "label": "تكلفة العمل",
             "fieldtype": "Currency", "insert_after": "hourly_cost",
             "read_only": 1, "in_list_view": 1},
        ],
        "Work Card": [
            {"fieldname": "sec_costing", "label": "التكلفة والربحية",
             "fieldtype": "Section Break", "insert_after": "grand_total",
             "collapsible": 1},
            {"fieldname": "labour_hours", "label": "إجمالي ساعات العمل",
             "fieldtype": "Float", "insert_after": "sec_costing",
             "read_only": 1, "allow_on_submit": 1},
            dict(money, fieldname="labour_cost", label="تكلفة العمالة",
                 insert_after="labour_hours"),
            dict(money, fieldname="commission_total", label="إجمالي العمولات",
                 insert_after="labour_cost"),
            dict(money, fieldname="parts_cost", label="تكلفة القطع (فعلية)",
                 insert_after="commission_total",
                 description="تقييم المخزون الفعلي للقطع المصروفة — لا سعر بيعها"),
            {"fieldname": "cb_costing", "fieldtype": "Column Break",
             "insert_after": "parts_cost"},
            dict(money, fieldname="total_cost", label="إجمالي التكلفة",
                 insert_after="cb_costing"),
            dict(money, fieldname="gross_profit", label="الربح الإجمالي",
                 insert_after="total_cost"),
            {"fieldname": "margin_pct", "label": "هامش الربح %",
             "fieldtype": "Percent", "insert_after": "gross_profit",
             "read_only": 1, "allow_on_submit": 1},
        ],
    }


def _seed_hourly_costs():
    """Give every technician a rate; never overwrite one already set."""
    filled = 0
    for name, spec, cost in frappe.get_all(
        "Workshop Technician",
        fields=["name", "specialization", "hourly_cost"], as_list=True
    ):
        if cost:
            continue
        frappe.db.set_value("Workshop Technician", name, "hourly_cost",
                            HOURLY_COST.get(spec, DEFAULT_HOURLY_COST))
        filled += 1
    return filled


def execute():
    create_custom_fields(_fields(), update=True)
    frappe.db.commit()

    filled = _seed_hourly_costs()
    frappe.db.commit()
    frappe.clear_cache()
    print("LABOUR_COSTING fields=ok technicians_rated=%d" % filled)
