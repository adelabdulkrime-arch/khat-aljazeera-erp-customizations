# -*- coding: utf-8 -*-
"""«نسيت كلمة المرور» تعمل لكل حساب، ومنها حساب المالك.

دالة الإطار (frappe.core.doctype.user.user.reset_password) تبحث عن المستخدم
باسم سجلّه وتتخطّى «Administrator» بصمت. وحساب المالك هنا هو ذلك السجلّ نفسه
(الحساب الذي لا يُحذف)، وبريده الحقيقي حقلٌ فيه لا اسمُه: فكان يكتب بريده في
«نسيت كلمة المرور»، تقول الصفحة «أرسلنا التعليمات»، ولا يصله شيء أبداً — وطريقه
الوحيد إلى حسابه أمرٌ على الخادم.

هذه تحلّ محلّها (hooks.override_whitelisted_methods) بالعقد نفسه والردّ العام
نفسه (لا يُعرف من الردّ إن كان الحساب موجوداً)، مع فرقين:

  * يُعرَف الحساب بما يُكتب في صفحة الدخول: البريد أو اسم الدخول، لا اسم السجلّ
    وحده. الرسالة تذهب إلى بريد الحساب المسجَّل، لا إلى ما كُتب.
  * حساب المالك يُرسَل له ما دام بريده صندوقاً حقيقياً. من يملك ذلك الصندوق
    يملك النظام — كما هو حال أي مدير نظام في الإطار — فالصندوق يُحمى بالتحقق
    بخطوتين.
"""

import frappe
from frappe import _
from frappe.core.doctype.user.user import get_password_reset_limit
from frappe.rate_limiter import rate_limit

OWNER = "Administrator"
PLACEHOLDER_EMAILS = ("", "admin@example.com")


def _resolve(text):
    """اسم سجلّ المستخدم مما يكتبه في صفحة الدخول: البريد أو اسم الدخول."""
    text = (text or "").strip()
    if not text:
        return None
    if frappe.db.exists("User", text):
        return text
    return (frappe.db.get_value("User", {"email": text}, "name")
            or frappe.db.get_value("User", {"username": text}, "name"))


@frappe.whitelist(allow_guest=True, methods=["POST"])
@rate_limit(limit=get_password_reset_limit, seconds=60 * 60)
def reset_password(user: str) -> None:
    try:
        name = _resolve(user)
        if name:
            doc = frappe.get_doc("User", name)
            real_mailbox = (doc.email or "").strip().lower() not in PLACEHOLDER_EMAILS
            if doc.enabled and name != "Guest" and (name != OWNER or real_mailbox):
                doc.validate_reset_password()
                doc._reset_password(send_email=True)
    except frappe.DoesNotExistError:
        frappe.clear_messages()
    except frappe.OutgoingEmailError:
        frappe.clear_messages()
        frappe.log_error(title="Password reset email could not be sent", message=frappe.get_traceback())
    except Exception:
        frappe.clear_messages()
        frappe.log_error(title="Password reset failed unexpectedly", message=frappe.get_traceback())

    frappe.msgprint(
        msg=_("If this email is registered with us, we have sent password reset instructions to it. "
              "Please check your inbox."),
        title=_("Password Reset"),
    )
