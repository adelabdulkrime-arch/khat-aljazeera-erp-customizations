// فاحص صفحة الدخول — يُشغَّل في المتصفح بعد حقن login.css.
// يعيد قائمة fails فارغة حين تنجح كل الفحوص، وإلا يسمّي كل عيب بقيمته المقيسة.
(function () {
  const px = v => parseFloat(v) || 0;
  const rect = e => e.getBoundingClientRect();
  const shown = e => {
    const r = rect(e), cs = getComputedStyle(e);
    return r.width > 0 && r.height > 0 && cs.display !== 'none' && cs.visibility !== 'hidden' && cs.opacity !== '0';
  };
  const parse = c => {
    const m = c.match(/rgba?\(([^)]+)\)/);
    if (!m) return null;
    const p = m[1].split(/[ ,\/]+/).filter(Boolean).map(Number);
    return {r: p[0], g: p[1], b: p[2], a: p.length > 3 ? p[3] : 1};
  };
  const over = (f, b) => ({
    r: f.r * f.a + b.r * (1 - f.a), g: f.g * f.a + b.g * (1 - f.a),
    b: f.b * f.a + b.b * (1 - f.a), a: 1,
  });
  const lum = c => {
    const f = v => { v /= 255; return v <= .03928 ? v / 12.92 : Math.pow((v + .055) / 1.055, 2.4); };
    return .2126 * f(c.r) + .7152 * f(c.g) + .0722 * f(c.b);
  };
  const ratio = (a, b) => {
    const [x, y] = [lum(a), lum(b)].sort((p, q) => q - p);
    return (x + .05) / (y + .05);
  };
  // الخلفية الفعلية: نصعد حتى نجد لوناً معتماً
  const bgOf = e => {
    let stack = [];
    for (let n = e; n; n = n.parentElement) {
      const c = parse(getComputedStyle(n).backgroundColor);
      if (c && c.a > 0) { stack.push(c); if (c.a >= 1) break; }
    }
    let base = {r: 255, g: 255, b: 255, a: 1};
    for (let i = stack.length - 1; i >= 0; i--) base = over(stack[i], base);
    return base;
  };

  window.__kajCheck = function () {
    const fails = [], info = {};
    const F = (id, msg) => fails.push(id + ': ' + msg);
    const vw = innerWidth, vh = innerHeight;
    const rtl = document.documentElement.dir === 'rtl';
    info.viewport = vw + 'x' + vh;
    info.dir = document.documentElement.dir;
    info.scheme = matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';

    // القسم الظاهر
    const section = [...document.querySelectorAll('section')]
      .find(s => s.querySelector('.page-card') && getComputedStyle(s).display !== 'none');
    if (!section) { F('SECTION', 'لا قسم ظاهر'); return {fails, info}; }
    info.section = section.className;
    const card = section.querySelector('.page-card');

    // ١) فيض أفقي
    const sw = document.documentElement.scrollWidth;
    if (sw > vw + 1) F('OVERFLOW-X', 'scrollWidth=' + sw + ' > ' + vw);

    // ٢) الفيض الرأسي: هل يحتاج المستخدم للتمرير؟ وهل الزر الأساسي قابل للوصول؟
    const sh = document.documentElement.scrollHeight;
    info.scrollH = sh; info.needsScroll = sh > vh + 1;
    // من 480px ارتفاعاً فما فوق يجب أن يتّسع الدخول كاملاً بلا تمرير: مستخدم
    // يضطر للتمرير ليجد زر الدخول يظنّ الصفحة معطّلة.
    if (vh >= 480 && sh > vh + 1) F('FITS', 'المحتوى ' + sh + 'px > النافذة ' + vh + 'px — يحتاج تمريراً');
    const primary = section.querySelector('.btn-login:not(.btn-login-option), .btn-forgot');
    if (primary && shown(primary)) {
      const r = rect(primary);
      info.primaryBottom = Math.round(r.bottom + scrollY);
      if (r.top + scrollY < 0) F('PRIMARY-UNREACHABLE', 'الزر فوق الصفحة');
      if (sh <= vh + 1 && r.bottom > vh + 1) F('PRIMARY-CLIPPED', 'bottom=' + Math.round(r.bottom) + ' > ' + vh + ' دون إمكان التمرير');
    }

    // ٣) أهداف اللمس والحجم
    section.querySelectorAll('input:not([type=checkbox]), button, a.btn').forEach(e => {
      if (!shown(e)) return;
      const r = rect(e);
      if (r.height < 44 - .5) F('TOUCH', (e.id || e.className.toString().slice(0, 40)) + ' h=' + Math.round(r.height));
    });
    section.querySelectorAll('input:not([type=checkbox])').forEach(e => {
      if (!shown(e)) return;
      const fs = px(getComputedStyle(e).fontSize);
      if (fs < 16) F('INPUT-FONT', e.id + ' ' + fs + 'px <16 (يُكبّر iOS الصفحة)');
    });

    // ٤) تراكب الأيقونات على النص + محاذاتها الرأسية
    section.querySelectorAll('.field-icon, .toggle-password').forEach(ic => {
      if (!shown(ic)) return;
      const wrap = ic.closest('.email-field, .password-field');
      const inp = wrap && wrap.querySelector('input');
      if (!inp) return;
      const ir = rect(ic), nr = rect(inp), cs = getComputedStyle(inp);
      const l = nr.left + px(cs.borderLeftWidth) + px(cs.paddingLeft);
      const r = nr.right - px(cs.borderRightWidth) - px(cs.paddingRight);
      if (ir.right > l + .5 && ir.left < r - .5)
        F('ICON-OVERLAP', (ic.getAttribute('class') || '') + ' يتراكب مع منطقة النص (icon ' + Math.round(ir.left) + '-' + Math.round(ir.right) + ' / نص ' + Math.round(l) + '-' + Math.round(r) + ')');
      if (ir.left < nr.left - .5 || ir.right > nr.right + .5) F('ICON-OUTSIDE', 'الأيقونة خارج الحقل');
      const dy = Math.abs((ir.top + ir.height / 2) - (nr.top + nr.height / 2));
      if (dy > 1.5) F('ICON-VCENTER', 'انحراف رأسي ' + dy.toFixed(1) + 'px');
    });
    // الأيقونة الأولى عند بداية الحقل (جهة القراءة)
    const first = section.querySelector('.field-icon');
    if (first && shown(first)) {
      const inp = first.closest('.email-field, .password-field').querySelector('input');
      const atStart = rtl ? rect(first).left > rect(inp).left + rect(inp).width / 2
                          : rect(first).left < rect(inp).left + rect(inp).width / 2;
      if (!atStart) F('ICON-SIDE', 'الأيقونة ليست عند بداية الحقل');
    }

    // ٥) اقتطاع النص
    section.querySelectorAll('label, h4, .page-card-subtitle, .btn, a, .kaj-remember').forEach(e => {
      if (!shown(e)) return;
      if (e.scrollWidth > e.clientWidth + 1 && getComputedStyle(e).overflow !== 'visible')
        F('TEXT-CLIP', (e.textContent || '').trim().slice(0, 30));
    });

    // ٦) التباين WCAG AA
    const probes = [
      ['h4', section.querySelector('h4')],
      ['subtitle', section.querySelector('.page-card-subtitle')],
      ['label', section.querySelector('.form-label')],
      ['forgot', section.querySelector('.forgot-password-message a')],
      ['remember', section.querySelector('.kaj-remember')],
      ['primary', primary],
      ['secondary', section.querySelector('.btn-login-option')],
      ['input', section.querySelector('input:not([type=checkbox])')],
    ];
    info.contrast = {};
    probes.forEach(([name, e]) => {
      if (!e || !shown(e)) return;
      // الشفافية تُحتسب: عنصر بـopacity أقلّ من 1 يذوب لونه ولون خلفيته معاً في
      // ما وراءه، وتجاهلها كان يُمرّر زراً باهتاً على أنه سليم التباين.
      const cse = getComputedStyle(e), op = parseFloat(cse.opacity);
      let fg = parse(cse.color), bg = bgOf(e);
      if (!fg) return;
      if (op < 1) {
        const behind = bgOf(e.parentElement);
        const own = parse(cse.backgroundColor) || {r: 0, g: 0, b: 0, a: 0};
        bg = over({r: own.r, g: own.g, b: own.b, a: own.a * op}, behind);
        fg = {r: fg.r, g: fg.g, b: fg.b, a: fg.a * op};
      }
      const c = ratio(over(fg, bg), bg);
      info.contrast[name] = +c.toFixed(2);
      const big = px(getComputedStyle(e).fontSize) >= 24 || (px(getComputedStyle(e).fontSize) >= 18.66 && +getComputedStyle(e).fontWeight >= 700);
      if (c < (big ? 3 : 4.5)) F('CONTRAST', name + '=' + c.toFixed(2));
    });
    // النص الإرشادي
    const inp0 = section.querySelector('input:not([type=checkbox])');
    if (inp0 && shown(inp0)) {
      const ph = parse(getComputedStyle(inp0, '::placeholder').color), bg = bgOf(inp0);
      if (ph) {
        const c = ratio(over(ph, bg), bg);
        info.contrast.placeholder = +c.toFixed(2);
        if (c < 4.5) F('CONTRAST', 'placeholder=' + c.toFixed(2));
      }
    }

    // ٧) محاذاة الاتجاه: التسمية والعنوان يبدآن من نفس حافة الحقل
    const lbl = section.querySelector('.form-label'), fld = section.querySelector('input:not([type=checkbox])');
    if (lbl && fld && shown(lbl) && shown(fld)) {
      const a = rtl ? rect(lbl).right : rect(lbl).left, b = rtl ? rect(fld).right : rect(fld).left;
      if (Math.abs(a - b) > 1.5) F('ALIGN', 'التسمية لا تبدأ من حافة الحقل (فرق ' + Math.abs(a - b).toFixed(1) + 'px)');
    }
    const h4 = section.querySelector('h4');
    if (h4 && fld && shown(h4)) {
      const cs = getComputedStyle(h4);
      const startEdge = rtl ? rect(h4).right : rect(h4).left, fe = rtl ? rect(fld).right : rect(fld).left;
      if (Math.abs(startEdge - fe) > 1.5) F('ALIGN-H4', 'العنوان لا يبدأ من حافة الحقل');
    }

    // ٨) مربّع الشعار (::before ثابت): يظهر من 1024px فقط، داخل النافذة،
    //    ولا يتقاطع مع البطاقة.
    const pb = getComputedStyle(document.body, '::before');
    const panelOn = pb.content !== 'none' && pb.position === 'fixed';
    info.panel = panelOn;
    if (vw >= 1024 && !panelOn) F('PANEL', 'الشعار غائب عند ' + vw);
    if (vw < 1024 && panelOn) F('PANEL', 'الشعار ظاهر عند ' + vw);
    const cr = rect(card);
    let art = null;
    if (panelOn) {
      const w = px(pb.width), h = px(pb.height), t = px(pb.top), l = px(pb.left);
      art = {left: l, right: l + w, top: t, bottom: t + h};
      info.art = Math.round(l) + ',' + Math.round(t) + ' ' + Math.round(w) + 'x' + Math.round(h);
      if (art.left < -.5 || art.right > vw + .5 || art.top < -.5 || art.bottom > vh + .5)
        F('ART-OUT', 'الشعار خارج النافذة: ' + info.art);
      if (w < 240) F('ART-SMALL', 'ضلع الشعار ' + Math.round(w) + 'px');
      if (!(cr.right < art.left || cr.left > art.right || cr.bottom < art.top || cr.top > art.bottom))
        F('PANEL-OVERLAP', 'البطاقة تتقاطع مع الشعار');
      // الشعار في نصف البداية والبطاقة في نصف النهاية
      const artMid = (art.left + art.right) / 2, cardMid = (cr.left + cr.right) / 2;
      if (rtl ? !(artMid > vw / 2 && cardMid < vw / 2) : !(artMid < vw / 2 && cardMid > vw / 2))
        F('SIDES', 'الشعار والبطاقة ليسا في جهتيهما');
      // التكوين متماثل: مركزا الشعار والبطاقة على بُعد واحد من منتصف الشاشة
      const dArt = Math.abs(artMid - vw / 2), dCard = Math.abs(cardMid - vw / 2);
      if (Math.abs(dArt - dCard) > 2) F('SYMMETRY', 'الشعار على ' + Math.round(dArt) + 'px والبطاقة على ' + Math.round(dCard) + 'px من المنتصف');
      // متجاوران لا متلاصقان ولا متباعدان إلى الأطراف
      const gap = rtl ? art.left - cr.right : cr.left - art.right;
      info.gap = Math.round(gap);
      if (gap < 40) F('GAP-TIGHT', 'المسافة بين الشعار والبطاقة ' + Math.round(gap) + 'px');
      if (gap > 260) F('GAP-WIDE', 'المسافة بين الشعار والبطاقة ' + Math.round(gap) + 'px');
      // الشعار لا يطغى على البطاقة
      const ratio2 = (art.right - art.left) / cr.width;
      if (ratio2 > 1.25) F('ART-DOMINANT', 'الشعار ' + ratio2.toFixed(2) + '× عرض البطاقة');
    }
    // البطاقة داخل النافذة، وغير مقصوصة من الأعلى
    if (cr.left < -.5 || cr.right > vw + .5) F('CARD-OUT', Math.round(cr.left) + '..' + Math.round(cr.right));
    if (cr.top + scrollY < -.5) F('CARD-CLIPPED', 'أعلى البطاقة عند ' + Math.round(cr.top + scrollY));
    info.cardTop = Math.round(cr.top); info.cardBottom = Math.round(cr.bottom);

    // ٩) العناصر الثابتة (مبدّل اللغة، «ثبّت التطبيق»…): لا تركب البطاقة،
    //    ولا الشعار، ولا تغطّي عنصراً تفاعلياً، ولا تخرج عن النافذة.
    const fixedEls = [...document.body.querySelectorAll('*')].filter(e => {
      if (e === document.body || e.closest('section')) return false;
      const cs = getComputedStyle(e);
      return cs.position === 'fixed' && shown(e);
    });
    const hit = (a, b) => !(a.right < b.left || a.left > b.right || a.bottom < b.top || a.top > b.bottom);
    const nameOf = e => e.id || e.className.toString().slice(0, 20) || e.tagName;
    info.fixed = fixedEls.map(nameOf);
    fixedEls.forEach(fx => {
      const r = rect(fx);
      if (r.left < -.5 || r.right > vw + .5 || r.top < -.5 || r.bottom > vh + .5) F('FIXED-OUT', nameOf(fx) + ' خارج النافذة');
      if (hit(r, cr)) F('FIXED-ON-CARD', nameOf(fx) + ' يركب البطاقة');
      if (art && hit(r, art)) F('FIXED-ON-ART', nameOf(fx) + ' يركب الشعار');
      section.querySelectorAll('input, button, a.btn, a[href]').forEach(e => {
        if (!shown(e)) return;
        if (hit(r, rect(e))) F('FIXED-OVERLAP', nameOf(fx) + ' يغطّي ' + (e.id || e.className.toString().slice(0, 30) || e.tagName));
      });
    });
    // العناصر الثابتة لا تركب بعضها
    for (let i = 0; i < fixedEls.length; i++)
      for (let j = i + 1; j < fixedEls.length; j++)
        if (hit(rect(fixedEls[i]), rect(fixedEls[j]))) F('FIXED-ON-FIXED', nameOf(fixedEls[i]) + ' × ' + nameOf(fixedEls[j]));

    // ١٠) الخط الأساسي
    info.h4Font = h4 ? px(getComputedStyle(h4).fontSize) : null;
    info.cardW = Math.round(cr.width);
    return {fails, info};
  };
})();
