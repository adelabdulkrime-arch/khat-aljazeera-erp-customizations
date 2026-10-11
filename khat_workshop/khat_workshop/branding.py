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

    # صفحة الدخول كصفحة واحدة متناسقة، لا بطاقة عائمة فوق صورة.
    #
    # ما كان مكسوراً: الخلفية كانت `background-size:cover` على <body>. وcover
    # يقيس بوحدات CSS لا بالبكسل الفيزيائي، فكلما صغّر المستخدم الصفحة
    # (Ctrl -) اتّسع إطار العرض منطقياً وتضخّم الشعار معه حتى ابتلع الشاشة
    # وصارت البطاقة غير مقروءة فوقه. رُصد في لقطة عند التصغير.
    #
    # الحل: الخلفية طبقة مستقلة `position:fixed` لا تتبع تدفّق الصفحة، وحجمها
    # مُقيَّد بـclamp على min(vw,vh) فيبقى الشعار في نطاق معقول عند أي تكبير.
    # فوقها طبقة تعتيم منفصلة — فصل الصورة عن التعتيم يجعل ضبط كلٍّ منهما
    # مستقلاً بدل تدرّج واحد يخدم الاثنين بإخفاق.
    #
    # والبطاقة زجاجية: backdrop-filter فوق لون كحلي شبه شفاف، فيظهر الشعار
    # من خلالها بوضوح مضبوط مع بقاء النص مقروءاً. اللون الصلب هو القيمة
    # الاحتياطية لمتصفح لا يدعم backdrop-filter.
    style = (
        '<style id="kaj-login-bg">'
        ':root{--kaj-navy:#16233d;--kaj-navy-2:#1e3050;--kaj-red:#a52834;'
        '--kaj-gold:#f0b429;}'
        # ── الخلفية: طبقتان مستقلتان ──
        # ::before الصورة، ::after التعتيم. كلاهما fixed فلا يتأثر بتمرير
        # الصفحة ولا بارتفاع محتواها.
        'body[data-path="login"]{background:var(--kaj-navy);min-height:100vh;}'
        'body[data-path="login"]::before{content:"";position:fixed;inset:0;'
        'z-index:0;pointer-events:none;'
        'background-image:url("__KAJ_BG__");'
        'background-repeat:no-repeat;background-position:center;'
        # القيد الحاسم: الحجم مربوط بأصغر البُعدين لا بإطار العرض كاملاً،
        # ومحصور بين 420 و900 بكسل. فعند التصغير لا يتضخّم الشعار، وعند
        # التكبير لا يتضاءل حتى يختفي.
        'background-size:clamp(420px,min(78vw,88vh),900px) auto;'
        # الصورة مربّعة على خلفية كحلية سادة، فحوافّها تظهر كمستطيل ملصق
        # بأربعة أضلاع حادّة — رُصد في لقطة الشاشة. قناع إشعاعي يُذيب
        # الحوافّ في لون الهوية فتبدو الصورة نسيجاً لا صورة موضوعة.
        #
        # نسب القناع تُقاس من صندوق العنصر (إطار العرض كاملاً) لا من الصورة،
        # والصورة أصغر منه بكثير ومتوسّطة — فقناع بنسب مئوية يرسم بيضاوية
        # أوسع من الصورة ولا يلمس حوافّها أبداً، وتبقى حادّة. لذا يُقاس
        # القناع بنفس وحدة حجم الصورة ويُوضع في مركزها.
        '-webkit-mask-image:radial-gradient(closest-side,#000 55%,transparent 100%);'
        'mask-image:radial-gradient(closest-side,#000 55%,transparent 100%);'
        '-webkit-mask-size:clamp(420px,min(78vw,88vh),900px) '
        'clamp(420px,min(78vw,88vh),900px);'
        'mask-size:clamp(420px,min(78vw,88vh),900px) '
        'clamp(420px,min(78vw,88vh),900px);'
        '-webkit-mask-position:center;mask-position:center;'
        '-webkit-mask-repeat:no-repeat;mask-repeat:no-repeat;'
        # شفافية خفيفة إضافية: الشعار حاضر لكنه لا يزاحم البطاقة.
        'opacity:.55;}'
        'body[data-path="login"]::after{content:"";position:fixed;inset:0;'
        'z-index:1;pointer-events:none;'
        # تعتيم متدرّج خفيف: الصورة صارت معتّمة أصلاً بـopacity والقناع،
        # فتعتيم إضافي ثقيل كان سيمحوها تماماً. الضبابية في البطاقة هي ما
        # يضمن قراءة النص لا حجب الخلفية.
        'background:radial-gradient(ellipse at center,rgba(12,20,36,.55) 0%,'
        'rgba(12,20,36,.45) 50%,rgba(12,20,36,.40) 100%);}'
        # المحتوى فوق الطبقتين.
        'body[data-path="login"] .page-container,'
        'body[data-path="login"] .for-login,'
        'body[data-path="login"] section{position:relative;z-index:2;}'
        # ── التوسيط الرأسي ──
        # البطاقة كانت تبدأ من أعلى الصفحة فتطفو لأعلى عند التصغير.
        #
        # ‏min-height:100vh على .for-login وحدها خطأ: الغلاف الذي يحويها
        # (.page-content-wrapper) يحمل padding-top:60px، فيصير مجموع
        # الارتفاعين إطار عرض كامل + 60px ويخرج أسفل البطاقة عن الشاشة —
        # قِيس فعلياً: أسفل البطاقة 629px وإطار العرض 587px، فزرّ «الدخول
        # برابط البريد» مقصوص. السلسلة فُحصت في المتصفح لا بالتخمين:
        # body ← div ← .page-content-wrapper ← main.container ← .page_content
        # ← div ← section.for-login ← .login-content.page-card
        #
        # الحل: نُلغي الحشو العلوي من الغلاف ونجعله هو صاحب ارتفاع الشاشة،
        # فتتوسّط البطاقة داخله بلا فائض. وsafe center يحاذي للبداية حين
        # يطول المحتوى عن الشاشة بدل قصّ طرفيه معاً بلا إمكان تمرير.
        'body[data-path="login"] .page-content-wrapper{padding-top:0 !important;'
        'min-height:100vh;display:flex;flex-direction:column;}'
        'body[data-path="login"] main.container,'
        'body[data-path="login"] .page_content{flex:1 1 auto;display:flex;'
        'flex-direction:column;min-height:0 !important;}'
        'body[data-path="login"] .page_content > div{flex:1 1 auto;display:flex;'
        'flex-direction:column;}'
        'body[data-path="login"] .for-login{background:none;border:0;'
        'box-shadow:none;min-height:0;flex:1 1 auto;display:flex;'
        'flex-direction:column;align-items:center;justify-content:safe center;'
        'padding:24px 0;}'
        # ── البطاقة الزجاجية ──
        'body[data-path="login"] .login-content.page-card{'
        # اللون الصلب أولاً: قيمة احتياطية لمن لا يدعم backdrop-filter.
        'background:rgba(16,27,48,.80);'
        'border:1px solid rgba(255,255,255,.14);'
        'border-radius:16px;'
        'box-shadow:0 24px 60px rgba(0,0,0,.50),0 1px 0 rgba(255,255,255,.08) inset;'
        # حدّ أدنى يمنع انكماش البطاقة عند التصغير. وmax-width صريح لأن
        # login.bundle.css يفرض max-width:371px على .for-login .page-card،
        # فيقصّ عرضنا بلا أن يظهر ذلك في قاعدة العرض نفسها — رُصد بقراءة
        # القواعد المطبَّقة في المتصفح.
        'min-width:340px;width:min(92vw,400px);max-width:400px !important;'
        'padding:clamp(22px,2.4vw,32px) clamp(20px,2.2vw,30px);'
        # خط أساسي لا ينزل تحت 15px مهما صغرت الصفحة.
        'font-size:clamp(15px,1.05vw,16px);}'
        # @supports يطبّق الزجاج على الداعمين فقط، فلا يفقد غيرهم التعتيم.
        '@supports ((backdrop-filter:blur(1px)) or (-webkit-backdrop-filter:blur(1px))){'
        'body[data-path="login"] .login-content.page-card{'
        'background:rgba(15,23,42,.58);'
        '-webkit-backdrop-filter:blur(14px) saturate(130%);'
        'backdrop-filter:blur(14px) saturate(130%);}}'
        # ── النصوص ──
        'body[data-path="login"] .for-login h4,'
        'body[data-path="login"] .page-card h4,'
        'body[data-path="login"] h1,body[data-path="login"] h3{'
        'color:#fff !important;font-weight:700;letter-spacing:.2px;'
        'font-size:clamp(19px,1.5vw,23px);}'
        # التباين: كان rgba(.62) ≈ 3.4:1 على الزجاج — دون عتبة WCAG AA.
        # رُفع إلى .88 للعنوان الفرعي و.80 للتسميات، وكلاهما يتجاوز 4.5:1.
        'body[data-path="login"] .page-card-subtitle,'
        'body[data-path="login"] .text-muted{'
        'color:rgba(255,255,255,.88) !important;'
        'font-size:clamp(13.5px,.95vw,14.5px);}'
        'body[data-path="login"] label,'
        'body[data-path="login"] .form-label{color:rgba(255,255,255,.80) !important;'
        'font-size:clamp(13.5px,.95vw,14.5px);font-weight:500;}'
        # ── الحقول ──
        'body[data-path="login"] .form-control,'
        'body[data-path="login"] input[type="text"],'
        'body[data-path="login"] input[type="email"],'
        'body[data-path="login"] input[type="password"]{'
        'background:rgba(255,255,255,.09) !important;'
        'border:1px solid rgba(255,255,255,.20) !important;'
        'color:#fff !important;border-radius:10px;'
        'height:clamp(42px,3.2vw,46px);font-size:clamp(14px,1vw,15px);'
        'transition:border-color .16s,background .16s;}'
        'body[data-path="login"] .form-control:focus,'
        'body[data-path="login"] input:focus{'
        'background:rgba(255,255,255,.14) !important;'
        'border-color:var(--kaj-gold) !important;'
        'box-shadow:0 0 0 3px rgba(240,180,41,.18) !important;}'
        # النص الإرشادي كان rgba(.34) — غير مقروء عملياً.
        'body[data-path="login"] input::placeholder{'
        'color:rgba(255,255,255,.52) !important;}'
        'body[data-path="login"] .field-icon,'
        'body[data-path="login"] .toggle-password,'
        'body[data-path="login"] .input-group-text{'
        'color:rgba(255,255,255,.55) !important;}'
        # ── الأزرار ──
        # .btn-login يحمل صنف btn-default في هذا الإصدار، فلا بدّ من ترتيبه
        # قبل قاعدة btn-default الثانوية وإلا أعادته رمادياً.
        'body[data-path="login"] .btn-primary,'
        'body[data-path="login"] .btn-login.btn-default,'
        'body[data-path="login"] .btn-login{'
        'background:var(--kaj-red) !important;border:0 !important;'
        'color:#fff !important;border-radius:10px;'
        'height:clamp(44px,3.4vw,48px);font-weight:700;'
        'font-size:clamp(14.5px,1.05vw,15.5px);'
        'box-shadow:0 6px 18px rgba(165,40,52,.38);'
        'transition:filter .16s,transform .16s;}'
        'body[data-path="login"] .btn-login:hover{filter:brightness(1.12);'
        'transform:translateY(-1px);}'
        # «الدخول برابط البريد» مسار ثانوي: بلا خلفية ولا إطار فلا يزاحم
        # الزر الأساسي بصرياً. كان يبدو زرّاً مكافئاً له تماماً.
        'body[data-path="login"] .btn-login-option,'
        'body[data-path="login"] .btn-login-with-email-link{'
        'background:transparent !important;border:0 !important;'
        'color:rgba(255,255,255,.72) !important;'
        'height:auto !important;min-height:34px;font-weight:500;'
        'font-size:clamp(13px,.92vw,13.8px);'
        'text-decoration:underline;text-underline-offset:3px;'
        'box-shadow:none !important;}'
        'body[data-path="login"] .btn-login-option:hover,'
        'body[data-path="login"] .btn-login-with-email-link:hover{'
        'background:transparent !important;color:#fff !important;}'
        # أزرار أخرى (العودة، إعادة الإرسال) تبقى ثانوية عادية.
        'body[data-path="login"] .btn-default:not(.btn-login):not(.btn-login-option),'
        'body[data-path="login"] .btn-secondary{'
        'background:rgba(255,255,255,.10) !important;'
        'border:1px solid rgba(255,255,255,.18) !important;'
        'color:rgba(255,255,255,.88) !important;border-radius:10px;'
        'height:clamp(42px,3.2vw,46px);}'
        # ── الروابط ──
        'body[data-path="login"] a{color:var(--kaj-gold) !important;'
        'text-decoration:none;}'
        'body[data-path="login"] a:hover{text-decoration:underline;}'
        # «هل نسيت كلمة المرور؟» هو المسار الأساسي للاستعادة، فيبقى ذهبياً
        # بارزاً. كان يرث text-align:left من Frappe فيلتصق بالحافة اليسرى في
        # واجهة عربية — start يتبع اتجاه الصفحة فيعمل في الاتجاهين.
        'body[data-path="login"] .forgot-password-message{'
        'text-align:start !important;margin:8px 0 0;}'
        'body[data-path="login"] .forgot-password-message a{'
        'font-size:clamp(13px,.95vw,14px);font-weight:600;}'
        'body[data-path="login"] .page-card-actions{text-align:start !important;}'
        'body[data-path="login"] .btn-login{margin-top:14px;}'
        'body[data-path="login"] .btn-login + .btn,'
        'body[data-path="login"] .btn-login + a.btn{margin-top:8px;}'
        # ── خانة «تذكّرني» ──
        # تُحقن بجافاسكربت (login_lang.js) لأن Frappe لا يصدرها في الصفحة.
        'body[data-path="login"] .kaj-remember{'
        'display:flex;align-items:center;gap:8px;'
        'font-size:clamp(13px,.95vw,14px);color:rgba(255,255,255,.80);'
        'cursor:pointer;user-select:none;}'
        'body[data-path="login"] .kaj-remember input{'
        'width:16px;height:16px;margin:0;accent-color:var(--kaj-red);'
        'cursor:pointer;flex:0 0 auto;}'
        'body[data-path="login"] .kaj-remember:hover{color:#fff;}'
        # صفّ واحد يجمع «تذكّرني» و«نسيت كلمة المرور» على طرفي البطاقة.
        'body[data-path="login"] .kaj-authrow{'
        'display:flex;align-items:center;justify-content:space-between;'
        'gap:12px;flex-wrap:wrap;margin-top:12px;}'
        'body[data-path="login"] .kaj-authrow .kaj-remember,'
        'body[data-path="login"] .kaj-authrow .forgot-password-message{margin:0;}'
        # ── الشعار داخل البطاقة ──
        # كان 72px فيُقرأ كزخرفة صغيرة؛ تكبيره يجعله عنوان البطاقة.
        'body[data-path="login"] .for-login img,'
        'body[data-path="login"] .page-card img,'
        'body[data-path="login"] .app-logo{'
        'width:clamp(84px,7vw,104px) !important;height:auto !important;'
        'max-height:none;display:block;margin:0 auto 16px;'
        'border-radius:18px;border:0;'
        # ظل خفيف يفصل الشعار عن الزجاج خلفه بدل أن يسبح فيه.
        'box-shadow:0 8px 24px rgba(0,0,0,.35);}'
        'body[data-path="login"] .page-card-head,'
        'body[data-path="login"] .page-card-head-text{text-align:center;}'
        'body[data-path="login"] .form-group{margin-bottom:14px !important;}'
        # ── الهاتف ──
        # البطاقة تملأ الشاشة فلا يُرى الشعار خلفها؛ نكتفي بتدرّج الهوية
        # ونوقف الضبابية — مكلفة على معالجات الهواتف بلا فائدة هنا.
        '@media (max-width:820px){'
        # القناع لا معنى له مع cover: الصورة تملأ الشاشة فلا حوافّ تُذاب.
        'body[data-path="login"]::before{background-size:cover;opacity:.35;'
        '-webkit-mask-image:none;mask-image:none;}'
        'body[data-path="login"] .login-content.page-card{'
        'min-width:0;width:min(94vw,400px);'
        # حشو أقلّ على الهاتف: البطاقة كانت تتجاوز أسفل الشاشة بـ24px عند
        # 390×844 — قِيس فعلياً. وتقليل الحشو وحده لا يكفي حين تقصر الشاشة
        # أكثر، فـoverflow-y:auto يجعل البطاقة نفسها قابلة للتمرير بدل أن
        # يُقصّ زر الدخول بلا وسيلة للوصول إليه.
        'padding:20px 18px;max-height:calc(100vh - 32px);overflow-y:auto;'
        '-webkit-backdrop-filter:none;backdrop-filter:none;'
        'background:rgba(16,27,48,.90);}'
        # الحاوية تلتزم ارتفاع الشاشة فلا تدفع البطاقة خارجها.
        'body[data-path="login"] .for-login{padding:16px 0;}}'
        # تقليل الحركة لمن يطلبها في إعدادات نظامه.
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
