# -*- coding: utf-8 -*-
"""Itemised print format for Sales Invoice / Quotation — second voice note,
2026-08-23.

The owner's exact complaint: the invoice/quotation handed to a customer (and
sometimes submitted to a government office) has to show the vehicle's plate
number, chassis number (VIN), date and time, followed by every operation
performed as its own line — not a single lump total. The default ERPNext
print format doesn't surface the workshop's custom `vehicle` field at all
(added by workshop_gl_stock_integration), so even with itemised Items
(workshop_replacement_operations) the vehicle identification he needs was
still missing from the printout.

Adds one custom, non-default Print Format per doctype (Sales Invoice,
Quotation) — chosen manually from the print dialog for now, rather than
forced as the system default, since that's a call the owner should make
after seeing it render on a real document. Deliberately built as a plain
Jinja/HTML format (not the print format builder) so it stays a single
readable file here, consistent with the rest of this repo.

Reads `doc.vehicle` (Link -> Customer Vehicle, already on both doctypes) to
pull plate number and chassis number; nothing new to fill in on the
Quotation/Sales Invoice form beyond what staff already select.
"""

import frappe

# __TITLE__ is swapped per-doctype in _html(); kept as plain string.replace
# rather than Python %/str.format() because the template itself is full of
# literal { } and % characters that Jinja needs untouched.
_TEMPLATE = u"""
<div style="direction: rtl; text-align: right;">
  <h3 style="text-align:center; margin-bottom: 14px;">__TITLE__</h3>

  {% set veh = frappe.db.get_value("Customer Vehicle", doc.vehicle,
      ["plate_number", "chassis_no", "brand", "model"], as_dict=True) if doc.get("vehicle") else None %}

  <table style="width:100%; margin-bottom:10px; font-size:0.95em;">
    <tr>
      <td style="width:50%;"><strong>العميل:</strong> {{ doc.customer_name or doc.customer }}</td>
      <td><strong>التاريخ:</strong> {{ frappe.utils.formatdate(doc.posting_date) }}
          &nbsp; <strong>الساعة:</strong> {{ doc.posting_time or "" }}</td>
    </tr>
    <tr>
      <td><strong>رقم اللوحة:</strong> {{ veh.plate_number if veh else "" }}</td>
      <td><strong>رقم الشاصي (VIN):</strong> {{ veh.chassis_no if veh else "" }}</td>
    </tr>
    <tr>
      <td colspan="2"><strong>المركبة:</strong>
        {{ ((veh.brand or "") ~ " " ~ (veh.model or "")) if veh else "" }}</td>
    </tr>
  </table>

  <table style="width:100%; border-collapse: collapse; font-size:0.95em;">
    <thead>
      <tr style="background:#eee;">
        <th style="border:1px solid #999; padding:4px;">#</th>
        <th style="border:1px solid #999; padding:4px;">العمل / القطعة</th>
        <th style="border:1px solid #999; padding:4px;">الكمية</th>
        <th style="border:1px solid #999; padding:4px;">السعر</th>
        <th style="border:1px solid #999; padding:4px;">الإجمالي</th>
      </tr>
    </thead>
    <tbody>
      {% for row in doc.items %}
      <tr>
        <td style="border:1px solid #999; padding:4px; text-align:center;">{{ loop.index }}</td>
        <td style="border:1px solid #999; padding:4px;">{{ row.item_name or row.description }}</td>
        <td style="border:1px solid #999; padding:4px; text-align:center;">{{ row.qty }}</td>
        <td style="border:1px solid #999; padding:4px; text-align:center;">{{ "%.3f"|format(row.rate or 0) }}</td>
        <td style="border:1px solid #999; padding:4px; text-align:center;">{{ "%.3f"|format(row.amount or 0) }}</td>
      </tr>
      {% endfor %}
    </tbody>
  </table>

  <table style="width:100%; margin-top:10px;">
    <tr>
      <td style="width:70%;"></td>
      <td style="text-align:left; font-weight:bold; font-size:1.15em;">
        الإجمالي: {{ "%.3f"|format(doc.grand_total or 0) }} {{ doc.currency or "" }}
      </td>
    </tr>
  </table>
</div>
"""

MODULE = "Khat Workshop"

FORMATS = [
    ("فاتورة تشغيل مفصّلة - خط الجزيرة", "Sales Invoice", "فاتورة إصلاح"),
    ("عرض سعر مفصّل - خط الجزيرة", "Quotation", "عرض سعر"),
]


def _html(title):
    return _TEMPLATE.replace("__TITLE__", title)


def _ensure_print_format(name, doctype, title):
    if frappe.db.exists("Print Format", name):
        doc = frappe.get_doc("Print Format", name)
        doc.html = _html(title)
        doc.save(ignore_permissions=True)
        return "updated"
    frappe.get_doc({
        "doctype": "Print Format",
        "name": name,
        "doc_type": doctype,
        "module": MODULE,
        "standard": "No",
        "custom_format": 1,
        "print_format_type": "Jinja",
        "disabled": 0,
        "html": _html(title),
    }).insert(ignore_permissions=True)
    return "created"


def execute():
    results = {}
    for name, doctype, title in FORMATS:
        results[doctype] = _ensure_print_format(name, doctype, title)
    frappe.db.commit()
    frappe.clear_cache()
    print("OPERATIONS_PRINT_FORMAT %s" % results)
