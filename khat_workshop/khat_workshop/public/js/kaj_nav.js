// تنقّل ثابت: شريط جانبي واحد في كل شاشات النظام.
//
// Frappe v16 يختار الشريط الجانبي بحسب الشاشة المفتوحة: لكل وحدة قياسية شريطها
// (المستخدمون، المخازن، الحسابات…). فمن يفتح «المستخدمون» من الإعدادات العامة
// يجد قائمته الجانبية كلها قد استُبدلت بقائمة أخرى، ولا رابط فيها للعودة إلى
// لوحته. رُصد ستة عشر شريطاً مختلفاً عبر الشاشات التي تصل إليها اللوحات السبع.
//
// هنا يُحصر الاختيار في أشرطة لوحاتنا السبع — وكلها تحمل الروابط نفسها:
//   • الشاشة التي فُتحت من لوحة يبقى معها شريط تلك اللوحة كما هو.
//   • الدخول المباشر إلى شاشة (رابط محفوظ، تحديث الصفحة) يعرض شريط اللوحة
//     التي تنتمي إليها، من frappe.boot.kaj.nav (مصدره navigation.py).
//
// التدخّل في موضع واحد: Sidebar.setup، وهو ما تمرّ به كل طرق تبديل الشريط في
// الإطار. إن أعاد إصدار لاحق تسمية الدالة عاد سلوك الإطار الأصلي ولم ينكسر شيء.
(function () {
	'use strict';

	const data = () => (window.frappe && frappe.boot && frappe.boot.kaj) || null;
	const isAr = () => String(frappe.boot.lang || 'ar').startsWith('ar');

	function patchSidebar() {
		const Sidebar = frappe.ui && frappe.ui.Sidebar;
		const info = data();
		if (!Sidebar || !info) return false;
		if (Sidebar.prototype.__kaj_nav) return true;
		Sidebar.prototype.__kaj_nav = true;

		const ours = info.workspaces;
		const home = ours[0];

		function pick(sidebar, wanted) {
			if (ours.includes(wanted)) return wanted;
			if (sidebar.sidebar_title && ours.includes(sidebar.sidebar_title)) return sidebar.sidebar_title;
			return info.nav[wanted] || home;
		}

		const setup = Sidebar.prototype.setup;
		Sidebar.prototype.setup = function (title) {
			const before = this.sidebar_title;
			const out = setup.call(this, pick(this, title));
			// مسار التنقّل يقرأ اسم اللوحة من الشريط، ويُرسم قبل أن يتبدّل
			// الشريط: من انتقل من قائمة الأصناف إلى بطاقات العمل رأى
			// «المخزون ‹ بطاقات العمل». يُعاد رسمه متى تبدّل الشريط.
			if (this.sidebar_title !== before) {
				setTimeout(() => {
					if (frappe.breadcrumbs && frappe.breadcrumbs.__kaj_nav) frappe.breadcrumbs.update();
				}, 0);
			}
			return out;
		};

		// يُسأل عند كل تنقّل: «أي شريط لهذه الشاشة؟» — الحالي إن كان من أشرطتنا
		Sidebar.prototype.resolve_sidebar = function (entity) {
			this.preferred_sidebars = ours;
			return pick(this, info.nav[entity] || '');
		};

		Sidebar.prototype.show_sidebar_for_module = function () {
			if (this.sidebar_title && ours.includes(this.sidebar_title)) {
				this.set_active_workspace_item();
			} else {
				this.setup(home);
			}
		};

		// الإطار يظلّل بند الشريط الذي يطابق مسار الصفحة. داخل شاشة فرعية
		// (قائمة العملاء مثلاً) لا بند يطابق، فلا يُظلَّل شيء ويضيع «أين أنا».
		// نظلّل بند اللوحة التي يُعرض شريطها.
		const setActive = Sidebar.prototype.set_active_workspace_item;
		Sidebar.prototype.set_active_workspace_item = function () {
			setActive.call(this);
			if (this.is_route_in_sidebar()) return;
			const slug = '/desk/' + frappe.router.slug(this.sidebar_title || '');
			const anchor = this.wrapper.find('.item-anchor').filter(function () {
				const href = decodeURIComponent(($(this).attr('href') || '').split('?')[0]).replace(/\/$/, '');
				return href === slug;
			}).first();
			if (!anchor.length) return;
			if (this.active_item) this.active_item.removeClass('active-sidebar');
			this.active_item = anchor.parent();
			this.active_item.addClass('active-sidebar');
		};

		// لوحة لا يملك المستخدم صلاحية أي شيء فيها لا تظهر في شريطه
		const make = Sidebar.prototype.make_sidebar;
		Sidebar.prototype.make_sidebar = function () {
			make.call(this);
			const allowed = (window.kaj && window.kaj.dashboard && window.kaj.dashboard.allowed) || null;
			if (!allowed) return;
			const hiddenSlugs = info.modules
				.filter((m) => m.key !== 'home' && !(m.sections || []).some((s) => s.tiles.some(allowed)))
				.map((m) => '/desk/' + frappe.router.slug(m.workspace));
			this.wrapper.find('.item-anchor').each(function () {
				const href = decodeURIComponent(($(this).attr('href') || '').split('?')[0]).replace(/\/$/, '');
				if (hiddenSlugs.includes(href)) $(this).closest('.sidebar-item-container').hide();
			});
		};
		return true;
	}

	// ── رأس الشريط: شعار المنشأة وقائمة مختصرة ───────────────────────────────
	//
	// القائمة القياسية تعرض «سطح المكتب» (شبكة تطبيقات Frappe وERPNext وHR)،
	// و«الموقع»، و«الجلسة الافتراضية»، و«مساعدة» (وثائق Frappe بالإنجليزية).
	// كلها أبواب إلى خارج النظام كما يعرفه صاحب الورشة. يبقى ما يخصّه:
	// المظهر، تحديث البيانات، اللغة، والخروج.
	const DROP = ['desktop', 'workspaces', 'website', 'edit-sidebar', 'help'];
	const DROP_LABELS = ['Session Defaults'];

	function patchHeader() {
		const Header = frappe.ui && frappe.ui.SidebarHeader;
		const info = data();
		if (!Header || !info) return false;
		if (Header.prototype.__kaj_nav) return true;
		Header.prototype.__kaj_nav = true;

		if (info.brand && info.brand.logo) {
			Header.prototype.set_header_icon = function () {
				this.header_icon = '<img class="kaj-brand-logo" alt="" src="' +
					frappe.utils.escape_html(info.brand.logo) + '">';
			};
		}

		// الرأس يرسم لكل بند في قائمته صورةً من icon_url، وأغلب البنود بلا
		// icon_url: فيطلب المتصفح ‎/desk/undefined‎ — صفحة المكتب كاملةً، 420KB
		// تزاحم ملفات الصفحة — مع كل تحميل.
		const addItem = Header.prototype.add_app_item;
		Header.prototype.add_app_item = function (item) {
			if (item && !item.icon && !item.icon_url) item = Object.assign({}, item, { icon: 'circle' });
			return addItem.call(this, item);
		};

		const menu = Header.prototype.setup_app_switcher;
		Header.prototype.setup_app_switcher = function () {
			let items = (this.dropdown_items || []).filter((item) =>
				!DROP.includes(item.name) && !DROP_LABELS.includes(item.label) && !item.hidden);

			items.forEach((item) => {
				// بند اللغة يحمل اللغتين معاً («العربية / English») فلا يُعرف
				// أيّهما سيُفعَّل. يُسمّى باللغة التي سينتقل إليها.
				if (/'language'/.test(item.action || '')) {
					item.label = isAr() ? 'English' : 'العربية';
					item.icon = item.icon || 'languages';
				} else if (item.label && item.label !== 'Logout') {
					item.label = __(item.label);
				}
				if (item.name === 'logout') item.label = __('Log out');
			});

			// الفواصل: لا فاصل في أول القائمة أو آخرها، ولا فاصلان متتاليان
			items = items.filter((item, i) => !item.is_divider || (i > 0 && !items[i - 1].is_divider));
			while (items.length && items[items.length - 1].is_divider) items.pop();
			while (items.length && items[0].is_divider) items.shift();

			this.dropdown_items = items;
			return menu.call(this);
		};
		return true;
	}

	// ── مسار التنقّل أعلى الصفحة ─────────────────────────────────────────────
	//
	// المسار القياسي: أيقونة بيت تفتح /desk — شبكة تطبيقات الإطار لا رئيسية
	// النظام — ثم اسم المستند مفرداً («مستخدم») عنواناً لقائمة. يصير:
	//     الرئيسية ‹ اللوحة ‹ القائمة (جمعاً) ‹ المستند
	// فيعرف المستخدم أين هو، ويعود درجة أو درجتين بنقرة.
	function patchBreadcrumbs() {
		const bc = frappe.breadcrumbs;
		const info = data();
		if (!bc || !info || !frappe.app || !frappe.app.sidebar) return false;
		if (bc.__kaj_nav) return true;
		bc.__kaj_nav = true;

		bc.clear = function () {
			this.$breadcrumbs = $('.navbar-breadcrumbs').empty();
			this.append_breadcrumb_element('/desk/home', frappe.utils.icon('home'));
		};

		bc.set_workspace_breadcrumb = function () {
			const title = frappe.app.sidebar.sidebar_title;
			const module = info.modules.find((m) => m.workspace === title);
			if (!module || module.key === 'home') return;
			this.append_breadcrumb_element(
				'/desk/' + frappe.router.slug(module.workspace),
				frappe.utils.escape_html(isAr() ? module.title : module.title_en),
				'worksapce-breadcrumb'
			);
			this.$breadcrumbs.find('li a.worksapce-breadcrumb').parent().addClass('ellipsis');
		};

		const list = bc.set_list_breadcrumb;
		bc.set_list_breadcrumb = function (breadcrumbs) {
			list.call(this, breadcrumbs);
			const plural = (info.plurals || {})[breadcrumbs.doctype];
			if (plural) this.$breadcrumbs.find('li a.title-text').text(isAr() ? plural[0] : plural[1]);
		};

		// عنوان المستند من المستند المفتوح، لا من مسار الصفحة. بعد أول حفظ يبقى المسار
		// باسم المستند المؤقت (new-…) والمسار القياسي يقرأ العنوان منه: «إضافة فاتورة
		// مبيعات» فوق فاتورة محفوظة ومعتمدة، إلى أن تُحدَّث الصفحة.
		const form = bc.set_form_breadcrumb;
		bc.set_form_breadcrumb = function (breadcrumbs, view) {
			form.call(this, breadcrumbs, view);
			const frm = window.cur_frm;
			if (!frm || frm.doctype !== breadcrumbs.doctype || frm.is_new()) return;
			let title = frappe.model.get_doc_title(frm.doc) || frm.doc.name;
			if (frappe.utils.is_html(title)) title = strip_html(title);
			this.$breadcrumbs.find('.title-text-form').text(__(title))
				.attr('href', '/desk/' + frappe.router.slug(frm.doctype) + '/' + encodeURIComponent(frm.doc.name));
		};

		// قبل أن يحدّد الموجّه المسار (تحديث صفحة قائمة) لا مسار يُرسم بعد؛ الإطار
		// يرسمه حين يحدّده، بالدوالّ المعدَّلة أعلاه.
		if (frappe.get_route()) bc.update();
		return true;
	}

	// ── بلاطات اللوحات في البحث (Ctrl+K) ─────────────────────────────────────
	//
	// بحث الإطار يعرف الشاشات بأسمائها القياسية. بتسجيل البلاطات فيه يجد
	// المستخدم «سندات القبض» أو «مرتجعات المبيعات» بالاسم الذي يراه على
	// لوحته، وبتصفيتها. بحث واحد بدل اثنين: لوحة أوامر مستقلة (Ctrl+/) كانت
	// تكرّر هذا بقائمة مكتوبة باليد، وتخطف اختصار طيّ الشريط الجانبي.
	function registerSearch() {
		const info = data();
		const utils = frappe.search && frappe.search.utils;
		const dash = window.kaj && window.kaj.dashboard;
		if (!info || !utils || !utils.make_function_searchable || !dash) return false;
		if (registerSearch.done) return true;
		registerSearch.done = true;

		const seen = new Set();
		info.modules.forEach((m) => {
			const groups = (m.sections || []).map((s) => s.tiles).concat([m.quick || []]);
			groups.forEach((tiles) => tiles.forEach((t) => {
				const label = dash.label(t);
				if (seen.has(label) || !dash.allowed(t)) return;
				seen.add(label);
				utils.make_function_searchable(() => dash.go(t), label);
			}));
		});
		return true;
	}

	function attempt() {
		const a = patchSidebar();
		const b = patchHeader();
		const c = registerSearch();
		const d = patchBreadcrumbs();
		return a && b && c && d;
	}

	// ── شاشة النسخ الاحتياطي: التاريخ كما يُكتب في بقية النظام ──
	// الصفحة تكتب تاريخ كل نسخة كما يطبعه الخادم: «Wed Oct 14 04:36 2026».
	function backupDates() {
		if (!frappe.get_route || frappe.get_route_str() !== 'backups') return;
		$('.page-container:visible .layout-main-section *').each(function () {
			const text = this.children.length ? '' : this.textContent.trim();
			if (!/^[A-Z][a-z]{2} [A-Z][a-z]{2}\s+\d{1,2} \d{2}:\d{2} \d{4}$/.test(text)) return;
			const when = moment(text.replace(/\s+/g, ' '), 'ddd MMM D HH:mm YYYY', 'en');
			if (when.isValid()) this.textContent = frappe.datetime.str_to_user(when.format('YYYY-MM-DD HH:mm:ss'));
		});
	}
	if (frappe.router && frappe.router.on) {
		frappe.router.on('change', () => [300, 1200, 3000].forEach((ms) => setTimeout(backupDates, ms)));
	}

	// frappe.boot وأصناف الشريط تُعرَّف قبل هذا الملف في الترتيب المعتاد؛
	// المحاولات المتكررة تغطي أي ترتيب تحميل آخر، وتتوقف عند النجاح.
	if (!attempt()) {
		let tries = 0;
		const timer = setInterval(() => { if (attempt() || ++tries > 60) clearInterval(timer); }, 100);
	}
})();
