// لوحات خط الجزيرة — رسّام واحد للوحات السبع.
//
// كل لوحة Custom HTML Block فيه نقطة تثبيت فارغة، وسكربته سطر واحد:
//     kaj.dashboard.mount(root_element, 'workshop')
// المحتوى كله يُرسم هنا من frappe.boot.kaj.modules (مصدره
// khat_workshop/navigation.py)، فاللوحات السبع تتشارك مكوّناً واحداً لكل شيء:
// بلاطة، رقم، عنوان قسم، زر. قبل ذلك كان لكل لوحة HTML وCSS وسكربت خاص بها
// (نحو 26KB مكرّرة في كل واحدة)، فاختلفت المقاسات والألوان والسلوك بينها.
//
// البلاطات روابط حقيقية (<a href>): تُفتح في تبويب جديد بالنقر الأوسط، ويصلها
// Tab وEnter، ويقرؤها قارئ الشاشة. ما لا يملك المستخدم صلاحيته لا يُرسم.
(function () {
	'use strict';

	window.kaj = window.kaj || {};

	const isAr = () => String((frappe.boot && frappe.boot.lang) || 'ar').startsWith('ar');
	const tr = (ar, en) => (isAr() ? ar : en);
	const lab = (o) => (isAr() ? o.label : o.label_en || o.label);
	const ttl = (o) => (isAr() ? o.title : o.title_en || o.title);
	const esc = (s) => frappe.utils.escape_html(s == null ? '' : String(s));
	const modules = () => (frappe.boot.kaj && frappe.boot.kaj.modules) || [];

	// الأيقونات معرَّفة <symbol> في المستند الرئيسي، و<use href> لا يعبر حدّ
	// Shadow DOM. يُنسخ رسم الرمز نفسه — بضعة مسارات — بدل جلب ملف الأيقونات
	// كاملاً (ألفا رمز) وحقنه في كل لوحة كما كان.
	function icon(name, cls) {
		const sym = name && document.getElementById('icon-' + name);
		if (!sym) return '';
		return '<svg class="kd-ico' + (cls ? ' ' + cls : '') + '" viewBox="' +
			(sym.getAttribute('viewBox') || '0 0 24 24') + '" aria-hidden="true">' + sym.innerHTML + '</svg>';
	}

	// ── الوجهات ──────────────────────────────────────────────────────────────
	function company() {
		return frappe.defaults.get_default('company') || (frappe.boot.sysdefaults || {}).company || '';
	}

	function href(t) {
		const slug = (s) => encodeURIComponent(frappe.router.slug(s));
		if (t.kind === 'list') {
			const q = t.filters ? '?' + new URLSearchParams(
				Object.entries(t.filters).filter(([, v]) => typeof v !== 'object')).toString() : '';
			return '/desk/' + slug(t.target) + q;
		}
		if (t.kind === 'new') return '/desk/' + slug(t.target) + '/new';
		if (t.kind === 'report') return '/desk/query-report/' + encodeURIComponent(t.target);
		if (t.kind === 'tree') return '/desk/' + slug(t.target) + '/view/tree';
		if (t.kind === 'form') return '/desk/' + slug(t.target);
		if (t.kind === 'company') return '/desk/company/' + encodeURIComponent(company());
		if (t.kind === 'workspace') return '/desk/' + slug(t.target);
		return '/desk/' + t.target;
	}

	function go(t) {
		if (t.kind === 'list') {
			// القائمة تبدأ بما تقوله البلاطة بالضبط: بتصفيتها إن كانت لها تصفية،
			// وكاملةً إن لم تكن (kaj_list.js لا يستعيد تصفية الزيارة السابقة).
			frappe.route_options = t.filters ? JSON.parse(JSON.stringify(t.filters)) : {};
			return frappe.set_route('List', t.target, 'List');
		}
		if (t.kind === 'new') return frappe.new_doc(t.target, t.defaults || {});
		if (t.kind === 'report') return frappe.set_route('query-report', t.target);
		if (t.kind === 'tree') return frappe.set_route('Tree', t.target);
		if (t.kind === 'form') return frappe.set_route('Form', t.target);
		if (t.kind === 'company') return frappe.set_route('Form', 'Company', company());
		if (t.kind === 'workspace') return frappe.set_route('Workspaces', t.target);
		if (t.kind === 'doc') return frappe.set_route('Form', t.target, t.name);
		return frappe.set_route(t.target);
	}

	function allowed(t) {
		const user = frappe.boot.user || {};
		if (t.kind === 'list' || t.kind === 'tree' || t.kind === 'form') return frappe.model.can_read(t.target);
		if (t.kind === 'new') return frappe.model.can_create(t.target);
		if (t.kind === 'company') return frappe.model.can_read('Company');
		if (t.kind === 'report') return !user.all_reports || !!user.all_reports[t.target];
		if (t.kind === 'page') return !frappe.boot.allowed_pages || frappe.boot.allowed_pages.includes(t.target);
		return true;
	}

	// ── القيم ────────────────────────────────────────────────────────────────
	function money(v, currency) {
		return format_currency(v || 0, currency || frappe.boot.sysdefaults.currency);
	}
	function count(v) {
		return format_number(v || 0, null, 0);
	}

	// ── القطع ────────────────────────────────────────────────────────────────
	// كل ما يُنقر يحمل data-go = فهرس في جدول الوجهات لهذه اللوحة
	function Board(root, module) {
		this.root = root;
		this.module = module;
		this.targets = [];
	}

	Board.prototype.ref = function (t) {
		this.targets.push(t);
		return this.targets.length - 1;
	};

	Board.prototype.tile = function (t) {
		return '<a class="kd-tile" href="' + esc(href(t)) + '" data-go="' + this.ref(t) + '">' +
			'<span class="kd-chip">' + icon(t.icon) + '</span>' +
			'<span class="kd-tile-label">' + esc(lab(t)) + '</span>' +
			icon('chevron-right', 'kd-chev') + '</a>';
	};

	Board.prototype.quick = function (t, primary) {
		return '<a class="kd-btn' + (primary ? ' kd-btn-primary' : '') + '" href="' + esc(href(t)) +
			'" data-go="' + this.ref(t) + '">' + icon(t.icon) + '<span>' + esc(lab(t)) + '</span></a>';
	};

	// كل قسم بطاقة تسرد بلاطاته عمودياً، والبطاقات في شبكة. قسم من بلاطة أو
	// اثنتين لا يحتلّ صفاً كاملاً من الصفحة كما لو كان شبكة مستقلة.
	Board.prototype.sections = function () {
		const cards = (this.module.sections || []).map((s) => {
			const tiles = s.tiles.filter(allowed);
			if (!tiles.length) return '';
			return '<section class="kd-sec kd-card"><h2 class="kd-sec-title">' + esc(ttl(s)) + '</h2>' +
				'<div class="kd-list">' + tiles.map((t) => this.tile(t)).join('') + '</div></section>';
		}).join('');
		if (!cards) {
			return '<p class="kd-note">' + tr('لا تملك صلاحية على أي شاشة في هذا القسم. راجع مدير النظام.',
				'You have no access to any screen in this section. Contact your administrator.') + '</p>';
		}
		return '<div class="kd-secs">' + cards + '</div>';
	};

	Board.prototype.header = function () {
		const m = this.module;
		const quick = (m.quick || []).filter(allowed);
		return '<header class="kd-head"><div class="kd-head-text">' +
			'<h1 class="kd-title">' + esc(ttl(m)) + '</h1>' +
			(m.desc ? '<p class="kd-desc">' + esc(isAr() ? m.desc : m.desc_en || m.desc) + '</p>' : '') +
			'</div>' +
			(quick.length ? '<div class="kd-quick">' + quick.map((t, i) => this.quick(t, i === 0)).join('') + '</div>' : '') +
			'</header>';
	};

	// الأرقام: هياكل بالمقاس النهائي حتى لا تقفز الصفحة حين تصل القيم
	Board.prototype.statsShell = function () {
		const n = (this.module.stats || []).length;
		if (!n) return '';
		return '<section class="kd-stats" aria-busy="true">' +
			new Array(n).fill('<div class="kd-stat kd-skel"><span class="kd-stat-label">&nbsp;</span><span class="kd-stat-val">&nbsp;</span></div>').join('') +
			'</section>';
	};

	Board.prototype.fillStats = function (data) {
		const box = this.root.querySelector('.kd-stats');
		if (!box) return;
		const stats = (data && data.stats) || [];
		if (!stats.length) { box.remove(); return; }
		box.setAttribute('aria-busy', 'false');
		box.innerHTML = stats.map((s) => {
			const value = s.kind === 'currency' ? money(s.value, data.currency) : count(s.value);
			return '<a class="kd-stat" href="' + esc(href(s.route)) + '" data-go="' + this.ref(s.route) + '">' +
				'<span class="kd-stat-label">' + esc(lab(s)) + '</span>' +
				'<span class="kd-stat-val">' + esc(value) + '</span></a>';
		}).join('');
	};

	// ── البحث ────────────────────────────────────────────────────────────────
	const GROUPS = [
		['customer', 'العملاء', 'Customers', 'users'],
		['vehicle', 'المركبات', 'Vehicles', 'car-front'],
		['work_card', 'بطاقات العمل', 'Work cards', 'clipboard-list'],
		['invoice', 'الفواتير', 'Invoices', 'receipt'],
	];

	Board.prototype.lookupShell = function () {
		if (!frappe.model.can_read('Customer')) return '';
		const ph = tr('اسم العميل، رقم الجوال، رقم اللوحة أو رقم الفاتورة', 'Customer name, mobile, plate or invoice number');
		return '<section class="kd-lookup"><label class="kd-lookup-field">' + icon('search') +
			'<input class="kd-lookup-input" type="search" autocomplete="off" spellcheck="false" ' +
			'placeholder="' + esc(ph) + '" aria-label="' + esc(tr('بحث', 'Search')) + '">' +
			'</label><div class="kd-lookup-out" hidden></div></section>';
	};

	Board.prototype.wireLookup = function () {
		const input = this.root.querySelector('.kd-lookup-input');
		const out = this.root.querySelector('.kd-lookup-out');
		if (!input || !out) return;
		let seq = 0, timer = null;

		const show = (html) => { out.innerHTML = html; out.hidden = !html; };
		const message = (text) => show('<p class="kd-note">' + esc(text) + '</p>');

		const profile = (name) => {
			const mine = ++seq;
			message(tr('جارٍ التحميل…', 'Loading…'));
			frappe.call('khat_workshop.api.customer_profile', { customer: name }).then((r) => {
				if (mine !== seq) return;
				const p = r.message;
				const row = (t, main, side) => '<a class="kd-row" href="' + esc(href(t)) + '" data-go="' + this.ref(t) + '">' +
					'<span>' + main + '</span>' + (side ? '<span class="kd-pill">' + esc(side) + '</span>' : '') + '</a>';
				const customer = { kind: 'doc', target: 'Customer', name: p.customer.name };
				const newCard = { kind: 'new', target: 'Work Card', defaults: { customer: p.customer.name } };
				let h = '<div class="kd-profile"><div class="kd-profile-head"><div>' +
					'<strong class="kd-profile-name">' + esc(p.customer.customer_name || p.customer.name) + '</strong>' +
					(p.customer.mobile_no ? '<bdi class="kd-profile-phone">' + esc(p.customer.mobile_no) + '</bdi>' : '') +
					'</div><div class="kd-profile-actions">' +
					(frappe.model.can_create('Work Card') ? '<a class="kd-btn kd-btn-primary" href="#" data-go="' + this.ref(newCard) + '">' + icon('plus') + '<span>' + tr('بطاقة عمل لهذا العميل', 'Work card for this customer') + '</span></a>' : '') +
					'<a class="kd-btn" href="' + esc('/desk/customer/' + encodeURIComponent(p.customer.name)) + '" data-go="' + this.ref(customer) + '"><span>' + tr('فتح ملف العميل', 'Open customer') + '</span></a>' +
					'</div></div>';
				h += '<div class="kd-figures">' +
					'<div><span>' + count(p.vehicles.length) + '</span><small>' + tr('المركبات', 'Vehicles') + '</small></div>' +
					'<div><span>' + esc(money(p.invoiced, p.currency)) + '</span><small>' + tr('إجمالي الفواتير', 'Invoiced') + '</small></div>' +
					'<div><span>' + esc(money(p.paid, p.currency)) + '</span><small>' + tr('المدفوع', 'Paid') + '</small></div>' +
					'<div class="' + (p.outstanding > 0 ? 'kd-due' : '') + '"><span>' + esc(money(p.outstanding, p.currency)) + '</span><small>' + tr('المتبقي', 'Outstanding') + '</small></div></div>';
				if (p.vehicles.length) {
					h += '<h3 class="kd-sub">' + tr('المركبات', 'Vehicles') + '</h3><div class="kd-rows">' + p.vehicles.map((v) =>
						row({ kind: 'doc', target: 'Customer Vehicle', name: v.name },
							'<bdi>' + esc(v.plate_number || v.name) + '</bdi>', [v.brand, v.model].filter(Boolean).join(' '))).join('') + '</div>';
				}
				if (p.work_cards.length) {
					h += '<h3 class="kd-sub">' + tr('أحدث بطاقات العمل', 'Latest work cards') + '</h3><div class="kd-rows">' + p.work_cards.map((w) =>
						row({ kind: 'doc', target: 'Work Card', name: w.name },
							'<bdi>' + esc(w.name) + '</bdi>' + (w.plate_number ? ' · <bdi>' + esc(w.plate_number) + '</bdi>' : ''), w.status)).join('') + '</div>';
				}
				if (p.invoices.length) {
					h += '<h3 class="kd-sub">' + tr('أحدث الفواتير', 'Latest invoices') + '</h3><div class="kd-rows">' + p.invoices.map((i) =>
						row({ kind: 'doc', target: 'Sales Invoice', name: i.name },
							'<bdi>' + esc(i.name) + '</bdi> · ' + esc(money(i.grand_total, p.currency)), __(i.status))).join('') + '</div>';
				}
				if (!p.vehicles.length && !p.work_cards.length && !p.invoices.length) {
					h += '<p class="kd-note">' + tr('لا مركبات ولا بطاقات ولا فواتير لهذا العميل بعد.', 'No vehicles, work cards or invoices for this customer yet.') + '</p>';
				}
				show(h + '</div>');
			});
		};

		const search = () => {
			const q = input.value.trim();
			const mine = ++seq;
			if (q.length < 2) { show(''); return; }
			frappe.call('khat_workshop.api.lookup', { q: q }).then((r) => {
				if (mine !== seq) return;      // وصل ردّ بحث أقدم بعد أحدث منه
				const rows = r.message || [];
				if (!rows.length) { message(tr('لا نتائج لـ«' + q + '»', 'No results for “' + q + '”')); return; }
				show(GROUPS.map(([type, ar, en, ic]) => {
					const items = rows.filter((x) => x.type === type);
					if (!items.length) return '';
					return '<h3 class="kd-sub">' + icon(ic) + tr(ar, en) + '</h3><div class="kd-rows">' + items.map((x) => {
						const side = x.amount != null ? money(x.amount, x.currency) : '';
						const attr = type === 'customer' ? 'data-profile="' + esc(x.name) + '" href="#"'
							: 'href="' + esc('/desk/' + frappe.router.slug(x.doctype) + '/' + encodeURIComponent(x.name)) +
								'" data-go="' + this.ref({ kind: 'doc', target: x.doctype, name: x.name }) + '"';
						return '<a class="kd-row" ' + attr + '><span><bdi>' + esc(x.title) + '</bdi>' +
							(x.sub ? '<small><bdi>' + esc(x.sub) + '</bdi></small>' : '') + '</span>' +
							(side ? '<span class="kd-pill">' + esc(side) + '</span>' : '') + '</a>';
					}).join('') + '</div>';
				}).join(''));
			});
		};

		input.addEventListener('input', () => { clearTimeout(timer); timer = setTimeout(search, 250); });
		input.addEventListener('keydown', (e) => {
			if (e.key === 'Enter') { e.preventDefault(); clearTimeout(timer); search(); }
			if (e.key === 'Escape') { input.value = ''; seq++; show(''); }
		});
		out.addEventListener('click', (e) => {
			const a = e.target.closest('[data-profile]');
			if (a) { e.preventDefault(); profile(a.dataset.profile); }
		});
	};

	// ── أحدث بطاقات العمل ────────────────────────────────────────────────────
	Board.prototype.recentShell = function () {
		if (!frappe.model.can_read('Work Card')) return '';
		const all = { kind: 'list', target: 'Work Card' };
		return '<section class="kd-recent"><div class="kd-recent-head"><h2 class="kd-sec-title">' +
			tr('أحدث بطاقات العمل', 'Latest work cards') + '</h2>' +
			'<a class="kd-link" href="' + esc(href(all)) + '" data-go="' + this.ref(all) + '">' + tr('عرض الكل', 'View all') + '</a></div>' +
			'<div class="kd-table-wrap"><p class="kd-note">' + tr('جارٍ التحميل…', 'Loading…') + '</p></div></section>';
	};

	Board.prototype.fillRecent = function (cards) {
		const wrap = this.root.querySelector('.kd-table-wrap');
		if (!wrap) return;
		if (!cards || !cards.length) {
			wrap.innerHTML = '<p class="kd-note">' + tr('لا توجد بطاقات عمل بعد.', 'No work cards yet.') + '</p>';
			return;
		}
		const head = [tr('رقم البطاقة', 'Card'), tr('العميل', 'Customer'), tr('المركبة', 'Vehicle'),
			tr('تاريخ الدخول', 'Checked in'), tr('الحالة', 'Status'), tr('الإجمالي', 'Total')];
		wrap.innerHTML = '<table class="kd-table"><thead><tr>' + head.map((h, i) =>
			'<th' + (i === 5 ? ' class="kd-num"' : '') + '>' + esc(h) + '</th>').join('') + '</tr></thead><tbody>' +
			cards.map((c) => {
				const t = { kind: 'doc', target: 'Work Card', name: c.name };
				const car = [c.brand, (c.model || '').replace(c.brand + '-', '')].filter(Boolean).join(' ');
				const color = /^#[0-9a-f]{6}$/i.test(c.status_color || '') ? c.status_color : '';
				return '<tr data-go="' + this.ref(t) + '" tabindex="0">' +
					'<td><a href="' + esc('/desk/work-card/' + encodeURIComponent(c.name)) + '" data-go="' + this.ref(t) + '"><bdi>' + esc(c.name) + '</bdi></a></td>' +
					'<td>' + esc(c.customer_name || '') + (c.customer_phone ? '<small><bdi>' + esc(c.customer_phone) + '</bdi></small>' : '') + '</td>' +
					'<td><bdi>' + esc(c.plate_number || '') + '</bdi>' + (car ? '<small>' + esc(car) + '</small>' : '') + '</td>' +
					'<td>' + esc(c.entry_date ? frappe.datetime.str_to_user(c.entry_date, false, true) : '') + '</td>' +
					'<td>' + (c.status ? '<span class="kd-status"' + (color ? ' style="--kd-st:' + color + '"' : '') + '>' + esc(c.status) + '</span>' : '') + '</td>' +
					'<td class="kd-num">' + esc(money(c.grand_total)) + '</td></tr>';
			}).join('') + '</tbody></table>';
	};

	// ── الرئيسية ─────────────────────────────────────────────────────────────
	Board.prototype.home = function () {
		const user = frappe.session.user;
		// «Administrator» اسم حساب تقني لا اسم شخص
		const who = user === 'Administrator' ? tr('مدير النظام', 'System Administrator') : (frappe.session.user_fullname || user);
		const brand = (frappe.boot.kaj && frappe.boot.kaj.brand) || {};
		const today = frappe.datetime.str_to_user(frappe.datetime.now_date());
		const cards = modules().filter((m) => m.key !== 'home').map((m) => {
			const visible = (m.sections || []).some((s) => s.tiles.some(allowed));
			if (!visible) return '';
			const t = { kind: 'workspace', target: m.workspace };
			return '<a class="kd-mod" style="--kd-module:' + esc(m.color) + '" href="' + esc(href(t)) + '" data-go="' + this.ref(t) + '">' +
				'<span class="kd-mod-chip">' + icon(m.icon) + '</span>' +
				'<span class="kd-mod-text"><strong>' + esc(ttl(m)) + '</strong><small>' + esc(isAr() ? m.desc : m.desc_en) + '</small></span>' +
				icon('chevron-right', 'kd-chev') + '</a>';
		}).join('');
		return '<header class="kd-hero"><div><h1 class="kd-hero-title">' + esc(tr('أهلاً، ', 'Hello, ') + who) + '</h1>' +
			'<p class="kd-hero-sub">' + esc(brand.name || '') + ' · <bdi>' + esc(today) + '</bdi></p></div>' +
			(brand.logo ? '<img class="kd-hero-logo" src="' + esc(brand.logo) + '" alt="">' : '') + '</header>' +
			this.lookupShell() +
			'<section class="kd-sec"><h2 class="kd-sec-title">' + tr('أقسام النظام', 'Modules') + '</h2>' +
			'<div class="kd-mods">' + cards + '</div></section>';
	};

	// ── التثبيت ──────────────────────────────────────────────────────────────
	Board.prototype.render = function () {
		const m = this.module;
		const widgets = m.widgets || [];
		const body = m.key === 'home' ? this.home()
			: this.header() + this.statsShell() +
				(widgets.includes('lookup') ? this.lookupShell() : '') +
				(widgets.includes('recent_cards') ? this.recentShell() : '') +
				this.sections();

		const host = this.root.querySelector('.kd-mount') || this.root;
		host.innerHTML = '<div class="kd" dir="' + (frappe.utils.is_rtl() ? 'rtl' : 'ltr') + '" data-module="' + esc(m.key) +
			'" style="--kd-module:' + esc(m.color || '#c62839') + '">' + body + '</div>';

		// نقرة عادية تتنقّل داخل التطبيق بلا إعادة تحميل؛ النقر الأوسط وCtrl
		// يتركان المتصفح يفتح الرابط في تبويب جديد.
		const activate = (e) => {
			const el = e.target.closest('[data-go]');
			if (!el) return;
			if (e.type === 'click' && (e.button !== 0 || e.ctrlKey || e.metaKey || e.shiftKey)) return;
			if (e.type === 'keydown' && e.key !== 'Enter') return;
			if (e.type === 'keydown' && el.tagName === 'A') return;     // الرابط يستقبل Enter نقرةً
			e.preventDefault();
			go(this.targets[+el.dataset.go]);
		};
		host.addEventListener('click', activate);
		host.addEventListener('keydown', activate);

		this.wireLookup();

		this.load();
		boards.push(this);
	};

	// الأرقام وأحدث البطاقات. تُطلب عند الرسم، ثم كلما عادت اللوحة إلى الواجهة.
	Board.prototype.load = function () {
		const m = this.module;
		if (!(m.stats || []).length && !(m.widgets || []).includes('recent_cards')) return;
		this.loadedAt = Date.now();
		frappe.call({ method: 'khat_workshop.api.dashboard', args: { module: m.key }, type: 'GET' })
			.then((r) => { this.fillStats(r.message); this.fillRecent(r.message && r.message.recent_cards); })
			.catch(() => { const s = this.root.querySelector('.kd-stats'); if (s) s.remove(); this.fillRecent([]); });
	};

	// المكتب يُبقي اللوحة في الصفحة بعد مغادرتها ويعرضها عند العودة كما رُسمت أول
	// مرة: بطاقة عمل أُنشئت بعدها لا تظهر، واللوحة تقول «لا توجد بطاقات عمل بعد»
	// إلى أن يُحدَّث المتصفح. مع كل تنقّل تُحدَّث اللوحة الظاهرة.
	const boards = [];
	const refresh = function () {
		for (let i = boards.length - 1; i >= 0; i--) {
			const b = boards[i], host = b.root.host || b.root;
			if (!host.isConnected) { boards.splice(i, 1); continue; }
			if (host.offsetParent !== null && Date.now() - (b.loadedAt || 0) > 2000) b.load();
		}
	};
	if (frappe.router && frappe.router.on) frappe.router.on('change', () => setTimeout(refresh, 400));

	kaj.dashboard = {
		mount: function (root, key) {
			const module = modules().find((m) => m.key === key);
			if (!module) return;
			new Board(root, module).render();
		},
		go: go,
		href: href,
		allowed: allowed,
		label: lab,
	};
})();
