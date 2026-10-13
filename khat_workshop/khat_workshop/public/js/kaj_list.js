// شاشات القوائم — جدول واضح بدل قائمة Frappe القياسية.
//
// ما رُصد في القائمة القياسية ويعالَج هنا لكل القوائم دفعة واحدة:
//
//   • بجانب كل صف وقت آخر تعديل («2 د»)، عدّاد تعليقات وقلب إعجاب — أدوات
//     شبكة اجتماعية — ولا شيء لما يريده المستخدم فعلاً: تعديل الصف أو حذفه.
//     يحلّ محلّها عمود «الإجراءات».
//   • الأعمدة ما صادف أنه معلَّم «في القائمة»، ثم عمود «المعرّف». تُؤخذ الآن
//     من khat_workshop/lists.py: ما يحتاجه المستخدم، بالترتيب.
//   • القائمة تستعيد تصفية آخر زيارة. قائمة بطاقات العمل ظهرت فارغة وفيها
//     إحدى عشرة بطاقة، بسبب تصفية نُسيت قبل يومين. كل زيارة تبدأ الآن بما
//     طُلب: القائمة كاملة، أو مصفّاة بما تقوله البلاطة التي فُتحت منها.
//   • النقر على خلية كان يصفّي القائمة بقيمتها بدل فتح الصف. الصف كله الآن
//     يفتح مستنده.
//   • مبدّل العرض (قائمة/تقرير/كانبان…) والتصفيات المحفوظة في شريط الأدوات:
//     يُخفيان.
//
// الطريقة: صنف يرث frappe.views.ListView ويحلّ محلّه. عروض الإطار الأخرى
// (التقرير، الكانبان…) ترث الصنف الأصلي فلا تتأثر. كل دالة هنا تستدعي
// الأصل حيث أمكن؛ إن تغيّر اسم دالة في إصدار لاحق سقط ذلك التعديل وحده
// وبقيت القائمة تعمل.
(function () {
	'use strict';

	const isAr = () => String((frappe.boot && frappe.boot.lang) || 'ar').startsWith('ar');
	const tr = (ar, en) => (isAr() ? ar : en);
	const esc = (s) => frappe.utils.escape_html(s == null ? '' : String(s));
	const conf = (doctype) => ((frappe.boot.kaj && frappe.boot.kaj.lists) || {})[doctype] || null;

	// حقول قياسية ليست في تعريف المستند لكنها أعمدة صالحة
	const STD = {
		name: () => ({ fieldname: 'name', label: tr('الرقم', 'No.'), fieldtype: 'Data' }),
		creation: () => ({ fieldname: 'creation', label: tr('تاريخ الإنشاء', 'Created'), fieldtype: 'Date' }),
		modified: () => ({ fieldname: 'modified', label: tr('آخر تعديل', 'Last updated'), fieldtype: 'Date' }),
	};
	// أعمدة محسوبة: تُرسم فارغة ثم تُملأ بطلب واحد بعد عرض الصفوف
	const COMPUTED = {
		'@roles': () => ({ fieldname: '_kaj_roles', label: tr('الأدوار', 'Roles'), fieldtype: 'Data', kaj_computed: 'roles' }),
	};

	function install() {
		const Base = frappe.views && frappe.views.ListView;
		if (!Base || !frappe.boot || !frappe.boot.kaj) return false;
		if (Base.__kaj) return true;

		class KajListView extends Base {
			// العرض دائماً قائمة: لا يُستعاد عرض آخر (تقرير، كانبان) من زيارة سابقة
			static load_last_view() {
				const route = frappe.get_route();
				if (route.length === 2) {
					frappe.set_route('list', frappe.router.doctype_layout || route[1], 'list');
					return true;
				}
				return false;
			}

			setup_defaults() {
				// عنوان القائمة جمع («العملاء»)؛ اسم المستند المفرد («عميل») لأزرارها
				const plural = ((frappe.boot.kaj.plurals || {})[this.doctype]);
				if (plural) this.page_title = isAr() ? plural[0] : plural[1];
				const ready = super.setup_defaults();
				// خانة البحث بالرقم تظهر حيث للمستند رقم يُعرض في القائمة
				// (فاتورة، سند…). في غيرها اسم المستند هو عنوانه أو رمز داخلي.
				const c = conf(this.doctype);
				this.settings.hide_name_filter = !(c && (c.columns || []).includes('name'));
				// القائمة تبدأ كاملة: بلا تصفية الزيارة السابقة، وبلا التصفية
				// الافتراضية التي يضعها الإطار لبعض المستندات (المستخدمون
				// المفعّلون فقط مثلاً) — تصفية لم يطلبها أحد تُخفي صفوفاً بلا
				// سبب ظاهر. المعطَّل يظهر وحالته بجانبه.
				this.filters = [];
				return ready;
			}

			// بلاطة اللوحة تحدّد ما يُعرض: بتصفيتها، أو القائمة كاملة إن لم تكن
			// لها تصفية. الأصل يتجاهل route_options الفارغة فتبقى تصفية البلاطة
			// السابقة على القائمة نفسها.
			before_refresh() {
				if (!frappe.route_options || !this.filter_area) return Promise.resolve();
				const filters = this.parse_filters_from_route_options();
				frappe.route_options = null;
				this.filters = filters;
				return this.filter_area.clear(false).then(() =>
					(filters.length ? this.filter_area.set(filters) : null));
			}

			// الصفوف المستثناة تُضاف للاستعلام والعدّ، لا لعنوان الصفحة: هناك
			// تتحوّل إلى تصفية ظاهرة عند أول تحديث.
			get_filters_for_args() {
				const c = conf(this.doctype);
				const filters = super.get_filters_for_args();
				return c && c.exclude && !this.kaj_plain_filters ? filters.concat(c.exclude) : filters;
			}

			update_url_with_filters() {
				this.kaj_plain_filters = true;
				try { return super.update_url_with_filters(); } finally { this.kaj_plain_filters = false; }
			}

			get_args() {
				const args = super.get_args();
				args.with_comment_count = 0;
				return args;
			}

			// مبدّل العرض: القائمة هي العرض
			setup_view_menu() {}

			// «التصفيات المحفوظة»: التصفية نفسها نقرتان، وحفظها باسم ميزة لمحلّل
			// بيانات لا لموظف استقبال
			setup_list_filter_by() {}

			// قائمة «…»: يبقى الاستيراد. الباقي (ضوابط المستخدم، مدير الصلاحيات،
			// تخصيص النموذج، تعديل نوع المستند) أدوات مطوّر تُفتح من مكانها.
			get_menu_items() {
				const keep = __('Import', null, 'Button in list view menu');
				return super.get_menu_items().filter((item) => item.label === keep);
			}

			// ── الأعمدة ──
			get_fields_in_list_view() {
				const c = conf(this.doctype);
				if (!c) return super.get_fields_in_list_view();
				// ما يُجلب من الخادم: حقول الأعمدة، وحقل العمود الأول إن خُصّص،
				// وحقل الحالة الذي تُبنى منه شارة الحالة
				const fields = this.kaj_columns().filter((df) => !df.kaj_computed && !STD[df.fieldname]);
				[c.subject, 'status'].forEach((name) => {
					const df = name && frappe.meta.get_docfield(this.doctype, name);
					if (df && !fields.includes(df)) fields.push(df);
				});
				return fields;
			}

			kaj_columns() {
				const c = conf(this.doctype);
				return (c.columns || []).map((name) => {
					if (STD[name]) return STD[name]();
					if (COMPUTED[name]) return COMPUTED[name]();
					const df = frappe.meta.get_docfield(this.doctype, name);
					return df && frappe.perm.has_perm(this.doctype, df.permlevel, 'read') ? df : null;
				}).filter(Boolean);
			}

			// اسم المستند «رقم» حين يولّده النظام (WC-2026-00012)، و«اسم» حين
			// يكتبه المستخدم (اسم الدور، اسم الفني).
			kaj_name_df() {
				const auto = String(this.meta.autoname || '');
				const numbered = /^naming_series|\.#|^hash$|^autoincrement$/i.test(auto) || !auto;
				return numbered ? STD.name()
					: { fieldname: 'name', label: tr('الاسم', 'Name'), fieldtype: 'Data' };
			}

			setup_columns() {
				const c = conf(this.doctype);
				if (!c) {
					super.setup_columns();
					// عمود «المعرّف» في آخر القائمة: يكرّر العمود الأول أو يعرض رمزاً
					this.columns = this.columns.filter((col, i) =>
						i === 0 || !(col.type === 'Field' && col.df && col.df.fieldname === 'name'));
					if (this.columns[0].df && this.columns[0].df.fieldname === 'name') {
						this.columns[0].df = this.kaj_name_df();
					}
					return;
				}

				const get_df = (name) => frappe.meta.get_docfield(this.doctype, name);
				const subject = (c.subject && get_df(c.subject)) ||
					(this.meta.title_field && get_df(this.meta.title_field)) || this.kaj_name_df();
				this.columns = [{ type: 'Subject', df: subject }, { type: 'Tag' }];

				const fields = this.kaj_columns()
					.filter((df) => df.fieldname !== subject.fieldname)
					.map((df) => ({ type: 'Field', df: df }));
				this.columns = this.columns.concat(fields);

				if (c.status !== false && frappe.has_indicator(this.doctype)) {
					this.columns.push({ type: 'Status', df: { label: typeof c.status === 'string' ? c.status : 'Status' } });
				}
			}

			get_column_html(col, doc, show_in_mobile) {
				const df = col.df || {};
				if (df.kaj_computed) {
					// عرض ثابت: الإطار يحاذي الأعمدة بعرض موحّد لكل اسم حقل
					// (apply_column_widths)، وخلية بلا عرض تتمدّد بمحتواها
					// فتزيح ما بعدها في صفّها وحده.
					this.column_max_widths[df.fieldname] = 210;
					return '<div class="list-row-col ellipsis hidden-xs" data-fieldname="' + esc(df.fieldname) +
						'"><span class="kaj-computed ellipsis" data-compute="' +
						esc(df.kaj_computed) + '" data-name="' + esc(doc.name) + '"></span></div>';
				}
				// حالة بطاقة العمل بلونها، كما في اللوحة
				const colors = frappe.boot.kaj.status_colors || {};
				if (this.doctype === 'Work Card' && df.fieldname === 'status' && doc.status) {
					const color = /^#[0-9a-f]{6}$/i.test(colors[doc.status] || '') ? colors[doc.status] : '#6b7686';
					this.column_max_widths.status = Math.max(this.column_max_widths.status || 0, 170);
					return '<div class="list-row-col ellipsis hidden-xs" data-fieldname="status">' +
						'<span class="kaj-status" style="--kaj-st:' + color + '">' + esc(doc.status) + '</span></div>';
				}
				// التاريخ والوقت في القائمة تاريخٌ فقط: الوقت يضاعف عرض العمود
				// فيُقتطع («…3:29 13-10-2026»)، وتفصيله في المستند نفسه.
				if (df.fieldtype === 'Datetime' && doc[df.fieldname]) {
					const day = Object.assign({}, doc, { [df.fieldname]: String(doc[df.fieldname]).slice(0, 10) });
					return super.get_column_html(Object.assign({}, col, { df: Object.assign({}, df, { fieldtype: 'Date' }) }), day, show_in_mobile);
				}
				return super.get_column_html(col, doc, show_in_mobile);
			}

			// ── الصف: الإجراءات مكان الوقت والتعليقات والإعجاب ──
			get_header_html_skeleton(left, right) {
				return super.get_header_html_skeleton(left,
					'<span class="list-count"></span><span class="kaj-actions-head">' + tr('الإجراءات', 'Actions') + '</span>');
			}

			get_meta_html(doc) {
				const readonly = doc.docstatus > 0 || !this.can_write;
				const open = readonly ? tr('عرض', 'View') : tr('تعديل', 'Edit');
				// المعتمد لا يُحذف (يُلغى من داخله أولاً)، وهذا ما يفرضه الخادم أيضاً
				const deletable = frappe.model.can_delete(this.doctype) && doc.docstatus !== 1;
				return '<div class="level-item kaj-row-actions hidden-xs">' +
					'<a class="kaj-row-btn" href="' + this.get_form_link(doc) + '" title="' + open + '" aria-label="' + open + '">' +
					frappe.utils.icon(readonly ? 'eye' : 'pencil', 'sm') + '</a>' +
					(deletable
						? '<button type="button" class="kaj-row-btn kaj-row-delete" data-idx="' + doc._idx + '" title="' +
							tr('حذف', 'Delete') + '" aria-label="' + tr('حذف', 'Delete') + '">' + frappe.utils.icon('trash-2', 'sm') + '</button>'
						: '<span class="kaj-row-btn kaj-row-btn-none"></span>') +
					'</div><div class="level-item visible-xs text-right">' + this.get_indicator_html(doc) + '</div>';
			}

			setup_events() {
				super.setup_events();
				this.$result.on('click', '.kaj-row-delete', (e) => {
					e.preventDefault();
					e.stopPropagation();
					const doc = this.data[+e.currentTarget.getAttribute('data-idx')];
					if (doc) this.kaj_delete(doc);
				});
			}

			// النقر على خلية يفتح الصف، لا يصفّي القائمة بقيمتها
			setup_filterable() {
				this.$result.on('click', '.filterable', (e) => {
					if (e.metaKey || e.ctrlKey) return;
					e.stopPropagation();
					const link = $(e.currentTarget).closest('.list-row').find('.list-subject a').get(0);
					if (link) frappe.set_route(link.pathname);
				});
			}

			kaj_delete(doc) {
				const subject = this.columns[0].df.fieldname;
				const title = doc[subject] || doc.name;
				const what = __(this.doctype) + ' «' + title + '»';
				frappe.confirm(
					esc(tr('حذف ' + what + ' نهائياً؟ لا يمكن التراجع.', 'Delete ' + what + ' permanently? This cannot be undone.')),
					() => frappe.call({
						method: 'frappe.client.delete',
						args: { doctype: this.doctype, name: doc.name },
						freeze: true,
					}).then(() => {
						frappe.show_alert({ message: tr('تم الحذف', 'Deleted'), indicator: 'green' });
						this.refresh();
					})
				);
			}

			render_list() {
				super.render_list();
				this.kaj_fill_computed();
			}

			kaj_fill_computed() {
				const cells = this.$result.find('.kaj-computed[data-compute="roles"]');
				if (!cells.length) return;
				const users = cells.map((i, el) => el.getAttribute('data-name')).get();
				frappe.call({ method: 'khat_workshop.api.user_roles', args: { users: users }, type: 'GET' }).then((r) => {
					const roles = r.message || {};
					cells.each((i, el) => {
						const mine = roles[el.getAttribute('data-name')];
						if (mine === '*') { el.textContent = tr('مالك النظام', 'System owner'); return; }
						const list = (mine || []).map((role) => __(role));
						// ثلاثة أدوار تكفي للتعرّف؛ الباقي عدداً، والقائمة كاملة في التلميح
						el.textContent = list.length > 3
							? list.slice(0, 3).join('، ') + ' +' + (list.length - 3)
							: (list.join('، ') || '—');
						el.title = list.join('، ');
					});
				});
			}
		}

		KajListView.__kaj = true;
		frappe.views.ListView = KajListView;
		return true;
	}

	if (!install()) {
		let tries = 0;
		const timer = setInterval(() => { if (install() || ++tries > 60) clearInterval(timer); }, 100);
	}
})();
