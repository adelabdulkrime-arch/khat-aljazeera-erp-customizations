// معاينة محلية لواجهة النظام (المكتب) على نسخة الاختبار.
//
// تعرض نسخة الاختبار kaj-staging.localhost على http://127.0.0.1:8766، بملفات
// المستودع مكان /assets/khat_workshop المنشورة. فيُجرَّب أي تعديل على
// desk.js وrtl_fixes.css — وأي إدخال بيانات — دون أن يمسّ الإنتاج شيء.
//
// نسخة الاختبار موقع ثانٍ على الخادم نفسه بقاعدة بيانات مستقلة (نسخة من
// الإنتاج)، بريدها مكتوم ومهامّها المجدولة موقوفة. يُوصَل إليها بنفق SSH إلى
// حاوية backend مباشرة، لأن حاوية frontend تثبّت اسم موقع الإنتاج:
//
//   tools/desk-check/staging.sh sync
//   ssh -N -L 8082:<عنوان حاوية backend>:8001 ubuntu@<الخادم>
//   node tools/desk-check/serve.js
//
// الكتابة تذهب لنسخة الاختبار وحدها: اسم الموقع مثبّت هنا في ترويسة كل طلب،
// وموقع الإنتاج لا يُطلب منه إلا ملفات ثابتة بـGET.
const http = require('http'), fs = require('fs'), path = require('path');

const SITE = 'kaj-staging.localhost';
const BACKEND = {host: '127.0.0.1', port: +(process.env.KAJ_BACKEND_PORT || 8082)};
const STATIC = 'https://khat.onemedia24.xyz';        // الحزم ذات البصمة والملفات العامة: GET فقط
const PUBLIC = path.join(__dirname, '..', '..', 'khat_workshop', 'khat_workshop', 'public');
const TYPES = {'.js': 'text/javascript; charset=utf-8', '.css': 'text/css; charset=utf-8', '.json': 'application/json',
  '.png': 'image/png', '.webp': 'image/webp', '.svg': 'image/svg+xml', '.ico': 'image/x-icon', '.woff2': 'font/woff2'};
const OURS = '/assets/khat_workshop/';

const cache = new Map();

function local(url, res) {
  const rel = decodeURIComponent(url.slice(OURS.length));
  const file = path.join(PUBLIC, rel);
  if (!file.startsWith(PUBLIC) || !fs.existsSync(file) || !fs.statSync(file).isFile()) { res.writeHead(404); return res.end('not found'); }
  res.writeHead(200, {'Content-Type': TYPES[path.extname(file)] || 'application/octet-stream', 'Cache-Control': 'no-store'});
  res.end(fs.readFileSync(file));
}

async function fromStatic(url, res) {
  let hit = cache.get(url);
  if (!hit) {
    const up = await fetch(STATIC + url, {redirect: 'manual'});
    hit = {status: up.status, type: up.headers.get('content-type') || 'application/octet-stream', body: Buffer.from(await up.arrayBuffer())};
    if (up.status === 200) cache.set(url, hit);
  }
  res.writeHead(hit.status, {'Content-Type': hit.type, 'Cache-Control': 'max-age=3600'});
  res.end(hit.body);
}

function toBackend(req, res) {
  const headers = {...req.headers, host: SITE, 'x-frappe-site-name': SITE, 'x-forwarded-proto': 'http'};
  delete headers['accept-encoding'];
  delete headers.origin; delete headers.referer;
  const up = http.request({...BACKEND, method: req.method, path: req.url, headers}, ur => {
    const h = {...ur.headers};
    if (h['set-cookie']) h['set-cookie'] = h['set-cookie'].map(c => c.replace(/;\s*Secure/ig, '').replace(/;\s*Domain=[^;]*/ig, ''));
    res.writeHead(ur.statusCode, h);
    ur.pipe(res);
  });
  up.on('error', e => { if (!res.headersSent) res.writeHead(502); res.end('backend: ' + e.message); });
  req.pipe(up);
}

http.createServer((req, res) => {
  const url = req.url.split('?')[0];
  const fail = e => { if (!res.headersSent) res.writeHead(502); res.end(String(e && e.message || e)); };
  if (url.startsWith(OURS)) return local(url, res);
  // أدوات الفحص نفسها (audit.js…) تُحمَّل في الصفحة من هنا
  if (url.startsWith('/__kaj/')) {
    const file = path.join(__dirname, path.basename(url));
    if (!fs.existsSync(file)) { res.writeHead(404); return res.end('not found'); }
    res.writeHead(200, {'Content-Type': TYPES[path.extname(file)] || 'text/plain; charset=utf-8', 'Cache-Control': 'no-store'});
    return res.end(fs.readFileSync(file));
  }
  if (url.startsWith('/assets/') || url.startsWith('/files/')) {
    if (req.method !== 'GET') { res.writeHead(405); return res.end('read-only'); }
    return fromStatic(req.url, res).catch(fail);
  }
  // الإشعارات اللحظية غير مطلوبة للفحص، والمكتب يعمل بدونها
  if (url.startsWith('/socket.io')) { res.writeHead(404); return res.end(); }
  toBackend(req, res);
}).listen(8766, '127.0.0.1', () => console.log('desk-check: http://127.0.0.1:8766  ←  ' + SITE));
