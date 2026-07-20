#!/bin/bash
# One-time site creation + workshop customisation.
# Idempotent — safe to re-run on every deploy.
# NO set -e intentionally: we want explicit error handling, not silent exits.

SITE_NAME="${SITE_NAME:-erp.local}"
DB_HOST="${DB_HOST:-db}"
DB_PORT="${DB_PORT:-3306}"

log()  { echo "[init] $(date '+%H:%M:%S') $*"; }
die()  { log "FATAL: $*"; exit 1; }
warn() { log "WARN:  $*"; }

log "=========================================="
log "Khat Al Jazeera ERP — init container start"
log "SITE_NAME   = ${SITE_NAME}"
log "DB_HOST     = ${DB_HOST}:${DB_PORT}"
log "=========================================="

# Activate frappe virtualenv so 'bench' is on PATH
VENV="/home/frappe/frappe-bench/env/bin/activate"
if [ -f "$VENV" ]; then
  # shellcheck disable=SC1090
  source "$VENV"
  log "virtualenv activated"
else
  warn "virtualenv not found at $VENV — bench may not be on PATH"
fi

# Ensure working directory is the bench root
cd /home/frappe/frappe-bench || die "Cannot cd to /home/frappe/frappe-bench"
log "cwd = $(pwd)"

# ── 1. Wait for common_site_config.json (configurator must finish first) ────
log "Waiting for configurator (common_site_config.json)..."
TRIES=0
while true; do
  CHECK=$(python3 -c "
import json, sys
try:
    c = json.load(open('sites/common_site_config.json'))
    sys.exit(0 if c.get('db_host') else 1)
except Exception as e:
    sys.exit(1)
" 2>/dev/null)
  RC=$?
  if [ $RC -eq 0 ]; then
    log "common_site_config.json is ready."
    break
  fi
  TRIES=$((TRIES + 1))
  [ $TRIES -ge 24 ] && die "common_site_config.json not ready after 2 min"
  log "  still waiting... (${TRIES}/24)"
  sleep 5
done

# ── 2. Wait for MariaDB ──────────────────────────────────────────────────────
log "Waiting for MariaDB at ${DB_HOST}:${DB_PORT}..."
TRIES=0
while true; do
  if mysqladmin ping -h "${DB_HOST}" -P "${DB_PORT}" \
                    -u root -p"${DB_ROOT_PASSWORD}" --silent 2>/dev/null; then
    log "MariaDB is up."
    break
  fi
  TRIES=$((TRIES + 1))
  [ $TRIES -ge 36 ] && die "MariaDB not ready after 3 min"
  log "  still waiting... (${TRIES}/36)"
  sleep 5
done

# ── 3. Create site if it does not already exist ──────────────────────────────
if [ ! -d "sites/${SITE_NAME}" ]; then
  log "Creating site: ${SITE_NAME} (this takes several minutes)..."
  bench new-site \
    --no-mariadb-socket \
    --db-host "${DB_HOST}" \
    --db-port "${DB_PORT}" \
    --db-root-password "${DB_ROOT_PASSWORD}" \
    --db-password "${MYSQL_PASSWORD}" \
    --admin-password "${ADMIN_PASSWORD}" \
    --install-app erpnext \
    "${SITE_NAME}"
  RC=$?
  if [ $RC -ne 0 ]; then
    die "bench new-site exited with code $RC"
  fi
  log "Site created successfully."
else
  log "Site ${SITE_NAME} already exists — skipping creation."
fi

# Mark as default site (needed by bench commands below)
echo "${SITE_NAME}" > sites/currentsite.txt
log "currentsite.txt written."

# Set host_name so wkhtmltopdf can fetch static assets via the nginx container
bench --site "${SITE_NAME}" set-config host_name "http://frontend:8080" \
  && log "host_name set to http://frontend:8080" \
  || warn "Could not set host_name (non-fatal)"

# ── 4. Apply workshop customisations in the correct order ────────────────────
SCRIPTS=(
  workshop_futuristic          # shared CSS/JS — must be first
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
)

log "Applying workshop customisations..."
for module in "${SCRIPTS[@]}"; do
  src="/opt/workshop-scripts/${module}.py"
  dst="apps/frappe/frappe/${module}.py"

  if [ ! -f "$src" ]; then
    warn "Script not found — skipping: $src"
    continue
  fi

  cp "$src" "$dst"
  bench --site "${SITE_NAME}" execute "frappe.${module}.execute" 2>&1
  RC=$?
  if [ $RC -eq 0 ]; then
    log "  OK    ${module}"
  else
    warn "  ${module} returned code ${RC} (continuing)"
  fi
done

log "=========================================="
log "Init complete. ERPNext ready at: https://${SITE_NAME}"
log "=========================================="
