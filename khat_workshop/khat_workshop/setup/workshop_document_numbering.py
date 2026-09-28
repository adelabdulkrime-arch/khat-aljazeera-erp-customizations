# -*- coding: utf-8 -*-
"""Separate numbering for workshop documents — from screenshots he shared
(2026-08-25) of a real Mazoon install.

The screenshots showed a plain point-of-sale invoice numbered SI-0002 (no
vehicle, no customer context) sitting alongside a *different* series for
vehicle-linked documents: a quotation numbered WQ-2026-0002, and a receipt
that referenced "فاتورة الإصلاح WI-2026-0002". Two distinct series, so a
workshop job is visually and numerically distinguishable from a counter sale
the moment you see the document number — useful for the owner (at a glance,
which of these is a repair job) and matches what he has already seen and
expects.

This project deliberately does NOT have a separate "Repair Invoice" doctype
(one existed before and was retired — see workshop_retire_shadow.py — because
mirroring two documents produced tax and cancellation bugs). Reintroducing a
second doctype just to get a second number would bring the same class of bug
back. Instead: same doctype (Sales Invoice / Quotation), a second Naming
Series option added to the existing field, auto-selected the moment a
`vehicle` is set on a new document. A plain counter sale never touches
`vehicle` and keeps the default series untouched.

Depends on workshop_gl_stock_integration, which is what put the `vehicle`
custom field on Sales Invoice and Quotation in the first place.
"""

import frappe

# (doctype, series to add, event fieldname the client script watches)
DOCS = [
    ("Sales Invoice", "WI-.YYYY.-"),
    ("Quotation", "WQ-.YYYY.-"),
]

_JS_TEMPLATE = u"""
frappe.ui.form.on('__DOCTYPE__', {
    vehicle: (frm) => {
        if (frm.is_new() && frm.doc.vehicle && frm.doc.naming_series !== '__SERIES__') {
            frm.set_value('naming_series', '__SERIES__');
        }
    },
});
"""


def _ensure_series_option(doctype, series):
    field = frappe.get_meta(doctype).get_field("naming_series")
    if not field:
        return "skipped (no naming_series field on %s)" % doctype
    lines = [l.strip() for l in (field.options or "").split("\n") if l.strip()]
    if series in lines:
        return "already present"
    lines.append(series)
    # NOTE (2026-09-29): there are TWO functions named make_property_setter,
    # and they take different arguments:
    #
    #   frappe.custom.doctype.property_setter.property_setter.make_property_setter
    #       (doctype, fieldname, property, value, property_type, ...)   positional
    #   frappe.make_property_setter                                      <- this one
    #       (args: dict, ignore_validate=False, ...)                     a single dict
    #
    # An earlier comment here claimed the positional form was "verified against
    # the real framework source" — but it had checked the first function while
    # the code calls the second. The result was a hard TypeError ("takes from 1
    # to 4 positional arguments but 5 were given") that killed this step on
    # every single deploy, so the WI-/WQ- series were never registered.
    frappe.make_property_setter({
        "doctype": doctype,
        "fieldname": "naming_series",
        "property": "options",
        "value": "\n".join(lines),
        "property_type": "Text",
    })
    return "added"


def _ensure_autoselect_script(doctype, series):
    name = "%s Workshop Series Autoselect" % doctype
    js = _JS_TEMPLATE.replace("__DOCTYPE__", doctype).replace("__SERIES__", series)
    if frappe.db.exists("Client Script", name):
        frappe.delete_doc("Client Script", name, force=1, ignore_permissions=True)
    frappe.get_doc({
        "doctype": "Client Script", "name": name,
        "dt": doctype, "view": "Form", "enabled": 1, "script": js,
    }).insert(ignore_permissions=True)


def execute():
    results = {}
    for doctype, series in DOCS:
        results[doctype] = _ensure_series_option(doctype, series)
        _ensure_autoselect_script(doctype, series)
    frappe.db.commit()
    frappe.clear_cache()
    print("DOCUMENT_NUMBERING %s" % results)
