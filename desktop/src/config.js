'use strict';

const { app } = require('electron');
const fs = require('fs');
const path = require('path');

// الدومين الافتراضي — يُستخدم ما لم يغيّره المستخدم من شاشة الإعدادات
const DEFAULT_SERVER = 'https://khat.onemedia24.xyz';

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
