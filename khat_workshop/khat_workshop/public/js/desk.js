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

// ── اسم النظام في رأس الشريط الجانبي ────────────────────────────────────────
//
// الشريط كان يعرض اسم تطبيق آخر فوق نظام يُباع باسم «خط الجزيرة»:
// "ERPNext" في الرئيسية و"Frappe Framework" داخل لوحة الورشة.
//
// السبب خلل في choose_app_name() بملف
// frappe/public/js/frappe/ui/sidebar/sidebar.js: الحلقة تمرّ على التطبيقات،
// وتضبط header_subtitle داخل فرع else — أي لكل تطبيق *لا* يطابق. فآخر تطبيق
// غير مطابق يدهس النتيجة الصحيحة حتى حين تكون اللوحة مملوكة لنا وحدنا
// (تحققت: khat_workshop هو التطبيق الوحيد الذي يتضمن لوحة Home).
//
// الدالة نفسها تخرج فوراً إذا كان app_name_style == "Default"، فتترك العنوان
// كما هو. فنضبط هذه القيمة قبل بناء الشريط، ونضع العنوان الصحيح مرة واحدة.
// إصلاح بقيمة إعداد يدعمها الإطار، لا بتعديل DOM يتكسّر مع أي تحديث.
(function () {
	'use strict';

	var NAME = 'خط الجزيرة';

	function apply() {
		if (!window.frappe || !frappe.boot) return false;
		frappe.boot.app_name_style = 'Default';
		return true;
	}

	if (!apply()) {
		var n = 0;
		var t = setInterval(function () {
			if (apply() || ++n > 40) clearInterval(t);
		}, 250);
	}

	// العنوان يُعاد بناؤه عند كل تنقّل بين اللوحات، فنصححه بعد كل بناء بدل
	// مرة واحدة عند التحميل.
	function fixSubtitle() {
		document.querySelectorAll('.header-subtitle').forEach(function (el) {
			if (el.textContent.trim() !== NAME) el.textContent = NAME;
		});
	}

	function watch() {
		if (!document.body) return;
		fixSubtitle();
		var pending = false;
		new MutationObserver(function () {
			if (pending) return;
			pending = true;
			requestAnimationFrame(function () {
				pending = false;
				fixSubtitle();
			});
		}).observe(document.body, { childList: true, subtree: true });
	}

	if (document.readyState === 'loading') {
		document.addEventListener('DOMContentLoaded', watch);
	} else {
		watch();
	}
})();

// ── زر الإجراء السريع ───────────────────────────────────────────────────────
//
// أكثر ما يتكرر في الورشة: فتح بطاقة عمل، تسجيل عميل جديد، إصدار فاتورة.
// كلٌّ منها يحتاج 3-4 نقرات عبر القوائم. زر عائم واحد يختصرها إلى نقرتين من
// أي شاشة.
//
// زر عائم لا بند في قائمة: البند يُرى فقط حين تُفتح قائمته، أما العائم فمرئي
// دائماً — وهذا الغرض منه.
(function () {
	'use strict';

	var ACTIONS = [
		{ label: 'بطاقة عمل جديدة', route: '/app/work-card/new', icon: 'edit' },
		{ label: 'عميل جديد', route: '/app/customer/new', icon: 'users' },
		{ label: 'مركبة جديدة', route: '/app/customer-vehicle/new', icon: 'car' },
		{ label: 'فاتورة جديدة', route: '/app/sales-invoice/new', icon: 'money-coins-1' },
		{ label: 'عرض سعر جديد', route: '/app/quotation/new', icon: 'file' },
	];

	function build() {
		if (document.getElementById('kaj-fab')) return;
		if (!document.body) return;
		// لا نعرضه على صفحات الدخول أو الإعداد — لا معنى لإجراء سريع قبل الدخول.
		if (!/^\/(app|desk)\b/.test(window.location.pathname)) return;

		var wrap = document.createElement('div');
		wrap.id = 'kaj-fab-wrap';

		var menu = document.createElement('div');
		menu.id = 'kaj-fab-menu';
		menu.setAttribute('role', 'menu');
		menu.hidden = true;

		ACTIONS.forEach(function (a) {
			var item = document.createElement('button');
			item.type = 'button';
			item.className = 'kaj-fab-item';
			item.setAttribute('role', 'menuitem');
			item.textContent = a.label;
			item.addEventListener('click', function () {
				close();
				// router بدل تغيير العنوان: التنقّل داخل التطبيق لا يُعيد تحميل
				// الصفحة كاملة، فهو أسرع ويحفظ حالة الواجهة.
				if (window.frappe && frappe.set_route) {
					frappe.set_route(a.route.replace(/^\/app\//, '').split('/'));
				} else {
					window.location.href = a.route;
				}
			});
			menu.appendChild(item);
		});

		var fab = document.createElement('button');
		fab.id = 'kaj-fab';
		fab.type = 'button';
		fab.title = 'إجراء سريع';
		fab.setAttribute('aria-label', 'إجراء سريع');
		fab.setAttribute('aria-expanded', 'false');
		fab.innerHTML =
			'<svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" ' +
			'stroke-width="2.4" stroke-linecap="round"><path d="M12 5v14M5 12h14"/></svg>';

		function open() {
			menu.hidden = false;
			fab.setAttribute('aria-expanded', 'true');
			fab.classList.add('is-open');
		}
		function close() {
			menu.hidden = true;
			fab.setAttribute('aria-expanded', 'false');
			fab.classList.remove('is-open');
		}
		fab.addEventListener('click', function (e) {
			e.stopPropagation();
			menu.hidden ? open() : close();
		});
		// النقر خارج القائمة أو Esc يغلقها — سلوك متوقع من أي قائمة منبثقة.
		document.addEventListener('click', function (e) {
			if (!wrap.contains(e.target)) close();
		});
		document.addEventListener('keydown', function (e) {
			if (e.key === 'Escape') close();
		});

		wrap.appendChild(menu);
		wrap.appendChild(fab);

		var css = document.createElement('style');
		css.id = 'kaj-fab-style';
		css.textContent = [
			'#kaj-fab-wrap{position:fixed;inset-inline-end:22px;bottom:22px;z-index:1030;',
			'display:flex;flex-direction:column;align-items:flex-end;gap:10px;}',
			'#kaj-fab{width:52px;height:52px;border-radius:50%;border:0;cursor:pointer;',
			'background:#e63946;color:#fff;display:flex;align-items:center;justify-content:center;',
			'box-shadow:0 6px 18px rgba(230,57,70,.38);transition:transform .2s,box-shadow .2s;}',
			'#kaj-fab:hover{transform:translateY(-2px);box-shadow:0 10px 24px rgba(230,57,70,.46);}',
			'#kaj-fab.is-open{transform:rotate(45deg);}',
			'#kaj-fab:focus-visible{outline:2px solid #f0b429;outline-offset:3px;}',
			'#kaj-fab-menu{display:flex;flex-direction:column;gap:6px;background:var(--card-bg,#fff);',
			'border:1px solid var(--border-color,#e3e6ec);border-radius:12px;padding:6px;',
			'box-shadow:0 12px 30px rgba(16,30,54,.16);min-width:188px;}',
			'.kaj-fab-item{background:none;border:0;text-align:start;cursor:pointer;',
			'padding:9px 12px;border-radius:8px;font-size:13.5px;font-weight:600;',
			'color:var(--text-color,#1a2b4a);font-family:inherit;transition:background .13s;}',
			'.kaj-fab-item:hover{background:rgba(230,57,70,.09);color:#e63946;}',
			'.kaj-fab-item:focus-visible{outline:2px solid #f0b429;outline-offset:-2px;}',
			// على الجوال يتزاحم مع أزرار النظام السفلية، فنرفعه قليلاً.
			'@media (max-width:768px){#kaj-fab-wrap{bottom:72px;inset-inline-end:16px;}}',
		].join('');

		document.head.appendChild(css);
		document.body.appendChild(wrap);
	}

	function start() {
		build();
		// الواجهة تُعيد بناء أجزاء منها عند التنقّل، فنتأكد أن الزر باقٍ.
		var pending = false;
		new MutationObserver(function () {
			if (pending) return;
			pending = true;
			requestAnimationFrame(function () {
				pending = false;
				build();
			});
		}).observe(document.body, { childList: true, subtree: true });
	}

	if (document.readyState === 'loading') {
		document.addEventListener('DOMContentLoaded', start);
	} else {
		start();
	}
})();
