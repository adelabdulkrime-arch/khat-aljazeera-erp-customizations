// مصفوفة فحص صفحة الدخول — تُحمَّل في المعاينة المحلية (serve.js):
//
//   const s = document.createElement('script'); s.src = '/matrix.js'; document.head.append(s);
//   await __kajMatrix.points('ar');   // تحميل جديد لكل مقاس وقسم وحالة
//   await __kajMatrix.sweep('ar');    // كل ارتفاع لكل عرض وحالة
//
// كلاهما يعيد {runs, pass, fails}. الوضع الفاتح/الداكن يتبع المتصفح، فيُشغَّل
// كلٌّ منهما مرتين. الصفحة تُحمَّل في <iframe> من الأصل نفسه بالمقاس المطلوب:
// استعلامات الوسائط تُقاس على نافذة الإطار.
(function () {
  const sleep = ms => new Promise(r => setTimeout(r, ms));

  // مقاسات CSS لا فيزيائية: 1920×1080 بتكبير 150% نافذتها نحو 1260×590
  const VIEWPORTS = [
    [2560, 1300], [1920, 950], [1536, 730], [1440, 680], [1366, 650], [1280, 600], [1260, 590],
    [1093, 510], [1024, 768], [1023, 700], [768, 1024], [390, 844], [390, 664], [375, 553],
    [360, 640], [360, 560], [320, 568],
    // أقصر من المحتوى (هاتف بالعرض، نافذة مصغَّرة): التمرير حتميّ، والمطلوب
    // ألا يُقصّ شيء ولا يتعذّر الوصول إليه ولا يركب عائمٌ البطاقة بعد التمرير
    [844, 390], [667, 375], [360, 460], [1093, 400],
  ];
  // [القسم، الحالة]. حالات الخطأ تخصّ الدخول: القسمان الآخران أقصر منه
  // ولا يعرضان تنبيه حقول (زرّهما معطّل حتى يُكتب البريد).
  const CASES = [
    ['login', 'base'], ['login', 'banner'], ['login', 'long'], ['login', 'fields'],
    ['forgot', 'base'], ['login-with-email-link', 'base'],
  ];
  const SWEEP_WIDTHS = [320, 340, 359, 360, 375, 390, 412, 480, 575, 576, 768, 1023, 1024, 1093, 1260, 1366, 1920, 2560];

  // «ثبّت التطبيق» يظهر فقط حين يعرض المتصفح التثبيت؛ يُحاكى بتنسيق pwa.js
  const FAB_CSS = '#kaj-install-fab{position:fixed;bottom:18px;left:18px;z-index:1030;display:none;align-items:center;gap:10px;direction:rtl;background:#1a2b4a;color:#fff;border-radius:999px;padding:10px 14px 10px 16px;font-family:"Tahoma","Segoe UI",sans-serif;font-size:14px;font-weight:bold;}#kaj-install-fab .kaj-install-x{margin-inline-start:2px;width:20px;height:20px;display:inline-flex;align-items:center;justify-content:center;border-radius:50%;font-size:13px;font-weight:normal;}';

  let checkerSrc = null;

  async function open(lang, view, state, w, h) {
    if (!checkerSrc) checkerSrc = await fetch('/checker.js').then(r => r.text());
    document.cookie = 'preferred_language=' + lang + ';path=/;max-age=31536000';
    let lastError;
    for (let attempt = 0; attempt < 3; attempt++) {
      const f = document.createElement('iframe');
      f.style.cssText = 'position:fixed;top:0;left:0;border:0;z-index:99999;width:' + w + 'px;height:' + h + 'px;';
      const loaded = new Promise(res => { f.onload = () => res(true); setTimeout(() => res(false), 40000); });
      f.src = '/login?m=' + Math.random().toString(36).slice(2) + '#' + view;
      document.body.append(f);
      try {
        if (!(await loaded)) throw new Error('انتهت مهلة التحميل');
        const d = f.contentDocument, win = f.contentWindow;
        for (let i = 0; i < 80 && !(d.getElementById('khat-lang-switch') && win.login && win.login.set_invalid); i++) await sleep(100);
        if (!win.login) throw new Error('جافاسكربت الدخول لم يُحمَّل');
        if (d.documentElement.lang !== lang) throw new Error('لغة الصفحة ' + d.documentElement.lang + ' لا ' + lang);
        await d.fonts.ready;
        await sleep(300);
        await Promise.all(d.getAnimations().map(a => a.finished.catch(() => {})));
        const s = d.createElement('style'); s.textContent = FAB_CSS; d.head.append(s);
        const fab = d.createElement('div'); fab.id = 'kaj-install-fab';
        fab.innerHTML = '<span>⬇</span><span>ثبّت التطبيق</span><span class="kaj-install-x">×</span>';
        d.body.append(fab); fab.style.display = 'inline-flex';
        win.eval(checkerSrc);
        win.__kajSetState(state);
        // الإطار يهزّ البطاقة نصف ثانية عند فشل الدخول
        await sleep(700);
        await Promise.all(d.getAnimations().map(a => a.finished.catch(() => {})));
        return {f, d, win};
      } catch (e) { lastError = e; f.remove(); await sleep(800); }
    }
    throw lastError;
  }

  const label = (lang, view, state, w, h) => lang + ' ' + w + '×' + h + ' #' + view + ':' + state;

  // تحميل جديد لكل نقطة: كل الفحوص
  async function points(lang, viewports) {
    const out = {lang, scheme: matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light', runs: 0, pass: 0, fails: []};
    for (const [w, h] of viewports || VIEWPORTS) for (const [view, state] of CASES) {
      out.runs++;
      try {
        const {f, win} = await open(lang, view, state, w, h);
        const r = win.__kajCheck();
        const fails = r.fails.slice();
        if (r.info.viewport !== w + 'x' + h) fails.push('SIZE: ' + r.info.viewport);
        if (r.info.scheme !== out.scheme) fails.push('SCHEME: ' + r.info.scheme);
        if (state !== 'base' && !r.info.messages) fails.push('STATE: لم تظهر رسالة في حالة ' + state);
        if (state === 'base' && r.info.messages) fails.push('STATE: رسالة ظاهرة في الحالة العادية');
        f.remove();
        if (fails.length) out.fails.push(label(lang, view, state, w, h) + ' → ' + fails.join(' | ')); else out.pass++;
      } catch (e) { out.fails.push(label(lang, view, state, w, h) + ' → RUNNER: ' + e.message); }
    }
    return out;
  }

  // مسح الارتفاعات: تحميل واحد لكل حالة ثم تغيير مقاس الإطار. لكل عرض:
  //   ١) أقصر ارتفاع للمحتوى (يُقاس والنافذة أقصر منه) لا يتجاوز حدّ الاتساع؛
  //   ٢) من ذلك الارتفاع فما فوق لا تمرير عند أي ارتفاع — أي لا «ثغرات»
  //      يطول فيها المحتوى أسرع من الشاشة؛
  //   ٣) لا تمرير أفقي عند أي مقاس.
  async function sweep(lang, widths) {
    const out = {lang, scheme: matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light', runs: 0, pass: 0, fails: [], minHeights: {}};
    for (const [view, state] of CASES) {
      let ctx;
      try { ctx = await open(lang, view, state, 1260, 590); }
      catch (e) { out.runs++; out.fails.push(lang + ' #' + view + ':' + state + ' → RUNNER: ' + e.message); continue; }
      const {f, d, win} = ctx, root = d.documentElement, row = {};
      for (const w of widths || SWEEP_WIDTHS) {
        out.runs++;
        const fails = [];
        f.style.width = w + 'px'; f.style.height = '240px';
        const minH = root.scrollHeight;
        row[w] = minH;
        const budget = win.__kajBudget(w, state !== 'base');
        if (minH > budget) fails.push('BUDGET: أقصر ارتفاع ' + minH + 'px > الحدّ ' + budget + 'px');
        const holes = [];
        for (let h = Math.max(minH, 240); h <= 1400; h += 2) {
          f.style.height = h + 'px';
          if (win.innerWidth !== w || win.innerHeight !== h) { fails.push('SIZE: ' + win.innerWidth + 'x' + win.innerHeight); break; }
          if (root.scrollHeight > h + 1) holes.push(h);
          if (root.scrollWidth > w + 1) { fails.push('OVERFLOW-X: عند ' + w + '×' + h); break; }
        }
        if (holes.length) fails.push('HOLE: تمرير عند ' + holes[0] + '–' + holes[holes.length - 1] + 'px (' + holes.length + ' ارتفاعاً) مع أن المحتوى يتّسع عند ' + minH + 'px');
        if (fails.length) out.fails.push(lang + ' عرض ' + w + ' #' + view + ':' + state + ' → ' + fails.join(' | ')); else out.pass++;
      }
      out.minHeights[view + ':' + state] = row;
      f.remove();
    }
    return out;
  }

  window.__kajMatrix = {points, sweep, open, VIEWPORTS, CASES, SWEEP_WIDTHS};
})();
