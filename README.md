# خط الجزيرة — تخصيصات ERPNext لورشة الصيانة وقطع الغيار

تخصيصات Python/JS مبنية فوق **Frappe / ERPNext v16** (عبر [frappe_docker](https://github.com/frappe/frappe_docker)) لإدارة ورشة صيانة سيارات ومحل قطع غيار، مُعرّبة بالكامل (RTL)، بواجهة تحاكي منافساً محلياً اسمه Mazoon ERP.

> للتفاصيل الكاملة (البيئة، أوامر التشغيل، الأمور التقنية الدقيقة، المهام المعلّقة) راجع [`HANDOFF.md`](HANDOFF.md).

## نظرة عامة

هذا المستودع **لا يحتوي على تطبيق Frappe كاملاً** — فقط ملفات التخصيص التي تُنشر فوق تثبيت frappe_docker قياسي عبر `bench execute`. كل ملف هو *setup script* يُنشئ/يحدّث Client Scripts وServer Scripts وCustom Fields وWorkspaces داخل الموقع، وهو **idempotent** (يمكن إعادة تشغيله بأمان).

## الملفات

| الملف | الوظيفة |
|------|---------|
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
| `workshop_invoice_whatsapp.py` | توليد PDF لفاتورة الإصلاح وإرجاع رابط لإرساله عبر واتساب |
| `workshop_translations.py` | جداول الترجمة العربية |

## النشر

```bash
docker compose cp workshop_scripts.py backend:/home/frappe/frappe-bench/apps/frappe/frappe/workshop_scripts.py
docker compose exec backend bench --site erp.local execute frappe.workshop_scripts.execute
```
كرّر لكل ملف بنفس النمط. (على git-bash في ويندوز أضف `MSYS_NO_PATHCONV=1` قبل أوامر docker).

## المتطلبات

- Frappe/ERPNext v16 عبر Docker (انظر [frappe/frappe_docker](https://github.com/frappe/frappe_docker))
- الدولايتايبات المخصّصة: `Work Card`, `Repair Invoice`, `Workshop Payment`, `Customer Vehicle`, `Workshop Technician`, `Service Package`, `Workshop Settings` (من تطبيق الورشة المخصّص — غير مُضمّن في هذا المستودع)

## ملاحظة أمنية

روابط فواتير واتساب المُولَّدة تعتمد على حقل **"الرابط العام للنظام"** في `Workshop Settings` — يجب ضبطه على دومين عام حقيقي (HTTPS) عند النشر الإنتاجي، وإلا فالروابط لن تعمل على هاتف العميل.
