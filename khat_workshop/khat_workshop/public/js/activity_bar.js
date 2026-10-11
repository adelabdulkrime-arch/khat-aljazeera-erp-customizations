// شريط جانبي على نمط VS Code: شريط نشاط ضيق + لوح فرعي.
//
// الشريط في v16 قائمة واحدة عريضة: سبع لوحات باسمها الكامل، والوصول لأي
// شاشة يمرّ بفتح لوحتها ثم البحث عنها في جسم الصفحة. والأسماء تلتهم عرضاً
// دائماً وإن لم يقرأها أحد بعد أول يوم.
//
// البنية الجديدة كما في VS Code:
//   ┌────┬──────────────────┐
//   │ 🏠 │  الورشة          │   شريط نشاط (أيقونات فقط، ~50px)
//   │ 🔧 │  ───────────     │   + لوح فرعي يعرض محتويات اللوحة المختارة
//   │ 🛒 │  بطاقات العمل    │
//   │ 📦 │  الفنيون         │
//   └────┴──────────────────┘
//
// كلّه أمامي: يقرأ روابط مساحات العمل عبر frappe.client.get_list (فتُطبَّق
// صلاحيات المستخدم على الخادم، ولا نبني قائمة محلياً قد تكشف ما لا يملكه)،
// ويبني طبقة فوق الشريط الأصلي دون حذف عناصره — فروابطه تبقى سليمة، وإن
// تغيّر الإطار في إصدار قادم عاد الشريط لسلوكه الأصلي بلا كسر.

(function () {
	'use strict';

	// لوحات الورشة السبع بترتيب بطاقات الصفحة الرئيسية نفسه.
	var PANELS = [
		{ ws: 'Home',                  label: 'الرئيسية',        icon: 'home' },
		{ ws: 'Workshop',              label: 'الورشة',          icon: 'tool' },
		{ ws: 'Sales Dashboard',       label: 'لوحة المبيعات',   icon: 'shopping-cart' },
		{ ws: 'Purchasing Dashboard',  label: 'لوحة المشتريات',  icon: 'package-plus' },
		{ ws: 'Inventory Dashboard',   label: 'لوحة المخزون',    icon: 'layout-grid' },
		{ ws: 'Accounting Dashboard',  label: 'لوحة المحاسبة',   icon: 'receipt' },
		{ ws: 'General Settings',      label: 'الإعدادات العامة', icon: 'settings' },
	];

	// الرئيسية لوحة تحكّم لا مجموعة شاشات، فلا لوح فرعي لها — النقر عليها
	// يفتحها مباشرة كما يفعل زر الصفحة الرئيسية في أي نظام.
	var NO_PANEL = ['Home'];

	var ACTIVE_KEY = 'kaj_active_panel';
	var MOBILE_Q = '(max-width: 991px)';
	var TIP_DELAY = 300;              // نفس تأخير VS Code

	var linksCache = null;
	var fetching = null;
	var els = {};

	// ── تخزين الاختيار ──
	// localStorage يرمي في وضع التصفّح الخاص، فكل وصول محمي ويعود لقيمة
	// افتراضية بدل أن يُسقط الشريط كلّه.
	function readActive() {
		try { return localStorage.getItem(ACTIVE_KEY) || ''; } catch (e) { return ''; }
	}
	function writeActive(ws) {
		try { localStorage.setItem(ACTIVE_KEY, ws || ''); } catch (e) {}
	}

	function t(s) {
		try { return window.__ ? window.__(s) : s; } catch (e) { return s; }
	}

	function isMobile() {
		try { return window.matchMedia(MOBILE_Q).matches; } catch (e) { return false; }
	}

	function slug(ws) {
		return ws.toLowerCase().replace(/\s+/g, '-');
	}

	// مسار العنصر حسب نوعه. Report وPage لهما مسارات مختلفة عن DocType.
	function routeFor(row) {
		var to = row.link_to || '';
		if (!to) return null;
		if (row.link_type === 'Report') return '/app/query-report/' + encodeURIComponent(to);
		if (row.link_type === 'Page') return '/app/' + encodeURIComponent(to);
		return '/app/' + encodeURIComponent(slug(to));
	}

	// ── جلب الروابط ──
	// نداء واحد لكل اللوحات بدل نداء لكل لوحة: ستة نداءات عند كل تحميل
	// صفحة حِمل بلا مقابل على خادم ورشة صغيرة.
	function fetchLinks() {
		if (linksCache) return Promise.resolve(linksCache);
		if (fetching) return fetching;
		if (!window.frappe || !frappe.call) return Promise.resolve({});

		var names = PANELS.map(function (p) { return p.ws; })
			.filter(function (w) { return NO_PANEL.indexOf(w) === -1; });

		fetching = frappe.call({
			method: 'frappe.client.get_list',
			args: {
				doctype: 'Workspace Link',
				filters: { parent: ['in', names], type: 'Link' },
				fields: ['parent', 'label', 'link_to', 'link_type', 'idx'],
				parent: 'Workspace',
				limit_page_length: 0,
				order_by: 'idx asc',
			},
		}).then(function (r) {
			var rows = (r && r.message) || [];
			linksCache = {};
			rows.forEach(function (row) {
				if (!row.link_to) return;
				(linksCache[row.parent] = linksCache[row.parent] || []).push(row);
			});
			fetching = null;
			return linksCache;
		}).catch(function (e) {
			// فشل الجلب لا يكسر التنقّل: شريط النشاط يبقى وروابط اللوحات تعمل.
			console.warn('[kaj] activity bar: links unavailable', e);
			linksCache = {};
			fetching = null;
			return linksCache;
		});
		return fetching;
	}

	function svgUse(icon) {
		return '<svg class="kaj-ab-ico" aria-hidden="true"><use href="#icon-' + icon + '"></use></svg>';
	}

	// ── شريط النشاط ──
	function buildBar() {
		if (document.getElementById('kaj-activitybar')) return;
		if (!document.body) return;

		var bar = document.createElement('nav');
		bar.id = 'kaj-activitybar';
		bar.setAttribute('role', 'navigation');
		bar.setAttribute('aria-label', t('الوحدات الرئيسية'));

		PANELS.forEach(function (p) {
			var b = document.createElement('button');
			b.type = 'button';
			b.className = 'kaj-ab-btn';
			b.dataset.ws = p.ws;
			// الاسم لا يُعرض نصاً داخل الشريط إطلاقاً — تلميح فقط. ومع ذلك
			// aria-label يحمله دائماً فيقرأه قارئ الشاشة.
			b.setAttribute('aria-label', t(p.label));
			b.innerHTML = svgUse(p.icon);
			bar.appendChild(b);
		});

		document.body.appendChild(bar);
		els.bar = bar;

		bar.addEventListener('click', function (ev) {
			var btn = ev.target.closest('.kaj-ab-btn');
			if (!btn) return;
			ev.preventDefault();
			select(btn.dataset.ws, true);
		});

		bindTooltips(bar);
	}

	// ── التلميحات ──
	// تلميح واحد يُعاد استخدامه لكل الأزرار بدل عنصر لكل زر، ويظهر بعد
	// 300ms كما في VS Code: الظهور الفوري يومض مع كل مرور عابر للمؤشر.
	function bindTooltips(bar) {
		var tip = document.createElement('div');
		tip.id = 'kaj-ab-tip';
		tip.setAttribute('role', 'tooltip');
		document.body.appendChild(tip);
		els.tip = tip;

		var timer = null;

		function show(btn) {
			tip.textContent = btn.getAttribute('aria-label') || '';
			var r = btn.getBoundingClientRect();
			tip.style.top = Math.round(r.top + r.height / 2) + 'px';
			// الشريط على جانب البداية، فالتلميح يخرج ناحية النهاية — يعمل
			// في الاتجاهين بلا فرع لكل اتجاه.
			tip.style.insetInlineStart = Math.round(r.width + 10) + 'px';
			tip.classList.add('is-on');
		}
		function hide() {
			clearTimeout(timer);
			tip.classList.remove('is-on');
		}

		bar.addEventListener('mouseover', function (ev) {
			var btn = ev.target.closest('.kaj-ab-btn');
			if (!btn) return;
			clearTimeout(timer);
			timer = setTimeout(function () { show(btn); }, TIP_DELAY);
		});
		bar.addEventListener('mouseout', hide);
		// لوحة المفاتيح: التلميح يظهر فوراً عند التركيز، بلا تأخير — التأخير
		// يخدم المرور العابر للفأرة ولا معنى له هنا.
		bar.addEventListener('focusin', function (ev) {
			var btn = ev.target.closest('.kaj-ab-btn');
			if (btn) show(btn);
		});
		bar.addEventListener('focusout', hide);
		window.addEventListener('scroll', hide, true);
	}

	// ── اللوح الفرعي ──
	function buildPanel() {
		if (document.getElementById('kaj-sidepanel')) return;

		var p = document.createElement('aside');
		p.id = 'kaj-sidepanel';
		p.innerHTML =
			'<div class="kaj-sp-head">' +
			'  <span class="kaj-sp-title"></span>' +
			'  <button type="button" class="kaj-sp-close" aria-label="' + t('إغلاق') + '">' +
			'    <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" ' +
			'stroke-width="2.2" stroke-linecap="round"><path d="M18 6L6 18M6 6l12 12"/></svg>' +
			'  </button>' +
			'</div>' +
			'<div class="kaj-sp-body"></div>';
		document.body.appendChild(p);
		els.panel = p;
		els.title = p.querySelector('.kaj-sp-title');
		els.body = p.querySelector('.kaj-sp-body');

		p.querySelector('.kaj-sp-close').addEventListener('click', function () {
			closePanel();
		});

		// ستارة للجوال: اللوح يغطّي المحتوى هناك، فيحتاج مخرجاً بالنقر خارجه.
		var sc = document.createElement('div');
		sc.id = 'kaj-sp-scrim';
		sc.addEventListener('click', closePanel);
		document.body.appendChild(sc);
		els.scrim = sc;
	}

	function closePanel() {
		document.body.classList.remove('kaj-panel-open');
		if (els.scrim) els.scrim.classList.remove('is-on');
		// على الجوال الإغلاق مؤقّت ولا يمسح الاختيار المحفوظ: المستخدم أغلق
		// الدرج ليرى المحتوى، لا ليغيّر اللوحة.
		if (!isMobile()) writeActive('');
		if (els.bar) {
			els.bar.querySelectorAll('.kaj-ab-btn').forEach(function (b) {
				b.classList.remove('is-active');
				b.removeAttribute('aria-current');
			});
		}
	}

	// ── الاختيار ──
	// navigate=true حين ينقر المستخدم: نفتح اللوحة أيضاً. وfalse عند
	// الاستعادة من localStorage: نُظهر اللوح دون نقل المستخدم عن صفحته.
	function select(ws, navigate) {
		var panel = PANELS.filter(function (p) { return p.ws === ws; })[0];
		if (!panel) return;

		if (els.bar) {
			els.bar.querySelectorAll('.kaj-ab-btn').forEach(function (b) {
				var on = b.dataset.ws === ws;
				b.classList.toggle('is-active', on);
				if (on) b.setAttribute('aria-current', 'page');
				else b.removeAttribute('aria-current');
			});
		}

		if (NO_PANEL.indexOf(ws) !== -1) {
			closePanel();
			writeActive('');
			if (navigate) go('/app/' + slug(ws));
			return;
		}

		writeActive(ws);
		openPanel(panel, navigate);
	}

	function openPanel(panel, navigate) {
		buildPanel();
		els.title.textContent = t(panel.label);
		els.body.innerHTML = '<div class="kaj-sp-loading">' + t('جارٍ التحميل') + '…</div>';
		document.body.classList.add('kaj-panel-open');
		if (isMobile() && els.scrim) els.scrim.classList.add('is-on');

		fetchLinks().then(function (map) {
			var rows = (map && map[panel.ws]) || [];
			els.body.innerHTML = '';

			// رابط اللوحة نفسها أولاً: اللوح يعرض محتوياتها، ومن يريد
			// صفحتها الكاملة يحتاج مدخلاً صريحاً إليها.
			var head = document.createElement('a');
			head.className = 'kaj-sp-link is-board';
			head.href = '/app/' + slug(panel.ws);
			head.textContent = t(panel.label);
			els.body.appendChild(head);

			if (!rows.length) {
				var em = document.createElement('div');
				em.className = 'kaj-sp-empty';
				em.textContent = t('لا توجد عناصر');
				els.body.appendChild(em);
			} else {
				rows.forEach(function (row) {
					var href = routeFor(row);
					if (!href) return;
					var a = document.createElement('a');
					a.className = 'kaj-sp-link';
					a.href = href;
					a.textContent = t(row.label || row.link_to);
					a.title = a.textContent;
					els.body.appendChild(a);
				});
			}
			markCurrent();
		});

		if (navigate) go('/app/' + slug(panel.ws));
	}

	// تنقّل داخل التطبيق أحادي الصفحة إن أمكن: إعادة تحميل كاملة تمسح
	// الحالة وتُبطئ ما يُفترض أنه فوري.
	function go(path) {
		try {
			if (window.frappe && frappe.set_route) {
				frappe.set_route(path.replace(/^\/app\/?/, '') || 'home');
				return;
			}
		} catch (e) {}
		window.location.href = path;
	}

	// تمييز العنصر المطابق للصفحة المفتوحة.
	function markCurrent() {
		if (!els.body) return;
		var here = window.location.pathname.replace(/\/+$/, '');
		els.body.querySelectorAll('.kaj-sp-link').forEach(function (a) {
			var p = a.getAttribute('href').replace(/\/+$/, '');
			a.classList.toggle('is-current', p === here);
		});
	}

	// ── بطاقات الصفحة الرئيسية ──
	// النقر على بطاقة لوحة يفتح لوحها الفرعي أيضاً، فيتطابق الموضعان كما
	// طُلب. مفوَّض على المستند: البطاقات داخل كتلة HTML تُبنى بعد التحميل.
	function bindHomeCards() {
		if (document.body.dataset.kajCardsBound) return;
		document.body.dataset.kajCardsBound = '1';
		document.addEventListener('click', function (ev) {
			var card = ev.target.closest('.hm-card[data-route]');
			if (!card) return;
			var route = (card.dataset.route || '').split(',')[0].trim();
			var match = PANELS.filter(function (p) {
				return slug(p.ws) === route.toLowerCase();
			})[0];
			// لا نمنع السلوك الأصلي: البطاقة تُبحر كما كانت، ونحن نزامن
			// اللوح معها فقط.
			if (match) select(match.ws, false);
		}, true);
	}

	function styles() {
		if (document.getElementById('kaj-ab-css')) return;
		var W = 52;      // عرض شريط النشاط
		var P = 232;     // عرض اللوح الفرعي
		var css = document.createElement('style');
		css.id = 'kaj-ab-css';
		css.textContent = [
			':root{--kaj-ab-w:' + W + 'px;--kaj-sp-w:' + P + 'px;}',

			// ── شريط النشاط ──
			'#kaj-activitybar{position:fixed;inset-block:0;inset-inline-start:0;',
			'width:var(--kaj-ab-w);z-index:1030;display:flex;flex-direction:column;',
			'align-items:center;gap:4px;padding:10px 0;',
			'background:#16233d;border-inline-end:1px solid rgba(255,255,255,.07);}',
			'.kaj-ab-btn{position:relative;width:40px;height:40px;flex:0 0 auto;',
			'display:flex;align-items:center;justify-content:center;',
			'background:none;border:0;border-radius:10px;cursor:pointer;padding:0;',
			'color:rgba(255,255,255,.62);transition:color .15s,background .15s;}',
			'.kaj-ab-btn:hover{color:#fff;background:rgba(255,255,255,.09);}',
			'.kaj-ab-btn:focus-visible{outline:2px solid #f0b429;outline-offset:2px;}',
			'.kaj-ab-ico{width:21px;height:21px;}',
			'.kaj-ab-ico use{stroke:currentColor;}',
			// المؤشّر النشط: شريط رفيع على حافة البداية — يساراً في LTR
			// ويميناً في RTL، وinset-inline يتكفّل بالاتجاهين بلا فرعين.
			'.kaj-ab-btn.is-active{color:#fff;background:rgba(255,255,255,.12);}',
			'.kaj-ab-btn.is-active::before{content:"";position:absolute;',
			'inset-inline-start:-10px;top:50%;transform:translateY(-50%);',
			'width:3px;height:24px;border-radius:0 3px 3px 0;background:#fff;}',
			'[dir="rtl"] .kaj-ab-btn.is-active::before{border-radius:3px 0 0 3px;}',

			// ── التلميح ──
			'#kaj-ab-tip{position:fixed;z-index:1040;pointer-events:none;',
			'transform:translateY(-50%);opacity:0;visibility:hidden;',
			'background:#0f1a2e;color:#fff;font-size:12.5px;line-height:1;',
			'padding:7px 11px;border-radius:7px;white-space:nowrap;',
			'border:1px solid rgba(255,255,255,.12);',
			'box-shadow:0 6px 18px rgba(0,0,0,.35);',
			'transition:opacity .12s;}',
			'#kaj-ab-tip.is-on{opacity:1;visibility:visible;}',

			// ── اللوح الفرعي ──
			'#kaj-sidepanel{position:fixed;inset-block:0;',
			'inset-inline-start:var(--kaj-ab-w);width:var(--kaj-sp-w);z-index:1029;',
			'display:flex;flex-direction:column;',
			'background:var(--card-bg,#fff);',
			'border-inline-end:1px solid var(--border-color,#e5e8ee);',
			// مخفي افتراضياً، ينزلق للداخل عند الفتح.
			'transform:translateX(-100%);visibility:hidden;',
			'transition:transform .22s cubic-bezier(.2,.8,.2,1),visibility .22s;}',
			'[dir="rtl"] #kaj-sidepanel{transform:translateX(100%);}',
			'body.kaj-panel-open #kaj-sidepanel{transform:none;visibility:visible;}',
			'.kaj-sp-head{display:flex;align-items:center;gap:8px;',
			'padding:14px 14px 10px;border-bottom:1px solid var(--border-color,#eef0f4);}',
			'.kaj-sp-title{font-size:12px;font-weight:700;letter-spacing:.4px;',
			'text-transform:uppercase;color:var(--text-muted,#8a94a6);',
			'overflow:hidden;text-overflow:ellipsis;white-space:nowrap;}',
			'.kaj-sp-close{margin-inline-start:auto;background:none;border:0;',
			'padding:4px;border-radius:6px;cursor:pointer;display:flex;',
			'color:var(--text-muted,#8a94a6);}',
			'.kaj-sp-close:hover{background:var(--bg-light-gray,#f2f4f8);}',
			'.kaj-sp-body{flex:1;overflow-y:auto;padding:8px;',
			'display:flex;flex-direction:column;gap:1px;}',
			'.kaj-sp-link{display:block;padding:7px 10px;border-radius:7px;',
			'font-size:13px;line-height:1.5;color:var(--text-color,#44546b);',
			'text-decoration:none;white-space:nowrap;overflow:hidden;',
			'text-overflow:ellipsis;transition:background .14s,color .14s;}',
			'.kaj-sp-link:hover{background:var(--bg-light-gray,#f2f4f8);',
			'color:var(--text-color,#1a2b4a);text-decoration:none;}',
			'.kaj-sp-link.is-board{font-weight:700;color:var(--text-color,#1a2b4a);',
			'margin-bottom:4px;}',
			'.kaj-sp-link.is-current{background:rgba(230,57,70,.10);color:#e63946;',
			'font-weight:600;}',
			'.kaj-sp-link:focus-visible{outline:2px solid #e63946;outline-offset:-2px;}',
			'.kaj-sp-loading,.kaj-sp-empty{padding:10px;font-size:12.5px;',
			'color:var(--text-muted,#8a94a6);}',

			// ── إزاحة محتوى الصفحة ──
			// الشريطان ثابتان، فلولا الإزاحة لاختفى المحتوى تحتهما. الهامش
			// منطقي فيعمل في الاتجاهين، وينتقل بنفس سرعة انزلاق اللوح.
			'body{transition:padding-inline-start .22s cubic-bezier(.2,.8,.2,1);}',
			'body[data-path]{padding-inline-start:var(--kaj-ab-w);}',
			'body.kaj-panel-open[data-path]{',
			'padding-inline-start:calc(var(--kaj-ab-w) + var(--kaj-sp-w));}',
			// الشريط الأصلي يبقى في DOM (فروابطه ومعالجاته سليمة) لكنه
			// مخفيّ بصرياً: شريطان جنباً إلى جنب يزاحمان المحتوى.
			'.layout-side-section,.body-sidebar-container{display:none !important;}',

			// ── الستارة ──
			'#kaj-sp-scrim{position:fixed;inset:0;z-index:1028;background:rgba(10,18,32,.45);',
			'opacity:0;visibility:hidden;transition:opacity .2s,visibility .2s;}',
			'#kaj-sp-scrim.is-on{opacity:1;visibility:visible;}',

			// ── الجوال واللوحي ──
			// شريط النشاط يبقى ظاهراً، واللوح يصير درجاً فوق المحتوى بدل
			// أن يزيحه — الإزاحة على شاشة 360px لا تترك شيئاً للمحتوى.
			'@media ' + MOBILE_Q + '{',
			'  #kaj-sidepanel{width:min(78vw,280px);box-shadow:0 0 40px rgba(0,0,0,.28);z-index:1031;}',
			'  body.kaj-panel-open[data-path]{padding-inline-start:var(--kaj-ab-w);}',
			'}',
			// الطباعة: الشريطان ليسا جزءاً من المستند.
			'@media print{#kaj-activitybar,#kaj-sidepanel,#kaj-sp-scrim{display:none !important;}',
			'body[data-path]{padding-inline-start:0 !important;}}',
			'@media (prefers-reduced-motion:reduce){',
			'  #kaj-sidepanel,body{transition:none !important;}}',
		].join('');
		document.head.appendChild(css);
	}

	function restore() {
		var ws = readActive();
		if (!ws) return;
		if (!PANELS.some(function (p) { return p.ws === ws; })) return;
		// على الجوال لا نفتح الدرج تلقائياً: يغطّي الشاشة فور الدخول.
		select(ws, false);
		if (isMobile()) closePanel();
	}

	function start() {
		if (!document.body) return;
		styles();
		buildBar();
		buildPanel();
		bindHomeCards();
		restore();

		// الديسك تطبيق أحادي الصفحة، فالمسار يتغيّر بلا إعادة تحميل —
		// نُحدّث العنصر المميَّز عند كل تنقّل.
		try {
			if (window.frappe && frappe.router && frappe.router.on) {
				frappe.router.on('change', markCurrent);
			}
		} catch (e) {}
		window.addEventListener('popstate', markCurrent);

		// الشريط الأصلي يُعاد بناؤه عند التنقّل؛ نتأكد أن شريطنا باقٍ.
		var pending = false;
		new MutationObserver(function () {
			if (pending) return;
			pending = true;
			setTimeout(function () {
				pending = false;
				buildBar();
				markCurrent();
			}, 200);
		}).observe(document.body, { childList: true, subtree: true });
	}

	if (document.readyState === 'loading') {
		document.addEventListener('DOMContentLoaded', start);
	} else {
		start();
	}
})();
