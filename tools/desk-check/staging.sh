#!/usr/bin/env bash
# نسخة الاختبار: تشغيل كود المستودع على موقع kaj-staging.localhost دون مسّ الإنتاج.
#
# الموقعان يتشاركان حاويات واحدة وكوداً واحداً، فتعديل ملف بايثون داخل الحاوية
# يغيّر الإنتاج معه. الحلّ: نسخة من حزمة khat_workshop في ‎/tmp/kaj-overlay
# داخل حاوية backend، تُقدَّم على مسار الاستيراد (PYTHONPATH) لعمليات نسخة
# الاختبار وحدها — gunicorn ثانٍ على المنفذ 8001، وأوامر bench التي تُشغَّل من
# هنا. عمليات الإنتاج لا ترى هذا المسار.
#
#   tools/desk-check/staging.sh sync            ينسخ كود المستودع ويعيد تشغيل خادم الاختبار
#   tools/desk-check/staging.sh run <method>    bench execute على نسخة الاختبار بكود المستودع
#   tools/desk-check/staging.sh setup           يطبّق خطوات الإعداد كلها (ما يفعله migrate)
#   echo "<query>" | tools/desk-check/staging.sh sql   استعلام على قاعدة نسخة الاختبار
#   echo "<python>" | tools/desk-check/staging.sh py    كود بايثون داخل نسخة الاختبار
#   tools/desk-check/staging.sh stop            يوقف خادم الاختبار
#
# ثم: نفق SSH للمنفذ 8001 وnode tools/desk-check/serve.js (راجع README).
set -euo pipefail

HOST="${KAJ_HOST:-ubuntu@84.13.132.250}"
KEY="${KAJ_KEY:-$HOME/.ssh/id_ed25519}"
SITE="kaj-staging.localhost"
REPO="$(cd "$(dirname "$0")/../.." && pwd)"
SSH=(ssh -o BatchMode=yes -o ConnectTimeout=25 -i "$KEY" "$HOST")
DC="cd ~/khat-erp && sudo docker compose"
BENCH="cd /home/frappe/frappe-bench && PYTHONPATH=/tmp/kaj-overlay"

case "${1:-}" in
  sync)
    tar -C "$REPO/khat_workshop" --exclude='__pycache__' --exclude='*.pyc' -czf - khat_workshop \
      | "${SSH[@]}" "cat > /tmp/kaj-overlay.tgz && $DC cp /tmp/kaj-overlay.tgz backend:/tmp/kaj-overlay.tgz >/dev/null 2>&1 \
        && $DC exec -T backend bash -c 'rm -rf /tmp/kaj-overlay && mkdir -p /tmp/kaj-overlay && tar -C /tmp/kaj-overlay -xzf /tmp/kaj-overlay.tgz && find /tmp/kaj-overlay -name \"*.py\" | wc -l' \
        && $DC exec -T backend bash -c '[ -f /tmp/kaj-staging.pid ] && kill \$(cat /tmp/kaj-staging.pid) 2>/dev/null; sleep 1; true' \
        && $DC exec -T -d backend bash -c 'cd /home/frappe/frappe-bench/sites && PYTHONPATH=/tmp/kaj-overlay exec /home/frappe/frappe-bench/env/bin/gunicorn -b 0.0.0.0:8001 -w 2 -t 120 --pid /tmp/kaj-staging.pid --access-logfile /tmp/kaj-staging-access.log --error-logfile /tmp/kaj-staging-error.log frappe.app:application' \
        && $DC exec -T backend bash -c '$BENCH bench --site $SITE clear-cache >/dev/null 2>&1; for i in 1 2 3 4 5 6 7 8 9 10; do curl -s -o /dev/null -w \"%{http_code}\" -H \"X-Frappe-Site-Name: $SITE\" http://127.0.0.1:8001/api/method/ping | grep -q 200 && { echo \"staging server: up\"; exit 0; }; sleep 1; done; echo \"staging server: DOWN\"; tail -5 /tmp/kaj-staging-error.log; exit 1'"
    ;;
  run)
    shift
    # bench execute يعيد المحاولة بتقييم النص بعد أي استثناء، فيُلحق بكل خطأ
    # حقيقي NameError لا معنى له. يُقطع الناتج عند تلك النقطة.
    "${SSH[@]}" "$DC exec -T backend bash -c '$BENCH bench --site $SITE execute $* 2>&1'" \
      | sed '/During handling of the above exception, another exception occurred/,$d'
    ;;
  setup)
    "${SSH[@]}" "$DC exec -T backend bash -c '$BENCH bench --site $SITE execute khat_workshop.setup.run_all && $BENCH bench --site $SITE clear-cache'"
    ;;
  sql)
    # الاستعلام من الدخل القياسي: يعبر ثلاث طبقات اقتباس (محلي، ssh، docker)
    # دون أن تُفسد علامات الاقتباس داخله.   echo "select …" | staging.sh sql
    "${SSH[@]}" "$DC exec -T backend bash -c 'cd /home/frappe/frappe-bench && bench --site $SITE mariadb'"
    ;;
  py)
    # كود بايثون من الدخل القياسي يُنفَّذ داخل نسخة الاختبار (frappe مهيَّأ ومتصل،
    # والحفظ عند النهاية). يُكتب وحدةً مؤقتة داخل النسخة المنسوخة من الكود —
    # bench execute لا يستدعي إلا دوالّ تطبيق مثبَّت — ولا يدخل المستودع.
    #   echo "import frappe; print(frappe.db.count('User'))" | staging.sh py
    { cat; printf '\n\ndef main():\n    pass\n'; } \
      | "${SSH[@]}" "cat > /tmp/kaj-run.py && $DC cp /tmp/kaj-run.py backend:/tmp/kaj-overlay/khat_workshop/_staging_run.py >/dev/null 2>&1 && $DC exec -T backend bash -c '$BENCH bench --site $SITE execute khat_workshop._staging_run.main 2>&1'" \
      | sed '/During handling of the above exception, another exception occurred/,$d'
    ;;
  stop)
    "${SSH[@]}" "$DC exec -T backend bash -c '[ -f /tmp/kaj-staging.pid ] && kill \$(cat /tmp/kaj-staging.pid) 2>/dev/null; echo stopped'"
    ;;
  *)
    sed -n '2,18p' "$0"; exit 1 ;;
esac
