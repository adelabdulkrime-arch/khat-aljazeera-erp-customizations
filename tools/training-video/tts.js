// يولّد التعليق الصوتي: ملف لكل جملة في out/audio (<scene>.mp3 ثم <scene>.2.mp3 …)،
// ومدّة كل مشهد في out/durations.json (ما ينتظره record.js) ومدد الجمل في
// out/parts.json (ما يوزّعه build.js). الجملة التي تغيّر نصّها يُعاد توليدها.
//   node tts.js [out-dir]
// الصوت من خدمة القراءة الصوتية في Microsoft Edge (مكتبة msedge-tts). ما يُرسَل
// إليها نصّ narration.js وحده.
const fs = require('fs');
const path = require('path');
const { execFileSync } = require('child_process');
const { MsEdgeTTS, OUTPUT_FORMAT } = require('msedge-tts');
const ffmpeg = require('ffmpeg-static');
const scenes = require('./narration');

const OUT = path.resolve(process.argv[2] || 'out');
const VOICE = process.env.KAJ_VOICE || 'ar-OM-AbdullahNeural';

const PAUSE = 1.5;                                  // أقلّ فاصل بين جملتين في المشهد
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

function duration(file) {
  let log = '';
  try { execFileSync(ffmpeg, ['-i', file], { stdio: 'pipe' }); } catch (e) { log = String(e.stderr || ''); }
  const m = /Duration: (\d+):(\d+):([\d.]+)/.exec(log);
  if (!m) throw new Error('لا مدة لـ ' + file);
  return +m[1] * 3600 + +m[2] * 60 + +m[3];
}

(async () => {
  const dir = path.join(OUT, 'audio');
  fs.mkdirSync(dir, { recursive: true });
  const durations = {}, parts = {};
  const memo = path.join(OUT, 'texts.json');
  const texts = fs.existsSync(memo) ? JSON.parse(fs.readFileSync(memo, 'utf8')) : {};
  for (const scene of scenes) for (const [k, say] of [].concat(scene.say).entries()) {
    const key = scene.id + (k ? '.' + (k + 1) : '');
    const file = path.join(dir, key + '.mp3');
    if (!(key in texts) && fs.existsSync(file)) texts[key] = say;      // ملف من قبل هذه الذاكرة
    if (!fs.existsSync(file) || texts[key] !== say || process.env.KAJ_TTS_FORCE) {
      const tmp = path.join(dir, '_' + key);
      fs.mkdirSync(tmp, { recursive: true });
      // الخدمة تحدّ عدد الطلبات المتتابعة (429): مهلة بين المشاهد، وإعادة بمهلة أطول
      for (let attempt = 1; ; attempt++) {
        const tts = new MsEdgeTTS();
        try {
          await tts.setMetadata(VOICE, OUTPUT_FORMAT.AUDIO_24KHZ_96KBITRATE_MONO_MP3);
          const made = await tts.toFile(tmp, say, { rate: '-4%' });
          fs.renameSync(made.audioFilePath, file);
          break;
        } catch (e) {
          if (attempt >= 7) throw e;
          console.log('  retry', key, attempt, String(e && e.message || e).slice(0, 60));
          await sleep(6000 * attempt);
        } finally {
          try { tts.close(); } catch (e) { /* مغلق */ }
        }
      }
      fs.rmSync(tmp, { recursive: true, force: true });
      texts[key] = say;
      fs.writeFileSync(memo, JSON.stringify(texts, null, 2));
      await sleep(3000);
    }
    const d = +duration(file).toFixed(2);
    (parts[scene.id] = parts[scene.id] || []).push(d);
    console.log(key, d + 's');
  }
  // مدّة المشهد: جمله وبينها فاصل. record.js لا يُنهي المشهد قبلها.
  for (const [id, list] of Object.entries(parts)) durations[id] = +(list.reduce((a, b) => a + b, 0) + PAUSE * (list.length - 1)).toFixed(2);
  fs.writeFileSync(memo, JSON.stringify(texts, null, 2));
  fs.writeFileSync(path.join(OUT, 'parts.json'), JSON.stringify(parts, null, 2));
  fs.writeFileSync(path.join(OUT, 'durations.json'), JSON.stringify(durations, null, 2));
  console.log('TOTAL', Object.values(durations).reduce((a, b) => a + b, 0).toFixed(1) + 's');
  process.exit(0);
})().catch((e) => { console.error('TTS_FAIL', e && (e.message || e)); process.exit(1); });
