// Рендер каруселей из carousels.json в PNG 1080x1350.
// Запуск: node content/carousels/render_slides.js [тема]  ->  content/carousels/out/<id>/NN.png
// Превью тем: node content/carousels/render_slides.js --preview  ->  content/carousels/out/themes.png
const { chromium } = require(require('child_process').execSync('npm root -g').toString().trim() + '/playwright');
const fs = require('fs');
const path = require('path');

const HANDLE = '@miko_oloo';
const WORDS = ['ОСАНКА', 'ПРОГРАММА', 'СУШКА'];
const dir = __dirname;
const data = JSON.parse(fs.readFileSync(process.env.CAROUSELS || path.join(dir, 'carousels.json'), 'utf8'));
const OUT = process.env.OUT || path.join(dir, 'out');

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
const mark = s => WORDS.reduce((t, w) => t.split(w).join(`<span class="kw">${w}</span>`), esc(s)).replace(/\n/g, '<br>');

function bodySize(text, cover, img) {
  if (cover) return 52;
  const n = text.length;
  if (img) return n < 120 ? 44 : n < 200 ? 40 : n < 280 ? 37 : 34;
  return n < 120 ? 56 : n < 200 ? 50 : n < 280 ? 46 : 42;
}

// Утка для обложки с хуком "Стоишь как утка?": простая плоская фигура в цвете акцента
const duck = t => `<svg class="duck" viewBox="0 0 420 380" xmlns="http://www.w3.org/2000/svg">
  <path d="M70 215 L18 132 L128 182 Z" fill="${t.accent}"/>
  <path d="M262 92 Q262 196 300 214 L340 230 Q330 320 210 320 Q80 320 62 232 Q60 170 150 168 Q228 166 246 150 Z" fill="${t.accent}"/>
  <circle cx="300" cy="98" r="62" fill="${t.accent}"/>
  <path d="M352 86 L414 104 L352 124 Z" fill="#FFD27A"/>
  <circle cx="318" cy="84" r="10" fill="${t.bg}"/>
  <path d="M120 220 Q190 200 260 236 Q200 282 120 220 Z" fill="${t.bg}" opacity=".18"/>
  <path d="M178 320 L178 360 M236 320 L236 360" stroke="#FFD27A" stroke-width="12" stroke-linecap="round"/>
  <path d="M160 362 L200 362 M218 362 L258 362" stroke="#FFD27A" stroke-width="12" stroke-linecap="round"/>
</svg>`;

const dataUri = rel => {
  const file = path.join(dir, 'img', rel);
  const mime = /\.png$/i.test(rel) ? 'image/png' : 'image/jpeg';
  return `data:${mime};base64,${fs.readFileSync(file).toString('base64')}`;
};

// Пометки поверх фото, координаты в процентах блока с фото:
// {type:'circle', x, y, r} | {type:'arrow', x1, y1, x2, y2} | {type:'line', points:[[x,y],...]} | {type:'label', x, y, text}
function marksSvg(marks, t) {
  if (!marks || !marks.length) return '';
  const els = marks.map(m => {
    if (m.type === 'circle') return `<ellipse cx="${m.x}" cy="${m.y}" rx="${m.r}" ry="${m.ry || m.r}" fill="none" stroke="${t.accent}" stroke-width="0.9" vector-effect="non-scaling-stroke" class="mk"/>`;
    if (m.type === 'arrow') return `<line x1="${m.x1}" y1="${m.y1}" x2="${m.x2}" y2="${m.y2}" stroke="${t.accent}" class="mk" marker-end="url(#ah)"/>`;
    if (m.type === 'line') return `<polyline points="${m.points.map(p => p.join(',')).join(' ')}" fill="none" stroke="${t.accent}" class="mk" stroke-dasharray="${m.dash ? '2 1.5' : 'none'}"/>`;
    return '';
  }).join('');
  const labels = marks.filter(m => m.type === 'label').map(m => `<div class="mlabel" style="left:${m.x}%;top:${m.y}%">${esc(m.text)}</div>`).join('');
  return `<div class="marks"><svg viewBox="0 0 100 100" preserveAspectRatio="none"><defs><marker id="ah" viewBox="0 0 10 10" refX="7" refY="5" markerWidth="5" markerHeight="5" orient="auto-start-reverse"><path d="M0 0 L10 5 L0 10 z" fill="${t.accent}"/></marker></defs>${els}</svg>${labels}</div>`;
}

function slideHtml(s, i, total, t) {
  const cover = i === 0, last = i === total - 1;
  const layout = s.layout || 'plain';
  const cls = layout === 'plain' ? (cover ? 'cover' : last ? 'cta' : 'mid') : layout;
  const h = px => Math.round(px * t.hs) + 'px';
  const img = s.img && fs.readFileSync(path.join(dir, 'img', s.img + '.png')).toString('base64');
  const photo = s.photo && dataUri(s.photo);
  const focus = s.focus || '50% 50%';
  const head = `<div class="top"><span>${HANDLE}</span><span>${i + 1}/${total}</span></div>`;
  const foot = `<div class="bottom"><span>Осанка. Сила. Система.</span>${last ? '' : '<span class="swipe">Листай</span>'}</div>`;
  const title = `<h1>${mark(s.title)}</h1>`;
  const body = s.body ? `<p>${mark(s.body)}</p>` : '';
  let inner;
  if (layout === 'plain') {
    inner = `${head}
  ${cover ? (s.duck ? duck(t) : '') : '<div class="bar"></div>'}
  ${title}
  <p style="font-size:${bodySize(s.body, cover, img)}px">${mark(s.body)}</p>
  ${img ? `<div class="pic"><img src="data:image/png;base64,${img}"></div>` : ''}
  ${foot}`;
  } else if (layout === 'photo-top' || layout === 'exercise-annotated') {
    const second = s.photo2 ? `<img src="${dataUri(s.photo2)}" style="object-position:${s.focus2 || '50% 50%'}">` : '';
    inner = `<div class="ph${s.photo2 ? ' duo' : ''}"><img src="${photo}" style="object-position:${focus};${s.fit ? 'object-fit:' + s.fit + ';' : ''}${s.bw ? 'filter:grayscale(1) contrast(1.12) brightness(.92)' : ''}">${second}${marksSvg(s.marks, t)}</div>
  ${head}<div class="txt"><div class="bar"></div>${title}${body}</div>${foot}`;
  } else if (layout === 'big-number') {
    inner = `<img class="bg" src="${photo}" style="object-position:${focus}"><div class="shade"></div>
  ${head}<div class="txt"><div class="num">${esc(s.number || '')}</div>${title}${body}</div>${foot}`;
  } else {
    // cover-photo, photo-full-card, cta-photo: фото на весь слайд, текст снизу
    inner = `<img class="bg" src="${photo}" style="object-position:${focus}"><div class="shade"></div>${marksSvg(s.marks, t)}
  ${head}<div class="txt">${layout === 'cover-photo' ? '' : '<div class="bar"></div>'}${title}${body}</div>${foot}`;
  }
  const n = (s.body || '').length;
  return `<!doctype html><html><head><meta charset="utf-8"><style>
  ${fontFaces}
  *{box-sizing:border-box;margin:0;padding:0}
  body{width:1080px;height:1350px;font-family:'${t.body}',sans-serif;background:${t.bg};color:${t.text};overflow:hidden}
  .wrap{position:relative;width:100%;height:100%;padding:110px 96px 120px;display:flex;flex-direction:column}
  .top{position:relative;z-index:3;display:flex;justify-content:space-between;font-size:30px;font-weight:700;color:${t.muted};letter-spacing:.5px}
  .bar{width:120px;height:10px;background:${t.accent};border-radius:5px;margin:auto 0 50px}
  h1{font-family:'${t.head}',sans-serif;font-weight:800;line-height:1.1;letter-spacing:${t.ls}px}
  .mid h1{font-size:${h(78)}}
  .cover h1{font-size:${h(100)};margin-top:auto}
  .cta h1{font-size:${h(86)};margin-top:auto}
  p{margin-top:48px;line-height:1.38;color:${t.soft};font-weight:500}
  .cover p{color:${t.accent};font-weight:700}
  .kw{color:${t.onAccent};background:${t.accent};padding:2px 14px;border-radius:10px;font-weight:800}
  .bottom{position:relative;z-index:3;margin-top:auto;padding-top:60px;display:flex;justify-content:space-between;align-items:center;font-size:30px;font-weight:500;color:${t.muted}}
  .cover .bottom,.cta .bottom{margin-top:90px}
  .swipe{color:${t.accent};font-weight:800}
  .duck{width:500px;align-self:flex-end;margin-top:40px;margin-bottom:40px}
  .duck + h1{margin-top:auto}
  .has-img .bar{margin:50px 0 40px}
  .has-img h1{font-size:${h(64)}}
  .has-img p{margin-top:30px}
  .pic{flex:1;position:relative;margin-top:30px;min-height:0;display:flex;align-items:flex-end;justify-content:center}
  .pic::before{content:'';position:absolute;width:560px;height:560px;border-radius:50%;left:50%;bottom:-40px;transform:translateX(-50%);background:radial-gradient(circle at 50% 45%, ${t.accent}55, ${t.accent}10 62%, transparent 72%)}
  .pic img{position:relative;max-width:100%;max-height:100%;object-fit:contain;filter:drop-shadow(0 24px 30px rgba(0,0,0,.35))}
  .has-img .bottom{margin-top:30px;padding-top:30px}
  /* фото: один тон на всю карусель */
  .bg,.ph img{filter:saturate(.88) contrast(1.06) brightness(.97)}
  .bg{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;z-index:0}
  .shade{position:absolute;inset:0;z-index:1;background:linear-gradient(180deg, ${t.bg}B0 0%, ${t.bg}00 16%, ${t.bg}00 38%, ${t.bg}D9 66%, ${t.bg}FA 100%)}
  .marks{position:absolute;inset:0;z-index:2}
  .marks svg{position:absolute;inset:0;width:100%;height:100%;overflow:visible}
  .marks .mk{stroke-width:10px;vector-effect:non-scaling-stroke;stroke-linecap:round;stroke-linejoin:round;filter:drop-shadow(0 2px 6px rgba(0,0,0,.45))}
  .mlabel{position:absolute;font:800 34px/1.2 '${t.head}',sans-serif;color:${t.onAccent};background:${t.accent};padding:8px 18px;border-radius:12px;white-space:nowrap;box-shadow:0 4px 14px rgba(0,0,0,.35)}
  .txt{position:relative;z-index:3;margin-top:auto;display:flex;flex-direction:column}
  .txt .bar{margin:0 0 34px}
  .cover-photo .top span,.photo-full-card .top span,.cta-photo .top span,.big-number .top span{color:#fff;text-shadow:0 2px 10px rgba(0,0,0,.6)}
  .cover-photo h1{font-size:${h(104)};text-shadow:0 4px 24px rgba(0,0,0,.45)}
  .cover-photo p{margin-top:30px;font-size:46px;color:${t.accent};font-weight:700;text-shadow:0 2px 14px rgba(0,0,0,.5)}
  .cover-photo .bottom,.photo-full-card .bottom,.cta-photo .bottom,.big-number .bottom{margin-top:56px;padding-top:0}
  .photo-full-card h1,.cta-photo h1,.big-number h1{font-size:${h(70)}}
  .photo-full-card p,.cta-photo p,.big-number p{margin-top:26px;font-size:${n < 90 ? 46 : 41}px;color:#EEF1F4}
  .cta-photo h1{font-size:${h(84)}}
  .ph{position:absolute;left:0;top:0;width:100%;height:${s.photoHeight || 58}%;z-index:0}
  .ph img{width:100%;height:100%;object-fit:cover;display:block}
  .ph.duo{display:flex;gap:8px}
  .ph.duo img{width:50%}
  .ph::after{content:'';position:absolute;inset:0;background:linear-gradient(180deg, ${t.bg}D0 0%, ${t.bg}00 20%, ${t.bg}00 70%, ${t.bg} 100%)}
  .photo-top h1,.exercise-annotated h1{font-size:${h(s.big ? 88 : 64)}}
  .photo-top p,.exercise-annotated p{margin-top:24px;font-size:${n < 90 ? 44 : n < 150 ? 40 : 37}px}
  .photo-top .bottom,.exercise-annotated .bottom{margin-top:48px;padding-top:0}
  .photo-top .top span,.exercise-annotated .top span{color:#fff;text-shadow:0 2px 10px rgba(0,0,0,.6)}
  .num{font-family:'${t.head}',sans-serif;font-weight:800;font-size:${s.number && s.number.length > 5 ? 170 : 240}px;line-height:.95;color:${t.accent};letter-spacing:-4px;margin-bottom:18px;text-shadow:0 6px 30px rgba(0,0,0,.35)}
  .cover-photo .shade{background:linear-gradient(180deg, ${t.bg}B0 0%, ${t.bg}00 15%, ${t.bg}00 28%, ${t.bg}CC 52%, ${t.bg}FA 78%)}
  .big-number .shade{background:linear-gradient(180deg, ${t.bg}C0 0%, ${t.bg}66 30%, ${t.bg}E6 62%, ${t.bg}FA 100%)}
  </style></head><body><div class="wrap ${cls}${img && layout === 'plain' ? ' has-img' : ''}">
  ${inner}
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
      const out = path.join(OUT, c.id);
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
