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

    style = (
        '<style id="kaj-login-bg">'
        'body[data-path="login"]{'
        'background-image:linear-gradient(rgba(0,0,0,.35),rgba(0,0,0,.55)),url("%s");'
        'background-size:cover;background-position:center;background-attachment:fixed;}'
        '</style>'
    ) % frappe.utils.escape_html(safe)

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
        f = frappe.get_doc("File", fname)
        if f.is_private:
            f.is_private = 0
            f.save(ignore_permissions=True)   # moves the file, rewrites file_url
            doc.set(field, f.file_url)
