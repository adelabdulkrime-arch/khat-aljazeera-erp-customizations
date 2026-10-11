// شريط جانبي على نمط VS Code: شريط نشاط ضيق + لوح فرعي قابل للطي.
//
// الشريط الأصلي في v16 قائمة عريضة بأسماء اللوحات السبع كاملة، والوصول لأي
// شاشة يمرّ بفتح لوحتها ثم البحث عنها في جسم الصفحة.
//
// البنية هنا كما في VS Code: شريط أيقونات ضيّق دائم، ولوح فرعي يعرض محتويات
// اللوحة المختارة ويُطوى بالكامل.
//
// ── مصدر المحتويات ──
// اللوحات لا تتشارك مصدراً واحداً: «الورشة» تُعرّف محتوياتها في Workspace
// Link، أما لوحات المبيعات والمشتريات والمخزون والمحاسبة فتبني بطاقاتها في
// Custom HTML Block (عناصر .acd-tile تحمل data-action/data-target). قراءة
// Workspace Link وحدها كانت تُرجع «لا توجد عناصر» لكل ما عدا الورشة.
//
// فنقرأ المصدرين: الروابط من الخادم بصلاحيات المستخدم، والبطاقات من صفحة
// اللوحة نفسها بعد رسمها. قراءة الصفحة المرسومة تضمن أن اللوح يطابق ما تراه
// اللوحة حرفياً — فإن أُضيفت بطاقة غداً ظهرت في اللوح بلا تعديل هنا، وما
// يُخفيه الخادم لصلاحيات لا يصل أصلاً.
//
// ── ما لا يلمسه ──
// الشريط الأصلي يبقى كاملاً في DOM وفي مكانه: البحث والإشعارات وحساب
// المستخدم وزرّ الطيّ كلها تعمل كما كانت. نسخة سابقة أخفته بالكامل
// (display:none) فاختفت معه تلك العناصر — وهذا خطأ صُحّح هنا: نضيف طبقة
// تنقّل، لا نستبدل شريط النظام.

(function () {
	'use strict';

	var PANELS = [
		{ ws: 'Home',                 label: 'الرئيسية',         icon: 'home' },
		{ ws: 'Workshop',             label: 'الورشة',           icon: 'tool' },
		{ ws: 'Sales Dashboard',      label: 'لوحة المبيعات',    icon: 'shopping-cart' },
		{ ws: 'Purchasing Dashboard', label: 'لوحة المشتريات',   icon: 'package-plus' },
		{ ws: 'Inventory Dashboard',  label: 'لوحة المخزون',     icon: 'layout-grid' },
		{ ws: 'Accounting Dashboard', label: 'لوحة المحاسبة',    icon: 'receipt' },
		{ ws: 'General Settings',     label: 'الإعدادات العامة', icon: 'settings' },
	];

	// الرئيسية لوحة تحكّم لا مجموعة شاشات: النقر عليها يفتحها مباشرة.
	var NO_PANEL = ['Home'];

	var ACTIVE_KEY = 'kaj_active_panel';
	var OPEN_KEY = 'kaj_panel_open';
	var MOBILE_Q = '(max-width: 991px)';
	var TIP_DELAY = 300;

	var linkCache = {};      // روابط Workspace Link لكل لوحة
	var tileCache = {};      // بطاقات .acd-tile مقروءة من الصفحة
	var els = {};
	var current = '';

	function store(k, v) { try { localStorage.setItem(k, v); } catch (e) {} }
	function load(k, d) { try { return localStorage.getItem(k) || d; } catch (e) { return d; } }
	function t(s) { try { return window.__ ? window.__(s) : s; } catch (e) { return s; } }
	function isMobile() {
		try { return window.matchMedia(MOBILE_Q).matches; } catch (e) { return false; }
	}
	function slug(ws) { return ws.toLowerCase().replace(/\s+/g, '-'); }

	// ── مصدر ١: Workspace Link (الورشة وما يشبهها) ──
	function fetchLinks(ws) {
		if (linkCache[ws]) return Promise.resolve(linkCache[ws]);
		if (!window.frappe || !frappe.call) return Promise.resolve([]);
		return frappe.call({
			method: 'frappe.client.get_list',
			args: {
				doctype: 'Workspace Link',
				filters: { parent: ws, type: 'Link' },
				fields: ['label', 'link_to', 'link_type', 'idx'],
				parent: 'Workspace',
				limit_page_length: 0,
				order_by: 'idx asc',
			},
		}).then(function (r) {
			var rows = ((r && r.message) || []).filter(function (x) { return x.link_to; });
			linkCache[ws] = rows.map(function (row) {
				return { label: row.label || row.link_to, href: linkRoute(row) };
			});
			return linkCache[ws];
		}).catch(function () { linkCache[ws] = []; return []; });
	}

	function linkRoute(row) {
		var to = row.link_to;
		if (row.link_type === 'Report') return '/app/query-report/' + encodeURIComponent(to);
		if (row.link_type === 'Page') return '/app/' + encodeURIComponent(to);
		return '/app/' + encodeURIComponent(slug(to));
	}

	// ── مصدر ٢: بطاقات .acd-tile من صفحة اللوحة المرسومة ──
	// البطاقات تُبنى داخل Custom HTML Block بعد تحميل الصفحة، فنقرأها من
	// المستند حين تكون لوحتها مفتوحة. ونخزّنها، فتظل متاحة للّوح بعد أن
	// ينتقل المستخدم لصفحة أخرى.
	function harvestTiles(ws) {
		var tiles = document.querySelectorAll('.acd-tile[data-action]');
		if (!tiles.length) return null;
		var out = [];
		tiles.forEach(function (el) {
			var lbl = el.querySelector('.acd-tile-lbl');
			var label = (lbl ? lbl.textContent : el.textContent || '').trim();
			if (!label) return;
			out.push({ label: label, href: tileRoute(el) });
		});
		if (out.length) {
			tileCache[ws] = out;
			try { sessionStorage.setItem('kaj_tiles_' + ws, JSON.stringify(out)); } catch (e) {}
		}
		return out.length ? out : null;
	}

	function tileRoute(el) {
		var action = el.dataset.action;
		var target = el.dataset.target || '';
		var filters = el.dataset.filters;
		var base;
		if (action === 'report') base = '/app/query-report/' + encodeURIComponent(target);
		else if (action === 'page') base = '/app/' + encodeURIComponent(target);
		else base = '/app/' + encodeURIComponent(slug(target));
		// الفلاتر جزء من هوية البطاقة: «مرتجعات المبيعات» و«فواتير البيع»
		// يقصدان نفس الـdoctype ويفترقان بالفلتر وحده.
		if (filters) {
			try {
				var f = JSON.parse(filters);
				var q = Object.keys(f).map(function (k) {
					return encodeURIComponent(k) + '=' + encodeURIComponent(f[k]);
				}).join('&');
				if (q) base += '?' + q;
			} catch (e) {}
		}
		return base;
	}

	function cachedTiles(ws) {
		if (tileCache[ws]) return tileCache[ws];
		try {
			var raw = sessionStorage.getItem('kaj_tiles_' + ws);
			if (raw) { tileCache[ws] = JSON.parse(raw); return tileCache[ws]; }
		} catch (e) {}
		return null;
	}

	// ── مصدر ٣: ترميز كتلة اللوحة من الخادم ──
	// انتظارُ أن يزور المستخدم كل لوحة مرة ليمتلئ لوحها شرطٌ لا يُقبل: اللوح
	// يجب أن يعمل من أول دخول. فنقرأ ترميز Custom HTML Block نفسه ونحلّله
	// بنفس منطق .acd-tile. القراءة عبر frappe.client.get_value فتخضع
	// لصلاحيات المستخدم على الخادم.
	function fetchBlockTiles(ws) {
		if (!window.frappe || !frappe.call) return Promise.resolve([]);
		var block = ws + ' Tiles';
		return frappe.call({
			method: 'frappe.client.get_value',
			args: { doctype: 'Custom HTML Block', filters: { name: block }, fieldname: 'html' },
		}).then(function (r) {
			var html = r && r.message && r.message.html;
			if (!html) return [];
			var doc = new DOMParser().parseFromString(html, 'text/html');
			var out = [];
			doc.querySelectorAll('.acd-tile[data-action]').forEach(function (el) {
				var lbl = el.querySelector('.acd-tile-lbl');
				var label = (lbl ? lbl.textContent : '').trim();
				if (label) out.push({ label: label, href: tileRoute(el) });
			});
			if (out.length) tileCache[ws] = out;
			return out;
		}).catch(function () { return []; });
	}

	// محتويات لوحة: روابط مساحة العمل أولاً (الورشة)، ثم ما التُقط من
	// الصفحة، ثم ترميز الكتلة من الخادم — فلا تبقى لوحة فارغة.
	function itemsFor(ws) {
		return fetchLinks(ws).then(function (links) {
			if (links && links.length) return links;
			var cached = cachedTiles(ws);
			if (cached && cached.length) return cached;
			return fetchBlockTiles(ws);
		});
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
			// النقر على الأيقونة النشطة يطوي اللوح ويفتحه — سلوك VS Code.
			if (btn.dataset.ws === current && isOpen() && NO_PANEL.indexOf(current) === -1) {
				setOpen(false);
				return;
			}
			select(btn.dataset.ws, true);
		});

		bindTooltips(bar);
	}

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
			var rtl = document.documentElement.getAttribute('dir') === 'rtl';
			// الشريط على حافة البداية، فالتلميح يخرج ناحية النهاية.
			if (rtl) tip.style.right = Math.round(window.innerWidth - r.left + 10) + 'px',
				tip.style.left = 'auto';
			else tip.style.left = Math.round(r.right + 10) + 'px', tip.style.right = 'auto';
			tip.classList.add('is-on');
		}
		function hide() { clearTimeout(timer); tip.classList.remove('is-on'); }

		bar.addEventListener('mouseover', function (ev) {
			var btn = ev.target.closest('.kaj-ab-btn');
			if (!btn) return;
			clearTimeout(timer);
			timer = setTimeout(function () { show(btn); }, TIP_DELAY);
		});
		bar.addEventListener('mouseout', hide);
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
			'  <button type="button" class="kaj-sp-close" aria-label="' + t('طيّ اللوح') + '">' +
			'    <svg viewBox="0 0 24 24" width="15" height="15" fill="none" stroke="currentColor" ' +
			'stroke-width="2.3" stroke-linecap="round" stroke-linejoin="round">' +
			'<path d="M15 18l-6-6 6-6"/></svg>' +
			'  </button>' +
			'</div>' +
			'<div class="kaj-sp-body"></div>';
		document.body.appendChild(p);
		els.panel = p;
		els.title = p.querySelector('.kaj-sp-title');
		els.body = p.querySelector('.kaj-sp-body');
		p.querySelector('.kaj-sp-close').addEventListener('click', function () { setOpen(false); });

		var sc = document.createElement('div');
		sc.id = 'kaj-sp-scrim';
		sc.addEventListener('click', function () { setOpen(false); });
		document.body.appendChild(sc);
		els.scrim = sc;
	}

	function isOpen() { return document.body.classList.contains('kaj-panel-open'); }

	// الطيّ الحقيقي: اللوح ينزوي ويعود عرض المحتوى كاملاً، والحالة محفوظة.
	function setOpen(on) {
		document.body.classList.toggle('kaj-panel-open', !!on);
		if (els.scrim) els.scrim.classList.toggle('is-on', !!on && isMobile());
		store(OPEN_KEY, on ? '1' : '0');
	}

	function select(ws, navigate) {
		var panel = PANELS.filter(function (p) { return p.ws === ws; })[0];
		if (!panel) return;
		current = ws;

		if (els.bar) {
			els.bar.querySelectorAll('.kaj-ab-btn').forEach(function (b) {
				var on = b.dataset.ws === ws;
				b.classList.toggle('is-active', on);
				if (on) b.setAttribute('aria-current', 'page');
				else b.removeAttribute('aria-current');
			});
		}

		if (NO_PANEL.indexOf(ws) !== -1) {
			setOpen(false);
			store(ACTIVE_KEY, ws);
			if (navigate) go('/app/' + slug(ws));
			return;
		}

		store(ACTIVE_KEY, ws);
		fill(panel);
		setOpen(true);
		if (navigate) go('/app/' + slug(ws));
	}

	function fill(panel) {
		buildPanel();
		els.title.textContent = t(panel.label);
		els.body.innerHTML = '<div class="kaj-sp-note">' + t('جارٍ التحميل') + '…</div>';

		itemsFor(panel.ws).then(function (items) {
			els.body.innerHTML = '';

			var head = document.createElement('a');
			head.className = 'kaj-sp-link is-board';
			head.href = '/app/' + slug(panel.ws);
			head.textContent = t(panel.label);
			els.body.appendChild(head);

			if (!items.length) {
				var n = document.createElement('div');
				n.className = 'kaj-sp-note';
				n.textContent = t('لا توجد عناصر');
				els.body.appendChild(n);
			} else {
				items.forEach(function (it) {
					var a = document.createElement('a');
					a.className = 'kaj-sp-link';
					a.href = it.href;
					a.textContent = t(it.label);
					a.title = a.textContent;
					els.body.appendChild(a);
				});
			}
			markCurrent();
		});
	}

	function go(path) {
		try {
			if (window.frappe && frappe.set_route) {
				frappe.set_route(path.replace(/^\/app\/?/, '') || 'home');
				return;
			}
		} catch (e) {}
		window.location.href = path;
	}

	function markCurrent() {
		if (!els.body) return;
		var here = window.location.pathname.replace(/\/+$/, '');
		els.body.querySelectorAll('.kaj-sp-link').forEach(function (a) {
			var p = a.getAttribute('href').split('?')[0].replace(/\/+$/, '');
			a.classList.toggle('is-current', p === here);
		});
	}

	// مزامنة مع بطاقات الصفحة الرئيسية ومع المسار الحالي.
	function syncFromRoute() {
		var path = window.location.pathname.replace(/\/+$/, '');
		var m = path.match(/\/(?:app|desk)\/([^/?#]+)/);
		if (!m) return;
		var s = decodeURIComponent(m[1]).toLowerCase();
		var hit = PANELS.filter(function (p) { return slug(p.ws) === s; })[0];
		if (!hit) return;
		// نلتقط بطاقات هذه اللوحة إن كانت مرسومة، فيمتلئ لوحها لاحقاً.
		harvestTiles(hit.ws);
		if (hit.ws !== current) {
			current = hit.ws;
			if (els.bar) {
				els.bar.querySelectorAll('.kaj-ab-btn').forEach(function (b) {
					b.classList.toggle('is-active', b.dataset.ws === hit.ws);
				});
			}
			if (NO_PANEL.indexOf(hit.ws) === -1 && isOpen()) fill(hit);
		} else if (isOpen() && NO_PANEL.indexOf(hit.ws) === -1) {
			fill(hit);
		}
		markCurrent();
	}

	function styles() {
		if (document.getElementById('kaj-ab-css')) return;
		var css = document.createElement('style');
		css.id = 'kaj-ab-css';
		css.textContent = [
			':root{--kaj-ab-w:52px;--kaj-sp-w:230px;}',

			// ── شريط النشاط ──
			'#kaj-activitybar{position:fixed;inset-block:0;inset-inline-start:0;',
			'width:var(--kaj-ab-w);z-index:1035;display:flex;flex-direction:column;',
			'align-items:center;gap:4px;padding:10px 0;',
			'background:#16233d;border-inline-end:1px solid rgba(255,255,255,.07);}',
			'.kaj-ab-btn{position:relative;width:40px;height:40px;flex:0 0 auto;',
			'display:flex;align-items:center;justify-content:center;background:none;',
			'border:0;border-radius:10px;cursor:pointer;padding:0;',
			'color:rgba(255,255,255,.62);transition:color .15s,background .15s;}',
			'.kaj-ab-btn:hover{color:#fff;background:rgba(255,255,255,.09);}',
			'.kaj-ab-btn:focus-visible{outline:2px solid #f0b429;outline-offset:2px;}',
			'.kaj-ab-ico{width:21px;height:21px;}',
			'.kaj-ab-ico use{stroke:currentColor;}',
			'.kaj-ab-btn.is-active{color:#fff;background:rgba(255,255,255,.12);}',
			'.kaj-ab-btn.is-active::before{content:"";position:absolute;',
			'inset-inline-start:-10px;top:50%;transform:translateY(-50%);',
			'width:3px;height:24px;background:#fff;border-radius:0 3px 3px 0;}',
			'[dir="rtl"] .kaj-ab-btn.is-active::before{border-radius:3px 0 0 3px;}',

			// ── التلميح ──
			'#kaj-ab-tip{position:fixed;z-index:1045;pointer-events:none;',
			'transform:translateY(-50%);opacity:0;visibility:hidden;',
			'background:#0f1a2e;color:#fff;font-size:12.5px;line-height:1;',
			'padding:7px 11px;border-radius:7px;white-space:nowrap;',
			'border:1px solid rgba(255,255,255,.12);box-shadow:0 6px 18px rgba(0,0,0,.35);',
			'transition:opacity .12s;}',
			'#kaj-ab-tip.is-on{opacity:1;visibility:visible;}',

			// ── اللوح الفرعي ──
			'#kaj-sidepanel{position:fixed;inset-block:0;',
			'inset-inline-start:var(--kaj-ab-w);width:var(--kaj-sp-w);z-index:1034;',
			'display:flex;flex-direction:column;background:var(--card-bg,#fff);',
			'border-inline-end:1px solid var(--border-color,#e5e8ee);',
			'transform:translateX(-100%);visibility:hidden;',
			'transition:transform .22s cubic-bezier(.2,.8,.2,1),visibility .22s;}',
			'[dir="rtl"] #kaj-sidepanel{transform:translateX(100%);}',
			'body.kaj-panel-open #kaj-sidepanel{transform:none;visibility:visible;}',
			'.kaj-sp-head{display:flex;align-items:center;gap:8px;',
			'padding:14px 12px 10px;border-bottom:1px solid var(--border-color,#eef0f4);}',
			'.kaj-sp-title{font-size:12px;font-weight:700;letter-spacing:.4px;',
			'text-transform:uppercase;color:var(--text-muted,#8a94a6);',
			'overflow:hidden;text-overflow:ellipsis;white-space:nowrap;}',
			'.kaj-sp-close{margin-inline-start:auto;background:none;border:0;padding:4px;',
			'border-radius:6px;cursor:pointer;display:flex;color:var(--text-muted,#8a94a6);}',
			'[dir="rtl"] .kaj-sp-close svg{transform:scaleX(-1);}',
			'.kaj-sp-close:hover{background:var(--bg-light-gray,#f2f4f8);color:#e63946;}',
			'.kaj-sp-body{flex:1;overflow-y:auto;padding:8px;display:flex;',
			'flex-direction:column;gap:1px;}',
			'.kaj-sp-link{display:block;padding:7px 10px;border-radius:7px;font-size:13px;',
			'line-height:1.5;color:var(--text-color,#44546b);text-decoration:none;',
			'white-space:nowrap;overflow:hidden;text-overflow:ellipsis;',
			'transition:background .14s,color .14s;}',
			'.kaj-sp-link:hover{background:var(--bg-light-gray,#f2f4f8);',
			'color:var(--text-color,#1a2b4a);text-decoration:none;}',
			'.kaj-sp-link.is-board{font-weight:700;color:var(--text-color,#1a2b4a);margin-bottom:4px;}',
			'.kaj-sp-link.is-current{background:rgba(230,57,70,.10);color:#e63946;font-weight:600;}',
			'.kaj-sp-link:focus-visible{outline:2px solid #e63946;outline-offset:-2px;}',
			'.kaj-sp-note{padding:10px;font-size:12.5px;line-height:1.6;',
			'color:var(--text-muted,#8a94a6);}',

			// ── إزاحة المحتوى ──
			// الشريطان ثابتان فوق الصفحة، فالإزاحة تمنع اختفاء المحتوى تحتهما.
			// تُطبَّق على غلاف الصفحة لا على <body>: الإزاحة على body كانت
			// تحرّك الشريط العلوي والقوائم المنبثقة معها فيُقصّ المحتوى من
			// الجانب — وهو ما ظهر في الواجهة.
			'.main-section,.navbar,.page-head{',
			'transition:padding-inline-start .22s cubic-bezier(.2,.8,.2,1);}',
			'body[data-path] .main-section{padding-inline-start:var(--kaj-ab-w);}',
			'body.kaj-panel-open[data-path] .main-section{',
			'padding-inline-start:calc(var(--kaj-ab-w) + var(--kaj-sp-w));}',

			// ── الستارة (الجوال) ──
			'#kaj-sp-scrim{position:fixed;inset:0;z-index:1033;background:rgba(10,18,32,.45);',
			'opacity:0;visibility:hidden;transition:opacity .2s,visibility .2s;}',
			'#kaj-sp-scrim.is-on{opacity:1;visibility:visible;}',

			'@media ' + MOBILE_Q + '{',
			'  #kaj-sidepanel{width:min(78vw,280px);box-shadow:0 0 40px rgba(0,0,0,.28);}',
			'  body.kaj-panel-open[data-path] .main-section{',
			'    padding-inline-start:var(--kaj-ab-w);}',
			'}',
			'@media print{#kaj-activitybar,#kaj-sidepanel,#kaj-sp-scrim{display:none !important;}',
			'  body[data-path] .main-section{padding-inline-start:0 !important;}}',
			'@media (prefers-reduced-motion:reduce){',
			'  #kaj-sidepanel,.main-section{transition:none !important;}}',
		].join('');
		document.head.appendChild(css);
	}

	function restore() {
		var ws = load(ACTIVE_KEY, '');
		var open = load(OPEN_KEY, '1') === '1';
		if (ws && PANELS.some(function (p) { return p.ws === ws; })) {
			current = ws;
			if (els.bar) {
				els.bar.querySelectorAll('.kaj-ab-btn').forEach(function (b) {
					b.classList.toggle('is-active', b.dataset.ws === ws);
				});
			}
			if (open && !isMobile() && NO_PANEL.indexOf(ws) === -1) {
				fill(PANELS.filter(function (p) { return p.ws === ws; })[0]);
				setOpen(true);
			}
		}
		syncFromRoute();
	}

	function start() {
		if (!document.body) return;
		styles();
		buildBar();
		buildPanel();
		restore();

		try {
			if (window.frappe && frappe.router && frappe.router.on) {
				frappe.router.on('change', function () { setTimeout(syncFromRoute, 400); });
			}
		} catch (e) {}
		window.addEventListener('popstate', function () { setTimeout(syncFromRoute, 400); });

		// Ctrl+B يطوي اللوح ويعيده — نفس اختصار VS Code.
		document.addEventListener('keydown', function (ev) {
			if ((ev.ctrlKey || ev.metaKey) && (ev.key === 'b' || ev.key === 'B')) {
				if (NO_PANEL.indexOf(current) !== -1 || !current) return;
				ev.preventDefault();
				setOpen(!isOpen());
			}
		});

		// الصفحة تُعاد بناؤها عند التنقّل: نتأكد أن شريطنا باقٍ، ونلتقط
		// بطاقات اللوحة المفتوحة متى ظهرت.
		var pending = false;
		new MutationObserver(function () {
			if (pending) return;
			pending = true;
			setTimeout(function () {
				pending = false;
				buildBar();
				syncFromRoute();
			}, 300);
		}).observe(document.body, { childList: true, subtree: true });
	}

	if (document.readyState === 'loading') {
		document.addEventListener('DOMContentLoaded', start);
	} else {
		start();
	}
})();
