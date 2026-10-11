// شريط جانبي شجريّ على طريقة VS Code.
//
// الشريط في v16 قائمة مسطّحة: سبع لوحات، كل واحدة رابط واحد. للوصول إلى
// «بطاقات العمل» يفتح المستخدم لوحة الورشة ثم يبحث عن البطاقة في جسم
// الصفحة — خطوتان لكل شاشة يفتحها عشرات المرات يومياً.
//
// الفكرة المطلوبة (وهي فكرة مستكشف VS Code): الوحدة الرئيسية سطر قابل للطي،
// وعند الضغط عليه تنسدل محتوياته تحته، فيصل المستخدم لأي شاشة من الشريط
// مباشرة دون مغادرة ما هو فيه.
//
// التنفيذ كلّه أمامي: يقرأ روابط مساحات العمل من واجهة القراءة العامة
// (frappe.client.get_list) ويبني العقد تحت عناصر الشريط القائمة. لا يلمس
// قاعدة بيانات ولا يضيف نقطة نهاية، ولا يحذف عنصراً من الشريط الأصلي —
// يضيف طبقة فوقه. فإن تغيّر الشريط في إصدار قادم بقيت الروابط الأصلية
// تعمل كما هي ولم ينكسر شيء.
//
// الصلاحيات محفوظة: get_list يطبّق صلاحيات المستخدم، فمن لا يملك قراءة
// الفواتير لا تظهر له روابطها — لأننا نسأل الخادم ولا نبني القائمة محلياً.

(function () {
	'use strict';

	// نقتصر على لوحات الورشة السبع: إضافة شجرة تحت كل مساحة عمل في النظام
	// تُطيل الشريط بما لا يُقرأ، والسبع هي ما يستخدمه الفنّي فعلاً.
	var TREE_FOR = [
		'Workshop',
		'Sales Dashboard',
		'Purchasing Dashboard',
		'Inventory Dashboard',
		'Accounting Dashboard',
		'General Settings',
	];

	var STORE_KEY = 'kaj_sidebar_open';
	var cache = null;          // روابط كل المساحات، تُجلب مرة واحدة
	var building = false;

	// ── حفظ حالة الطيّ ──
	// من يفتح «الورشة» يريدها مفتوحة في الزيارة القادمة أيضاً. localStorage
	// قد يرمي في وضع التصفّح الخاص، فكل وصول محمي.
	function readOpen() {
		try { return JSON.parse(localStorage.getItem(STORE_KEY) || '{}') || {}; }
		catch (e) { return {}; }
	}
	function writeOpen(st) {
		try { localStorage.setItem(STORE_KEY, JSON.stringify(st)); } catch (e) {}
	}

	function t(s) {
		try { return window.__ ? window.__(s) : s; } catch (e) { return s; }
	}

	// مسار العنصر: Link إلى doctype يفتح قائمته، وReport يفتح التقرير.
	function routeFor(row) {
		var to = row.link_to || '';
		if (!to) return null;
		if (row.link_type === 'Report') {
			return '/app/query-report/' + encodeURIComponent(to);
		}
		if (row.link_type === 'Page') {
			return '/app/' + encodeURIComponent(to);
		}
		// Link إلى DocType: الاسم يُحوَّل لصيغة المسار (شُرَط بدل مسافات).
		return '/app/' + encodeURIComponent(to.toLowerCase().replace(/\s+/g, '-'));
	}

	// ── جلب الروابط ──
	// نداء واحد لكل المساحات بدل نداء لكل واحدة: ستة نداءات عند كل تحميل
	// صفحة حِمل بلا داعٍ على خادم الورشة.
	function fetchLinks() {
		if (cache) return Promise.resolve(cache);
		if (!window.frappe || !frappe.call) return Promise.resolve(null);
		return frappe.call({
			method: 'frappe.client.get_list',
			args: {
				doctype: 'Workspace Link',
				filters: { parent: ['in', TREE_FOR], type: 'Link' },
				fields: ['parent', 'label', 'link_to', 'link_type', 'idx'],
				parent: 'Workspace',
				limit_page_length: 0,
				order_by: 'idx asc',
			},
		}).then(function (r) {
			var rows = (r && r.message) || [];
			cache = {};
			rows.forEach(function (row) {
				if (!row.link_to) return;
				(cache[row.parent] = cache[row.parent] || []).push(row);
			});
			return cache;
		}).catch(function (e) {
			// فشل الجلب لا يكسر الشريط: تبقى الروابط الأصلية تعمل.
			console.warn('[kaj] sidebar tree: links unavailable', e);
			cache = {};
			return cache;
		});
	}

	// اسم مساحة العمل من عنصر الشريط. الرابط يحمل /app/<slug>، فنطابقه
	// بأسماء المساحات بدل الاعتماد على النص المعروض (يتغيّر مع اللغة).
	function wsNameOf(item) {
		var a = item.querySelector('a[href]');
		var href = a ? a.getAttribute('href') : '';
		var m = (href || '').match(/\/app\/([^/?#]+)/);
		if (!m) return null;
		var slug = decodeURIComponent(m[1]).toLowerCase();
		for (var i = 0; i < TREE_FOR.length; i++) {
			var ws = TREE_FOR[i];
			if (ws.toLowerCase().replace(/\s+/g, '-') === slug) return ws;
		}
		return null;
	}

	function buildNode(ws, item, links) {
		if (!links || !links.length) return;
		if (item.querySelector('.kaj-tree-children')) return;   // بُني سابقاً

		var open = readOpen()[ws] === true;

		// زرّ الطيّ: لا نلفّ الرابط الأصلي ولا نُعطّله — الضغط على اسم
		// الوحدة يفتح لوحتها كما كان، والضغط على السهم وحده يطوي ويفتح.
		// خلط الأمرين (أن يفتح الاسمُ الشجرةَ) يسلب المستخدم الوصول للوحة.
		var caret = document.createElement('button');
		caret.type = 'button';
		caret.className = 'kaj-tree-caret';
		caret.setAttribute('aria-expanded', open ? 'true' : 'false');
		caret.setAttribute('aria-label', t('إظهار المحتويات'));
		caret.innerHTML =
			'<svg viewBox="0 0 24 24" width="14" height="14" fill="none" ' +
			'stroke="currentColor" stroke-width="2.4" stroke-linecap="round" ' +
			'stroke-linejoin="round"><path d="M9 18l6-6-6-6"/></svg>';

		var box = document.createElement('div');
		box.className = 'kaj-tree-children' + (open ? '' : ' is-collapsed');

		links.forEach(function (row) {
			var href = routeFor(row);
			if (!href) return;
			var a = document.createElement('a');
			a.className = 'kaj-tree-link';
			a.href = href;
			a.textContent = t(row.label || row.link_to);
			a.title = a.textContent;
			box.appendChild(a);
		});

		if (!box.children.length) return;

		caret.addEventListener('click', function (ev) {
			// الضغط على السهم لا يجب أن يصل للرابط الأب فيُبحر بعيداً.
			ev.preventDefault();
			ev.stopPropagation();
			var nowOpen = caret.getAttribute('aria-expanded') !== 'true';
			caret.setAttribute('aria-expanded', nowOpen ? 'true' : 'false');
			box.classList.toggle('is-collapsed', !nowOpen);
			var st = readOpen();
			st[ws] = nowOpen;
			writeOpen(st);
		});

		var head = item.querySelector('.sidebar-item-control') || item.firstElementChild || item;
		head.appendChild(caret);
		item.appendChild(box);
		item.classList.add('kaj-has-tree');
	}

	function build() {
		if (building) return;
		var items = document.querySelectorAll('.sidebar-item-container');
		if (!items.length) return;

		building = true;
		fetchLinks().then(function (links) {
			building = false;
			if (!links) return;
			document.querySelectorAll('.sidebar-item-container').forEach(function (item) {
				var ws = wsNameOf(item);
				if (ws) buildNode(ws, item, links[ws]);
			});
		}).catch(function () { building = false; });
	}

	function styles() {
		if (document.getElementById('kaj-tree-css')) return;
		var css = document.createElement('style');
		css.id = 'kaj-tree-css';
		css.textContent = [
			// السهم يجلس في طرف السطر، ويدور عند الفتح — نفس اصطلاح VS Code.
			'.kaj-tree-caret{margin-inline-start:auto;background:none;border:0;',
			'padding:3px;display:flex;align-items:center;justify-content:center;',
			'color:var(--text-muted,#8a94a6);cursor:pointer;border-radius:5px;',
			'flex:0 0 auto;transition:transform .18s cubic-bezier(.2,.8,.2,1),background .15s;}',
			// في RTL يشير السهم لليسار وهو مغلق، ولأسفل وهو مفتوح.
			'[dir="rtl"] .kaj-tree-caret{transform:rotate(180deg);}',
			'.kaj-tree-caret[aria-expanded="true"]{transform:rotate(90deg);}',
			'[dir="rtl"] .kaj-tree-caret[aria-expanded="true"]{transform:rotate(90deg);}',
			'.kaj-tree-caret:hover{background:rgba(127,127,127,.16);color:var(--text-color,#1a2b4a);}',
			'.kaj-tree-caret:focus-visible{outline:2px solid #e63946;outline-offset:1px;}',
			// المحتويات: إزاحة وخطّ رأسي يربطها ببعضها كشجرة لا كقائمة ثانية.
			'.kaj-tree-children{display:flex;flex-direction:column;gap:1px;',
			'margin:2px 0 6px;padding-inline-start:22px;position:relative;}',
			'.kaj-tree-children::before{content:"";position:absolute;',
			'inset-inline-start:11px;top:2px;bottom:2px;width:1px;',
			'background:var(--border-color,#e5e8ee);}',
			'.kaj-tree-children.is-collapsed{display:none;}',
			'.kaj-tree-link{display:block;padding:5px 10px;border-radius:6px;',
			'font-size:12.5px;line-height:1.45;color:var(--text-muted,#7c8697);',
			'text-decoration:none;white-space:nowrap;overflow:hidden;',
			'text-overflow:ellipsis;transition:background .14s,color .14s;}',
			'.kaj-tree-link:hover{background:var(--bg-light-gray,#f2f4f8);',
			'color:var(--text-color,#1a2b4a);text-decoration:none;}',
			'.kaj-tree-link:focus-visible{outline:2px solid #e63946;outline-offset:-2px;}',
			// الشريط مطويّ (أيقونات فقط): الشجرة بلا معنى هناك.
			'.sidebar-collapsed .kaj-tree-children,',
			'.sidebar-collapsed .kaj-tree-caret{display:none;}',
		].join('');
		document.head.appendChild(css);
	}

	function start() {
		styles();
		build();
		// الشريط يُعاد بناؤه عند التنقّل بين اللوحات، فنُعيد تركيب الشجرة بعد
		// كل بناء. buildNode تتحقق من وجودها أولاً فلا تُكرّرها.
		var pending = false;
		new MutationObserver(function () {
			if (pending) return;
			pending = true;
			setTimeout(function () { pending = false; build(); }, 180);
		}).observe(document.body, { childList: true, subtree: true });
	}

	if (document.readyState === 'loading') {
		document.addEventListener('DOMContentLoaded', start);
	} else {
		start();
	}
})();
