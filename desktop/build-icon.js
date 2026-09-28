// يبني build/icon.ico من أيقونة الـPWA الموجودة (مصدر واحد للشعار، بدون تكرار)
const fs = require('fs');
const path = require('path');
const pngToIco = require('png-to-ico');

const src = path.join(__dirname, '..', 'khat_workshop', 'khat_workshop', 'public', 'icons', 'icon-512.png');
const out = path.join(__dirname, 'build', 'icon.ico');

pngToIco(src)
  .then((buf) => {
    fs.mkdirSync(path.dirname(out), { recursive: true });
    fs.writeFileSync(out, buf);
    console.log(`icon.ico written (${buf.length} bytes)`);
  })
  .catch((err) => { console.error(err); process.exit(1); });
