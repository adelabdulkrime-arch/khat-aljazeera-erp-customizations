# -*- coding: utf-8 -*-
"""حسابا النظام: مالكه التقني، ومدير الورشة.

النظام يُسلَّم بحسابين لا غير:

  ١. مالك النظام — «onemedia». هو الحساب الجذري المدمج في Frappe (سجلّه
     Administrator): يملك كل شيء بحكم تعريفه، ولا يُحذف ولا يُعطَّل، ولا يراه
     في قائمة المستخدمين ولا يعدّله أحد غيره — الإطار نفسه يمنع ذلك
     (core/doctype/user/user.py) لا كود نكتبه نحن. لا يُنشأ هنا حساب جديد؛
     يُعطى الحساب الجذري اسمه وبريده واسم دخوله.

  ٢. مدير الورشة — حساب العميل، بالمسمّيين «مدير النظام» و«مدير الورشة»:
     صلاحيات التشغيل كلها وإدارة المستخدمين والإعدادات. يظهر باسم
     «Administrator» كما طُلب. لا يدخل بهذه الكلمة: هي معرّف الحساب الجذري،
     والإطار يبحث عن الداخل بالمعرّف قبل اسم الدخول. يدخل ببريده أو بـ«Admin».

كلمتا المرور ليستا هنا ولا في أي ملف بالمستودع. كلمة مرور حساب العميل تُقرأ
من متغيّر البيئة DEMO_USER_PASSWORD **عند إنشاء الحساب فقط**. كانت تُكتب عند
كل نشر، فأي كلمة يغيّرها العميل من الواجهة تعود إلى القديمة مع أول تحديث.

الحساب السابق admin@khataljazeera.om يُعاد تسميته إلى البريد الجديد — لا يُحذف
وينشأ غيره — فيبقى ما أنشأه من مستندات منسوباً إليه.
"""

import os

import frappe
from frappe.utils.password import update_password

# ── مالك النظام: الحساب الجذري ──
ROOT = "Administrator"
OWNER_NAME = "onemedia"
OWNER_EMAIL = "onemedia2a@gmail.com"
OWNER_USERNAME = "onemedia"

# ── مدير الورشة ──
EMAIL = "khataljazeera@gmail.com"
OLD_EMAIL = "admin@khataljazeera.om"
USERNAME = "Admin"
FIRST_NAME = "Administrator"
ROLES = ("مدير النظام", "Workshop Manager")
# مسمّيات كانت تُمنح للحساب التجريبي ليرى اللوحات؛ «مدير النظام» يغني عنها
LEGACY_ROLES = ("محاسب", "مدير المستودع", "مسؤول المشتريات", "مندوب مبيعات")

PASSWORD_ENV = "DEMO_USER_PASSWORD"


def _username_free(username, user):
    holder = frappe.db.get_value("User", {"username": username}, "name")
    return not holder or holder == user


def _owner():
    """اسم مالك النظام وبريده واسم دخوله على الحساب الجذري."""
    doc = frappe.get_doc("User", ROOT)
    changed = []
    if doc.first_name != OWNER_NAME or doc.last_name:
        doc.first_name, doc.last_name = OWNER_NAME, None
        changed.append("name")
    if doc.email != OWNER_EMAIL:
        doc.email = OWNER_EMAIL
        changed.append("email")
    if doc.username != OWNER_USERNAME and _username_free(OWNER_USERNAME, ROOT):
        doc.username = OWNER_USERNAME
        changed.append("username")
    if changed:
        doc.flags.ignore_permissions = True
        doc.save()
    return changed


def _client():
    """حساب مدير الورشة: يُعاد تسمية السابق، أو يُنشأ. يعيد (المستند، ما جرى)."""
    notes = []
    if frappe.db.exists("User", OLD_EMAIL) and not frappe.db.exists("User", EMAIL):
        frappe.rename_doc("User", OLD_EMAIL, EMAIL, force=True)
        notes.append("renamed")

    if frappe.db.exists("User", EMAIL):
        doc = frappe.get_doc("User", EMAIL)
    else:
        doc = frappe.get_doc({
            "doctype": "User", "email": EMAIL, "first_name": FIRST_NAME,
            "enabled": 1, "user_type": "System User", "language": "ar",
            "send_welcome_email": 0,
        })
        doc.flags.no_welcome_mail = True
        doc.insert(ignore_permissions=True)
        notes.append("created")

    changed = False
    if not doc.enabled:
        doc.enabled, changed = 1, True
    if doc.email != EMAIL:
        doc.email, changed = EMAIL, True
    if doc.first_name != FIRST_NAME or doc.last_name:
        doc.first_name, doc.last_name, changed = FIRST_NAME, None, True
    if doc.username != USERNAME and _username_free(USERNAME, doc.name):
        doc.username, changed = USERNAME, True

    held = {row.role for row in doc.roles}
    for role in ROLES:
        if role not in held and frappe.db.exists("Role", role):
            doc.append("roles", {"role": role})
            changed = True
    for row in list(doc.roles):
        if row.role in LEGACY_ROLES:
            doc.remove(row)
            changed = True

    if changed:
        doc.flags.ignore_permissions = True
        doc.flags.no_welcome_mail = True
        doc.save()
        notes.append("updated")
    return doc, notes


def _has_password(user):
    return bool(frappe.db.sql(
        "select 1 from `__Auth` where doctype = 'User' and name = %s and fieldname = 'password'",
        user))


def _initial_password(user):
    """كلمة مرور أولى من البيئة لحساب بلا كلمة مرور. لا تُمسّ كلمة قائمة."""
    if _has_password(user):
        return "kept"
    pwd = (os.environ.get(PASSWORD_ENV) or "").strip()
    if not pwd:
        return "MISSING"
    # update_password يتجاوز فحص قوة كلمة المرور، وهو ما ينتهي إليه مسار
    # «إعادة التعيين» في الإطار نفسه
    update_password(user, pwd)
    return "set"


def _allow_username_login():
    """«Admin» و«onemedia» اسما دخول؛ بلا هذا الإعداد لا يُقبل إلا البريد."""
    field = "allow_login_using_user_name"
    if not frappe.get_meta("System Settings").has_field(field):
        return False
    if not frappe.db.get_single_value("System Settings", field):
        frappe.db.set_single_value("System Settings", field, 1)
    return True


def execute():
    owner = _owner()
    doc, notes = _client()
    by_username = _allow_username_login()
    password = _initial_password(doc.name)
    frappe.db.commit()
    print("ACCOUNTS owner=%s(%s) client=%s(%s) password=%s login_names=%s"
          % (OWNER_NAME, "+".join(owner) or "ok", doc.name, "+".join(notes) or "ok",
             password, "on" if by_username else "off"))
