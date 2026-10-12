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

    # صفحة الدخول — تخطيط مُقسَّم (split-screen).
    #
    # هذا ما استقرّت عليه واجهات SaaS الحديثة (Linear وVercel وStripe
    # وClerk): لوح هوية على جانب، ونموذج على سطح نظيف على الجانب الآخر.
    # وهجرت جميعها البطاقة العائمة فوق صورة كاملة، لسببين عمليين:
    #
    # ١) الصورة خلف النموذج تُنافس النص على الانتباه مهما عُتّمت، وتفرض
    #    ضبابية وتعتيماً لتبقى الحقول مقروءة — أي ثلاث طبقات تعالج مشكلة
    #    صنعناها نحن. بفصل الجانبين يحصل كلٌّ على ما يناسبه: الصورة تُعرض
    #    كاملة بلا حجب، والنموذج على سطح هادئ بلا منافس.
    #
    # ٢) النموذج على سطح صلب يرفع التباين لأقصاه، فيُقرأ في ضوء الورشة
    #    الساطع — وهو السياق الفعلي لا مكتب مظلم.
    #
    # وعلى الشاشة الضيقة ينطوي لوح الهوية ويبقى النموذج وحده: الصورة على
    # 390px تسرق نصف الشاشة من حقول يحتاجها المستخدم.
    #
    # القياسات مبنية على معايير 2026 لا على تقدير: ارتفاع الهدف اللمسي
    # 48px (Material 3) وهو يلبّي 44px في Apple HIG، وسُلّم طباعي بنسبة
    # ~1.25، وشبكة 4px لكل المسافات.
    style = (
        '<style id="kaj-login-bg">'
        ':root{'
        '--kaj-navy:#101a2e;--kaj-navy-2:#17253f;--kaj-red:#c62839;'
        '--kaj-gold:#f0b429;--kaj-ink:#0b1220;'
        # سُلّم المسافات: مضاعفات 4px. القيم العشوائية هي ما يجعل الواجهة
        # تبدو «قريبة من الصحيح» دون أن تكون منضبطة.
        '--s1:4px;--s2:8px;--s3:12px;--s4:16px;--s5:20px;--s6:24px;'
        '--s8:32px;--s10:40px;--s12:48px;'
        '--kaj-r:12px;--kaj-r-lg:16px;'
        '}'

        # ════ التخطيط ════
        'body[data-path="login"]{background:#fff;min-height:100vh;}'
        # الغلاف يصير شبكة من عمودين. الحشو العلوي من الإطار يُلغى، وإلا
        # دُفع المحتوى خارج الشاشة.
        'body[data-path="login"] .page-content-wrapper{'
        'padding:0 !important;min-height:100vh;}'
        'body[data-path="login"] main.container{max-width:none !important;'
        'padding:0 !important;margin:0 !important;}'
        'body[data-path="login"] .page_content{min-height:100vh;}'
        'body[data-path="login"] .for-login{'
        'background:none;border:0;box-shadow:none;padding:0;'
        'min-height:100vh;display:grid;'
        # 52/48 لا 50/50: جانب النموذج أوسع قليلاً فيأخذ الأولوية البصرية
        # دون أن يبدو التقسيم اعتباطياً.
        'grid-template-columns:1fr 1fr;align-items:stretch;}'

        # ════ لوح الهوية (الجانب الأول) ════
        # يُرسم بعنصر زائف لا بوسم جديد: لا نملك قالب الصفحة، والحقن
        # بجافاسكربت يومض قبل أن يعمل.
        'body[data-path="login"] .for-login::before{'
        'content:"";position:relative;overflow:hidden;'
        'background-color:var(--kaj-navy);'
        'background-image:'
        # توهّج لوني خفيف يكسر صمت اللون الواحد — أسلوب 2026 السائد.
        'radial-gradient(900px 600px at 20% 15%,rgba(198,40,57,.22),transparent 60%),'
        'radial-gradient(700px 500px at 85% 85%,rgba(240,180,41,.10),transparent 60%),'
        'linear-gradient(145deg,rgba(16,26,46,.86),rgba(11,18,32,.94)),'
        'url("__KAJ_BG__");'
        'background-size:auto,auto,auto,cover;'
        'background-position:center;background-repeat:no-repeat;}'

        # ════ جانب النموذج ════
        'body[data-path="login"] .login-content.page-card{'
        'background:#fff !important;'
        'border:0 !important;border-radius:0 !important;box-shadow:none !important;'
        '-webkit-backdrop-filter:none !important;backdrop-filter:none !important;'
        'width:100% !important;max-width:none !important;min-width:0 !important;'
        'min-height:100vh;'
        'display:flex;flex-direction:column;justify-content:center;'
        'padding:var(--s10) clamp(var(--s6),6vw,88px) !important;'
        'font-size:15px;}'
        # النموذج نفسه بعرض قراءة مريح وسط العمود، لا ممتداً بعرضه كاملاً.
        'body[data-path="login"] .login-content.page-card > *{'
        'width:100%;max-width:400px;margin-inline:auto;}'

        # ════ الشعار ════
        # 48px: علامة لا لوحة. كان 104px على بطاقة 400px (26% من عرضها)
        # فيسرق الانتباه من الفعل المطلوب. 48 ≈ 12% وهو المدى المعتاد.
        'body[data-path="login"] .for-login img,'
        'body[data-path="login"] .page-card img,'
        'body[data-path="login"] .app-logo{'
        'width:48px !important;height:48px !important;max-height:none;'
        'display:block;margin:0 0 var(--s6) !important;'
        'border-radius:10px;border:0;object-fit:contain;box-shadow:none;}'
        # محاذاة للبداية لا توسيط: التوسيط يناسب بطاقة مربّعة، أما العمود
        # فيُقرأ من حافّته — والعين تتبع خطاً رأسياً واحداً.
        'body[data-path="login"] .page-card-head,'
        'body[data-path="login"] .page-card-head-text{'
        'text-align:start !important;margin:0 0 var(--s8) !important;}'

        # ════ الطباعة ════
        # سُلّم بنسبة ~1.25: 28 / 15 / 13. كان 23/14.5/14/14 — أربعة أحجام
        # متقاربة فلا تدرّج يقود العين.
        'body[data-path="login"] .page-card h4,'
        'body[data-path="login"] .for-login h4,'
        'body[data-path="login"] h1,body[data-path="login"] h3{'
        'color:var(--kaj-ink) !important;font-weight:700 !important;'
        'font-size:28px !important;line-height:1.2 !important;'
        'letter-spacing:-.4px;margin:0 0 var(--s2) !important;}'
        'body[data-path="login"] .page-card-subtitle,'
        'body[data-path="login"] .text-muted{'
        'color:#5b6880 !important;font-size:15px !important;'
        'line-height:1.55;font-weight:400;margin:0 !important;}'
        'body[data-path="login"] label,'
        'body[data-path="login"] .form-label{'
        'color:#36425a !important;font-size:13px !important;'
        'font-weight:600 !important;letter-spacing:.1px;'
        'margin:0 0 var(--s2) !important;display:block;}'

        # ════ الحقول ════
        # 48px هدف لمسي: Material 3 يشترط 48 وApple HIG 44، فـ48 يلبّيهما.
        # كانت 28px فعلياً — login.bundle.css يفرضها بمحدِّد أخصّ من
        # قاعدتنا، فتفوز بالأخصّية لا بالترتيب. قِيس في المتصفح.
        'body[data-path="login"] .form-control,'
        'body[data-path="login"] input[type="text"],'
        'body[data-path="login"] input[type="email"],'
        'body[data-path="login"] input[type="password"],'
        'body[data-path="login"] .for-login .page-card .page-card-body input,'
        'body[data-path="login"] .for-forgot .page-card .page-card-body input,'
        'body[data-path="login"] .for-login-with-email-link .page-card .page-card-body input{'
        'background:#f7f8fa !important;color:var(--kaj-ink) !important;'
        'border:1.5px solid #e3e7ee !important;border-radius:var(--kaj-r) !important;'
        'height:48px !important;min-height:48px !important;'
        'padding:0 44px 0 var(--s4) !important;'
        'font-size:15px !important;line-height:normal !important;'
        'box-sizing:border-box !important;box-shadow:none !important;'
        'transition:border-color .16s,background .16s,box-shadow .16s;}'
        '[dir="ltr"] body[data-path="login"] .page-card-body input{'
        'padding:0 var(--s4) 0 44px !important;}'
        'body[data-path="login"] .form-control:hover,'
        'body[data-path="login"] .page-card-body input:hover{'
        'border-color:#ccd4e0 !important;}'
        'body[data-path="login"] .form-control:focus,'
        'body[data-path="login"] .page-card-body input:focus{'
        'background:#fff !important;border-color:var(--kaj-red) !important;'
        'box-shadow:0 0 0 4px rgba(198,40,57,.10) !important;outline:none !important;}'
        'body[data-path="login"] input::placeholder{color:#9aa5b8 !important;}'
        'body[data-path="login"] .form-group{margin:0 0 var(--s5) !important;}'

        # أيقونات الحقول تتوسّط رأسياً مع الارتفاع الجديد.
        'body[data-path="login"] .email-field,'
        'body[data-path="login"] .password-field{position:relative;}'
        'body[data-path="login"] .field-icon,'
        'body[data-path="login"] .toggle-password{'
        'position:absolute;top:50% !important;transform:translateY(-50%);'
        'margin:0 !important;color:#8d98ab !important;}'
        'body[data-path="login"] .field-icon{inset-inline-start:var(--s4);}'
        'body[data-path="login"] .toggle-password{'
        'inset-inline-end:var(--s4);cursor:pointer;transition:color .15s;}'
        'body[data-path="login"] .toggle-password:hover{color:var(--kaj-ink) !important;}'

        # ════ صفّ الخيارات ════
        # «تذكّرني» خيار ثانوي و«نسيت كلمة المرور» مخرج من مأزق — فكان
        # المربّع الملوّن يسحب العين أكثر من الرابط، عكس أهميتهما.
        'body[data-path="login"] .kaj-authrow{'
        'display:flex;align-items:center;justify-content:space-between;'
        'gap:var(--s3);flex-wrap:wrap;margin:0 0 var(--s6) !important;}'
        'body[data-path="login"] .kaj-remember{'
        'display:flex;align-items:center;gap:var(--s2);'
        'font-size:13.5px;cursor:pointer;user-select:none;'
        'transition:color .15s;}'
        'body[data-path="login"] .kaj-remember{color:#6b7689;}'
        'body[data-path="login"] .kaj-remember:hover{color:var(--kaj-ink);}'
        'body[data-path="login"] .kaj-remember input{'
        'width:16px;height:16px;margin:0;flex:0 0 auto;cursor:pointer;'
        'accent-color:var(--kaj-red);}'
        'body[data-path="login"] .forgot-password-message{'
        'margin:0 !important;text-align:start !important;}'
        'body[data-path="login"] .forgot-password-message a{'
        'color:var(--kaj-red) !important;font-size:13.5px;font-weight:600;'
        'text-decoration:none;transition:color .15s;}'
        'body[data-path="login"] .forgot-password-message a:hover{'
        'color:#9e1f2e !important;text-decoration:underline;}'

        # ════ الأزرار ════
        # الوزن كان يُقاس 420 رغم طلبنا 700: الإطار يفرض وزناً متغيّراً
        # بمحدِّد أخصّ، فيبدو الزر الأساسي باهتاً بلا سلطة بصرية.
        'body[data-path="login"] .btn-primary,'
        'body[data-path="login"] .btn-login.btn-default,'
        'body[data-path="login"] .for-login .page-card .page-card-actions .btn-login,'
        'body[data-path="login"] .btn-login{'
        'background:var(--kaj-red) !important;border:0 !important;'
        'color:#fff !important;border-radius:var(--kaj-r) !important;'
        'height:48px !important;min-height:48px !important;width:100% !important;'
        'font-weight:600 !important;font-size:15px !important;letter-spacing:.1px;'
        'box-shadow:0 1px 2px rgba(11,18,32,.08) !important;'
        'margin:0 !important;'
        'transition:background .16s,transform .12s,box-shadow .16s;}'
        'body[data-path="login"] .btn-login:hover{'
        'background:#a81f2f !important;'
        'box-shadow:0 4px 12px rgba(198,40,57,.26) !important;}'
        'body[data-path="login"] .btn-login:active{transform:translateY(1px);}'
        'body[data-path="login"] .btn-login:focus-visible{'
        'outline:3px solid rgba(198,40,57,.35);outline-offset:2px;}'
        'body[data-path="login"] .page-card-actions{'
        'margin:0 !important;text-align:start !important;'
        'display:flex;flex-direction:column;gap:var(--s3);}'
        # المسار الثانوي رابط لا زرّ: زرّان متجاوران بنفس الوزن يجعلان
        # المستخدم يختار بينهما بدل أن يمضي في المسار الأساسي.
        'body[data-path="login"] .btn-login-option,'
        'body[data-path="login"] .btn-login-with-email-link{'
        'background:transparent !important;border:0 !important;'
        'color:#5b6880 !important;height:auto !important;min-height:0 !important;'
        'font-weight:500 !important;font-size:13.5px !important;'
        'text-decoration:none !important;box-shadow:none !important;'
        'padding:var(--s2) 0 !important;margin:0 !important;'
        'transition:color .15s;}'
        'body[data-path="login"] .btn-login-option:hover,'
        'body[data-path="login"] .btn-login-with-email-link:hover{'
        'color:var(--kaj-red) !important;background:transparent !important;'
        'text-decoration:underline !important;}'
        # أزرار أخرى (العودة، إعادة الإرسال) ثانوية واضحة.
        'body[data-path="login"] .btn-default:not(.btn-login):not(.btn-login-option),'
        'body[data-path="login"] .btn-secondary{'
        'background:#f2f4f8 !important;border:1px solid #e3e7ee !important;'
        'color:#36425a !important;border-radius:var(--kaj-r) !important;'
        'height:44px !important;font-weight:500 !important;}'
        'body[data-path="login"] a{color:var(--kaj-red);text-decoration:none;}'
        'body[data-path="login"] a:hover{text-decoration:underline;}'

        # ════ مبدّل اللغة ════
        # على سطح أبيض الآن، فالنمط الداكن الذي كان يناسب الزجاج يصير
        # لطخة. حدّ خفيف وسطح شفّاف يناسب الجانبين.
        '#khat-lang-switch{background:rgba(255,255,255,.92) !important;'
        'border:1px solid #e3e7ee;box-shadow:0 1px 3px rgba(11,18,32,.06);}'
        '.khat-lang-btn{color:#5b6880 !important;}'
        '.khat-lang-btn:hover{color:var(--kaj-ink) !important;'
        'background:#f2f4f8 !important;}'
        '.khat-lang-btn.is-active{color:var(--kaj-red) !important;font-weight:700;}'
        '.khat-lang-sep{color:#ccd4e0 !important;}'

        # ════ الرسائل ════
        'body[data-path="login"] .login-error-banner{'
        'background:#fdf2f3 !important;border:1px solid #f5c6cb !important;'
        'color:#9e1f2e !important;border-radius:var(--kaj-r);'
        'padding:var(--s3) var(--s4);font-size:13.5px;margin-bottom:var(--s4);}'
        'body[data-path="login"] .field-error{'
        'color:#c62839 !important;font-size:12.5px;margin:var(--s1) 0 0;}'

        # ════ الشاشة الضيقة ════
        # لوح الهوية ينطوي: صورة تأخذ نصف شاشة 390px تسرقه من حقول
        # يحتاجها المستخدم. تبقى الهوية في الشعار وحده.
        '@media (max-width:900px){'
        'body[data-path="login"] .for-login{grid-template-columns:1fr;}'
        'body[data-path="login"] .for-login::before{display:none;}'
        'body[data-path="login"] .login-content.page-card{'
        'padding:var(--s8) var(--s5) !important;}'
        '}'
        # شاشة قصيرة جداً: البطاقة تتمدّد وتُمرَّر بدل أن يُقصّ الزرّ.
        '@media (max-height:620px){'
        'body[data-path="login"] .login-content.page-card{'
        'min-height:auto;padding-block:var(--s8) !important;}'
        'body[data-path="login"] .for-login{min-height:auto;}'
        '}'
        '@media (prefers-reduced-motion:reduce){'
        'body[data-path="login"] *{transition:none !important;}}'
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
