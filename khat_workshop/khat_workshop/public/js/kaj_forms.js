// النماذج والحوارات — ما يُدخَل في أول شاشة يراها المستخدم عند الإضافة.
//
//   • «إضافة مستخدم»: حوار واحد فيه الاسم والبريد وكلمة المرور والمسمّى
//     الوظيفي. النموذج القياسي يأخذ البريد والاسم، ثم — بعد الحفظ — الأدوار في
//     تبويب ثانٍ بين ستين دوراً، وكلمة المرور في تبويب ثالث.
//   • تبويب الأدوار في نموذج المستخدم: المسمّيات الوظيفية وحدها. الأدوار
//     القياسية التي يحملها المسمّى يضيفها الخادم (khat_workshop/roles.py).
//   • الإضافة السريعة للعميل والمورد: الاسم والجوال. كانت اثني عشر حقلاً،
//     بينها سطرا عنوان ورمز بريدي وولاية ودولة، لعميل يقف عند الاستقبال.
//
// الطريقة في الثلاثة نقطة توسعة يوفّرها الإطار: صنف باسم
// «<المستند>QuickEntryForm» يستعمله frappe.new_doc أياً كان مصدر الطلب — زر
// القائمة، بلاطة اللوحة، أو «إضافة» من حقل اختيار داخل نموذج آخر.
(function () {
	'use strict';

	const isAr = () => String((frappe.boot && frappe.boot.lang) || 'ar').startsWith('ar');
	const tr = (ar, en) => (isAr() ? ar : en);
	const esc = (s) => frappe.utils.escape_html(s == null ? '' : String(s));
	const jobs = () => (frappe.boot.kaj && frappe.boot.kaj.roles) || [];

	// ── إضافة مستخدم ──────────────────────────────────────────────────────────
	function rolesHtml() {
		return '<div class="kaj-roles" role="group" aria-label="' + esc(tr('المسمّى الوظيفي', 'Job role')) + '">' +
			jobs().map((job) =>
				'<label class="kaj-role">' +
				'<input type="checkbox" value="' + esc(job.role) + '">' +
				'<span class="kaj-role-text"><span class="kaj-role-name">' + esc(isAr() ? job.ar : job.en) + '</span>' +
				'<span class="kaj-role-desc">' + esc(isAr() ? job.desc : job.desc_en) + '</span></span>' +
				'</label>').join('') +
			'</div><div class="kaj-roles-error" role="alert" hidden>' +
			esc(tr('اختر مسمّى وظيفياً واحداً على الأقل', 'Choose at least one job role')) + '</div>';
	}

	function addUser(after_insert) {
		const d = new frappe.ui.Dialog({
			title: tr('إضافة مستخدم', 'Add user'),
			size: 'large',
			fields: [
				{ fieldname: 'full_name', fieldtype: 'Data', reqd: 1, label: tr('الاسم الكامل', 'Full name') },
				{ fieldtype: 'Column Break' },
				{ fieldname: 'email', fieldtype: 'Data', options: 'Email', reqd: 1,
					label: tr('البريد الإلكتروني', 'Email'),
					description: tr('يسجّل به الدخول', 'Used to sign in') },
				{ fieldtype: 'Column Break' },
				{ fieldname: 'password', fieldtype: 'Password', reqd: 1, label: tr('كلمة المرور', 'Password'),
					description: tr('يغيّرها المستخدم من ملفه بعد أول دخول',
						'The user can change it from their profile') },
				{ fieldtype: 'Section Break', label: tr('المسمّى الوظيفي', 'Job role'),
					description: tr('يحدّد ما يراه المستخدم وما يستطيع فعله. يمكن اختيار أكثر من مسمّى.',
						'Decides what the user sees and can do. More than one may be chosen.') },
				{ fieldname: 'roles_html', fieldtype: 'HTML', options: rolesHtml() },
			],
			primary_action_label: tr('إضافة المستخدم', 'Add user'),
			primary_action: (values) => {
				const $wrap = d.fields_dict.roles_html.$wrapper;
				const chosen = $wrap.find('input:checked').map((i, el) => el.value).get();
				$wrap.find('.kaj-roles-error').prop('hidden', chosen.length > 0);
				if (!chosen.length) return;
				frappe.call({
					method: 'khat_workshop.api.add_user',
					args: { full_name: values.full_name, email: values.email,
						password: values.password, job_roles: chosen },
					freeze: true, btn: d.get_primary_btn(),
				}).then((r) => {
					const user = r.message;
					if (!user) return;
					d.hide();
					frappe.show_alert({
						message: tr('تمت إضافة المستخدم «' + esc(user.full_name) + '»', 'User “' + esc(user.full_name) + '” added'),
						indicator: 'green',
					});
					const doc = { doctype: 'User', name: user.name, full_name: user.full_name };
					if (frappe._from_link) frappe.ui.form.update_calling_link(doc);
					else if (after_insert) after_insert(doc);
					else if (window.cur_list && cur_list.doctype === 'User') cur_list.refresh();
				});
			},
		});
		d.fields_dict.roles_html.$wrapper.on('change', 'input', () =>
			d.fields_dict.roles_html.$wrapper.find('.kaj-roles-error').prop('hidden', true));
		d.show();
		return d;
	}

	function install() {
		const Base = frappe.ui && frappe.ui.form && frappe.ui.form.QuickEntryForm;
		if (!Base || !frappe.boot || !frappe.boot.kaj) return false;
		if (Base.__kaj) return true;
		Base.__kaj = true;

		// من لا يدير المستخدمين يبقى له سلوك الإطار (نموذج لا يملك حفظه أصلاً)
		frappe.ui.form.UserQuickEntryForm = class KajUserQuickEntry extends Base {
			setup() {
				if (!frappe.user.has_role('System Manager') || !jobs().length || this.doc) return super.setup();
				frappe.quick_entry = null;
				return Promise.resolve(addUser(this.after_insert));
			}
		};

		// ── العميل والمورد: الاسم والجوال ──
		// الصنف الأب (ERPNext) يضيف حقول جهة الاتصال والعنوان إلى الحوار ثم
		// ينقلها عند الحفظ؛ يُترك له النقل ويُختصر ما يضيفه. العنوان والبريد
		// يُضافان من نموذج العميل متى وُجدا.
		const Party = frappe.ui.form.ContactAddressQuickEntryForm;
		if (Party) {
			class KajPartyQuickEntry extends Party {
				get_variant_fields() {
					return [{ label: __('Mobile No'), fieldname: 'mobile_number', fieldtype: 'Data' }];
				}
			}
			frappe.ui.form.CustomerQuickEntryForm = KajPartyQuickEntry;
			frappe.ui.form.SupplierQuickEntryForm = KajPartyQuickEntry;
		}
		return true;
	}

	if (!install()) {
		let tries = 0;
		const timer = setInterval(() => { if (install() || ++tries > 60) clearInterval(timer); }, 100);
	}

	// ── ما أُخفي يبقى مخفياً، وما حُجب من الأزرار لا يُضاف ──
	// forms.py يخفي الحقل بخاصية على تعريفه. لكن سكربتات ERPNext تستدعي
	// toggle_display لتُظهر حقولاً بعينها عند كل فتح: «التسلسل» في كل مستند
	// جديد، ومجاميع عملة الشركة. الحارس هنا على دوالّ النموذج نفسها: طلب إظهار
	// حقل في قائمة الإخفاء يُتجاهل، أياً كان السكربت الذي طلبه.
	function guardForms() {
		const Form = frappe.ui && frappe.ui.form && frappe.ui.form.Form;
		if (!Form || !frappe.boot || !frappe.boot.kaj) return false;
		if (Form.prototype.__kaj) return true;
		Form.prototype.__kaj = true;

		const conf = () => frappe.boot.kaj.forms || {};
		const sets = {};
		const hidden = (doctype) => {
			if (!sets[doctype]) sets[doctype] = new Set((conf().hidden || {})[doctype] || []);
			return sets[doctype];
		};

		const toggle_display = Form.prototype.toggle_display;
		Form.prototype.toggle_display = function (fnames, show) {
			const set = hidden(this.doctype);
			if (show && set.size) {
				fnames = (Array.isArray(fnames) ? fnames : [fnames]).filter((name) => !set.has(name));
				if (!fnames.length) return;
			}
			return toggle_display.call(this, fnames, show);
		};

		const set_df_property = Form.prototype.set_df_property;
		Form.prototype.set_df_property = function (fieldname, property, value, docname, table_field) {
			if (property === 'hidden' && !cint(value)) {
				const df = table_field && frappe.meta.get_docfield(this.doctype, fieldname);
				const doctype = table_field ? (df && df.options) : this.doctype;
				if (doctype && hidden(doctype).has(table_field || fieldname)) return;
			}
			return set_df_property.apply(this, arguments);
		};

		const add_custom_button = Form.prototype.add_custom_button;
		Form.prototype.add_custom_button = function (label) {
			const blocked = (conf().buttons || {})[this.doctype];
			// الأزرار تُضاف بنصّها المترجَم؛ المقارنة بترجمة النص الأصلي
			if (blocked && blocked.some((source) => __(source) === label)) return $();
			return add_custom_button.apply(this, arguments);
		};
		return true;
	}
	// صنف النموذج يُحمَّل مع أول نموذج يُفتح، لا مع المكتب
	if (!guardForms()) {
		$(document).on('form-load', guardForms);
		let tries = 0;
		const timer = setInterval(() => { if (guardForms() || ++tries > 600) clearInterval(timer); }, 100);
	}

	// ── نماذج الإعدادات (مستند وحيد): عنوانها في الشريط الجانبي بالعربية ──
	// الإطار يكتب هناك اسم المستند، وهو في المستند الوحيد اسم نوعه الإنجليزي
	// («Workshop Settings»).
	$(document).on('form-refresh', function (e, frm) {
		if (!frm || !frm.meta || !frm.meta.issingle || !frm.sidebar) return;
		setTimeout(function () {
			$(frm.wrapper).closest('.page-container').find('.form-sidebar *').each(function () {
				if (!this.children.length && this.textContent.trim() === frm.doctype) this.textContent = __(frm.doctype);
			});
		}, 0);
	});

	// ── مركبة العميل: الموديل من ماركته ──
	// الحقلان مستقلان: قائمة الموديلات كانت تعرض موديلات كل الماركات، وتُحفظ
	// «شيفروليه» مع «تويوتا-كامري». بعد اختيار الماركة تُعرض موديلاتها وحدها؛
	// واختيار موديل يضبط ماركته، وتغيير الماركة يمحو موديلاً ليس منها.
	const modelBrand = (model) => frappe.db.get_value('Vehicle Model', model, 'brand')
		.then((r) => (r.message && r.message.brand) || '');
	frappe.ui.form.on('Customer Vehicle', {
		setup: function (frm) {
			frm.set_query('model', () => (frm.doc.brand ? { filters: { brand: frm.doc.brand } } : {}));
		},
		model: function (frm) {
			if (!frm.doc.model) return;
			modelBrand(frm.doc.model).then((brand) => {
				if (brand && frm.doc.brand !== brand) frm.set_value('brand', brand);
			});
		},
		brand: function (frm) {
			if (!frm.doc.model || !frm.doc.brand) return;
			const brand = frm.doc.brand;
			modelBrand(frm.doc.model).then((own) => {
				if (own && own !== brand && frm.doc.brand === brand) frm.set_value('model', '');
			});
		},
	});

	// ── تبويب الأدوار في نموذج المستخدم: المسمّيات الوظيفية وحدها ──
	// محرّر الأدوار يرسم خانة لكل دور في النظام ويجلبها بطلب خاص به، في وقت لا
	// يُعلم به النموذج. قاعدة CSS تُظهر خانات المسمّيات وتخفي غيرها أياً كان
	// وقت رسمها، بدل مطاردة لحظة الرسم.
	function roleEditorCss() {
		if (!jobs().length || document.getElementById('kaj-role-editor-css')) return;
		const scope = '.frappe-control[data-fieldname="roles_html"]';
		const shown = jobs().map((job) =>
			scope + ' .unit-checkbox:has(input[data-unit="' + CSS.escape(job.role) + '"])').join(',\n');
		const style = document.createElement('style');
		style.id = 'kaj-role-editor-css';
		style.textContent = scope + ' .unit-checkbox { display: none; }\n' + shown + ' { display: block; }\n' +
			// «تحديد الكل» يحدّد الخانات المخفية معها
			scope + ' .bulk-select-options { display: none !important; }';
		document.head.appendChild(style);
	}
	$(document).on('app_ready', roleEditorCss);
	if (frappe.boot && frappe.boot.kaj) roleEditorCss();

	window.kaj = window.kaj || {};
	window.kaj.forms = { addUser: addUser };
})();
