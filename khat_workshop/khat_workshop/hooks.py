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
app_include_js = "/assets/khat_workshop/js/desk.js"

# Paint the uploaded background onto the login page. Runs server-side for every
# web page; khat_workshop.branding gates it to /login and no-ops when unset.
update_website_context = ["khat_workshop.branding.inject_login_background"]

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
        "route": "/desk/home",
    }
]

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
        "on_submit": "khat_workshop.costing.recompute_on_submit",
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
}
