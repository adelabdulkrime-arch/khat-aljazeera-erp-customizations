ARG ERPNEXT_VERSION=v16

# ── Stage 1: build the hrms (Frappe HR) assets ───────────────────────────────
# HR left ERPNext core at v14 and lives in the separate `hrms` app. Simply
# pip-installing it is not enough: its JS/CSS bundles have to be built, or every
# HR screen loads broken.
#
# The base image does ship node (via nvm, at ~/.nvm/versions/node/*/bin), but
# not yarn, and node is absent from the default PATH in some shells — which is
# exactly why a first check for it came back empty. Rather than depend on that,
# this stage installs a known node + yarn explicitly and runs
# `bench build --app hrms`.
#
# Keeping it as a separate stage means the build toolchain, the git clone and
# ~750MB of SPA node_modules stay out of the final image; only the built app is
# copied across.
FROM frappe/erpnext:${ERPNEXT_VERSION} AS hrms-builder

USER root
RUN apt-get update \
    && apt-get install -y --no-install-recommends git curl ca-certificates \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y --no-install-recommends nodejs \
    && npm install -g yarn \
    && rm -rf /var/lib/apt/lists/*

USER frappe
WORKDIR /home/frappe/frappe-bench

RUN bench get-app --branch version-16 --skip-assets hrms \
    && bench build --app hrms

# The freshly cloned app is ~806MB. Almost none of that is needed at runtime:
#   - .git            full clone history
#   - node_modules    at the top level AND nested inside frontend/ and roster/,
#                     which are separate Vue SPAs (the HR PWA). Their BUILT
#                     output already lives in hrms/hrms/public; the sources and
#                     their dependencies do not need to ship.
# Removing only the top-level node_modules left 790MB, hence the recursive find.
RUN rm -rf apps/hrms/.git \
    && find apps/hrms -type d -name node_modules -prune -exec rm -rf {} + \
    && find apps/hrms -type d -name .git -prune -exec rm -rf {} + \
    && cp sites/assets/assets.json /tmp/hrms-assets.json \
    && cp sites/assets/assets-rtl.json /tmp/hrms-assets-rtl.json \
    && du -sh apps/hrms

# ── Stage 2: the runtime image ───────────────────────────────────────────────
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
COPY --chown=frappe:frappe docker/merge-assets.py /opt/merge-assets.py
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

# ── Frappe HR (hrms), built in stage 1 ───────────────────────────────────────
COPY --from=hrms-builder --chown=frappe:frappe \
     /home/frappe/frappe-bench/apps/hrms /home/frappe/frappe-bench/apps/hrms
COPY --from=hrms-builder --chown=frappe:frappe \
     /tmp/hrms-assets.json /tmp/hrms-assets-rtl.json /tmp/

RUN /home/frappe/frappe-bench/env/bin/pip install --no-cache-dir \
        -e /home/frappe/frappe-bench/apps/hrms \
    && ln -sfn /home/frappe/frappe-bench/apps/hrms/hrms/public \
               /home/frappe/frappe-bench/assets/hrms \
    && /home/frappe/frappe-bench/env/bin/python /opt/merge-assets.py \
           /home/frappe/frappe-bench/assets \
           /tmp/hrms-assets.json /tmp/hrms-assets-rtl.json \
    && rm -f /tmp/hrms-assets.json /tmp/hrms-assets-rtl.json

# NOTE: deliberately NO `CMD` override here.
# The base image ships CMD ["start.sh"], which is what boots gunicorn for the
# backend service. This Dockerfile used to end with CMD ["/opt/init.sh"], which
# was harmless while only `init` used the image — but once every service builds
# from it, `backend` inherited that CMD and ran the init script instead of
# gunicorn. nginx then had no upstream and the whole site returned 502.
# `init` sets its own entrypoint in docker-compose.yml, so it does not need a
# default here.
