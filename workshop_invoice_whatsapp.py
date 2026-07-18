# -*- coding: utf-8 -*-
"""Generates a fresh public PDF copy of a Repair Invoice and returns its
public URL so it can be embedded in a WhatsApp message (wa.me links only
support pre-filled text, not attachments -- a link to the PDF is the closest
equivalent without a paid WhatsApp Business API integration)."""
import frappe
from frappe.utils.file_manager import save_file

PDF_PREFIX = "invoice-"


@frappe.whitelist()
def get_invoice_pdf_url(invoice):
    doc = frappe.get_doc("Repair Invoice", invoice)
    if not doc.has_permission("read"):
        frappe.throw(frappe._("ليس لديك صلاحية لعرض هذه الفاتورة"))

    # Regenerate every time (rather than reuse) so the PDF always reflects
    # the invoice's current amounts/status -- drop any previous copy first.
    old = frappe.get_all("File", filters={
        "attached_to_doctype": "Repair Invoice",
        "attached_to_name": invoice,
        "file_name": ["like", PDF_PREFIX + "%.pdf"],
    }, pluck="name")
    for f in old:
        frappe.delete_doc("File", f, ignore_permissions=True, force=1)

    # wkhtmltopdf runs inside this container and fetches the print page's
    # assets (css/images) over HTTP -- the site's configured host name isn't
    # resolvable from inside the container, and the backend's own gunicorn
    # (localhost:8000) doesn't serve /assets itself (that's nginx's job) --
    # only the "frontend" container, reachable via Docker's internal DNS,
    # serves both dynamic pages and static assets. Only used for the render
    # step; the link handed back to the customer is built separately.
    original_host = frappe.local.conf.get("host_name")
    frappe.local.conf.host_name = "http://frontend:8080"
    try:
        pdf = frappe.get_print("Repair Invoice", invoice, as_pdf=True)
    finally:
        if original_host is None:
            frappe.local.conf.pop("host_name", None)
        else:
            frappe.local.conf.host_name = original_host

    file_doc = save_file(
        PDF_PREFIX + invoice.replace("/", "-") + ".pdf", pdf,
        "Repair Invoice", invoice, is_private=0,
    )
    frappe.db.commit()

    # frappe.utils.get_url() resolves to the internal site name ("erp.local"),
    # which isn't a real, externally-reachable address -- neither the staff's
    # own browser nor a customer's phone can reach it. Prefer the configured
    # public domain once deployed; fall back to the local dev address used
    # throughout this environment.
    public_url = (frappe.db.get_single_value("Workshop Settings", "public_url") or "").rstrip("/")
    base = public_url or "http://localhost:8080"
    return base + file_doc.file_url


def execute():
    # Base URL customers can actually reach (e.g. once deployed on a real
    # domain) -- WhatsApp invoice links are built from this instead of the
    # internal site name, which is not a real public hostname.
    if not frappe.db.exists("Custom Field", "Workshop Settings-public_url"):
        frappe.get_doc({
            "doctype": "Custom Field", "dt": "Workshop Settings",
            "fieldname": "public_url", "label": "الرابط العام للنظام",
            "fieldtype": "Data",
            "description": "يُستخدم لبناء روابط الفواتير المُرسلة عبر واتساب "
                            "(مثال: https://khat-aljazeera.com) — اتركه فارغاً "
                            "أثناء التشغيل المحلي، لأن الروابط لن تعمل على "
                            "هاتف العميل إلا بعد نشر النظام على خادم عام.",
            "insert_after": "country_code",
        }).insert(ignore_permissions=True)
    frappe.db.commit()
    frappe.clear_cache()
    print("INVOICE_WHATSAPP_DONE")
