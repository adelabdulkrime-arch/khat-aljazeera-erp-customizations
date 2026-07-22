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
