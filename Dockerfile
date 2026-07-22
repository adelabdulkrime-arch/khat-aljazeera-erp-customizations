ARG ERPNEXT_VERSION=v16
FROM frappe/erpnext:${ERPNEXT_VERSION}

USER root

# MariaDB client so init.sh can poll the DB before bench new-site
RUN apt-get update \
    && apt-get install -y --no-install-recommends default-mysql-client \
    && rm -rf /var/lib/apt/lists/*

# Workshop customisation scripts — copied into a staging area
COPY --chown=frappe:frappe workshop_*.py /opt/workshop-scripts/

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

CMD ["/opt/init.sh"]
