# -*- coding: utf-8 -*-
"""خريطة النظام مع بيانات الإقلاع.

اللوحات والشريط الجانبي والبحث تُرسم في المتصفح من navigation.MODULES. إرسالها
مع الإقلاع يعني أن الواجهة تعرف خريطتها قبل أول رسم، بلا طلب إضافي — وأن
مصدرها ملف واحد في الخادم لا نسخة ثانية في جافاسكربت تتباعد عنه.
"""

import frappe

from khat_workshop import fastboot, forms, glossary, lists, navigation, reports, roles


def extend_bootinfo(bootinfo):
    kaj = navigation.for_boot()
    kaj["brand"] = {
        "name": frappe.db.get_single_value("Website Settings", "app_name") or "خط الجزيرة",
        "logo": frappe.db.get_single_value("Website Settings", "app_logo") or "",
    }
    kaj["lists"] = lists.LISTS
    kaj["plurals"] = glossary.PLURALS
    # ألوان حالات بطاقة العمل، لتُعرض الحالة بلونها في القائمة كما في اللوحة
    kaj["status_colors"] = {}
    if frappe.db.exists("DocType", "Work Card Status"):
        kaj["status_colors"] = dict(frappe.get_all(
            "Work Card Status", fields=["name", "color"], as_list=1))
    # المسمّيات الوظيفية، لحوار «إضافة مستخدم» وتبويب الأدوار
    kaj["roles"] = roles.for_boot()
    kaj["forms"] = forms.for_boot()
    kaj["reports"] = reports.for_boot()
    # اللوحات السبع وبلوكاتها: تُرسم بلا طلبَي «وصف المساحة» و«مستند البلوك»
    kaj["preload"] = fastboot.preload()
    bootinfo.kaj = kaj
