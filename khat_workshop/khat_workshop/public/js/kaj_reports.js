// التقارير — المرشّحات التي يحتاجها المستخدم، وقائمة «…» بلا أدوات المطوّر.
//
//   • فوق كل تقرير من تقارير ERPNext صفّان أو ثلاثة من المرشّحات (25 في
//     «مديونيات العملاء»). يبقى منها ما في khat_workshop/reports.py؛ الباقي
//     يُخفى ويحتفظ بقيمته الافتراضية، فالتقرير يُحسب كما كان.
//   • قائمة «…»: يبقى التحديث والطباعة وPDF والتصدير. «تعديل» يفتح منشئ
//     التقارير، و«ضوابط المستخدم» و«الإعداد التلقائي للبريد» و«إضافة عمود»
//     أدوات لمن يبني التقرير لا لمن يقرؤه.
//
// التدخّل في دالتين من صنف التقرير (setup_filters، get_menu_items). إن تغيّر
// اسم إحداهما في إصدار لاحق عاد ذلك الجزء إلى سلوك الإطار ولم ينكسر التقرير.
(function () {
	'use strict';

	const all = () => (frappe.boot && frappe.boot.kaj && frappe.boot.kaj.reports) || {};
	const conf = () => all().filters || {};
	const isAr = () => String((frappe.boot && frappe.boot.lang) || 'ar').startsWith('ar');

	// أعمدة قيمتها اسم نوع مستند («Sales Invoice»، «Customer»): تُعرض بالعربية
	const DOCTYPE_COLUMNS = ['voucher_type', 'party_type', 'against_voucher_type', 'reference_type'];
	// تقارير التحليل تسمّي أعمدتها «Oct 2026» من الخادم بلا ترجمة
	const MONTHS = { Jan: 'يناير', Feb: 'فبراير', Mar: 'مارس', Apr: 'أبريل', May: 'مايو', Jun: 'يونيو',
		Jul: 'يوليو', Aug: 'أغسطس', Sep: 'سبتمبر', Oct: 'أكتوبر', Nov: 'نوفمبر', Dec: 'ديسمبر' };
	const KEEP_MENU = ['Refresh', 'Print', 'PDF', 'Export'];

	function install() {
		const Report = frappe.views && frappe.views.QueryReport;
		if (!Report || !frappe.boot || !frappe.boot.kaj) return false;
		if (Report.prototype.__kaj) return true;
		Report.prototype.__kaj = true;

		// تقرير آخر يُفتح في الصفحة نفسها: يبقى السابق ظاهراً، بعنوانه وأرقامه، إلى أن
		// يصل إعداد الجديد من الخادم — ثوانٍ على اتصال بطيء يقرأ فيها المستخدم «قائمة
		// الدخل» فوق جدول رصيد المخزون. يُفرَّغ قبل التحميل.
		const load_report = Report.prototype.load_report;
		Report.prototype.load_report = function () {
			[this.$report, this.$chart, this.$summary].forEach((el) => el && el.empty && el.empty());
			if (this.$message) this.$message.hide && this.$message.hide();
			if (this.page && this.page.set_title) this.page.set_title(__(frappe.get_route()[1] || ''));
			return load_report.apply(this, arguments);
		};

		const setup_filters = Report.prototype.setup_filters;
		Report.prototype.setup_filters = function () {
			const keep = conf()[this.report_name];
			const filters = (this.report_settings && this.report_settings.filters) || [];
			if (keep) {
				filters.forEach((df) => {
					// الفواصل بلا اسم حقل؛ والمخفي أصلاً يبقى مخفياً
					if (df.fieldname && !keep.includes(df.fieldname)) df.hidden = 1;
				});
			}
			return setup_filters.apply(this, arguments);
		};

		const prepare_columns = Report.prototype.prepare_columns;
		if (prepare_columns) {
			Report.prototype.prepare_columns = function (columns) {
				const hide = (all().hidden_columns || {});
				const names = (hide['*'] || []).concat(hide[this.report_name] || []);
				// بعد تجهيز الإطار للأعمدة: تصل من بعض التقارير نصوصاً لا كائنات
				const prepared = prepare_columns.apply(this, arguments) || [];
				prepared.forEach((col) => {
					if (!col || typeof col !== 'object') return;
					if (names.includes(col.fieldname)) col.hidden = 1;
					const m = isAr() && /^([A-Z][a-z]{2}) ([0-9]{4})$/.exec(col.label || '');
					if (m && MONTHS[m[1]]) {
						col.label = MONTHS[m[1]] + ' ' + m[2];
						if (col.name) col.name = col.label;
					}
				});
				return prepared;
			};
		}

		const get_menu_items = Report.prototype.get_menu_items;
		if (get_menu_items) {
			Report.prototype.get_menu_items = function () {
				const keep = KEEP_MENU.map((label) => __(label));
				return (get_menu_items.apply(this, arguments) || []).filter((item) => keep.includes(item.label));
			};
		}
		return true;
	}

	function trim(name, settings) {
		if (!settings || typeof settings !== 'object') return;
		localize(settings);
		const keep = conf()[name];
		if (!keep || !Array.isArray(settings.filters)) return;
		settings.filters.forEach((df) => {
			if (df.fieldname && !keep.includes(df.fieldname)) df.hidden = 1;
		});
	}

	// «نوع السند» و«نوع الطرف» يصلان بالاسم الإنجليزي للمستند. يُعرضان مترجمَين
	// نصاً بلا رابط: الرابط الأصلي يفتح تعريف نوع المستند، لا المستند.
	function localize(settings) {
		if (settings.__kaj_localized) return;
		settings.__kaj_localized = true;
		const formatter = settings.formatter;
		settings.formatter = function (value, row, column, data, default_formatter) {
			if (column && DOCTYPE_COLUMNS.includes(column.fieldname) && value && typeof value === 'string') {
				return frappe.utils.escape_html(__(value));
			}
			return formatter
				? formatter.call(this, value, row, column, data, default_formatter)
				: default_formatter(value, row, column, data);
		};
	}

	// صنف التقرير يُحمَّل مع أول تقرير يُفتح، لا مع المكتب. ثلاث نقاط تضمن أن
	// أول تقرير يُفتح يأتي مختصراً مثل ما بعده:
	//   1. تعريف التقرير يُسجَّل في frappe.query_reports عند تحميل سكربته؛
	//      يُختصر لحظة تسجيله.
	//   2. frappe.require يحمّل حزمة التقارير؛ يُثبَّت التعديل فور وصولها.
	//   3. محاولات دورية احتياطاً لأي ترتيب تحميل آخر.
	frappe.provide('frappe.query_reports');
	if (!frappe.query_reports.__kaj && typeof Proxy === 'function') {
		Object.keys(frappe.query_reports).forEach((name) => trim(name, frappe.query_reports[name]));
		frappe.query_reports = new Proxy(frappe.query_reports, {
			get: (target, name) => (name === '__kaj' ? true : target[name]),
			set: (target, name, value) => { trim(name, value); target[name] = value; return true; },
		});
	}

	if (!install()) {
		const require = frappe.require;
		if (typeof require === 'function' && !require.__kaj) {
			frappe.require = function (items, callback) {
				const done = function () { install(); return callback && callback.apply(this, arguments); };
				const out = require.call(this, items, done);
				return out && typeof out.then === 'function' ? out.then((r) => { install(); return r; }) : out;
			};
			frappe.require.__kaj = true;
		}
		let tries = 0;
		const timer = setInterval(() => { if (install() || ++tries > 600) clearInterval(timer); }, 100);
	}
})();
