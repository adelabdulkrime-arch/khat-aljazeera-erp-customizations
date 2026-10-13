// يركّب الفيديو النهائي: التسجيل + شريط النصّ السفلي + التعليق الصوتي → MP4.
//
//   node build.js <out-dir> <output.mp4>
//
// يقرأ من out-dir ما تركه tts.js وrecord.js: video/*.webm، timeline.json،
// audio/<scene>.mp3. شريط النصّ يُرسم صوراً بالمتصفح (تشكيل عربي صحيح) ويوضع
// تحت الصفحة المسجَّلة، لكل مشهد في وقته؛ والتعليق الصوتي لكل مشهد يبدأ مع
// بدايته. بداية المشهد تُقرأ من الفيديو نفسه (مؤشّر المزامنة، sync.js) لا من
// ساعة record.js.
const fs = require('fs');
const path = require('path');
const { execFileSync } = require('child_process');
const { chromium } = require('playwright');
const ffmpeg = require('ffmpeg-static');
const scenes = require('./narration');
const sync = require('./sync');

const OUT = path.resolve(process.argv[2] || 'out');
const TARGET = path.resolve(process.argv[3] || path.join(OUT, 'training.mp4'));
const W = 1280, PAGE_H = 660, OUT_H = 720;
// الشريط يبدأ فوق أسفل الصفحة بارتفاع مؤشّر المزامنة، فيغطّيه
const STRIP_Y = PAGE_H - sync.SIZE.h, STRIP = OUT_H - STRIP_Y;
const FPS = 25;
const LEAD = 0.35;                                  // الصوت يبدأ بعد بداية المشهد بقليل

async function captions(dir) {
  fs.mkdirSync(dir, { recursive: true });
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: W, height: STRIP } });
  for (const scene of scenes) {
    const text = scene.caption || '';
    await page.setContent(`<!doctype html><html dir="rtl"><body style="margin:0;width:${W}px;height:${STRIP}px;background:#131d33;
      display:flex;align-items:center;justify-content:center;border-top:3px solid #f4a900;box-sizing:border-box;
      font:600 24px/1 'Segoe UI',Tahoma,sans-serif;color:#fff">${text
        ? `<span>${text.replace(/&/g, '&amp;').replace(/</g, '&lt;')}</span>`
        : `<span style="font-weight:400;font-size:18px;color:#8f9bb3;letter-spacing:.5px">خط الجزيرة — الدليل المصوَّر</span>`}</body></html>`);
    await page.screenshot({ path: path.join(dir, scene.id + '.png') });
  }
  await browser.close();
}

// بداية كل مشهد بزمن الفيديو: أول إطار يحمل لون مؤشّره. مشهد لم يُرَ مؤشّره
// (لا يُنتظر) يوضع بين جاريه بنسبة ما سجّلته ساعة record.js.
function marks(video, timeline) {
  const raw = execFileSync(ffmpeg, ['-loglevel', 'error', '-i', video,
    '-vf', `fps=${FPS},crop=4:4:4:${STRIP_Y + 2}`, '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'],
    { maxBuffer: 1024 * 1024 * 1024 });
  const frame = 4 * 4 * 3, frames = Math.floor(raw.length / frame);
  const n = timeline.scenes.length, seen = new Array(n).fill(null);
  for (let f = 0; f < frames; f++) {
    const o = f * frame + (4 + 1) * 3;                       // بكسل من وسط المربّع
    const i = sync.decode(raw[o], raw[o + 1], raw[o + 2]);
    if (i !== null && i < n && seen[i] === null) seen[i] = f / FPS;
  }
  const total = frames / FPS;
  seen[0] = 0;                                               // البطاقة الأولى من أول إطار
  const missing = seen.map((t, i) => (t === null ? timeline.scenes[i].id : null)).filter(Boolean);
  if (missing.length) console.log('SYNC_MISSING', missing.join(','));
  const clock = timeline.scenes.map((s) => s.start).concat(timeline.total);
  const known = seen.concat(total);
  const starts = seen.map((t, i) => {
    if (t !== null) return t;
    let a = i - 1, b = i + 1;
    while (known[b] === null) b++;
    while (known[a] === null) a--;
    return known[a] + (known[b] - known[a]) * (clock[i] - clock[a]) / (clock[b] - clock[a]);
  });
  for (let i = 1; i < n; i++) if (starts[i] <= starts[i - 1]) throw new Error('مزامنة غير مرتّبة عند ' + timeline.scenes[i].id);
  console.log('SYNC', timeline.scenes.map((s, i) => s.id + ' ' + clock[i].toFixed(0) + '→' + starts[i].toFixed(0)).join(' | '));
  return { starts, total };
}

(async () => {
  const timeline = JSON.parse(fs.readFileSync(path.join(OUT, 'timeline.json'), 'utf8'));
  if (timeline.failed) throw new Error('التسجيل لم يكتمل: ' + JSON.stringify(timeline.failed));
  const video = path.join(OUT, 'video', timeline.video);
  const capDir = path.join(OUT, 'captions');
  await captions(capDir);

  const { starts, total } = marks(video, timeline);
  const list = timeline.scenes.map((s, i) => ({
    id: s.id, start: starts[i], end: i + 1 < starts.length ? starts[i + 1] : total,
  }));

  // جمل المشهد: الأولى مع بدايته، والبقية على أبعاد متساوية حتى نهايته — ما
  // يُقال ثانياً يوافق ما يُفعل ثانياً. مشهد أقصر من كلامه يعني تسجيلاً أقدم
  // من النصّ: يُعاد record.js.
  const parts = JSON.parse(fs.readFileSync(path.join(OUT, 'parts.json'), 'utf8'));
  const clips = [];
  for (const s of list) {
    const d = parts[s.id], room = s.end - s.start - LEAD - d.reduce((a, b) => a + b, 0);
    if (room < 0.3 * d.length) throw new Error('المشهد ' + s.id + ' أقصر من تعليقه بـ ' + (-room).toFixed(1) + ' ث: أعد التسجيل');
    const gap = room / d.length;
    let at = s.start + LEAD;
    d.forEach((len, k) => { clips.push({ file: s.id + (k ? '.' + (k + 1) : '') + '.mp3', at }); at += len + gap; });
  }

  const args = ['-y', '-i', video];
  list.forEach((s) => args.push('-i', path.join(capDir, s.id + '.png')));
  clips.forEach((c) => args.push('-i', path.join(OUT, 'audio', c.file)));

  const n = list.length;
  const filters = [`[0:v]fps=${FPS},pad=${W}:${OUT_H}:0:0:color=0x131d33[v0]`];
  list.forEach((s, i) => {
    filters.push(`[v${i}][${i + 1}:v]overlay=0:${STRIP_Y}:enable='between(t,${s.start.toFixed(2)},${s.end.toFixed(2)})'[v${i + 1}]`);
  });
  clips.forEach((c, i) => {
    const ms = Math.round(c.at * 1000);
    filters.push(`[${n + 1 + i}:a]adelay=${ms}|${ms}[a${i}]`);
  });
  filters.push(clips.map((c, i) => `[a${i}]`).join('') + `amix=inputs=${clips.length}:normalize=0:dropout_transition=0[a]`);

  args.push('-filter_complex', filters.join(';'), '-map', `[v${n}]`, '-map', '[a]',
    '-t', total.toFixed(2),
    '-c:v', 'libx264', '-preset', 'medium', '-crf', '24', '-pix_fmt', 'yuv420p',
    '-c:a', 'aac', '-b:a', '128k', '-ar', '44100', '-movflags', '+faststart', TARGET);

  fs.mkdirSync(path.dirname(TARGET), { recursive: true });
  execFileSync(ffmpeg, args, { stdio: ['ignore', 'ignore', 'pipe'], maxBuffer: 64 * 1024 * 1024 });
  const mb = (fs.statSync(TARGET).size / 1048576).toFixed(1);
  console.log('BUILD_OK', TARGET, mb + 'MB', total.toFixed(0) + 's');
})().catch((e) => { console.error('BUILD_FAIL', String(e && (e.stderr || e.message) || e).slice(-1500)); process.exit(1); });
