// يتحقق أن كل رسالة يبنيها جافاسكربت صفحة الدخول في الإطار لها ترجمة عربية
// في LATE_STRINGS (login_lang.js).
//
//   node tools/login-check/check-strings.js
//
// القائمة أدناه مستخرَجة من مصدر الإطار:
//   grep -oE '__\("[^"]+"' frappe/templates/includes/login/login.js | sort -u
// وعند ترقية Frappe أعد استخراجها: رسالة جديدة غير مترجمة تظهر إنجليزية
// وسط واجهة عربية، ولا يصادفها أحد إلا مستخدم في لحظة خطأ.
const fs = require('fs');
const path = require('path');

const FRAMEWORK_JS_STRINGS = [
  'Both login and password required',
  'Create Account',
  'Email is required.',
  'Enter Code displayed in OTP App.',
  'Full name is required.',
  'Invalid Email.',
  'Invalid credentials, try again.',
  'OTP setup using OTP App was not completed. Please contact Administrator.',
  'Oops! Something went wrong.',
  'Password is required.',
  'Please enter a valid email.',
  'SMS was not sent. Please contact Administrator.',
  'Send Link',
  'Send login link',
  'Sent',
  'Something went wrong.',
  'Success',
  'Too many requests. Please try again later.',
  'Verification Code',
  'Verification code email not sent. Please contact Administrator.',
  'Verification',
  'Verify',
  'Verifying...',
];

// translateLate يتجاهل أي نص أطول من هذا
const MAX_LEN = 90;

const file = path.join(__dirname, '..', '..', 'khat_workshop', 'khat_workshop', 'public', 'js', 'login_lang.js');
const src = fs.readFileSync(file, 'utf8');
const start = src.indexOf('var LATE_STRINGS = {');
const end = src.indexOf('};', start);
if (start < 0 || end < 0) {
  console.error('لم يُعثر على LATE_STRINGS');
  process.exit(1);
}
// الكائن حرفيّ بلا تعابير، فتقييمه آمن ويغني عن تحليل يدوي للنصوص
const table = new Function('return ' + src.slice(start + 'var LATE_STRINGS = '.length, end + 1))();
const keys = Object.keys(table);

const trim = s => s.replace(/[.!]$/, '');
const covered = s => s in table || trim(s) in table;
const missing = FRAMEWORK_JS_STRINGS.filter(s => !covered(s));
const tooLong = keys.filter(k => k.length > MAX_LEN);
const empty = keys.filter(k => !String(table[k]).trim());
const latinOnly = keys.filter(k => !/[؀-ۿ]/.test(String(table[k])));

console.log('مفاتيح LATE_STRINGS :', keys.length);
console.log('رسائل الإطار        :', FRAMEWORK_JS_STRINGS.length, '| مغطّاة:', FRAMEWORK_JS_STRINGS.length - missing.length);
console.log('ناقصة               :', missing.length ? missing : 'لا شيء');
console.log('أطول من ' + MAX_LEN + ' حرفاً    :', tooLong.length ? tooLong : 'لا شيء');
console.log('ترجمة فارغة         :', empty.length ? empty : 'لا شيء');
console.log('ترجمة بلا حروف عربية:', latinOnly.length ? latinOnly : 'لا شيء');

process.exit(missing.length || tooLong.length || empty.length || latinOnly.length ? 1 : 0);
