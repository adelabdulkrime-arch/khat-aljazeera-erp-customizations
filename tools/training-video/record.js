// يسجّل الفيديو التعليمي: جولة حقيقية على النظام بمتصفح يُقاد آلياً.
//
//   node record.js <out-dir> [--dry] [--until=<scene>]
//
// يعمل على نسخة الاختبار عبر المعاينة المحلية (tools/desk-check)، لا على الموقع
// الفعلي: الجولة تُنشئ فنياً وأصنافاً وعميلاً وبطاقة وفاتورة. تُسجَّل على نسخة
// مستعادة من نظام نظيف، فما يظهر في الفيديو هو ما يراه العميل في يومه الأول.
//
// كل مشهد من narration.js: يُعرض نصّه أسفل الشاشة، تُنفَّذ خطواته بفأرة ولوحة
// مفاتيح حقيقيتين (المؤشّر المرسوم يتبع الفأرة)، ويمتدّ المشهد حتى ينتهي تعليقه
// الصوتي. يخرج: video/*.webm، timeline.json (بداية كل مشهد)، shots/*.png.
const fs = require('fs');
const path = require('path');
const { chromium } = require('playwright');
const PART = process.env.KAJ_PART === '2' ? '2' : '1';        // الجزء الثاني يبدأ من بيانات الأول
const scenes = require(PART === '2' ? './narration2' : './narration');
const sync = require('./sync');

const OUT = path.resolve(process.argv[2] || 'out');
const DRY = process.argv.includes('--dry');
const UNTIL = (process.argv.find((a) => a.startsWith('--until=')) || '').split('=')[1];
// ‎--from=<مشهد>‎: للتجربة — يُنفَّذ المشهد الأول (يجهّز الصفحة) ثم يُقفز إلى هذا المشهد
const FROM = (process.argv.find((a) => a.startsWith('--from=')) || '').split('=')[1];
const BASE = process.env.KAJ_BASE || 'http://127.0.0.1:8766';
const USER = process.env.KAJ_USER || 'Admin';
const PASS = process.env.KAJ_PASS || 'admin123';
const SFX = process.env.KAJ_SUFFIX || '';          // للتجارب المتكررة على البيانات نفسها
// الصفحة 1280×660؛ الشريط السفلي (60) يضيفه build.js وفيه نصّ المشهد، فلا يغطّي
// النصّ أزرار الحوارات كما كان يفعل وهو مرسوم فوق الصفحة.
const SIZE = { width: 1280, height: 660 };

// بيانات الجولة
const D = {
  workshop: 'خط الجزيرة لصيانة السيارات', phone: '+968 9123 4567', tax: 'OM1100123456',
  address: 'مسقط، الوادي الكبير، المنطقة الصناعية',
  tech: 'سعيد بن حمد الهنائي' + SFX,
  svcCode: 'SRV-OIL' + SFX, svcName: 'تغيير زيت المحرك', svcRate: '5',
  partCode: 'FLT-OIL' + SFX, partName: 'فلتر زيت', partRate: '3.5', partQty: '20', partCost: '2',
  customer: 'أحمد بن سالم البلوشي' + SFX, mobile: '92345678',
  plate: '45213 ب د' + SFX, year: '2021', mileage: '84500',
  complaint: 'صوت عند تشغيل المحرك، والمطلوب تغيير الزيت والفلتر',
  user: 'خالد بن ناصر الرواحي', email: 'khalid' + SFX.replace(/\W/g, '') + '@khataljazeera.om', password: 'Warsha#2026-Kh',
  role: 'موظف استقبال الورشة',
  // الجزء الثاني
  supplier: 'مؤسسة الخليج لقطع الغيار' + SFX, supplierMobile: '24567890', billNo: 'INV-7781',
  expenseAccount: 'مطبوعات وقرطاسية', bankAccount: 'الحساب البنكي', expenseAmount: '1.5',
};

// ── ما يُرسم فوق الصفحة: المؤشّر، النصّ السفلي، بطاقات العناوين ──
const OVERLAY = `(() => {
  if (window.__kv) return;
  const css = \`
    #kv-cursor{position:fixed;left:0;top:0;width:26px;height:26px;margin:-3px 0 0 -3px;z-index:2147483647;pointer-events:none;
      transition:transform .05s linear;will-change:transform}
    #kv-cursor svg{display:block;filter:drop-shadow(0 1px 2px rgba(0,0,0,.45))}
    #kv-cursor.down::after{content:"";position:absolute;left:-12px;top:-12px;width:34px;height:34px;border-radius:50%;
      border:3px solid #f4a900;animation:kvp .45s ease-out forwards}
    @keyframes kvp{from{transform:scale(.4);opacity:1}to{transform:scale(1.5);opacity:0}}
    #kv-caption{position:fixed;left:50%;bottom:22px;transform:translateX(-50%);max-width:86%;z-index:2147483646;pointer-events:none;
      padding:11px 26px;border-radius:12px;background:rgba(18,28,48,.94);color:#fff;font:600 21px/1.5 "Segoe UI",Tahoma,sans-serif;
      direction:rtl;text-align:center;box-shadow:0 8px 28px rgba(0,0,0,.28);border-bottom:3px solid #f4a900;opacity:0;transition:opacity .3s}
    #kv-caption.on{opacity:1}
    #kv-card{position:fixed;inset:0;z-index:2147483645;pointer-events:none;display:flex;flex-direction:column;align-items:center;justify-content:center;
      background:linear-gradient(135deg,#131d33,#1a2b4a 55%,#2b1f33);color:#fff;direction:rtl;text-align:center;opacity:0;transition:opacity .45s}
    #kv-card.on{opacity:1}
    #kv-card b{font:700 60px/1.3 "Segoe UI",Tahoma,sans-serif}
    #kv-card i{display:block;width:90px;height:4px;margin:22px 0;background:#f4a900;border-radius:2px}
    #kv-card span{font:400 28px/1.5 "Segoe UI",Tahoma,sans-serif;color:#d5dbe6}
    #kv-sync{position:fixed;left:0;bottom:0;width:__SW__px;height:__SH__px;z-index:2147483647;pointer-events:none}
  \`;
  const build = () => {
    if (document.getElementById('kv-cursor') || !document.body) return;
    const st = document.createElement('style'); st.textContent = css; document.documentElement.appendChild(st);
    const cur = document.createElement('div'); cur.id = 'kv-cursor';
    cur.innerHTML = '<svg width="26" height="26" viewBox="0 0 24 24"><path d="M4 2l15 9.2-6.6 1.5 4 7.6-2.7 1.4-4-7.6L5 19z" fill="#fff" stroke="#111" stroke-width="1.3" stroke-linejoin="round"/></svg>';
    const cap = document.createElement('div'); cap.id = 'kv-caption';
    const card = document.createElement('div'); card.id = 'kv-card'; card.innerHTML = '<b></b><i></i><span></span>';
    const mark = document.createElement('div'); mark.id = 'kv-sync'; mark.style.background = sessionStorage.getItem('kv-sync') || 'transparent';
    document.body.append(card, cap, cur, mark);
    const pos = JSON.parse(sessionStorage.getItem('kv-pos') || '[640,360]');
    cur.style.transform = 'translate(' + pos[0] + 'px,' + pos[1] + 'px)';
    const saved = sessionStorage.getItem('kv-caption'); if (saved) { cap.textContent = saved; cap.classList.add('on'); }
  };
  document.addEventListener('DOMContentLoaded', build); build();
  // فيديو عربي لا يُترك فيه سطر إنجليزي: كل نصّ ظاهر فيه كلمتان لاتينيتان
  // متتاليتان يُجمع (رسالة عابرة، وصف حقل في حوار…) ويُكتب في english.json.
  const EN = /[A-Za-z]{3,}[\\s,.:–-]+[A-Za-z]{3,}/;
  setInterval(() => {
    if (!document.body) return;
    const seen = new Set(JSON.parse(sessionStorage.getItem('kv-en') || '[]'));
    const before = seen.size, walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
    for (let node; (node = walker.nextNode());) {
      const t = node.nodeValue.trim();
      if (t.length < 8 || t.length > 400 || /[@{}=;]|https?:/.test(t) || !EN.test(t)) continue;
      const el = node.parentElement;
      if (!el || el.closest('script,style,noscript,[id^="kv-"]')) continue;
      const r = el.getBoundingClientRect();
      if (!r.width || !r.height || r.bottom < 0 || r.top > innerHeight || getComputedStyle(el).visibility === 'hidden') continue;
      seen.add(t.slice(0, 160));
    }
    if (seen.size !== before) sessionStorage.setItem('kv-en', JSON.stringify([...seen]));
  }, 600);
  addEventListener('mousemove', (e) => { const c = document.getElementById('kv-cursor'); if (c) c.style.transform = 'translate(' + e.clientX + 'px,' + e.clientY + 'px)'; sessionStorage.setItem('kv-pos', JSON.stringify([e.clientX, e.clientY])); }, true);
  addEventListener('mousedown', () => { const c = document.getElementById('kv-cursor'); if (!c) return; c.classList.remove('down'); void c.offsetWidth; c.classList.add('down'); }, true);
  window.__kv = {
    caption(t) { build(); const c = document.getElementById('kv-caption'); if (!c) return; if (t) { c.textContent = t; c.classList.add('on'); sessionStorage.setItem('kv-caption', t); } else { c.classList.remove('on'); sessionStorage.removeItem('kv-caption'); } },
    sync(c) { build(); sessionStorage.setItem('kv-sync', c); const m = document.getElementById('kv-sync'); if (m) m.style.background = c; },
    card(a, b) { build(); const c = document.getElementById('kv-card'); if (!c) return; if (a) { c.querySelector('b').textContent = a; c.querySelector('span').textContent = b || ''; c.classList.add('on'); } else c.classList.remove('on'); },
  };
})();`.replace('__SW__', sync.SIZE.w).replace('__SH__', sync.SIZE.h);

(async () => {
  fs.mkdirSync(path.join(OUT, 'video'), { recursive: true });
  fs.mkdirSync(path.join(OUT, 'shots'), { recursive: true });
  const durations = fs.existsSync(path.join(OUT, 'durations.json')) ? JSON.parse(fs.readFileSync(path.join(OUT, 'durations.json'), 'utf8')) : {};

  // متصفح سبق أن فتح النظام، كمتصفح أي موظف بعد يومه الأول: ملفات الواجهة
  // وقاموس الترجمة في مخزنه. بمتصفح جديد يصوّر الفيديو أول تحميل على الإطلاق —
  // أبطأ ما يراه المستخدم، مرة واحدة — وكأنه الدخول المعتاد. جلسة تمهيد غير
  // مسجَّلة تملأ المخزن، ثم يبدأ التسجيل بالملف الشخصي نفسه.
  const profile = path.join(OUT, 'profile');
  fs.rmSync(profile, { recursive: true, force: true });
  const warm = await chromium.launchPersistentContext(profile, { headless: true, viewport: SIZE, locale: 'ar' });
  try {
    const w = warm.pages()[0] || await warm.newPage();
    await w.goto(BASE + '/login', { waitUntil: 'domcontentloaded' });
    await w.fill('#login_email', USER); await w.fill('#login_password', PASS);
    await w.click('.for-login .btn-login');
    await w.waitForURL(/\/desk/, { timeout: 120000 });
    await w.waitForFunction(() => window.frappe && frappe.boot && document.querySelector('.body-sidebar') && !document.querySelector('.splash'), null, { timeout: 120000 });
    await w.waitForTimeout(4000);
    // الجزء الثاني يبدأ والمستخدم داخل النظام: الجلسة تبقى في الملف الشخصي
    if (PART === '1') await w.evaluate(() => fetch('/api/method/logout', { method: 'POST', headers: { 'X-Frappe-CSRF-Token': frappe.csrf_token } }));
    await w.waitForTimeout(500);
    console.log('warm-up done');
  } finally { await warm.close(); }

  const context = await chromium.launchPersistentContext(profile, { headless: true, viewport: SIZE, locale: 'ar', recordVideo: { dir: path.join(OUT, 'video'), size: SIZE } });
  await context.addInitScript(OVERLAY);
  const page = context.pages()[0] || await context.newPage();
  const t0 = Date.now();
  page.setDefaultTimeout(45000);
  const log = (...a) => console.log(((Date.now() - t0) / 1000).toFixed(1).padStart(6), ...a);
  page.on('pageerror', (e) => log('PAGEERROR', String(e.message).slice(0, 160)));

  // ── أدوات ──
  const wait = (ms) => page.waitForTimeout(ms);
  const js = (fn, arg) => page.evaluate(fn, arg);
  async function idle(extra = 500) {
    await page.waitForFunction(() => !window.frappe || !frappe.request || frappe.request.ajax_count === 0, null, { timeout: 60000 }).catch(() => log('idle timeout'));
    await wait(extra);
  }
  async function glide(loc) {
    await loc.scrollIntoViewIfNeeded().catch(() => {});
    await wait(150);
    const b = await loc.boundingBox();
    if (!b) throw new Error('عنصر بلا موضع');
    const x = b.x + Math.min(b.width / 2, b.width - 6), y = b.y + b.height / 2;
    await page.mouse.move(x, y, { steps: 26 });
    await wait(220);
    return { x, y };
  }
  async function click(loc, after = 400) { await glide(loc); await page.mouse.down(); await wait(60); await page.mouse.up(); await wait(after); }
  async function type(loc, text, opts = {}) {
    await click(loc, 200);
    // الكتابة تذهب حيث التركيز؛ إن لم يأخذه الحقل ذهبت الحروف إلى اختصارات
    // النظام (بحث، تنقّل) وفتحت شاشة أخرى
    await loc.focus().catch(() => {});
    if (opts.clear) { await page.keyboard.press('Control+A'); await page.keyboard.press('Delete'); }
    await page.keyboard.type(String(text), { delay: opts.delay || 45 });
    await wait(250);
  }
  const caption = async () => {};            // النصّ السفلي يُركَّب في build.js
  const card = (a, b) => js(([x, y]) => window.__kv && window.__kv.card(x, y), [a || '', b || '']);

  const inForm = (field) => page.locator(`.page-container:visible .form-layout .frappe-control[data-fieldname="${field}"] :is(input:not([type=hidden]), textarea, select):visible`).first();
  const inDialog = (field) => page.locator(`.modal.show .frappe-control[data-fieldname="${field}"] :is(input:not([type=hidden]), textarea, select):visible`).first();
  const primary = () => page.locator('.page-container:visible .page-actions .primary-action:visible').first();
  const sidebar = (label) => page.locator('.body-sidebar a.item-anchor:visible').filter({ hasText: label }).first();
  const tile = (label) => page.locator('.kd a, .kd button').filter({ hasText: label }).first();
  const frmDoc = (field) => js((f) => window.cur_frm && cur_frm.doc && cur_frm.doc[f], field);

  // حقل اختيار: تُكتب بدايته ويُختار من القائمة المنسدلة، كما يفعل المستخدم
  async function pick(loc, text, optionText) {
    const option = page.locator('.awesomplete > ul:visible > [role="option"]').filter({ hasText: optionText || text }).first();
    for (let attempt = 1; attempt <= 2; attempt++) {
      await click(loc, 200);
      await loc.focus().catch(() => {});
      // النقر يفتح القائمة كاملة (بحث بلا نصّ). تُنتظر نتيجته قبل الكتابة: إن
      // وصلت بعد نتيجة النصّ المكتوب بقيت القائمة كاملة ولم يظهر المطلوب.
      await wait(700);
      await idle(300);
      await page.keyboard.press('Control+A'); await page.keyboard.press('Delete');
      await page.keyboard.type(String(text), { delay: 70 });
      try {
        await option.waitFor({ state: 'visible', timeout: 8000 });
        await wait(350);
        await click(option, 300);
        await idle(400);
        return;
      } catch (e) { log('  لا قائمة لـ', text, '— محاولة', attempt); }
    }
    // قائمة بقيت مفتوحة تغطّي الحقل الذي تحتها فتأخذ نقرته: «شيفروليه» اختيرت
    // هكذا بنقرةٍ قُصد بها حقل الموديل.
    await js(() => {
      if (document.activeElement && document.activeElement.blur) document.activeElement.blur();
      document.querySelectorAll('.awesomplete > ul').forEach((u) => { u.hidden = true; });
    });
    await idle(400);
  }
  async function goSection(label) {
    await click(sidebar(label), 300);
    await idle(900);
    await page.locator('.kd').first().waitFor({ timeout: 30000 }).catch(() => {});
    await wait(700);
  }
  async function save(expectSubmit) {
    await click(primary(), 500);
    if (expectSubmit) {
      const yes = page.locator('.modal.show .modal-footer .btn-primary:visible').first();
      await yes.waitFor({ state: 'visible', timeout: 15000 });
      await wait(500);
      await click(yes, 400);
    }
    await idle(900);
  }
  // بند من قائمة منسدلة في رأس المستند («إنشاء» ← «إنشاء فاتورة»). رأس المستند
  // يُعاد رسمه بعد الحفظ والاعتماد، فقائمة فُتحت قبل اكتمال الرسم تختفي: يُعاد الضغط.
  async function menuItem(group, item) {
    await idle(900);
    const button = () => page.locator('.page-container:visible .inner-group-button > button:visible').filter({ hasText: group }).first();
    const entry = page.locator('.page-container:visible .inner-group-button .dropdown-item:visible').filter({ hasText: item }).first();
    for (let attempt = 0; attempt < 4; attempt++) {
      await click(button(), 500);
      if (await entry.isVisible().catch(() => false)) break;
      await wait(1200);
      if (await entry.isVisible().catch(() => false)) break;
    }
    await click(entry, 600);
  }
  async function closeAlerts() { await js(() => { document.querySelectorAll('.desk-alert .close, #alert-container .close').forEach((b) => b.click()); }); }
  // صف جديد في جدول: يُضغط «إضافة صف» ثم تُملأ خلاياه
  async function gridRow(table, cells, reuse) {
    const grid = `.page-container:visible .frappe-control[data-fieldname="${table}"]`;
    // جداول المعاملات تبدأ بصف فارغ أو صفّين: يُملأ أول فارغ (reuse = الحقل الذي يدلّ
    // فراغه على فراغ الصف)، وإلا يُضاف صف.
    let idx = reuse ? await js(([t, f]) => (cur_frm.doc[t] || []).findIndex((r) => !r[f]), [table, reuse]) : -1;
    if (idx < 0) {
      await click(page.locator(`${grid} .grid-add-row:visible`).first(), 700);
      idx = await js((t) => (cur_frm.doc[t] || []).length - 1, table);
    }
    const row = `${grid} .grid-body .rows > .grid-row:nth-child(${idx + 1})`;
    for (const [field, value, kind, optionText] of cells) {
      const cell = page.locator(`${row} [data-fieldname="${field}"]`).first();
      await click(cell, 350);
      const input = page.locator(`${row} [data-fieldname="${field}"] input:visible`).first();
      if (await input.count()) {
        await page.keyboard.press('Control+A'); await page.keyboard.press('Delete');
        await page.keyboard.type(String(value), { delay: 70 });
        if (kind === 'link') {
          const option = page.locator('.awesomplete > ul:visible > [role="option"]').filter({ hasText: optionText || value }).first();
          try { await option.waitFor({ state: 'visible', timeout: 15000 }); await wait(300); await click(option, 300); }
          catch (e) { log('  لا قائمة في الجدول لـ', value); await page.screenshot({ path: path.join(OUT, 'shots', 'debug-grid-' + table + '-' + field + '.png') }).catch(() => {}); }
        // Tab من آخر عمود يُنشئ صفاً جديداً فارغاً: القيمة تُثبَّت بالرجوع خانة
        } else { await page.keyboard.press(kind === 'end' ? 'Shift+Tab' : 'Tab'); }
      }
      await idle(500);
      // ما لم تثبته الواجهة يُثبَّت من خلفها: الفيديو لا يتوقف عند خلية عنيدة
      const ok = await js(([t, f, v, i]) => { const r = (cur_frm.doc[t] || [])[i]; return r && (String(r[f] == null ? '' : r[f]) === String(v) || (v !== '' && !isNaN(v) && Number(r[f]) === Number(v))); }, [table, field, value, idx]);
      if (!ok) {
        log('  FALLBACK', table, field);
        await js(([t, f, v, i]) => { const r = (cur_frm.doc[t] || [])[i]; return frappe.model.set_value(r.doctype, r.name, f, isNaN(v) || v === '' ? v : Number(v)); }, [table, field, value, idx]);
        await idle(600);
      }
    }
    await page.keyboard.press('Escape').catch(() => {});
    await wait(300);
  }
  // خلية في صف موجود: تُضغط وتُكتب قيمتها
  async function gridCell(table, field, value) {
    const grid = `.page-container:visible .frappe-control[data-fieldname="${table}"]`;
    const cell = page.locator(`${grid} .grid-body .grid-row:last-child [data-fieldname="${field}"]`).first();
    await click(cell, 350);
    const input = page.locator(`${grid} .grid-body .grid-row:last-child [data-fieldname="${field}"] input:visible`).first();
    if (await input.count()) {
      await page.keyboard.press('Control+A'); await page.keyboard.press('Delete');
      await page.keyboard.type(String(value), { delay: 80 });
      await page.keyboard.press('Tab');
    }
    await idle(600);
    const ok = await js(([t, f, v]) => { const rows = cur_frm.doc[t] || []; const r = rows[rows.length - 1]; return r && Number(r[f]) === Number(v); }, [table, field, value]);
    if (!ok) {
      log('  FALLBACK', table, field);
      await js(([t, f, v]) => { const rows = cur_frm.doc[t] || []; const r = rows[rows.length - 1]; return frappe.model.set_value(r.doctype, r.name, f, Number(v)); }, [table, field, value]);
      await idle(600);
    }
    await page.keyboard.press('Escape').catch(() => {});
    await wait(300);
  }
  const field = (name) => page.locator(`.page-container:visible .frappe-control[data-fieldname="${name}"]:visible`).first();
  const checkbox = (name) => page.locator(`.page-container:visible .frappe-control[data-fieldname="${name}"] input[type=checkbox]:visible`).first();
  // نموذج جديد من بلاطة في لوحة
  async function newFrom(section, label, doctype) {
    await goSection(section);
    await click(tile(label), 600);
    await page.waitForFunction((d) => window.cur_frm && cur_frm.doctype === d && cur_frm.is_new(), doctype, { timeout: 90000 });
    await idle(900);
  }
  // حفظ ثم اعتماد، كما يفعل المستخدم: زرّ «حفظ» ثم «اعتماد» وتأكيده
  async function saveAndSubmit(what) {
    await js(() => window.scrollTo({ top: 0, behavior: 'smooth' })); await wait(600);
    await save();
    if (await js(() => cur_frm.is_new())) throw new Error('لم يُحفظ: ' + what + ' — ' + await js(() => (document.querySelector('.modal.show .msgprint') || {}).innerText || ''));
    await closeAlerts(); await dismissMessage(); await wait(700);
    await save(true);
    await page.waitForFunction(() => window.cur_frm && cur_frm.doc.docstatus === 1, null, { timeout: 60000 });
    await idle(1200); await closeAlerts(); await dismissMessage();
    return frmDoc('name');
  }
  // رسالة في نافذة (لا سؤال): تُقرأ ثم تُغلق بزرّها، كما يفعل المستخدم
  async function dismissMessage() {
    const box = page.locator('.modal.show:has(.msgprint)').first();
    if (!(await box.isVisible().catch(() => false))) return;
    log('  رسالة:', (await box.innerText().catch(() => '')).replace(/s+/g, ' ').slice(0, 140));
    await wait(1500);
    await click(box.locator('.btn-modal-close:visible, .modal-header .close:visible').first(), 500).catch(() => page.keyboard.press('Escape'));
    await wait(400);
  }
  // اختيار الطرف يجلب بياناته ثم يعيد رسم الحقول: ما يُكتب قبل أن ينتهي يضيع
  async function settle() { await idle(1800); await idle(700); }
  async function reportReady(name) {
    await page.waitForFunction((n) => window.frappe && frappe.query_report && frappe.query_report.report_name === n && (frappe.query_report.data || []).length > 0 && !frappe.request.ajax_count, name, { timeout: 60000 }).catch(() => log('  التقرير بلا صفوف:', name));
    await idle(1500);
  }
  async function ensure(field, value, where) {
    const got = await frmDoc(field);
    if (String(got == null ? '' : got) !== String(value)) {
      log('  FALLBACK', where || '', field, '←', value, '(كان:', got, ')');
      await js(([f, v]) => cur_frm.set_value(f, v), [field, value]);
      await idle(500);
    }
  }

  const ctx = {};
  if (DRY) {
    const timed = (name, fn) => async (...args) => { const t = Date.now(); try { return await fn(...args); } finally { log('    ⏱', name, typeof args[0] === 'string' ? args[0] : '', ((Date.now() - t) / 1000).toFixed(1) + 's'); } };
    gridRow = timed('gridRow', gridRow); pick = timed('pick', pick); saveAndSubmit = timed('saveAndSubmit', saveAndSubmit);
    newFrom = timed('newFrom', newFrom); menuItem = timed('menuItem', menuItem); gridCell = timed('gridCell', gridCell);
  }
  // ── المشاهد ──
  const run = {
    async intro() { await page.goto(BASE + '/login', { waitUntil: 'domcontentloaded' }); await wait(800); },

    async login() {
      await type(page.locator('#login_email'), USER);
      await type(page.locator('#login_password'), PASS);
      await click(page.locator('.for-login .btn-login:visible').first(), 300);
      await page.waitForURL(/\/desk/, { timeout: 60000 });
      await page.waitForFunction(() => window.frappe && frappe.boot && frappe.boot.kaj, null, { timeout: 60000 });
      await page.locator('.kd').first().waitFor({ timeout: 60000 });
      await idle(1500);
    },

    async home() {
      for (const label of ['الورشة', 'المبيعات', 'المشتريات', 'المخزون', 'المحاسبة', 'الإعدادات العامة']) { await glide(sidebar(label)); await wait(900); }
      await glide(page.locator('.kd-lookup-input').first()); await wait(1500);
    },

    async part1() { await wait(300); },

    async settings() {
      await goSection('الورشة');
      await click(tile('إعدادات الورشة'), 500);
      await page.waitForFunction(() => window.cur_frm && cur_frm.doctype === 'Workshop Settings', null, { timeout: 30000 });
      await idle(900);
      await type(inForm('workshop_name'), D.workshop, { clear: true });
      await type(inForm('phone'), D.phone, { clear: true });
      await type(inForm('tax_number'), D.tax, { clear: true });
      await type(inForm('address'), D.address, { clear: true });
      await save();
      await closeAlerts();
    },

    async technician() {
      await goSection('الورشة');
      await click(tile('الفنيون'), 500);
      await page.waitForFunction(() => window.cur_list && cur_list.doctype === 'Workshop Technician', null, { timeout: 30000 });
      await idle(800);
      await click(primary(), 600);
      await page.waitForFunction(() => window.cur_frm && cur_frm.doctype === 'Workshop Technician' && cur_frm.is_new(), null, { timeout: 30000 });
      await idle(600);
      await type(inForm('technician_name'), D.tech);
      await type(inForm('specialization'), 'ميكانيكا');
      await type(inForm('commission_rate'), '10', { clear: true });
      await save();
      ctx.tech = await frmDoc('name');
      if (!ctx.tech || (await js(() => cur_frm.is_new()))) throw new Error('لم يُحفظ الفني');
      await closeAlerts();
    },

    async item(code, name, group, stock, rate, qty, cost) {
      await goSection('المخزون');
      await click(tile('صنف جديد'), 600);
      await page.locator('.modal.show .frappe-control[data-fieldname="item_code"] input').first().waitFor({ timeout: 30000 });
      await idle(500);
      await type(inDialog('item_code'), code);
      await type(inDialog('item_name'), name);
      await pick(inDialog('item_group'), group.slice(0, 5), group);
      const uom = await js(() => cur_dialog.get_value('stock_uom'));
      if (!uom) await js(() => cur_dialog.set_value('stock_uom', 'Nos'));
      if (!stock) { await click(page.locator('.modal.show .frappe-control[data-fieldname="is_stock_item"] input[type=checkbox]').first(), 500); }
      await type(inDialog('standard_rate'), rate, { clear: true });
      if (stock) {
        if (await inDialog('opening_stock').count()) await type(inDialog('opening_stock'), qty, { clear: true });
        await type(inDialog('valuation_rate'), cost, { clear: true });
      }
      // ما لم يثبت في الحوار يُثبَّت قبل الحفظ
      await js(([c, n, g, s, r, q, k]) => { const d = cur_dialog; const set = (f, v) => { if (String(d.get_value(f) == null ? '' : d.get_value(f)) !== String(v)) return d.set_value(f, v); };
        return Promise.all([set('item_code', c), set('item_name', n), set('item_group', g), set('is_stock_item', s ? 1 : 0), set('standard_rate', Number(r)), s ? set('opening_stock', Number(q)) : null, s ? set('valuation_rate', Number(k)) : null]); },
        [code, name, group, stock, rate, qty, cost]);
      await wait(700);
      await click(page.locator('.modal.show .modal-footer .btn-primary:visible, .modal.show .btn-primary:visible').first(), 600);
      await idle(1500);
      const exists = await js((c) => frappe.db.exists('Item', c), code);
      if (!exists) throw new Error('لم يُحفظ الصنف ' + code);
      await closeAlerts();
    },
    async service() { await run.item(D.svcCode, D.svcName, 'خدمات الورشة', false, D.svcRate); },
    async part() { await run.item(D.partCode, D.partName, 'قطع غيار', true, D.partRate, D.partQty, D.partCost); },

    async part2() { await wait(300); },

    async customer() {
      await goSection('الورشة');
      await click(tile('عميل جديد'), 600);
      await page.locator('.modal.show .frappe-control[data-fieldname="customer_name"] input').first().waitFor({ timeout: 30000 });
      await idle(400);
      await type(inDialog('customer_name'), D.customer);
      await type(inDialog('mobile_number'), D.mobile);
      await wait(600);
      await click(page.locator('.modal.show .modal-footer .btn-primary:visible, .modal.show .btn-primary:visible').first(), 600);
      await idle(1500);
      ctx.customer = (await js((n) => frappe.db.get_list('Customer', { filters: { customer_name: n }, limit: 1 }), D.customer))[0];
      if (!ctx.customer) throw new Error('لم يُحفظ العميل');
      ctx.customer = ctx.customer.name;
      await closeAlerts();
    },

    async vehicle() {
      const brands = await js(() => frappe.db.get_list('Vehicle Brand', { limit: 50 }));
      const brand = (brands.find((b) => /تويوتا/.test(b.name)) || brands[0]).name;
      const models = await js((b) => frappe.db.get_list('Vehicle Model', { filters: { brand: b }, fields: ['name', 'model_name'], limit: 20 }), brand);
      const model = models.find((m) => /كامري/.test(m.model_name || m.name)) || models[0];
      await goSection('الورشة');
      await click(tile('مركبة جديدة'), 600);
      await page.waitForFunction(() => window.cur_frm && cur_frm.doctype === 'Customer Vehicle' && cur_frm.is_new(), null, { timeout: 30000 });
      await idle(700);
      await pick(inForm('customer'), D.customer.slice(0, 8), D.customer);
      await ensure('customer', ctx.customer, 'vehicle');
      await js(() => { document.querySelectorAll('.modal.show .btn-primary, .modal.show .btn-modal-close').forEach((b) => b.click()); });
      await type(inForm('plate_number'), D.plate, { clear: true });
      await pick(inForm('brand'), brand.slice(0, 4), brand);
      await ensure('brand', brand, 'vehicle');
      if (model) { await pick(inForm('model'), (model.model_name || model.name).slice(0, 4), model.model_name || model.name); await ensure('model', model.name, 'vehicle'); }
      await type(inForm('year'), D.year, { clear: true });
      await type(inForm('mileage'), D.mileage, { clear: true });
      await ensure('plate_number', D.plate, 'vehicle');
      await save();
      ctx.vehicle = await frmDoc('name');
      if (await js(() => cur_frm.is_new())) throw new Error('لم تُحفظ المركبة');
      await closeAlerts();
    },

    async card_open() {
      await goSection('الورشة');
      await click(tile('بطاقة عمل جديدة'), 600);
      await page.waitForFunction(() => window.cur_frm && cur_frm.doctype === 'Work Card' && cur_frm.is_new(), null, { timeout: 30000 });
      await idle(800);
      await pick(inForm('customer'), D.customer.slice(0, 8), D.customer);
      await ensure('customer', ctx.customer, 'card');
      await idle(1500);
      if (!(await frmDoc('vehicle'))) await ensure('vehicle', ctx.vehicle, 'card');
      await glide(inForm('customer_phone')); await wait(700);
      await type(inForm('mileage'), '84620', { clear: true });
      await type(inForm('complaint'), D.complaint, { clear: true });
      const fuel = inForm('fuel_level');
      await glide(fuel); await fuel.selectOption({ label: 'نصف' }).catch(() => {}); await wait(500);
      await ensure('fuel_level', 'نصف', 'card');
      await click(page.locator('.page-container:visible .frappe-control[data-fieldname="no_visible_damage"] input[type=checkbox]:visible').first(), 500);
      if (!(await frmDoc('no_visible_damage'))) await ensure('no_visible_damage', 1, 'card');
    },

    async card_work() {
      await click(page.locator('.page-container:visible .form-tabs .nav-link:visible').filter({ hasText: 'الأعمال والقطع' }).first(), 700);
      await gridRow('services', [['service', D.svcCode, 'link', D.svcCode]]);
      await idle(900);
      await gridRow('parts', [['item', D.partCode, 'link', D.partCode], ['qty', '1']]);
      await idle(900);
      await gridRow('technicians', [['technician', ctx.tech, 'link', ctx.tech], ['task', 'تغيير الزيت والفلتر'], ['hours', '1']]);
      await idle(700);
      const totals = page.locator('.page-container:visible .frappe-control[data-fieldname="grand_total"]:visible').first();
      await glide(totals); await wait(1200);
      const got = await js(() => ({ s: cur_frm.doc.services_total, p: cur_frm.doc.parts_total, g: cur_frm.doc.grand_total }));
      log('  الإجماليات', JSON.stringify(got));
      if (!(got.g > 0)) throw new Error('إجمالي البطاقة صفر');
    },

    async card_submit() {
      await js(() => window.scrollTo({ top: 0, behavior: 'smooth' })); await wait(700);
      // العمل انتهى: الحالة «جاهزة للتسليم» قبل الاعتماد
      await click(page.locator('.page-container:visible .form-tabs .nav-link:visible').filter({ hasText: 'الاستلام' }).first(), 600);
      await pick(inForm('status'), 'جاهزة', 'جاهزة للتسليم');
      await ensure('status', 'جاهزة للتسليم', 'card');
      await save();
      if (await js(() => cur_frm.is_new())) throw new Error('لم تُحفظ البطاقة');
      ctx.card = await frmDoc('name');
      await closeAlerts(); await wait(900);
      await save(true);
      await page.waitForFunction(() => window.cur_frm && cur_frm.doc.docstatus === 1, null, { timeout: 60000 });
      await idle(1200); await closeAlerts();
    },

    async invoice() {
      await js(() => window.scrollTo({ top: 0 })); await wait(400);
      await menuItem('إنشاء', 'إنشاء فاتورة');
      await page.waitForFunction(() => window.cur_frm && cur_frm.doctype === 'Sales Invoice', null, { timeout: 60000 });
      await idle(1500);
      ctx.invoice = await frmDoc('name');
      const items = page.locator('.page-container:visible .frappe-control[data-fieldname="items"]:visible').first();
      await glide(items); await wait(1400);
      const total = page.locator('.page-container:visible .frappe-control[data-fieldname="grand_total"]:visible').first();
      await glide(total); await wait(1600);
      await js(() => window.scrollTo({ top: 0, behavior: 'smooth' })); await wait(700);
      if (await js(() => cur_frm.doc.docstatus === 0 && !!cur_frm.doc.__unsaved)) await save();
      await save(true);
      await page.waitForFunction(() => window.cur_frm && cur_frm.doc.docstatus === 1, null, { timeout: 60000 });
      await idle(1200); await closeAlerts();
    },

    async payment() {
      await js(() => window.scrollTo({ top: 0 })); await wait(400);
      await menuItem('إنشاء', 'سداد');
      await page.waitForFunction(() => window.cur_frm && cur_frm.doctype === 'Payment Entry', null, { timeout: 60000 });
      await idle(1500);
      await glide(page.locator('.page-container:visible .frappe-control[data-fieldname="paid_amount"]:visible').first()); await wait(900);
      await type(inForm('reference_no'), 'نقداً', { clear: true });
      await js(() => cur_frm.set_value('reference_date', frappe.datetime.get_today())); await idle(400);
      await ensure('reference_no', 'نقداً', 'payment');
      await js(() => window.scrollTo({ top: 0, behavior: 'smooth' })); await wait(600);
      await save();
      if (await js(() => cur_frm.is_new())) throw new Error('لم يُحفظ السند');
      await closeAlerts(); await wait(700);
      await save(true);
      await page.waitForFunction(() => window.cur_frm && cur_frm.doc.docstatus === 1, null, { timeout: 60000 });
      await idle(1200); await closeAlerts();
    },

    async print() {
      await js((n) => frappe.set_route('Form', 'Sales Invoice', n), ctx.invoice);
      await page.waitForFunction((n) => window.cur_frm && cur_frm.doctype === 'Sales Invoice' && cur_frm.doc.name === n, ctx.invoice, { timeout: 60000 });
      await idle(1500);
      await glide(page.locator('.page-container:visible .indicator-pill:visible').first()).catch(() => {}); await wait(1200);
      const printer = page.locator('.page-container:visible .page-head button:has(use[href="#icon-printer"]):visible, .page-container:visible .form-sidebar .form-print:visible').first();
      await click(printer, 800);
      await page.waitForFunction(() => /print/.test(frappe.get_route_str().toLowerCase()), null, { timeout: 30000 }).catch(() => log('  لم تُفتح صفحة الطباعة'));
      await idle(3500);
      // الفاتورة من أعلاها أولاً (الرأس والعميل والبنود)، ثم الإجماليات والتوقيع
      await page.mouse.move(430, 300, { steps: 20 }); await wait(5000);
      await page.mouse.wheel(0, 170); await wait(4000);
    },

    async part3() { await wait(300); },

    async dashboard() {
      await goSection('الورشة');
      await glide(page.locator('.kd-stats').first()).catch(() => {}); await wait(1800);
      await type(page.locator('.kd-lookup-input').first(), D.customer.slice(0, 10), { delay: 90 });
      const hit = page.locator('.kd-lookup-out [data-profile]').first();
      await hit.waitFor({ state: 'visible', timeout: 20000 }).catch(() => log('  لا نتيجة بحث'));
      await wait(600);
      if (await hit.count()) { await click(hit, 600); await idle(1500); await page.mouse.wheel(0, 240); await wait(2200); }
    },

    async report() {
      await goSection('المخزون');
      await click(tile('رصيد المخزون'), 600);
      await page.waitForFunction(() => window.frappe && frappe.query_report && frappe.query_report.report_name === 'Stock Balance' && (frappe.query_report.data || []).length > 0 && !frappe.request.ajax_count, null, { timeout: 60000 }).catch(() => log('  التقرير بلا صفوف'));
      await idle(1500);
      const cell = page.locator('.page-container:visible .dt-row:not(.dt-row-header):not(.dt-row-filter) .dt-cell__content').filter({ hasText: D.partName }).first();
      if (await cell.count()) { await glide(cell); await wait(1200); }
      await page.mouse.move(520, 420, { steps: 20 }); await wait(1800);
    },

    async users() {
      await goSection('الإعدادات العامة');
      await click(tile('المستخدمون'), 600);
      await page.waitForFunction(() => window.cur_list && cur_list.doctype === 'User', null, { timeout: 30000 });
      await idle(1200);
      await click(primary(), 700);
      await page.locator('.modal.show .kaj-roles').first().waitFor({ timeout: 30000 });
      await wait(500);
      await type(inDialog('full_name'), D.user);
      await type(inDialog('email'), D.email);
      await type(inDialog('password'), D.password);
      const role = page.locator('.modal.show .kaj-role').filter({ hasText: D.role }).first();
      await click(role, 700);
      await wait(900);
      await click(page.locator('.modal.show .modal-footer .btn-primary:visible').first(), 700);
      await idle(2500);
      const made = await js((e) => frappe.db.exists('User', e), D.email);
      if (!made) log('  تحذير: المستخدم لم يُنشأ');
      await closeAlerts(); await wait(1200);
    },

    async outro() { await wait(300); },

    // ══ الجزء الثاني ══
    async intro2() {
      await page.goto(BASE + '/desk/home', { waitUntil: 'domcontentloaded' });
      await page.waitForFunction(() => window.frappe && frappe.boot && frappe.boot.kaj && document.querySelector('.body-sidebar') && !document.querySelector('.splash'), null, { timeout: 120000 });
      await page.locator('.kd').first().waitFor({ timeout: 60000 });
      // العميل والأصناف من الجزء الأول، بأسمائها هناك (اللاحقة لما يُنشأ هنا وحده)
      if (SFX) for (const k of ['customer', 'partCode', 'svcCode']) D[k] = D[k].slice(0, -SFX.length);
      ctx.customer = (await js((n) => frappe.db.get_list('Customer', { filters: { customer_name: n }, limit: 1 }), D.customer))[0].name;
      ctx.company = await js(() => frappe.defaults.get_default('company'));
      ctx.abbr = (await js((c) => frappe.db.get_value('Company', c, 'abbr'), ctx.company)).message.abbr;
      ctx.warehouse = (await js(() => frappe.db.get_single_value('Stock Settings', 'default_warehouse')));
      await idle(800);
    },
    async s_sales() { await wait(300); },

    async quotation() {
      await newFrom('المبيعات', 'عرض سعر جديد', 'Quotation');
      await pick(inForm('party_name'), D.customer.slice(0, 8), D.customer);
      await settle();
      await ensure('party_name', ctx.customer, 'quotation');
      await settle();
      await gridRow('items', [['item_code', D.partCode, 'link', D.partCode], ['qty', '2']], 'item_code');
      await idle(900);
      await gridRow('items', [['item_code', D.svcCode, 'link', D.svcCode], ['qty', '1']], 'item_code');
      await idle(900);
      await glide(field('grand_total')); await wait(1500);
      await ensure('party_name', ctx.customer, 'quotation');
      ctx.quotation = await saveAndSubmit('عرض السعر');
      await glide(page.locator('.page-container:visible .indicator-pill:visible').first()).catch(() => {}); await wait(1200);
    },

    async direct_sale() {
      await newFrom('المبيعات', 'فاتورة مبيعات جديدة', 'Sales Invoice');
      await pick(inForm('customer'), D.customer.slice(0, 8), D.customer);
      await settle();
      await ensure('customer', ctx.customer, 'sale');
      await settle();
      await click(checkbox('update_stock'), 600);
      if (!(await frmDoc('update_stock'))) await ensure('update_stock', 1, 'sale');
      await gridRow('items', [['item_code', D.partCode, 'link', D.partCode], ['qty', '2']], 'item_code');
      await idle(900);
      await glide(field('grand_total')); await wait(1500);
      await ensure('customer', ctx.customer, 'sale');
      if (!(await frmDoc('update_stock'))) await ensure('update_stock', 1, 'sale');
      ctx.sale = await saveAndSubmit('فاتورة البيع');
    },

    async sales_return() {
      await js(() => window.scrollTo({ top: 0 })); await wait(400);
      await menuItem('إنشاء', 'مرتجع');
      await page.waitForFunction(() => window.cur_frm && cur_frm.doctype === 'Sales Invoice' && cur_frm.doc.is_return && cur_frm.is_new(), null, { timeout: 60000 });
      await idle(1500);
      await glide(field('is_return')).catch(() => {}); await wait(900);
      // أُعيدت قطعة واحدة من اثنتين
      await gridCell('items', 'qty', '-1');
      await glide(field('grand_total')); await wait(1400);
      ctx.ret = await saveAndSubmit('المرتجع');
    },

    async s_purchasing() { await wait(300); },

    async supplier() {
      await goSection('المشتريات');
      await click(page.locator('.kd-sections a, .kd-sec a, .kd a').filter({ hasText: /^\s*الموردون\s*$/ }).last(), 600);
      await page.waitForFunction(() => window.cur_list && cur_list.doctype === 'Supplier', null, { timeout: 30000 });
      await idle(1000);
      await click(primary(), 700);
      await page.locator('.modal.show .frappe-control[data-fieldname="supplier_name"] input').first().waitFor({ timeout: 30000 });
      await idle(400);
      await type(inDialog('supplier_name'), D.supplier);
      await type(inDialog('mobile_number'), D.supplierMobile);
      await wait(600);
      await click(page.locator('.modal.show .modal-footer .btn-primary:visible, .modal.show .btn-primary:visible').first(), 600);
      await idle(1500);
      ctx.supplier = ((await js((n) => frappe.db.get_list('Supplier', { filters: { supplier_name: n }, limit: 1 }), D.supplier))[0] || {}).name;
      if (!ctx.supplier) throw new Error('لم يُحفظ المورد');
      await closeAlerts(); await wait(900);
    },

    async purchase() {
      await newFrom('المشتريات', 'فاتورة مشتريات جديدة', 'Purchase Invoice');
      await pick(inForm('supplier'), D.supplier.slice(0, 8), D.supplier);
      await settle();
      await ensure('supplier', ctx.supplier, 'purchase');
      await settle();
      await type(inForm('bill_no'), D.billNo, { clear: true });
      await click(checkbox('update_stock'), 600);
      if (!(await frmDoc('update_stock'))) await ensure('update_stock', 1, 'purchase');
      await gridRow('items', [['item_code', D.partCode, 'link', D.partCode], ['qty', '3'], ['rate', '2', 'end']], 'item_code');
      await idle(900);
      await ensure('supplier', ctx.supplier, 'purchase');
      await ensure('bill_no', D.billNo, 'purchase');
      if (!(await frmDoc('update_stock'))) await ensure('update_stock', 1, 'purchase');
      await glide(field('grand_total')).catch(() => {}); await wait(1500);
      ctx.purchase = await saveAndSubmit('فاتورة المشتريات');
    },

    async purchase_pay() {
      await js(() => window.scrollTo({ top: 0 })); await wait(400);
      await menuItem('إنشاء', 'سداد');
      await page.waitForFunction(() => window.cur_frm && cur_frm.doctype === 'Payment Entry', null, { timeout: 60000 });
      await idle(1500);
      await glide(field('paid_amount')); await wait(900);
      await type(inForm('reference_no'), 'حوالة 5521', { clear: true });
      await js(() => cur_frm.set_value('reference_date', frappe.datetime.get_today())); await idle(400);
      await ensure('reference_no', 'حوالة 5521', 'purchase_pay');
      await saveAndSubmit('سند الصرف');
    },

    async s_stock() { await wait(300); },

    async stock_ledger() {
      await goSection('المخزون');
      await click(tile('دفتر حركة المخزون'), 600);
      await reportReady('Stock Ledger');
      const rows = page.locator('.page-container:visible .dt-row:not(.dt-row-header):not(.dt-row-filter)');
      const n = Math.min(await rows.count(), 6);
      for (let i = 0; i < n; i++) { await glide(rows.nth(i).locator('.dt-cell__content').nth(2)).catch(() => {}); await wait(1100); }
      await page.mouse.move(520, 470, { steps: 20 }); await wait(1500);
    },

    async stock_issue() {
      await newFrom('المخزون', 'حركة مخزون جديدة', 'Stock Entry');
      // أنواع الحركة تُعرض مترجمة ويُبحث فيها بأسمائها الأصلية: تُفتح القائمة ويُختار منها
      await click(inForm('stock_entry_type'), 300);
      const issue = page.locator('.awesomplete > ul:visible > [role="option"]').filter({ hasText: 'صرف مواد' }).first();
      await issue.waitFor({ state: 'visible', timeout: 12000 }).then(() => click(issue, 400)).catch(() => log('  لا خيار «صرف مواد» في القائمة'));
      await idle(600);
      await ensure('stock_entry_type', 'Material Issue', 'issue');
      await idle(900);
      await gridRow('items', [['s_warehouse', ctx.warehouse, 'link', ctx.warehouse.split(' - ')[0]], ['item_code', D.partCode, 'link', D.partCode], ['qty', '1', 'end']], 'item_code');
      await idle(900);
      ctx.issue = await saveAndSubmit('حركة الصرف');
    },

    async stocktake() {
      await goSection('المخزون');
      await click(page.locator('.kd a').filter({ hasText: /^\s*الجرد\s*$/ }).last(), 600);
      await page.waitForFunction(() => window.cur_list && cur_list.doctype === 'Stock Reconciliation', null, { timeout: 30000 });
      await idle(1000);
      await click(primary(), 700);
      await page.waitForFunction(() => window.cur_frm && cur_frm.doctype === 'Stock Reconciliation' && cur_frm.is_new(), null, { timeout: 45000 });
      await idle(900);
      const purpose = inForm('purpose');
      await glide(purpose); await purpose.selectOption('Stock Reconciliation').catch(() => {}); await wait(600);
      await ensure('purpose', 'Stock Reconciliation', 'stocktake');
      await idle(900);
      const counted = (await js(([i, w]) => frappe.db.get_value('Bin', { item_code: i, warehouse: w }, 'actual_qty'), [D.partCode, ctx.warehouse])).message.actual_qty - 1;
      await gridRow('items', [['item_code', D.partCode, 'link', D.partCode], ['warehouse', ctx.warehouse, 'link', ctx.warehouse.split(' - ')[0]], ['qty', String(counted), 'end']], 'item_code');
      await idle(1500);
      // حساب الفرق: تسويات المخزون (الجرد ليس رصيداً افتتاحياً)
      const adj = (await js((c) => frappe.db.get_value('Company', c, 'stock_adjustment_account'), ctx.company)).message.stock_adjustment_account;
      if ((await frmDoc('expense_account')) !== adj) await js((a) => cur_frm.set_value('expense_account', a), adj);
      await idle(600);
      await saveAndSubmit('الجرد');
    },

    async s_accounting() { await wait(300); },

    async expense() {
      await newFrom('المحاسبة', 'قيد يومية جديد', 'Journal Entry');
      const exp = D.expenseAccount + ' - ' + ctx.abbr, bank = D.bankAccount + ' - ' + ctx.abbr;
      await gridRow('accounts', [['account', exp, 'link', D.expenseAccount], ['debit_in_account_currency', D.expenseAmount]], 'account');
      await idle(800);
      await gridRow('accounts', [['account', bank, 'link', D.bankAccount], ['credit_in_account_currency', D.expenseAmount, 'end']], 'account');
      await idle(800);
      await glide(field('total_debit')).catch(() => {}); await wait(1500);
      ctx.journal = await saveAndSubmit('قيد اليومية');
    },

    async reports_fin() {
      await goSection('المحاسبة');
      await click(tile('قائمة الدخل'), 600);
      await reportReady('Profit and Loss Statement');
      const rows = page.locator('.page-container:visible .dt-row:not(.dt-row-header):not(.dt-row-filter)');
      const n = Math.min(await rows.count(), 8);
      for (let i = 0; i < n; i += 2) { await glide(rows.nth(i).locator('.dt-cell__content').nth(1)).catch(() => {}); await wait(1000); }
      await wait(2500);
      await goSection('المحاسبة');
      await click(tile('مديونيات العملاء'), 600);
      await reportReady('Accounts Receivable');
      const cell = page.locator('.page-container:visible .dt-row:not(.dt-row-header):not(.dt-row-filter) .dt-cell__content').filter({ hasText: D.customer }).first();
      if (await cell.count()) { await glide(cell); await wait(1500); }
      await page.mouse.move(520, 470, { steps: 20 }); await wait(2500);
    },

    async s_settings() { await wait(300); },

    async identity() {
      await goSection('الإعدادات العامة');
      await click(tile('الشعار والهوية'), 600);
      await page.waitForFunction(() => window.cur_frm && cur_frm.doctype === 'Website Settings', null, { timeout: 45000 });
      await idle(1200);
      await glide(field('app_name')).catch(() => {}); await wait(1500);
      await glide(field('app_logo')).catch(() => {}); await wait(2200);
      await goSection('الإعدادات العامة');
      await click(tile('ترويسات الطباعة'), 600);
      await page.waitForFunction(() => window.cur_list && cur_list.doctype === 'Letter Head', null, { timeout: 30000 });
      await idle(1200);
      const first = page.locator('.page-container:visible .list-row-container .list-row a.ellipsis, .page-container:visible .list-row-container .list-subject a').first();
      await click(first, 800).catch(() => {});
      if (!(await js(() => window.cur_frm && cur_frm.doctype === 'Letter Head'))) {
        const name = (await js(() => frappe.db.get_value('Letter Head', { is_default: 1 }, 'name'))).message.name;
        await js((n) => frappe.set_route('Form', 'Letter Head', n), name);
      }
      await page.waitForFunction(() => window.cur_frm && cur_frm.doctype === 'Letter Head' && !cur_frm.is_new(), null, { timeout: 45000 }).catch(() => log('  لم تُفتح الترويسة'));
      await idle(1200);
      for (const f of ['kaj_header_img', 'kaj_footer_img', 'kaj_stamp_img']) { await glide(field(f)).catch(() => {}); await wait(1300); }
    },

    async backup() {
      await goSection('الإعدادات العامة');
      await click(tile('النسخ الاحتياطي'), 600);
      await page.waitForFunction(() => /backups/.test(frappe.get_route_str()), null, { timeout: 30000 });
      await idle(2500);
      const cards = page.locator('.page-container:visible .layout-main-section a:visible, .page-container:visible .download-backup-card:visible');
      const n = Math.min(await cards.count(), 3);
      for (let i = 0; i < n; i++) { await glide(cards.nth(i)).catch(() => {}); await wait(1300); }
      await wait(1500);
    },

    async outro2() { await wait(300); },
  };

  const timeline = [];
  let failed = null;
  for (let i = 0; i < scenes.length; i++) {
    const scene = scenes[i];
    if (FROM && i > 0 && scenes.findIndex((x) => x.id === FROM) > i) continue;
    const start = (Date.now() - t0) / 1000;
    timeline.push({ id: scene.id, start: +start.toFixed(2) });
    log('▶', scene.id);
    try {
      if (i === 0) await run[scene.id]();                     // لا بدّ من صفحة تُرسم فوقها البطاقة
      await js((c) => window.__kv && window.__kv.sync(c), sync.color(i));   // بداية المشهد كما يراها الفيديو
      if (scene.card) { await caption(''); await card(scene.card[0], scene.card[1]); await wait(500); }
      else { await card('', ''); await caption(scene.caption); }
      const began = Date.now();
      if (i !== 0) await run[scene.id]();
      const need = DRY ? 400 : (durations[scene.id] || 4) * 1000 + 700 - (Date.now() - began);
      if (need > 0) await wait(need);
      await page.screenshot({ path: path.join(OUT, 'shots', String(i).padStart(2, '0') + '-' + scene.id + '.png') });
      if (scene.card) { await card('', ''); await wait(450); }
      timeline[timeline.length - 1].took = +((Date.now() - began) / 1000).toFixed(1);
    } catch (e) {
      failed = { scene: scene.id, error: String(e && e.message || e).slice(0, 400) };
      log('✗', scene.id, failed.error);
      await page.screenshot({ path: path.join(OUT, 'shots', 'FAILED-' + scene.id + '.png') }).catch(() => {});
      break;
    }
    if (UNTIL && scene.id === UNTIL) break;
  }
  const total = (Date.now() - t0) / 1000;
  await wait(600);
  const english = await js(() => JSON.parse(sessionStorage.getItem('kv-en') || '[]')).catch(() => []);
  fs.writeFileSync(path.join(OUT, 'english.json'), JSON.stringify(english, null, 2));
  console.log('ENGLISH', english.length);
  english.forEach((t) => console.log('   EN', t));
  await context.close();
  const video = fs.readdirSync(path.join(OUT, 'video')).filter((f) => f.endsWith('.webm')).map((f) => ({ f, t: fs.statSync(path.join(OUT, 'video', f)).mtimeMs })).sort((a, b) => b.t - a.t)[0];
  fs.writeFileSync(path.join(OUT, 'timeline.json'), JSON.stringify({ total: +total.toFixed(2), video: video && video.f, failed, scenes: timeline }, null, 2));
  console.log(failed ? 'RECORD_FAILED ' + JSON.stringify(failed) : 'RECORD_OK ' + total.toFixed(1) + 's ' + (video && video.f));
  process.exit(failed ? 1 : 0);
})().catch((e) => { console.error('RECORD_CRASH', e && e.stack || e); process.exit(2); });
