# -*- coding: utf-8 -*-
"""Rebuild the 'Home' workspace to match Mazoon ERP's landing page: 6 big
module tiles (Workshop, Sales, Purchases, Stock, Accounting, General Settings)
+ a Latest Updates tile. Reuses ERPNext's own native modules (Selling, Buying,
Stock, Invoicing already ship with ERPNext) — we only add the landing tiles."""
import json
import frappe
from khat_workshop.setup.workshop_futuristic import FUTURISTIC_CSS, FUTURISTIC_JS

HOME_BLOCK_NAME = "Home Dashboard Tiles"

# (label, route_csv, icon, description, gradient) — modern card per module
HOME_TILES = [
    ("ورشة صيانة السيارات", "workshop", "wrench", "بطاقات العمل والفنيون والصيانة", "linear-gradient(135deg,#16304d,#8b1a1f)"),
    ("المبيعات", "sales-dashboard", "shopping-cart", "الفواتير والعملاء ونقاط البيع", "linear-gradient(135deg,#1f9d55,#27c06b)"),
    ("المشتريات", "purchasing-dashboard", "package-plus", "الموردون وأوامر الشراء", "linear-gradient(135deg,#e67e22,#f39c12)"),
    ("المخزون", "inventory-dashboard", "layout-grid", "المنتجات والمستودعات والجرد", "linear-gradient(135deg,#8e44ad,#a55eea)"),
    ("المحاسبة", "accounting-dashboard", "receipt", "القيود والتقارير المالية", "linear-gradient(135deg,#2d6cdf,#4a90e2)"),
    ("الإعدادات العامة", "general-settings", "settings", "المستخدمون والأدوار والإعدادات", "linear-gradient(135deg,#5b6472,#7c8697)"),
]

LATEST_UPDATES_TILE = ("آخر التحديثات", "List,Notification Log", "bell", "الإشعارات وآخر المستجدات", "linear-gradient(135deg,#c0392b,#e63946)")


def _home_tiles_html():
    cells = []
    for label, route_csv, icon, desc, grad in HOME_TILES + [LATEST_UPDATES_TILE]:
        cells.append(
            '<a class="hm-card" href="#" data-route="%s">'
            '<span class="hm-icon" style="background:%s;">'
            '<svg class="icon"><use href="#icon-%s"></use></svg></span>'
            '<span class="hm-text">'
            '<span class="hm-title" data-i18n="%s">%s</span>'
            '<span class="hm-desc" data-i18n="%s">%s</span>'
            '</span>'
            # chevron-right دائماً، ويُقلب بـCSS في RTL. كان chevron-left
            # ثابتاً فيشير للخارج خطأً في الإنجليزية.
            '<svg class="icon hm-arrow"><use href="#icon-chevron-right"></use></svg>'
            '</a>'
            % (route_csv, grad, icon,
               frappe.utils.escape_html(label), label,
               frappe.utils.escape_html(desc), desc)
        )
    return '<div class="hm-grid" id="hm-modules">' + "".join(cells) + '</div>'


HOME_STYLE = """
/* بلا direction ثابت: الكتلة ترث اتجاه <html> الذي يضبطه الإطار من لغة
   المستخدم. كانت direction:rtl هنا تُبقي البطاقات معكوسة في الإنجليزية. */
.hm-wrap { }
/* ---- Welcome header ---- */
.hm-header { background:linear-gradient(120deg,#16304d 0%,#1e3a5f 55%,#7a1a1f 100%);
  border-radius:18px; padding:26px 30px; color:#fff; margin-bottom:24px;
  display:flex; justify-content:space-between; align-items:center; gap:20px;
  box-shadow:0 10px 30px rgba(22,48,77,.22); position:relative; overflow:hidden; }
.hm-header::after { content:""; position:absolute; inset-inline-start:-40px; top:-40px;
  width:220px; height:220px; border-radius:50%; background:rgba(255,255,255,.06); }
.hm-hello { font-size:22px; font-weight:800; margin:0; letter-spacing:-.2px; }
.hm-sub { font-size:13.5px; opacity:.85; margin-top:6px; }
.hm-logo { height:66px; width:auto; background:#fff; border-radius:14px; padding:6px; flex-shrink:0; }
/* ---- Section title ---- */
.hm-sectitle { font-size:14px; font-weight:700; color:var(--text-color,#1a2b4a);
  letter-spacing:.15px; text-transform:uppercase;
  margin:4px 0 14px; display:flex; align-items:center; gap:8px; }
.hm-sectitle::before { content:""; width:4px; height:18px; background:#e63946; border-radius:3px; }
/* ---- عنوان قسم قابل للطي ----
   القسم يُطوى بالنقر على عنوانه. زرّ لا <div> لتعمل لوحة المفاتيح
   (Tab ثم Enter) ويقرأه قارئ الشاشة، وaria-expanded يعلن الحالة. */
button.hm-sectitle { width:100%; background:none; border:0; padding:0;
  cursor:pointer; text-align:start; font-family:inherit; }
button.hm-sectitle:hover { color:#e63946; }
button.hm-sectitle:focus-visible { outline:2px solid #e63946; outline-offset:3px; border-radius:4px; }
.hm-sectoggle { margin-inline-start:auto; display:flex; align-items:center;
  color:var(--text-muted,#8a94a6); transition:transform .2s cubic-bezier(.2,.8,.2,1); }
.hm-sectoggle .icon { width:16px; height:16px; }
button.hm-sectitle[aria-expanded="false"] .hm-sectoggle { transform:rotate(-90deg); }
/* الطيّ: display:none لا ارتفاع صفري — المحتوى شبكة متغيّرة الارتفاع،
   فانتقال الارتفاع عليها يحتاج قياساً بجافاسكربت بلا مقابل بصري يُذكر. */
.hm-collapsed { display:none !important; }
/* ---- Stat tiles ----
   بطاقات مؤشرات صغيرة: الرقم أولاً وبحجم كبير لأنه ما يُقرأ من مسافة، ثم
   التسمية. auto-fit حتى تنقص الأعمدة على الشاشة الضيقة بدل أن تُضغط البطاقة.
   البطاقة كلها رابط لقائمة مفلترة — رقمٌ لا يمكن النقر عليه يترك المستخدم
   يبحث عن مصدره يدوياً. */
/* auto-fill لا auto-fit: مع ستّ بطاقات كان auto-fit يمدّدها حتى تتسع خمسٌ في
   الصف وتبقى السادسة وحدها في صف تالٍ — شكل غير متوازن. auto-fill يحافظ على
   عرض ثابت للبطاقة فتنتظم ثلاثاً ثلاثاً أو اثنتين اثنتين حسب الشاشة. */
/* قواعد بطاقات «نظرة سريعة» حُذفت مع القسم نفسه. تنسيق .hm-stat الباقي
   يخصّ بطاقة العميل وحدها ومكتوب تحت .hm-profile-stats أدناه. */
/* ---- Module cards grid ---- */
@keyframes kajFadeUp { from { opacity:0; transform:translateY(10px); } to { opacity:1; transform:translateY(0); } }
/* auto-fit بدل repeat(3,1fr): ثلاثة أعمدة ثابتة كانت تُضغط على الشاشات
   الأضيق حتى تلتف عناوين البطاقات على سطرين ("ورشة صيانة / السيارات")
   وتُبتر أوصافها. الآن ينقص عدد الأعمدة تلقائياً بدل أن تضيق البطاقة، فتبقى
   مقروءة على الشاشة الصغيرة والجوال — وهو ما يستخدمه فنيّو الورشة فعلاً. */
.hm-grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(300px,1fr)); gap:16px; }
.hm-card { display:flex; align-items:center; gap:15px; background:var(--card-bg,#fff);
  border:1px solid var(--border-color,#eef0f4); border-radius:16px; padding:20px 22px;
  text-decoration:none !important; cursor:pointer; min-height:88px;
  box-shadow:0 1px 3px rgba(16,30,54,.06);
  animation:kajFadeUp .45s cubic-bezier(.2,.8,.2,1) backwards;
  transition:transform .22s cubic-bezier(.2,.8,.2,1), box-shadow .22s, border-color .22s; }
.hm-card:hover { transform:translateY(-4px); box-shadow:0 10px 24px rgba(16,30,54,.12); border-color:#dfe3ea; }
.hm-grid > .hm-card:nth-child(1){ animation-delay:.02s; } .hm-grid > .hm-card:nth-child(2){ animation-delay:.06s; }
.hm-grid > .hm-card:nth-child(3){ animation-delay:.10s; } .hm-grid > .hm-card:nth-child(4){ animation-delay:.14s; }
.hm-grid > .hm-card:nth-child(5){ animation-delay:.18s; } .hm-grid > .hm-card:nth-child(6){ animation-delay:.22s; }
.hm-grid > .hm-card:nth-child(7){ animation-delay:.26s; }
.hm-icon { width:56px; height:56px; border-radius:15px; flex-shrink:0;
  display:flex; align-items:center; justify-content:center; box-shadow:0 6px 16px rgba(0,0,0,.14); }
.hm-icon .icon { width:26px; height:26px; color:#fff; }
.hm-icon svg use { stroke:#fff; }
.hm-text { display:flex; flex-direction:column; flex:1; min-width:0; }
/* العنوان يلتف ولا يُقص: محاولة أولى ثبّتته على سطر واحد (nowrap + ellipsis)
   فصار "ورشة صيانة السيـ…" — وقصُّ اسم الوحدة أسوأ من التفافه، لأن المستخدم
   يفقد معرفة ما تفتحه البطاقة. السطران مقبولان، والمهم أن تتساوى البطاقات:
   align-items:center في .hm-card يتكفّل بذلك. */
.hm-title { font-size:16px; font-weight:700; color:var(--text-color,#1a2b4a);
  line-height:1.35; overflow-wrap:break-word; }
/* الوصف يُسمح له بسطرين ثم يُقص — أطول من ذلك يُخرج البطاقات عن تساويها. */
.hm-desc { font-size:12.5px; color:var(--text-muted,#8a94a6); margin-top:3px;
  display:-webkit-box; -webkit-line-clamp:2; -webkit-box-orient:vertical;
  overflow:hidden; }
/* السهم يشير دائماً «للأمام» في اتجاه القراءة: يميناً في LTR ويساراً في
   RTL. الرمز chevron-right ويُقلب أفقياً في RTL، والحركة عند المرور تتبع
   نفس الاتجاه — كانت translateX(-4px) ثابتة فتتحرّك للخلف في الإنجليزية. */
.hm-arrow { width:18px; height:18px; color:var(--text-muted,#c4ccd8);
  flex-shrink:0; transition:transform .2s; }
[dir="rtl"] .hm-arrow { transform:scaleX(-1); }
.hm-card:hover .hm-arrow { transform:translateX(4px); color:#e63946; }
[dir="rtl"] .hm-card:hover .hm-arrow { transform:scaleX(-1) translateX(4px); }
/* ---- Tablet & phone (touch-friendly) ---- */
@media (max-width:1024px){
  .hm-grid{ grid-template-columns:repeat(2,1fr); gap:14px; }
  .hm-card{ min-height:92px; padding:20px; }
  .hm-header{ padding:22px; }
}
@media (max-width:640px){
  .hm-grid{ grid-template-columns:1fr; }
  .hm-header{ flex-direction:column; text-align:center; }
  .hm-hello{ font-size:19px; }
}
/* ---- Quick search by phone number ---- */
.hm-search-box { background:var(--card-bg,#fff); border:1px solid var(--border-color,#eef0f4);
  border-radius:16px; padding:18px 20px; margin-bottom:22px; box-shadow:0 1px 3px rgba(16,30,54,.06); position:relative; }
.hm-search-title { font-size:14px; font-weight:700; color:var(--text-color,#1a2b4a); margin-bottom:10px;
  display:flex; align-items:center; gap:8px; }
.hm-search-title .icon { width:16px; height:16px; color:#e63946; }
.hm-search-row { display:flex; gap:10px; }
.hm-search-input { flex:1; border:1px solid var(--border-color,#e5e7eb); border-radius:10px;
  padding:11px 14px; font-size:14px; outline:none; background:var(--control-bg,#fff);
  color:var(--text-color);
  /* أرقام الجوال واللوحة تُكتب يساراً-ليميناً في اللغتين، لكن محاذاة النص
     تتبع اتجاه الصفحة: text-align:right كانت تدفعه للحافة الخطأ في
     الإنجليزية. start يحاذيه لبداية السطر في الاتجاهين. */
  direction:ltr; text-align:start; }
.hm-search-input:focus { border-color:#e63946; box-shadow:0 0 0 3px rgba(230,57,70,.10); }
.hm-search-btn { border:none; background:linear-gradient(135deg,#c0392b,#e63946); color:#fff;
  padding:0 22px; border-radius:10px; font-size:14px; font-weight:700; cursor:pointer;
  display:flex; align-items:center; gap:6px; box-shadow:0 6px 16px rgba(230,57,70,.24); }
.hm-search-btn:hover { box-shadow:0 8px 20px rgba(230,57,70,.32); }
.hm-search-btn .icon { width:15px; height:15px; }
.hm-search-results { margin-top:10px; }
.hm-search-res { padding:9px 12px; font-size:13.5px; cursor:pointer; border-radius:8px;
  display:flex; justify-content:space-between; gap:10px; }
.hm-search-res:hover { background:var(--bg-light-gray,#f5f7fa); }
.hm-search-res-phone { color:var(--text-muted,#8a94a6); direction:ltr; }
.hm-search-empty { padding:10px 12px; font-size:13px; color:var(--text-muted,#8a94a6); }
.hm-profile-loading { padding:14px 0; font-size:13px; color:var(--text-muted,#8a94a6); }
.hm-customer-profile { margin-top:14px; border-top:1px solid var(--border-color,#eef0f4); padding-top:14px; }
.hm-profile-head { display:flex; align-items:center; justify-content:space-between; gap:10px; flex-wrap:wrap; margin-bottom:12px; }
.hm-profile-name { font-size:16px; font-weight:700; color:var(--text-color,#1a2b4a); }
.hm-profile-phone { font-size:13px; color:var(--text-muted,#8a94a6); direction:ltr; margin-inline-start:8px; }
.hm-profile-open { font-size:12.5px; color:#e63946; font-weight:700; text-decoration:none; cursor:pointer; }
.hm-profile-stats { display:grid; grid-template-columns:repeat(4,1fr); gap:10px; margin-bottom:16px; }
/* محصورة داخل بطاقة العميل: .hm-stat يستخدمه هذا القسم وحده الآن، لكن
   النطاق يبقى صريحاً حتى لا يتسرّب التنسيق إن أُضيفت بطاقات أخرى لاحقاً. */
.hm-profile-stats .hm-stat { background:var(--bg-light-gray,#f8f9fb); border:0;
  border-radius:10px; padding:10px 8px; text-align:center; box-shadow:none; }
.hm-profile-stats .hm-stat::before { display:none; }
.hm-profile-stats .hm-stat-val { display:block; font-size:15px; font-weight:800; color:var(--text-color,#1a2b4a); font-variant-numeric:tabular-nums; }
.hm-profile-stats .hm-stat-lbl { display:block; font-size:11px; color:var(--text-muted,#8a94a6); margin-top:3px; }
.hm-profile-stats .hm-stat-danger .hm-stat-val { color:#e63946; }
.hm-profile-section-title { font-size:12.5px; font-weight:700; color:var(--text-muted,#8a94a6); margin:12px 0 6px; }
.hm-profile-chips { display:flex; flex-wrap:wrap; gap:6px; }
.hm-chip { background:var(--bg-light-gray,#f5f7fa); border:1px solid var(--border-color,#eef0f4);
  border-radius:8px; padding:5px 10px; font-size:12px; color:var(--text-color,#1a2b4a); }
.hm-profile-list { display:flex; flex-direction:column; gap:2px; }
.hm-profile-row { display:flex; align-items:center; justify-content:space-between; gap:10px;
  padding:8px 10px; border-radius:8px; cursor:pointer; font-size:13px; }
.hm-profile-row:hover { background:var(--bg-light-gray,#f5f7fa); }
.hm-badge { background:#eef1fb; color:#1a2b4a; border-radius:999px; padding:2px 10px; font-size:11.5px; font-weight:600; }
@media (max-width:640px){
  .hm-profile-stats{ grid-template-columns:repeat(2,1fr); }
  .hm-search-row{ flex-direction:column; }
}
""" + FUTURISTIC_CSS

ICON_SPRITE_JS = r"""
// SVG <use href="#icon-x"> can't resolve across a Shadow DOM boundary — fetch
// a copy of the icon sprite once (cached on window) and inject it locally.
(async function(){
  if(root.querySelector('#wsd-icon-sprite-holder')) return;
  try {
    if(!window.__wsd_icon_sprite_text){
      const resp = await fetch('/assets/frappe/icons/lucide/icons.svg');
      window.__wsd_icon_sprite_text = await resp.text();
    }
    const holder = document.createElement('div');
    holder.id = 'wsd-icon-sprite-holder';
    holder.style.display = 'none';
    holder.innerHTML = window.__wsd_icon_sprite_text;
    root.insertBefore(holder, root.firstChild);
  } catch(e){ console.error('icon sprite inject failed', e); }
})();
"""


HOME_SCRIPT = """
const root = (typeof root_element !== 'undefined' && root_element) ? root_element : document;
""" + ICON_SPRITE_JS + FUTURISTIC_JS + """
function translateAll(){
  root.querySelectorAll('[data-i18n]').forEach(function(el){ el.textContent = __(el.dataset.i18n); });
  root.querySelectorAll('[data-i18n-placeholder]').forEach(function(el){
    el.placeholder = __(el.dataset.i18nPlaceholder);
  });
}
translateAll();

/* ── طيّ الأقسام ──
   عنوان القسم يطوي محتواه ويحفظ الحالة في localStorage، فمن يطوي «الوحدات
   الرئيسية» يجدها مطويّة في الزيارة القادمة بدل أن يطويها كل مرة.
   localStorage قد يرمي في وضع التصفّح الخاص، فكل وصول إليه محمي. */
(function(){
  var KEY = 'kaj_home_collapsed';

  function readState(){
    try { return JSON.parse(localStorage.getItem(KEY) || '{}') || {}; }
    catch(e){ return {}; }
  }
  function writeState(st){
    try { localStorage.setItem(KEY, JSON.stringify(st)); } catch(e){}
  }

  function apply(btn, open){
    var target = root.querySelector('#' + btn.dataset.collapse);
    if(!target) return;
    btn.setAttribute('aria-expanded', open ? 'true' : 'false');
    target.classList.toggle('hm-collapsed', !open);
  }

  var state = readState();
  root.querySelectorAll('button.hm-sectitle[data-collapse]').forEach(function(btn){
    var id = btn.dataset.collapse;
    /* الافتراضي مفتوح: القسم المخفي افتراضياً يُخفي ميزة لا يعرف المستخدم
       بوجودها. الإخفاء اختيار صريح منه. */
    var open = state[id] !== false;
    apply(btn, open);
    btn.addEventListener('click', function(){
      var nowOpen = btn.getAttribute('aria-expanded') !== 'true';
      apply(btn, nowOpen);
      var st = readState();
      st[id] = nowOpen;
      writeState(st);
    });
  });
})();
// greeting + date + logo
try {
  const nameEl = root.querySelector('.hm-hello-name');
  if(nameEl){
    /* "Administrator" اسم حساب تقني لا اسم شخص، وعرضه في تحية على شاشة
       يفتحها صاحب الورشة كل صباح يقرأ كأن النظام لم يُعدّ بعد. نستبدله
       بمسمّى الدور بالعربية؛ وأي مستخدم حقيقي يظهر باسمه كما هو. */
    let who = frappe.session.user_fullname || frappe.session.user || '';
    if(who === 'Administrator' || frappe.session.user === 'Administrator'){
      who = __('مدير النظام');
    }
    nameEl.textContent = who;
  }
  const dateEl = root.querySelector('.hm-date');
  if(dateEl){ dateEl.textContent = frappe.datetime.str_to_user(frappe.datetime.now_date()); }
  const logoEl = root.querySelector('.hm-logo');
  if(logoEl){
    // Resolve the logo from Website Settings. The old code fell back to a
    // hardcoded /files/kaj-logo<hash>.png that only ever existed on the
    // original dev machine, so every fresh deploy rendered a broken image.
    // Now: show the configured logo, or show nothing at all.
    const lg = (frappe.boot && frappe.boot.website_settings && frappe.boot.website_settings.app_logo)
      || (frappe.boot && frappe.boot.app_logo_url) || '';
    if(lg){ logoEl.src = lg; logoEl.style.display = ''; }
    else { logoEl.style.display = 'none'; }
  }
} catch(e){ console.error(e); }
root.querySelectorAll('.hm-card').forEach(function(a){
  a.addEventListener('click', function(e){
    e.preventDefault();
    frappe.set_route.apply(frappe, a.dataset.route.split(','));
  });
});

// ---- Quick search by phone number -> full customer profile ----
(function(){
  const input = root.querySelector('.hm-search-input');
  const btn = root.querySelector('.hm-search-btn');
  const resultsEl = root.querySelector('.hm-search-results');
  const profileEl = root.querySelector('.hm-customer-profile');
  if(!input || !btn || !resultsEl || !profileEl) return;

  function fmt(v){
    try { return frappe.format_currency(v || 0); } catch(e){ return (v || 0); }
  }

  async function showProfile(customer){
    resultsEl.innerHTML = '';
    profileEl.style.display = 'block';
    profileEl.innerHTML = '<div class="hm-profile-loading">' + __('جاري التحميل...') + '</div>';
    try {
      const [vehicles, workCards, invoices] = await Promise.all([
        frappe.db.get_list('Customer Vehicle', { filters: { customer: customer.name }, fields: ['name', 'plate_number', 'brand', 'model'], limit: 20 }),
        frappe.db.get_list('Work Card', { filters: { customer: customer.name }, fields: ['name', 'status', 'entry_date', 'plate_number'], order_by: 'creation desc', limit: 5 }),
        frappe.db.get_list('Sales Invoice', { filters: { customer: customer.name }, fields: ['name', 'grand_total', 'outstanding_amount', 'status', 'posting_date'], order_by: 'creation desc', limit: 10 }),
      ]);
      const totalInvoiced = invoices.reduce(function(s, i){ return s + (i.grand_total || 0); }, 0);
      const totalOutstanding = invoices.reduce(function(s, i){ return s + (i.outstanding_amount || 0); }, 0);
      // Sales Invoice.paid_amount is only reliably populated for POS invoices --
      // for normal credit invoices (paid later via a separate Payment Entry) it
      // stays 0 even once fully paid. grand_total - outstanding_amount is what
      // ERPNext itself treats as "actually paid" regardless of how it was paid.
      const totalPaid = totalInvoiced - totalOutstanding;

      let html = '';
      html += '<div class="hm-profile-head">';
      html += '  <div><span class="hm-profile-name">' + frappe.utils.escape_html(customer.customer_name || customer.name) + '</span>';
      html += '  <span class="hm-profile-phone">' + (customer.mobile_no ? frappe.utils.escape_html(customer.mobile_no) : '') + '</span></div>';
      html += '  <a class="hm-profile-open" data-name="' + encodeURIComponent(customer.name) + '">' + __('فتح ملف العميل') + '</a>';
      html += '</div>';

      html += '<div class="hm-profile-stats">';
      html += '  <div class="hm-stat"><span class="hm-stat-val">' + vehicles.length + '</span><span class="hm-stat-lbl">' + __('المركبات') + '</span></div>';
      html += '  <div class="hm-stat"><span class="hm-stat-val">' + fmt(totalInvoiced) + '</span><span class="hm-stat-lbl">' + __('إجمالي الفواتير') + '</span></div>';
      html += '  <div class="hm-stat"><span class="hm-stat-val">' + fmt(totalPaid) + '</span><span class="hm-stat-lbl">' + __('المدفوع') + '</span></div>';
      html += '  <div class="hm-stat' + (totalOutstanding > 0 ? ' hm-stat-danger' : '') + '"><span class="hm-stat-val">' + fmt(totalOutstanding) + '</span><span class="hm-stat-lbl">' + __('المتبقي') + '</span></div>';
      html += '</div>';

      if(vehicles.length){
        html += '<div class="hm-profile-section-title">' + __('المركبات') + '</div>';
        html += '<div class="hm-profile-chips">' + vehicles.map(function(v){
          return '<span class="hm-chip">' + frappe.utils.escape_html(v.plate_number || v.name) +
            (v.brand ? ' — ' + frappe.utils.escape_html(v.brand) : '') +
            (v.model ? ' ' + frappe.utils.escape_html(v.model) : '') + '</span>';
        }).join('') + '</div>';
      }
      if(workCards.length){
        html += '<div class="hm-profile-section-title">' + __('أحدث بطاقات العمل') + '</div>';
        html += '<div class="hm-profile-list">' + workCards.map(function(w){
          return '<div class="hm-profile-row" data-dt="Work Card" data-name="' + encodeURIComponent(w.name) + '">' +
            '<span>' + w.name + (w.plate_number ? ' · ' + frappe.utils.escape_html(w.plate_number) : '') + '</span>' +
            '<span class="hm-badge">' + frappe.utils.escape_html(w.status || '') + '</span></div>';
        }).join('') + '</div>';
      }
      if(invoices.length){
        html += '<div class="hm-profile-section-title">' + __('الفواتير') + '</div>';
        html += '<div class="hm-profile-list">' + invoices.map(function(i){
          return '<div class="hm-profile-row" data-dt="Sales Invoice" data-name="' + encodeURIComponent(i.name) + '">' +
            '<span>' + i.name + ' · ' + fmt(i.grand_total) + '</span>' +
            '<span class="hm-badge">' + frappe.utils.escape_html(i.status || '') + '</span></div>';
        }).join('') + '</div>';
      }
      if(!vehicles.length && !workCards.length && !invoices.length){
        html += '<div class="hm-search-empty">' + __('لا توجد بيانات إضافية لهذا العميل بعد') + '</div>';
      }
      profileEl.innerHTML = html;

      const openLink = profileEl.querySelector('.hm-profile-open');
      if(openLink) openLink.addEventListener('click', function(e){
        e.preventDefault();
        frappe.set_route('Form', 'Customer', decodeURIComponent(openLink.dataset.name));
      });
      profileEl.querySelectorAll('.hm-profile-row').forEach(function(row){
        row.addEventListener('click', function(){
          frappe.set_route('Form', row.dataset.dt, decodeURIComponent(row.dataset.name));
        });
      });
    } catch(e){ console.error('customer profile', e); }
  }

  async function runSearch(){
    const q = (input.value || '').trim();
    resultsEl.innerHTML = '';
    profileEl.style.display = 'none';
    profileEl.innerHTML = '';
    if(!q) return;
    try {
      const [byPhone, matchingVehicles] = await Promise.all([
        frappe.db.get_list('Customer', {
          filters: [['mobile_no', 'like', '%' + q + '%']],
          fields: ['name', 'customer_name', 'mobile_no'],
          limit: 10,
        }),
        frappe.db.get_list('Customer Vehicle', {
          filters: [['plate_number', 'like', '%' + q + '%']],
          fields: ['name', 'plate_number', 'customer'],
          limit: 10,
        }),
      ]);

      let byPlate = [];
      const vehicleCustomerNames = [...new Set(matchingVehicles.map(function(v){ return v.customer; }).filter(Boolean))];
      if(vehicleCustomerNames.length){
        byPlate = await frappe.db.get_list('Customer', {
          filters: [['name', 'in', vehicleCustomerNames]],
          fields: ['name', 'customer_name', 'mobile_no'],
          limit: 10,
        });
      }

      // merge + dedupe by customer name, keep matched plate number for display
      const plateByCustomer = {};
      matchingVehicles.forEach(function(v){ if(v.customer) plateByCustomer[v.customer] = v.plate_number; });
      const merged = {};
      byPhone.forEach(function(c){ merged[c.name] = Object.assign({}, c, { matchedPlate: null }); });
      byPlate.forEach(function(c){
        merged[c.name] = Object.assign({}, merged[c.name] || c, { matchedPlate: plateByCustomer[c.name] || null });
      });
      const customers = Object.values(merged);

      if(!customers.length){
        resultsEl.innerHTML = '<div class="hm-search-empty">' + __('لا يوجد عميل أو مركبة بهذا الرقم') + '</div>';
        return;
      }
      if(customers.length === 1){
        showProfile(customers[0]);
        return;
      }
      resultsEl.innerHTML = customers.map(function(c){
        return '<div class="hm-search-res" data-name="' + encodeURIComponent(c.name) + '">' +
          '<b>' + frappe.utils.escape_html(c.customer_name || c.name) + '</b>' +
          '<span class="hm-search-res-phone">' + (c.matchedPlate ? frappe.utils.escape_html(c.matchedPlate) : (c.mobile_no ? frappe.utils.escape_html(c.mobile_no) : '')) + '</span></div>';
      }).join('');
      resultsEl.querySelectorAll('.hm-search-res').forEach(function(el){
        el.addEventListener('click', function(){
          const found = customers.find(function(c){ return c.name === decodeURIComponent(el.dataset.name); });
          if(found) showProfile(found);
        });
      });
    } catch(e){ console.error('phone/plate search', e); }
  }

  btn.addEventListener('click', runSearch);
  input.addEventListener('keydown', function(e){ if(e.key === 'Enter'){ e.preventDefault(); runSearch(); } });
})();

"""


def _make_home_block():
    html = (
        # لا dir ثابت: الكتلة كانت تحمل dir="rtl" حرفياً، فتبقى البطاقات
        # معكوسة (الأيقونة يميناً والسهم يساراً) حتى بعد التبديل للإنجليزية —
        # رُصد في الواجهة. بحذفه ترث الكتلة اتجاه <html> الذي يضبطه الإطار من
        # لغة المستخدم، فتصير عربية RTL وإنجليزية LTR تلقائياً.
        '<div class="hm-wrap">'
        '  <div class="hm-header">'
        '    <div>'
        '      <div class="hm-hello"><span data-i18n="أهلاً">أهلاً</span> '
        '        <span class="hm-hello-name"></span></div>'
        '      <div class="hm-sub"><span data-i18n="مرحباً بعودتك إلى نظام خط الجزيرة">'
        'مرحباً بعودتك إلى نظام خط الجزيرة</span> · <span class="hm-date"></span></div>'
        '    </div>'
        # Transparent 1x1 placeholder; the real logo (if any) is set by JS from
        # Website Settings. Avoids a broken-image flash before JS runs.
        '    <img class="hm-logo" style="display:none" alt="logo"'
        ' src="data:image/gif;base64,R0lGODlhAQABAAAAACH5BAEKAAEALAAAAAABAAEAAAICTAEAOw==">'
        '  </div>'
        '  <div class="hm-search-box">'
        '    <div class="hm-search-title"><svg class="icon"><use href="#icon-phone"></use></svg>'
        '      <span data-i18n="بحث سريع بالجوال أو رقم اللوحة">بحث سريع بالجوال أو رقم اللوحة</span></div>'
        '    <div class="hm-search-row">'
        '      <input class="hm-search-input" type="text" data-i18n-placeholder="أدخل رقم الجوال أو رقم لوحة المركبة..." placeholder="أدخل رقم الجوال أو رقم لوحة المركبة...">'
        '      <button class="hm-search-btn"><svg class="icon"><use href="#icon-search"></use></svg>'
        '        <span data-i18n="بحث">بحث</span></button>'
        '    </div>'
        '    <div class="hm-search-results"></div>'
        '    <div class="hm-customer-profile" style="display:none"></div>'
        '  </div>'
        '  <button type="button" class="hm-sectitle" data-collapse="hm-modules"'
        ' aria-expanded="true" aria-controls="hm-modules">'
        '    <span data-i18n="الوحدات الرئيسية">الوحدات الرئيسية</span>'
        '    <span class="hm-sectoggle"><svg class="icon">'
        '<use href="#icon-chevron-down"></use></svg></span>'
        '  </button>'
        + _home_tiles_html() +
        '</div>'
    )
    if frappe.db.exists("Custom HTML Block", HOME_BLOCK_NAME):
        frappe.delete_doc("Custom HTML Block", HOME_BLOCK_NAME, force=1, ignore_permissions=True)
    d = frappe.get_doc({
        "doctype": "Custom HTML Block", "name": HOME_BLOCK_NAME,
        "html": html, "style": HOME_STYLE, "script": HOME_SCRIPT,
    })
    d.insert(ignore_permissions=True)
    # An empty roles table on Custom HTML Block hides it from everyone
    # (opt-in allow-list) — must explicitly grant, same as the Workshop block.
    d.append("roles", {"role": "System Manager"})
    d.append("roles", {"role": "All"})
    d.save(ignore_permissions=True)
    frappe.db.commit()
    return d.name


def execute():
    block_name = _make_home_block()

    home = frappe.get_doc("Workspace", "Home")
    content = [
        {"id": "hwd_hdr", "type": "header",
         "data": {"text": '<span class="h4"><b>لوحة التحكم</b></span>', "col": 12}},
        {"id": "hwd_cb", "type": "custom_block",
         "data": {"custom_block_name": block_name, "col": 12}},
    ]
    home.content = json.dumps(content, ensure_ascii=False)
    home.shortcuts = []
    home.number_cards = []
    home.links = []
    home.quick_lists = []
    home.charts = []
    # IMPORTANT: block.js matches data.custom_block_name against this row's
    # `label` field (not custom_block_name) — they must be equal.
    home.custom_blocks = []
    home.append("custom_blocks", {"custom_block_name": block_name, "label": block_name})
    home.sequence_id = 1
    home.title = "لوحة التحكم"
    home.save(ignore_permissions=True)

    # Reorder sidebar to match Mazoon: Home, Settings, Accounting, Stock,
    # Buying, Selling, Workshop — then push everything else further down.
    order = [
        ("Home", 1),
        ("General Settings", 2),
        ("Accounting Dashboard", 3),
        ("Inventory Dashboard", 4),
        ("Purchasing Dashboard", 5),
        ("Sales Dashboard", 6),
        ("Workshop", 7),
    ]
    for name, seq in order:
        if frappe.db.exists("Workspace", name):
            frappe.db.set_value("Workspace", name, "sequence_id", seq)

    others = frappe.get_all("Workspace", filters={
        "public": 1, "name": ["not in", [n for n, _ in order]]
    }, pluck="name")
    for i, name in enumerate(others):
        frappe.db.set_value("Workspace", name, "sequence_id", 20 + i)

    frappe.db.commit()
    frappe.clear_cache()
    print("HOME_DONE tiles=%d others_deprioritized=%d" % (len(HOME_TILES) + 1, len(others)))
