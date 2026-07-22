ARG ERPNEXT_VERSION=v16
FROM frappe/erpnext:${ERPNEXT_VERSION}

USER root

# MariaDB client so init.sh can poll the DB before bench new-site
RUN apt-get update \
    && apt-get install -y --no-install-recommends default-mysql-client \
    && rm -rf /var/lib/apt/lists/*

# The Khat Workshop app. Previously these were loose workshop_*.py scripts
# staged in /opt and copied into apps/frappe/frappe/ at runtime — i.e. our code
# was written into the framework itself. Now it is a real Frappe app.
COPY --chown=frappe:frappe khat_workshop /home/frappe/frappe-bench/apps/khat_workshop

# One-time init entrypoint
COPY --chown=frappe:frappe docker/init.sh /opt/init.sh
# Strip Windows CRLF line endings that break bash path resolution on Linux
RUN sed -i 's/\r$//' /opt/init.sh && chmod +x /opt/init.sh

# Backup target. Created here (owned by frappe) so that when Docker first
# populates the named `backups` volume it inherits frappe ownership. Without
# this the volume is created root-owned, the container runs as frappe, and
# every backup fails with Frappe's misleading "Database or site_config.json
# may be corrupted" — which is really just EACCES.
RUN mkdir -p /backups && chown frappe:frappe /backups

USER frappe
WORKDIR /home/frappe/frappe-bench

# Install the app into the bench virtualenv, editable — the same way frappe and
# erpnext themselves are installed. This makes `khat_workshop` importable by
# every service, which is only possible because ALL services now build from
# this image (see the x-frappe-image anchor in docker-compose.yml).
#
# Registering the app with the SITE happens at runtime in init.sh, not here:
# sites/apps.txt lives inside the `sites` volume and anything written to it at
# build time would be masked the moment that volume is mounted.
RUN /home/frappe/frappe-bench/env/bin/pip install --no-cache-dir \
        -e /home/frappe/frappe-bench/apps/khat_workshop

# Expose the app's static files at /assets/khat_workshop/... exactly the way the
# image already does it for frappe and erpnext:
#     assets/frappe  -> apps/frappe/frappe/public
#     assets/erpnext -> apps/erpnext/erpnext/public
#
# This MUST be baked into the image rather than created at runtime. The image
# entrypoint does, on every single container start:
#     rm -rf sites/assets && ln -s /home/frappe/frappe-bench/assets sites/assets
# so sites/assets is a symlink into the image, and anything written under it at
# runtime is wiped by the next start.
#
# `bench build` would normally do this, but it needs node/yarn and this runtime
# image has neither. A plain symlink is all a non-bundled .js file requires.
RUN ln -sfn /home/frappe/frappe-bench/apps/khat_workshop/khat_workshop/public \
            /home/frappe/frappe-bench/assets/khat_workshop

# NOTE: deliberately NO `CMD` override here.
# The base image ships CMD ["start.sh"], which is what boots gunicorn for the
# backend service. This Dockerfile used to end with CMD ["/opt/init.sh"], which
# was harmless while only `init` used the image — but once every service builds
# from it, `backend` inherited that CMD and ran the init script instead of
# gunicorn. nginx then had no upstream and the whole site returned 502.
# `init` sets its own entrypoint in docker-compose.yml, so it does not need a
# default here.
