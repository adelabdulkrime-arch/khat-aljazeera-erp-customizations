// Khat Al Jazeera — desk-level layer.
//
// This file used to inject a language switcher, a logout item, and a rule
// hiding `.sidebar-header` into the navbar. All three hooked into the v15 desk:
// the script looked for `.page-icon-group`, and v16 replaced the top navbar
// with a sidebar, so that element does not exist and the script returned on its
// second line. It did nothing at all while looking installed — the failure mode
// this project keeps paying for.
//
// The language switch now lives in Navbar Settings (see
// khat_workshop.setup.workshop_navbar): a DocType record rather than a CSS
// selector, so it cannot go stale the next time the interface changes. Logout
// and the sidebar header are v16's own and need no help from us.
//
// Kept as a loaded but empty file on purpose: app_include_js points here, and
// this is where any future desk-wide script belongs. Removing it would mean a
// 404 on every desk page for no gain.
