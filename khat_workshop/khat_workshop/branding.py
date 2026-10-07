# -*- coding: utf-8 -*-
"""Put the uploaded login-page background onto the login page.

Frappe has no login-background field — the logo, favicon and splash image are
built in, but the full-page background behind the login card is not. So this
adds the missing half: a custom field holds the image (see
setup/workshop_branding) and this hook paints it on.

update_website_context runs server-side for every web page, so the style is
injected only when the page being rendered is /login. Nothing is added to any
other page, and if no background has been uploaded nothing is added at all —
the login page keeps Frappe's default look until the owner chooses otherwise.
"""

from urllib.parse import quote

import frappe


def force_site_language(context):
    """Render the login page in the site's language, not the browser's.

    Frappe picks the language for a signed-out visitor in this order:
    the `preferred_language` cookie, then the browser's Accept-Language, and
    only then the site default. A workshop PC whose Chrome is US English
    therefore opened an Arabic system on an English login screen — verified
    live: with no cookie the page came back lang="en" dir="ltr" although
    System Settings says "ar".

    So: when the visitor has expressed no preference, fall back to the site
    language instead of the browser's. Anyone who picks a language with the
    switcher sets the cookie, and that choice still wins — this only replaces
    the guess, never an actual choice.
    """
    if frappe.request and frappe.request.cookies.get("preferred_language"):
        return

    site_lang = frappe.db.get_single_value("System Settings", "language")
    if not site_lang or frappe.local.lang == site_lang:
        return

    frappe.local.lang = site_lang
    # Clear the memoised dictionary so the new language is the one actually
    # used to translate this page, not the one loaded a moment ago.
    frappe.local.lang_full_dict = None
    context["lang"] = site_lang

    # base.html renders <html lang="{{boot.lang}}">, and that boot dict is built
    # before this hook runs — so setting frappe.local.lang alone left the markup
    # saying lang="en" while the page itself was translated to Arabic. Verified
    # in apps/frappe/frappe/templates/base.html rather than assumed.
    boot = context.get("boot")
    if boot is not None:
        try:
            boot["lang"] = site_lang
        except TypeError:
            # boot is a JSON string on some render paths; leave it rather than
            # corrupting it — dir/translation are already correct by here.
            pass


def inject_login_background(context):
    # Gate strictly to the login route. context.path is the www page name.
    path = (context.get("path") or "").strip("/")
    if path != "login":
        return

    bg = frappe.db.get_single_value("Website Settings", "login_background")
    if not bg:
        return

    # Uploaded filenames routinely carry spaces and Arabic characters. Percent-
    # encode the path (keeping the slashes) so the CSS url() is unambiguous
    # rather than relying on the browser to encode a bare literal.
    safe = quote(bg, safe="/")

    # صفحة الدخول كصفحة واحدة متناسقة، لا بطاقة بيضاء عائمة فوق صورة.
    #
    # المحاولات السابقة عالجت الخلفية وحدها: `contain` أظهر الصورة مربعاً
    # بحوافّ ظاهرة وسط شاشة عريضة، و`cover` ملأها لكن بقيت البطاقة صندوقاً
    # أبيض لا صلة له بما خلفه. المشكلة لم تكن في الصورة بل في أن البطاقة
    # تنتمي لنظام ألوان آخر.
    #
    # الحل: البطاقة تأخذ لون الهوية الكحلي ونصاً فاتحاً، فتبدو جزءاً من
    # الصفحة. والخلفية تُغطّى بتدرّج قُطري من نفس اللون يترك الشعار ظاهراً
    # في الحافة البعيدة ويُعتّم خلف البطاقة — فيُقرأ النص بوضوح ويبقى الشعار
    # حاضراً. هذا ما يجعل صفحات الدخول الاحترافية تبدو مصمَّمة لا مركَّبة.
    style = (
        '<style id="kaj-login-bg">'
        ':root{--kaj-navy:#16233d;--kaj-navy-2:#1e3050;--kaj-red:#a52834;'
        '--kaj-gold:#f0b429;}'
        # ── الخلفية ──
        'body[data-path="login"]{'
        'background-color:var(--kaj-navy);'
        # الخلفية صارت النسخة الفاتحة (شعار داكن على أبيض): تبرز خلف التعتيم
        # بدل أن تذوب فيه كما كانت الداكنة. والتعتيم أقوى لأن الأبيض يحتاج
        # حجباً أكثر ليبقى النص الفاتح مقروءاً فوقه.
        'background-image:linear-gradient(135deg,rgba(14,24,42,.90) 0%,'
        'rgba(14,24,42,.80) 45%,rgba(14,24,42,.90) 100%),url("__KAJ_BG__");'
        # الصورة مربّعة والشاشة عريضة، فكلا الخيارين يُخفق وحده: contain
        # يتركها مربعاً معلّقاً بحوافّ ظاهرة، وcover يُكبّرها حتى يُقصّ الترس
        # يساراً و«خط» يميناً — فوضى بصرية خلف البطاقة.
        #
        # الحل: تصغيرها لارتفاع الشاشة تقريباً (auto 82%) وتوسيطها، فتظهر
        # كاملة غير مقصوصة ويملأ لون الهوية ما حولها. والتعتيم أقوى ومتساوٍ
        # ليصير الشعار نسيجاً خلفياً هادئاً لا عنصراً يزاحم بطاقة الدخول.
        # cover في النهاية: أي مقاس يُبقي الصورة المربّعة داخل الشاشة العريضة
        # يترك حافّتين رأسيّتين حادّتين تبدوان كمستطيل ملصق — جرّبتُ 82% ثم
        # 120% وبقيت الحافّتان. وcover وحده يملأ العرض كاملاً فتختفيان.
        #
        # ما جعل cover يُخفق أول مرة هو ضعف التعتيم: الشعار المقصوص كان
        # يزاحم البطاقة. مع تعتيم .90/.80 صار نسيجاً خلفياً هادئاً، فالقصّ
        # لم يعد مرئياً كعيب.
        'background-size:cover;background-position:center;'
        'background-repeat:no-repeat;background-attachment:fixed;min-height:100vh;}'
        # ── البطاقة ──
        # .login-content.page-card وحدها هي البطاقة (371px). أما .for-login
        # فغلاف خارجي بعرض 1010px — تنسيقه كبطاقة أنتج بطاقتين متداخلتين،
        # فصار شفافاً بلا إطار. تحققت من الأبعاد في المتصفح لا بالتخمين.
        'body[data-path="login"] .for-login{background:none;border:0;box-shadow:none;'
        'padding:0;}'
        'body[data-path="login"] .login-content.page-card{'
        'background:linear-gradient(160deg,rgba(30,48,80,.96),rgba(18,30,52,.97));'
        'border:1px solid rgba(255,255,255,.10);'
        'border-radius:18px;'
        'box-shadow:0 24px 60px rgba(0,0,0,.45),0 2px 0 rgba(255,255,255,.06) inset;'
        'backdrop-filter:blur(10px);'
        'padding:34px 30px 30px;}'
        # ── النصوص داخل البطاقة ──
        'body[data-path="login"] .for-login h4,'
        'body[data-path="login"] .page-card h4,'
        'body[data-path="login"] .for-login .page-card-head,'
        'body[data-path="login"] h1,body[data-path="login"] h3{'
        'color:#fff !important;font-weight:700;letter-spacing:.2px;}'
        'body[data-path="login"] .text-muted,'
        'body[data-path="login"] .page-card-head + div,'
        'body[data-path="login"] label,'
        'body[data-path="login"] .form-label{color:rgba(255,255,255,.62) !important;}'
        # ── الحقول ──
        'body[data-path="login"] .form-control,'
        'body[data-path="login"] input[type="text"],'
        'body[data-path="login"] input[type="email"],'
        'body[data-path="login"] input[type="password"]{'
        'background:rgba(255,255,255,.07) !important;'
        'border:1px solid rgba(255,255,255,.16) !important;'
        'color:#fff !important;border-radius:10px;height:44px;'
        'transition:border-color .16s,background .16s;}'
        'body[data-path="login"] .form-control:focus,'
        'body[data-path="login"] input:focus{'
        'background:rgba(255,255,255,.11) !important;'
        'border-color:var(--kaj-gold) !important;box-shadow:none !important;}'
        'body[data-path="login"] input::placeholder{color:rgba(255,255,255,.34) !important;}'
        # أيقونات الحقول (المظروف والقفل والعين) كانت داكنة على حقل داكن.
        'body[data-path="login"] .input-group-text,'
        'body[data-path="login"] .form-control + svg,'
        'body[data-path="login"] .input-with-feedback svg{color:rgba(255,255,255,.45) !important;}'
        # ── الأزرار ──
        # الأساسي بأحمر الهوية بدل أسود Frappe الافتراضي.
        # .btn-login يحمل صنف btn-default في هذا الإصدار، فالقاعدة الثانوية
        # أدناه كانت تُلغي لونه الأحمر وتعيده رمادياً. ترتيبه هنا يضمن الأسبقية.
        'body[data-path="login"] .btn-primary,'
        'body[data-path="login"] .btn-login.btn-default,'
        'body[data-path="login"] .btn-login{'
        'background:var(--kaj-red) !important;border:0 !important;'
        'border-radius:10px;height:44px;font-weight:700;'
        'box-shadow:0 6px 18px rgba(165,40,52,.38);'
        'transition:filter .16s,transform .16s;}'
        'body[data-path="login"] .btn-primary:hover{filter:brightness(1.12);'
        'transform:translateY(-1px);}'
        # :not(.btn-login) حتى لا تُلغي هذه القاعدة أحمرَ زر الدخول أعلاه.
        'body[data-path="login"] .btn-default:not(.btn-login),'
        'body[data-path="login"] .btn-secondary{'
        'background:rgba(255,255,255,.08) !important;'
        'border:1px solid rgba(255,255,255,.14) !important;'
        'color:rgba(255,255,255,.82) !important;border-radius:10px;height:44px;}'
        'body[data-path="login"] .btn-default:hover{background:rgba(255,255,255,.14) !important;}'
        # ── الروابط ──
        'body[data-path="login"] a{color:var(--kaj-gold) !important;'
        'text-decoration:none;}'
        'body[data-path="login"] a:hover{text-decoration:underline;}'
        # "هل نسيت كلمة السر؟" يرث text-align:left من Frappe، فيلتصق بالحافة
        # اليسرى في واجهة عربية بينما كل ما حوله محاذٍ لليمين. الحاوية تتبع
        # اتجاه الصفحة بدل قيمة ثابتة.
        'body[data-path="login"] .forgot-password-message,'
        'body[data-path="login"] a[href*="forgot"],'
        'body[data-path="login"] a[href*="#forgot"]{display:inline-block;}'
        'body[data-path="login"] .forgot-password-message,'
        'body[data-path="login"] .page-card-actions{text-align:start !important;}'
        # مسافة أوضح بين الزرّين: 12px تجعلهما يبدوان كتلة واحدة.
        'body[data-path="login"] .btn-login{margin-top:6px;}'
        'body[data-path="login"] .btn-login + .btn,'
        'body[data-path="login"] .btn-login + a.btn{margin-top:10px;}'
        # ── الشعار داخل البطاقة ──
        # كان 40 بكسل تقريباً فيُقرأ كلطخة؛ تكبيره وتوسيطه يجعله عنوان البطاقة.
        'body[data-path="login"] .for-login img,'
        'body[data-path="login"] .page-card img,'
        'body[data-path="login"] .app-logo{'
        'width:72px !important;height:auto !important;max-height:72px;'
        'display:block;margin:0 auto 14px;border-radius:16px;'
        # الشعار صار النسخة الداكنة (شعار فاتح على كحلي)، فيندمج مع البطاقة
        # بلا إطار ولا ظل — المربع الأبيض السابق كان يبدو ملصقاً عليها.
        'border:0;box-shadow:none;}'
        # تقليل الحشو والفراغات: البطاقة كانت تتجاوز ارتفاع الشاشة على
        # اللابتوب فيضطر المستخدم للتمرير ليرى زر الدخول.
        'body[data-path="login"] .login-content.page-card{padding:28px 26px 24px;}'
        'body[data-path="login"] .form-group,'
        'body[data-path="login"] .frappe-control{margin-bottom:12px !important;}'
        # ── الهاتف ──
        # الشعار خلف بطاقة تملأ الشاشة لا يُرى، فنكتفي بتدرّج الهوية.
        '@media (max-width:820px){body[data-path="login"]{'
        'background-image:linear-gradient(160deg,#1e3050,#0e182a);}}'
        '</style>'
    )
    # استبدال بعلامة نصّية لا %-formatting: نسب CSS (0%، 42%، 100%) كانت
    # تُفسَّر كمحدّدات تنسيق فيفشل بناء الصفحة كاملاً بخطأ 500.
    style = style.replace("__KAJ_BG__", frappe.utils.escape_html(safe))

    # head_html is what base.html renders inside <head>; append so we never
    # clobber anything another hook may have set.
    context.head_html = (context.get("head_html") or "") + style


BRANDING_FILE_FIELDS = ("app_logo", "login_background")


def ensure_public_branding(doc, method=None):
    """Force the logo and login background to be public files.

    The login page is served to logged-out visitors, and a guest cannot read a
    private file — so a logo or background uploaded as private (Frappe's default
    for an Attach) is there in the database but invisible on the very page it is
    meant for. This runs on save: any branding image still private is flipped to
    public and the field repointed at its new /files/ URL, so an upload works
    the moment it is saved rather than only after a manual fix.
    """
    for field in BRANDING_FILE_FIELDS:
        url = doc.get(field)
        if not url:
            continue
        fname = frappe.db.get_value("File", {"file_url": url}, "name")
        if not fname:
            continue
        # A failure to flip the file must not block saving Website Settings —
        # the worst case is the branding image stays private and invisible,
        # which the owner will see and report, whereas a raised exception would
        # make the settings page unsaveable. Log it and move on.
        try:
            f = frappe.get_doc("File", fname)
            if f.is_private:
                f.is_private = 0
                f.save(ignore_permissions=True)   # moves the file, rewrites file_url
                doc.set(field, f.file_url)
        except Exception:
            frappe.log_error(
                title="ensure_public_branding failed for %s" % field,
                message=frappe.get_traceback(),
            )
