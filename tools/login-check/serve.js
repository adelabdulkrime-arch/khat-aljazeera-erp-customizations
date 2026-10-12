// خادم اختبار محلي لصفحة الدخول.
//
// يقدّم login.css وlogin_lang.js وصورة الشعار من المستودع مباشرة، فتُحقَن
// فوق الصفحة الحيّة وتُفحص بقواعد الإطار الحقيقية قبل أي نشر. التشغيل:
//   node tools/login-check/serve.js
const http = require('http'), fs = require('fs'), path = require('path');
const APP = path.join(__dirname, '..', '..', 'khat_workshop', 'khat_workshop', 'public');
const FILES = {
  '/login.css': path.join(APP, 'css', 'login.css'),
  '/login_lang.js': path.join(APP, 'js', 'login_lang.js'),
  '/login-art.webp': path.join(APP, 'icons', 'login-art.webp'),
  '/checker.js': path.join(__dirname, 'checker.js'),
};
const TYPES = {'.js': 'text/javascript; charset=utf-8', '.css': 'text/css; charset=utf-8', '.webp': 'image/webp'};

http.createServer((req, res) => {
  // الصفحة الحيّة (https) تجلب من localhost: يلزم CORS وإذن الشبكة الخاصة
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Private-Network', 'true');
  res.setHeader('Access-Control-Allow-Headers', '*');
  res.setHeader('Cache-Control', 'no-store');
  if (req.method === 'OPTIONS') { res.writeHead(204); return res.end(); }
  const f = FILES[req.url.split('?')[0]];
  if (!f) { res.writeHead(404); return res.end('not found'); }
  try {
    res.writeHead(200, {'Content-Type': TYPES[path.extname(f)] || 'application/octet-stream'});
    res.end(fs.readFileSync(f));
  } catch (e) { res.writeHead(500); res.end(String(e)); }
}).listen(8765, '127.0.0.1', () => console.log('login-check: http://127.0.0.1:8765'));
