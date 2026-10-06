// مبدّل اللغة على صفحة الدخول.
//
// صفحة الدخول تُقدَّم قبل أن يُعرف المستخدم، فلا يمكنها قراءة تفضيله من حسابه.
// Frappe يبني الصفحة بلغة الموقع (ar هنا)، لكن لا يعرض أي وسيلة لتغييرها —
// فمن يفضّل الإنجليزية، أو من يجد الصفحة بلغة لا يقرؤها، يعلق بلا مخرج.
//
// الحل: زر يضبط كوكي `preferred_language` الذي يقرأه Frappe عند تقديم الصفحة،
// ثم يعيد التحميل. بعد الدخول تتولّى لغة الحساب نفسه الأمر.

(function () {
  'use strict';

  // صفحات الدخول/التسجيل فقط — لا نُقحم الزر داخل النظام، فهناك تبديل اللغة
  // متاح من إعدادات المستخدم.
  var path = window.location.pathname;
  if (!/^\/(login|update-password)/.test(path)) return;

  var LANGS = [
    { code: 'ar', label: 'العربية' },
    { code: 'en', label: 'English' },
  ];

  function currentLang() {
    var m = document.cookie.match(/(?:^|;\s*)preferred_language=([^;]+)/);
    if (m) return decodeURIComponent(m[1]);
    return (document.documentElement.getAttribute('lang') || 'ar').slice(0, 2);
  }

  function setLang(code) {
    // سنة كاملة، ومسار الجذر ليشمل الصفحة والنظام معاً.
    document.cookie =
      'preferred_language=' + encodeURIComponent(code) + ';path=/;max-age=31536000';
    window.location.reload();
  }

  // بعض نصوص صفحة الدخول يبنيها جافاسكربت بعد تحميل قاموس الترجمة، فتبقى
  // إنجليزية مهما أضفنا للقاموس. هذه هي البقية التي رصدناها على الصفحة
  // المعروضة فعلاً — تُترجَم هنا بعد أن يبنيها Frappe.
  var LATE_STRINGS = {
    'Email or Username': 'البريد الإلكتروني أو اسم المستخدم',
    'Forgot password?': 'نسيت كلمة السر؟',
    'Send Link': 'إرسال الرابط',
    'Back to sign in': 'العودة لتسجيل الدخول',
    'Resend': 'إعادة الإرسال',
    'Login with password': 'الدخول بكلمة السر',
  };

  function translateLate() {
    // عربية فقط — في الإنجليزية النص الأصلي هو الصحيح.
    if (currentLang() !== 'ar') return;
    document.querySelectorAll('label, a, button').forEach(function (el) {
      if (el.closest('#khat-lang-switch')) return;      // لا نترجم زرَّي اللغة
      if (el.children.length) return;                    // نص مباشر فقط
      var t = (el.textContent || '').trim();
      if (LATE_STRINGS[t]) el.textContent = LATE_STRINGS[t];
    });
  }

  function build() {
    if (document.getElementById('khat-lang-switch')) return;

    var active = currentLang();
    var wrap = document.createElement('div');
    wrap.id = 'khat-lang-switch';
    wrap.setAttribute('role', 'group');
    wrap.setAttribute('aria-label', 'Language / اللغة');

    LANGS.forEach(function (l, i) {
      var b = document.createElement('button');
      b.type = 'button';
      b.textContent = l.label;
      b.lang = l.code;
      b.className = 'khat-lang-btn' + (l.code === active ? ' is-active' : '');
      b.setAttribute('aria-pressed', String(l.code === active));
      // لا تُعد التحميل بلا داعٍ إن كانت اللغة مختارة أصلاً.
      b.addEventListener('click', function () {
        if (l.code !== active) setLang(l.code);
      });
      wrap.appendChild(b);
      if (i === 0) {
        var sep = document.createElement('span');
        sep.className = 'khat-lang-sep';
        sep.setAttribute('aria-hidden', 'true');
        sep.textContent = '·';
        wrap.appendChild(sep);
      }
    });

    var css = document.createElement('style');
    css.textContent = [
      '#khat-lang-switch{position:fixed;top:14px;inset-inline-end:16px;z-index:2147483000;',
      'display:flex;align-items:center;gap:6px;font-size:13px;',
      'font-family:system-ui,"Segoe UI",Tahoma,sans-serif;direction:ltr}',
      '.khat-lang-btn{background:none;border:0;padding:4px 8px;border-radius:6px;cursor:pointer;',
      'color:#64748b;font:inherit;line-height:1.4;transition:color .15s,background .15s}',
      '.khat-lang-btn:hover{color:#1a2b4a;background:rgba(26,43,74,.06)}',
      '.khat-lang-btn.is-active{color:#1a2b4a;font-weight:600}',
      '.khat-lang-btn:focus-visible{outline:2px solid #f0b429;outline-offset:2px}',
      '.khat-lang-sep{color:#cbd5e1}',
      // الوضع الداكن يتبع تفضيل الجهاز، فالزر يبقى مقروءاً في الحالتين.
      '@media (prefers-color-scheme:dark){',
      '.khat-lang-btn{color:#94a3b8}',
      '.khat-lang-btn:hover{color:#e8edf7;background:rgba(255,255,255,.08)}',
      '.khat-lang-btn.is-active{color:#f0b429}',
      '.khat-lang-sep{color:#475569}}',
    ].join('');

    document.head.appendChild(css);
    document.body.appendChild(wrap);
  }

  function start() {
    build();
    translateLate();

    // الصفحة تبدّل نماذجها دون إعادة تحميل (نسيت كلمة السر، الدخول برابط
    // بريد)، وكل تبديل يبني نصوصاً جديدة — فنترجم عند كل تغيير في DOM بدل
    // مرة واحدة عند التحميل. مؤجَّل بإطار واحد حتى لا نتسابق مع البناء نفسه.
    var pending = false;
    new MutationObserver(function () {
      if (pending) return;
      pending = true;
      requestAnimationFrame(function () {
        pending = false;
        translateLate();
      });
    }).observe(document.body, { childList: true, subtree: true });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', start);
  } else {
    start();
  }
})();
