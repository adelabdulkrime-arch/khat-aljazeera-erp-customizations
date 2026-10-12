# -*- coding: utf-8 -*-
"""Put the uploaded login-page background onto the login page.

Frappe has no login-background field — the logo, favicon and splash image are
built in, but the full-page background behind the login card is not. So this
adds the missing half: a custom field holds the image (see
setup/workshop_branding) and this hook paints it on.

update_website_context runs server-side for every web page, so the style is
injected only when the page being rendered is /login — nothing is added to any
other page. The design itself is public/css/login.css; this module only
inlines it and hands it the per-site values (background image, tagline).
"""

import json
import os
import re
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


_CSS_CACHE = {}


def _login_css():
    """Return public/css/login.css minified, re-read only when the file changes.

    The stylesheet lives in a real .css file so it can be linted, diffed and
    tested in a browser, instead of being assembled from Python string
    fragments — where one mistyped colour value (a stray word inside a hex
    code) once shipped unnoticed. It is inlined rather than linked: the login
    page is the first thing a visitor loads, so a separate request on a slow
    link shows an unstyled page first, and the frontend container serves a
    baked copy of /assets that only a rebuild refreshes.
    """
    path = frappe.get_app_path("khat_workshop", "public", "css", "login.css")
    mtime = os.path.getmtime(path)
    hit = _CSS_CACHE.get(path)
    if hit and hit[0] == mtime:
        return hit[1]

    with open(path, encoding="utf-8") as fh:
        css = fh.read()
    css = re.sub(r"/\*.*?\*/", "", css, flags=re.S)       # comments
    css = re.sub(r"\s+", " ", css)                        # whitespace
    css = re.sub(r"\s*([{};,>])\s*", r"\1", css)          # around punctuation
    css = css.strip()
    _CSS_CACHE[path] = (mtime, css)
    return css


def _css_string(text):
    """Quote text as a CSS string. JSON string syntax is a subset of CSS's;
    "</" is broken up so the value can never close the <style> element."""
    return json.dumps(text, ensure_ascii=False).replace("</", "<\\/")


def inject_login_background(context):
    # Gate strictly to the login route. context.path is the www page name.
    path = (context.get("path") or "").strip("/")
    if path != "login":
        return

    # Per-site values the stylesheet reads as custom properties: the uploaded
    # background and the panel's tagline. The tagline goes through _() so it
    # follows the language force_site_language() has just fixed for this
    # render — it is the one piece of copy in the page that is ours, not the
    # framework's.
    bg = frappe.db.get_single_value("Website Settings", "login_background")
    # Uploaded filenames routinely carry spaces and Arabic characters.
    # Percent-encode (keeping the slashes) so the url() is unambiguous.
    bg_value = 'url("%s")' % quote(bg, safe="/") if bg else "none"
    tagline = frappe._("إدارة الورشة بدقّة، من الاستلام إلى التسليم.")

    style = (
        '<style id="kaj-login-vars">body[data-path="login"]{'
        "--kaj-bg:%s;--kaj-tagline:%s;}</style>"
        '<style id="kaj-login-css">%s</style>'
    ) % (bg_value, _css_string(tagline), _login_css())

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
