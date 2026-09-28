# النشر على Oracle Cloud المجاني — دليل كامل

نشر نظام خط الجزيرة على **Oracle Cloud Always Free**: ‏4 أنوية ARM و24GB ذاكرة، مجاناً بلا حد زمني — أكبر بكثير من الحد الأدنى الذي يحتاجه النظام (4 أنوية / 8GB).

> بديل مدفوع رخيص: أي VPS بـ8GB (Hetzner ≈ €5/شهر). نفس خطوات القسم 3 فما بعد تنطبق عليه حرفياً.

---

## ⚠️ اقرأ هذا أولاً

**الاستضافة العادية (shared hosting / cPanel) لا تُشغّل هذا النظام.** ERPNext يحتاج Python وDocker وصلاحيات root وخدمات تعمل 24/7 (قاعدة بيانات، ثلاث خدمات Redis، عمّال خلفية، مُجدول). الاستضافة العادية تعطيك PHP وMySQL فقط. تحتاج **VPS** أو **Cloud instance** — ولا يوجد التفاف على هذا.

**وبخصوص المجاني:** حساب Oracle المجاني ممتاز لكنه ليس ضماناً تعاقدياً — Oracle قد تحذف الحسابات الخاملة. بياناتك هنا فواتير وعملاء ومخزون، لذا **النسخ الاحتياطي خارج السيرفر (القسم 8) ليس اختيارياً.**

---

## 1) إنشاء الحساب

1. سجّل في [cloud.oracle.com](https://www.oracle.com/cloud/free/) واختر أقرب منطقة (Region) لعُمان — عادة **Saudi Arabia (Jeddah)** أو **UAE (Dubai)**. **المنطقة لا يمكن تغييرها لاحقاً.**
2. يطلب بطاقة للتحقق فقط — لا يُخصم منها شيء ما دمت ضمن Always Free.

> التسجيل قد يُرفض أحياناً بلا سبب واضح (مشكلة معروفة). إن رُفض، جرّب بطاقة أخرى أو متصفحاً آخر، أو انتقل لـHetzner المدفوع.

## 2) إنشاء الخادم (Instance)

من القائمة: **Compute ← Instances ← Create Instance**

| الإعداد | القيمة |
|---|---|
| Image | **Ubuntu 22.04** (أو 24.04) |
| Shape | **Ampere ARM — VM.Standard.A1.Flex** |
| OCPUs / Memory | **4 نواة / 24GB** (كامل الحصة المجانية) |
| Boot volume | 100GB (ضمن المجاني: 200GB إجمالاً) |
| SSH keys | احفظ المفتاح الخاص — **لا سبيل لتحميله مرة ثانية** |

> **صنف ARM مقصود** — صورة ERPNext الأساسية متعددة المعمارية وتدعم arm64، تحققتُ من ذلك. لا يحتاج `Dockerfile` أي تعديل.

> إن ظهر «Out of capacity»، جرّب Availability Domain آخر أو أعد المحاولة لاحقاً — الطلب على ARM المجاني مرتفع.

## 3) فتح المنافذ — خطوتان، ونسيان الثانية هو الخطأ الأشهر

**أ. جدار Oracle السحابي:** من صفحة الخادم ← Subnet ← Security List ← **Add Ingress Rules**، أضف قاعدتين مصدرهما `0.0.0.0/0` للمنفذين **80** و**443** (TCP).

**ب. جدار أوبنتو الداخلي:** صور أوبنتو في Oracle تأتي بقواعد iptables تحجب كل شيء، حتى لو فتحت الجدار السحابي:

```bash
sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 80 -j ACCEPT
sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 443 -j ACCEPT
sudo netfilter-persistent save
```

## 4) الدومين

وجّه سجل **A** من `khat-aljazeera.onemedia.xyz` إلى **عنوان IP العام** للخادم من لوحة إدارة `onemedia.xyz`.

تحقق قبل المتابعة (Caddy سيفشل في إصدار الشهادة إن لم يكن الدومين موجّهاً):
```bash
dig +short khat-aljazeera.onemedia.xyz
```

## 5) تجهيز الخادم

```bash
ssh -i <مفتاحك> ubuntu@<IP>

sudo apt update && sudo apt upgrade -y
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker $USER
newgrp docker            # أو أعد تسجيل الدخول
```

**ملف تبادل (Swap) — مهم:** البناء الأول يستهلك ذاكرة كبيرة، وبدون swap قد يُقتل بـOOM:
```bash
sudo fallocate -l 4G /swapfile && sudo chmod 600 /swapfile
sudo mkswap /swapfile && sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

## 6) النشر

```bash
git clone <رابط-المستودع> khat-erp && cd khat-erp
cp .env.example .env
nano .env
```

عبّئ القيم — **كلمات مرور قوية فعلية، لا القيم الافتراضية**:

| المتغيّر | القيمة |
|---|---|
| `SITE_NAME` | `khat-aljazeera.onemedia.xyz` — **بدون `https://` وبدون `/` في آخره** |
| `ADMIN_PASSWORD` | كلمة مرور حساب `Administrator` |
| `DEMO_USER_PASSWORD` | كلمة مرور الحساب التجريبي (اتركه فارغاً لتعطيل الحساب) |
| `DB_ROOT_PASSWORD` | كلمة مرور جذر MariaDB |
| `MYSQL_PASSWORD` | كلمة مرور مستخدم قاعدة بيانات الموقع |
| `ACME_EMAIL` | بريدك — لتنبيهات انتهاء شهادة Let's Encrypt |

ثم شغّل — **لاحظ `-f` مرتين، والترتيب مهم**:

```bash
docker compose -f docker-compose.yml -f docker-compose.caddy.yml up -d --build
```

الملف الثاني ([docker-compose.caddy.yml](docker-compose.caddy.yml)) يضيف **Caddy** كبروكسي عكسي يُصدر شهادة HTTPS ويجدّدها تلقائياً. الملف الأساسي وحده مبني لـCoolify (كان Traefik يتولّى هذا الدور) وخدمة `frontend` فيه لا تنشر أي منفذ — أي أن تشغيله وحده على VPS عادي **لن يجعل النظام متاحاً من الإنترنت**.

**البناء الأول يستغرق 15-25 دقيقة** (تحميل الصورة الأساسية وبناء أصول hrms). تابع:
```bash
docker compose logs -f init
```

عند اكتمال `init` بنجاح، افتح `https://khat-aljazeera.onemedia.xyz` وسجّل الدخول بـ`Administrator` وكلمة `ADMIN_PASSWORD`.

## 7) التحديثات اللاحقة

```bash
git pull
docker compose -f docker-compose.yml -f docker-compose.caddy.yml up -d --build
```

`init` يعيد تشغيل `bench migrate` تلقائياً، وكل سكربتات الإعداد idempotent — آمنة التكرار.

## 8) النسخ الاحتياطي — لا تتخطَّ هذا

خدمة `backup` في `docker-compose.yml` تأخذ نسخاً **داخل نفس السيرفر**، وهي لا تحميك من فقدان الخادم نفسه (وهو السيناريو الواقعي مع حساب مجاني). انسخها لجهازك دورياً:

```bash
# على جهازك، لا على السيرفر
scp -i <مفتاحك> -r ubuntu@<IP>:/var/lib/docker/volumes/khat-erp_backups/_data ./erp-backups
```

اختبر استعادة نسخة مرة واحدة على الأقل — نسخة احتياطية لم تُختبر ليست نسخة احتياطية.

## مشاكل شائعة

| العرض | السبب والحل |
|---|---|
| الموقع لا يفتح إطلاقاً | جدار أوبنتو الداخلي — راجع القسم 3-ب |
| خطأ شهادة / يفتح على http فقط | الدومين لا يشير للسيرفر بعد، أو المنفذ 80 مغلق. راجع `docker compose logs caddy` |
| `Invalid Host header` أو صفحة بيضاء | `SITE_NAME` لا يطابق الدومين حرفياً، أو فيه `https://` |
| البناء يُقتل فجأة | ذاكرة غير كافية — أضف swap (القسم 5) |
| الإشعارات الفورية لا تعمل | مسار `/socket.io/*` — تحقق أن `docker/Caddyfile` منسوخ ومقروء |
