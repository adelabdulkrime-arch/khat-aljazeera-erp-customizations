# -*- coding: utf-8 -*-
"""Serve the PWA service worker at the site root (/sw.js).

Why a custom page_renderer instead of a plain static file:

  * A service worker can only control pages **at or below the path it is served
    from**. To control the whole app — /app/*, /desk/home, /login — the worker
    must be served from the origin root, i.e. /sw.js.
  * Frappe's static-file renderer (the one that serves an app's www/ folder)
    BLACKLISTS .js, .css, .json, .txt … (see
    frappe/website/page_renderers/static_page.py). So www/sw.js would 404.
  * Files under /assets/khat_workshop/ ARE served (that is how desk.js loads),
    but their scope is /assets/khat_workshop/ — too narrow to control /app.

A page_renderer is checked BEFORE every built-in renderer (see
frappe/website/path_resolver.py), so this claims /sw.js and returns the worker
source with `Service-Worker-Allowed: /`, which lets a script physically at the
root register with an origin-wide scope.

The worker source lives here as a string rather than a .js file on disk so it
travels with the code that serves it — the same reason the dashboard builders
bake their JS into Python.
"""

from frappe.website.page_renderers.base_renderer import BaseRenderer

# ── Service worker source ────────────────────────────────────────────────────
# Deliberately minimal. This is a live ERP: the worker must NEVER serve stale
# data. So it caches exactly one thing — the offline fallback page — and only
# intercepts top-level navigations. Every asset, REST call and POST goes straight
# to the network, untouched. Bump CACHE (…-vN) whenever the offline page changes
# so the activate handler drops the old cache.
SERVICE_WORKER_JS = """// Khat Al Jazeera — PWA service worker. Served at /sw.js by
// khat_workshop.pwa.ServiceWorkerRenderer so its scope is the whole origin.
const CACHE = 'kaj-pwa-v1';
const OFFLINE_URL = '/assets/khat_workshop/offline.html';

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE)
      .then((cache) => cache.add(new Request(OFFLINE_URL, { cache: 'reload' })))
      .then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys()
      .then((keys) => Promise.all(keys.map((k) => (k === CACHE ? null : caches.delete(k)))))
      .then(() => self.clients.claim())
  );
});

// Network-first for page navigations only. If the network is unreachable, show
// the branded offline page. Everything else is left to the browser so the ERP
// never serves stale forms, stale reports, or breaks a write request.
self.addEventListener('fetch', (event) => {
  const req = event.request;
  if (req.mode !== 'navigate') return;
  event.respondWith(fetch(req).catch(() => caches.match(OFFLINE_URL)));
});
"""


class ServiceWorkerRenderer(BaseRenderer):
    """Return the service worker for GET /sw.js, at origin-wide scope."""

    def can_render(self):
        # self.path is already stripped of leading/trailing slashes.
        return self.path == "sw.js"

    def render(self):
        # build_response infers text/javascript from the ".js" in self.path.
        # Service-Worker-Allowed lets the root-served worker claim scope "/";
        # no-cache keeps the browser checking for a newer worker on each visit.
        return self.build_response(
            SERVICE_WORKER_JS,
            headers={
                "Service-Worker-Allowed": "/",
                "Cache-Control": "no-cache",
                "Content-Type": "text/javascript; charset=utf-8",
            },
        )
