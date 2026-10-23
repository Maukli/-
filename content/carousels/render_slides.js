// Рендер каруселей из carousels.json в PNG 1080x1350.
// Запуск: node content/carousels/render_slides.js [тема]  ->  content/carousels/out/<id>/NN.png
// Превью тем: node content/carousels/render_slides.js --preview  ->  content/carousels/out/themes.png
const { chromium } = require(require('child_process').execSync('npm root -g').toString().trim() + '/playwright');
const fs = require('fs');
const path = require('path');

const HANDLE = '@miko_oloo';
const WORDS = ['ОСАНКА', 'ПРОГРАММА', 'СУШКА'];
const dir = __dirname;
const data = JSON.parse(fs.readFileSync(path.join(dir, 'carousels.json'), 'utf8'));

// head: шрифт заголовков, body: шрифт текста, hs: множитель размера заголовков (широкие шрифты меньше)
const THEMES = {
  sand:   { label: '1. Песок', ls: -1, bg: '#F3EEE6', text: '#1E2422', soft: '#3A423F', muted: '#7A817C', accent: '#1F6F5C', onAccent: '#F3EEE6', head: 'Manrope', body: 'Manrope', hs: 1 },
  navy:   { label: '2. Тёмно-синий', ls: -1, bg: '#102033', text: '#F4F1EA', soft: '#D5DCE4', muted: '#8597AB', accent: '#FF9F5A', onAccent: '#102033', head: 'Montserrat', body: 'Manrope', hs: 0.92 },
  forest: { label: '3. Лес', ls: -1, bg: '#15302A', text: '#F2EEE4', soft: '#D3DDD7', muted: '#93ABA1', accent: '#E8B04B', onAccent: '#15302A', head: 'Manrope', body: 'Manrope', hs: 1 },
  coral:  { label: '4. Графит', ls: 0, bg: '#1B1B1E', text: '#F5F4F0', soft: '#D9D8D3', muted: '#8E8D88', accent: '#FF6F5B', onAccent: '#1B1B1E', head: 'Unbounded', body: 'Manrope', hs: 0.78 },
};
const DEFAULT_THEME = 'navy';

const fontFaces = ['manrope', 'montserrat', 'unbounded'].flatMap(f => [500, 700, 800].flatMap(w => ['cyrillic', 'latin'].map(sub => {
  const file = path.join(dir, 'fonts', `${f}-${sub}-${w}-normal.woff2`);
  const range = sub === 'latin' ? 'U+0000-00FF,U+2000-206F' : 'U+0400-045F,U+0490-0491,U+04B0-04B1,U+2116';
  const name = f[0].toUpperCase() + f.slice(1);
  return `@font-face{font-family:'${name}';font-weight:${w};src:url(data:font/woff2;base64,${fs.readFileSync(file).toString('base64')}) format('woff2');unicode-range:${range}}`;
}))).join('\n');

const esc = s => s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
const mark = s => WORDS.reduce((t, w) => t.split(w).join(`<span class="kw">${w}</span>`), esc(s));

function bodySize(text, cover) {
  if (cover) return 52;
  const n = text.length;
  return n < 120 ? 56 : n < 200 ? 50 : n < 280 ? 46 : 42;
}

function slideHtml(s, i, total, t) {
  const cover = i === 0, last = i === total - 1;
  const cls = cover ? 'cover' : last ? 'cta' : 'mid';
  const h = px => Math.round(px * t.hs) + 'px';
  return `<!doctype html><html><head><meta charset="utf-8"><style>
  ${fontFaces}
  *{box-sizing:border-box;margin:0;padding:0}
  body{width:1080px;height:1350px;font-family:'${t.body}',sans-serif;background:${t.bg};color:${t.text};overflow:hidden}
  .wrap{position:relative;width:100%;height:100%;padding:110px 96px 120px;display:flex;flex-direction:column}
  .top{display:flex;justify-content:space-between;font-size:30px;font-weight:700;color:${t.muted};letter-spacing:.5px}
  .bar{width:120px;height:10px;background:${t.accent};border-radius:5px;margin:auto 0 50px}
  h1{font-family:'${t.head}',sans-serif;font-weight:800;line-height:1.1;letter-spacing:${t.ls}px}
  .mid h1{font-size:${h(78)}}
  .cover h1{font-size:${h(100)};margin-top:auto}
  .cta h1{font-size:${h(86)};margin-top:auto}
  p{margin-top:48px;line-height:1.38;color:${t.soft};font-weight:500}
  .cover p{color:${t.accent};font-weight:700}
  .kw{color:${t.onAccent};background:${t.accent};padding:2px 14px;border-radius:10px;font-weight:800}
  .bottom{margin-top:auto;padding-top:60px;display:flex;justify-content:space-between;align-items:center;font-size:30px;font-weight:500;color:${t.muted}}
  .cover .bottom,.cta .bottom{margin-top:90px}
  .swipe{color:${t.accent};font-weight:800}
  </style></head><body><div class="wrap ${cls}">
  <div class="top"><span>${HANDLE}</span><span>${i + 1}/${total}</span></div>
  ${cover ? '' : '<div class="bar"></div>'}
  <h1>${mark(s.title)}</h1>
  <p style="font-size:${bodySize(s.body, cover)}px">${mark(s.body)}</p>
  <div class="bottom"><span>Осанка. Сила. Система.</span>${last ? '' : '<span class="swipe">Листай</span>'}</div>
  </div></body></html>`;
}

async function shot(p, html, file) {
  await p.setContent(html);
  await p.evaluate(() => document.fonts.ready);
  const over = await p.evaluate(() => document.querySelector('.wrap').scrollHeight > 1350);
  await p.screenshot({ path: file });
  return over;
}

(async () => {
  const arg = process.argv[2];
  const b = await chromium.launch();
  const p = await b.newPage({ viewport: { width: 1080, height: 1350 } });
  if (arg === '--preview') {
    // Обложка, средний слайд и призыв первой карусели в каждой теме
    const c = data[0], picks = [0, 3, c.slides.length - 1];
    const tmp = path.join(dir, 'out', '_preview');
    fs.mkdirSync(tmp, { recursive: true });
    const cells = [];
    for (const name of Object.keys(THEMES)) for (const i of picks) {
      const f = path.join(tmp, `${name}_${i}.png`);
      await shot(p, slideHtml(c.slides[i], i, c.slides.length, THEMES[name]), f);
      cells.push({ name, f });
    }
    const imgs = cells.map(c => `<img src="data:image/png;base64,${fs.readFileSync(c.f).toString('base64')}">`);
    const rows = Object.keys(THEMES).map((n, r) => `<div class="row"><div class="lbl">${THEMES[n].label}</div>${imgs.slice(r * 3, r * 3 + 3).join('')}</div>`).join('');
    await p.setViewportSize({ width: 1240, height: 400 * Object.keys(THEMES).length });
    await p.setContent(`<html><body style="margin:0;background:#fff;font:600 28px Inter">
      <style>.row{display:flex;gap:16px;align-items:center;padding:10px}.row img{width:300px;height:375px}.lbl{width:170px}</style>${rows}</body></html>`);
    await p.screenshot({ path: path.join(dir, 'out', 'themes.png'), fullPage: true });
    fs.rmSync(tmp, { recursive: true });
  } else {
    const t = THEMES[arg || DEFAULT_THEME];
    for (const c of data) {
      const out = path.join(dir, 'out', c.id);
      fs.mkdirSync(out, { recursive: true });
      for (let i = 0; i < c.slides.length; i++) {
        if (await shot(p, slideHtml(c.slides[i], i, c.slides.length, t), path.join(out, String(i + 1).padStart(2, '0') + '.png')))
          console.warn(`переполнение: ${c.id} слайд ${i + 1}`);
      }
      console.log(c.id, c.slides.length);
    }
  }
  await b.close();
})();
