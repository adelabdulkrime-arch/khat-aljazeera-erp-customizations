#!/bin/bash
# One-time site creation + workshop customisation.
# Idempotent — safe to re-run on every deploy.
# NO set -e intentionally: we want explicit error handling, not silent exits.

SITE_NAME="${SITE_NAME:-erp.local}"
DB_HOST="${DB_HOST:-db}"
DB_PORT="${DB_PORT:-3306}"

# Defensive: strip any scheme (http://, https://) and trailing path/slash that
# may have been copied from a Coolify-generated domain URL. Frappe site names
# must be a bare hostname. NOTE: the frontend container's FRAPPE_SITE_NAME_HEADER
# uses SITE_NAME raw, so the env var itself must ALSO be a bare hostname for
# nginx routing to match — see .env.example.
SITE_NAME="${SITE_NAME#http://}"
SITE_NAME="${SITE_NAME#https://}"
SITE_NAME="${SITE_NAME%%/*}"

# ── Persistent logging ───────────────────────────────────────────────────────
# Tee everything to a file inside the shared 'sites' volume so the log
# survives even when Coolify removes this container on failure. Retrieve with:
#   docker run --rm -v <project>_sites:/s alpine cat /s/init.log
cd /home/frappe/frappe-bench 2>/dev/null || cd / || true
mkdir -p sites 2>/dev/null || true
exec > >(tee -a sites/init.log) 2>&1

log()  { echo "[init] $(date '+%H:%M:%S') $*"; }
die()  { log "FATAL: $*"; exit 1; }
warn() { log "WARN:  $*"; }

log "=============================================="
log "Khat Al Jazeera ERP — init container start"
log "SITE_NAME = ${SITE_NAME}"
log "DB_HOST   = ${DB_HOST}:${DB_PORT}"
log "PWD       = $(pwd)"
log "whoami    = $(whoami)"
log "=============================================="

# Trace every command from here on (visible in the tee'd log)
set -x

# Activate frappe virtualenv so 'bench' is on PATH
VENV="/home/frappe/frappe-bench/env/bin/activate"
if [ -f "$VENV" ]; then
  # shellcheck disable=SC1090
  source "$VENV"
  log "virtualenv activated"
else
  warn "virtualenv not found at $VENV"
fi

command -v bench || warn "bench not found on PATH"
command -v mysqladmin || warn "mysqladmin not found on PATH"

# Ensure we are in the bench root
cd /home/frappe/frappe-bench || die "Cannot cd to /home/frappe/frappe-bench"

# ── 1. Wait for common_site_config.json (configurator must finish first) ────
log "Waiting for configurator (common_site_config.json)..."
TRIES=0
while true; do
  if python3 -c "import json,sys; c=json.load(open('sites/common_site_config.json')); sys.exit(0 if c.get('db_host') else 1)" 2>/dev/null; then
    log "common_site_config.json is ready."
    break
  fi
  TRIES=$((TRIES + 1))
  [ $TRIES -ge 24 ] && die "common_site_config.json not ready after 2 min"
  sleep 5
done

# ── 2. Wait for MariaDB ──────────────────────────────────────────────────────
log "Waiting for MariaDB at ${DB_HOST}:${DB_PORT}..."
TRIES=0
while true; do
  if mysqladmin ping -h "${DB_HOST}" -P "${DB_PORT}" -u root -p"${DB_ROOT_PASSWORD}" --silent 2>/dev/null; then
    log "MariaDB is up."
    break
  fi
  TRIES=$((TRIES + 1))
  [ $TRIES -ge 36 ] && die "MariaDB not ready after 3 min"
  sleep 5
done

# ── 3. Create site if it does not already exist ──────────────────────────────
if [ ! -d "sites/${SITE_NAME}" ]; then
  log "Creating site: ${SITE_NAME} (takes several minutes)..."
  # Frappe v15/v16 flags: --mariadb-user-host-login-scope replaces the old
  # --no-mariadb-socket; --db-root-username makes the root login explicit.
  bench new-site \
    --mariadb-user-host-login-scope='%' \
    --db-root-username=root \
    --db-root-password="${DB_ROOT_PASSWORD}" \
    --db-host="${DB_HOST}" \
    --db-port="${DB_PORT}" \
    --admin-password="${ADMIN_PASSWORD}" \
    --install-app erpnext \
    "${SITE_NAME}"
  RC=$?
  [ $RC -ne 0 ] && die "bench new-site exited with code $RC"
  log "Site created successfully."
else
  log "Site ${SITE_NAME} already exists — skipping creation."
fi

# Mark as default / current site
echo "${SITE_NAME}" > sites/currentsite.txt
bench use "${SITE_NAME}" 2>/dev/null || true

# host_name so wkhtmltopdf can fetch static assets via the nginx container
bench --site "${SITE_NAME}" set-config host_name "http://frontend:8080" \
  && log "host_name set" || warn "could not set host_name (non-fatal)"

# ── 4. Install the Khat Workshop app, then migrate ───────────────────────────
# The customisations are now a real Frappe app (apps/khat_workshop), installed
# into the venv at image build time. We no longer copy any .py file into
# apps/frappe/frappe/.
#
# Two things must still happen at RUNTIME:
#   1. register the app in sites/apps.txt — that file lives inside the `sites`
#      volume, so anything written at build time would be masked by the mount;
#   2. install the app on the site and migrate. The `after_migrate` hook then
#      re-applies every idempotent setup step, which is what the old
#      copy-and-execute loop did, only through a supported mechanism.
# hrms first: it brings the HR module (payroll, attendance, leave). khat_workshop
# second, since its customisations sit on top of what the other apps provide.
APPS="hrms khat_workshop"

for APP in $APPS; do
  if [ ! -d "apps/${APP}" ]; then
    warn "apps/${APP} missing from the image — skipping"
    continue
  fi

  if grep -qxF "$APP" sites/apps.txt 2>/dev/null; then
    log "$APP already registered in sites/apps.txt"
  else
    # apps.txt may have no trailing newline; add one before appending.
    if [ -s sites/apps.txt ] && [ -n "$(tail -c 1 sites/apps.txt)" ]; then
      echo "" >> sites/apps.txt
    fi
    echo "$APP" >> sites/apps.txt
    log "registered $APP in sites/apps.txt"
  fi

  if bench --site "${SITE_NAME}" list-apps 2>/dev/null | grep -qw "$APP"; then
    log "$APP already installed on ${SITE_NAME}"
  else
    log "installing $APP on ${SITE_NAME}..."
    bench --site "${SITE_NAME}" install-app "$APP" \
      && log "install-app $APP OK" \
      || warn "install-app $APP failed (migrate may still apply setup)"
  fi
done

# Server Scripts must be enabled or the whole automation layer is inert.
#
# Found the hard way: the parts-issue and reversal scripts existed, were visible
# in the UI, and Work Cards submitted without a single error — but nothing was
# ever deducted from stock, because Frappe refuses to run Server Scripts unless
# this flag is set. A system in that state looks perfectly healthy and silently
# never moves inventory.
#
# Set here rather than left to manual configuration, because it lives in
# common_site_config.json inside the sites volume and would otherwise be lost on
# any clean rebuild.
bench set-config -g server_script_enabled true \
  && log "server_script_enabled = true" \
  || warn "could not enable server scripts — automation will NOT run"

# NOTE: the app's static assets are wired up in the Dockerfile, NOT here.
# The image entrypoint runs, on EVERY container start:
#     rm -rf  /home/frappe/frappe-bench/sites/assets
#     ln -s   /home/frappe/frappe-bench/assets  /home/frappe/frappe-bench/sites/assets
# so sites/assets is not a directory in the volume at all — it is a symlink to
# the assets baked into the image. Anything created under it at runtime is
# deleted by the next container start, which is exactly what happened on the
# first attempt.

# Not fatal on failure: init failing would block backend from ever starting
# (depends_on: service_completed_successfully), turning a partial setup problem
# into a total outage. run_all() already isolates per-step failures.
log "running bench migrate (re-applies all setup steps via after_migrate)..."
if bench --site "${SITE_NAME}" migrate; then
  log "migrate OK"
else
  warn "bench migrate FAILED — check the output above"
fi

set +x
log "=============================================="
log "Init complete. ERPNext ready at https://${SITE_NAME}"
log "=============================================="
