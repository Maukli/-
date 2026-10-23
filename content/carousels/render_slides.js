// Рендер каруселей из carousels.json в PNG 1080x1350.
// Запуск: node content/carousels/render_slides.js  ->  content/carousels/out/<id>/NN.png
const { chromium } = require(require('child_process').execSync('npm root -g').toString().trim() + '/playwright');
const fs = require('fs');
const path = require('path');

const HANDLE = '@miko_oloo';
const WORDS = ['ОСАНКА', 'ПРОГРАММА', 'СУШКА'];
const dir = __dirname;
const data = JSON.parse(fs.readFileSync(path.join(dir, 'carousels.json'), 'utf8'));

const esc = s => s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
const mark = s => WORDS.reduce((t, w) => t.split(w).join(`<span class="kw">${w}</span>`), esc(s));

function bodySize(text, cover) {
  if (cover) return 52;
  const n = text.length;
  return n < 120 ? 58 : n < 200 ? 52 : n < 280 ? 47 : 43;
}

function slideHtml(s, i, total) {
  const cover = i === 0, last = i === total - 1;
  const cls = cover ? 'cover' : last ? 'cta' : 'mid';
  return `<!doctype html><html><head><meta charset="utf-8"><style>
  *{box-sizing:border-box;margin:0;padding:0}
  body{width:1080px;height:1350px;font-family:Inter,sans-serif;background:#111312;color:#f2f2ee;overflow:hidden}
  .wrap{position:relative;width:100%;height:100%;padding:110px 96px 120px;display:flex;flex-direction:column}
  .top{display:flex;justify-content:space-between;font-size:30px;font-weight:600;color:#9aa39c;letter-spacing:.5px}
  .bar{width:120px;height:10px;background:#c8f04b;border-radius:5px;margin:auto 0 50px}
  h1{font-weight:800;line-height:1.08;letter-spacing:-1px}
  .mid h1{font-size:80px}
  .cover h1{font-size:104px;margin-top:auto}
  .cta h1{font-size:88px;margin-top:auto}
  p{margin-top:48px;line-height:1.35;color:#d6d9d3;font-weight:500}
  .cover p{color:#c8f04b;font-weight:700}
  .kw{color:#111312;background:#c8f04b;padding:2px 14px;border-radius:10px;font-weight:800}
  .bottom{margin-top:auto;padding-top:60px;display:flex;justify-content:space-between;align-items:center;font-size:30px;color:#9aa39c}
  .cover .bottom,.cta .bottom{margin-top:90px}
  .swipe{color:#c8f04b;font-weight:700}
  </style></head><body><div class="wrap ${cls}">
  <div class="top"><span>${HANDLE}</span><span>${i + 1}/${total}</span></div>
  ${cover ? '' : '<div class="bar"></div>'}
  <h1>${mark(s.title)}</h1>
  <p style="font-size:${bodySize(s.body, cover)}px">${mark(s.body)}</p>
  <div class="bottom"><span>Осанка. Сила. Система.</span>${last ? '' : '<span class="swipe">Листай</span>'}</div>
  </div></body></html>`;
}

(async () => {
  const b = await chromium.launch();
  const p = await b.newPage({ viewport: { width: 1080, height: 1350 } });
  for (const c of data) {
    const out = path.join(dir, 'out', c.id);
    fs.mkdirSync(out, { recursive: true });
    for (let i = 0; i < c.slides.length; i++) {
      await p.setContent(slideHtml(c.slides[i], i, c.slides.length));
      await p.evaluate(() => document.fonts.ready);
      const over = await p.evaluate(() => document.querySelector('.wrap').scrollHeight > 1350);
      if (over) console.warn(`переполнение: ${c.id} слайд ${i + 1}`);
      await p.screenshot({ path: path.join(out, String(i + 1).padStart(2, '0') + '.png') });
    }
    console.log(c.id, c.slides.length);
  }
  await b.close();
})();
