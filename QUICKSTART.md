# دليل التشغيل السريع — Quick Start

> **⚠️ تحديث 2026-08-25:** هذا الملف كان يوثّق طريقة نشر **قديمة** (نسخ ملفات `.py` منفردة داخل `apps/frappe/frappe/` وتشغيلها بـ`bench execute frappe.X.execute`). المشروع تجاوز هذي الطريقة — `khat_workshop` الآن **تطبيق Frappe حقيقي** (`hooks.py` + `after_migrate`)، يُبنى ويُنشر بالكامل عبر `Dockerfile` + `docker-compose.yml`. الدليل الصحيح بالأسفل.

دليل نشر المشروع على سيرفر جديد (VPS عادي أو Coolify) من الصفر.

> راجع [`HANDOFF.md`](HANDOFF.md) للتفاصيل الكاملة و[`README.md`](README.md) لوظيفة كل ملف.

---

## 0) المتطلبات المسبقة

- سيرفر فيه **Docker + Docker Compose** (أو حساب **Coolify** يشير لهذا السيرفر)
- **دومين** يشير لعنوان IP السيرفر (أو subdomain مجاني من Coolify نوع `*.sslip.io` للتجربة)
- 4 CPU / 8GB RAM موصى بها كحد أدنى (نفس ما تحتاجه أي نشرة ERPNext)

---

## 1) طريقة Coolify (الموصى بها — الملفات مبنية لها تحديداً)

`docker-compose.yml` مكتوب خصيصاً ليتوافق مع شبكة Coolify التلقائية (Traefik) — لاحظ التعليق بالملف: *"In managed compose mode Coolify puts every service on the per-stack network and attaches Traefik to it"*.

1. **مشروع جديد بـ Coolify** ← Add Resource ← **Docker Compose** ← اربطه بمستودع Git لهذا المشروع (أو ارفع الملفات مباشرة).
2. Coolify يقرأ `docker-compose.yml` تلقائياً ويعرض الخدمات (db, backend, frontend, init...).
3. **Environment Variables** — انسخ من [``.env.example`](.env.example) وعبّي القيم الحقيقية في إعدادات المشروع بـCoolify (**وليس** بملف `.env` على القرص):

   | المتغيّر | القيمة |
   |---|---|
   | `SITE_NAME` | دومين حقيقي بدون `http://` — مثال: `erp.khataljazeera.com` أو الدومين المجاني اللي يعطيه Coolify (`xxxxx.sslip.io`) |
   | `ADMIN_PASSWORD` | كلمة مرور قوية لحساب `Administrator` |
   | `DEMO_USER_PASSWORD` | كلمة مرور حساب العميل التجريبي (`Admin` / `admin@khataljazeera.om`) — اتركه فارغ يمنع الدخول بهذا الحساب تماماً بدل كلمة مرور افتراضية |
   | `DB_ROOT_PASSWORD` | كلمة مرور MariaDB root |
   | `MYSQL_PASSWORD` | كلمة مرور مستخدم قاعدة بيانات الموقع |
   | `ERPNEXT_VERSION` | `v16` (أو تاغ آخر من [إصدارات frappe_docker](https://github.com/frappe/frappe_docker/releases)) |

4. **Domain**: بإعدادات خدمة `frontend` بـCoolify، اربط الدومين نفسه المكتوب بـ`SITE_NAME` بالضبط (نفس القيمة، حرفياً — أي فرق يكسر التوجيه).
5. اضغط **Deploy**. أول نشرة تاخذ عدة دقائق (بناء الصورة + `bench new-site` + تثبيت hrms/khat_workshop + `bench migrate`).
6. **تابع التقدّم**: من داخل Coolify افتح لوق حاوية `init` — أو من الطرفية:
   ```bash
   docker logs -f <اسم-حاوية-init>
   ```
   أو اقرأ اللوق المحفوظ داخل الـvolume المشترك حتى لو انحذفت الحاوية:
   ```bash
   docker run --rm -v <اسم-المشروع>_sites:/s alpine cat /s/init.log
   ```
7. لما تخلص: `https://<SITE_NAME>` — `Administrator` بكلمة `ADMIN_PASSWORD`، أو حساب العميل التجريبي `Admin` بكلمة `DEMO_USER_PASSWORD`.

---

## 2) طريقة VPS عادي (بدون Coolify)

```bash
git clone <رابط-المستودع> khat-erp && cd khat-erp
cp .env.example .env
nano .env   # عبّي القيم الحقيقية (SITE_NAME بدومين فعلي يشير للسيرفر، وكل كلمات المرور)
docker compose up -d --build
```

- أول تشغيل يبني الصورة (تحميل base image + بناء hrms) — قد ياخذ **15-20 دقيقة** أول مرة، أسرع بكثير بعدها لأن الطبقات محفوظة بالكاش (السبب موثّق بأعلى `Dockerfile`).
- بدون Coolify/Traefik، لازم تعكس منفذ `frontend` (8080 داخلياً) لمنفذ 80/443 بنفسك — عبر nginx/Caddy عكسي على السيرفر نفسه، أو بإضافة `ports: ["80:8080"]` تحت خدمة `frontend` بـ`docker-compose.yml` مباشرة إذا مافيه بروكسي تاني قدامه.
- تابع التقدّم: `docker compose logs -f init`

---

## 3) بعد أول نشرة ناجحة — التحديثات اللاحقة

**كل تعديل بالكود (زي التعديلات الأخيرة على `workshop_replacement_operations.py`, `workshop_document_numbering.py`, `workshop_work_card_to_invoice.py`...) يُنشر بإعادة بناء الصورة، مو بنسخ ملفات يدوياً:**

```bash
git pull                      # أو ادفع التعديلات لنفس المستودع اللي Coolify يراقبه
docker compose up -d --build  # أو زر "Redeploy" بـ Coolify
```

`init` يعيد التشغيل تلقائياً في كل نشرة (`bench migrate` يُعاد تنفيذه، والذي بدوره يُعيد تشغيل STEPS كاملة داخل `setup/__init__.py` — كلها idempotent فآمنة تتكرر). ما تحتاج تدخل بالحاويات يدوياً ولا تنسخ ملفات `.py` بنفسك.

**لو تبي تشغّل خطوة واحدة بس يدوياً** (مثلاً وأنت تختبر تعديل معيّن قبل نشرة كاملة):
```bash
docker compose exec backend bench --site <SITE_NAME> execute khat_workshop.setup.workshop_replacement_operations.execute
```
(استبدل الاسم بأي ملف من `khat_workshop/khat_workshop/setup/` — لاحظ المسار `khat_workshop.setup.<اسم_الملف>.execute`، مختلف عن الشكل القديم `frappe.<اسم_الملف>.execute` لأن الكود صار تطبيق منفصل، مو داخل frappe نفسها).

---

## 4) ملاحظات مهمة

- **الدولايتايبات المخصّصة موجودة فعلاً هنا** (`Work Card`, `Customer Vehicle`, `Workshop Technician`, `Service Package`, `Workshop Settings`...) — تُنشأ تلقائياً بـ`workshop_setup.py` كأول خطوة بـ`STEPS`. ما تحتاج تطبيق ورشة منفصل (خلاف ما كان مكتوب هنا سابقاً).
- **روابط PDF/واتساب** تعتمد على `host_name` مضبوط على `http://frontend:8080` (يضبطه `init.sh` تلقائياً) — يشتغل لأن wkhtmltopdf يجيب أصول الصفحة عبر شبكة Docker الداخلية، مو من `localhost`.
- **Server Scripts** لازم تكون مفعّلة (`server_script_enabled=true`) وإلا طبقة الأتمتة (خصم المخزون عند اعتماد بطاقة العمل...) تكون صامتة تماماً بدون أي خطأ ظاهر — `init.sh` يضبط هذا تلقائياً بكل نشرة.
- **النسخ الاحتياطي**: خدمة `backup` بـ`docker-compose.yml` تاخذ نسخة كل 24 ساعة (`BACKUP_INTERVAL_SECONDS`) وتحتفظ بـ14 يوم (`BACKUP_RETENTION_DAYS`) بـvolume منفصل (`backups`) — منفصل عمداً عن بيانات الموقع حتى لو تعطّبت.

---

## 5) أوامر تشغيلية سريعة

```bash
docker compose ps                    # حالة الحاويات
docker compose logs -f backend       # لوق الباك إند
docker compose logs -f init          # لوق أول نشرة/التحديث الأخير
docker compose restart backend websocket queue-short queue-long frontend
docker compose down                  # إيقاف (البيانات تبقى بالـvolumes)
```

