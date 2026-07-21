# دليل التشغيل السريع — Quick Start

دليل لتجهيز البيئة على جهاز جديد وتشغيل عرض تجريبي (demo) بأسرع وقت، ثم نشر سكربتات التخصيص.

> هذا المستودع **لا يحوي تطبيق Frappe** — فقط سكربتات `.py` تُنشر فوق تثبيت **frappe_docker** قياسي.
> راجع [`HANDOFF.md`](HANDOFF.md) للتفاصيل الكاملة و[`README.md`](README.md) لوظيفة كل ملف.

---

## 0) المتطلبات المسبقة (Prerequisites)

على الجهاز الجديد ثبّت:

- **Docker Desktop** (Windows/Mac/Linux) — شغّله وتأكد أنه يعمل: `docker version`
- **Git** — `git version`
- على ويندوز: استخدم **Git Bash** لأوامر docker (وليس PowerShell) — راجع ملاحظة `MSYS_NO_PATHCONV` أدناه.

الموارد المقترحة لـ Docker: **4 CPU / 8GB RAM** على الأقل.

---

## 1) إحضار هذا المستودع (بعد نسخه من الجهاز الأول)

فُكّ ضغط `khat-aljazeera-erp-customizations.zip` — بداخله مجلد المشروع كاملاً مع تاريخ Git (`.git`).

```bash
cd khat-aljazeera-erp-customizations
git log --oneline        # تأكد أن التاريخ موجود
```

### الربط بمستودع بعيد والدفع (Push)
```bash
git remote add origin <رابط-المستودع-على-GitHub-أو-غيره>
git push -u origin master
```

---

## 2) تشغيل ERPNext v16 عبر Docker (أسرع طريق للـ demo)

في مجلد **منفصل** (بجانب هذا المستودع، وليس بداخله):

```bash
git clone https://github.com/frappe/frappe_docker
cd frappe_docker
docker compose -f pwd.yml up -d
```

- سينزّل الصور ويُنشئ موقعاً افتراضياً — انتظر **5–10 دقائق** في أول مرة.
- تابع تقدّم إنشاء الموقع:
  ```bash
  docker compose -f pwd.yml logs -f create-site
  ```
- عند الانتهاء افتح: **http://localhost:8080**
  - المستخدم الافتراضي في `pwd.yml`: **Administrator** / كلمة المرور: **admin**

> **بيئة الإنتاج الأصلية** (كما في HANDOFF) تستخدم ملف `compose.yaml` مخصّص، الموقع باسم **erp.local** والدخول **Administrator / Admin@2026**. للـ demo السريع اكتفِ بـ `pwd.yml` أعلاه، وعدّل اسم الموقع في أوامر النشر حسب موقعك الفعلي.

اعرف اسم موقعك الفعلي واسم حاوية الـ backend:
```bash
docker compose -f pwd.yml exec backend bench --site all list-apps   # يطبع اسم الموقع
docker compose -f pwd.yml ps                                        # أسماء الحاويات
```

---

## 3) نشر سكربتات التخصيص

كل ملف يُنسخ داخل حاوية backend ثم يُنفَّذ عبر `bench execute`. اضبط المتغيّرين:

```bash
SITE=frontend          # أو erp.local حسب موقعك
COMPOSE="-f pwd.yml"   # أو احذفه إن كنت تستخدم compose.yaml مباشرة
```

### نشر ملف واحد
```bash
MSYS_NO_PATHCONV=1 docker compose $COMPOSE cp workshop_scripts.py \
  backend:/home/frappe/frappe-bench/apps/frappe/frappe/workshop_scripts.py

MSYS_NO_PATHCONV=1 docker compose $COMPOSE exec backend \
  bench --site $SITE execute frappe.workshop_scripts.execute
```

### نشر كل الملفات دفعة واحدة (نفّذ من داخل مجلد هذا المستودع)

رتّب التنفيذ بحيث يأتي `workshop_futuristic.py` (الوحدة المشتركة) **أولاً**:

```bash
for f in workshop_futuristic.py \
         workshop_home.py \
         workshop_dashboard.py \
         workshop_accounting.py \
         workshop_inventory.py \
         workshop_purchasing.py \
         workshop_sales.py \
         workshop_general_settings.py \
         workshop_scripts.py \
         workshop_gl_stock_integration.py \
         workshop_invoice_whatsapp.py \
         workshop_translations.py; do
  echo "=== $f ==="
  mod="${f%.py}"
  MSYS_NO_PATHCONV=1 docker compose $COMPOSE cp "$f" \
    "backend:/home/frappe/frappe-bench/apps/frappe/frappe/$f"
  MSYS_NO_PATHCONV=1 docker compose $COMPOSE exec backend \
    bench --site "$SITE" execute "frappe.$mod.execute"
done
```

السكربتات **idempotent** — يمكن إعادة تشغيلها بأمان.

---

## 4) ملاحظات مهمة (Gotchas)

- **`MSYS_NO_PATHCONV=1`** ضروري قبل كل أمر docker على **Git Bash / ويندوز**، وإلا تُفسد المسارات داخل الحاوية.
- بعد تعديل `workshop_futuristic.py` أعِد التشغيل ثم أعِد تنفيذ **كل** اللوحات السبع (الـ JS يُخبز داخل كل لوحة عند التنفيذ):
  ```bash
  docker compose $COMPOSE restart backend websocket queue-short queue-long
  docker compose $COMPOSE restart frontend    # لتفادي 502 من nginx بعد إعادة التشغيل
  ```
- **الدولايتايبات المخصّصة** (`Work Card`, `Repair Invoice`, `Workshop Payment`, `Customer Vehicle`, `Workshop Technician`, `Service Package`, `Workshop Settings`) تأتي من تطبيق الورشة المخصّص **غير المُضمَّن هنا**. لذلك في demo نظيف:
  - ستعمل: طبقة التصميم، اللوحات، الترجمات.
  - قد تفشل جزئياً: السكربتات التي تعتمد على تلك الدولايتايبات (`workshop_scripts`, `workshop_gl_stock_integration`, `workshop_invoice_whatsapp`) حتى تُنشأ الدولايتايبات أولاً.
- **روابط PDF/واتساب** تعتمد على دومين عام حقيقي (HTTPS)؛ لن تعمل على هاتف العميل من `localhost`.

---

## 5) أوامر تشغيلية سريعة

```bash
docker compose $COMPOSE ps          # حالة الحاويات
docker compose $COMPOSE up -d        # تشغيل
docker compose $COMPOSE stop         # إيقاف مؤقت
docker compose $COMPOSE logs -f backend
```
cd "C:/Users/adela/Documents/GitHub/khat-aljazeera-erp-customizations"
git push
