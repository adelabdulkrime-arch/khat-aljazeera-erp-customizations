# -*- coding: utf-8 -*-
"""The client's trial account — runs the workshop, does not own the system.

The owner needs an account to hand the client so they can walk the real cycle:
receive a vehicle, open a Work Card, issue parts, invoice, take payment. That
is emphatically NOT the Administrator login, which can also drop doctypes and
rewrite settings.

WHAT IT GETS
  مدير الورشة / Workshop Manager is the core role: create and submit Work
  Cards, vehicles, packages, quotations, invoices, payments — the whole cycle.

  The four EXTRA_ROLES exist for one reason: the dashboards are role-gated
  allow-lists on their Custom HTML Blocks, and Workshop Manager appears in only
  one of them. Without these, four of the seven dashboards render empty and the
  trial looks broken rather than restricted. Each extra role also carries the
  permission set workshop_permissions already granted it, so the lists behind
  each dashboard actually open. Trim this tuple to narrow the account; the
  dashboards it unlocks go dark in step.

  System Manager is deliberately withheld. That is the line between "runs the
  workshop" and "can delete the workshop".

LOGIN NAME
  Frappe keys a User by e-mail — "Admin" alone cannot be the record's ID. So the
  record is EMAIL and USERNAME goes in the username field.

  That field is inert on its own: Frappe only looks a login up by username when
  System Settings.allow_login_using_user_name is on, so the flag is switched on
  here too. It is site-wide by nature — every user gains the option to sign in
  by username; nobody loses the ability to sign in by e-mail, which stays the
  guaranteed route for this account if the flag is ever turned back off.

PASSWORD
  Read from the DEMO_USER_PASSWORD environment variable, never from this file:
  a literal here would sit in git history for good, which is exactly how the
  previous admin password leaked. Set it in Coolify (see .env.example) — the value
  is re-asserted on every migrate, so changing it there rotates the password on
  the next deploy, and a password the client changes in the UI is reverted by
  it. That is the intended contract for a shared trial account.

  With the variable unset the account is still created and repaired, but with no
  password, so it simply cannot be logged into. Failing closed beats baking in a
  guessable default.
"""

import os

import frappe
from frappe.utils.password import update_password

# The User record's ID. Frappe requires an address; nobody needs to read mail
# here, so no welcome mail is sent and the domain need not resolve.
EMAIL = "admin@khataljazeera.om"

# What the client actually types at the login screen.
USERNAME = "Admin"
FIRST_NAME = "مدير الورشة"

PASSWORD_ENV = "DEMO_USER_PASSWORD"

CORE_ROLE = "Workshop Manager"

# Purely to unlock the remaining role-gated dashboards — see the module note.
#   محاسب              → لوحة المحاسبة
#   مدير المستودع      → لوحة المخزون
#   مسؤول المشتريات    → لوحة المشتريات
#   مندوب مبيعات       → لوحة المبيعات
EXTRA_ROLES = ("محاسب", "مدير المستودع", "مسؤول المشتريات", "مندوب مبيعات")

ROLES = (CORE_ROLE,) + EXTRA_ROLES


def _ensure_user():
    """Fetch the trial user, creating it on first run. Returns (doc, created)."""
    if frappe.db.exists("User", EMAIL):
        return frappe.get_doc("User", EMAIL), False

    doc = frappe.get_doc({
        "doctype": "User",
        "email": EMAIL,
        "first_name": FIRST_NAME,
        "enabled": 1,
        "user_type": "System User",
        # Explicit, so the account does not depend on workshop_language running
        # after this step to pick up Arabic.
        "language": "ar",
        "send_welcome_email": 0,
    })
    # send_welcome_email alone is not always honoured on insert; the flag is.
    doc.flags.no_welcome_mail = True
    doc.insert(ignore_permissions=True)
    return doc, True


def _username_is_free(doc):
    """True when USERNAME is unclaimed, or already claimed by this very user."""
    holder = frappe.db.get_value("User", {"username": USERNAME}, "name")
    return not holder or holder == doc.name


def _allow_username_login():
    """Turn on username logins, without which USERNAME is a decorative field.

    Guarded by has_field rather than set blind: if the flag is ever renamed
    upstream, the account should still be created — losing the short login name
    is a nuisance, losing the whole step is not.
    """
    field = "allow_login_using_user_name"
    if not frappe.get_meta("System Settings").has_field(field):
        print("DEMO USER warn: System Settings.%s absent — %r can only sign in "
              "with the e-mail address" % (field, USERNAME))
        return False

    if frappe.db.get_single_value("System Settings", field):
        return True

    frappe.db.set_single_value("System Settings", field, 1)
    return True


def _set_password():
    """Write the password straight to __Auth, bypassing the strength policy.

    Going through the User doc would run password_strength_test, which rejects
    anything as short as the client's chosen password. update_password is the
    same call Frappe's own reset flow ends in, so the stored hash is identical
    in kind — only the policy check is skipped.
    """
    pwd = (os.environ.get(PASSWORD_ENV) or "").strip()
    if not pwd:
        print("DEMO USER warn: %s unset — account left without a password "
              "and cannot be logged into" % PASSWORD_ENV)
        return False

    update_password(EMAIL, pwd)
    return True


def execute():
    doc, created = _ensure_user()

    changed = []

    # A disabled account is the one state that silently defeats the whole point.
    if not doc.enabled:
        doc.enabled = 1
        changed.append("enabled")

    if doc.username != USERNAME:
        if _username_is_free(doc):
            doc.username = USERNAME
            changed.append("username")
        else:
            print("DEMO USER warn: username %r is held by another user — "
                  "this account can only be reached by e-mail" % USERNAME)

    held = {d.role for d in doc.roles}
    added = []
    for role in ROLES:
        if role in held:
            continue
        if not frappe.db.exists("Role", role):
            print("DEMO USER warn: role %r absent — skipped" % role)
            continue
        doc.append("roles", {"role": role})
        added.append(role)

    if changed or added:
        doc.save(ignore_permissions=True)

    by_username = _allow_username_login()
    has_password = _set_password()

    frappe.db.commit()
    print("DEMO USER %s created=%s roles_added=%d password=%s login_name=%s"
          % (EMAIL, created, len(added),
             "set" if has_password else "MISSING",
             USERNAME if by_username else "e-mail only"))
