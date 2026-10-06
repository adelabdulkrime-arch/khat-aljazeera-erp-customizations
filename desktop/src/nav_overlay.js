// أزرار التنقّل داخل نافذة التطبيق.
//
// نافذة Electron بلا شريط متصفح، فالمستخدم يفقد الرجوع والأمام. أضفنا قائمة
// «تنقّل» واختصارات وأزرار فأرة — لكن القائمة مخفية خلف Alt، والاختصارات لا
// يعرفها أحد ما لم يُخبَر. فالنتيجة أن من يفتح التطبيق لأول مرة لا يجد وسيلة
// ظاهرة للرجوع، وهي أول ما يبحث عنه.
//
// هذا الملف يُحقن في كل صفحة يحمّلها التطبيق (عبر did-finish-load) ويضع
// زرَّين صغيرين ثابتين. لا يلمس صفحة النظام ولا يعدّل عناصرها — يضيف طبقة
// فوقها، فإن تغيّر النظام لاحقاً لا ينكسر شيء.
//
// يُحقن داخل سياق الصفحة، فلا يملك require ولا وصولاً لـNode: يتواصل مع
// العملية الرئيسية بوسم على الصفحة يراقبه main.js.

(function () {
  'use strict';

  // حقنة لاحقة على صفحة سبق تجهيزها: لا نُعيد تركيب كل شيء، لكن نتأكد أن
  // الشريط ما زال موجوداً — صفحة النظام تُعيد بناء DOM بعد التحميل وقد تمسحه.
  // (نسخة أولى كانت تعود هنا فوراً، فإن مُسح الشريط لم يُعَد أبداً.)
  if (window.__khatNavReady) {
    if (typeof window.__khatNavBuild === 'function') window.__khatNavBuild();
    return;
  }
  window.__khatNavReady = true;

  var BACK = 'khat-nav-back';
  var FWD = 'khat-nav-forward';

  function icon(d) {
    return (
      '<svg viewBox="0 0 24 24" width="17" height="17" fill="none" ' +
      'stroke="currentColor" stroke-width="2.2" stroke-linecap="round" ' +
      'stroke-linejoin="round"><path d="' + d + '"/></svg>'
    );
  }

  function build() {
    if (document.getElementById('khat-nav')) return;
    if (!document.body) return;

    var bar = document.createElement('div');
    bar.id = 'khat-nav';

    // في RTL: الرجوع سهم يمين، الأمام سهم يسار — موافقاً لاتجاه القراءة.
    var back = document.createElement('button');
    back.className = 'khat-nav-btn';
    back.id = BACK;
    back.title = 'رجوع  (Alt+→)';
    back.setAttribute('aria-label', 'رجوع');
    back.innerHTML = icon('M9 18l6-6-6-6');

    var fwd = document.createElement('button');
    fwd.className = 'khat-nav-btn';
    fwd.id = FWD;
    fwd.title = 'أمام  (Alt+←)';
    fwd.setAttribute('aria-label', 'أمام');
    fwd.innerHTML = icon('M15 18l-6-6 6-6');

    // السياق معزول عن Node، فلا سبيل لاستدعاء واجهات Electron مباشرة. نُبلّغ
    // العملية الرئيسية بتغيير عنوان الصفحة لحظياً إلى وسم متفق عليه: حدث
    // page-title-updated يصلها فوراً، ثم نُعيد العنوان كما كان.
    function signal(cmd) {
      var prev = document.title;
      document.title = '__khat_nav_' + cmd + '__';
      setTimeout(function () { document.title = prev; }, 0);
    }
    back.addEventListener('click', function () { signal('back'); });
    fwd.addEventListener('click', function () { signal('forward'); });

    bar.appendChild(back);
    bar.appendChild(fwd);

    var css = document.createElement('style');
    css.textContent = [
      '#khat-nav{position:fixed;top:8px;inset-inline-start:10px;z-index:2147483000;',
      'display:flex;gap:4px;direction:rtl;}',
      '.khat-nav-btn{width:30px;height:30px;display:flex;align-items:center;',
      'justify-content:center;border:0;border-radius:8px;cursor:pointer;',
      'background:rgba(127,127,127,.14);color:#9aa5b6;padding:0;',
      'transition:background .15s,color .15s,opacity .15s;}',
      '.khat-nav-btn:hover:not(:disabled){background:rgba(127,127,127,.26);color:#f0b429;}',
      '.khat-nav-btn:disabled{opacity:.3;cursor:default;}',
      '.khat-nav-btn:focus-visible{outline:2px solid #f0b429;outline-offset:2px;}',
    ].join('');

    document.head.appendChild(css);
    document.body.appendChild(bar);
  }

  // تعطيل الزر حين لا يوجد تاريخ في اتجاهه — زر يبدو فعّالاً ولا يفعل شيئاً
  // أسوأ من زر معطّل بوضوح. القيم تصل من العملية الرئيسية.
  // مكشوفة ليستدعيها الحقن اللاحق ويعيد تركيب الشريط إن مُسح.
  window.__khatNavBuild = build;

  window.__khatNavState = function (canBack, canFwd) {
    var b = document.getElementById(BACK);
    var f = document.getElementById(FWD);
    if (b) b.disabled = !canBack;
    if (f) f.disabled = !canFwd;
  };

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', build);
  } else {
    build();
  }

  // صفحات النظام تُعيد بناء DOM عند التنقّل الداخلي، فنتأكد أن الشريط باقٍ.
  new MutationObserver(function () {
    if (!document.getElementById('khat-nav')) build();
  }).observe(document.documentElement, { childList: true, subtree: true });
})();
