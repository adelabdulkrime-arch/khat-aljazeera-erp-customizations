// مؤشّر المزامنة: مربّع صغير في زاوية الصفحة يتلوّن بلون خاص بكل مشهد.
//
// ساعة التسجيل ليست ساعة الحائط: تسجيل طوله 700 ثانية خرج ملفّه 727، والفرق
// يتراكم — في آخر الفيديو كان التعليق يسبق الصورة بعشرين ثانية. فبداية كل مشهد
// لا تؤخذ من ساعة record.js بل تُقرأ من الفيديو نفسه: أول إطار يحمل لون المشهد.
// build.js يغطّي المربّع بشريط النصّ.
const LEVELS = [32, 128, 224];
const PALETTE = [];
for (const r of LEVELS) for (const g of LEVELS) for (const b of LEVELS) {
  if (r === g && g === b) continue;          // الرماديات تشبه خلفيات الصفحات
  PALETTE.push([r, g, b]);
}

const SIZE = { w: 12, h: 8 };                // أسفل يسار الصفحة

function color(i) {
  if (i >= PALETTE.length) throw new Error('مشاهد أكثر من ألوان المزامنة: ' + i);
  return 'rgb(' + PALETTE[i].join(',') + ')';
}

// رقم المشهد من لون بكسل في الفيديو، أو null إن لم يكن لون مؤشّر
function decode(r, g, b) {
  for (let i = 0; i < PALETTE.length; i++) {
    const p = PALETTE[i];
    if (Math.abs(p[0] - r) < 40 && Math.abs(p[1] - g) < 40 && Math.abs(p[2] - b) < 40) return i;
  }
  return null;
}

module.exports = { SIZE, color, decode };
