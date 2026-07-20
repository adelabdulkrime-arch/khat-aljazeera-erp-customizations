#!/bin/bash
# One-time site creation + workshop customisation script.
# Safe to re-run: site creation is skipped if the site already exists,
# and all workshop scripts are idempotent.
set -eo pipefail

SITE_NAME="${SITE_NAME:-erp.local}"
DB_HOST="${DB_HOST:-db}"
DB_PORT="${DB_PORT:-3306}"

log() { echo "[init] $*"; }

# ── 1. Wait for common_site_config.json (configurator must finish first) ────
log "Waiting for configurator to write common_site_config.json..."
until python3 - <<'EOF' 2>/dev/null
import json, sys
with open("sites/common_site_config.json") as f:
    c = json.load(f)
assert c.get("db_host"), "db_host missing"
EOF
do
  sleep 5
done
log "common_site_config.json is ready."

# ── 2. Wait for MariaDB ──────────────────────────────────────────────────────
log "Waiting for MariaDB at ${DB_HOST}:${DB_PORT}..."
until mysqladmin ping -h "${DB_HOST}" -P "${DB_PORT}" \
      -u root -p"${DB_ROOT_PASSWORD}" --silent 2>/dev/null; do
  sleep 5
done
log "MariaDB is up."

# ── 3. Create site (skipped if it already exists) ───────────────────────────
if [ ! -d "sites/${SITE_NAME}" ]; then
  log "Creating site: ${SITE_NAME}"
  bench new-site \
    --no-mariadb-socket \
    --db-host "${DB_HOST}" \
    --db-port "${DB_PORT}" \
    --db-root-password "${DB_ROOT_PASSWORD}" \
    --db-password "${MYSQL_PASSWORD}" \
    --admin-password "${ADMIN_PASSWORD}" \
    --install-app erpnext \
    --set-default \
    "${SITE_NAME}"
  log "Site created."
else
  log "Site ${SITE_NAME} already exists — skipping creation."
fi

# Ensure currentsite.txt points to our site (needed by bench commands below)
echo "${SITE_NAME}" > sites/currentsite.txt

# Set host_name to the internal nginx container so wkhtmltopdf can fetch
# static assets when generating PDF invoices (see HANDOFF.md §6).
bench --site "${SITE_NAME}" set-config host_name "http://frontend:8080"

# ── 4. Apply workshop customisations in the required order ───────────────────
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
    log "  SKIP  ${module}.py (not found)"
    continue
  fi

  cp "$src" "$dst"

  if bench --site "${SITE_NAME}" execute "frappe.${module}.execute" 2>&1; then
    log "  OK    ${module}"
  else
    log "  WARN  ${module} returned an error (continuing)"
  fi
done

log "Init complete. ERPNext is ready at https://${SITE_NAME}"
