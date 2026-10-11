#!/usr/bin/env bash
# نشر نظام خط الجزيرة على خادم Oracle Cloud (أو أي VPS بأوبنتو) بأمر واحد.
#
# الاستخدام على الخادم بعد الدخول بـSSH:
#   curl -fsSL <رابط-السكربت> | bash -s -- khat.onemedia24.xyz adelabdulkrime@gmail.com
# أو بعد نسخه يدوياً:
#   bash deploy-oracle.sh khat.onemedia24.xyz adelabdulkrime@gmail.com
#
# يتولّى: Docker، ملف التبادل، جدار الحماية الداخلي، سحب الكود، توليد كلمات
# المرور، ثم التشغيل خلف Caddy بشهادة HTTPS تلقائية.

set -euo pipefail

SITE_NAME="${1:-}"
ACME_EMAIL="${2:-admin@example.com}"
REPO_DIR="${HOME}/khat-erp"

log()  { printf '\n\033[1;36m[%s] %s\033[0m\n' "$(date +%H:%M:%S)" "$*"; }
ok()   { printf '\033[1;32m  ✓ %s\033[0m\n' "$*"; }
die()  { printf '\n\033[1;31m  ✗ %s\033[0m\n\n' "$*" >&2; exit 1; }

[ -n "$SITE_NAME" ] || die "الاستخدام: bash deploy-oracle.sh <الدومين> <البريد>"

# الدومين لازم يكون مجرداً — Frappe يرفض أي مخطط أو مسار، وnginx يطابق الترويسة حرفياً
case "$SITE_NAME" in
  http://*|https://*|*/*) die "اكتب الدومين مجرداً بلا http:// وبلا / — مثال: khat.onemedia24.xyz" ;;
esac

log "1/7 التحقق من توجيه الدومين"
RESOLVED="$(getent hosts "$SITE_NAME" 2>/dev/null | awk '{print $1}' | head -1 || true)"
PUBLIC_IP="$(curl -fsS --max-time 15 https://api.ipify.org 2>/dev/null || echo '')"
if [ -z "$RESOLVED" ]; then
  echo "  ⚠ الدومين $SITE_NAME لا يشير لأي عنوان بعد."
  echo "    أضف سجل A في لوحة الدومين يشير إلى: ${PUBLIC_IP:-<عنوان هذا الخادم>}"
  echo "    بدونه لن تُصدر شهادة HTTPS — لكن التثبيت سيكمل."
  read -rp "  أكمل على أي حال؟ [y/N] " a; [ "${a:-n}" = "y" ] || exit 1
elif [ -n "$PUBLIC_IP" ] && [ "$RESOLVED" != "$PUBLIC_IP" ]; then
  echo "  ⚠ الدومين يشير إلى $RESOLVED بينما عنوان هذا الخادم $PUBLIC_IP"
  read -rp "  أكمل على أي حال؟ [y/N] " a; [ "${a:-n}" = "y" ] || exit 1
else
  ok "الدومين يشير لهذا الخادم ($RESOLVED)"
fi

log "2/7 تحديث النظام وتثبيت Docker"
sudo apt-get update -qq
sudo DEBIAN_FRONTEND=noninteractive apt-get upgrade -y -qq
if ! command -v docker >/dev/null 2>&1; then
  curl -fsSL https://get.docker.com | sudo sh
  sudo usermod -aG docker "$USER"
  ok "Docker مثبّت (ستحتاج إعادة دخول لتفعيل المجموعة)"
else
  ok "Docker موجود مسبقاً"
fi
sudo systemctl enable --now docker

log "3/7 ملف التبادل (swap)"
# البناء الأول يستهلك ذاكرة كبيرة؛ بدون swap قد يُقتل بـOOM على الأجهزة الصغيرة.
if ! sudo swapon --show | grep -q swapfile; then
  sudo fallocate -l 4G /swapfile
  sudo chmod 600 /swapfile
  sudo mkswap /swapfile >/dev/null
  sudo swapon /swapfile
  grep -q '/swapfile' /etc/fstab || echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab >/dev/null
  ok "أُنشئ ملف تبادل 4GB"
else
  ok "ملف التبادل موجود"
fi

log "4/7 فتح المنفذين 80 و443"
# صور أوبنتو في Oracle تأتي بقواعد iptables تحجب كل شيء، حتى لو فتحت الجدار
# السحابي من لوحة التحكم — ونسيان ذلك أشهر سبب لـ"الموقع لا يفتح". أما Hetzner
# وContabo وDigitalOcean فتأتي مفتوحة، وبعضها يستخدم ufw بدل iptables الخام.
# نتعامل مع الحالتين بدل افتراض Oracle.
if command -v ufw >/dev/null 2>&1 && sudo ufw status 2>/dev/null | grep -q "Status: active"; then
  sudo ufw allow 80/tcp  >/dev/null 2>&1 || true
  sudo ufw allow 443/tcp >/dev/null 2>&1 || true
  ok "فُتح المنفذان عبر ufw"
else
  # الموضع حاسم لا الوجود: صور أوبنتو في Oracle تنتهي بقاعدة REJECT تبتلع كل
  # ما بعدها، فإدراج القاعدة برقم ثابت (6) يضعها بعد الرفض متى كان REJECT في
  # الموضع الخامس — فلا تعمل أبداً، والموقع يبقى محجوباً بينما `iptables -L`
  # يُظهر المنفذ «مفتوحاً». نقرأ رقم سطر REJECT ونُدرج قبله.
  REJECT_LINE="$(sudo iptables -L INPUT -n --line-numbers 2>/dev/null \
    | awk '/REJECT|DROP/ {print $1; exit}')"
  for p in 80 443; do
    if sudo iptables -C INPUT -m state --state NEW -p tcp --dport "$p" -j ACCEPT 2>/dev/null; then
      continue
    fi
    if [ -n "$REJECT_LINE" ]; then
      sudo iptables -I INPUT "$REJECT_LINE" -m state --state NEW -p tcp --dport "$p" -j ACCEPT 2>/dev/null || true
    else
      sudo iptables -A INPUT -m state --state NEW -p tcp --dport "$p" -j ACCEPT 2>/dev/null || true
    fi
  done
  if command -v netfilter-persistent >/dev/null 2>&1; then
    sudo netfilter-persistent save >/dev/null 2>&1 || true
  else
    sudo DEBIAN_FRONTEND=noninteractive apt-get install -y -qq iptables-persistent >/dev/null 2>&1 || true
  fi
  ok "فُتح المنفذان عبر iptables"
fi
echo "    ملاحظة: على Oracle افتح أيضاً Security List من لوحة التحكم (0.0.0.0/0 على 80 و443)."
echo "    على Hetzner/Contabo/DigitalOcean عادةً لا يلزم شيء إضافي."

log "5/7 جلب الكود"
if [ -d "$REPO_DIR/.git" ]; then
  git -C "$REPO_DIR" pull --ff-only && ok "حُدّث المستودع"
else
  [ -d "$REPO_DIR" ] || die "انسخ ملفات المشروع إلى $REPO_DIR أولاً (أو استنسخ المستودع)"
  ok "المجلد موجود"
fi
cd "$REPO_DIR"

log "6/7 إعداد كلمات المرور"
if [ -f .env ]; then
  ok ".env موجود — لن يُستبدل"
else
  gen() { tr -dc 'A-Za-z0-9' </dev/urandom | head -c 24; }
  cat > .env <<ENVEOF
# أُنشئ تلقائياً بواسطة deploy-oracle.sh في $(date -u +%Y-%m-%dT%H:%M:%SZ)
SITE_NAME=${SITE_NAME}
ADMIN_PASSWORD=$(gen)
DEMO_USER_PASSWORD=$(gen)
DB_ROOT_PASSWORD=$(gen)
MYSQL_PASSWORD=$(gen)
ERPNEXT_VERSION=v16
ACME_EMAIL=${ACME_EMAIL}
ENVEOF
  chmod 600 .env
  ok "أُنشئ .env بكلمات مرور عشوائية قوية"
fi

log "7/7 البناء والتشغيل (قد يستغرق 15-25 دقيقة)"
# سحب الصور الأساسية أولاً: docker pull يستأنف عند الانقطاع، بينما البناء
# يعيد الطبقة من أولها — فرق حاسم على اتصال بطيء.
sudo docker pull mariadb:10.6 || true
sudo docker compose -f docker-compose.yml -f docker-compose.caddy.yml up -d --build

log "متابعة التهيئة"
sudo docker compose logs -f init 2>/dev/null | sed -n '/Init complete/q;p' || true

echo
echo "════════════════════════════════════════════════════════"
echo "  اكتمل النشر"
echo "════════════════════════════════════════════════════════"
echo "  العنوان : https://${SITE_NAME}"
echo "  المستخدم: Administrator"
echo "  كلمة المرور:"
grep '^ADMIN_PASSWORD=' .env | cut -d= -f2
echo
echo "  للتحقق من نجاح كل الخطوات:"
echo "    sudo docker compose logs init | grep -E 'steps OK|failure'"
echo "  المتوقع: [khat_workshop] all 41 steps OK"
echo "════════════════════════════════════════════════════════"
