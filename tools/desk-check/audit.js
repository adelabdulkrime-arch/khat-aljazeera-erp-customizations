// جرد واجهة النظام — يُحمَّل في المعاينة المحلية (serve.js) بعد الدخول:
//
//   const s = document.createElement('script'); s.src = '/__kaj/audit.js'; document.head.append(s);
//   await __kajAudit.list('Customer');      // شاشة قائمة
//   await __kajAudit.form('Customer');      // نموذج جديد (لا يُحفظ)
//   await __kajAudit.report('Stock Balance');
//   await __kajAudit.route(['Workspaces', 'Home']);
//   await __kajAudit.crawl();               // كل شاشة تفتحها بلاطة، وخلاصة ما وُجد
//
// كل دالة تفتح الشاشة، تنتظر حتى تهدأ الطلبات، وتعيد ما يراه المستخدم فعلاً:
// العنوان، الأزرار، رؤوس الأعمدة، عناصر الشريط الجانبي، كل نص ظاهر مع منطقته،
// وكل خطأ ظهر أثناء الفتح (رسالة حمراء، طلب فاشل، استثناء جافاسكربت).
// لا تحفظ شيئاً ولا تعدّل بيانات.
(function () {
  const sleep = ms => new Promise(r => setTimeout(r, ms));
  const errors = [];
  const note = (kind, msg) => errors.push({kind, msg: String(msg).slice(0, 300), route: location.pathname});

  if (!window.__kajAuditHooked) {
    window.__kajAuditHooked = true;
    window.addEventListener('error', e => { if (!/ResizeObserver loop/.test(e.message || '')) note('js', e.message + ' @ ' + (e.filename || '').split('/').pop() + ':' + e.lineno); });
    window.addEventListener('unhandledrejection', e => note('promise', (e.reason && (e.reason.message || e.reason.exc_type || JSON.stringify(e.reason))) || 'rejection'));
    const ce = console.error.bind(console);
    console.error = function () { note('console', [].map.call(arguments, a => (a && a.message) || (typeof a === 'string' ? a : JSON.stringify(a))).join(' ')); ce.apply(null, arguments); };
    $(document).ajaxError((ev, xhr, opts) => { if (!/socket\.io/.test(opts.url) && !(xhr.status === 0 && xhr.statusText === 'abort')) note('http ' + xhr.status, opts.url + ' ' + ((opts.data && String(opts.data).slice(0, 120)) || '')); });
    const mp = frappe.msgprint;
    frappe.msgprint = function (m) { const o = (m && typeof m === 'object') ? m : {message: m}; if (/red|orange/.test(o.indicator || '') || o.title === __('Error') || /Error|خطأ/.test(o.title || '')) note('msgprint', (o.title || '') + ': ' + $('<div>').html(o.message || '').text()); return mp.apply(this, arguments); };
  }

  // تهدأ الشاشة حين لا طلبات جارية ولا هياكل تحميل ظاهرة، لنصف ثانية متصلة
  async function settle(timeout = 30000) {
    const t0 = performance.now();
    let quiet = 0;
    while (performance.now() - t0 < timeout) {
      const busy = (frappe.request && frappe.request.ajax_count > 0) || $('.list-skeleton:visible, .freeze:visible, #freeze:visible').length > 0 || !frappe.boot;
      quiet = busy ? 0 : quiet + 1;
      if (quiet >= 5) return Math.round(performance.now() - t0);
      await sleep(100);
    }
    note('timeout', 'الشاشة لم تهدأ خلال ' + timeout + 'ms');
    return -1;
  }

  const visible = el => { if (!el || !el.getClientRects().length) return false; const cs = getComputedStyle(el); return cs.visibility !== 'hidden' && cs.display !== 'none' && +cs.opacity !== 0; };
  const REGIONS = [['.modal.show, .modal.in', 'modal'], ['.body-sidebar, .layout-side-section, .desk-sidebar, .sidebar-container', 'sidebar'], ['.page-head', 'head'],
    ['.page-form, .filter-section, .standard-filter-section', 'filters'], ['.list-row-head', 'list-head'], ['.list-row-container', 'list-row'], ['.list-paging-area', 'paging'],
    ['.form-layout, .form-page', 'form'], ['.report-wrapper, .datatable', 'report'], ['.dropdown-menu', 'menu'], ['.layout-main-section', 'main']];
  const regionOf = el => { for (const [sel, name] of REGIONS) if (el.closest(sel)) return name; return 'other'; };

  // كل نص يراه المستخدم: نصوص العناصر، والنصوص الإرشادية، والتلميحات
  function texts(root) {
    root = root || document.body;
    const out = new Map();
    const add = (el, t, how) => { t = (t || '').replace(/\s+/g, ' ').trim(); if (!t || t.length > 140) return; const k = regionOf(el) + '|' + how + '|' + t; if (!out.has(k)) out.set(k, {r: regionOf(el), how, t}); };
    const walk = node => {
      const w = document.createTreeWalker(node, NodeFilter.SHOW_TEXT);
      for (let n = w.nextNode(); n; n = w.nextNode()) { const p = n.parentElement; if (!p || /^(SCRIPT|STYLE|NOSCRIPT|OPTION)$/.test(p.tagName) || !n.nodeValue.trim()) continue; if (visible(p)) add(p, n.nodeValue, 'text'); }
      node.querySelectorAll('[placeholder],[title],[aria-label],[data-original-title]').forEach(el => { if (!visible(el)) return; ['placeholder', 'title', 'aria-label', 'data-original-title'].forEach(a => { const v = el.getAttribute(a); if (v) add(el, v, a === 'placeholder' ? 'placeholder' : 'tip'); }); });
      node.querySelectorAll('*').forEach(el => { if (el.shadowRoot) walk(el.shadowRoot); });
    };
    walk(root);
    return [...out.values()];
  }

  const common = () => ({
    path: decodeURIComponent(location.pathname), title: document.title,
    pageTitle: ($('.page-head:visible .title-text, .page-head:visible .page-title .ellipsis').first().text() || '').trim(),
    breadcrumbs: $('#navbar-breadcrumbs:visible li, .navbar-breadcrumbs:visible li, .page-head:visible .breadcrumb li').map((i, e) => $(e).text().trim()).get().filter(Boolean),
    sidebarTitle: ($('.body-sidebar .header-title, .sidebar-header .header-title').first().text() || '').trim(),
    sidebar: $('.body-sidebar .sidebar-item-label:visible, .body-sidebar .item-anchor:visible').map((i, e) => $(e).text().trim()).get().filter(Boolean),
    overflowX: document.documentElement.scrollWidth > innerWidth + 1,
  });
  const take = () => { const e = errors.splice(0); return e; };

  async function list(doctype) {
    take();
    const t0 = performance.now();
    await frappe.set_route('List', doctype, 'List');
    const ms = await settle();
    await sleep(400);
    const lv = window.cur_list && cur_list.doctype === doctype ? cur_list : null;
    const $p = lv ? lv.page.wrapper : $('.page-container:visible');
    return Object.assign(common(), {
      kind: 'list', doctype, ok: !!lv, ms: Math.round(performance.now() - t0), settle: ms,
      primary: ($p.find('.primary-action:visible').text() || '').trim(),
      toolbar: $p.find('.page-actions:visible').find('button:visible, a.btn:visible').map((i, e) => ($(e).text().trim() || $(e).attr('title') || $(e).attr('aria-label') || '[أيقونة ' + ($(e).find('use').attr('href') || '?') + ']')).get(),
      filters: $p.find('.page-form:visible input:visible, .page-form:visible select:visible').map((i, e) => $(e).attr('placeholder') || $(e).attr('data-fieldname') || '').get(),
      filterButton: ($p.find('.filter-selector:visible .filter-button').text() || '').trim(),
      sort: ($p.find('.sort-selector:visible').text() || '').replace(/\s+/g, ' ').trim(),
      headers: $p.find('.list-row-head:visible .list-row-col:visible').map((i, e) => $(e).text().trim()).get(),
      headRight: ($p.find('.list-row-head:visible .level-right').text() || '').replace(/\s+/g, ' ').trim(),
      rows: lv ? lv.data.length : 0,
      firstRow: $p.find('.list-row-container:visible .list-row').eq(0).find('.list-row-col:visible').map((i, e) => $(e).text().replace(/\s+/g, ' ').trim()).get(),
      empty: ($p.find('.no-result:visible').text() || '').replace(/\s+/g, ' ').trim(),
      columns: lv ? lv.columns.map(c => c.type === 'Field' || c.type === 'Subject' ? (c.df && c.df.fieldname) : c.type) : [],
      // هندسة الجدول: تمرير أفقي، أعمدة لا تصطفّ بين الصفوف، وعمود الإجراءات
      geometry: (() => {
        const res = $p.find('.result')[0];
        if (!res) return null;
        const lines = $p.find('.list-row-head, .list-row-container .list-row').slice(0, 7).map((i, row) =>
          [$(row).find('.list-row-col:visible').map((j, c) => Math.round(c.getBoundingClientRect().right)).get()]).get();
        const cols = lines.length ? lines[0].length : 0;
        const misaligned = [];
        for (let c = 0; c < cols; c++) { const xs = lines.map(l => l[c]).filter(x => x != null); if (Math.max(...xs) - Math.min(...xs) > 2) misaligned.push(c); }
        return {overflowX: res.scrollWidth > res.clientWidth + 1 ? res.scrollWidth - res.clientWidth : 0, misaligned,
          unevenCols: lines.some(l => l.length !== cols), actions: $p.find('.list-row-container .kaj-row-actions').length, likes: $p.find('.list-row-container .like-action:visible, .list-row-container .comment-count:visible').length};
      })(),
      texts: texts($('.page-container:visible')[0]).concat(texts($('.body-sidebar')[0])), errors: take(),
    });
  }

  async function form(doctype) {
    take();
    const t0 = performance.now();
    await frappe.model.with_doctype(doctype);
    const meta = frappe.get_meta(doctype);
    if (meta.issingle) await frappe.set_route('Form', doctype, doctype); else frappe.new_doc(doctype);
    const ms = await settle();
    await sleep(700);
    const $m = $('.modal.show:visible, .modal.in:visible').last();
    const quick = $m.length > 0;
    const frm = !quick && window.cur_frm && cur_frm.doctype === doctype ? cur_frm : null;
    const $s = quick ? $m : (frm ? $(frm.wrapper) : $('.page-container:visible'));
    const res = Object.assign(common(), {
      kind: 'form', doctype, ok: quick || !!frm, quick, single: !!meta.issingle, ms: Math.round(performance.now() - t0), settle: ms,
      heading: quick ? ($m.find('.modal-title').text() || '').trim() : ($s.find('.title-text:visible').first().text() || '').trim(),
      indicator: ($s.find('.indicator-pill:visible').first().text() || '').trim(),
      buttons: $s.find('.page-actions:visible, .modal-footer:visible, .modal-header:visible').find('button:visible').map((i, e) => ($(e).text().trim() || $(e).attr('title') || $(e).attr('aria-label') || '[أيقونة]')).get(),
      tabs: $s.find('.form-tabs:visible .nav-link:visible').map((i, e) => $(e).text().trim()).get(),
      sections: $s.find('.section-head:visible').map((i, e) => $(e).text().trim()).get().filter(Boolean),
      visibleFields: $s.find('.frappe-control:visible').filter((i, e) => !$(e).closest('.grid-row, .hide-control').length).map((i, e) => { const lab = ($(e).find('.control-label, .label-area').first().text() || '').trim(); const req = $(e).find('.reqd, .control-label.reqd').length || $(e).hasClass('has-error') ? '*' : ''; return (lab || '[' + ($(e).attr('data-fieldname') || '') + ']') + req; }).get(),
      texts: texts($s[0]), errors: take(),
    });
    // لا يُحفظ شيء: يُغلق الحوار، والنموذج الجديد يُهمَل من الذاكرة
    if (quick) $m.modal('hide');
    else if (frm && frm.is_new()) { try { frappe.model.clear_doc(frm.doctype, frm.docname); } catch (e) { /* مسودة محلية فقط */ } }
    await sleep(300);
    return res;
  }

  async function route(parts, kind) {
    take();
    const t0 = performance.now();
    await frappe.set_route(parts);
    const ms = await settle(45000);
    await sleep(900);
    return Object.assign(common(), {kind: kind || 'page', route: parts.join('/'), ms: Math.round(performance.now() - t0), settle: ms,
      toolbar: $('.page-container:visible .page-actions:visible').find('button:visible, a.btn:visible').map((i, e) => ($(e).text().trim() || $(e).attr('title') || '[أيقونة]')).get(),
      filters: $('.page-container:visible .page-form:visible .frappe-control:visible').map((i, e) => $(e).find('input, select').attr('placeholder') || $(e).attr('data-fieldname') || '').get(),
      headers: $('.page-container:visible .dt-header .dt-cell__content:visible').map((i, e) => $(e).text().trim()).get().filter(Boolean),
      texts: texts($('.page-container:visible')[0]), errors: take()});
  }
  const report = name => route(['query-report', name], 'report');

  // ── الزحف: كل ما تفتحه اللوحات، بحساب المستخدم الحالي ──
  // نصّ لاتيني في واجهة عربية: تسمية لم تُترجم. تُستثنى البيانات (صفوف القوائم
  // وجسم التقارير) والرموز: أرقام المستندات، البريد، الاختصارات.
  const CODE = /^[A-Z0-9][A-Z0-9 ._#\/+-]*$|@|^Ctrl|^\W*$|^https?:|KHAT|^[A-Za-z]{1,2}$|OMR|^Administrator$|^Nos$/;
  const latin = t => /[A-Za-z]{3,}/.test(t) && !/[\u0600-\u06FF]/.test(t) && !CODE.test(t);
  const CHROME_REGIONS = ['head', 'filters', 'list-head', 'form', 'menu', 'modal', 'paging', 'main', 'sidebar'];

  function digest(res) {
    const out = { ok: res.ok !== false, ms: res.ms };
    if (res.errors && res.errors.length) out.errors = res.errors.map(e => e.kind + ': ' + e.msg).slice(0, 4);
    const eng = (res.texts || []).filter(x => CHROME_REGIONS.includes(x.r) && latin(x.t)).map(x => x.t);
    if (eng.length) out.english = [...new Set(eng)].slice(0, 12);
    if (res.overflowX) out.pageOverflowX = true;
    if (res.geometry) {
      const g = res.geometry;
      if (g.overflowX || g.misaligned.length || g.unevenCols || g.likes || (res.rows && !g.actions)) out.geometry = g;
    }
    if (res.kind === 'list') { out.headers = res.headers.join(' | '); out.primary = res.primary; out.rows = res.rows; }
    if (res.kind === 'form') { out.fields = res.visibleFields.length; out.tabs = res.tabs.length; out.quick = res.quick; }
    if (res.kind === 'report') out.columns = res.headers.length;
    return out;
  }

  async function crawl() {
    const kaj = frappe.boot.kaj;
    const allowed = (t) => !(window.kaj && window.kaj.dashboard && window.kaj.dashboard.allowed) || window.kaj.dashboard.allowed(t);
    const screens = [], seen = new Set();
    const push = (id, run) => { if (!seen.has(id)) { seen.add(id); screens.push({ id, run }); } };
    (kaj.modules || []).forEach(m => {
      push('لوحة ' + m.title, () => route(['Workspaces', m.workspace], 'workspace'));
      const tiles = (m.quick || []).concat(...(m.sections || []).map(sec => sec.tiles || []));
      tiles.filter(allowed).forEach(t => {
        if (t.kind === 'list') { push('قائمة ' + t.target, () => list(t.target)); push('نموذج ' + t.target, () => form(t.target)); }
        else if (t.kind === 'new' || t.kind === 'form') push('نموذج ' + t.target, () => form(t.target));
        else if (t.kind === 'report') push('تقرير ' + t.target, () => report(t.target));
        else if (t.kind === 'tree') push('شجرة ' + t.target, () => route(['Tree', t.target], 'tree'));
        else if (t.kind === 'page') push('صفحة ' + t.target, () => route([t.target], 'page'));
      });
    });
    const results = {};
    window.__kajCrawl = { total: screens.length, done: 0, results };
    for (const sc of screens) {
      try { results[sc.id] = digest(await sc.run()); }
      catch (e) { results[sc.id] = { ok: false, exception: String(e && e.message || e) }; }
      $('.modal.show').modal('hide');
      window.__kajCrawl.done++;
    }
    window.__kajCrawl.finished = true;
    return results;
  }

  // ما يستحق النظر من نتيجة الزحف: أخطاء، شاشات لم تُفتح، خلل هندسي، نصوص لم تُترجم
  function problems(results) {
    const out = {}, english = {};
    for (const [id, r] of Object.entries(results || {})) {
      const p = {};
      if (!r.ok) p.notOpened = r.exception || true;
      if (r.errors) p.errors = r.errors;
      if (r.geometry) p.geometry = r.geometry;
      if (r.pageOverflowX) p.pageOverflowX = true;
      if (Object.keys(p).length) out[id] = p;
      (r.english || []).forEach(t => { (english[t] = english[t] || []).push(id); });
    }
    return { screens: Object.keys(results || {}).length, problems: out,
      english: Object.entries(english).sort((a, b) => b[1].length - a[1].length).map(([t, ids]) => t + '  ×' + ids.length + '  ' + ids.slice(0, 2).join('، ')) };
  }

  window.__kajAudit = {list, form, route, report, settle, texts, errors, crawl, problems};
})();
