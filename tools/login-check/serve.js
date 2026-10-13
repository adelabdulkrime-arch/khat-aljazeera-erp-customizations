// خادم اختبار محلي لصفحة الدخول.
//
// يعرض صفحة الدخول الحيّة نفسها — HTML الإطار وحزمه كما هي — لكن بملفات
// المستودع مكان ملفاتنا المنشورة، على http://127.0.0.1:8765/login. فيُفحص
// التعديل بقواعد الإطار الحقيقية قبل أي نشر، دون حقن يدوي، ودون أي صلة
// بجلسة متصفّح مفتوحة على الموقع (الأصل مختلف فلا تُشارَك الكوكيز).
//
// للقراءة فقط: كل طلب غير GET يُرفض هنا ولا يصل الخادم، فلا يمكن لاختبار أن
// يسجّل دخولاً أو يستهلك حدّ المحاولات.
//
//   node tools/login-check/serve.js [https://الموقع]
const http = require('http'), fs = require('fs'), path = require('path');

const UPSTREAM = (process.argv[2] || 'https://khat.onemedia24.xyz').replace(/\/$/, '');
const APP = path.join(__dirname, '..', '..', 'khat_workshop', 'khat_workshop', 'public');
// ملفاتنا: تُقدَّم من المستودع بالمسار الذي تطلبه الصفحة الحيّة
const LOCAL = {
  '/assets/khat_workshop/css/login.css': path.join(APP, 'css', 'login.css'),
  '/assets/khat_workshop/js/login_lang.js': path.join(APP, 'js', 'login_lang.js'),
  '/assets/khat_workshop/js/pwa.js': path.join(APP, 'js', 'pwa.js'),
  '/assets/khat_workshop/icons/login-art.webp': path.join(APP, 'icons', 'login-art.webp'),
  '/checker.js': path.join(__dirname, 'checker.js'),
  '/matrix.js': path.join(__dirname, 'matrix.js'),
  // مسارات الحقن اليدوي القديمة (راجع README)
  '/login.css': path.join(APP, 'css', 'login.css'),
  '/login_lang.js': path.join(APP, 'js', 'login_lang.js'),
  '/login-art.webp': path.join(APP, 'icons', 'login-art.webp'),
};
const TYPES = {'.js': 'text/javascript; charset=utf-8', '.css': 'text/css; charset=utf-8', '.webp': 'image/webp'};

// التصغير نفسه الذي يجريه branding._login_css قبل تضمين الملف في الصفحة:
// ما يُفحص هنا هو ما سيصل المتصفح حرفياً.
const minify = css => css
  .replace(/\/\*[\s\S]*?\*\//g, '')
  .replace(/\s+/g, ' ')
  .replace(/\s*([{};,>])\s*/g, '$1')
  .trim();

const cache = new Map();   // الحزم ذات البصمة لا تتغيّر: تُجلب مرة واحدة

async function loginPage(req, res) {
  // لغة الصفحة يحدّدها كوكي preferred_language وحده؛ لا يُمرَّر غيره
  const lang = /(?:^|;\s*)preferred_language=([^;]+)/.exec(req.headers.cookie || '');
  const up = await fetch(UPSTREAM + req.url, {
    headers: lang ? {cookie: 'preferred_language=' + lang[1]} : {},
    redirect: 'manual',
  });
  let html = await up.text();
  const css = minify(fs.readFileSync(LOCAL['/assets/khat_workshop/css/login.css'], 'utf8'));
  const tag = /<style id="kaj-login-css">[\s\S]*?<\/style>/;
  if (!tag.test(html)) throw new Error('الصفحة الحيّة بلا <style id="kaj-login-css"> (HTTP ' + up.status + ')');
  html = html.replace(tag, () => '<style id="kaj-login-css">' + css + '</style>');
  res.writeHead(200, {'Content-Type': 'text/html; charset=utf-8', 'Cache-Control': 'no-store'});
  res.end(html);
}

async function passthrough(req, res, url) {
  let hit = cache.get(url);
  if (!hit) {
    const up = await fetch(UPSTREAM + url, {redirect: 'manual'});
    hit = {status: up.status, type: up.headers.get('content-type') || 'application/octet-stream',
           body: Buffer.from(await up.arrayBuffer())};
    if (up.status === 200 && url.startsWith('/assets/')) cache.set(url, hit);
  }
  res.writeHead(hit.status, {'Content-Type': hit.type, 'Cache-Control': 'no-store'});
  res.end(hit.body);
}

http.createServer((req, res) => {
  // الحقن اليدوي من الصفحة الحيّة (https) يجلب من localhost: يلزمه CORS
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Private-Network', 'true');
  res.setHeader('Access-Control-Allow-Headers', '*');
  if (req.method === 'OPTIONS') { res.writeHead(204); return res.end(); }
  if (req.method !== 'GET') { res.writeHead(405); return res.end('read-only'); }

  const url = req.url.split('?')[0];
  const fail = e => { if (!res.headersSent) res.writeHead(502); res.end(String(e && e.message || e)); };
  const f = LOCAL[url];
  if (f) {
    try {
      res.writeHead(200, {'Content-Type': TYPES[path.extname(f)] || 'application/octet-stream', 'Cache-Control': 'no-store'});
      return res.end(fs.readFileSync(f));
    } catch (e) { return fail(e); }
  }
  if (url === '/login') return loginPage(req, res).catch(fail);
  if (url.startsWith('/assets/') || url === '/website_script.js') return passthrough(req, res, req.url).catch(fail);
  res.writeHead(404); res.end('not found');
}).listen(8765, '127.0.0.1', () => console.log('login-check: http://127.0.0.1:8765/login  ←  ' + UPSTREAM));
