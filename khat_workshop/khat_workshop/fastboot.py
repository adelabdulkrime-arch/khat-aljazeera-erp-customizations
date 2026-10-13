# -*- coding: utf-8 -*-
"""الدخول السريع: ما لا يتغيّر لا يُنقل مع كل تحميل.

الخادم يجهّز صفحة المكتب في أقل من خُمس ثانية؛ ما يطيل الدخول هو الشبكة. قِيس من
اتصال المالك (ربع ثانية لكل طلب، ونحو 150KB في الثانية): سبع ثوانٍ من ضغط «تسجيل
الدخول» إلى ظهور الرئيسية، في متصفح سبق أن حمّل كل الملفات. ثلاثة أشياء أكلتها:

  1. الترجمة. صفحة المكتب تحمل قاموس الواجهة كاملاً في جسمها: 342KB من 420KB
     (مضغوطة)، والصفحة لا تُخزَّن في المتصفح، فيُنزَّل القاموس مع كل دخول وكل
     تحديث وكل تبويب جديد. يخرج الآن إلى ملف له عنوان يحمل بصمة محتواه
     (messages_js)، فيُنزَّل مرة ويبقى في المتصفح إلى أن تتغيّر الترجمة.

  2. اللوحة. قبل أن تُرسم يطلب المكتب وصف مساحة العمل ثم مستند البلوك، طلبين
     متتابعين لا يتغيّر جوابهما. يُرسلان مع بيانات الإقلاع (preload).

  3. ملفاتنا. كانت تُراجَع مع الخادم في كل تحميل (must-revalidate)، عشرة طلبات
     تسبق الرسم. عناوينها تحمل الآن بصمة محتواها (versioned)، فتُخزَّن بلا
     مراجعة، والتعديل يغيّر العنوان فيصل فوراً (‎_v‎ في hooks.py، والترويسة في
     docker/Caddyfile).
"""

import hashlib
import json
import re

import frappe
import orjson

from khat_workshop import navigation

BLOCK_PREFIX = "Kaj Dashboard - "


# ── 1. قاموس الواجهة خارج الصفحة ─────────────────────────────────────────────

def _messages(lang):
    from frappe.translate import get_all_translations

    data = orjson.dumps(get_all_translations(lang), option=orjson.OPT_SORT_KEYS)
    return data, hashlib.md5(data).hexdigest()[:12]


def kaj_messages_src(boot):
    """عنوان ملف القاموس، ويُفرَّغ القاموس من بيانات الإقلاع.

    تُنادى من templates/includes/splash_screen.html، وهو يُرسم قبل أن تُكتب
    بيانات الإقلاع في الصفحة: التفريغ والعنوان في مكان واحد، فلا يُفرَّغ القاموس
    في صفحة لا تحمل وسم الملف.
    """
    lang = frappe.local.lang or "en"
    _, digest = _messages(lang)
    boot["__messages"] = {}
    return "/api/method/khat_workshop.fastboot.messages_js?lang=%s&v=%s" % (lang, digest)


@frappe.whitelist(methods=["GET"])
def messages_js(lang="en", v=None):
    """قاموس الواجهة للغة، سكربتاً يُخزَّن في المتصفح. `v` بصمة المحتوى في العنوان."""
    from werkzeug.wrappers import Response

    if not re.fullmatch(r"[A-Za-z]{2,3}([-_][A-Za-z]{2,4})?", lang or ""):
        frappe.throw(frappe._("Invalid language"))
    data, _ = _messages(lang)
    response = Response(b"window.__kaj_messages=" + data + b";",
                        content_type="application/javascript; charset=utf-8")
    response.headers["Cache-Control"] = "private, max-age=31536000, immutable"
    return response


# ── 2. اللوحات مع بيانات الإقلاع ─────────────────────────────────────────────

def preload():
    """وصف مساحات العمل السبع وبلوكاتها، كما يردّ بهما الخادم على طلبَي المكتب.

    لا يختلفان من مستخدم لآخر (البلوك لدور «All»، وما يراه المستخدم داخل
    اللوحة تحدّده صلاحياته في المتصفح)، فيُبنيان مرة ويُحفظان بمفتاح من تواريخ
    تعديلهما: إعادة الإعداد عند النشر تغيّر التواريخ فيُبنيان من جديد.
    """
    names = [m["workspace"] for m in navigation.MODULES]
    spaces = frappe.get_all("Workspace", filters={"name": ["in", names]},
                            fields=["name", "title", "public", "modified"], order_by="name")
    blocks = frappe.get_all("Custom HTML Block", filters={"name": ["like", BLOCK_PREFIX + "%"]},
                            fields=["name", "modified"], order_by="name")
    stamp = hashlib.md5(repr([(d.name, str(d.modified)) for d in spaces + blocks]).encode()).hexdigest()[:12]
    key = "kaj_preload:" + stamp
    cached = frappe.cache.get_value(key)
    if cached:
        return cached

    from frappe.desk.desktop import get_desktop_page

    pages = {}
    for s in spaces:
        page = get_desktop_page(json.dumps({"name": s.name, "title": s.title, "public": s.public}))
        # مساحة لا يراها من بُنيت بحسابه لا تُحفظ فارغةً للجميع: يطلبها المتصفح
        if page and (page.get("custom_blocks") or {}).get("items"):
            pages[s.name] = page

    docs = frappe.get_all("Custom HTML Block", filters={"name": ["like", BLOCK_PREFIX + "%"]},
                          fields=["name", "html", "script", "style"])
    # التنسيق واحد في البلوكات السبعة (35KB): يُرسل مرة
    style = docs[0].style if docs and all(d.style == docs[0].style for d in docs) else None
    out = {
        "pages": pages,
        "style": style,
        "blocks": {d.name: ({"html": d.html, "script": d.script} if style is not None
                            else {"html": d.html, "script": d.script, "style": d.style}) for d in docs},
    }
    out = json.loads(frappe.as_json(out))
    frappe.cache.set_value(key, out, expires_in_sec=6 * 3600)
    return out
