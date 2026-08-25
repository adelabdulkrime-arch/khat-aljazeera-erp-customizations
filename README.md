# خط الجزيرة — تخصيصات ERPNext لورشة الصيانة وقطع الغيار

تخصيصات Python/JS مبنية فوق **Frappe / ERPNext v16** (عبر [frappe_docker](https://github.com/frappe/frappe_docker)) لإدارة ورشة صيانة سيارات ومحل قطع غيار، مُعرّبة بالكامل (RTL)، بواجهة تحاكي منافساً محلياً اسمه Mazoon ERP.

> للتفاصيل الكاملة (البيئة، أوامر التشغيل، الأمور التقنية الدقيقة، المهام المعلّقة) راجع [`HANDOFF.md`](HANDOFF.md).

## نظرة عامة

هذا المستودع **لا يحتوي على تطبيق Frappe كاملاً** — فقط ملفات التخصيص التي تُنشر فوق تثبيت frappe_docker قياسي عبر `bench execute`. كل ملف هو *setup script* يُنشئ/يحدّث Client Scripts وServer Scripts وCustom Fields وWorkspaces داخل الموقع، وهو **idempotent** (يمكن إعادة تشغيله بأمان).

## الملفات

| الملف | الوظيفة |
|------|---------|
| `workshop_setup.py` | **يُنشئ كل الدولايتايبات المخصّصة** (بطاقة العمل، فاتورة الإصلاح، مركبة العميل، إعدادات الورشة…) كـ Custom DocTypes مخزّنة في قاعدة البيانات — **يجب تشغيله أولاً** |
| `workshop_futuristic.py` | وحدة CSS/JS مشتركة تستوردها كل اللوحات |
| `workshop_home.py` | لوحة الرئيسية + بحث سريع بالجوال/رقم اللوحة |
| `workshop_dashboard.py` | لوحة "إدارة ورشة الصيانة" (بلاطات + إحصائيات قابلة للطي) |
| `workshop_accounting.py` | لوحة الحسابات |
| `workshop_inventory.py` | لوحة المخزون |
| `workshop_purchasing.py` | لوحة المشتريات |
| `workshop_sales.py` | لوحة المبيعات |
| `workshop_general_settings.py` | لوحة الإعدادات العامة |
| `workshop_scripts.py` | حسابات المجاميع، أزرار واتساب، تعبئة بيانات العميل العائد تلقائياً |
| `workshop_gl_stock_integration.py` | ربط بطاقة العمل/الفواتير/الدفعات بمحرك المحاسبة والمخزون الحقيقي في ERPNext |
| `workshop_service_catalogue.py` | كتالوج خدمات أساسي (5 خطوط خدمة عامة) كأصناف حقيقية بدل نص حر |
| `workshop_replacement_operations.py` | كتالوج "عمليات الاستبدال" التفصيلية (تبديل بطارية، فلتر زيت، بوش، لينك رود...) — أكواد مولّدة تلقائياً بصيغة `SRV-####` (مطابقة لمازون) عبر عدّاد Frappe الذري، يستحيل تكرارها |
| `workshop_operations_print_format.py` | قالب طباعة مفصّل لفاتورة المبيعات وعرض السعر يعرض رقم اللوحة، الشاصي، التاريخ، الساعة، وجدول الأعمال بنداً بنداً + الإجمالي |
| `workshop_document_numbering.py` | تسلسل ترقيم منفصل `WI-.YYYY.-` / `WQ-.YYYY.-` لمستندات الورشة (مركبة مرتبطة) مقابل التسلسل الافتراضي لبيع نقطة البيع العادي — يُختار تلقائياً بمجرد ربط مركبة، بنفس منطق مازون |
| `workshop_invoice_whatsapp.py` | توليد PDF للفاتورة (Sales Invoice، بقالبنا المفصّل) وإرجاع رابط لإرساله عبر واتساب |
| `workshop_work_card_to_invoice.py` | دالتان مكشوفتان (whitelist) تنشئان فاتورة/عرض سعر تلقائياً من بطاقة عمل — تُستدعى من زر "إنشاء فاتورة/عرض سعر" على بطاقة العمل. **بدون STEPS تسجيل** (لا يوجد شيء يُهيَّأ، فقط دوال تُستدعى عند الطلب) |
| `workshop_translations.py` | جداول الترجمة العربية |
| `workshop_oman_setup2.py` | إعادة وسم دليل الحسابات إلى OMR (قبل تبديل عملة الشركة) |
| `workshop_oman_setup.py` | توطين عُمان: عملة OMR (3 خانات)، ضريبة 5%، توقيت مسقط |

## تطبيق ويب قابل للتثبيت (PWA)

النظام الآن **قابل للتثبيت كتطبيق** على الجوال والتابلت واللابتوب — من نفس قاعدة الكود، دون متجر تطبيقات ودون إعادة بناء. الطبقة:

| الملف | الوظيفة |
|------|---------|
| `khat_workshop/public/manifest.json` | بيان التطبيق: الاسم «خط الجزيرة»، الأيقونات، لون الهوية `#1a2b4a`، `start_url=/desk/home`، عرض `standalone` |
| `khat_workshop/public/icons/` | أيقونات 192/512 + نسخة `maskable` + `apple-touch-icon` (شعار «خط» على تدرّج كحلي) |
| `khat_workshop/public/js/pwa.js` | يحقن المانيفست ووسوم iOS/`theme-color`، يسجّل الـ service worker، ويعرض زر **«ثبّت التطبيق»** داخل النظام — يُحمَّل على الديسك (`app_include_js`) وصفحة الدخول (`web_include_js`) |
| `khat_workshop/public/offline.html` | صفحة «لا يوجد اتصال» المعرَّبة تظهر عند انقطاع الشبكة |
| `khat_workshop/pwa.py` | `page_renderer` يقدّم الـ service worker على `/sw.js` بنطاق يغطّي كامل النظام (`/app`, `/desk/home`) |

### التثبيت على الأجهزة

> يتطلّب التثبيت أن يكون النظام على **دومين HTTPS حقيقي** (يعمل على `localhost` للتجربة فقط).

على **أندرويد واللابتوب (Chrome/Edge)** يظهر زر **«ثبّت التطبيق»** تلقائياً داخل النظام (أسفل الشاشة) — اضغطه ووافِق. وإن أُغلق أو لم يظهر، استخدم الطريقة اليدوية:

- **أندرويد (Chrome):** قائمة (⋮) ← «تثبيت التطبيق» / «إضافة إلى الشاشة الرئيسية».
- **آيفون/آيباد (Safari):** زر المشاركة ⬆️ ← «إضافة إلى الشاشة الرئيسية». (متصفح آبل لا يدعم الزر التلقائي.)
- **لابتوب (Chrome/Edge):** أيقونة التثبيت ⊕ في شريط العنوان ← «تثبيت» — يصبح **برنامجاً بنافذته الخاصة** وأيقونة في قائمة ابدأ/شريط المهام.

الخدمة تعمل بمبدأ **الشبكة أولاً**: لا تُخزّن أي بيانات ERP مؤقتاً (لا فواتير ولا تقارير قديمة) — تتدخّل فقط لعرض صفحة «لا يوجد اتصال» عند انقطاع الشبكة، فلا تُقدَّم بيانات قديمة أبداً.

### النشر (مهم)
كل ملفات الـ PWA ثابتة (لا تحتاج `bench build`) لكنها **تُخبز داخل صورة Docker**. لذا بعد سحب هذا التحديث **أعد بناء الصورة وأعد النشر**؛ يتكفّل `init.sh` بالباقي (`bench migrate` يُحدّث الـ hooks تلقائياً).

## النشر

```bash
docker compose cp workshop_scripts.py backend:/home/frappe/frappe-bench/apps/frappe/frappe/workshop_scripts.py
docker compose exec backend bench --site erp.local execute frappe.workshop_scripts.execute
```
كرّر لكل ملف بنفس النمط. (على git-bash في ويندوز أضف `MSYS_NO_PATHCONV=1` قبل أوامر docker).

## المتطلبات

- Frappe/ERPNext v16 عبر Docker (انظر [frappe/frappe_docker](https://github.com/frappe/frappe_docker))
- الدولايتايبات المخصّصة (`Work Card`, `Repair Invoice`, `Workshop Payment`, `Customer Vehicle`, `Workshop Technician`, `Service Package`, `Workshop Settings` …) أصبحت الآن **مُضمّنة** ويُنشئها `workshop_setup.py` تلقائياً عند النشر — لم تعد تحتاج تطبيقاً خارجياً.

## النشر الحاوي (Docker / Coolify)

هذا المستودع يتضمّن الآن نشراً حاوياً كاملاً: `docker-compose.yml` + `Dockerfile` + `docker/init.sh`. عند النشر (محلياً أو عبر Coolify) تُنشأ الحاوية `init` الموقعَ وتُنفّذ كل سكربتات التخصيص بالترتيب الصحيح (`workshop_setup` أولاً). راجع [`.env.example`](.env.example) للمتغيّرات المطلوبة.

## ملاحظة أمنية

روابط فواتير واتساب المُولَّدة تعتمد على حقل **"الرابط العام للنظام"** في `Workshop Settings` — يجب ضبطه على دومين عام حقيقي (HTTPS) عند النشر الإنتاجي، وإلا فالروابط لن تعمل على هاتف العميل.
