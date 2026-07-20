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

# ── 4. Apply workshop customisations in the required order ───────────────────
SCRIPTS=(
  workshop_setup               # creates all custom DocTypes — MUST be first
  workshop_futuristic          # shared CSS/JS design layer
  workshop_home
  workshop_dashboard
  workshop_accounting
  workshop_inventory
  workshop_purchasing
  workshop_sales
  workshop_general_settings
  workshop_scripts
  workshop_gl_stock_integration
  workshop_invoice_whatsapp
  workshop_translations
  workshop_oman_setup2         # retag chart of accounts to OMR (before currency switch)
  workshop_oman_setup          # Oman localisation: OMR currency, 5% VAT, timezone
)

log "Applying workshop customisations..."
for module in "${SCRIPTS[@]}"; do
  src="/opt/workshop-scripts/${module}.py"
  dst="apps/frappe/frappe/${module}.py"
  if [ ! -f "$src" ]; then
    warn "not found, skipping: $src"
    continue
  fi
  cp "$src" "$dst"
  if bench --site "${SITE_NAME}" execute "frappe.${module}.execute"; then
    log "  OK    ${module}"
  else
    warn "  ${module} failed (continuing)"
  fi
done

set +x
log "=============================================="
log "Init complete. ERPNext ready at https://${SITE_NAME}"
log "=============================================="
