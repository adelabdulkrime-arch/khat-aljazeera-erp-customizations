'use strict';

const { app } = require('electron');
const fs = require('fs');
const path = require('path');

// العنوان الافتراضي — يُستخدم ما لم يغيّره المستخدم من شاشة الإعدادات.
//
// `localhost` وليس عنوان IP ولا الدومين السحابي، لأنه الوحيد الذي لا يتعطّل:
//
//   - عنوان IP ثابت مكتوب هنا يصلح يوماً واحداً. حدث فعلاً أن تبدّل عنوان جهاز
//     السيرفر ثلاث مرات في يوم (192.168.1.101 ← 192.168.197.66 ← 10.86.67.20)
//     مع تغيّر الشبكة، فصار التطبيق يعرض «لا يمكن الوصول» بينما النظام يعمل.
//   - دومين سحابي لم يُنشأ بعد يستقبل كل من يثبّت التطبيق بشاشة خطأ.
//   - `localhost` يعمل دائماً على جهاز السيرفر نفسه، وهو أول جهاز يُجرَّب عليه.
//
// على أجهزة الموظفين الأخرى: اسم الجهاز أمتن من رقمه — `http://<الاسم>.local`
// (مثال: http://Adell.local) يصمد عبر تغيّر العناوين والشبكات، ولا يحتاج إعداد
// راوتر. يضبطه المستخدم من (ملف ← إعدادات الاتصال) بلا إعادة بناء، وكذلك
// الدومين السحابي عند النشر عليه.
const DEFAULT_SERVER = 'http://localhost';

const configPath = () => path.join(app.getPath('userData'), 'config.json');

/** يتحقق أن العنوان https/http وله مضيف صالح، ويُرجع الأصل فقط (بدون مسار). */
function normalizeServer(raw) {
  if (typeof raw !== 'string' || !raw.trim()) return null;
  let value = raw.trim();
  // أي بروتوكول آخر (file:, javascript:, ftp:...) يُرفض بدل أن يُلصق به
  // https:// فيتحوّل `file:///c:/x` إلى مضيف وهمي اسمه "file".
  if (/^[a-z][a-z0-9+.-]*:/i.test(value) && !/^https?:\/\//i.test(value)) return null;
  if (!/^https?:\/\//i.test(value)) value = `https://${value}`;
  try {
    const url = new URL(value);
    if (url.protocol !== 'https:' && url.protocol !== 'http:') return null;
    if (!url.hostname) return null;
    return url.origin;
  } catch {
    return null;
  }
}

function readServer() {
  try {
    const raw = fs.readFileSync(configPath(), 'utf8');
    const saved = normalizeServer(JSON.parse(raw).server);
    if (saved) return saved;
  } catch {
    // لا يوجد ملف إعدادات بعد، أو تالف — نرجع للافتراضي
  }
  return DEFAULT_SERVER;
}

function writeServer(raw) {
  const server = normalizeServer(raw);
  if (!server) return null;
  try {
    fs.writeFileSync(configPath(), JSON.stringify({ server }, null, 2), 'utf8');
    return server;
  } catch {
    return null;
  }
}

module.exports = { DEFAULT_SERVER, normalizeServer, readServer, writeServer };
