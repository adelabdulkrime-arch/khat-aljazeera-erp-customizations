# -*- coding: utf-8 -*-
"""Service packages — a fixed bundle of services and parts sold at one price.

Mazoon's Packages screen lets a workshop predefine a bundle like "صيانة دورية
20 ألف" (oil, filters, labour) so the counter adds it to a job card in one
click instead of keying every line. It is one of the two operational features
our Workshop dashboard was missing.

Modelled as its own DocType rather than ERPNext's Product Bundle because a
workshop package carries things Product Bundle does not: an Arabic and an
English name, its own discount, and an active flag — exactly the columns Mazoon
shows. The line total and package total are filled by khat_workshop.packages on
save.

Applying a package to a Work Card (copying its lines in) is a deliberate next
step; this builds the master the counter picks from.
"""

import frappe

from khat_workshop.setup.workshop_setup import f, make_dt


def _doctypes():
    make_dt("Workshop Package Item", istable=1, fields=[
        f("item", "الصنف / الخدمة", "Link", options="Item", reqd=1,
          in_list_view=1, columns=4),
        f("item_name", "الاسم", "Data", fetch_from="item.item_name",
          read_only=1, in_list_view=1, columns=3),
        f("qty", "الكمية", "Float", default="1", in_list_view=1, columns=1),
        f("rate", "السعر", "Currency", in_list_view=1, columns=2),
        f("amount", "الإجمالي", "Currency", read_only=1, in_list_view=1, columns=2),
    ])

    make_dt(
        "Workshop Package",
        autoname="PKG-.#####",
        title_field="package_name",
        search_fields="package_name_en",
        fields=[
            f("package_name", "اسم الباقة (عربي)", "Data", reqd=1, in_list_view=1),
            f("package_name_en", "اسم الباقة (إنجليزي)", "Data", in_list_view=1),
            f("is_active", "مفعّلة", "Check", default="1", in_list_view=1),
            f("cb_pkg", "", "Column Break"),
            f("description", "الوصف", "Small Text"),
            f("sec_items", "البنود", "Section Break"),
            f("items", "البنود", "Table", options="Workshop Package Item"),
            f("sec_totals", "الإجماليات", "Section Break"),
            f("subtotal", "المجموع الفرعي", "Currency", read_only=1),
            f("discount_percentage", "نسبة الخصم %", "Percent"),
            f("cb_totals", "", "Column Break"),
            f("discount_amount", "قيمة الخصم", "Currency", read_only=1),
            f("total", "الإجمالي النهائي", "Currency", read_only=1, in_list_view=1),
        ],
    )


def execute():
    _doctypes()
    frappe.db.commit()
    frappe.clear_cache()
    print("PACKAGES doctypes=ok")
