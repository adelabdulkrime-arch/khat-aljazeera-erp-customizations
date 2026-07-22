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

# The five service lines the workshop actually operates. Leading blank so the
# field starts unset rather than silently defaulting every job to Mechanical.
SERVICE_LINES = "\n".join([
    "",
    "ميكانيكا",
    "سمكرة وحوادث",
    "دهان",
    "كهرباء",
    "تكييف",
])

WORK_CARD_STOCK_SCRIPT = """
if not doc.stock_entry:
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
		# db_set, not attribute assignment: On Submit runs after the document is
		# written, so a plain assignment would never persist.
		doc.db_set("stock_entry", se.name)
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




WORK_CARD_CANCEL_SCRIPT = """
if doc.stock_entry and frappe.db.exists("Stock Entry", doc.stock_entry):
	se = frappe.get_doc("Stock Entry", doc.stock_entry)
	if se.docstatus == 1:
		se.cancel()
		frappe.msgprint("تم عكس صرف قطع الغيار من المخزون: %s" % se.name)
	doc.db_set("stock_entry", None)
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
        current = frappe.db.get_value(
            "Server Script", name, ["doctype_event", "reference_doctype"], as_dict=True
        )
        # Frappe will not let doctype_event change on an existing Server Script —
        # assigning it and saving silently keeps the old value, so the new body
        # kept running on the old event. Verified on the live system: repeated
        # saves left the trigger on Before Save. Recreate instead of update.
        if current.doctype_event != event or current.reference_doctype != doctype:
            frappe.delete_doc("Server Script", name, force=1, ignore_permissions=True)
            print("Recreating Server Script %s: event %s -> %s"
                  % (name, current.doctype_event, event))
        else:
            doc = frappe.get_doc("Server Script", name)
            doc.script = script
            doc.disabled = 0
            doc.save(ignore_permissions=True)
            print("Updated Server Script: %s (event=%s)" % (name, event))
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

    # Workshop context ON the native documents. Users now raise a real Quotation
    # and a real Sales Invoice; these fields carry the workshop link that the
    # retired shadow doctypes used to hold.
    for dt, after in (("Sales Invoice", "customer"), ("Quotation", "party_name")):
        _ensure_custom_field(dt, "work_card", "بطاقة العمل", "Link", "Work Card", insert_after=after, read_only=0)
        _ensure_custom_field(dt, "vehicle", "المركبة", "Link", "Customer Vehicle", insert_after="work_card", read_only=0)

    # Service line — audit finding #2.
    #
    # Nothing distinguished Mechanical / Body / Paint / Electrical / HVAC, so
    # profit per department was impossible to calculate — the single most
    # important management figure in a multi-discipline workshop.
    #
    # Added now, deliberately, while Work Card and Sales Invoice hold ZERO
    # documents: today it is one field, after a thousand job cards it is a data
    # migration. Placed on the invoice as well as the job card so revenue can be
    # grouped by department without joining back through the workshop.
    _ensure_custom_field("Work Card", "service_line", "خط الخدمة", "Select",
                         SERVICE_LINES, insert_after="status", read_only=0)
    for dt in ("Sales Invoice", "Quotation"):
        _ensure_custom_field(dt, "service_line", "خط الخدمة", "Select",
                             SERVICE_LINES, insert_after="vehicle", read_only=0)

    # Parts are issued AFTER SUBMIT, not on a status change.
    #
    # Previously any user could set the status to "جاهزة للتسليم" and that alone
    # fired a real, submitted, irreversible Stock Entry — with no approval gate,
    # and reverting the status did NOT reverse the stock. Submitting is now the
    # deliberate act of approval, and Frappe locks the document once submitted.
    #
    # It also fixes a structural defect: the old script called submit() from
    # inside Before Save, so a later validation failure could leave a submitted
    # Stock Entry orphaned against an unsaved Work Card.
    _ensure_server_script("Work Card Issue Parts On Ready", "Work Card", "After Submit", WORK_CARD_STOCK_SCRIPT)

    # Cancelling the Work Card reverses the stock movement, closing the
    # phantom-stock hole the audit flagged as the highest-risk mechanism.
    _ensure_server_script("Work Card Reverse Parts On Cancel", "Work Card", "After Cancel", WORK_CARD_CANCEL_SCRIPT)

    # Retire the mirroring scripts. They existed only to copy the shadow
    # documents into real ones; with users working directly in Sales Invoice and
    # Payment Entry there is nothing left to mirror — and with it goes the whole
    # class of bugs it carried: no tax on the generated invoice, every line
    # collapsed to WORKSHOP-SERVICE, no cancellation handling, and submit()
    # inside Before Save leaving orphaned submitted documents.
    for stale in ("Repair Invoice Create Sales Invoice",
                  "Workshop Payment Create Payment Entry",
                  "Update Invoice On Payment",
                  "Update Invoice On Payment Delete"):
        if frappe.db.exists("Server Script", stale):
            frappe.delete_doc("Server Script", stale, force=1, ignore_permissions=True)
            print("removed Server Script:", stale)

    frappe.db.commit()
    frappe.clear_cache()
    print("GL_STOCK_INTEGRATION_DONE default_warehouse=%s" % default_warehouse)
