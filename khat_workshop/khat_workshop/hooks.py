app_name = "khat_workshop"
app_title = "Khat Workshop"
app_publisher = "Khat Al Jazeera"
app_description = "Vehicle-workshop customisations for ERPNext"
app_email = "adelabdulkrime@gmail.com"
app_license = "MIT"

# Re-apply all workshop customisations after every `bench migrate`.
#
# The steps are idempotent by design: they create-or-update DocTypes, roles,
# workspaces and settings. Running them on every migrate reproduces the old
# init.sh behaviour (every deploy re-applied everything, so UI changes shipped
# with the deploy) but through a supported Frappe hook rather than by copying
# files into apps/frappe/frappe/.
#
# Deliberately NOT patches.txt: patches are recorded as applied and run once,
# which would mean a new patch entry for every dashboard tweak.
after_migrate = ["khat_workshop.setup.run_all"]

# عناوين ملفاتنا تحمل بصمة محتواها (‎?v=…‎): المتصفح يخزّنها بلا مراجعة مع الخادم
# (docker/Caddyfile يعطي ما له v سنةً وimmutable)، وأي تعديل يغيّر العنوان فيصل
# فوراً. كانت تُراجَع في كل تحميل: عشرة طلبات تسبق الرسم، ربع ثانية لكلٍّ على
# اتصال بعيد. راجع khat_workshop/fastboot.py.
import hashlib as _hashlib
import os as _os


def _v(path):
    full = _os.path.join(_os.path.dirname(__file__), "public", *path.split("/"))
    with open(full, "rb") as f:
        return "/assets/khat_workshop/%s?v=%s" % (path, _hashlib.md5(f.read()).hexdigest()[:10])


# Desk-level assets, loaded on EVERY desk page.
#
# desk.js (navbar language switcher, logout item, sidebar-header hiding) used to
# be injected inside seven Custom HTML Block scripts, so it only ran on the seven
# dashboards. Opening any standard page — /app/user, /app/role, a Sales Invoice —
# dropped straight back to the stock navbar. Loading it here fixes that and means
# the code exists once instead of seven times.
#
# Plain .js on purpose, NOT a .bundle.js: the runtime image ships no node/yarn,
# so anything needing esbuild could not be built. Plain files only require the
# sites/assets/khat_workshop symlink, which init.sh creates.
#
# pwa.js turns the desk into an installable app (manifest + icons + service
# worker). It is added to BOTH app_include_js (desk) and web_include_js (login /
# portal) so "install" works whether the user triggers it before or after login.
app_include_js = [
    # اللوحات السبع: رسّام واحد يقرأ خريطة النظام من بيانات الإقلاع
    # (extend_bootinfo أدناه). قبل kaj_nav.js لأنه يستعمل فحص الصلاحيات منه.
    _v("js/kaj_dashboard.js"),
    # شريط جانبي واحد ثابت في كل الشاشات، وبلاطات اللوحات في البحث.
    _v("js/kaj_nav.js"),
    # شاشات القوائم: أعمدة من lists.py، وعمود إجراءات مكان الإعجاب والتعليقات.
    _v("js/kaj_list.js"),
    # النماذج والحوارات: «إضافة مستخدم» في خطوة واحدة، والإضافة السريعة للعميل والمورد.
    _v("js/kaj_forms.js"),
    # التقارير: المرشّحات التي في reports.py، وقائمة «…» مختصرة.
    _v("js/kaj_reports.js"),
    _v("js/desk.js"),
    _v("js/pwa.js"),
    # tooltips.js: تلميحات عربية لأيقونات القوائم وأشرطة الأدوات. Frappe يعرض
    # القلب والتعليق وأزرار الصفوف بلا نص ولا title، فالمستخدم يمرّ عليها ولا
    # يعرف وظيفتها — احتكاك يومي على نظام يستخدمه فنّيون لا تقنيون.
    _v("js/tooltips.js"),
]

# RTL fixes for cases where Frappe applies the Arabic direction to Latin text
# and renders it reversed — "Ctrl+/" appeared as "/+Ctrl", and the user's email
# in the sidebar came out backwards. Each rule addresses something seen on the
# rendered screen, not a theoretical case.
app_include_css = [
    _v("css/rtl_fixes.css"),
    # مظهر المكتب: القوائم، شريط الأدوات، رأس الشريط الجانبي.
    _v("css/kaj_desk.css"),
]

# خريطة النظام (اللوحات، بلاطاتها، وأي شريط جانبي لأي شاشة) مع بيانات
# الإقلاع: مصدرها khat_workshop/navigation.py وحده.
extend_bootinfo = "khat_workshop.boot.extend_bootinfo"

# Same PWA bootstrap on the website + login pages (desk assets do not load there).
# login_lang.js: مبدّل لغة على صفحة الدخول. الصفحة تُقدَّم قبل أن يُعرف
# المستخدم، فلا تقرأ تفضيله من حسابه، وFrappe لا يعرض أي وسيلة لتغيير اللغة
# هناك — فمن يجدها بلغة لا يقرؤها يعلق بلا مخرج. يضبط الزر كوكي
# `preferred_language`، وهو ما يقرأه Frappe فعلاً للزائر غير المسجّل
# (frappe/translate.py: "2. Cookie => preferred_language").
web_include_js = [
    _v("js/pwa.js"),
    _v("js/login_lang.js"),
]

# Serve the service worker at the origin root (/sw.js) with an origin-wide scope.
# It cannot be a static file: Frappe's www renderer blacklists .js, and /assets
# files only get a /assets/khat_workshop/ scope — too narrow to control /app.
# See khat_workshop.pwa for the full rationale.
page_renderer = ["khat_workshop.pwa.ServiceWorkerRenderer"]

# Paint the uploaded background onto the login page. Runs server-side for every
# web page; khat_workshop.branding gates it to /login and no-ops when unset.
update_website_context = [
    # Must precede the background hook: it fixes the language for the whole
    # render, so anything rendered after it is translated in the right one.
    "khat_workshop.branding.force_site_language",
    "khat_workshop.branding.inject_login_background",
]

# Register the workshop as an "app" whose route is the dashboard, /desk/home.
#
# This exists to fix where a login lands. frappe's login does
# `redirect_to = get_default_path() or get_home_page()`. get_home_page() already
# returns /desk/home (our dashboard), but get_default_path() shadows it: with
# two desk apps (erpnext, hrms) and no default_app set, it returns bare /desk —
# v16's module-launcher grid, not the dashboard. So every fresh login landed on
# the grid.
#
# get_default_path() resolves default_app through get_route(), which reads this
# hook. Pointing our entry at /desk/home and setting it as the default_app (see
# setup/workshop_default_app) makes get_default_path() return the dashboard, so
# login lands there. It also adds a branded "خط الجزيرة" tile to /apps.
add_to_apps_screen = [
    {
        "name": "khat_workshop",
        "title": "خط الجزيرة",
        # /desk/home, not /desk: ERPNext registers "/desk" as its own route, and
        # the desk resolves the current app by longest matching route — so with
        # a bare /desk the Home workspace was attributed to ERPNext and the
        # sidebar header read "ERPNext" on the system's own landing page.
        "route": "/desk/home",
        # Without a logo the apps screen and the desk sidebar fall back to a
        # letter tile, while every other app shows its mark — the workshop's own
        # app looked the least finished of the three.
        "logo": "/assets/khat_workshop/icons/icon-192.png",
    }
]

# دوالّ تُنادى من قوالب الطباعة باسمها
jinja = {"methods": [
    "khat_workshop.print_template.in_words_ar",
    # قاموس الواجهة من ملف مخزَّن بدل جسم الصفحة (templates/includes/splash_screen.html)
    "khat_workshop.fastboot.kaj_messages_src",
]}

# Work Card automation, plus keeping branding files public.
#
# The costing cannot be a Server Script: it reads Item valuation and the linked
# Stock Entry, and the same code runs on both save and submit — on_submit as
# well as validate because parts cost is only exact once the parts have been
# issued, which happens after the card is submitted. doc_events keeps it in one
# version-controlled place next to the fields it fills
# (see khat_workshop.setup.workshop_labour_costing).
doc_events = {
    "Work Card": {
        "validate": "khat_workshop.costing.compute",
        "on_submit": [
            "khat_workshop.costing.recompute_on_submit",
            # Stamp the vehicle's last/next service date off this job card.
            "khat_workshop.maintenance.set_next_service",
        ],
        # before_submit, not validate: a draft may legitimately be half-filled
        # while the car is still being walked around. What must never happen is
        # work starting on a vehicle whose condition nobody recorded.
        "before_submit": "khat_workshop.intake.validate_intake",
    },
    # Keep the logo and login background public, so the login page (served to
    # logged-out visitors) can actually load them.
    "Website Settings": {
        "validate": "khat_workshop.branding.ensure_public_branding",
    },
    # Compose the printed header/footer/stamp from the uploaded images, and keep
    # those images public so wkhtmltopdf can fetch them while rendering the PDF.
    "Letter Head": {
        "validate": "khat_workshop.print_template.compose",
    },
    # المسمّى الوظيفي يحمل الأدوار القياسية التي تؤدي عمله (khat_workshop/roles.py).
    "User": {
        "before_validate": "khat_workshop.roles.sync_implied",
    },
    # الماركة تتبع الموديل: لا «شيفروليه» مع «تويوتا-كامري».
    "Customer Vehicle": {
        "validate": "khat_workshop.maintenance.brand_follows_model",
    },
    # Total a service package from its lines, applying the package discount.
    "Workshop Package": {
        "validate": "khat_workshop.packages.compute",
    },
}
