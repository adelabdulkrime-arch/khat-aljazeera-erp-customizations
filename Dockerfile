ARG ERPNEXT_VERSION=v16
FROM ghcr.io/frappe/erpnext:${ERPNEXT_VERSION}

USER root

# MariaDB client so init.sh can poll the DB before bench new-site
RUN apt-get update \
    && apt-get install -y --no-install-recommends default-mysql-client \
    && rm -rf /var/lib/apt/lists/*

# Workshop customisation scripts — copied into a staging area
COPY --chown=frappe:frappe workshop_*.py /opt/workshop-scripts/

# One-time init entrypoint
COPY --chown=frappe:frappe docker/init.sh /opt/init.sh
RUN chmod +x /opt/init.sh

USER frappe
WORKDIR /home/frappe/frappe-bench

CMD ["/opt/init.sh"]
