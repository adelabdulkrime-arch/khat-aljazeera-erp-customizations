# -*- coding: utf-8 -*-
"""Wire the Workshop module into REAL ERPNext accounting and stock, closing
the two Critical gaps from the production-readiness audit:

  1. Work Card parts never decremented real stock -> now auto-creates a
     real Stock Entry (Material Issue) the moment a Work Card's status is
     set to "جاهزة للتسليم" (ready for delivery), for every part row that
     has a valid linked Item.

  2. Repair Invoice / Workshop Payment were a shadow bookkeeping system,
     disconnected from the General Ledger -> now auto-creates a real Sales
     Invoice (mirroring line items) the first time a Repair Invoice is
     saved with items+total, and a real Payment Entry (allocated against
     that Sales Invoice) every time a Workshop Payment is recorded.

Known simplification (documented, not hidden): once the linked Sales
Invoice/Stock Entry is created, later edits to the Repair Invoice/Work Card
do NOT sync forward automatically -- this is a one-time bridge, not a live
two-way sync. Reversal/cancellation flows are not handled in this first pass.
"""
import frappe

SERVICE_ITEM_CODE = "WORKSHOP-SERVICE"
SERVICE_ITEM_NAME = "خدمة إصلاح ورشة"
DEFAULT_WAREHOUSE_NAME_LIKE = "%مخازن%"

WORK_CARD_STOCK_SCRIPT = """
if doc.status == "جاهزة للتسليم" and not doc.stock_entry:
	valid_rows = [p for p in (doc.parts or []) if p.item and p.qty]
	if valid_rows and doc.warehouse:
		company = frappe.db.get_single_value("Global Defaults", "default_company")
		se = frappe.get_doc({
			"doctype": "Stock Entry",
			"stock_entry_type": "Material Issue",
			"company": company,
			"posting_date": frappe.utils.nowdate(),
			"items": [
				{"item_code": p.item, "qty": p.qty, "s_warehouse": doc.warehouse}
				for p in valid_rows
			],
		})
		se.insert(ignore_permissions=True)
		se.submit()
		doc.stock_entry = se.name
		skipped = len(doc.parts or []) - len(valid_rows)
		if skipped:
			frappe.msgprint(
				"تم صرف %d قطعة من المخزون. تم تجاهل %d صف بدون صنف مرتبط أو كمية." % (len(valid_rows), skipped)
			)
		else:
			frappe.msgprint("تم صرف قطع الغيار من المستودع تلقائياً: %s" % se.name)
	elif valid_rows and not doc.warehouse:
		frappe.msgprint(
			"تنبيه: توجد %d قطعة مرتبطة بصنف حقيقي لكن لم يتم تحديد المستودع - لم يتم خصم أي شيء من المخزون. حدد المستودع واحفظ مجدداً." % len(valid_rows)
		)
"""

REPAIR_INVOICE_SI_SCRIPT = """
if not doc.sales_invoice and doc.customer and doc.items and (doc.grand_total or 0) > 0:
	company = frappe.db.get_single_value("Global Defaults", "default_company")
	si = frappe.get_doc({
		"doctype": "Sales Invoice",
		"customer": doc.customer,
		"company": company,
		"posting_date": doc.date or frappe.utils.nowdate(),
		"due_date": doc.date or frappe.utils.nowdate(),
		"items": [
			{
				"item_code": "WORKSHOP-SERVICE",
				"item_name": row.description or "خدمة إصلاح ورشة",
				"description": row.description or "خدمة إصلاح ورشة",
				"qty": row.qty or 1,
				"rate": row.rate if row.rate else ((row.amount or 0) / (row.qty or 1)),
			}
			for row in doc.items
		],
		"discount_amount": doc.discount or 0,
		"apply_discount_on": "Grand Total",
		"remarks": "فاتورة مبيعات مُنشأة تلقائياً من فاتورة الإصلاح %s" % doc.name,
	})
	si.insert(ignore_permissions=True)
	si.submit()
	doc.sales_invoice = si.name
	frappe.msgprint("تم إنشاء فاتورة مبيعات حقيقية مرتبطة: %s" % si.name)
"""

WORKSHOP_PAYMENT_PE_SCRIPT = """
if doc.invoice:
	sales_invoice = frappe.db.get_value("Repair Invoice", doc.invoice, "sales_invoice")
	if sales_invoice and frappe.db.exists("Sales Invoice", sales_invoice):
		si = frappe.get_doc("Sales Invoice", sales_invoice)
		outstanding = si.outstanding_amount
		if outstanding and outstanding > 0:
			pay_amount = min(doc.amount or 0, outstanding)
			if doc.amount and doc.amount > outstanding:
				frappe.msgprint(
					"تنبيه: المبلغ المدخل (%s) أكبر من المتبقي فعلياً على الفاتورة (%s). تم تسجيل %s فقط في سند القبض الحقيقي؛ راجع الفرق يدوياً." % (doc.amount, outstanding, pay_amount)
				)
			company = frappe.db.get_single_value("Global Defaults", "default_company")
			receivable_account = frappe.db.get_value("Company", company, "default_receivable_account")
			paid_to = None
			if doc.mode_of_payment:
				paid_to = frappe.db.get_value(
					"Mode of Payment Account",
					{"parent": doc.mode_of_payment, "company": company},
					"default_account",
				)
			if not paid_to:
				paid_to = frappe.db.get_value(
					"Account", {"company": company, "account_type": "Cash", "is_group": 0}, "name"
				)
			currency = frappe.db.get_value("Company", company, "default_currency")
			pe = frappe.get_doc({
				"doctype": "Payment Entry",
				"payment_type": "Receive",
				"party_type": "Customer",
				"party": doc.customer,
				"company": company,
				"mode_of_payment": doc.mode_of_payment,
				"paid_from": receivable_account,
				"paid_to": paid_to,
				"paid_from_account_currency": currency,
				"paid_to_account_currency": currency,
				"source_exchange_rate": 1,
				"target_exchange_rate": 1,
				"posting_date": doc.date or frappe.utils.nowdate(),
				"paid_amount": pay_amount,
				"received_amount": pay_amount,
				"reference_no": doc.reference or doc.name,
				"reference_date": doc.date or frappe.utils.nowdate(),
				"references": [{
					"reference_doctype": "Sales Invoice",
					"reference_name": si.name,
					"allocated_amount": pay_amount,
				}],
			})
			pe.insert(ignore_permissions=True)
			pe.submit()
			doc.db_set("payment_entry", pe.name)
		else:
			frappe.msgprint(
				"تنبيه: فاتورة المبيعات المرتبطة مسددة بالكامل بالفعل - لم يتم إنشاء سند قبض حقيقي لهذه الدفعة. تحقق من صحة المبلغ المدخل."
			)
"""


def _ensure_service_item():
    if not frappe.db.exists("Item", SERVICE_ITEM_CODE):
        frappe.get_doc({
            "doctype": "Item",
            "item_code": SERVICE_ITEM_CODE,
            "item_name": SERVICE_ITEM_NAME,
            "item_group": "Services",
            "is_stock_item": 0,
            "stock_uom": "Nos",
        }).insert(ignore_permissions=True)
        print("Created service item:", SERVICE_ITEM_CODE)


def _ensure_custom_field(doctype, fieldname, label, fieldtype="Link", options=None, insert_after=None, read_only=1, default=None):
    name = "%s-%s" % (doctype, fieldname)
    if frappe.db.exists("Custom Field", name):
        return
    cf = frappe.get_doc({
        "doctype": "Custom Field",
        "dt": doctype,
        "fieldname": fieldname,
        "label": label,
        "fieldtype": fieldtype,
        "options": options,
        "insert_after": insert_after,
        "read_only": read_only,
        "default": default,
    })
    cf.insert(ignore_permissions=True)
    print("Created Custom Field:", name)


def _ensure_server_script(name, doctype, event, script):
    if frappe.db.exists("Server Script", name):
        doc = frappe.get_doc("Server Script", name)
        doc.script = script
        doc.save(ignore_permissions=True)
        print("Updated Server Script:", name)
        return
    frappe.get_doc({
        "doctype": "Server Script",
        "name": name,
        "script_type": "DocType Event",
        "reference_doctype": doctype,
        "doctype_event": event,
        "script": script,
        "disabled": 0,
    }).insert(ignore_permissions=True)
    print("Created Server Script:", name)


def execute():
    _ensure_service_item()

    default_warehouse = frappe.db.get_value(
        "Warehouse", {"warehouse_name": ["like", DEFAULT_WAREHOUSE_NAME_LIKE]}, "name"
    )

    _ensure_custom_field("Work Card", "warehouse", "المستودع (لصرف القطع)", "Link", "Warehouse", insert_after="sec_parts", read_only=0, default=default_warehouse)
    _ensure_custom_field("Work Card", "stock_entry", "حركة المخزون المرتبطة", "Link", "Stock Entry", insert_after="warehouse", read_only=1)
    _ensure_custom_field("Repair Invoice", "sales_invoice", "فاتورة المبيعات المرتبطة", "Link", "Sales Invoice", insert_after="grand_total", read_only=1)
    _ensure_custom_field("Workshop Payment", "payment_entry", "سند القبض المرتبط", "Link", "Payment Entry", insert_after="reference", read_only=1)

    _ensure_server_script("Work Card Issue Parts On Ready", "Work Card", "Before Save", WORK_CARD_STOCK_SCRIPT)
    _ensure_server_script("Repair Invoice Create Sales Invoice", "Repair Invoice", "Before Save", REPAIR_INVOICE_SI_SCRIPT)
    _ensure_server_script("Workshop Payment Create Payment Entry", "Workshop Payment", "After Insert", WORKSHOP_PAYMENT_PE_SCRIPT)

    frappe.db.commit()
    frappe.clear_cache()
    print("GL_STOCK_INTEGRATION_DONE default_warehouse=%s" % default_warehouse)
