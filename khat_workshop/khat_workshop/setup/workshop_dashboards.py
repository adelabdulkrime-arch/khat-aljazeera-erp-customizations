# -*- coding: utf-8 -*-
"""اللوحات السبع وشريطها الجانبي، من khat_workshop.navigation.

هذه الخطوة تحلّ محلّ تسع خطوات: ستة بُناة لوحات (workshop_home،
workshop_dashboard، workshop_sales، workshop_purchasing، workshop_inventory،
workshop_accounting، workshop_general_settings)، وخطوتين كانتا تصحّحان ما
تتركه (workshop_sidebar_nav للشريط، workshop_workspace_polish للترتيب
والإخفاء). كل بانٍ منها حمل قائمة بلاطاته وHTML وCSS وسكربتاً خاصاً، وعرّف
ترتيب اللوحات ثلاث مرات بثلاث قيم مختلفة يدهس آخرُها أولَها.

ما تنشئه هنا لكل لوحة:
  • Custom HTML Block فيه نقطة تثبيت فارغة؛ المحتوى يرسمه
    public/js/kaj_dashboard.js من بيانات الإقلاع، فتغيير بلاطة يعني تعديل
    navigation.py وحده.
  • Workspace محتواه ذلك البلوك فقط.
  • Workspace Sidebar بالروابط السبعة نفسها، فالشريط واحد في كل اللوحات.

وتُخفي كل مساحة عمل عامة غير السبع، وتحذف ما خلّفته البُناة القديمة من
بلوكات وبطاقات أرقام (كانت تجمع المسودات والملغى مع المعتمد).

آمنة لإعادة التشغيل: تُحدّث الموجود وتنشئ الناقص.
"""

import json
import re

import frappe

from khat_workshop import navigation

APP = "khat_workshop"

# اللوحات بلا وحدة (module) عن قصد. الإطار يحجب مساحة العمل عمّن لا يقرأ
# مستنداً واحداً على الأقل من وحدتها (Workspace.__init__ في desk/desktop.py)؛
# وحدة «Khat Workshop» لا مستندات فيها، فكانت اللوحات السبع تظهر لـAdministrator
# وحده، ويرى كل مستخدم آخر — ومنهم حساب مدير الورشة — «غير مسموح به». ووحدة
# «Workshop» (حيث بطاقة العمل) تحجبها عن محاسب لا شأن له بالبطاقات. بلا وحدة
# تظهر اللوحة لكل مستخدم، وما يراه داخلها تحدّده صلاحيته على كل بلاطة.
MODULE = None

# بلوكات البُناة السابقة وبطاقات أرقامها
OLD_BLOCKS = [
    "Home Dashboard Tiles", "Workshop Dashboard Search", "Sales Dashboard Tiles",
    "Purchasing Dashboard Tiles", "Inventory Dashboard Tiles",
    "Accounting Dashboard Tiles", "General Settings Tiles",
]
OLD_NUMBER_CARDS = [
    "بطاقات العمل", "العملاء", "المركبات", "فواتير الإصلاح", "إجمالي المدفوعات",
    "المتبقيات", "أوامر البيع المعلقة", "الذمم المدينة", "إجمالي المبيعات",
    "إجمالي عدد فواتير المشتريات", "إجمالي المشتريات", "إجمالي المدفوع", "الموردون",
    "الأوامر المفتوحة", "طلبات معلقة",
]


def block_name(module):
    return "Kaj Dashboard - %s" % module["workspace"]


def _css():
    """تنسيق اللوحات، مصغَّراً، ليُنسخ إلى كل بلوك (Shadow DOM لا يرى ملفات الصفحة)."""
    path = frappe.get_app_path(APP, "public", "css", "kaj_dashboard.css")
    with open(path, encoding="utf-8") as f:
        css = f.read()
    css = re.sub(r"/\*.*?\*/", "", css, flags=re.S)
    css = re.sub(r"\s+", " ", css)
    return re.sub(r"\s*([{};,>])\s*", r"\1", css).strip()


def _script(module):
    # الرسّام يُحمَّل مع المكتب (hooks.app_include_js). إن وصل البلوك قبله —
    # نسخة قديمة من الملف في ذاكرة المتصفح — يقول ما العمل بدل لوحة فارغة.
    return (
        "if (window.kaj && kaj.dashboard) { kaj.dashboard.mount(root_element, %s); }\n"
        "else { root_element.querySelector('.kd-mount').textContent = "
        "'تعذّر تحميل اللوحة. حدّث الصفحة بـ Ctrl+Shift+R.'; }"
    ) % json.dumps(module["key"])


def _make_block(module, css):
    name = block_name(module)
    values = {
        "html": '<div class="kd-mount"></div>',
        "style": css,
        "script": _script(module),
    }
    exists = frappe.db.exists("Custom HTML Block", name)
    if exists:
        doc = frappe.get_doc("Custom HTML Block", name)
        doc.update(values)
    else:
        doc = frappe.get_doc(dict(values, doctype="Custom HTML Block", name=name))
    # جدول أدوار فارغ يحجب البلوك عن الجميع. «All» = كل مستخدم مسجَّل؛ ما يراه
    # داخل اللوحة تحدّده صلاحياته على كل بلاطة، لا صلاحية على اللوحة كلها.
    doc.set("roles", [{"role": "All"}])
    doc.flags.ignore_permissions = True
    # is_new() لا يصلح هنا: مستند مبنيّ من dict لا يحمل __islocal فيُحسب قديماً
    doc.save() if exists else doc.insert()
    return name


def _sidebar_items():
    return [{
        "label": m["title"], "type": "Link", "link_type": "Workspace",
        "link_to": m["workspace"], "icon": m["icon"],
    } for m in navigation.MODULES]


def _make_workspace(module, block, sequence):
    name = module["workspace"]
    content = [{"id": "kaj_" + module["key"], "type": "custom_block",
                "data": {"custom_block_name": block, "col": 12}}]
    values = {
        "label": name, "title": module["title"], "public": 1, "is_hidden": 0,
        "icon": module["icon"], "app": APP, "sequence_id": sequence,
        "module": MODULE,
        "content": json.dumps(content, ensure_ascii=False),
    }
    exists = frappe.db.exists("Workspace", name)
    if exists:
        ws = frappe.get_doc("Workspace", name)
        ws.update(values)
    else:
        ws = frappe.get_doc(dict(values, doctype="Workspace", name=name))
    for table in ("shortcuts", "links", "number_cards", "quick_lists", "charts", "roles"):
        ws.set(table, [])
    # block.js يطابق custom_block_name في المحتوى مع حقل label في هذا الصف
    ws.set("custom_blocks", [{"custom_block_name": block, "label": block}])
    ws.flags.ignore_permissions = True
    ws.save() if exists else ws.insert()


def _make_sidebar(module):
    name = module["workspace"]
    if frappe.db.exists("Workspace Sidebar", name):
        sb = frappe.get_doc("Workspace Sidebar", name)
    else:
        sb = frappe.new_doc("Workspace Sidebar")
        sb.title = name
    sb.header_icon = module["icon"]
    sb.module = MODULE
    sb.standard = 0
    sb.set("items", _sidebar_items())
    sb.flags.ignore_permissions = True
    sb.save()


def _hide_other_workspaces():
    hidden = 0
    others = frappe.get_all(
        "Workspace", filters={"public": 1, "name": ["not in", navigation.WORKSPACES]},
        fields=["name", "is_hidden"])
    for i, ws in enumerate(others):
        changes = {"sequence_id": 50 + i}
        if not ws.is_hidden:
            changes["is_hidden"] = 1
            hidden += 1
        frappe.db.set_value("Workspace", ws.name, changes, update_modified=False)
    return hidden


def _remove_leftovers():
    removed = 0
    for name in OLD_BLOCKS:
        if frappe.db.exists("Custom HTML Block", name):
            frappe.delete_doc("Custom HTML Block", name, force=1, ignore_permissions=True)
            removed += 1
    # بطاقات الأرقام تُسمّى بتسميتها مع لاحقة (-1، -2…) عند التكرار، وكلها غير
    # قياسية (is_standard = 0) لأن البُناة أنشأتها من خارج وضع المطوّر.
    for card in frappe.get_all(
            "Number Card", filters={"label": ["in", OLD_NUMBER_CARDS], "is_standard": 0},
            pluck="name"):
        frappe.delete_doc("Number Card", card, force=1, ignore_permissions=True)
        removed += 1
    return removed


def execute():
    css = _css()

    for i, module in enumerate(navigation.MODULES):
        block = _make_block(module, css)
        _make_workspace(module, block, i + 1)

    # الشريط بعد إنشاء اللوحات كلها: روابطه تشير إليها
    for module in navigation.MODULES:
        _make_sidebar(module)

    hidden = _hide_other_workspaces()
    removed = _remove_leftovers()

    frappe.db.commit()
    frappe.clear_cache()
    tiles = len(navigation.all_tiles())
    print("DASHBOARDS modules=%d tiles=%d css=%dB hidden_workspaces=%d removed_leftovers=%d"
          % (len(navigation.MODULES), tiles, len(css), hidden, removed))
