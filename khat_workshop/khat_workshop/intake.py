# -*- coding: utf-8 -*-
"""Refuse to start work on a vehicle whose condition nobody recorded.

An intake form that staff can skip gets skipped, and the one card that needed
it is always the one in dispute. So submission is blocked until the condition
is stated — either by listing what is damaged, or by declaring there is nothing
visible.

The escape hatch is deliberate and one click wide. The point is not paperwork;
it is that "nothing was wrong with it" becomes something a named person put on
the record at a known time, instead of an empty field that proves nothing
either way.
"""

import frappe
from frappe import _


def validate_intake(doc, method=None):
    if doc.get("no_visible_damage") or doc.get("damages"):
        return

    frappe.throw(
        _("سجّل حالة المركبة قبل ترحيل البطاقة: أضف الأضرار الظاهرة في جدول "
          "«الأضرار المسجّلة»، أو فعّل «لا توجد أضرار ظاهرة» إن كانت المركبة سليمة."),
        title=_("حالة الاستلام غير مسجّلة"),
    )
