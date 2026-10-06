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
    // شاشتا «نسيت كلمة المرور» و«الدخول برابط البريد»: تُبنيان بجافاسكربت بعد
    // تحميل قاموس الترجمة، فتبقى نصوصهما إنجليزية مهما أُضيف للقاموس. رُصدت
    // على الشاشة المعروضة فعلاً.
    'Please check your email.': 'تفقّد بريدك الإلكتروني.',
    'Please check your email': 'تفقّد بريدك الإلكتروني',
    "Didn't receive the link?": 'لم يصلك الرابط؟',
    "Didn't receive the link": 'لم يصلك الرابط',
    'Email is required.': 'البريد الإلكتروني مطلوب.',
    'Email is required': 'البريد الإلكتروني مطلوب',
    'Password is required.': 'كلمة السر مطلوبة.',
    'Password is required': 'كلمة السر مطلوبة',
    "Please enter your email, we'll send you password reset link":
      'أدخل بريدك الإلكتروني وسنرسل لك رابط إعادة تعيين كلمة السر',
    'Invalid login credentials': 'بيانات دخول غير صحيحة',
    'Email': 'البريد الإلكتروني',
    'Sent': 'أُرسل',
    'Submit': 'إرسال',
    'Verify': 'تحقّق',
  };

  function translateLate() {
    // عربية فقط — في الإنجليزية النص الأصلي هو الصحيح.
    if (currentLang() !== 'ar') return;

    // الوسوم موسّعة: رسائل مثل "Please check your email" و"Email is required"
    // تظهر في div/p/span لا في label أو button، فالاقتصار على الثلاثة الأولى
    // كان يتركها إنجليزية.
    var SEL = 'label, a, button, div, p, span, small, h1, h2, h3, h4';
    document.querySelectorAll(SEL).forEach(function (el) {
      if (el.closest('#khat-lang-switch')) return;      // لا نترجم زرَّي اللغة
      if (el.children.length) return;                    // نص مباشر فقط
      var t = (el.textContent || '').trim();
      if (!t || t.length > 90) return;
      if (LATE_STRINGS[t]) { el.textContent = LATE_STRINGS[t]; return; }
      // بعض الرسائل تأتي بنقطة أو بدونها حسب السياق، فنجرّب الشكلين بدل
      // إضافة كل تنويعة يدوياً.
      var bare = t.replace(/[.!]$/, '');
      if (LATE_STRINGS[bare]) el.textContent = LATE_STRINGS[bare] + t.slice(bare.length);
    });

    // النصوص الإرشادية داخل الحقول.
    document.querySelectorAll('input[placeholder]').forEach(function (el) {
      var p = (el.placeholder || '').trim();
      if (LATE_STRINGS[p]) el.placeholder = LATE_STRINGS[p];
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
      // سطح داكن شبه شفاف خلف الزرّين: صفحة الدخول صارت تحمل صورة خلفية،
      // فألوان النص وحدها لم تعد تضمن تبايناً — كان زر «English» يختفي تماماً
      // فوق الجزء الفاتح من الشعار. السطح يجعلهما مقروءين فوق أي خلفية،
      // داكنة كانت أو فاتحة، فتسقط الحاجة لقواعد وضع داكن منفصلة.
      '#khat-lang-switch{position:fixed;top:14px;inset-inline-end:16px;z-index:2147483000;',
      'display:flex;align-items:center;gap:4px;font-size:13px;',
      'background:rgba(16,26,46,.72);backdrop-filter:blur(6px);',
      'padding:4px 8px;border-radius:999px;',
      'font-family:system-ui,"Segoe UI",Tahoma,sans-serif;direction:ltr}',
      '.khat-lang-btn{background:none;border:0;padding:3px 9px;border-radius:999px;cursor:pointer;',
      'color:rgba(255,255,255,.72);font:inherit;line-height:1.4;',
      'transition:color .15s,background .15s}',
      '.khat-lang-btn:hover{color:#fff;background:rgba(255,255,255,.14)}',
      '.khat-lang-btn.is-active{color:#f0b429;font-weight:700}',
      '.khat-lang-btn:focus-visible{outline:2px solid #f0b429;outline-offset:2px}',
      '.khat-lang-sep{color:rgba(255,255,255,.3)}',
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
