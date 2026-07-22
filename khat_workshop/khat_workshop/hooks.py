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
