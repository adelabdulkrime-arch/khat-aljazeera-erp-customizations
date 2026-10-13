#!/usr/bin/env bash
# نفق SSH إلى خادم نسخة الاختبار (gunicorn على المنفذ 8001 داخل حاوية backend)،
# يُعاد فتحه تلقائياً إن انقطع الاتصال. عنوان الحاوية يُقرأ في كل محاولة لأنه
# يتغيّر متى أُعيد إنشاؤها.
HOST="${KAJ_HOST:-ubuntu@84.13.132.250}"
KEY="${KAJ_KEY:-$HOME/.ssh/id_ed25519}"
PORT="${KAJ_BACKEND_PORT:-8082}"
while true; do
  IP=$(ssh -o BatchMode=yes -o ConnectTimeout=20 -i "$KEY" "$HOST" \
    'sudo docker inspect -f "{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}" khat-erp-backend-1' 2>/dev/null)
  if [ -n "$IP" ]; then
    echo "$(date +%T) tunnel 127.0.0.1:$PORT -> $IP:8001"
    ssh -o BatchMode=yes -o ExitOnForwardFailure=yes -o ServerAliveInterval=20 -o ServerAliveCountMax=3 \
      -N -L "127.0.0.1:$PORT:$IP:8001" -i "$KEY" "$HOST"
  fi
  echo "$(date +%T) tunnel down — retrying"
  sleep 3
done
