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

import frappe


def inject_login_background(context):
    # Gate strictly to the login route. context.path is the www page name.
    path = (context.get("path") or "").strip("/")
    if path != "login":
        return

    bg = frappe.db.get_single_value("Website Settings", "login_background")
    if not bg:
        return

    style = (
        '<style id="kaj-login-bg">'
        'body[data-path="login"]{'
        'background-image:linear-gradient(rgba(0,0,0,.35),rgba(0,0,0,.55)),url("%s");'
        'background-size:cover;background-position:center;background-attachment:fixed;}'
        '</style>'
    ) % frappe.utils.escape_html(bg)

    # head_html is what base.html renders inside <head>; append so we never
    # clobber anything another hook may have set.
    context.head_html = (context.get("head_html") or "") + style
