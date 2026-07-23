// Khat Al Jazeera — desk-level layer, loaded on every desk page via
// app_include_js.
//
// History: this file once injected a language switcher and logout item into the
// v15 navbar by looking for `.page-icon-group`. v16 replaced the top navbar with
// a sidebar, that element vanished, and the script silently did nothing. The
// language switch now lives in Navbar Settings (workshop_navbar) — a DocType
// record, not a CSS selector, so it cannot go stale.
//
// What remains here is one override: logout.
//
// v16's sidebar logout calls redirect_to_login(), which sends the browser to
//   /login?redirect-to=<current page>
// so after signing back in the user lands on whatever page they logged out from
// — not the dashboard. We replace frappe.app.logout so it returns to a clean
// /login with no redirect-to; login then follows default_app
// (khat_workshop -> /desk/home) straight to the dashboard.
//
// This swaps a method by name, not a DOM node. If a future version renames it,
// the sidebar keeps its native behaviour — this degrades, it does not break.
// Session-expiry still uses redirect_to_login() untouched, because returning to
// where you were after a timeout is the right behaviour there.

frappe.provide("frappe");

(function () {
	function patch() {
		if (window.frappe && frappe.app && typeof frappe.app.logout === "function") {
			if (frappe.app.__kaj_clean_logout) return true;
			frappe.app.__kaj_clean_logout = true;
			frappe.app.logout = function () {
				frappe.confirm(__("Are you sure you want to log out?"), function () {
					frappe.call({
						method: "logout",
						callback: function (r) {
							if (!r.exc) window.location.href = "/login";
						},
					});
				});
			};
			return true;
		}
		return false;
	}

	// frappe.app is created during desk boot and may not exist yet. Patch now if
	// it does, otherwise poll briefly until it appears, then stop.
	if (!patch()) {
		var tries = 0;
		var timer = setInterval(function () {
			if (patch() || ++tries > 40) clearInterval(timer);
		}, 500);
	}
})();
