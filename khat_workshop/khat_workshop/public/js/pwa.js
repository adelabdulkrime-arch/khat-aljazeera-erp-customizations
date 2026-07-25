// Khat Al Jazeera — PWA client bootstrap.
//
// Loaded on BOTH contexts so the app is installable everywhere the user might be
// when they choose "install / add to home screen":
//   * desk pages (/app/*, /desk/home) via app_include_js
//   * website + login pages via web_include_js
//
// It has no Frappe dependency on purpose (pure DOM + navigator APIs), so the very
// same file works on the login page — which boots before frappe.app exists — and
// inside the desk. Everything here is idempotent: running twice changes nothing.
//
// Responsibilities:
//   1. Guarantee exactly one <link rel="manifest"> — OURS. Frappe ships its own
//      generic manifest on the desk; if we merely appended a second one the
//      browser would keep the first and the app would install as "Frappe" with
//      the Frappe icon. So we strip any foreign manifest first.
//   2. Add the iOS / theme meta tags Frappe does not emit.
//   3. Register the service worker (served at /sw.js, origin-wide scope).
//   4. Offer an in-app "install" button, because most users never find the
//      browser's own install menu — especially inside a desk that fills the tab.

(function () {
	"use strict";

	var MANIFEST = "/assets/khat_workshop/manifest.json";
	var THEME_COLOR = "#1a2b4a";
	var APP_TITLE = "خط الجزيرة";
	var APPLE_ICON = "/assets/khat_workshop/icons/apple-touch-icon.png";

	// How long a dismissal of the install button is respected before we offer it
	// again (ms). Long enough not to nag, short enough that a user who dismissed
	// by reflex still gets a second chance.
	var DISMISS_MS = 14 * 24 * 60 * 60 * 1000;
	var DISMISS_KEY = "kaj-install-dismissed-at";

	// ── manifest + meta tags ─────────────────────────────────────────────────
	function ensureManifest() {
		var links = document.querySelectorAll('link[rel="manifest"]');
		for (var i = 0; i < links.length; i++) {
			if (links[i].id !== "kaj-manifest") links[i].parentNode.removeChild(links[i]);
		}
		if (!document.getElementById("kaj-manifest")) {
			var l = document.createElement("link");
			l.id = "kaj-manifest";
			l.rel = "manifest";
			l.href = MANIFEST;
			document.head.appendChild(l);
		}
	}

	// Create the tag matched by `selector` if absent, then set every attribute in
	// `attrs` (except the pseudo-attr `tag`, which names the element to create).
	function ensureTag(selector, attrs) {
		var el = document.head.querySelector(selector);
		if (!el) {
			el = document.createElement(attrs.tag);
			document.head.appendChild(el);
		}
		for (var k in attrs) {
			if (k !== "tag" && attrs.hasOwnProperty(k)) el.setAttribute(k, attrs[k]);
		}
	}

	function ensureMetaTags() {
		ensureTag('meta[name="theme-color"]', { tag: "meta", name: "theme-color", content: THEME_COLOR });
		ensureTag('meta[name="mobile-web-app-capable"]', { tag: "meta", name: "mobile-web-app-capable", content: "yes" });
		ensureTag('meta[name="apple-mobile-web-app-capable"]', { tag: "meta", name: "apple-mobile-web-app-capable", content: "yes" });
		ensureTag('meta[name="apple-mobile-web-app-status-bar-style"]', { tag: "meta", name: "apple-mobile-web-app-status-bar-style", content: "black-translucent" });
		ensureTag('meta[name="apple-mobile-web-app-title"]', { tag: "meta", name: "apple-mobile-web-app-title", content: APP_TITLE });
		ensureTag('link[rel="apple-touch-icon"]', { tag: "link", rel: "apple-touch-icon", href: APPLE_ICON });
	}

	// ── service worker ───────────────────────────────────────────────────────
	function registerServiceWorker() {
		if (!("serviceWorker" in navigator)) return;
		// Service workers need a secure context. Browsers treat localhost as one,
		// so a local demo over http still registers; anything else needs HTTPS.
		var host = location.hostname;
		var secure = location.protocol === "https:" || host === "localhost" || host === "127.0.0.1";
		if (!secure) return;

		navigator.serviceWorker.register("/sw.js", { scope: "/" }).catch(function (err) {
			if (window.console && console.warn) console.warn("[kaj-pwa] service worker registration failed:", err);
		});
	}

	// ── in-app install button ────────────────────────────────────────────────
	// `beforeinstallprompt` fires only on Chromium (Android + desktop Chrome/Edge)
	// and only when the app is installable and not yet installed — which is
	// exactly when we want the button. We stash the event and drive the native
	// prompt from our own button. iOS Safari has no such event; those users
	// install via the Share sheet (documented in the README), so no button there.
	var deferredPrompt = null;

	function inStandalone() {
		return (window.matchMedia && window.matchMedia("(display-mode: standalone)").matches) ||
			window.navigator.standalone === true;
	}

	function isDismissed() {
		try {
			var at = parseInt(localStorage.getItem(DISMISS_KEY) || "0", 10);
			return at > 0 && (Date.now() - at) < DISMISS_MS;
		} catch (e) { return false; }
	}

	function setDismissed() {
		try { localStorage.setItem(DISMISS_KEY, String(Date.now())); } catch (e) {}
	}

	function injectStyleOnce() {
		if (document.getElementById("kaj-install-style")) return;
		var css =
			'#kaj-install-fab{position:fixed;bottom:18px;left:18px;z-index:1030;' +
			'display:none;align-items:center;gap:10px;direction:rtl;' +
			'background:#1a2b4a;color:#fff;border-radius:999px;padding:10px 14px 10px 16px;' +
			'box-shadow:0 6px 22px rgba(0,0,0,.28);font-family:"Tahoma","Segoe UI",sans-serif;' +
			'font-size:14px;font-weight:bold;cursor:pointer;user-select:none;' +
			'transition:transform .15s ease,background .15s ease;}' +
			'#kaj-install-fab:hover{background:#22345a;transform:translateY(-1px);}' +
			'#kaj-install-fab .kaj-install-ico{font-size:16px;line-height:1;}' +
			'#kaj-install-fab .kaj-install-x{margin-inline-start:2px;width:20px;height:20px;' +
			'display:inline-flex;align-items:center;justify-content:center;border-radius:50%;' +
			'background:rgba(255,255,255,.14);font-size:13px;font-weight:normal;}' +
			'#kaj-install-fab .kaj-install-x:hover{background:#e63946;}';
		var s = document.createElement("style");
		s.id = "kaj-install-style";
		s.textContent = css;
		document.head.appendChild(s);
	}

	function buildFab() {
		var fab = document.getElementById("kaj-install-fab");
		if (fab) return fab;
		injectStyleOnce();

		fab = document.createElement("div");
		fab.id = "kaj-install-fab";
		fab.setAttribute("role", "button");
		fab.setAttribute("aria-label", "تثبيت التطبيق");

		var ico = document.createElement("span");
		ico.className = "kaj-install-ico";
		ico.textContent = "⬇";

		var label = document.createElement("span");
		label.textContent = "ثبّت التطبيق";

		var close = document.createElement("span");
		close.className = "kaj-install-x";
		close.textContent = "✕";
		close.setAttribute("aria-label", "إخفاء");

		fab.appendChild(ico);
		fab.appendChild(label);
		fab.appendChild(close);
		document.body.appendChild(fab);

		fab.addEventListener("click", function (e) {
			if (e.target === close) { setDismissed(); hideFab(); e.stopPropagation(); return; }
			if (!deferredPrompt) { hideFab(); return; }
			deferredPrompt.prompt();
			deferredPrompt.userChoice.then(function () {
				deferredPrompt = null;
				hideFab();
			});
		});
		return fab;
	}

	function showFab() {
		if (inStandalone() || isDismissed() || !document.body) return;
		buildFab().style.display = "inline-flex";
	}

	function hideFab() {
		var fab = document.getElementById("kaj-install-fab");
		if (fab) fab.style.display = "none";
	}

	// Register these as early as the script runs — beforeinstallprompt can fire
	// before DOMContentLoaded.
	window.addEventListener("beforeinstallprompt", function (e) {
		e.preventDefault();
		deferredPrompt = e;
		showFab();
	});
	window.addEventListener("appinstalled", function () {
		deferredPrompt = null;
		hideFab();
	});

	// ── boot ─────────────────────────────────────────────────────────────────
	function boot() {
		try {
			ensureManifest();
			ensureMetaTags();
			registerServiceWorker();
			if (deferredPrompt) showFab();  // event may have fired before boot
		} catch (e) {
			if (window.console && console.warn) console.warn("[kaj-pwa] init failed:", e);
		}
	}

	if (document.readyState === "loading") {
		document.addEventListener("DOMContentLoaded", boot);
	} else {
		boot();
	}
})();
