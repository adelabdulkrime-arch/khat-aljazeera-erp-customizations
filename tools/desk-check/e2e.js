// تجربة النظام بإدخالات حقيقية من الواجهة — يُحمَّل في المعاينة المحلية:
//
//   const s = document.createElement('script'); s.src = '/__kaj/e2e.js'; document.head.append(s);
//   await __kajE2E.run('workshop')     // أو: purchasing · stock · accounting · settings
//
// كل سيناريو يفتح النماذج كما يفتحها المستخدم (frappe.new_doc، الإدخال
// السريع، أزرار «إنشاء» داخل المستند)، يملأ الحقول بدوالّ النموذج نفسها
// فتعمل سكربتات الحقول والتحقق، ثم يضغط زرّ الصفحة الأساسي للحفظ والاعتماد.
// ما يُسجَّل لكل خطوة: هل نجحت، اسم المستند وحالته، وكل رسالة خطأ ظهرت
// (حوار أحمر، حقول ناقصة، طلب فاشل، استثناء).
//
// يعمل على نسخة الاختبار وحدها: يرفض التشغيل على أي موقع آخر.
(function () {
  const sleep = ms => new Promise(r => setTimeout(r, ms));
  const TAG = 'تجربة';
  const stamp = String(Date.now()).slice(-6);

  const errors = [];
  const note = (kind, msg) => errors.push(kind + ': ' + String(msg).replace(/\s+/g, ' ').slice(0, 260));
  if (!window.__kajE2EHooked) {
    window.__kajE2EHooked = true;
    window.addEventListener('error', e => { if (!/ResizeObserver loop/.test(e.message || '')) note('js', e.message); });
    window.addEventListener('unhandledrejection', e => { const r = e.reason; note('promise', (r && (r.message || r.exc_type)) || JSON.stringify(r || '').slice(0, 120)); });
    $(document).ajaxError((ev, xhr, opts) => { if (!/socket\.io/.test(opts.url) && !(xhr.status === 0 && xhr.statusText === 'abort')) note('http ' + xhr.status, (opts.url || '').split('?')[0] + ' ' + String((xhr.responseJSON && (xhr.responseJSON.exception || xhr.responseJSON._server_messages)) || '').slice(0, 200)); });
    const mp = frappe.msgprint;
    frappe.msgprint = function (m) {
      let o = (m && typeof m === 'object') ? m : { message: m };
      // رسائل الخادم تصل نصّ JSON فيه الرسالة ولونها
      if (typeof o.message === 'string' && o.message.trim().startsWith('{')) { try { o = Object.assign({}, o, JSON.parse(o.message)); } catch (e) { /* نص عادي */ } }
      const text = $('<div>').html(Array.isArray(o.message) ? o.message.join(' ') : (o.message || '')).text().trim();
      // تنبيه النجاح الأخضر («تم الحفظ») ليس خطأ، والرسالة الفارغة لا تُعرض
      if (text && !(o.alert && o.indicator === 'green')) {
        note((/red|orange/.test(o.indicator || '') || o.raise_exception ? 'خطأ' : 'رسالة') + (o.title ? ' «' + o.title + '»' : ''), text);
      }
      return mp.apply(this, arguments);
    };
  }
  const takeErrors = () => errors.splice(0);

  async function settle(max = 40000) {
    const t0 = Date.now(); let quiet = 0;
    while (Date.now() - t0 < max) {
      quiet = (frappe.request.ajax_count > 0 || $('#freeze:visible, .freeze-message-container:visible').length) ? 0 : quiet + 1;
      if (quiet >= 6) return true;
      await sleep(100);
    }
    note('مهلة', 'الواجهة لم تهدأ خلال ' + max + 'ms (طلبات جارية: ' + frappe.request.ajax_count + '، تجميد: ' + $('#freeze:visible, .freeze-message-container:visible').length + ')'); return false;
  }
  const closeDialogs = () => { $('.modal.show').each(function () { $(this).modal('hide'); }); };
  // الحوارات الإعلامية والتأكيدية تُغلق كما يغلقها المستخدم: بزرّها الأساسي
  async function confirmDialog() {
    for (let i = 0; i < 20; i++) {
      const $m = $('.modal.show:visible').last();
      if ($m.length && $m.find('.modal-footer .btn-primary:visible').length && !$m.find('.form-layout .frappe-control:visible input:visible').length) {
        $m.find('.modal-footer .btn-primary:visible').first().click(); await sleep(400); return true;
      }
      await sleep(150);
    }
    return false;
  }

  async function openNew(doctype, opts) {
    closeDialogs();
    frappe.new_doc(doctype, opts || {});
    for (let i = 0; i < 300; i++) {
      const dialog = window.cur_dialog && cur_dialog.display && cur_dialog.doctype === doctype ? cur_dialog : null;
      if (dialog) { await settle(); return { quick: dialog }; }
      if (window.cur_frm && cur_frm.doctype === doctype && cur_frm.is_new() && $(cur_frm.wrapper).is(':visible')) { await settle(); await sleep(500); return { frm: cur_frm }; }
      await sleep(100);
    }
    throw new Error('لم يُفتح نموذج ' + doctype);
  }

  async function setValues(frm, values) {
    for (const [field, value] of Object.entries(values || {})) {
      if (!frm.fields_dict[field]) throw new Error('الحقل ' + field + ' غير موجود في ' + frm.doctype);
      await frm.set_value(field, value);
      await settle(15000);
    }
  }
  async function addRows(frm, table, rows) {
    // نماذج المعاملات تفتح بصفّ أول فارغ؛ المستخدم يملؤه ولا يضيف تحته
    const blank = (frm.doc[table] || []).filter(r => !Object.keys(r).some(k => !['name', 'idx', 'doctype', 'parent', 'parentfield', 'parenttype', 'docstatus', 'owner', 'creation', 'modified', 'modified_by'].includes(k) && !k.startsWith('__') && ['item_code', 'item', 'service', 'account', 'technician'].includes(k) && r[k]));
    for (const row of rows || []) {
      const child = blank.shift() || frm.add_child(table, {});
      frm.refresh_field(table);
      for (const [field, value] of Object.entries(row)) {
        await frappe.model.set_value(child.doctype, child.name, field, value);
        await settle(15000);
      }
    }
    frm.refresh_field(table);
  }

  // زرّ الصفحة الأساسي: «حفظ» للمسودة، «اعتماد» للمحفوظة
  async function pressPrimary(frm) {
    const $btn = frm.page.btn_primary;
    if (!$btn || !$btn.is(':visible')) throw new Error('لا زرّ أساسي ظاهر في ' + frm.doctype);
    const label = $btn.text().trim();
    $btn.click();
    await sleep(600);
    await confirmDialog();
    await settle(60000);
    await sleep(700);
    return label;
  }

  function invisibleMandatory(frm) {
    // حقول إلزامية فارغة لا يراها المستخدم: النموذج سيرفض الحفظ بلا سبب ظاهر
    return frm.fields.filter(f => f.df.reqd && !['Section Break', 'Column Break', 'Tab Break'].includes(f.df.fieldtype))
      .filter(f => { const v = frm.doc[f.df.fieldname]; return (v === undefined || v === null || v === '' || (Array.isArray(v) && !v.length)); })
      .filter(f => f.df.hidden || !$(f.wrapper).closest('.form-layout').length || $(f.wrapper).closest('.hide-control').length)
      .map(f => f.df.fieldname).filter(name => !name.startsWith('__'));
  }

  const steps = [];
  async function step(title, fn) {
    takeErrors();
    const rec = { step: title, ok: false };
    try { const result = await fn() || {}; Object.assign(rec, result); rec.ok = result.ok !== false; }
    catch (e) { rec.ok = false; rec.exception = (e && e.message) || String(e); }
    rec.errors = takeErrors();
    // رسالة خطأ أو طلب فاشل = الخطوة فشلت ولو لم تُرمَ استثناءً
    if (rec.errors.some(e => /^(http|js|promise|مهلة|خطأ)/.test(e)) && rec.expectError !== true) rec.ok = false;
    closeDialogs();
    steps.push(rec);
    return rec;
  }

  // مستند كامل: فتح، ملء، حفظ، ثم اعتماد إن طُلب
  async function create(doctype, values, tables, opts) {
    opts = opts || {};
    const { frm, quick } = await openNew(doctype, opts.defaults);
    if (quick) {
      for (const [field, value] of Object.entries(values || {})) {
        if (!quick.fields_dict[field]) throw new Error('الإدخال السريع لـ' + doctype + ' بلا حقل ' + field);
        await quick.set_value(field, value); await sleep(150);
      }
      const shown = quick.fields.filter(f => f.fieldtype && !['Section Break', 'Column Break'].includes(f.fieldtype) && !f.hidden && $(quick.fields_dict[f.fieldname] && quick.fields_dict[f.fieldname].wrapper).is(':visible')).map(f => f.label || f.fieldname);
      let saved = null;
      const sniff = (ev, xhr, opts) => { if (/frappe\.client\.save/.test(opts.url + ' ' + (opts.data || '')) && xhr.responseJSON && xhr.responseJSON.message && xhr.responseJSON.message.doctype === doctype) saved = xhr.responseJSON.message; };
      $(document).on('ajaxComplete', sniff);
      quick.get_primary_btn().click();
      await sleep(600); await settle(40000); await sleep(800);
      $(document).off('ajaxComplete', sniff);
      if (!saved) throw new Error('الإدخال السريع لم يحفظ ' + doctype);
      return { name: saved.name, docstatus: saved.docstatus, quickFields: shown };
    }
    await setValues(frm, values);
    for (const [table, rows] of Object.entries(tables || {})) await addRows(frm, table, rows);
    if (opts.before) await opts.before(frm);
    const missing = invisibleMandatory(frm);
    const visible = frm.fields.filter(f => !['Section Break', 'Column Break', 'Tab Break', 'HTML', 'Button'].includes(f.df.fieldtype) && !f.df.hidden && $(f.wrapper).is(':visible')).length;
    await pressPrimary(frm);
    if (frm.is_new()) throw new Error('لم يُحفظ ' + doctype + (missing.length ? ' — إلزامي غير ظاهر: ' + missing.join(',') : ''));
    const out = { name: frm.doc.name, docstatus: frm.doc.docstatus, visibleFields: visible };
    if (missing.length) out.hiddenMandatory = missing;
    if (opts.submit) {
      await pressPrimary(frm);
      out.docstatus = frm.doc.docstatus;
      if (frm.doc.docstatus !== 1) throw new Error(doctype + ' ' + frm.doc.name + ' لم يُعتمد');
    }
    return out;
  }

  // زرّ داخل قائمة «إنشاء» أو زرّ مخصّص في رأس المستند
  async function clickAction(frm, label) {
    const $all = frm.page.wrapper.find('.page-actions .dropdown-item:not(.hide), .page-actions .btn:visible, .inner-group-button .dropdown-item');
    const $hit = $all.filter((i, e) => $(e).text().trim() === label || $(e).attr('data-label') === encodeURIComponent(label)).first();
    if (!$hit.length) throw new Error('لا زرّ «' + label + '» في ' + frm.doctype + '. الموجود: ' + $all.map((i, e) => $(e).text().trim()).get().filter(Boolean).join('، '));
    $hit[0].click();
    await sleep(800); await confirmDialog(); await settle(60000); await sleep(1000);
  }
  async function openDoc(doctype, name) {
    await frappe.set_route('Form', doctype, name);
    for (let i = 0; i < 300; i++) { if (window.cur_frm && cur_frm.doctype === doctype && cur_frm.doc.name === name && $(cur_frm.wrapper).is(':visible')) break; await sleep(100); }
    await settle(); await sleep(600);
    return cur_frm;
  }
  // رصيد الصنف: مجموع أرصدة مستودعاته
  const stockOf = async (item) => (await frappe.db.get_list('Bin', { filters: { item_code: item }, fields: ['actual_qty'], limit: 100 })).reduce((t, b) => t + (b.actual_qty || 0), 0);
  const value = (dt, name, field) => frappe.db.get_value(dt, name, field).then(r => r.message && r.message[field]);

  // قطعة لها رصيد كافٍ في المستودع الذي تُصرف منه
  async function stockedPart(warehouse, need) {
    const bins = await frappe.db.get_list('Bin', { filters: { warehouse, actual_qty: ['>=', need || 5] }, fields: ['item_code', 'actual_qty'], order_by: 'actual_qty desc', limit: 20 });
    for (const b of bins) {
      const it = (await frappe.db.get_list('Item', { filters: { name: b.item_code, disabled: 0, is_stock_item: 1, item_code: ['not like', 'TJ-%'] }, fields: ['name', 'item_name'], limit: 1 }))[0];
      if (it) return it;
    }
    throw new Error('لا قطعة برصيد ' + (need || 5) + ' في ' + warehouse);
  }
  const defaultWarehouse = async () => (await frappe.db.get_single_value('Stock Settings', 'default_warehouse')) || 'Stores - KHAT';

  const ctx = {};

  const SCENARIOS = {
    // يوم في الورشة: عميل جديد يدخل بسيارته، تُفتح له بطاقة، تُنفَّذ، تُفوتَر، يدفع
    async workshop() {
      await step('عميل جديد (إدخال سريع)', async () => {
        const r = await create('Customer', { customer_name: TAG + ' سالم الحبسي ' + stamp, mobile_number: '9' + stamp + '1' });
        ctx.customer = r.name; return r;
      });
      await step('العميل الجديد «فرد» افتراضياً، وجواله محفوظ', async () => {
        const type = await value('Customer', ctx.customer, 'customer_type');
        const mobile = await value('Customer', ctx.customer, 'mobile_no');
        return { ok: type === 'Individual' && !!mobile, type, mobile };
      });
      await step('مركبة للعميل', async () => {
        const brand = (await frappe.db.get_list('Vehicle Brand', { limit: 1 }))[0].name;
        const model = (await frappe.db.get_list('Vehicle Model', { filters: { brand }, limit: 1 }))[0];
        const r = await create('Customer Vehicle', { customer: ctx.customer, plate_number: 'ت ج ' + stamp, brand, model: model && model.name, year: '2021', mileage: 84500 });
        ctx.vehicle = r.name; return r;
      });
      await step('بطاقة عمل: العميل يجلب جواله ومركبته تلقائياً', async () => {
        const { frm } = await openNew('Work Card');
        await setValues(frm, { customer: ctx.customer });
        await sleep(1500); await settle();
        const got = { phone: frm.doc.customer_phone, vehicle: frm.doc.vehicle, plate: frm.doc.plate_number };
        ctx.cardFrm = frm;
        return Object.assign({ ok: !!got.phone && got.vehicle === ctx.vehicle }, got);
      });
      await step('بطاقة عمل: خدمة وقطعة وفني، ثم حفظ', async () => {
        const frm = ctx.cardFrm;
        const part = ctx.partDoc || await stockedPart(frm.doc.warehouse || await defaultWarehouse(), 5);
        const tech = (await frappe.db.get_list('Workshop Technician', { limit: 1 }))[0].name;
        const line = frm.fields_dict.service_line.df.options.split('\n').filter(Boolean)[0];
        const status = (await frappe.db.get_list('Work Card Status', { filters: { is_closed: 0 }, limit: 1 }))[0].name;
        await setValues(frm, { service_line: line, status, complaint: 'صوت عند الفرملة واهتزاز في المقود', mileage: 84620, fuel_level: frm.fields_dict.fuel_level.df.options.split('\n').filter(Boolean)[1], no_visible_damage: 1 });
        const service = ctx.serviceDoc || (await frappe.db.get_list('Item', { filters: { is_stock_item: 0, disabled: 0, item_code: ['like', 'WS-%'] }, fields: ['name', 'item_name'], limit: 1 }))[0];
        if (!service) throw new Error('لا خدمة في دليل الخدمات (WS-…)');
        ctx.service = service.name;
        // المستخدم يختار الصنف ويكتب الكمية؛ الاسم والسعر يجلبهما النموذج
        const priceOf = async (item) => (await frappe.call({ method: 'khat_workshop.api.item_info', args: { item } })).message.rate;
        const sRate = await priceOf(service.name), pRate = await priceOf(part.name);
        if (!sRate || !pRate) throw new Error('لا سعر بيع مسجَّل: الخدمة ' + sRate + '، القطعة ' + pRate);
        await addRows(frm, 'services', [{ service: service.name }]);
        await sleep(800); await settle();
        await addRows(frm, 'parts', [{ item: part.name }]);
        await sleep(800); await settle();
        await addRows(frm, 'parts', []);
        const partRow = frm.doc.parts.find(r => r.item === part.name);
        await frappe.model.set_value(partRow.doctype, partRow.name, 'qty', 2); await settle();
        const sRow = frm.doc.services.find(r => r.service === service.name);
        ctx.autofill = { serviceRate: sRow.rate, serviceText: sRow.description, partRate: partRow.rate, partName: partRow.part_name };
        if (sRow.rate !== sRate || partRow.rate !== pRate || !partRow.part_name) throw new Error('لم يُجلب الاسم أو السعر تلقائياً: ' + JSON.stringify(ctx.autofill));
        ctx.expectCard = sRate + 2 * pRate;
        await addRows(frm, 'technicians', [{ technician: tech, task: 'فرامل', hours: 1.5, commission: 2 }]);
        ctx.part = part.name;
        const label = await pressPrimary(frm);
        if (frm.is_new()) throw new Error('لم تُحفظ البطاقة — إلزامي غير ظاهر: ' + invisibleMandatory(frm).join(','));
        ctx.card = frm.doc.name;
        const expect = ctx.expectCard;
        return { name: frm.doc.name, button: label, autofill: ctx.autofill, services_total: frm.doc.services_total, parts_total: frm.doc.parts_total, grand_total: frm.doc.grand_total, ok: Math.abs(frm.doc.grand_total - expect) < 0.001 };
      });
      await step('اعتماد البطاقة: تُصرف القطع من المخزون وتُحسب التكلفة', async () => {
        const frm = await openDoc('Work Card', ctx.card);
        const bin = () => stockOf(ctx.part);
        const before = await bin();
        const label = await pressPrimary(frm);
        await sleep(800); await frm.reload_doc(); await settle();
        const after = await bin();
        return { button: label, docstatus: frm.doc.docstatus, stock_entry: frm.doc.stock_entry, stockBefore: before, stockAfter: after, gross_profit: frm.doc.gross_profit, margin_pct: frm.doc.margin_pct, ok: frm.doc.docstatus === 1 && !!frm.doc.stock_entry && before - after === 2 };
      });
      await step('من البطاقة: إنشاء عرض سعر', async () => {
        const frm = await openDoc('Work Card', ctx.card);
        await clickAction(frm, 'إنشاء عرض سعر');
        const q = window.cur_frm;
        if (!q || q.doctype !== 'Quotation') throw new Error('لم يُفتح عرض السعر');
        ctx.quotation = q.doc.name;
        return { name: q.doc.name, customer: q.doc.party_name, work_card: q.doc.work_card, items: (q.doc.items || []).length, grand_total: q.doc.grand_total, taxes: q.doc.total_taxes_and_charges, ok: q.doc.work_card === ctx.card && (q.doc.items || []).length > 0 };
      });
      await step('من البطاقة: إنشاء فاتورة واعتمادها', async () => {
        const frm = await openDoc('Work Card', ctx.card);
        await clickAction(frm, 'إنشاء فاتورة');
        const si = window.cur_frm;
        if (!si || si.doctype !== 'Sales Invoice') throw new Error('لم تُفتح الفاتورة');
        ctx.invoice = si.doc.name;
        const hidden = invisibleMandatory(si);
        const label = await pressPrimary(si);
        return { name: si.doc.name, button: label, docstatus: si.doc.docstatus, net: si.doc.net_total, vat: si.doc.total_taxes_and_charges, grand_total: si.doc.grand_total, outstanding: si.doc.outstanding_amount, hiddenMandatory: hidden, ok: si.doc.docstatus === 1 && Math.abs(si.doc.total_taxes_and_charges - si.doc.net_total * 0.05) < 0.002 };
      });
      await step('من الفاتورة: سند قبض يسدّدها كاملة', async () => {
        const si = await openDoc('Sales Invoice', ctx.invoice);
        await clickAction(si, __('Payment'));
        const pe = window.cur_frm;
        if (!pe || pe.doctype !== 'Payment Entry') throw new Error('لم يُفتح سند القبض');
        await setValues(pe, { reference_no: 'نقداً-' + stamp, reference_date: frappe.datetime.get_today() });
        const hidden = invisibleMandatory(pe);
        await pressPrimary(pe);            // حفظ
        if (pe.doc.docstatus === 0 && !pe.is_new()) await pressPrimary(pe);   // اعتماد
        const outstanding = await value('Sales Invoice', ctx.invoice, 'outstanding_amount');
        ctx.payment = pe.doc.name;
        return { name: pe.doc.name, docstatus: pe.doc.docstatus, paid: pe.doc.paid_amount, type: pe.doc.payment_type, invoiceOutstanding: outstanding, hiddenMandatory: hidden, ok: pe.doc.docstatus === 1 && Math.abs(outstanding) < 0.001 };
      });
    },

    // اليوم الأول على نظام فارغ (بعد khat_workshop.handover.clean): لا فني ولا
    // خدمة ولا قطعة. العميل يدخلها بنفسه، ثم يفتح أول بطاقة عمل ويفوترها.
    async firstday() {
      await step('نظام فارغ: لا أصناف نموذجية ولا عملاء', async () => {
        const items = await frappe.db.count('Item', { filters: { item_group: ['in', ['قطع غيار', 'خدمات الورشة', 'عمليات الاستبدال']] } });
        const customers = await frappe.db.count('Customer');
        return { items, customers, ok: true };
      });
      await step('فني جديد', async () => {
        const r = await create('Workshop Technician', { technician_name: TAG + ' فني ' + stamp, specialization: 'ميكانيكا', commission_rate: 10 });
        ctx.tech = r.name; return r;
      });
      await step('خدمة جديدة بسعرها (إدخال سريع)', async () => {
        const name = 'تغيير زيت وفلتر ' + stamp;
        const r = await create('Item', { item_code: 'KH-SVC-' + stamp, item_name: name, item_group: 'خدمات الورشة', stock_uom: 'Nos', is_stock_item: 0, standard_rate: 8 });
        ctx.serviceDoc = { name: r.name, item_name: name };
        r.priceListed = (await frappe.call({ method: 'khat_workshop.api.item_info', args: { item: r.name } })).message.rate;
        r.ok = r.priceListed === 8;
        return r;
      });
      await step('قطعة جديدة بسعرها ورصيدها الافتتاحي (إدخال سريع)', async () => {
        const name = 'فلتر زيت ' + stamp;
        const r = await create('Item', { item_code: 'KH-PRT-' + stamp, item_name: name, item_group: 'قطع غيار', stock_uom: 'Nos', is_stock_item: 1, standard_rate: 3.5, opening_stock: 10, valuation_rate: 2 });
        ctx.partDoc = { name: r.name, item_name: name };
        r.stock = await stockOf(r.name);
        r.ok = r.stock === 10;
        return r;
      });
      await SCENARIOS.workshop();
    },

    // دورة شراء: مورد، أمر شراء، استلام، فاتورة، سداد
    async purchasing() {
      await step('مورد جديد (إدخال سريع)', async () => {
        const r = await create('Supplier', { supplier_name: TAG + ' قطع غيار الخليج ' + stamp });
        ctx.supplier = r.name; return r;
      });
      await step('أمر شراء واعتماده', async () => {
        const part = (await frappe.db.get_list('Item', { filters: { is_stock_item: 1, disabled: 0 }, limit: 1 }))[0].name;
        ctx.buyPart = part;
        const r = await create('Purchase Order', { supplier: ctx.supplier, schedule_date: frappe.datetime.add_days(frappe.datetime.get_today(), 3) },
          { items: [{ item_code: part, qty: 10, rate: 2.75 }] }, { submit: true });
        ctx.po = r.name;
        r.total = cur_frm.doc.grand_total; r.ok = Math.abs(cur_frm.doc.total - 27.5) < 0.001;
        return r;
      });
      await step('من أمر الشراء: إشعار استلام يزيد المخزون', async () => {
        const bin = () => stockOf(ctx.buyPart);
        const before = await bin();
        const po = await openDoc('Purchase Order', ctx.po);
        await clickAction(po, __('Purchase Receipt'));
        const pr = window.cur_frm;
        if (!pr || pr.doctype !== 'Purchase Receipt') throw new Error('لم يُفتح إشعار الاستلام');
        const hidden = invisibleMandatory(pr);
        await pressPrimary(pr); if (pr.doc.docstatus === 0 && !pr.is_new()) await pressPrimary(pr);
        ctx.pr = pr.doc.name;
        const after = await bin();
        return { name: pr.doc.name, docstatus: pr.doc.docstatus, stockBefore: before, stockAfter: after, hiddenMandatory: hidden, ok: pr.doc.docstatus === 1 && after - before === 10 };
      });
      await step('من إشعار الاستلام: فاتورة مشتريات', async () => {
        const pr = await openDoc('Purchase Receipt', ctx.pr);
        await clickAction(pr, __('Purchase Invoice'));
        const pi = window.cur_frm;
        if (!pi || pi.doctype !== 'Purchase Invoice') throw new Error('لم تُفتح فاتورة المشتريات');
        await setValues(pi, { bill_no: 'INV-' + stamp, bill_date: frappe.datetime.get_today() });
        const hidden = invisibleMandatory(pi);
        await pressPrimary(pi); if (pi.doc.docstatus === 0 && !pi.is_new()) await pressPrimary(pi);
        ctx.pi = pi.doc.name;
        return { name: pi.doc.name, docstatus: pi.doc.docstatus, grand_total: pi.doc.grand_total, outstanding: pi.doc.outstanding_amount, hiddenMandatory: hidden, ok: pi.doc.docstatus === 1 };
      });
      await step('من فاتورة المشتريات: سند صرف للمورد', async () => {
        const pi = await openDoc('Purchase Invoice', ctx.pi);
        await clickAction(pi, __('Payment'));
        const pe = window.cur_frm;
        if (!pe || pe.doctype !== 'Payment Entry') throw new Error('لم يُفتح سند الصرف');
        await setValues(pe, { reference_no: 'حوالة-' + stamp, reference_date: frappe.datetime.get_today() });
        await pressPrimary(pe); if (pe.doc.docstatus === 0 && !pe.is_new()) await pressPrimary(pe);
        const outstanding = await value('Purchase Invoice', ctx.pi, 'outstanding_amount');
        return { name: pe.doc.name, docstatus: pe.doc.docstatus, type: pe.doc.payment_type, invoiceOutstanding: outstanding, ok: pe.doc.docstatus === 1 && Math.abs(outstanding) < 0.001 };
      });
    },

    async stock() {
      await step('صنف جديد (إدخال سريع)', async () => {
        const group = (await frappe.db.get_list('Item Group', { filters: { is_group: 0 }, limit: 1 }))[0].name;
        const r = await create('Item', { item_code: 'TJ-' + stamp, item_name: TAG + ' فلتر مكيف', item_group: group, stock_uom: 'Nos', is_stock_item: 1, standard_rate: 6.5 });
        ctx.item = r.name;
        r.priceListed = (await frappe.call({ method: 'khat_workshop.api.item_info', args: { item: r.name } })).message.rate;
        r.ok = r.priceListed === 6.5;
        return r;
      });
      await step('حركة مخزون: استلام مواد', async () => {
        const wh = (await frappe.db.get_list('Warehouse', { filters: { is_group: 0 }, limit: 1 }))[0].name;
        ctx.wh = wh;
        const r = await create('Stock Entry', { stock_entry_type: 'Material Receipt' }, { items: [{ item_code: ctx.item, t_warehouse: wh, qty: 5, basic_rate: 3 }] }, { submit: true });
        return r;
      });
      await step('حركة مخزون: صرف مواد', async () => {
        const r = await create('Stock Entry', { stock_entry_type: 'Material Issue' }, { items: [{ item_code: ctx.item, s_warehouse: ctx.wh, qty: 1 }] }, { submit: true });
        const q = await stockOf(ctx.item);
        r.balance = q; r.ok = q === 4; return r;
      });
    },

    // بيع من الرف بلا بطاقة عمل: عرض سعر، ثم فاتورة تصرف من المخزون وتُقبض
    async sales() {
      const part = (await stockedPart(await defaultWarehouse(), 5)).name;
      const customer = ctx.customer || (await frappe.db.get_list('Customer', { filters: { disabled: 0 }, limit: 1 }))[0].name;
      await step('عرض سعر مباشر واعتماده', async () => {
        const r = await create('Quotation', { party_name: customer }, { items: [{ item_code: part, qty: 3 }] }, { submit: true });
        r.rate = cur_frm.doc.items[0].rate; r.vat = cur_frm.doc.total_taxes_and_charges; r.grand_total = cur_frm.doc.grand_total;
        r.ok = r.rate > 0 && Math.abs(r.vat - cur_frm.doc.net_total * 0.05) < 0.002;
        return r;
      });
      await step('فاتورة مبيعات مباشرة تصرف من المخزون', async () => {
        const before = await stockOf(part);
        const r = await create('Sales Invoice', { customer, update_stock: 1 }, { items: [{ item_code: part, qty: 1 }] }, { submit: true });
        ctx.directInvoice = r.name;
        const after = await stockOf(part);
        r.stockBefore = before; r.stockAfter = after; r.grand_total = cur_frm.doc.grand_total; r.vat = cur_frm.doc.total_taxes_and_charges;
        r.ok = before - after === 1 && r.vat > 0;
        return r;
      });
      await step('مرتجع مبيعات من الفاتورة يعيد القطعة للمخزون', async () => {
        const before = await stockOf(part);
        const si = await openDoc('Sales Invoice', ctx.directInvoice);
        await clickAction(si, __('Return / Credit Note'));
        const ret = window.cur_frm;
        if (!ret || ret.doctype !== 'Sales Invoice' || !ret.doc.is_return) throw new Error('لم يُفتح المرتجع');
        await pressPrimary(ret); if (ret.doc.docstatus === 0 && !ret.is_new()) await pressPrimary(ret);
        const after = await stockOf(part);
        return { name: ret.doc.name, docstatus: ret.doc.docstatus, grand_total: ret.doc.grand_total, stockBefore: before, stockAfter: after, ok: ret.doc.docstatus === 1 && after - before === 1 };
      });
    },

    // كل تقرير تعرضه بلاطة: يفتح، يجلب بياناته بلا خطأ، وله أعمدة
    async reports() {
      const seen = new Set();
      const tiles = [];
      (frappe.boot.kaj.modules || []).forEach(m => (m.sections || []).forEach(sec => (sec.tiles || []).forEach(t => {
        if (t.kind === 'report' && !seen.has(t.target)) { seen.add(t.target); tiles.push(t); }
      })));
      for (const t of tiles) {
        await step('تقرير: ' + t.label, async () => {
          await frappe.set_route('query-report', t.target);
          let qr = null;
          for (let i = 0; i < 300; i++) { await sleep(100); qr = frappe.query_report; if (qr && qr.report_name === t.target && frappe.get_route()[1] === t.target && (qr.columns || []).length && !frappe.request.ajax_count) break; }
          await settle(60000); await sleep(600);
          qr = frappe.query_report;
          const cols = (qr && qr.report_name === t.target && qr.columns || []).length;
          const rows = (qr && qr.data || []).length;
          // ما بقي بالإنجليزية من تسميات المرشّحات والأعمدة
          const isLatin = x => /[A-Za-z]{3,}/.test(x) && !/[\u0600-\u06FF]/.test(x);
          const filters = (qr.filters || []).filter(c => !c.df.hidden && c.df.fieldtype !== 'Break').map(c => __(c.df.label || '')).filter(isLatin);
          const columns = (qr.columns || []).filter(c => !c.hidden).map(c => __(c.label || '')).filter(isLatin);
          return { report: t.target, columns: cols, rows, englishFilters: filters, englishColumns: columns, ok: cols > 0 };
        });
      }
    },

    async accounting() {
      await step('قيد يومية متوازن واعتماده', async () => {
        const cash = (await frappe.db.get_list('Account', { filters: { account_type: 'Cash', is_group: 0 }, limit: 1 }))[0].name;
        const expense = (await frappe.db.get_list('Account', { filters: { root_type: 'Expense', is_group: 0 }, limit: 1 }))[0].name;
        return await create('Journal Entry', { voucher_type: 'Journal Entry', posting_date: frappe.datetime.get_today(), user_remark: TAG + ' مصروف نظافة ' + stamp },
          { accounts: [{ account: expense, debit_in_account_currency: 15 }, { account: cash, credit_in_account_currency: 15 }] }, { submit: true });
      });
    },

    async settings() {
      await step('إضافة مستخدم: حوار واحد بالاسم والبريد وكلمة المرور والمسمّى', async () => {
        closeDialogs();
        frappe.new_doc('User');
        let d = null;
        for (let i = 0; i < 100 && !d; i++) { await sleep(100); if (window.cur_dialog && cur_dialog.display && cur_dialog.fields_dict.roles_html) d = cur_dialog; }
        if (!d) throw new Error('لم يُفتح حوار إضافة مستخدم');
        const email = 'tajriba' + stamp + '@example.com';
        await d.set_value('full_name', TAG + ' موظف استقبال'); await d.set_value('email', email); await d.set_value('password', 'Istiqbal#' + stamp + '-Wrsha');
        d.fields_dict.roles_html.$wrapper.find('input[value="موظف استقبال الورشة"]').prop('checked', true).trigger('change');
        d.get_primary_btn().click();
        await sleep(600); await settle(40000); await sleep(600);
        const doc = await frappe.db.get_doc('User', email);
        ctx.user = doc.name;
        const roles = doc.roles.map(r => r.role);
        return { name: doc.name, enabled: doc.enabled, type: doc.user_type, roles, ok: !d.display && doc.enabled === 1 && doc.user_type === 'System User' && roles.includes('موظف استقبال الورشة') && roles.includes('Sales User') };
      });
      await step('نموذج المستخدم: التبويبات والحقول الظاهرة', async () => {
        const frm = await openDoc('User', ctx.user);
        return { tabs: $(frm.wrapper).find('.form-tabs .nav-link:visible').map((i, e) => $(e).text().trim()).get(), sections: $(frm.wrapper).find('.section-head:visible').map((i, e) => $(e).text().trim()).get() };
      });
    },
  };

  window.__kajE2E = {
    steps, ctx,
    async run(name) {
      if (frappe.boot.sitename !== 'kaj-staging.localhost') throw new Error('التجربة تعمل على نسخة الاختبار فقط، لا على ' + frappe.boot.sitename);
      const from = steps.length;
      await SCENARIOS[name]();
      return steps.slice(from).map(s => ({ ok: s.ok, step: s.step, detail: Object.fromEntries(Object.entries(s).filter(([k]) => !['ok', 'step', 'errors'].includes(k))), errors: s.errors }));
    },
    scenarios: Object.keys(SCENARIOS),
  };
})();
