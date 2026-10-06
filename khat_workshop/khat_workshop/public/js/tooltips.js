// تلميحات عربية لأيقونات النظام.
//
// Frappe يعرض في صفوف القوائم وأشرطة الأدوات أيقونات بلا نص: قلب، فقاعة
// تعليق، ساعة، أسهم ترتيب، أزرار تعديل وحذف. بعضها يحمل `title` إنجليزياً
// وأكثرها لا يحمل شيئاً إطلاقاً — فالمستخدم يمرّ عليها ولا يعرف ما تفعل،
// ويضطر للتجربة. على نظام معرّب يستخدمه فنّيون لا تقنيون، هذا احتكاك يومي.
//
// الملف يضيف `title` عربياً (التلميح الذي يظهره المتصفح عند المرور) و
// `aria-label` (لقارئ الشاشة) لكل نمط معروف. لا يغيّر سلوكاً ولا يستبدل
// عنصراً — يضيف سمة فقط، فلا شيء ينكسر إن تغيّرت بنية Frappe لاحقاً.

(function () {
	'use strict';

	// محدد CSS -> التلميح العربي. المحددات مبنية على ما رُصد فعلياً في DOM
	// الصفحات، لا على تخمين.
	var MAP = [
		// ── صفوف القوائم ────────────────────────────────────────────────
		['.like-action', 'أعجبني'],
		['.liked', 'إلغاء الإعجاب'],
		['.comment-count', 'التعليقات'],
		['.list-row-activity .modified', 'آخر تعديل'],
		['.list-subject .level-item.seen', 'تمت قراءته'],
		['.list-row-checkbox', 'تحديد الصف'],
		['.list-check-all', 'تحديد الكل'],

		// ── أشرطة الأدوات ───────────────────────────────────────────────
		['.btn-refresh', 'تحديث'],
		['[data-original-title="Refresh"]', 'تحديث'],
		['.menu-btn-group > .btn', 'خيارات إضافية'],
		['.filter-button', 'الفلاتر'],
		['.filter-x-button', 'إزالة الفلاتر'],
		['.sort-selector .btn-order', 'عكس الترتيب'],
		['.list-count', 'عدد السجلات'],
		['.sidebar-toggle-btn', 'إظهار/إخفاء القائمة الجانبية'],

		// ── أزرار المستند ───────────────────────────────────────────────
		['.btn-edit', 'تعديل'],
		['.btn-delete', 'حذف'],
		['[data-label="Delete"]', 'حذف'],
		['[data-label="Edit"]', 'تعديل'],
		['[data-label="Duplicate"]', 'نسخ'],
		['[data-label="Print"]', 'طباعة'],
		['[data-label="Email"]', 'إرسال بالبريد'],
		['[data-label="Rename"]', 'إعادة تسمية'],
		['.btn-primary.primary-action', 'حفظ'],

		// ── شريط العنوان ────────────────────────────────────────────────
		['.navbar-home', 'الصفحة الرئيسية'],
		['.dropdown-notifications', 'الإشعارات'],
		['.search-bar', 'بحث'],

		// ── جداول الصفوف الفرعية ────────────────────────────────────────
		['.grid-add-row', 'إضافة صف'],
		['.grid-remove-rows', 'حذف الصفوف المحددة'],
		['.grid-duplicate-row', 'نسخ الصف'],
		['.grid-move-row', 'تحريك الصف'],
		['.grid-insert-row', 'إدراج صف'],
		['.btn-open-row', 'فتح الصف'],
	];

	// أزرار أيقونية لا يطالها أي محدد أعلاه: نستدلّ على وظيفتها من اسم أيقونة
	// SVG التي بداخلها (<use href="#icon-refresh">). هذا يغطي ما تضيفه
	// إصدارات Frappe لاحقاً دون تعديل القائمة يدوياً.
	var BY_ICON = {
		refresh: 'تحديث',
		'refresh-2': 'تحديث',
		'reload': 'تحديث',
		edit: 'تعديل',
		'edit-1': 'تعديل',
		delete: 'حذف',
		trash: 'حذف',
		close: 'إغلاق',
		'small-down': 'المزيد',
		'dot-horizontal': 'خيارات إضافية',
		filter: 'الفلاتر',
		search: 'بحث',
		add: 'إضافة',
		'small-add': 'إضافة',
		printer: 'طباعة',
		'mail': 'إرسال بالبريد',
		attachment: 'مرفقات',
		link: 'رابط',
		setting: 'إعدادات',
		'list': 'عرض القائمة',
		'sort-ascending': 'ترتيب تصاعدي',
		'sort-descending': 'ترتيب تنازلي',

		// أسماء رُصدت فعلياً في DOM الإصدار المثبّت. Frappe يخلط بين تسميتين
		// (icon-* القديمة وes-line-* الأحدث)، فنغطّي الاثنتين.
		'chevron-down': 'فتح القائمة',
		'chevron-up': 'طيّ القائمة',
		home: 'الصفحة الرئيسية',
		'equal-approximately': 'نوع المطابقة',
	};

	// المفتاح يُستخرج من href بعد إزالة أي من البادئتين.
	function iconKey(href) {
		return href.replace('#icon-', '').replace('#es-line-', '').replace('#es-', '').trim();
	}

	function applyByIcon(scope) {
		scope.querySelectorAll('button, a').forEach(function (el) {
			if ((el.textContent || '').trim()) return;          // له نص مرئي
			var cur = el.getAttribute('title');
			if (cur && /[؀-ۿ]/.test(cur)) return;      // تلميح عربي موجود
			var use = el.querySelector('use');
			if (!use) return;
			var href = use.getAttribute('href') || use.getAttribute('xlink:href') || '';
			var key = iconKey(href);
			var label = BY_ICON[key];
			if (!label) return;
			el.setAttribute('title', label);
			if (!el.getAttribute('aria-label')) el.setAttribute('aria-label', label);
		});
	}

	function apply(root) {
		var scope = root && root.querySelectorAll ? root : document;
		applyByIcon(scope);
		MAP.forEach(function (pair) {
			var sel = pair[0];
			var label = pair[1];
			var nodes;
			try {
				nodes = scope.querySelectorAll(sel);
			} catch (e) {
				return; // محدد غير مدعوم في متصفح قديم — نتجاوزه بهدوء
			}
			nodes.forEach(function (el) {
				// لا نطمس تلميحاً عربياً موجوداً، لكن نستبدل الإنجليزي.
				var cur = el.getAttribute('title');
				if (cur && /[؀-ۿ]/.test(cur)) return;
				el.setAttribute('title', label);
				if (!el.getAttribute('aria-label')) el.setAttribute('aria-label', label);
			});
		});
	}

	function start() {
		if (!document.body) return;
		apply(document);

		// القوائم تُعاد بناؤها عند كل تحميل أو فلترة أو تنقّل، فنعيد التطبيق
		// بعد كل تغيير في DOM. مؤجَّل بإطار واحد حتى لا نزاحم البناء نفسه.
		var pending = false;
		new MutationObserver(function () {
			if (pending) return;
			pending = true;
			requestAnimationFrame(function () {
				pending = false;
				apply(document);
			});
		}).observe(document.body, { childList: true, subtree: true });
	}

	if (document.readyState === 'loading') {
		document.addEventListener('DOMContentLoaded', start);
	} else {
		start();
	}
})();
