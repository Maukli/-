'use strict';
// Библиотека рисования упражнений кодом. drawExercise(spec) -> строка SVG 900 на 650.
// Фигура строится прямой кинематикой от таза, сегменты рисуются плавными контурами,
// мышцы привязаны к сегментам. Описание spec: API.md.

const COL = {
  line: '#37474F', body: '#ECEFF1', farBody: '#F7F9FA', farLine: '#90A4AE', ghostLine: '#64B5F6', ghostBody: '#F3F9FE',
  equip: '#B0BEC5', equipLine: '#37474F', cable: '#546E7A',
  work: '#E53935', stretch: '#FB8C00', workText: '#C62828', stretchText: '#E65100',
  arrow: '#1E88E5', title: '#263238', hint: '#455A64', note: '#607D8B', floor: '#CFD8DC',
};
const FONT = "'DejaVu Sans', Arial, sans-serif";
const CW = 900, CH = 650;
const SW = 2.75; // толщина контура тела
const HIDDEN_AREA = 90; // px2: меньше этого мышца считается закрытой и рисуется пунктиром поверх

// ---------- геометрия ----------
const rad = a => a * Math.PI / 180;
const deg = r => r * 180 / Math.PI;
const dirv = a => [Math.cos(rad(a)), Math.sin(rad(a))];
const add = (a, b) => [a[0] + b[0], a[1] + b[1]];
const sub = (a, b) => [a[0] - b[0], a[1] - b[1]];
const mul = (a, k) => [a[0] * k, a[1] * k];
const len2 = a => Math.hypot(a[0], a[1]);
const lerp = (a, b, t) => a + (b - a) * t;
const normA = a => { a = ((a + 180) % 360 + 360) % 360 - 180; return a === -180 ? 180 : a; };
const fx = v => String(Math.round(v * 10) / 10);
const fp = p => fx(p[0]) + ',' + fx(p[1]);
const esc = s => String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
const clamp = (v, a, b) => Math.max(a, Math.min(b, v));

function dedupe(pts, eps = 0.4) {
  const out = [];
  for (const p of pts) if (!out.length || len2(sub(p, out[out.length - 1])) > eps) out.push(p);
  if (out.length > 2 && len2(sub(out[0], out[out.length - 1])) <= eps) out.pop();
  return out;
}
// замкнутый сплайн Катмулла-Рома через точки
function smoothClosed(pts, k = 1) {
  pts = dedupe(pts);
  const n = pts.length;
  if (n < 3) return '';
  let d = 'M' + fp(pts[0]);
  for (let i = 0; i < n; i++) {
    const p0 = pts[(i - 1 + n) % n], p1 = pts[i], p2 = pts[(i + 1) % n], p3 = pts[(i + 2) % n];
    const c1 = [p1[0] + (p2[0] - p0[0]) / 6 * k, p1[1] + (p2[1] - p0[1]) / 6 * k];
    const c2 = [p2[0] - (p3[0] - p1[0]) / 6 * k, p2[1] - (p3[1] - p1[1]) / 6 * k];
    d += 'C' + fp(c1) + ' ' + fp(c2) + ' ' + fp(p2);
  }
  return d + 'Z';
}
// точки плотной выборки по пути из smoothClosed/smoothOpen (M и C), для проверок по настоящему контуру
function pathPts(d, per = 5) {
  const nums = d.match(/-?[\d.]+/g).map(Number), out = [];
  let p = [nums[0], nums[1]];
  out.push(p);
  for (let i = 2; i + 5 < nums.length; i += 6) {
    const c1 = [nums[i], nums[i + 1]], c2 = [nums[i + 2], nums[i + 3]], q = [nums[i + 4], nums[i + 5]];
    for (let j = 1; j <= per; j++) {
      const t = j / per, u = 1 - t;
      out.push([0, 1].map(k => u * u * u * p[k] + 3 * u * u * t * c1[k] + 3 * u * t * t * c2[k] + t * t * t * q[k]));
    }
    p = q;
  }
  return out;
}
function smoothOpen(pts, k = 1) {
  pts = dedupe(pts);
  const n = pts.length;
  if (n < 2) return '';
  let d = 'M' + fp(pts[0]);
  for (let i = 0; i < n - 1; i++) {
    const p0 = pts[Math.max(0, i - 1)], p1 = pts[i], p2 = pts[i + 1], p3 = pts[Math.min(n - 1, i + 2)];
    const c1 = [p1[0] + (p2[0] - p0[0]) / 6 * k, p1[1] + (p2[1] - p0[1]) / 6 * k];
    const c2 = [p2[0] - (p3[0] - p1[0]) / 6 * k, p2[1] - (p3[1] - p1[1]) / 6 * k];
    d += 'C' + fp(c1) + ' ' + fp(c2) + ' ' + fp(p2);
  }
  return d;
}
// ширины профиля: кубическая эрмитова интерполяция (плавно, без "полочек" на ключах)
function profAt(prof, t) {
  if (t <= prof[0][0]) return [prof[0][1], prof[0][2]];
  const n = prof.length;
  for (let i = 1; i < n; i++) {
    if (t <= prof[i][0]) {
      const a = prof[i - 1], b = prof[i];
      const h = b[0] - a[0], u = (t - a[0]) / h;
      const out = [];
      for (const k of [1, 2]) {
        const slope = j => {
          const lo = prof[Math.max(0, j - 1)], hi = prof[Math.min(n - 1, j + 1)];
          return (hi[k] - lo[k]) / (hi[0] - lo[0]);
        };
        let m0 = slope(i - 1) * h, m1 = slope(i) * h;
        const d = b[k] - a[k];
        // ограничение наклонов, чтобы не было выбросов
        if (d === 0) { m0 = 0; m1 = 0; } else { m0 = clamp(m0, -3 * Math.abs(d) - 0.5, 3 * Math.abs(d) + 0.5); m1 = clamp(m1, -3 * Math.abs(d) - 0.5, 3 * Math.abs(d) + 0.5); }
        const u2 = u * u, u3 = u2 * u;
        out.push((2 * u3 - 3 * u2 + 1) * a[k] + (u3 - 2 * u2 + u) * m0 + (-2 * u3 + 3 * u2) * b[k] + (u3 - u2) * m1);
      }
      return out;
    }
  }
  const l = prof[n - 1];
  return [l[1], l[2]];
}

// ---------- сегменты ----------
// prof-сегмент: ось A->B, ширины [t, передняя(или латеральная), задняя(или медиальная)].
// frame-сегмент: собственная система координат (u вдоль оси, v в "переднюю" сторону) и контур pts.
function mkSeg(o) {
  const d = dirv(o.ang), n = [-d[1], d[0]];
  o.d = d; o.n = n;
  if (o.kind !== 'frame') o.B = add(o.A, mul(d, o.len));
  o.antSign = o.antSign || 1;
  o.sym = o.sym || 1; // зеркалирование v для frame (фас: правая/левая сторона)
  return o;
}
function segPt(s, t, f) {
  const [ant, post] = profAt(s.prof, t);
  const wPos = (s.antSign > 0 ? ant : post) * s.S, wNeg = (s.antSign > 0 ? post : ant) * s.S;
  const sp = f * s.antSign;
  const off = sp >= 0 ? sp * wPos : sp * wNeg;
  return add(add(s.A, mul(s.d, t * s.len)), mul(s.n, off));
}
function framePt(s, u, v) {
  return add(add(s.A, mul(s.d, u * s.S)), mul(s.n, v * s.S * s.antSign));
}
function segAt(s, a, b) { return s.kind === 'frame' ? framePt(s, a, b) : segPt(s, a, b); }

function segOutline(s) {
  if (s.kind === 'frame') return smoothClosed(s.pts.map(p => framePt(s, p[0], p[1])), s.k || 1);
  const N = s.samples || 10, pos = [], neg = [];
  for (let i = 0; i <= N; i++) { const t = i / N; pos.push(segPt(s, t, s.antSign)); neg.push(segPt(s, t, -s.antSign)); }
  const cap = (t, dirSign, k, from, to) => {
    const [a, b] = profAt(s.prof, t);
    const wP = (s.antSign > 0 ? a : b) * s.S, wN = (s.antSign > 0 ? b : a) * s.S;
    const r = (wP + wN) / 2;
    const c = add(add(s.A, mul(s.d, t * s.len)), mul(s.n, (wP - wN) / 2));
    const out = [];
    for (const ph of from) out.push(add(add(c, mul(s.n, r * Math.cos(ph))), mul(s.d, dirSign * r * k * Math.sin(ph))));
    return out;
  };
  const P4 = Math.PI / 4;
  const capB = cap(1, 1, s.capB ?? 0.9, [P4, 2 * P4, 3 * P4]);
  const capA = cap(0, -1, s.capA ?? 0.9, [3 * P4, 2 * P4, P4]);
  return smoothClosed([...pos, ...capB, ...neg.reverse(), ...capA]);
}
// единый контур цепочки prof-сегментов (живот + грудная клетка) без ступенек на стыке
function chainOutline(parts) {
  const pos = [], neg = [];
  parts.forEach((s, i) => {
    const N = 8;
    for (let k = (i ? 1 : 0); k <= N; k++) { const t = k / N; pos.push(segPt(s, t, s.antSign)); neg.push(segPt(s, t, -s.antSign)); }
  });
  const a = parts[0], b = parts[parts.length - 1];
  const P4 = Math.PI / 4;
  const cap = (s, t, dirSign, k, phs) => {
    const [x, y] = profAt(s.prof, t);
    const wP = (s.antSign > 0 ? x : y) * s.S, wN = (s.antSign > 0 ? y : x) * s.S, r = (wP + wN) / 2;
    const c = add(add(s.A, mul(s.d, t * s.len)), mul(s.n, (wP - wN) / 2));
    return phs.map(ph => add(add(c, mul(s.n, r * Math.cos(ph))), mul(s.d, dirSign * r * k * Math.sin(ph))));
  };
  return smoothClosed([...pos, ...cap(b, 1, 1, b.capB ?? 0.6, [P4, 2 * P4, 3 * P4]), ...neg.reverse(), ...cap(a, 0, -1, a.capA ?? 0.6, [3 * P4, 2 * P4, P4])]);
}
function outlineOf(F, n) {
  const s = F.segs[n];
  if (s.kind === 'custom') return smoothClosed(s.pts, s.k || 1);
  return s.kind === 'chain' ? chainOutline(s.parts.map(p => F.segs[p])) : segOutline(s);
}
// единый контур туловища в профиль: таз + живот + грудная клетка одной линией,
// без горбов на стыках (поясничный прогиб плавно переходит в ягодицу)
function torsoSidePts(segs) {
  const pel = segs.pelvis, abd = segs.abd, ch = segs.chest;
  const out = [];
  // таз: от ягодицы вниз, под тазом и вверх по передней стороне до низа живота
  for (const [u, v] of [[10, -37.5], [-4, -39], [-16, -34.5], [-24, -21], [-26, 0], [-18, 13], [-4, 21], [12, 23.5]]) out.push(framePt(pel, u, v));
  for (let i = 0; i <= 6; i++) out.push(segPt(abd, i / 6, 1));
  for (let i = 1; i <= 8; i++) out.push(segPt(ch, i / 8, 1));
  // верх грудной клетки (линия плеч)
  const P4 = Math.PI / 4;
  const [x, y] = profAt(ch.prof, 1);
  const wP = x * ch.S, wN = y * ch.S, r = (wP + wN) / 2;
  const c = add(add(ch.A, mul(ch.d, ch.len)), mul(ch.n, (wP - wN) / 2));
  for (const ph of [P4, 2 * P4, 3 * P4]) out.push(add(add(c, mul(ch.n, r * Math.cos(ph))), mul(ch.d, r * (ch.capB ?? 0.55) * Math.sin(ph))));
  for (let i = 8; i >= 0; i--) out.push(segPt(ch, i / 8, -1));
  // поясница: прогиб, затем плавный выход в ягодицу
  for (const t of [0.8, 0.6, 0.4, 0.2]) out.push(segPt(abd, t, -1));
  out.push(framePt(pel, 24, -33));
  return out;
}
function segEdge(s, side, t0, t1) {
  const f = side === 'ant' ? 1 : -1, pts = [];
  for (let i = 0; i <= 8; i++) pts.push(segPt(s, lerp(t0, t1, i / 8), f));
  return smoothOpen(pts);
}

// ---------- пропорции (рост 440 px при scale 1) ----------
const L = { thigh: 104, shin: 102, upper: 82, fore: 66, hand: 46, abd: 46, chest: 70, neck: 22 };
const PROF = {
  // профиль: [t, передняя, задняя]
  abd: [[0, 25.5, 27], [0.45, 23, 23], [1, 26, 25]],
  chest: [[0, 26, 25], [0.3, 30.5, 28], [0.55, 32.5, 29], [0.78, 29, 28.5], [0.92, 23, 24.5], [1, 15, 18]],
  neck: [[0, 15, 14], [0.5, 13.5, 13], [1, 13, 14]],
  upper: [[0, 15, 15], [0.15, 15.5, 15.5], [0.38, 12.5, 13.5], [0.62, 12, 13], [0.86, 9.5, 10], [1, 9, 9]],
  fore: [[0, 10, 9.5], [0.18, 11.5, 10.5], [0.5, 9, 8.5], [0.85, 6.5, 6], [1, 6, 5.5]],
  hand: [[0, 6.5, 6], [0.3, 8.5, 6], [0.62, 8.5, 5.5], [0.86, 6.5, 4], [1, 3.5, 3]],
  thigh: [[0, 22, 24], [0.15, 24, 25], [0.4, 23, 21], [0.7, 19.5, 17], [0.9, 15.5, 14], [1, 14.5, 13.5]],
  shin: [[0, 14, 13.5], [0.12, 11.5, 17], [0.3, 9.5, 19], [0.6, 8, 14], [0.85, 6.5, 8], [1, 7, 8]],
  fist: [[0, 6.5, 6], [0.22, 9, 7.5], [0.55, 10.5, 8.5], [0.85, 10, 8], [1, 8.5, 7]],
};
const PROF_FRONT = {
  // фас: [t, латеральная, медиальная]
  neck: [[0, 17, 17], [0.5, 15, 15], [1, 15, 15]],
  upper: [[0, 16, 11], [0.18, 17, 11.5], [0.5, 13, 11], [0.8, 10, 9], [1, 9.5, 9]],
  fore: [[0, 11, 11], [0.25, 13, 11], [0.6, 10, 8.5], [1, 7, 6]],
  hand: [[0, 7, 7], [0.4, 9, 8], [0.75, 8, 7], [1, 5, 4]],
  fist: [[0, 7, 7], [0.35, 10, 8.5], [0.75, 10, 8.5], [1, 8, 7]],
  thigh: [[0, 22, 20], [0.12, 24, 20], [0.4, 21.5, 17], [0.75, 16, 13], [1, 13.5, 12.5]],
  shin: [[0, 13.5, 13], [0.25, 14, 15.5], [0.55, 11, 11.5], [0.9, 7.5, 7.5], [1, 8, 7.5]],
};
// контуры frame-сегментов (u вверх/вдоль, v вперёд/вправо)
const PELVIS_SIDE = [[38, -24], [26, -30.5], [10, -37], [-6, -38.5], [-18, -33], [-25, -19], [-26, 0], [-18, 13], [-4, 21], [12, 23.5], [27, 23.5], [38, 21]];
// голова в профиль: затылок, темя, лоб, надбровье, нос, губы, подбородок (масштаб 1.07 к росту 440)
const HEAD_SIDE = [[-3, -13], [6, -20], [17, -23.5], [29, -22.2], [38.5, -16.5], [44.6, -7], [46.4, 3], [44.2, 12.5], [38.8, 19.2], [32, 22.6], [27, 23.4], [25, 23], [21.6, 26.2], [18.6, 29.4], [16.6, 29.1], [15, 26.9], [13.6, 25.4], [11.6, 25.6], [9.6, 24.9], [7.8, 25.1], [5.8, 24], [3, 24.8], [-0.2, 23.6], [-3.2, 21], [-6.6, 16], [-8.2, 9.5], [-4, 3]].map(([u, v]) => [u * 1.07, v * 1.07]);
const FOOT_SIDE = [[-9, 7], [-15, -5], [-15.5, -15], [-10, -23], [8, -21.5], [24, -20.5], [40, -23], [49, -22.5], [54, -18], [50, -13], [40, -10.5], [24, -3], [12, 4], [6, 9]];
const ANKLE_H = 23; // высота голеностопа над полом
const mirrorPts = half => [...half, ...half.slice().reverse().map(([u, v]) => [u, -v])];
const PELVIS_FRONT = mirrorPts([[60, 38], [42, 43], [22, 46], [2, 47], [-14, 40], [-24, 23], [-27, 4]]);
// верх грудной клетки: скат трапеции от шеи к акромиону, плечевой сустав ниже линии трапеции
const CHEST_FRONT = mirrorPts([[0, 38], [28, 44], [50, 50], [62, 51.5], [70, 50], [76, 44.5], [81, 33], [85, 22], [88, 13], [89, 5]]).reverse();
const SHOULDER_FRONT = [66, 45];
const HEAD_FRONT = mirrorPts([[-12, 2], [-9, 11], [0, 18.5], [16, 22.5], [32, 22], [44, 13], [48, 3]]).map(([u, v]) => [u * 1.06, v * 1.04]);
// кисть в фас/со спины (ладонь к бедру, видна с ребра): u от запястья, v>0 тыльная (латеральная) сторона
const HAND_FRONT = [[0, 6], [9, 7], [20, 7.5], [30, 6.8], [38, 5], [43.5, 2], [44.5, -1.5], [41, -4.5], [34, -6.5], [27, -7.8], [19, -8.6], [11, -8], [4, -7], [0, -6]];
const FOOT_FRONT = [[-6, -10], [4, -13], [14, -14.5], [22, -13], [26, -6], [27, 4], [25, 13], [14, 15], [2, 12], [-6, 9]];
const FOOT_BACK = [[-6, -9], [6, -11.5], [16, -11], [22, -7], [23.5, 0], [22, 7], [16, 11], [6, 11.5], [-6, 9]];

// ---------- сборка фигуры ----------
const OTHER = { l: 'r', r: 'l' };
function sideParams(pose, s) {
  return Object.assign({}, pose.both || {}, pose[s] || {});
}
function makeXf(px, py, rot, mirror) {
  const c = Math.cos(rad(rot)), s = Math.sin(rad(rot));
  const f = p => { const x = mirror ? -p[0] : p[0], y = p[1]; return [px + x * c - y * s, py + x * s + y * c]; };
  f.inv = p => { const dx = p[0] - px, dy = p[1] - py; let x = dx * c + dy * s; const y = -dx * s + dy * c; if (mirror) x = -x; return [x, y]; };
  f.transform = `translate(${fx(px)},${fx(py)}) rotate(${fx(rot)})${mirror ? ' scale(-1,1)' : ''}`;
  return f;
}
// двухзвенная обратная кинематика: flexSign +1: a2 = a1 - сгиб, -1: a2 = a1 + сгиб
function ik2(R, l1, l2, T, flexSign, flip) {
  const dx = T[0] - R[0], dy = T[1] - R[1];
  let d = Math.hypot(dx, dy);
  d = clamp(d, Math.abs(l1 - l2) + 1e-3, l1 + l2 - 1e-3);
  const phi = deg(Math.atan2(dy, dx));
  const al = deg(Math.acos(clamp((l1 * l1 + d * d - l2 * l2) / (2 * l1 * d), -1, 1)));
  const sols = [phi + al, phi - al].map(a1 => {
    const J = add(R, mul(dirv(a1), l1));
    const a2 = deg(Math.atan2(T[1] - J[1], T[0] - J[0]));
    const fl = flexSign > 0 ? normA(a1 - a2) : normA(a2 - a1);
    return { a1, a2, fl };
  });
  sols.sort((a, b) => (flip ? a.fl - b.fl : b.fl - a.fl));
  return [sols[0].a1, sols[0].a2];
}

// точки для handAt/gripAt/footAt: координаты холста, имя точки торса/плеча или {at, dx, dy}
function mkLoc(early, xf) {
  const loc = p => {
    if (Array.isArray(p)) return xf.inv(p);
    if (typeof p === 'string') {
      if (early[p]) return early[p];
      throw new Error('Точка ' + p + ' недоступна для handAt/gripAt/footAt. Можно: ' + Object.keys(early).join(', '));
    }
    const w = add(p.at ? xf(loc(p.at)) : [p.x || 0, p.y || 0], [p.dx || 0, p.dy || 0]);
    return xf.inv(w);
  };
  return loc;
}

function buildSide(spec, xf) {
  const P = spec.pose || {};
  const S = spec.scale || P.scale || 1;
  const near = P.near || 'l', far = OTHER[near];
  const T = P.trunk || 0;
  const segs = {};
  const add_ = o => { o.S = o.S || S; segs[o.name] = mkSeg(o); return segs[o.name]; };
  const pel = add_({ name: 'pelvis', kind: 'frame', A: [0, 0], ang: -90 + T + (P.pelvisTilt || 0), pts: PELVIS_SIDE });
  const abdAng = -90 + T + (P.lumbar || 0);
  const abd = add_({ name: 'abd', A: framePt(pel, 28, -3), ang: abdAng, len: L.abd * S, prof: PROF.abd, capA: 0.9, capB: 0.5 });
  const chestAng = abdAng + (P.thoracic || 0);
  const chest = add_({ name: 'chest', A: abd.B, ang: chestAng, len: L.chest * S, prof: PROF.chest, capA: 0.5, capB: 0.55 });
  const neckAng = chestAng + (P.neck || 0);
  const neck = add_({ name: 'neck', A: segPt(chest, 1, -0.2), ang: neckAng, len: L.neck * S, prof: PROF.neck, capA: 0.3, capB: 0.5 });
  add_({ name: 'head', kind: 'frame', A: neck.B, ang: neckAng + (P.head || 0), pts: HEAD_SIDE });
  segs.trunk = { name: 'trunk', kind: 'custom', parts: ['pelvis', 'abd', 'chest'], pts: torsoSidePts(segs) };
  const chestLean = chestAng + 90;
  const sh = segPt(chest, 0.78, 0.1);
  const farShift = P.farShift || [0, 0];
  const early = {
    pelvis: [0, 0], hip: [0, 0], head: framePt(segs.head, 18, 4), neck: segPt(neck, 0.5, 0),
    chest: segPt(chest, 0.6, 1), sternum: segPt(chest, 0.6, 1), back: segPt(chest, 0.6, -1), upperback: segPt(chest, 0.85, -1),
    lowback: segPt(abd, 0.5, -1), belly: segPt(abd, 0.5, 1), butt: framePt(pel, -6, -38), sacrum: framePt(pel, 26, -31),
    shoulder: sh, ['shoulder_' + near]: sh, shoulder_near: sh, ['shoulder_' + far]: add(sh, farShift), shoulder_far: add(sh, farShift),
  };
  const loc = mkLoc(early, xf);
  for (const s of ['l', 'r']) {
    const J = sideParams(P, s);
    const shift = s === far ? farShift : [0, 0];
    const shoulder = add(sh, shift), hip = add([0, 0], shift);
    let armA = 90 + chestLean - (J.shoulder || 0);
    let foreA = armA - (J.elbow || 0);
    const k = J.lengths || {};
    const lu = L.upper * S * (k.upper || 1), lf = L.fore * S * (k.fore || 1), lh = L.hand * S * (k.hand || 1);
    const lt = L.thigh * S * (k.thigh || 1), ls = L.shin * S * (k.shin || 1);
    if (J.handAt || J.gripAt) {
      const tgt = loc(J.handAt || J.gripAt);
      let wristT = tgt;
      for (let it = 0; it < (J.gripAt ? 4 : 1); it++) {
        if (J.gripAt) { const hA = foreA - (J.wrist || 0); wristT = sub(tgt, mul(dirv(hA), (J.hand === 'open' ? 0.45 : 0.3) * lh)); }
        [armA, foreA] = ik2(shoulder, lu, lf, wristT, 1, J.bend === -1);
      }
    }
    const handA = foreA - (J.wrist || 0);
    let thighA = 90 + T - (J.hip || 0);
    let shinA = thighA + (J.knee || 0);
    if (J.footAt) [thighA, shinA] = ik2(hip, lt, ls, loc(J.footAt), -1, J.bend === -1);
    // стопа по footAt без явного ankle ставится ровно на пол (подошва горизонтальна на холсте)
    const footA = J.footAt && J.ankle == null ? ((P.facing || 'right') === 'left' ? (P.rotate || 0) : -(P.rotate || 0)) : shinA - 90 - (J.ankle || 0);
    const up = add_({ name: 'upper_' + s, side: s, A: shoulder, ang: armA, len: lu, prof: PROF.upper, antSign: -1, capA: 0.85, capB: 0.8 });
    const fo = add_({ name: 'fore_' + s, side: s, A: up.B, ang: foreA, len: lf, prof: PROF.fore, antSign: -1, capA: 0.8, capB: 0.7 });
    const fist = J.hand ? J.hand === 'fist' : !!J.gripAt;
    add_({ name: 'hand_' + s, side: s, A: fo.B, ang: handA, len: fist ? lh * 0.6 : lh, prof: fist ? PROF.fist : PROF.hand, antSign: -1, capA: 0.6, capB: fist ? 0.9 : 1, fist });
    const th = add_({ name: 'thigh_' + s, side: s, A: hip, ang: thighA, len: lt, prof: PROF.thigh, antSign: -1, capA: 0.9, capB: 0.6 });
    const sn = add_({ name: 'shin_' + s, side: s, A: th.B, ang: shinA, len: ls, prof: PROF.shin, antSign: -1, capA: 0.8, capB: 0.6 });
    add_({ name: 'foot_' + s, side: s, kind: 'frame', A: sn.B, ang: footA, antSign: -1, pts: FOOT_SIDE });
    segs['_j_' + s] = { elbow: normA(armA - foreA), knee: normA(shinA - thighA), hip: normA((90 + T) - thighA), shoulder: normA(90 + chestLean - armA) };
  }
  const n = near, f = far;
  const clusters = [
    { name: 'farLeg', far: true, segs: ['thigh_' + f, 'shin_' + f, 'foot_' + f] },
    { name: 'farArm', far: true, segs: ['upper_' + f, 'fore_' + f, 'hand_' + f] },
    { name: 'torso', segs: ['thigh_' + n, 'shin_' + n, 'foot_' + n, 'trunk', 'neck', 'head'] },
    { name: 'nearArm', segs: ['upper_' + n, 'fore_' + n, 'hand_' + n] },
  ];
  if (P.order) clusters.sort((a, b) => P.order.indexOf(a.name) - P.order.indexOf(b.name));
  // складки: внутренние линии там, где сегменты одного силуэта сложились
  const creases = [];
  for (const s of ['l', 'r']) {
    const j = segs['_j_' + s];
    if (j.knee > 55) creases.push({ seg: 'shin_' + s, side: 'post', t0: 0.06, t1: clamp(0.25 + j.knee / 200, 0.4, 0.75) });
    if (j.elbow > 70) creases.push({ seg: 'fore_' + s, side: 'ant', t0: 0.1, t1: 0.6 });
    if (s === near && j.hip > 95) creases.push({ seg: 'thigh_' + s, side: 'ant', t0: 0.12, t1: 0.75 });
  }
  const details = [
    { kind: 'ear', seg: 'head', u: 18.5, v: -5 },
  ];
  // именованные точки
  const pts = Object.assign({}, early, { nose: framePt(segs.head, 20.5, 29.5), chin: framePt(segs.head, -4.5, 22.5) });
  for (const s of ['l', 'r']) {
    const tag = s === near ? 'near' : 'far';
    const sp = {
      shoulder: segs['upper_' + s].A, elbow: segs['upper_' + s].B, wrist: segs['fore_' + s].B,
      hand: segPt(segs['hand_' + s], segs['hand_' + s].fist ? 0.5 : 0.45, 0), fingers: segs['hand_' + s].B,
      knee: segs['thigh_' + s].B, ankle: segs['shin_' + s].B,
      heel: framePt(segs['foot_' + s], -10, -23), toe: framePt(segs['foot_' + s], 53, -18), ball: framePt(segs['foot_' + s], 40, -23),
      kneefront: segPt(segs['shin_' + s], 0.02, 1.2), shin: segPt(segs['shin_' + s], 0.5, 1), thigh: segPt(segs['thigh_' + s], 0.5, 0),
    };
    for (const k in sp) { pts[k + '_' + s] = sp[k]; pts[k + '_' + tag] = sp[k]; }
  }
  return { view: 'side', segs, clusters, creases, details, pts, near, far, S };
}

function buildFront(spec, xf, back) {
  const P = spec.pose || {};
  const S = spec.scale || P.scale || 1;
  const segs = {};
  const add_ = o => { o.S = o.S || S; segs[o.name] = mkSeg(o); return segs[o.name]; };
  const T = P.trunk || 0;
  const pel = add_({ name: 'pelvis', kind: 'frame', A: [0, 0], ang: -90 + (P.pelvisTilt || 0), pts: PELVIS_FRONT });
  const chest = add_({ name: 'chest', kind: 'frame', A: framePt(pel, 58, 0), ang: -90 + T, pts: CHEST_FRONT });
  const neckAng = -90 + T + (P.neck || 0);
  const neck = add_({ name: 'neck', A: framePt(chest, 84, 0), ang: neckAng, len: 24 * S, prof: PROF_FRONT.neck, capA: 0.3, capB: 0.4 });
  add_({ name: 'head', kind: 'frame', A: neck.B, ang: neckAng + (P.head || 0), pts: HEAD_FRONT });
  const sgOf = s => (back ? (s === 'l' ? -1 : 1) : (s === 'l' ? 1 : -1));
  const early = {
    pelvis: [0, 0], hip: [0, 0], head: framePt(segs.head, 18, 0), neck: segPt(neck, 0.5, 0), chest: framePt(chest, 58, 0),
    belly: framePt(chest, 2, 0), navel: framePt(chest, 2, 0), back: framePt(chest, 50, 0), lowback: framePt(chest, 8, 0), butt: framePt(pel, -4, 0),
  };
  for (const s of ['l', 'r']) { early['shoulder_' + s] = framePt(chest, SHOULDER_FRONT[0], SHOULDER_FRONT[1] * sgOf(s)); early['hip_' + s] = framePt(pel, 0, 24 * sgOf(s)); }
  const loc = mkLoc(early, xf);
  for (const s of ['l', 'r']) {
    const J = sideParams(P, s), sg = sgOf(s);
    const k = J.lengths || {};
    const lu = L.upper * S * (k.upper || 1), lf = L.fore * S * (k.fore || 1), lh = L.hand * S * (k.hand || 1);
    const lt = L.thigh * S * (k.thigh || 1), ls = L.shin * S * (k.shin || 1);
    const shoulder = framePt(chest, SHOULDER_FRONT[0], SHOULDER_FRONT[1] * sg), hip = framePt(pel, 0, 24 * sg);
    let armA = 90 + T - sg * (J.shoulder || 0);
    let foreA = armA - sg * (J.elbow || 0);
    if (J.handAt || J.gripAt) {
      const tgt = loc(J.handAt || J.gripAt);
      let wristT = tgt;
      for (let it = 0; it < (J.gripAt ? 4 : 1); it++) {
        if (J.gripAt) { const hA = foreA - sg * (J.wrist || 0); wristT = sub(tgt, mul(dirv(hA), (J.hand === 'open' ? 0.45 : 0.3) * lh)); }
        [armA, foreA] = ik2(shoulder, lu, lf, wristT, sg, J.bend === -1);
      }
    }
    const handA = foreA - sg * (J.wrist || 0);
    let thighA = 90 - sg * (J.hip || 0);
    let shinA = thighA + sg * (J.knee || 0);
    if (J.footAt) [thighA, shinA] = ik2(hip, lt, ls, loc(J.footAt), -sg, J.bend === -1);
    const latSign = -sg;
    const up = add_({ name: 'upper_' + s, side: s, A: shoulder, ang: armA, len: lu, prof: PROF_FRONT.upper, antSign: latSign, capA: 0.65, capB: 0.8 });
    const fo = add_({ name: 'fore_' + s, side: s, A: up.B, ang: foreA, len: lf, prof: PROF_FRONT.fore, antSign: latSign, capA: 0.8, capB: 0.7 });
    const fist = J.hand ? J.hand === 'fist' : !!J.gripAt;
    if (fist) add_({ name: 'hand_' + s, side: s, A: fo.B, ang: handA, len: lh * 0.6, prof: PROF_FRONT.fist, antSign: latSign, capA: 0.6, capB: 0.9, fist });
    else add_({ name: 'hand_' + s, side: s, kind: 'frame', A: fo.B, ang: handA, antSign: latSign, pts: HAND_FRONT.map(([u, v]) => [u * (k.hand || 1), v]), fist: false, handLen: 44 * (k.hand || 1) });
    const th = add_({ name: 'thigh_' + s, side: s, A: hip, ang: thighA, len: lt, prof: PROF_FRONT.thigh, antSign: latSign, capA: 0.9, capB: 0.6 });
    const sn = add_({ name: 'shin_' + s, side: s, A: th.B, ang: shinA, len: ls, prof: PROF_FRONT.shin, antSign: latSign, capA: 0.8, capB: 0.6 });
    add_({ name: 'foot_' + s, side: s, kind: 'frame', A: sn.B, ang: 90 - sg * (J.ankle || 0), antSign: latSign, pts: back ? FOOT_BACK : FOOT_FRONT });
    segs['_j_' + s] = { elbow: Math.abs(normA(armA - foreA)), knee: Math.abs(normA(shinA - thighA)), sg };
  }
  const clusters = [
    { name: 'body', segs: ['thigh_l', 'shin_l', 'foot_l', 'thigh_r', 'shin_r', 'foot_r', 'pelvis', 'chest', 'neck', 'head'] },
    { name: 'armR', segs: ['upper_r', 'fore_r', 'hand_r'] },
    { name: 'armL', segs: ['upper_l', 'fore_l', 'hand_l'] },
  ];
  if (P.order) clusters.sort((a, b) => P.order.indexOf(a.name) - P.order.indexOf(b.name));
  const creases = [];
  for (const s of ['l', 'r']) {
    const j = segs['_j_' + s];
    if (j.elbow > 70) creases.push({ seg: 'fore_' + s, side: 'med', t0: 0.1, t1: 0.6 });
  }
  const details = back ? [] : [{ kind: 'earF', seg: 'head', u: 4, v: 23 }, { kind: 'earF', seg: 'head', u: 4, v: -23 }];
  if (back) details.push({ kind: 'earF', seg: 'head', u: 4, v: 23 }, { kind: 'earF', seg: 'head', u: 4, v: -23 });
  const pts = Object.assign({}, early, { chin: framePt(segs.head, -10, 0) });
  for (const s of ['l', 'r']) {
    const sg = sgOf(s);
    const sp = {
      shoulder: segs['upper_' + s].A, elbow: segs['upper_' + s].B, wrist: segs['fore_' + s].B,
      hand: segs['hand_' + s].kind === 'frame' ? framePt(segs['hand_' + s], 20, 0) : segPt(segs['hand_' + s], 0.5, 0),
      fingers: segs['hand_' + s].kind === 'frame' ? framePt(segs['hand_' + s], 44, 0) : segs['hand_' + s].B, hip: framePt(pel, 0, 24 * sg),
      knee: segs['thigh_' + s].B, ankle: segs['shin_' + s].B, heel: framePt(segs['foot_' + s], 23, 0), toe: framePt(segs['foot_' + s], 23, 0),
      shin: segPt(segs['shin_' + s], 0.5, 0), thigh: segPt(segs['thigh_' + s], 0.5, 0),
    };
    for (const k in sp) { pts[k + '_' + s] = sp[k]; pts[k + '_near'] = pts[k + '_near'] || sp[k]; }
  }
  return { view: back ? 'back' : 'front', segs, clusters, creases, details, pts, sgOf, S };
}

// ---------- мышцы ----------
const NAMES = {
  deltoid: 'Дельты', pecs: 'Грудные', lats: 'Широчайшие',
  trap_upper: 'Верх трапеции', trap_middle: 'Середина трапеции', trap_lower: 'Низ трапеции', traps: 'Трапеция',
  rhomboids: 'Ромбовидные', biceps: 'Бицепс', triceps: 'Трицепс', forearm: 'Предплечье',
  rectus_abdominis: 'Прямая мышца живота', obliques: 'Косые мышцы живота', erectors: 'Разгибатели спины',
  glute_max: 'Большая ягодичная', glute_med: 'Средняя ягодичная', glute_min: 'Малая ягодичная',
  tfl: 'НШФБ', iliopsoas: 'Подвздошно-поясничная', quads: 'Квадрицепс', rectus_femoris: 'Прямая мышца бедра',
  adductors: 'Приводящие', hamstrings: 'Бицепс бедра', gastrocnemius: 'Икроножная', soleus: 'Камбаловидная',
  tibialis_anterior: 'Передняя большеберцовая', neck_flexors: 'Сгибатели шеи', piriformis: 'Грушевидная',
  serratus: 'Передняя зубчатая', foot: 'Мышцы стопы',
};
const ALIASES = {
  delts: 'deltoid', chest: 'pecs', pec: 'pecs', lat: 'lats', abs: 'rectus_abdominis', rectus: 'rectus_abdominis',
  oblique: 'obliques', erector: 'erectors', spinal_erectors: 'erectors', glutes: 'glute_max', gluteus_maximus: 'glute_max',
  gluteus_medius: 'glute_med', gluteus_minimus: 'glute_min', psoas: 'iliopsoas', hip_flexors: 'iliopsoas', quadriceps: 'quads',
  adductor: 'adductors', hams: 'hamstrings', calf: 'gastrocnemius', calves: 'gastrocnemius', gastroc: 'gastrocnemius',
  tibialis: 'tibialis_anterior', neck: 'neck_flexors', serratus_anterior: 'serratus', feet: 'foot', foot_muscles: 'foot',
  rhomboid: 'rhomboids', trapezius: 'traps',
};
const TORSO_MUSCLES = new Set(['pecs', 'lats', 'trap_upper', 'trap_middle', 'trap_lower', 'rhomboids', 'rectus_abdominis', 'obliques', 'erectors', 'neck_flexors', 'serratus', 'glute_max', 'glute_med', 'glute_min', 'tfl', 'iliopsoas', 'piriformis']);

// фабрика форм: band вдоль сегмента или цепочки сегментов, free по опорным точкам
function shapeKit(F, sideKey, sym) {
  const segName = n => (F.segs[n] ? n : n + '_' + sideKey);
  const S = n => F.segs[segName(n)];
  const at = (n, a, b) => { const s = S(n); return s.kind === 'frame' ? framePt(s, a, b * (s.sym === 'side' ? sym : 1)) : segPt(s, a, b); };
  function gband(atU, fA, fB, o = {}) {
    const ta = o.ta ?? 0.5, tb = o.tb ?? 0.5, p = o.p ?? 0.8, n = o.n ?? 12, edge = o.edge;
    const r = x => Math.pow(Math.sin(clamp(x, 0, 1) * Math.PI / 2), p);
    const sF = u => Math.min(ta <= 0 ? 1 : r(u / ta), tb <= 0 ? 1 : r((1 - u) / tb));
    const A = [], B = [];
    for (let i = 0; i <= n; i++) {
      const u = i / n, s = sF(u);
      const mid = edge === 'a' ? fA : edge === 'b' ? fB : (fA + fB) / 2;
      A.push(atU(u, mid + (fA - mid) * s)); B.push(atU(u, mid + (fB - mid) * s));
    }
    return A.concat(B.reverse());
  }
  return {
    S, segName, joint: F.segs['_j_' + sideKey] || {},
    band: (n, t0, t1, fA, fB, o) => gband((u, f) => segPt(S(n), lerp(t0, t1, u), f), fA, fB, o),
    chain: (parts, fA, fB, o) => {
      const ws = parts.map(([n, a, b]) => Math.abs(b - a) * S(n).len), tot = ws.reduce((x, y) => x + y, 0);
      return gband((u, f) => {
        let acc = 0;
        for (let i = 0; i < parts.length; i++) {
          const w = ws[i] / tot;
          if (u <= acc + w + 1e-9 || i === parts.length - 1) { const [n, a, b] = parts[i]; return segPt(S(n), lerp(a, b, clamp((u - acc) / w, 0, 1)), f); }
          acc += w;
        }
      }, fA, fB, o);
    },
    free: list => list.map(([n, a, b]) => at(n, a, b)),
    // tube: плавная лента по осевой линии через опорные точки, ширины в px (на рост 440)
    tube: (list, widths) => {
      const c = list.map(([n, a, b]) => at(n, a, b));
      const Sx = F.S || 1;
      const pts = [], ws = [];
      const M = 6;
      for (let i = 0; i < c.length - 1; i++) {
        const p0 = c[Math.max(0, i - 1)], p1 = c[i], p2 = c[i + 1], p3 = c[Math.min(c.length - 1, i + 2)];
        for (let j = 0; j < M; j++) {
          const t = j / M, t2 = t * t, t3 = t2 * t;
          const q = [0, 1].map(k => 0.5 * ((2 * p1[k]) + (-p0[k] + p2[k]) * t + (2 * p0[k] - 5 * p1[k] + 4 * p2[k] - p3[k]) * t2 + (-p0[k] + 3 * p1[k] - 3 * p2[k] + p3[k]) * t3));
          pts.push(q); ws.push(lerp(widths[i], widths[i + 1], t) * Sx);
        }
      }
      pts.push(c[c.length - 1]); ws.push(widths[widths.length - 1] * Sx);
      const A = [], B = [];
      for (let i = 0; i < pts.length; i++) {
        const d = sub(pts[Math.min(pts.length - 1, i + 1)], pts[Math.max(0, i - 1)]);
        const L_ = len2(d) || 1, nn = [-d[1] / L_, d[0] / L_];
        const u = i / (pts.length - 1), taper = Math.pow(Math.sin(Math.PI * clamp(u * 0.92 + 0.04, 0, 1)), 0.35);
        const w = ws[i] / 2 * taper;
        A.push(add(pts[i], mul(nn, w))); B.push(sub(pts[i], mul(nn, w)));
      }
      return A.concat(B.reverse());
    },
  };
}

// дельта шапкой: широкая и круглая над головкой плеча (t от -0.36 до 0.06 на всю ширину руки),
// держит ширину до середины и сужается только у бугристости tEnd, конец тупой (не капля)
function deltCap(k, tEnd) {
  const e = tEnd;
  const half = [['upper', -0.3, 0.9], ['upper', -0.14, 1.25], ['upper', 0.06, 1.25], ['upper', e * 0.5, 1.15], ['upper', e * 0.72, 0.9], ['upper', e * 0.9, 0.48], ['upper', e, 0.16]];
  return k.free([['upper', -0.36, 0], ...half, ...half.slice().reverse().map(([n, t, v]) => [n, t, -v])]);
}
const SIDE_DEFS = {
  // дельта: только головка плеча (верхняя треть), грудная: передний верх грудной клетки перед плечом
  // дельта: шапка над головкой плеча (широкая и круглая сверху), сужается к бугристости на 0.42 длины плеча
  deltoid: k => [{ segs: ['upper'], pts: deltCap(k, 0.42) }],
  // грудная: передний верх грудной клетки и переход на головку плечевой кости. Часть на плече рисуется
  // в слое руки поверх неё (top), поэтому грудная видна в жимах, где рука закрывает грудную клетку
  pecs: k => {
    const out = [{ segs: ['chest'], pts: k.free([['chest', 0.97, 0.3], ['chest', 0.97, 1.2], ['chest', 0.72, 1.25], ['chest', 0.42, 1.22], ['chest', 0.27, 0.95], ['chest', 0.28, 0.45], ['chest', 0.45, 0.08], ['chest', 0.7, 0.02], ['chest', 0.86, 0.1]]) }];
    // жимовые положения (плечо согнуто больше 45): рука закрывает грудную клетку, поэтому грудная заходит
    // на основание плеча со стороны подмышки (передняя подмышечная складка, задняя сторона согнутого плеча)
    // и рисуется поверх дельты (top): грудная остаётся видна и одной массой переходит с груди на плечо
    if ((k.joint.shoulder ?? 0) > 45) out.push({ segs: ['upper'], top: true, pts: k.free([['upper', -0.1, -0.15], ['upper', -0.12, -1.25], ['upper', 0.08, -1.3], ['upper', 0.22, -1.2], ['upper', 0.27, -0.8], ['upper', 0.2, -0.4], ['upper', 0.06, -0.12]]) });
    return out;
  },
  lats: k => [{ segs: ['abd', 'chest'], pts: k.free([['abd', 0.2, -1.1], ['abd', 0.75, -1.1], ['chest', 0.3, -1.1], ['chest', 0.6, -0.95], ['chest', 0.8, -0.3], ['chest', 0.72, 0.15], ['chest', 0.5, 0.1], ['chest', 0.15, -0.35], ['abd', 0.6, -0.65]]) }],
  // верх трапеции: сзади шеи от затылка к надплечью; сгибатели шеи (ГКС): спереди, от уха к грудине
  trap_upper: k => [{ segs: ['neck', 'chest'], pts: k.free([['neck', 0.98, -1.15], ['neck', 0.6, -0.5], ['neck', 0.2, -0.25], ['chest', 0.99, -0.05], ['chest', 0.92, -0.35], ['chest', 0.86, -0.75], ['chest', 0.9, -1.15], ['neck', 0.3, -1.2]]) }],
  trap_middle: k => [{ segs: ['chest'], pts: k.band('chest', 0.6, 0.95, -1.1, -0.5, { edge: 'a', ta: 0.3, tb: 0.3 }) }],
  trap_lower: k => [{ segs: ['chest'], pts: k.band('chest', 0.28, 0.7, -1.1, -0.55, { edge: 'a', ta: 0.75, tb: 0.2 }) }],
  rhomboids: k => [{ deep: true, segs: ['chest'], pts: k.band('chest', 0.56, 0.88, -0.97, -0.6, { ta: 0.3, tb: 0.3 }) }],
  // передняя зубчатая: бок грудной клетки под подмышкой, зубцы спереди (к грудной), сзади уходит под широчайшую
  serratus: k => {
    const pts = [], c = k.S('chest');
    // зубцы спереди (к грудной), задний край под краем широчайшей
    for (let i = 0; i <= 8; i++) pts.push(segPt(c, lerp(0.3, 0.7, i / 8), i % 2 ? 0.58 : 0.85 - 0.12 * i / 8));
    pts.push(segPt(c, 0.75, 0.35));
    for (let i = 8; i >= 0; i--) pts.push(segPt(c, lerp(0.32, 0.74, i / 8), 0.02 + 0.06 * Math.sin(Math.PI * i / 8)));
    return [{ segs: ['chest'], pts }];
  },
  // прямая мышца живота: полоса вдоль передней стенки от лобка до грудины
  // прямая мышца живота: лента ровной ширины вдоль передней стенки от лобка (ось живота продлена вниз) до рёбер
  rectus_abdominis: k => [{ segs: ['pelvis', 'abd', 'chest'], pts: k.chain([['abd', -0.55, 1], ['chest', 0, 0.42]], 1.15, 0.45, { edge: 'a', ta: 0.06, tb: 0.22 }) }],
  // наружная косая: весь бок живота от гребня таза до нижних рёбер, между прямой мышцей и широчайшей
  obliques: k => [{ segs: ['pelvis', 'abd', 'chest'], pts: k.free([['pelvis', 36, -14], ['abd', 0.3, -0.6], ['abd', 0.75, -0.62], ['chest', 0.18, -0.58], ['chest', 0.42, -0.25], ['chest', 0.5, 0.15], ['chest', 0.4, 0.4], ['chest', 0.12, 0.44], ['abd', 0.6, 0.44], ['abd', 0.2, 0.44], ['pelvis', 34, 8], ['pelvis', 38.5, -3]]) }],
  // разгибатели: от крестца (низ доходит до верхнего края большой ягодичной, без разрыва) до грудного отдела
  erectors: k => [{ segs: ['pelvis', 'abd', 'chest'], pts: k.chain([['abd', -0.17, 1], ['chest', 0, 0.78]], -1.1, -0.45, { edge: 'a', ta: 0.14, tb: 0.5 }) }],
  neck_flexors: k => [{ segs: ['neck', 'chest', 'head'], pts: k.tube([['head', 5, -5], ['neck', 0.72, 0.15], ['neck', 0.3, 0.62], ['chest', 0.97, 0.98]], [8, 10, 9, 7]) }],
  biceps: k => [{ segs: ['upper'], pts: k.band('upper', 0.34, 0.92, 1.1, 0.0, { edge: 'a', ta: 0.5, tb: 0.3 }) }],
  triceps: k => [{ segs: ['upper'], pts: k.band('upper', 0.3, 0.94, -1.1, -0.05, { edge: 'a', ta: 0.4, tb: 0.3 }) }],
  forearm: k => [{ segs: ['fore'], pts: k.band('fore', -0.08, 0.8, -1.1, 1.1, { ta: 0.08, tb: 0.75 }) }],
  // большая ягодичная: передний край на бедре не дальше v -0.3 (сбоку остаётся за висящей рукой), низ по ягодичной складке
  glute_max: k => [{ segs: ['pelvis', 'thigh'], pts: k.free([['pelvis', 26, -27], ['pelvis', 10, -34], ['pelvis', -6, -37], ['pelvis', -19, -31], ['thigh', 0.25, -1.05], ['thigh', 0.3, -0.55], ['thigh', 0.2, -0.32], ['pelvis', 4, -14], ['pelvis', 16, -16]]) }],
  // средняя ягодичная: крыло таза под гребнем, веером к большому вертелу; грушевидная ниже, под большой ягодичной
  glute_med: k => [{ segs: ['pelvis'], pts: k.free([['pelvis', 39, -17], ['pelvis', 39.5, -2], ['pelvis', 36, 7], ['pelvis', 26, 9], ['pelvis', 13, 3], ['pelvis', 9, -6], ['pelvis', 17, -15], ['pelvis', 29, -21]]) }],
  glute_min: k => [{ deep: true, segs: ['pelvis'], pts: k.free([['pelvis', 27, -6], ['pelvis', 25, 7], ['pelvis', 14, 8], ['pelvis', 8, -1], ['pelvis', 15, -9]]) }],
  tfl: k => [{ segs: ['pelvis', 'thigh'], pts: k.tube([['pelvis', 28, 17], ['pelvis', 10, 14], ['thigh', 0.22, 0.25], ['thigh', 0.4, 0.1]], [10, 14, 12, 6]) }],
  piriformis: k => [{ deep: true, segs: ['pelvis'], pts: k.tube([['pelvis', 15, -32], ['pelvis', 8, -21], ['pelvis', 2, -9]], [11, 9, 6]) }],
  // подвздошно-поясничная одной лентой: поясничная часть над тазом переходит в подвздошную перед средней ягодичной
  // (ось на v 17-18 у таза, средняя ягодичная кончается на v 9), так верх не выглядит отдельной мышцей
  iliopsoas: k => [{ deep: true, segs: ['pelvis', 'abd', 'thigh'], pts: k.tube([['abd', 0.72, 0.0], ['abd', 0.3, 0.42], ['pelvis', 30, 17.5], ['pelvis', 16, 18], ['pelvis', 3, 16.5], ['thigh', 0.2, 0.25]], [9, 11, 11, 11, 10, 7]) }],
  quads: k => [{ segs: ['thigh'], pts: k.band('thigh', 0.12, 0.97, 1.1, -0.25, { edge: 'a', ta: 0.4, tb: 0.3 }) }],
  rectus_femoris: k => [{ segs: ['thigh', 'pelvis'], pts: k.band('thigh', -0.12, 0.9, 1.1, 0.4, { edge: 'a', ta: 0.3, tb: 0.35 }) }],
  adductors: k => [{ deep: true, segs: ['thigh'], pts: k.band('thigh', 0.04, 0.62, 0.45, -0.25, { ta: 0.3, tb: 0.7 }) }],
  hamstrings: k => [{ segs: ['thigh'], pts: k.band('thigh', 0.12, 0.97, -1.1, 0.0, { edge: 'a', ta: 0.35, tb: 0.35 }) }],
  soleus: k => [{ segs: ['shin'], pts: k.band('shin', 0.26, 0.9, -1.1, 0.1, { edge: 'a', ta: 0.4, tb: 0.5 }) }],
  gastrocnemius: k => [{ segs: ['shin'], pts: k.band('shin', 0.0, 0.64, -1.1, 0.0, { edge: 'a', ta: 0.3, tb: 0.6, p: 0.7 }) }],
  tibialis_anterior: k => [{ segs: ['shin'], pts: k.band('shin', 0.06, 0.8, 1.1, 0.2, { edge: 'a', ta: 0.3, tb: 0.5 }) }],
  foot: k => [{ segs: ['foot'], pts: k.free([['foot', -8, -17], ['foot', 12, -15], ['foot', 32, -17], ['foot', 46, -18], ['foot', 45, -22], ['foot', 30, -23], ['foot', 12, -21], ['foot', -6, -22]]) }],
};
SIDE_DEFS.traps = k => [...SIDE_DEFS.trap_upper(k), ...SIDE_DEFS.trap_middle(k), ...SIDE_DEFS.trap_lower(k)];

// фас и спина: v у торса зеркалится по стороне (sym), у конечностей f>0 латеральная сторона
const FRONT_DEFS = {
  // дельта: верхняя треть плеча; бицепс по центру передней поверхности плеча до локтевого сгиба
  deltoid: k => [{ segs: ['upper'], pts: deltCap(k, 0.38) }],
  pecs: k => [{ segs: ['chest', 'upper'], pts: k.free([['chest', 81, 2.5], ['chest', 82, 18], ['chest', 79, 33], ['upper', 0.12, -0.6], ['upper', 0.2, -0.2], ['chest', 62, 49], ['chest', 53, 40], ['chest', 47, 27], ['chest', 45.5, 13], ['chest', 47, 2.5]]) }],
  biceps: k => [{ segs: ['upper'], pts: k.band('upper', 0.27, 0.9, -0.78, 0.78, { ta: 0.4, tb: 0.3, p: 0.7 }) }],
  forearm: k => [{ segs: ['fore'], pts: k.band('fore', -0.08, 0.8, -1.1, 1.1, { ta: 0.08, tb: 0.75 }) }],
  rectus_abdominis: k => [{ segs: ['chest', 'pelvis'], pts: k.free([['chest', 42, 1.5], ['chest', 42, 16], ['chest', 24, 17], ['chest', 0, 15], ['chest', -24, 12], ['chest', -46, 5], ['chest', -46, 1.5]]) }],
  obliques: k => [{ segs: ['chest', 'pelvis'], pts: k.free([['chest', 36, 26], ['chest', 32, 42], ['chest', 8, 37], ['chest', -12, 37], ['chest', -30, 30], ['chest', -26, 19], ['chest', -4, 20], ['chest', 16, 22]]) }],
  serratus: k => [{ segs: ['chest'], pts: k.free([['chest', 62, 41], ['chest', 56, 48], ['chest', 40, 45], ['chest', 30, 41], ['chest', 38, 38], ['chest', 50, 40]]) }],
  trap_upper: k => [{ segs: ['chest', 'neck'], pts: k.free([['chest', 89, 12], ['chest', 85, 30], ['chest', 80, 42], ['chest', 77, 34], ['chest', 81, 18], ['chest', 85, 11]]) }],
  neck_flexors: k => [{ segs: ['neck', 'chest', 'head'], pts: k.free([['neck', 1.05, 0.9], ['neck', 0.85, 1.05], ['neck', 0.3, 0.55], ['chest', 81, 7], ['chest', 83, 2], ['neck', 0.3, 0.15], ['neck', 0.85, 0.55]]) }],
  // квадрицепс до надколенника, внизу медиально капля медиальной широкой
  // квадрицепс: вся передняя поверхность бедра от паховой складки (сбоку выше, у промежности ниже) до надколенника,
  // латеральная широкая снаружи, внизу медиально капля медиальной широкой
  quads: k => [{ segs: ['thigh'], pts: k.free([['thigh', 0.1, 1.15], ['thigh', 0.13, 0.6], ['thigh', 0.18, 0.12], ['thigh', 0.3, -0.12], ['thigh', 0.45, -0.38], ['thigh', 0.6, -0.62], ['thigh', 0.76, -0.88], ['thigh', 0.9, -0.75], ['thigh', 0.97, -0.2], ['thigh', 0.96, 0.4], ['thigh', 0.88, 0.85], ['thigh', 0.7, 1.12], ['thigh', 0.4, 1.15]]) }],
  rectus_femoris: k => [{ segs: ['thigh', 'pelvis'], pts: k.band('thigh', -0.05, 0.86, -0.3, 0.42, { ta: 0.35, tb: 0.35 }) }],
  // приводящие: внутренняя поверхность бедра от паховой складки (у промежности) до середины бедра, не на тазу
  adductors: k => [{ segs: ['thigh'], pts: k.free([['thigh', 0.16, -1.25], ['thigh', 0.17, 0.05], ['thigh', 0.3, -0.12], ['thigh', 0.45, -0.38], ['thigh', 0.6, -0.64], ['thigh', 0.66, -1.0], ['thigh', 0.6, -1.25], ['thigh', 0.4, -1.3]]) }],
  tfl: k => [{ segs: ['pelvis', 'thigh'], pts: k.free([['pelvis', 26, 40], ['pelvis', 12, 46], ['thigh', 0.32, 1.1], ['thigh', 0.28, 0.65], ['pelvis', 10, 35]]) }],
  glute_med: k => [{ segs: ['pelvis'], pts: k.free([['pelvis', 52, 36], ['pelvis', 30, 43], ['pelvis', 10, 46], ['pelvis', 16, 38], ['pelvis', 36, 34]]) }],
  glute_min: k => [{ deep: true, segs: ['pelvis'], pts: k.free([['pelvis', 40, 34], ['pelvis', 24, 42], ['pelvis', 10, 43], ['pelvis', 20, 34]]) }],
  iliopsoas: k => [{ deep: true, segs: ['chest', 'pelvis', 'thigh'], pts: k.tube([['chest', 16, 6], ['pelvis', 40, 13], ['pelvis', 14, 22], ['thigh', 0.16, -0.5]], [9, 14, 13, 7]) }],
  tibialis_anterior: k => [{ segs: ['shin'], pts: k.band('shin', 0.08, 0.8, 0.0, 0.85, { ta: 0.3, tb: 0.5 }) }],
  gastrocnemius: k => [{ segs: ['shin'], pts: k.band('shin', 0.06, 0.58, -1.1, -0.45, { edge: 'a', ta: 0.3, tb: 0.6 }) }],
  soleus: k => [{ segs: ['shin'], pts: k.band('shin', 0.35, 0.86, -1.1, -0.55, { edge: 'a', ta: 0.4, tb: 0.5 }) }],
  foot: k => [{ segs: ['foot'], pts: k.free([['foot', 6, -10], ['foot', 20, -11], ['foot', 22, 0], ['foot', 20, 11], ['foot', 6, 10], ['foot', 10, 0]]) }],
};
const BACK_DEFS = {
  deltoid: FRONT_DEFS.deltoid,
  trap_upper: k => [{ segs: ['chest', 'neck'], pts: k.free([['neck', 0.75, 0.2], ['neck', 0.55, 1.05], ['chest', 85, 30], ['chest', 80, 42], ['chest', 75, 36], ['chest', 75, 16], ['chest', 77, 2], ['neck', 0.2, 0.05]]) }],
  trap_middle: k => [{ segs: ['chest'], pts: k.free([['chest', 77, 1], ['chest', 75, 16], ['chest', 75, 36], ['chest', 71, 43], ['chest', 62, 38], ['chest', 58, 20], ['chest', 58, 1]]) }],
  trap_lower: k => [{ segs: ['chest'], pts: k.free([['chest', 58, 1], ['chest', 58, 20], ['chest', 61, 32], ['chest', 52, 28], ['chest', 38, 12], ['chest', 26, 2]]) }],
  rhomboids: k => [{ deep: true, segs: ['chest'], pts: k.free([['chest', 77, 4], ['chest', 66, 22], ['chest', 50, 33], ['chest', 46, 27], ['chest', 60, 9], ['chest', 70, 3]]) }],
  lats: k => [{ segs: ['chest', 'pelvis'], pts: k.free([['chest', 52, 32], ['chest', 64, 50], ['chest', 54, 53], ['chest', 34, 48], ['chest', 10, 41], ['chest', -8, 31], ['chest', -14, 14], ['chest', -14, 4], ['chest', 6, 4], ['chest', 30, 12], ['chest', 44, 24]]) }],
  erectors: k => [{ segs: ['chest', 'pelvis'], pts: k.free([['pelvis', 36, 3], ['pelvis', 38, 14], ['chest', 0, 15], ['chest', 30, 12], ['chest', 60, 7], ['chest', 64, 3]]) }],
  glute_max: k => [{ segs: ['pelvis', 'thigh'], pts: k.free([['pelvis', 30, 3], ['pelvis', 36, 14], ['pelvis', 33, 28], ['pelvis', 22, 41], ['pelvis', 4, 47], ['pelvis', -14, 44], ['pelvis', -24, 34], ['pelvis', -29, 20], ['pelvis', -27, 8], ['pelvis', -18, 2.5], ['pelvis', 8, 1.5]]) }],
  // средняя ягодичная: верхне-наружная часть под гребнем таза, над большой ягодичной
  glute_med: k => [{ segs: ['pelvis'], pts: k.free([['pelvis', 54, 22], ['pelvis', 56, 38], ['pelvis', 46, 46], ['pelvis', 28, 47], ['pelvis', 18, 44], ['pelvis', 26, 34], ['pelvis', 35, 22], ['pelvis', 44, 17]]) }],
  glute_min: k => [{ deep: true, segs: ['pelvis'], pts: k.free([['pelvis', 40, 30], ['pelvis', 30, 44], ['pelvis', 14, 46], ['pelvis', 22, 32]]) }],
  piriformis: k => [{ deep: true, segs: ['pelvis'], pts: k.tube([['pelvis', 22, 6], ['pelvis', 16, 26], ['pelvis', 8, 44]], [12, 11, 6]) }],
  triceps: k => [{ segs: ['upper'], pts: k.band('upper', 0.15, 0.92, -0.7, 0.75, { ta: 0.4, tb: 0.3 }) }],
  forearm: FRONT_DEFS.forearm,
  hamstrings: k => [{ segs: ['thigh'], pts: k.band('thigh', 0.18, 0.97, -0.7, 0.8, { ta: 0.35, tb: 0.35 }) }],
  adductors: k => [{ segs: ['thigh'], pts: k.band('thigh', 0.24, 0.6, -1.1, -0.55, { edge: 'a', ta: 0.2, tb: 0.75 }) }],
  soleus: k => [{ segs: ['shin'], pts: k.band('shin', 0.32, 0.9, -1.1, 1.1, { ta: 0.35, tb: 0.55 }) }],
  gastrocnemius: k => [
    { segs: ['shin'], pts: k.band('shin', 0.04, 0.62, -1.1, -0.05, { edge: 'a', ta: 0.3, tb: 0.6 }) },
    { segs: ['shin'], pts: k.band('shin', 0.04, 0.55, 0.05, 1.1, { edge: 'b', ta: 0.3, tb: 0.6 }) }],
  foot: k => [{ segs: ['foot'], pts: k.free([['foot', 4, -8], ['foot', 18, -9], ['foot', 22, 0], ['foot', 18, 9], ['foot', 4, 8], ['foot', 8, 0]]) }],
  obliques: FRONT_DEFS.obliques,
  tfl: FRONT_DEFS.tfl,
  neck_flexors: () => [],
};
BACK_DEFS.traps = k => [...BACK_DEFS.trap_upper(k), ...BACK_DEFS.trap_middle(k), ...BACK_DEFS.trap_lower(k)];
FRONT_DEFS.traps = FRONT_DEFS.trap_upper;
const FRONT_TORSO = new Set(['pecs', 'rectus_abdominis', 'obliques', 'serratus', 'trap_upper', 'neck_flexors', 'tfl', 'glute_med', 'glute_min', 'iliopsoas', 'trap_middle', 'trap_lower', 'rhomboids', 'lats', 'erectors', 'glute_max', 'piriformis', 'traps']);

// ---------- снаряды ----------
const eqStyle = (sw = 2.5) => `fill="${COL.equip}" stroke="${COL.equipLine}" stroke-width="${sw}" stroke-linejoin="round"`;
function rodSvg(a, b, w) {
  return `<line x1="${fx(a[0])}" y1="${fx(a[1])}" x2="${fx(b[0])}" y2="${fx(b[1])}" stroke="${COL.equipLine}" stroke-width="${w + 5}" stroke-linecap="round"/>` +
    `<line x1="${fx(a[0])}" y1="${fx(a[1])}" x2="${fx(b[0])}" y2="${fx(b[1])}" stroke="${COL.equip}" stroke-width="${w}" stroke-linecap="round"/>`;
}
function boxOf(points, pad = 0) {
  const xs = points.map(p => p[0]), ys = points.map(p => p[1]);
  return { x0: Math.min(...xs) - pad, y0: Math.min(...ys) - pad, x1: Math.max(...xs) + pad, y1: Math.max(...ys) + pad };
}
function rectSvg(x, y, w, h, rx = 5, extra = '') { return `<rect x="${fx(x)}" y="${fx(y)}" width="${fx(w)}" height="${fx(h)}" rx="${rx}" ${eqStyle()} ${extra}/>`; }
function polySvg(pts) { return `<path d="M${pts.map(fp).join('L')}Z" ${eqStyle()}/>`; }
function rotRect(c, ang, w, h, rx = 6) {
  return `<rect x="${fx(-w / 2)}" y="${fx(-h / 2)}" width="${fx(w)}" height="${fx(h)}" rx="${rx}" transform="translate(${fp(c)}) rotate(${fx(ang)})" ${eqStyle()}/>`;
}

function drawEquip(e, ctx) {
  const R = p => ctx.resolve(p);
  const view = ctx.view, S = ctx.S;
  const floor = e.floor ?? ctx.floor ?? 600;
  switch (e.type) {
    case 'mat': {
      const y = e.y ?? floor, x = e.x ?? 120, w = e.w ?? 660, h = e.h ?? 12;
      return { svg: rectSvg(x, y, w, h, h / 2), box: { x0: x, y0: y, x1: x + w, y1: y + h } };
    }
    case 'floor': {
      const y = e.y ?? floor;
      return { svg: `<line x1="${e.x0 ?? 50}" y1="${fx(y)}" x2="${e.x1 ?? 850}" y2="${fx(y)}" stroke="${COL.floor}" stroke-width="3" stroke-linecap="round"/>`, box: null };
    }
    case 'bench': {
      const x = e.x, y = e.y, w = e.w ?? 300, t = e.t ?? 20;
      const legs = [x + 30, x + w - 30];
      let svg = '';
      for (const lx of legs) svg += polySvg([[lx - 7, y + t - 2], [lx + 7, y + t - 2], [lx + 9, floor - 6], [lx - 9, floor - 6]]) + rectSvg(lx - 26, floor - 8, 52, 8, 3);
      svg += rectSvg(x, y, w, t, 8);
      return { svg, box: { x0: x - 4, y0: y, x1: x + w + 4, y1: floor } };
    }
    case 'incline_bench': {
      // hinge: верхняя точка стыка сиденья и спинки, angle: наклон спинки от горизонта,
      // back: куда смотрит спинка от шарнира ('left' или 'right'), len: длина спинки, seat: длина сиденья
      const H = R(e.hinge || e.at), a = e.angle ?? 35, lenB = e.len ?? 230, seat = e.seat ?? 90, t = 20;
      const dirS = (e.back || 'left') === 'left' ? 1 : -1;
      const bd = dirv(dirS > 0 ? 180 + a : -a);
      const down = dirS > 0 ? [bd[1], -bd[0]] : [-bd[1], bd[0]];
      const top = add(H, mul(bd, lenB));
      const seatEnd = [H[0] + dirS * seat, H[1]];
      const padPts = [H, top, add(top, mul(down, t)), add(H, mul(down, t))];
      const mid = add(add(H, mul(bd, lenB * 0.55)), mul(down, t));
      const postX = H[0] + dirS * seat * 0.45;
      const xs = [top[0], seatEnd[0], H[0]];
      let svg = '';
      svg += rodSvg([postX, H[1] + t], [postX, floor - 8], 8);
      svg += rodSvg([postX, floor - 30], mid, 6);
      svg += rectSvg(Math.min(...xs) - 10, floor - 8, Math.max(...xs) - Math.min(...xs) + 20, 8, 3);
      svg += rectSvg(Math.min(H[0], seatEnd[0]) - 6, H[1], seat + 12, t, 8);
      svg += `<path d="${smoothClosed([...padPts.map((p, k) => p)], 0.15)}" ${eqStyle()}/>`;
      return { svg, box: boxOf([H, top, seatEnd, [H[0], floor]], 12) };
    }
    case 'box': {
      const x = e.x, y = e.y, w = e.w ?? 120, h = e.h ?? (floor - e.y);
      return { svg: rectSvg(x, y, w, h, 6), box: { x0: x, y0: y, x1: x + w, y1: y + h } };
    }
    case 'wall': {
      const x = e.x, top = e.top ?? 120, bottom = e.bottom ?? floor, w = e.w ?? 20;
      const xx = (e.side || 'right') === 'right' ? x : x - w;
      return { svg: rectSvg(xx, top, w, bottom - top, 3), box: { x0: xx, y0: top, x1: xx + w, y1: bottom } };
    }
    case 'stick': case 'band': {
      const a = R(e.from), b = R(e.to);
      const w = e.type === 'stick' ? (e.w ?? 7) : (e.w ?? 5);
      return { svg: rodSvg(a, b, w), box: boxOf([a, b], w) };
    }
    case 'barbell': {
      const c = R(e.at), r = (e.r ?? 52) * S;
      if (view === 'side') {
        const svg = `<circle cx="${fx(c[0])}" cy="${fx(c[1])}" r="${fx(r)}" ${eqStyle()}/>` +
          `<circle cx="${fx(c[0])}" cy="${fx(c[1])}" r="${fx(r * 0.78)}" fill="none" stroke="${COL.equipLine}" stroke-width="1.5" opacity="0.5"/>` +
          `<circle cx="${fx(c[0])}" cy="${fx(c[1])}" r="${fx(r * 0.2)}" ${eqStyle()}/>` +
          `<circle cx="${fx(c[0])}" cy="${fx(c[1])}" r="${fx(r * 0.08)}" fill="${COL.equipLine}"/>`;
        // гриф почти торцом: короткая втулка (около 30 px) выходит из кулака поверх блина, чтобы хват читался
        if (e.sleeve === false) return { svg, box: boxOf([c], r) };
        const sl = (e.sleeveLen ?? 30) * S;
        // направление втулки: первое из кандидатов, где она не уходит под руку, голову или корпус
        const cands = typeof e.sleeve === 'number' ? [e.sleeve] : (ctx.facing === 'left' ? [45, -45, 135, 0, 90, -135, 180, -90] : [135, -135, 45, 180, 90, -45, 0, -90]);
        const sa = cands.find(a => [0.55, 0.8, 1].every(f => !ctx.inBody(add(c, mul(dirv(a), sl * f + 6))))) ?? cands[0];
        const se = add(c, mul(dirv(sa), sl));
        const handSvg = rodSvg(c, se, 7 * S) + `<circle cx="${fx(se[0])}" cy="${fx(se[1])}" r="${fx(5.5 * S)}" ${eqStyle(2)}/>`;
        return { svg, box: boxOf([c, se], r), handSvg, handAt: c };
      }
      const half = (e.w ?? 470) / 2;
      let svg = rodSvg([c[0] - half, c[1]], [c[0] + half, c[1]], 6);
      for (const sgn of [-1, 1]) {
        const px = c[0] + sgn * (half - 60);
        svg += rectSvg(px - 11, c[1] - r, 22, 2 * r, 4) + rectSvg(px + sgn * 15 - 6, c[1] - r * 0.7, 12, 1.4 * r, 3);
      }
      return { svg, box: { x0: c[0] - half, y0: c[1] - r, x1: c[0] + half, y1: c[1] + r } };
    }
    case 'dumbbell': {
      // в профиль по умолчанию гантель боком (нейтральный хват): ручка поперёк кисти, кулак закрывает её середину,
      // по обе стороны кулака видны короткие куски ручки и диски r 22. orient: 'end' даёт вид с торца
      // (большой диск с ободом поверх кисти)
      const c = R(e.at);
      if (view === 'side' && e.orient === 'end') {
        const r = (e.r ?? 23) * S;
        const svg = `<circle cx="${fx(c[0])}" cy="${fx(c[1])}" r="${fx(r)}" ${eqStyle()}/>` + `<circle cx="${fx(c[0])}" cy="${fx(c[1])}" r="${fx(r - 4 * S)}" fill="none" stroke="${COL.equipLine}" stroke-width="1.6" opacity="0.6"/>` + `<circle cx="${fx(c[0])}" cy="${fx(c[1])}" r="${fx(r * 0.28)}" ${eqStyle(2)}/>`;
        return { svg, box: boxOf([c], r), layer: 'front' };
      }
      const r = (e.r ?? (view === 'side' ? 22 : 17)) * S;
      const hd = view === 'side' && e.angle == null ? ctx.handDir(e.at) : null;
      const a = e.angle ?? (hd ? deg(Math.atan2(hd[1], hd[0])) + 90 : 0), half = (e.len ?? (view === 'side' ? 76 : 70)) * S / 2;
      const d = dirv(a), pw = (view === 'side' ? 15 : 14) * S;
      let svg = rodSvg(sub(c, mul(d, half)), add(c, mul(d, half)), 6);
      for (const sgn of [-1, 1]) {
        svg += rotRect(add(c, mul(d, sgn * (half - pw / 2))), a, pw, 2 * r, 4);
        if (view === 'side') svg += rotRect(add(c, mul(d, sgn * (half - pw - 3 * S))), a, 6 * S, 1.3 * r, 2);
      }
      return { svg, box: boxOf([sub(c, mul(d, half)), add(c, mul(d, half))], r) };
    }
    case 'kettlebell': {
      const c = R(e.at), r = (e.r ?? 20) * S;
      const svg = `<path d="M${fx(c[0] - r * 0.55)},${fx(c[1] + r * 0.2)} L${fx(c[0] - r * 0.6)},${fx(c[1] - r * 0.6)} Q${fx(c[0])},${fx(c[1] - r * 1.3)} ${fx(c[0] + r * 0.6)},${fx(c[1] - r * 0.6)} L${fx(c[0] + r * 0.55)},${fx(c[1] + r * 0.2)}" fill="none" stroke="${COL.equipLine}" stroke-width="6" stroke-linecap="round"/>` +
        `<circle cx="${fx(c[0])}" cy="${fx(c[1] + r)}" r="${fx(r)}" ${eqStyle()}/>`;
      return { svg, box: boxOf([c], r * 2) };
    }
    case 'plate': {
      const c = R(e.at), r = (e.r ?? 30) * S;
      const svg = `<circle cx="${fx(c[0])}" cy="${fx(c[1])}" r="${fx(r)}" ${eqStyle()}/>` + `<circle cx="${fx(c[0])}" cy="${fx(c[1])}" r="${fx(r * 0.22)}" fill="#fff" stroke="${COL.equipLine}" stroke-width="2"/>`;
      return { svg, box: boxOf([c], r) };
    }
    case 'ball': case 'foam_roller': {
      const c = R(e.at), r = (e.r ?? (e.type === 'ball' ? 60 : 18)) * S;
      let svg = `<circle cx="${fx(c[0])}" cy="${fx(c[1])}" r="${fx(r)}" ${eqStyle()}/>`;
      if (e.type === 'ball') svg += `<path d="M${fx(c[0] - r * 0.7)},${fx(c[1] - r * 0.4)} Q${fx(c[0])},${fx(c[1] - r * 0.05)} ${fx(c[0] + r * 0.7)},${fx(c[1] - r * 0.4)}" fill="none" stroke="${COL.equipLine}" stroke-width="1.5" opacity="0.6"/>`;
      else svg += `<circle cx="${fx(c[0])}" cy="${fx(c[1])}" r="${fx(r * 0.35)}" fill="none" stroke="${COL.equipLine}" stroke-width="1.5" opacity="0.6"/>`;
      return { svg, box: boxOf([c], r) };
    }
    case 'cable_low': case 'cable_high': {
      const x = e.x, top = e.top ?? 140, w = 30;
      const py = e.type === 'cable_low' ? floor - 45 : top + 35;
      const px = (e.side || 'right') === 'right' ? x : x + w;
      let svg = rectSvg(x, top, w, floor - top, 4);
      const pul = [px, py];
      // без to трос свободно висит вниз (верхний блок) или лежит к полу (нижний), на конце рукоять
      const tgt = e.to ? R(e.to) : (e.type === 'cable_high' ? [px - 12, py + (e.hang ?? 130)] : [px - 60, floor - 14]);
      const start = e.to || e.type === 'cable_low' ? pul : [px - 11, py];
      svg += `<line x1="${fx(start[0])}" y1="${fx(start[1])}" x2="${fx(tgt[0])}" y2="${fx(tgt[1])}" stroke="${COL.cable}" stroke-width="2.5"/>`;
      svg += `<circle cx="${fx(pul[0])}" cy="${fx(pul[1])}" r="11" ${eqStyle()}/><circle cx="${fx(pul[0])}" cy="${fx(pul[1])}" r="3" fill="${COL.equipLine}"/>`;
      let hbox = null;
      if (e.handle !== false) {
        // D-рукоять: карабин и перекладина поперёк троса
        const dv = sub(tgt, start), L_ = len2(dv) || 1, d = mul(dv, 1 / L_), nv = [-d[1], d[0]];
        const c = add(tgt, mul(d, 16));
        svg += `<path d="M${fp(tgt)} L${fp(add(c, mul(nv, -13)))} L${fp(add(c, mul(nv, 13)))} Z" fill="none" stroke="${COL.equipLine}" stroke-width="3" stroke-linejoin="round"/>`;
        svg += rodSvg(add(c, mul(nv, -15)), add(c, mul(nv, 15)), 5);
        hbox = boxOf([tgt, add(c, mul(nv, -16)), add(c, mul(nv, 16))], 4);
      }
      const bx = { x0: x, y0: top, x1: x + w, y1: floor };
      if (hbox) { bx.x0 = Math.min(bx.x0, hbox.x0); bx.y0 = Math.min(bx.y0, hbox.y0); bx.x1 = Math.max(bx.x1, hbox.x1); bx.y1 = Math.max(bx.y1, hbox.y1); }
      return { svg, box: bx };
    }
    case 'pullup_bar': {
      const c = R(e.at);
      if (view === 'side') {
        const svg = rodSvg([c[0], c[1]], [c[0] + (e.mount ?? -60), c[1] - 40], 6) + `<circle cx="${fx(c[0])}" cy="${fx(c[1])}" r="8" ${eqStyle()}/>`;
        return { svg, box: boxOf([c], 50) };
      }
      const half = (e.w ?? 300) / 2;
      const svg = rodSvg([c[0] - half, c[1]], [c[0] + half, c[1]], 7) + rodSvg([c[0] - half, c[1]], [c[0] - half, c[1] - 60], 7) + rodSvg([c[0] + half, c[1]], [c[0] + half, c[1] - 60], 7);
      return { svg, box: { x0: c[0] - half, y0: c[1] - 60, x1: c[0] + half, y1: c[1] + 8 } };
    }
    case 'dip_bars': {
      const c = R(e.at), h = floor - c[1];
      const svg = rodSvg([c[0] - 60, c[1]], [c[0] + 60, c[1]], 7) + rodSvg([c[0] - 45, c[1]], [c[0] - 45, floor], 7) + rodSvg([c[0] + 45, c[1]], [c[0] + 45, floor], 7);
      return { svg, box: { x0: c[0] - 64, y0: c[1] - 6, x1: c[0] + 64, y1: c[1] + h } };
    }
    case 'machine_leg_ext': {
      // seat: [x, y] передний край сиденья (под коленом), back: x спинки, pad: точка валика (обычно голень у стопы)
      const s = R(e.seat || 'knee_near'), pad = R(e.pad || 'shin_near'), axis = R(e.axis || 'knee_near');
      const backX = e.backX ?? (s[0] - 140);
      let svg = '';
      svg += rectSvg(backX - 40, floor - 8, s[0] - backX + 90, 8, 3);
      svg += polySvg([[backX + 30, s[1] + 20], [backX + 46, s[1] + 20], [backX + 46, floor - 6], [backX + 30, floor - 6]]);
      svg += rotRect([backX - 6, s[1] - 95], -8, 24, 190, 8);
      svg += rectSvg(backX, s[1], s[0] - backX + 10, 22, 8);
      svg += rodSvg(axis, pad, 6);
      svg += `<circle cx="${fx(axis[0])}" cy="${fx(axis[1])}" r="7" ${eqStyle()}/>`;
      svg += `<circle cx="${fx(pad[0])}" cy="${fx(pad[1])}" r="13" ${eqStyle()}/>`;
      return { svg, box: boxOf([[backX - 40, s[1] - 190], [s[0] + 50, floor], pad], 10) };
    }
    case 'machine_adductor': {
      // фас: сиденье за фигурой, валики у внутренней стороны колен
      const c = R(e.at || 'pelvis');
      let svg = rectSvg(c[0] - 80, c[1] - 220, 160, 210, 14);
      svg += rectSvg(c[0] - 120, c[1] + 8, 240, 24, 8);
      svg += polySvg([[c[0] - 10, c[1] + 32], [c[0] + 10, c[1] + 32], [c[0] + 14, floor - 6], [c[0] - 14, floor - 6]]);
      svg += rectSvg(c[0] - 90, floor - 8, 180, 8, 3);
      for (const p of (e.pads || ['knee_l', 'knee_r'])) { const q = R(p); svg += rotRect(q, 90, 70, 18, 8); }
      return { svg, box: { x0: c[0] - 130, y0: c[1] - 220, x1: c[0] + 130, y1: floor } };
    }
    case 'roman_chair': {
      // hip: валик под тазом, foot: валик за пятками
      const hp = R(e.hip || 'pelvis'), ft = R(e.foot || 'ankle_near');
      const d = sub(hp, ft), a = deg(Math.atan2(d[1], d[0]));
      let svg = rodSvg(add(ft, [0, 18]), add(hp, [0, 24]), 7);
      svg += rodSvg(add(ft, [0, 18]), [ft[0], floor - 6], 7) + rodSvg(add(hp, [0, 24]), [hp[0] + 10, floor - 6], 7);
      svg += rectSvg(Math.min(ft[0], hp[0]) - 40, floor - 8, Math.abs(hp[0] - ft[0]) + 90, 8, 3);
      svg += rotRect(add(hp, [0, 10]), a, 70, 22, 9);
      svg += `<circle cx="${fx(ft[0])}" cy="${fx(ft[1] + 12)}" r="11" ${eqStyle()}/>`;
      return { svg, box: boxOf([hp, ft, [hp[0], floor]], 30) };
    }
    case 'rect': return { svg: rectSvg(e.x, e.y, e.w, e.h, e.rx ?? 5), box: { x0: e.x, y0: e.y, x1: e.x + e.w, y1: e.y + e.h } };
    case 'circle': { const c = R(e.at); return { svg: `<circle cx="${fx(c[0])}" cy="${fx(c[1])}" r="${fx(e.r)}" ${eqStyle()}/>`, box: boxOf([c], e.r) }; }
    case 'line': { const a = R(e.from), b = R(e.to); return { svg: rodSvg(a, b, e.w ?? 6), box: boxOf([a, b], 6) }; }
    case 'poly': { const p = e.points.map(R); return { svg: polySvg(p), box: boxOf(p) }; }
    default: throw new Error('Неизвестный снаряд: ' + e.type);
  }
}
const EQUIP_LAYER = { barbell: 'back', dumbbell: 'hand', kettlebell: 'hand', plate: 'hand', stick: 'hand', band: 'front', pullup_bar: 'back' };

// ---------- точки ----------
let CURRENT = null; // контекст текущей сборки для resolveRaw
function resolveRaw(p) {
  if (Array.isArray(p)) return p;
  if (typeof p === 'string') return CURRENT.world(p);
  if (p && typeof p === 'object') {
    const b = p.at ? resolveRaw(p.at) : [p.x || 0, p.y || 0];
    return [b[0] + (p.dx || 0), b[1] + (p.dy || 0)];
  }
  throw new Error('Не понимаю точку: ' + JSON.stringify(p));
}

// ---------- текст ----------
const textW = (s, size) => String(s).length * size * 0.62;
function wrap(text, size, maxW) {
  const words = String(text).split(/\s+/), lines = [];
  let cur = '';
  for (const w of words) {
    const t = cur ? cur + ' ' + w : w;
    if (textW(t, size) > maxW && cur) { lines.push(cur); cur = w; } else cur = t;
  }
  if (cur) lines.push(cur);
  return lines;
}

// ---------- построение фигуры ----------
function buildFigure(spec) {
  const P = spec.pose || {};
  const view = spec.view || 'side';
  const pel = P.pelvis || [450, 330];
  const xf = makeXf(pel[0], typeof pel[1] === 'number' ? pel[1] : 0, P.rotate || 0, (P.facing || 'right') === 'left');
  const fig = { xf };
  let F = view === 'side' ? buildSide(spec, xf) : buildFront(spec, xf, view === 'back');
  // авто-высота: таз ставится так, чтобы нижняя точка тела легла на пол
  if (typeof pel[1] !== 'number') {
    const floor = spec.floor ?? 600;
    let maxY = -1e9;
    for (const k in F.segs) {
      const s = F.segs[k];
      if (!s.A) continue;
      const pts = s.kind === 'frame' ? s.pts.map(p => framePt(s, p[0], p[1])) : [segPt(s, 0, 1), segPt(s, 0, -1), segPt(s, 1, 1), segPt(s, 1, -1), segPt(s, 0.5, 1), segPt(s, 0.5, -1)];
      for (const p of pts) maxY = Math.max(maxY, xf(p)[1]);
    }
    const nx = makeXf(pel[0], floor - maxY, P.rotate || 0, (P.facing || 'right') === 'left');
    Object.assign(fig, { xf: nx });
    F = view === 'side' ? buildSide(spec, nx) : buildFront(spec, nx, view === 'back');
  }
  Object.assign(fig, F);
  if (fig.view === 'side' && P.hideSlivers !== false) hideFarSlivers(fig);
  fig.world = n => {
    if (!(n in fig.pts)) throw new Error('Неизвестная точка тела: ' + n + '. Есть: ' + Object.keys(fig.pts).join(', '));
    return fig.xf(fig.pts[n]);
  };
  return fig;
}

// дальняя конечность почти совпадает с ближней (меньше 8-10 px): серый контур торчит на 2-4 px и даёт
// грязную двойную линию. Такой сегмент не рисуем: видимая часть проверяется на "ядро" (круг радиуса
// SLIVER_R целиком вне ближних частей тела с учётом толщины их контура)
const SLIVER_R = 6.5;
function hideFarSlivers(fig) {
  fig.hiddenSegs = new Set();
  fig.clusters.forEach((c, ci) => {
    if (!c.far) return;
    const wpoly = n => pathPts(outlineOf(fig, n)).map(p => fig.xf(p));
    const occ = fig.clusters.slice(ci + 1).flatMap(o => o.segs.map(wpoly)).filter(p => p.length);
    const covered = q => occ.some(pl => pip(q, pl));
    const ring = [];
    for (let k = 0; k < 12; k++) { const d = dirv(k * 30); ring.push(mul(d, SLIVER_R + SW), mul(d, (SLIVER_R + SW) / 2)); }
    let visArea = 0;
    for (const n of c.segs) {
      const pl = wpoly(n), b = boxOf(pl);
      let core = false, area = 0;
      for (let x = b.x0; x <= b.x1; x += 1.5) for (let y = b.y0; y <= b.y1; y += 1.5) {
        const q = [x, y];
        if (!pip(q, pl) || covered(q)) continue;
        area += 2.25;
        if (!core && ring.every(d => !covered(add(q, d)))) core = true;
      }
      if (!core) fig.hiddenSegs.add(n); else visArea += area;
    }
    // корень конечности спрятан, а от остального видно мало (висящее предплечье из-за корпуса): прячем целиком
    if (fig.hiddenSegs.has(c.segs[0]) && visArea < 700) c.segs.forEach(n => fig.hiddenSegs.add(n));
    c.segs = c.segs.filter(n => !fig.hiddenSegs.has(n));
  });
}
const expandSegs = (fig, list) => list.flatMap(n => (fig.segs[n].kind === 'chain' ? fig.segs[n].parts : [n]));
function figureOutlinePts(fig) {
  const out = [];
  for (const c of fig.clusters) for (const n of expandSegs(fig, c.segs)) {
    const s = fig.segs[n];
    if (s.kind === 'custom') { s.pts.forEach(p => out.push(fig.xf(p))); continue; }
    if (s.kind === 'frame') s.pts.forEach(p => out.push(fig.xf(framePt(s, p[0], p[1]))));
    else for (let i = 0; i <= 4; i++) { out.push(fig.xf(segPt(s, i / 4, 1.05))); out.push(fig.xf(segPt(s, i / 4, -1.05))); }
    if (s.kind !== 'frame') { out.push(fig.xf(add(s.A, mul(s.d, -profAt(s.prof, 0)[0] * s.S)))); out.push(fig.xf(add(s.B, mul(s.d, profAt(s.prof, 1)[0] * s.S)))); }
  }
  return out;
}

function segPolys(fig) {
  const out = [];
  for (const c of fig.clusters) for (const n of expandSegs(fig, c.segs)) out.push(segPoly(fig, n));
  return out;
}
function segPoly(fig, n) {
  const s = fig.segs[n];
  if (s.kind === 'chain') return [];
  if (s.kind === 'custom') return s.pts.map(p => fig.xf(p));
  if (s.kind === 'frame') return s.pts.map(p => fig.xf(framePt(s, p[0], p[1])));
  const a = [], b = [];
  for (let i = 0; i <= 8; i++) { a.push(fig.xf(segPt(s, i / 8, 1))); b.push(fig.xf(segPt(s, i / 8, -1))); }
  return [fig.xf(add(s.A, mul(s.d, -profAt(s.prof, 0)[0] * s.S * 0.8))), ...a, fig.xf(add(s.B, mul(s.d, profAt(s.prof, 1)[0] * s.S * 0.8))), ...b.reverse()];
}
// видимая часть мышцы: точки сетки внутри фигуры мышцы, внутри своих сегментов и не закрытые кластерами спереди.
// vis: видимые точки (шаг 2.5 px), all: точки без учёта перекрытия (для мышц целиком под рукой)
function visibleInfo(fig, items) {
  const later = ci => fig.clusters.slice(ci + 1).flatMap(c => expandSegs(fig, c.segs).map(n => segPoly(fig, n)));
  let best = [], all = [];
  for (const it of items) {
    const poly = it.sh.pts.map(p => fig.xf(p));
    const own = it.segNames.flatMap(n => expandSegs(fig, [n])).map(n => segPoly(fig, n));
    if (fig.segs.trunk && it.segNames.some(n => fig.segs.trunk.parts.includes(n))) own.push(segPoly(fig, 'trunk'));
    const front = later(it.ci);
    const bx = boxOf(poly);
    const vis = [], a = [];
    for (let x = bx.x0; x <= bx.x1; x += 2.5) for (let y = bx.y0; y <= bx.y1; y += 2.5) {
      const q = [x, y];
      if (pip(q, poly) && own.some(pl => pip(q, pl))) { a.push(q); if (!front.some(pl => pip(q, pl))) vis.push(q); }
    }
    if (vis.length > best.length) best = vis;
    if (a.length > all.length) all = a;
  }
  const pts = items[0].sh.pts;
  return { vis: best, all, fallback: fig.xf(pts.reduce((acc, p) => add(acc, p), [0, 0]).map(v => v / pts.length)) };
}
// точка выноски: ближе к центру видимой области, с запасом от края и не ближе minD к уже занятым якорям
function pickAnchor(pts, avoid, minD = 18) {
  if (!pts.length) return null;
  const c = pts.reduce((a, p) => add(a, p), [0, 0]).map(v => v / pts.length);
  const near = (q, d) => pts.some(r => Math.abs(r[0] - q[0] - d[0]) < 1.3 && Math.abs(r[1] - q[1] - d[1]) < 1.3);
  const inner = pts.filter(q => [[3, 0], [-3, 0], [0, 3], [0, -3]].every(d => near(q, d)));
  const pool = (inner.length ? inner : pts).map(q => ({ q, dc: len2(sub(q, c)), da: avoid.length ? Math.min(...avoid.map(a => len2(sub(q, a)))) : 1e9 }));
  const ok = pool.filter(o => o.da >= minD);
  if (ok.length) return ok.reduce((m, o) => (o.dc < m.dc ? o : m)).q;
  return pool.reduce((m, o) => (o.da > m.da ? o : m)).q;
}
const segX = (p1, p2, p3, p4) => {
  const d = (a, b, c) => (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0]);
  const d1 = d(p3, p4, p1), d2 = d(p3, p4, p2), d3 = d(p1, p2, p3), d4 = d(p1, p2, p4);
  return ((d1 > 0 && d2 < 0) || (d1 < 0 && d2 > 0)) && ((d3 > 0 && d4 < 0) || (d3 < 0 && d4 > 0));
};
function pip(pt, poly) {
  let ins = false;
  for (let i = 0, j = poly.length - 1; i < poly.length; j = i++) {
    const [xi, yi] = poly[i], [xj, yj] = poly[j];
    if ((yi > pt[1]) !== (yj > pt[1]) && pt[0] < (xj - xi) * (pt[1] - yi) / (yj - yi) + xi) ins = !ins;
  }
  return ins;
}

// перекрытия для маски мышцы: сегменты того же слоя, нарисованные позже первого своего сегмента
// и не входящие в мышцу. В профиль мышцы живота дополнительно закрывает ближнее бедро при согнутом
// тазобедренном (четвереньки, присед): иначе прямая мышца вылезает клином на пах и бедро
const ABDOMINAL = new Set(['rectus_abdominis', 'obliques']);
function occludersOf(F, c, own, it) {
  const list = expandSegs(F, c.segs);
  const idx = Math.min(...own.map(n => list.indexOf(n)).filter(i => i >= 0));
  const poly = it.sh.pts.map(p => F.xf(p)), bx = boxOf(poly);
  const hit = pl => { if (!pl.length) return false; const b = boxOf(pl); return b.x0 < bx.x1 && b.x1 > bx.x0 && b.y0 < bx.y1 && b.y1 > bx.y0; };
  const out = [];
  if (isFinite(idx)) for (let i = idx + 1; i < list.length; i++) {
    const n = list[i];
    if (own.includes(n) || n.startsWith('_')) continue;
    // в профиль корпус не закрывает мышцы бедра: при согнутом бедре оно визуально впереди живота (складка)
    if (F.view === 'side' && n === 'trunk') continue;
    if (hit(segPoly(F, n))) out.push(outlineOf(F, n));
  }
  if (F.view === 'side' && ABDOMINAL.has(it.m.name)) {
    const th = F.segs['thigh_' + F.near], j = F.segs['_j_' + F.near];
    if (th && j && j.hip > 40) {
      const a = [], b = [];
      for (let i = 0; i <= 10; i++) { a.push(segPt(th, 0.02 + 0.98 * i / 10, 1.08)); b.push(segPt(th, 0.02 + 0.98 * i / 10, -1.08)); }
      out.push('M' + [...a, ...b.reverse()].map(fp).join('L') + 'Z');
    }
  }
  return out;
}

// ---------- главная функция ----------
function drawExercise(spec) {
  spec = JSON.parse(JSON.stringify(spec));
  const view = spec.view || 'side';
  const defs = [], uid = (() => { let i = 0; return p => `${p}${++i}`; })();
  const fig = buildFigure(spec);
  CURRENT = fig;
  const resolve = p => resolveRaw(p);
  // направление кисти (запястье -> пальцы) на холсте для точки вида hand_near / {at: 'hand_l'}
  const handDir = p => {
    const nm = typeof p === 'string' ? p : p && typeof p.at === 'string' ? p.at : null;
    const m = nm && nm.match(/^(hand|wrist|fingers)_(l|r|near|far)$/);
    if (!m) return null;
    const sd = m[2] === 'near' ? (fig.near || 'l') : m[2] === 'far' ? (fig.far || 'r') : m[2];
    const h = fig.segs['hand_' + sd];
    const v = sub(fig.xf(h.B || framePt(h, 40, 0)), fig.xf(h.A));
    return mul(v, 1 / (len2(v) || 1));
  };
  const bodyPolys = segPolys(fig).filter(p => p.length);
  const ctx = { view, S: fig.S, floor: spec.floor, resolve, handDir, facing: (spec.pose || {}).facing || 'right', inBody: q => bodyPolys.some(pl => pip(q, pl)) };

  // --- мышцы: нормализация
  let mlist = [];
  for (const m of spec.muscles || []) mlist.push(typeof m === 'string' ? { name: m } : m);
  for (const n of spec.work || []) mlist.push(typeof n === 'string' ? { name: n, type: 'work' } : Object.assign({ type: 'work' }, n));
  for (const n of spec.stretch || []) mlist.push(typeof n === 'string' ? { name: n, type: 'stretch' } : Object.assign({ type: 'stretch' }, n));
  mlist = mlist.map(m => {
    const name = ALIASES[m.name] || m.name;
    if (!NAMES[name] && name !== 'traps') throw new Error('Неизвестная мышца: ' + m.name + '. Есть: ' + Object.keys(NAMES).join(', '));
    return Object.assign({ type: 'work', side: view === 'side' ? 'near' : 'both' }, m, { name });
  });
  const DEFS = view === 'side' ? SIDE_DEFS : view === 'front' ? FRONT_DEFS : BACK_DEFS;

  // распределение фигур мышц по кластерам
  const segCluster = {};
  fig.clusters.forEach((c, i) => expandSegs(fig, c.segs).forEach(s => { segCluster[s] = i; (fig.segs[s].parts || []).forEach(p => { segCluster[p] = i; }); }));
  const perCluster = fig.clusters.map(() => []);
  const labels = [];
  for (const m of mlist) {
    const def = DEFS[m.name];
    if (!def) { continue; }
    let sides;
    if (view === 'side') {
      const isTorso = TORSO_MUSCLES.has(m.name);
      const want = m.side === 'both' ? ['l', 'r'] : m.side === 'far' ? [fig.far] : m.side === 'near' ? [fig.near] : [m.side];
      sides = isTorso ? [fig.near] : want;
    } else {
      sides = m.side === 'both' ? ['l', 'r'] : m.side === 'near' ? ['l'] : [m.side];
    }
    let anchorPts = null;
    const allItems = [], altItems = [];
    for (const sd of sides) {
      const sym = view === 'side' ? 1 : fig.sgOf(sd);
      // frame-сегменты торса в фас зеркалятся по стороне
      if (view !== 'side') for (const n of ['pelvis', 'chest', 'head']) fig.segs[n].sym = 'side';
      const kit = shapeKit(fig, sd, sym);
      const shapes = def(kit);
      const items = [];
      for (const sh of shapes) {
        const segNames = sh.segs.map(kit.segName);
        if (fig.hiddenSegs && segNames.every(n => fig.hiddenSegs.has(n))) continue;
        const ci = segCluster[segNames[0]] ?? 0;
        const far = view === 'side' && fig.clusters[ci].far;
        const it = { m, sh, segNames, far, ci };
        perCluster[ci].push(it); items.push(it); allItems.push(it);
      }
      if (items.length && (!anchorPts || (view === 'side' && sd === fig.near))) anchorPts = items;
      if (items.length && view !== 'side') altItems.push(items);
    }
    if (anchorPts && m.label !== false) {
      const info = m.anchor ? null : visibleInfo(fig, anchorPts);
      // парная мышца в фас и со спины: якорь берётся на той половине тела, куда уходит подпись
      const alts = !m.anchor && altItems.length > 1 ? altItems.map(its => visibleInfo(fig, its)) : null;
      // мышца почти целиком закрыта (меньше HIDDEN_AREA px2): рисуем её пунктиром поверх, выноска к ней
      const hidden = !!info && info.vis.length * 6.25 < HIDDEN_AREA;
      if (hidden) for (const it of allItems) it.hidden = true;
      labels.push({ segNames: anchorPts.flatMap(it => it.segNames), ci: anchorPts[0].ci, fixedAnchor: m.anchor ? resolve(m.anchor) : null, info, alts, hidden, text: m.label || NAMES[m.name], type: m.type, at: m.labelAt, prefSide: m.labelSide });
    }
  }
  // якоря: сначала мышцы с маленькой видимой зоной, остальные разносятся не ближе 18 px друг от друга
  const taken = labels.filter(l => l.fixedAnchor).map(l => l.fixedAnchor);
  for (const l of labels) if (l.fixedAnchor) l.anchor = l.fixedAnchor;
  const order = labels.filter(l => !l.fixedAnchor).sort((a, b) => (a.hidden ? a.info.all : a.info.vis).length - (b.hidden ? b.info.all : b.info.vis).length);
  for (const l of order) {
    const pts = l.hidden ? l.info.all : l.info.vis;
    if (l.alts) {
      l.anchors = l.alts.map(a => pickAnchor(a.vis.length ? a.vis : a.all, taken) || a.fallback);
      l.anchors.sort((a, b) => a[0] - b[0]);
      taken.push(...l.anchors);
      l.anchor = l.anchors[0];
      continue;
    }
    l.anchor = pickAnchor(pts, taken) || l.info.fallback;
    taken.push(l.anchor);
  }

  // наружная сторона мышцы: от оси ближайшего сегмента к якорю. Выноска, уходящая сквозь конечность
  // на другую сторону (икроножная вперёд через голень), дороже
  for (const l of labels) {
    if (!l.anchor || !l.segNames || !l.segNames.every(n => /^(upper|fore|thigh|shin)_/.test(n))) continue;
    let best = null;
    for (const n of l.segNames) {
      const sg = fig.segs[n];
      if (!sg || !sg.len || sg.kind === 'frame') continue;
      const a = fig.xf(sg.A), b = fig.xf(sg.B), ab = sub(b, a), t = clamp(((l.anchor[0] - a[0]) * ab[0] + (l.anchor[1] - a[1]) * ab[1]) / (len2(ab) ** 2 || 1), 0, 1);
      const off = sub(l.anchor, add(a, mul(ab, t))), d = len2(off);
      if (!best || d < best.d) best = { d, off };
    }
    if (best && best.d > 4) l.outward = { v: mul(best.off, 1 / best.d), w: clamp(best.d / 12, 0, 1) };
  }

  // --- снаряды
  const equipBack = [], equipFront = [], equipBefore = {};
  const boxes = [];
  const clusterOfPoint = p => {
    if (typeof p !== 'string') return null;
    const m = p.match(/^(hand|wrist|fingers|elbow)_(l|r|near|far)$/);
    if (!m) return null;
    let sd = m[2];
    if (sd === 'near') sd = fig.near || 'l';
    if (sd === 'far') sd = fig.far || 'r';
    const idx = fig.clusters.findIndex(c => c.segs.includes('hand_' + sd));
    return idx;
  };
  for (const e of spec.equipment || []) {
    const r = drawEquip(e, ctx);
    if (r.box) boxes.push(r.box);
    if (r.handSvg) {
      // втулка грифа: под ближней рукой, если кулак на грифе, иначе поверх тела
      const nh = view === 'side' ? fig.near : 'l';
      const ci = fig.clusters.findIndex(c => c.segs.includes('hand_' + nh));
      if (ci >= 0 && len2(sub(fig.world('hand_' + nh), r.handAt)) < 30 * fig.S) (equipBefore[ci] = equipBefore[ci] || []).push(r.handSvg);
      else equipFront.push(r.handSvg);
    }
    let layer = e.layer || r.layer || EQUIP_LAYER[e.type] || 'back';
    if (layer === 'hand') {
      const ci = clusterOfPoint(e.at || e.from);
      if (ci != null && ci >= 0) { (equipBefore[ci] = equipBefore[ci] || []).push(r.svg); continue; }
      layer = 'front';
    }
    (layer === 'front' ? equipFront : equipBack).push(r.svg);
  }

  // --- рисование фигуры
  function drawFigure(F, opt = {}) {
    let out = `<g transform="${F.xf.transform}"${opt.opacity ? ` opacity="${opt.opacity}"` : ''}>`;
    const hiddenOut = [];
    F.clusters.forEach((c, ci) => {
      if (opt.before && opt.before[ci]) out += `</g>${opt.before[ci].join('')}<g transform="${F.xf.transform}">`;
      const far = F.view === 'side' && c.far;
      // фантом (другая фаза движения): голубой пунктир, чтобы не путать с дальними конечностями (серые, сплошные)
      const lineC = opt.ghost ? COL.ghostLine : far ? COL.farLine : COL.line, fillC = opt.ghost ? COL.ghostBody : far ? COL.farBody : COL.body;
      const paths = c.segs.map(n => outlineOf(F, n));
      out += `<g>`;
      out += paths.map(d => opt.ghost
        ? `<path d="${d}" fill="none" stroke="${lineC}" stroke-width="${SW * 1.6}" stroke-linejoin="round" stroke-dasharray="8 6"/>`
        : `<path d="${d}" fill="${lineC}" stroke="${lineC}" stroke-width="${SW * 2}" stroke-linejoin="round"${opt.dash ? ' stroke-dasharray="7 6"' : ''}/>`).join('');
      out += paths.map(d => `<path d="${d}" fill="${fillC}"/>`).join('');
      if (!opt.ghost) {
        // мышцы: клип по своим сегментам и поверх по итоговому контуру кластера (пересечение)
        const kid = uid('k');
        defs.push(`<clipPath id="${kid}">${paths.map(d => `<path d="${d}"/>`).join('')}</clipPath>`);
        out += `<g clip-path="url(#${kid})">`;
        for (const it of perCluster[ci].slice().sort((a, b) => (a.sh.top ? 1 : 0) - (b.sh.top ? 1 : 0))) {
          const cid = uid('c');
          const clipNames = [...new Set(it.segNames.map(n => (F.segs.trunk && F.segs.trunk.parts.includes(n) ? 'trunk' : n)))];
          defs.push(`<clipPath id="${cid}">${clipNames.map(n => `<path d="${outlineOf(F, n)}"/>`).join('')}</clipPath>`);
          it.cid = cid;
          // маска перекрытий: части тела, нарисованные в этом слое позже своих сегментов мышцы, закрывают её
          // (таз над верхом бедра в фас, голень над концом бедра у колена, предплечье над локтем)
          const occ = occludersOf(F, c, clipNames, it);
          const mid = occ.length ? uid('m') : null;
          if (mid) defs.push(`<mask id="${mid}" maskUnits="userSpaceOnUse" x="-3000" y="-3000" width="6000" height="6000"><rect x="-3000" y="-3000" width="6000" height="6000" fill="#fff"/>${occ.map(d => `<path d="${d}" fill="#000"/>`).join('')}</mask>`);
          const mattr = mid ? ` mask="url(#${mid})"` : '';
          const col = it.m.type === 'stretch' ? COL.stretch : COL.work;
          let op = it.m.type === 'stretch' ? 0.6 : 0.8;
          if (it.far) op *= 0.55;
          // глубокие мышцы: светлее и с пунктирным контуром
          const deep = !!it.sh.deep;
          if (deep) op *= 0.7;
          const dash = deep ? ' stroke-dasharray="5 3.5"' : '';
          const strokeC = it.m.type === 'stretch' ? '#E65100' : '#B71C1C';
          const sop = it.far ? 0.35 : deep ? 0.95 : 0.7;
          if (it.sh.top) out += `<path d="${smoothClosed(it.sh.pts)}" clip-path="url(#${cid})"${mattr} fill="${fillC}"/>`;
          out += `<path d="${smoothClosed(it.sh.pts)}" clip-path="url(#${cid})"${mattr} fill="${col}" fill-opacity="${fx(op)}" stroke="${strokeC}" stroke-opacity="${sop}" stroke-width="${deep ? 1.7 : 1.3}"${dash}/>`;
          if (it.hidden) hiddenOut.push(`<path d="${smoothClosed(it.sh.pts)}" clip-path="url(#${cid})"${mattr} fill="${col}" fill-opacity="0.22" stroke="${strokeC}" stroke-width="1.8" stroke-dasharray="5 3.5"/>`);
        }
        out += `</g>`;
        // складки и детали
        for (const cr of F.creases) if (c.segs.includes(cr.seg)) {
          const s = F.segs[cr.seg];
          let side = cr.side;
          if (side === 'med') side = 'post';
          out += `<path d="${segEdge(s, side, cr.t0, cr.t1)}" fill="none" stroke="${lineC}" stroke-width="2.2" stroke-linecap="round"/>`;
        }
        for (const dt of F.details) if (c.segs.includes(dt.seg)) {
          const s = F.segs[dt.seg];
          const p = framePt(s, dt.u, dt.v);
          const a = s.ang + 90;
          if (dt.kind === 'ear') out += `<ellipse cx="${fx(p[0])}" cy="${fx(p[1])}" rx="${fx(5 * s.S)}" ry="${fx(8.5 * s.S)}" transform="rotate(${fx(a - 12)} ${fp(p)})" fill="${fillC}" stroke="${lineC}" stroke-width="2"/>`;
          if (dt.kind === 'thumb') { const q = [[3, -4], [12, -3], [20, -2.5], [25, -4.5]].map(([u, v]) => framePt(s, u, v)); out += `<path d="${smoothOpen(q)}" fill="none" stroke="${lineC}" stroke-width="1.8" stroke-linecap="round"/>`; }
          if (dt.kind === 'earF') out += `<ellipse cx="${fx(p[0])}" cy="${fx(p[1])}" rx="${fx(4 * s.S)}" ry="${fx(8 * s.S)}" transform="rotate(${fx(a)} ${fp(p)})" fill="${fillC}" stroke="${lineC}" stroke-width="2"/>`;
        }
      }
      out += `</g>`;
    });
    // закрытые мышцы: пунктир поверх всех слоёв
    if (hiddenOut.length) out += `<g>${hiddenOut.join('')}</g>`;
    return out + `</g>`;
  }

  let body = '';
  let ghostFig = null;
  if (spec.ghost) {
    const gs = JSON.parse(JSON.stringify(spec));
    gs.pose = Object.assign({}, spec.pose, spec.ghost.pose || spec.ghost);
    for (const s of ['l', 'r', 'both']) if ((spec.ghost.pose || spec.ghost)[s]) gs.pose[s] = Object.assign({}, (spec.pose || {})[s], (spec.ghost.pose || spec.ghost)[s]);
    const g = buildFigure(gs);
    ghostFig = g;
    body += drawFigure(g, { ghost: true, opacity: spec.ghost.opacity ?? 0.9 });
    CURRENT = fig;
  }
  body += drawFigure(fig, { before: equipBefore });

  // --- стрелки
  let arrows = '';
  const arrowLabels = [], arrowBoxes = [];
  for (const a of spec.arrows || []) {
    let d, lp = a.labelAt ? resolve(a.labelAt) : null, anchor = 'middle', bpts;
    if (a.arc) {
      const c = resolve(a.arc.center), r = a.arc.r ?? 60;
      const s0 = a.arc.start ?? 0, s1 = a.arc.end ?? 90;
      const p0 = add(c, mul(dirv(s0), r)), p1 = add(c, mul(dirv(s1), r));
      const large = Math.abs(s1 - s0) > 180 ? 1 : 0, sweep = s1 > s0 ? 1 : 0;
      d = `M${fp(p0)} A${fx(r)},${fx(r)} 0 ${large} ${sweep} ${fp(p1)}`;
      bpts = [];
      for (let i = 0; i <= 8; i++) bpts.push(add(c, mul(dirv(lerp(s0, s1, i / 8)), r)));
      if (!lp) {
        const o = dirv((s0 + s1) / 2);
        lp = add(c, mul(o, r + 16));
        if (o[0] > 0.35) anchor = 'start'; else if (o[0] < -0.35) anchor = 'end'; else lp = add(lp, [0, o[1] < 0 ? -6 : 10]);
      }
    } else {
      const p0 = resolve(a.from), p1 = resolve(a.to);
      const v = sub(p1, p0), L_ = len2(v), nrm = [-v[1] / L_, v[0] / L_];
      const bend = a.bend || 0;
      let mid;
      if (bend) {
        const cp = add(add(p0, mul(v, 0.5)), mul(nrm, bend * L_));
        d = `M${fp(p0)} Q${fp(cp)} ${fp(p1)}`;
        mid = add(add(p0, mul(v, 0.5)), mul(nrm, bend * L_ * 0.5));
        bpts = [p0, p1, mid];
      } else { d = `M${fp(p0)} L${fp(p1)}`; mid = add(p0, mul(v, 0.5)); bpts = [p0, p1]; }
      if (!lp) {
        const off = a.labelOffset ?? 18;
        if (Math.abs(nrm[0]) > 0.3) { const side = a.labelSide === 'left' ? -1 : 1; lp = add(mid, [side * off, 0]); anchor = side > 0 ? 'start' : 'end'; }
        else lp = add(mid, [0, (a.labelSide === 'below' ? 1 : -1) * (off + 4)]);
      }
    }
    const markers = ` marker-end="url(#ah)"${a.both ? ' marker-start="url(#ahs)"' : ''}`;
    arrows += `<path d="${d}" fill="none" stroke="${COL.arrow}" stroke-width="4.5" stroke-linecap="round"${markers}${a.dash ? ' stroke-dasharray="9 7"' : ''}/>`;
    arrowBoxes.push(boxOf(bpts, 10));
    if (a.label) {
      const w = textW(a.label, 17);
      const x0 = anchor === 'start' ? lp[0] : anchor === 'end' ? lp[0] - w : lp[0] - w / 2;
      arrowBoxes.push({ x0, y0: lp[1] - 11, x1: x0 + w, y1: lp[1] + 11 });
      arrowLabels.push(`<text x="${fx(lp[0])}" y="${fx(lp[1])}" font-family="${FONT}" font-size="17" fill="${COL.arrow}" text-anchor="${a.anchor || anchor}" dominant-baseline="middle">${esc(a.label)}</text>`);
    }
  }

  // --- подписи мышц: выносные линии к свободному краю, без наложений и пересечений
  const figPts = figureOutlinePts(fig);
  const fb = boxOf(figPts);
  const polys = segPolys(fig), gpolys = ghostFig ? segPolys(ghostFig) : [];
  // растр тела (шаг 2 px): бит k = кластер k, бит 7 = фантом; ускоряет проверки выносок
  const RS = 2, RW = Math.ceil(CW / RS), RH = Math.ceil(CH / RS), raster = new Uint8Array(RW * RH);
  const rasterPoly = (pl, bit) => {
    if (!pl.length) return;
    const b = boxOf(pl);
    for (let j = Math.max(0, Math.floor(b.y0 / RS)); j <= Math.min(RH - 1, Math.ceil(b.y1 / RS)); j++)
      for (let i = Math.max(0, Math.floor(b.x0 / RS)); i <= Math.min(RW - 1, Math.ceil(b.x1 / RS)); i++)
        if (pip([(i + 0.5) * RS, (j + 0.5) * RS], pl)) raster[j * RW + i] |= bit;
  };
  const clusterPolys = fig.clusters.map(c => expandSegs(fig, c.segs).map(n => segPoly(fig, n)));
  clusterPolys.forEach((ps, k) => ps.forEach(pl => rasterPoly(pl, 1 << Math.min(k, 6))));
  gpolys.forEach(pl => rasterPoly(pl, 128));
  const cellAt = q => { const i = Math.floor(q[0] / RS), j = Math.floor(q[1] / RS); return i < 0 || j < 0 || i >= RW || j >= RH ? 0 : raster[j * RW + i]; };
  const inBody = pt => (cellAt(pt) & 127) !== 0;
  const inGhost = pt => (cellAt(pt) & 128) !== 0;
  const obst = [...boxes, ...arrowBoxes];
  const hitBox = (b, x0, y0, x1, y1) => b.x0 < x1 && b.x1 > x0 && b.y0 < y1 && b.y1 > y0;
  const inBox = (q, b, pad = 2) => q[0] > b.x0 - pad && q[0] < b.x1 + pad && q[1] > b.y0 - pad && q[1] < b.y1 + pad;
  const topLimit = spec.hint ? 128 : 92;
  const types = new Set(mlist.map(m => m.type));
  const hasLegend = !!(spec.legend ?? (types.size > 1));
  const bottomLimit = hasLegend ? CH - 36 : CH - 8;
  const SZ = 17, gap = 26;
  // выноска не должна идти по телу дольше этого (px); в фас и со спины допускается перейти через руку
  const MAX_BODY_RUN = view === 'side' ? 26 : 40;
  const placed = [];
  const textBox = (x, y, at, w) => { const x0 = at === 'end' ? x - w : at === 'start' ? x : x - w / 2; return [x0, y - 11, x0 + w, y + 11]; };
  const leaderEnd = (x, y, at, side) => at === 'end' ? [x + 6, y] : at === 'start' ? [x - 6, y] : [x, side === 'top' || side === 'freetop' ? y + 11 : y - 12];
  // сколько выноска идёт по чужим частям тела: выход из своей части (кластера мышцы) не штрафуется,
  // а заход на другие кластеры поверх неё или повторный заход на тело после выхода считается
  const bodyRun = (A, E, lb) => {
    const L_ = len2(sub(E, A)), n = Math.max(10, Math.ceil(L_ / 3));
    const ownBit = 1 << Math.min(lb.ci ?? 0, 6);
    let otherMask = 0, farMask = 0;
    fig.clusters.forEach((c, k) => { if (k !== lb.ci && (!lb.hidden || k < lb.ci)) { otherMask |= 1 << Math.min(k, 6); if (c.far) farMask |= 1 << Math.min(k, 6); } });
    let run = 0, first = 0, exited = false;
    for (let i = 1; i <= n; i++) {
      const q = add(A, mul(sub(E, A), i / n));
      if (len2(sub(q, A)) <= 8) continue;
      const cq = cellAt(q), inOwn = (cq & ownBit) !== 0, inOther = (cq & otherMask & ~ownBit) !== 0;
      if (!inOwn && !inOther) { exited = true; continue; }
      // дальние (светлые) конечности мешают выноске вдвое меньше
      const w = inOther && !inOwn && (cq & otherMask & ~farMask) === 0 ? 0.5 : 1;
      if (exited || inOther) run += w * L_ / n; else first += L_ / n;
    }
    // выход из своей части тела допустим, но длинный путь по ней (через чужие мышцы) тоже плох
    return run + Math.max(0, first - 22) * 1.5;
  };
  const zoneKey = q => Math.round(q[0] / 2.5) + ',' + Math.round(q[1] / 2.5);
  for (const l of labels) { l.zone = new Set(); if (l.info) for (const q of (l.hidden ? [] : l.info.vis)) l.zone.add(zoneKey(q)); if (l.alts) for (const a of l.alts) for (const q of a.vis) l.zone.add(zoneKey(q)); }
  const muscleRun = (A, E, lb) => {
    const L_ = len2(sub(E, A)), n = Math.max(10, Math.ceil(L_ / 2.5));
    let run = 0;
    for (let i = 1; i <= n; i++) {
      const q = add(A, mul(sub(E, A), i / n));
      if (len2(sub(q, A)) <= 6) continue;
      const k = zoneKey(q);
      if (labels.some(o => o !== lb && o.zone && o.zone.has(k) && !lb.zone.has(k))) run += L_ / n;
    }
    return run;
  };
  let curObst = obst;
  const leaderHitsObst = (A, E) => curObst.some(b => { for (let i = 1; i <= 24; i++) if (inBox(add(A, mul(sub(E, A), i / 24)), b)) return true; return false; });
  const candCost = (lb, s, x, y, at, w) => {
    const A = lb.anchor;
    const [tx0, ty0, tx1, ty1] = textBox(x, y, at, w);
    const fits = tx0 >= 10 && tx1 <= CW - 10 && ty0 >= topLimit && ty1 <= bottomLimit;
    if (!fits) return null;
    const E = leaderEnd(x, y, at, s);
    let cost = len2(sub(E, A)) + (s === 'top' || s === 'bottom' ? 40 : 0);
    if (lb.outward && view === 'side') { const dv = sub(E, A), dl = len2(dv) || 1, dot = (dv[0] * lb.outward.v[0] + dv[1] * lb.outward.v[1]) / dl; if (dot < 0) cost += -dot * 70 * lb.outward.w; }
    const run = bodyRun(A, E, lb);
    cost += run * 3 + (run > MAX_BODY_RUN ? 1500 + run * 10 : 0);
    // выноска поверх чужих закрашенных мышц читается плохо
    const mr = muscleRun(A, E, lb);
    cost += view === 'side' ? mr * 8 + (mr > 3 ? 120 : 0) + (mr > 30 ? 600 : 0) : mr * 4 + (mr > 30 ? 600 : 0);
    if (leaderHitsObst(A, E)) cost += 1500;
    // пересечение уже поставленных выносок и проход рядом с чужими якорями
    const segHitsRect = (P, Q, r) => { for (let i = 0; i <= 20; i++) { const q = add(P, mul(sub(Q, P), i / 20)); if (q[0] > r[0] - 3 && q[0] < r[2] + 3 && q[1] > r[1] - 2 && q[1] < r[3] + 2) return true; } return false; };
    for (const p of placed) {
      if (p === lb) continue;
      const pE = leaderEnd(p.x, p.y, p.anchorT, p.side);
      if (segX(A, E, p.anchor, pE)) cost += 2500;
      // выноска через чужую подпись или чужая выноска через эту подпись
      if (segHitsRect(A, E, textBox(p.x, p.y, p.anchorT, p.w))) cost += 600;
      if (segHitsRect(p.anchor, pE, [tx0, ty0, tx1, ty1])) cost += 600;
    }
    for (const o of labels) if (o !== lb && o.anchor) {
      const t = clamp(((o.anchor[0] - A[0]) * (E[0] - A[0]) + (o.anchor[1] - A[1]) * (E[1] - A[1])) / (len2(sub(E, A)) ** 2 || 1), 0, 1);
      if (t > 0.02 && len2(sub(o.anchor, add(A, mul(sub(E, A), t)))) < 9) cost += 300;
    }
    for (const q of [[tx0, ty0], [tx1, ty0], [tx0, ty1], [tx1, ty1], [(tx0 + tx1) / 2, y]]) { if (inBody(q)) cost += 400; else if (inGhost(q)) cost += 15; }
    for (const b of curObst) if (hitBox(b, tx0, ty0, tx1, ty1)) cost += 400;
    return cost;
  };
  // три прохода: на втором и третьем каждая подпись переставляется с учётом всех остальных.
  // Раскладка пробуется в нескольких порядках подписей, берётся с наименьшей суммарной ценой.
  const runLayout = order => { placed.length = 0; for (let pass = 0; pass < 3; pass++) for (const lb of order) {
    const w = textW(lb.text, SZ);
    const pi = placed.indexOf(lb);
    if (pi >= 0) placed.splice(pi, 1);
    if (lb.at) { const p = resolve(lb.at); placed.push(Object.assign(lb, { x: p[0], y: p[1], anchorT: lb.anchorT || 'start', side: 'fixed', w })); continue; }
    curObst = [...obst, ...placed.filter(p => p.side && p.side.startsWith('free')).map(p => { const [a0, b0, a1, b1] = textBox(p.x, p.y, p.anchorT, p.w); return { x0: a0 - 6, y0: b0 - 2, x1: a1 + 6, y1: b1 + 2 }; })];
    const cand = [];
    const sides = lb.prefSide ? [lb.prefSide] : ['left', 'right', 'top', 'bottom'];
    for (const s of sides) {
      if (lb.anchors) lb.anchor = s === 'right' ? lb.anchors[lb.anchors.length - 1] : lb.anchors[0];
      const A = lb.anchor;
      // колонки сбоку пробуются на разной высоте, сверху и снизу со сдвигом по x: так выноска обходит тело и снаряды
      const offs = [0, -30, 30, -60, 60, -95, 95, -130, 130];
      for (const o of offs) {
        let x, y, at;
        if (s === 'left' || s === 'right') {
          y = A[1] + o;
          const bl = s === 'left'
            ? curObst.filter(b => b.x0 < A[0] - 10 && b.x1 > fb.x0 - 40 && b.y0 - 12 <= y && b.y1 + 12 >= y).map(b => b.x0)
            : curObst.filter(b => b.x1 > A[0] + 10 && b.x0 < fb.x1 + 40 && b.y0 - 12 <= y && b.y1 + 12 >= y).map(b => b.x1);
          x = s === 'left' ? Math.min(fb.x0, A[0] - 20, ...bl) - gap : Math.max(fb.x1, A[0] + 20, ...bl) + gap;
          at = s === 'left' ? 'end' : 'start';
        } else {
          x = clamp(A[0] + o * 1.5, 12 + w / 2, CW - 12 - w / 2);
          if (s === 'top') { const bl = curObst.filter(b => b.x0 < x + w / 2 && b.x1 > x - w / 2 && b.y0 < A[1]).map(b => b.y0); y = Math.min(fb.y0, ...bl) - 22; }
          else { const bl = curObst.filter(b => b.x0 < x + w / 2 && b.x1 > x - w / 2 && b.y1 > A[1]).map(b => b.y1); y = Math.max(fb.y1, ...bl) + 26; }
          at = 'middle';
        }
        const c = candCost(lb, s, x, y, at, w);
        if (c != null) cand.push({ s, x, y, at, A, cost: c + Math.abs(o) * 1.2 });
      }
    }
    // свободное место рядом с якорем: короткая выноска, текст целиком на пустом месте
    const A = lb.anchor;
    if (!lb.prefSide && view === 'side') {
      for (const dist of [40, 60, 85, 115]) for (let k = 0; k < 12; k++) {
        const th = k * 30 + 15, dv = dirv(th), P0 = add(A, mul(dv, dist));
        const at = dv[0] > 0.25 ? 'start' : dv[0] < -0.25 ? 'end' : 'middle';
        const x = at === 'start' ? P0[0] + 6 : at === 'end' ? P0[0] - 6 : P0[0];
        const y = at === 'middle' ? P0[1] + (dv[1] < 0 ? -11 : 12) : P0[1];
        const side = at === 'middle' ? (dv[1] < 0 ? 'top' : 'bottom') : 'free';
        const [tx0, ty0, tx1, ty1] = textBox(x, y, at, w);
        if (tx0 < 10 || tx1 > CW - 10 || ty0 < topLimit || ty1 > bottomLimit) continue;
        let bad = false;
        const nx = Math.ceil((tx1 - tx0 + 8) / 7);
        for (let i = 0; i <= nx && !bad; i++) for (let j = 0; j <= 3 && !bad; j++) { const q = [lerp(tx0 - 4, tx1 + 4, i / nx), lerp(ty0 - 4, ty1 + 4, j / 3)]; if (inBody(q) || inGhost(q)) bad = true; }
        if (bad || curObst.some(b => hitBox(b, tx0 - 4, ty0 - 3, tx1 + 4, ty1 + 3))) continue;
        if (placed.some(p => { const [a0, b0, a1, b1] = textBox(p.x, p.y, p.anchorT, p.w); return a0 < tx1 + 8 && a1 > tx0 - 8 && b0 < ty1 + 4 && b1 > ty0 - 4; })) continue;
        const c = candCost(lb, side === 'free' ? 'free' : side, x, y, at, w);
        if (c != null) cand.push({ s: side === 'free' ? 'free' : 'free' + side, x, y, at, A, cost: c + 25 });
      }
    }
    cand.sort((a, b) => a.cost - b.cost);
    if (process.env.FIG_DEBUG) console.error(lb.text, JSON.stringify(lb.anchor.map(Math.round)), cand.slice(0, process.env.FIG_DEBUG_N ? +process.env.FIG_DEBUG_N : 6).map(c => c.s + "(" + Math.round(c.x) + ")" + '@' + Math.round(c.y) + ':' + Math.round(c.cost)).join(' '));
    const c = cand[0] || { s: lb.prefSide || 'right', x: fb.x1 + gap, y: A[1], at: 'start' };
    if (c.A) lb.anchor = c.A;
    lb.cost = c.cost || 0;
    placed.push(Object.assign(lb, { x: c.x, y: c.y, anchorT: c.at, side: c.s, w }));
  }
    return labels.reduce((t, l) => t + (l.cost || 0), 0);
  };
  const orders = [];
  const perm = (arr, pre = []) => { if (!arr.length) { orders.push(pre); return; } arr.forEach((x, i) => perm([...arr.slice(0, i), ...arr.slice(i + 1)], [...pre, x])); };
  if (labels.length <= 4) perm(labels);
  else {
    const by = f => labels.slice().sort((a, b) => f(a) - f(b));
    orders.push(labels, labels.slice().reverse(), by(l => l.anchor[1]), by(l => -l.anchor[1]), by(l => l.anchor[0]), by(l => -l.anchor[0]), by(l => (l.zone ? l.zone.size : 0)));
  }
  let bestL = null;
  for (const o of orders) {
    const tot = runLayout(o);
    if (!bestL || tot < bestL.tot) bestL = { tot, snap: labels.map(l => ({ x: l.x, y: l.y, anchorT: l.anchorT, side: l.side, anchor: l.anchor, w: l.w })) };
  }
  if (bestL) { labels.forEach((l, i) => Object.assign(l, bestL.snap[i])); placed.length = 0; placed.push(...labels); }
  // раздвижка: порядок подписей на стороне совпадает с порядком якорей, тогда выноски не перекрещиваются
  const spreadSide = s => {
    const g = placed.filter(p => p.side === s);
    if (s === 'left' || s === 'right') {
      if (g.length > 1) {
        const xs = g.map(p => p.x); const X = s === 'left' ? Math.min(...xs) : Math.max(...xs);
        if (g.every(p => (s === 'left' ? X - p.w >= 10 : X + p.w <= CW - 10))) g.forEach(p => { p.x = X; });
      }
      const ys = g.map(p => p.y).sort((a, b) => a - b);
      g.sort((a, b) => a.anchor[1] - b.anchor[1] || a.anchor[0] - b.anchor[0]).forEach((p, i) => { p.y = ys[i]; });
      for (let it = 0; it < 60; it++) {
        for (let i = 1; i < g.length; i++) if (g[i].y - g[i - 1].y < 26) { const m = (g[i].y + g[i - 1].y) / 2; g[i - 1].y = m - 13; g[i].y = m + 13; }
        for (const p of g) p.y = clamp(p.y, topLimit + 11, bottomLimit - 11);
      }
    } else {
      if (g.length > 1) { const ys = g.map(p => p.y); const Y = s === 'top' ? Math.min(...ys) : Math.max(...ys); g.forEach(p => { p.y = Y; }); }
      const xs = g.map(p => p.x).sort((a, b) => a - b);
      g.sort((a, b) => a.anchor[0] - b.anchor[0]).forEach((p, i) => { p.x = xs[i]; });
      for (let it = 0; it < 60; it++) {
        for (let i = 1; i < g.length; i++) {
          const need = (g[i].w + g[i - 1].w) / 2 + 24;
          if (g[i].x - g[i - 1].x < need) { const m = (g[i].x + g[i - 1].x) / 2; g[i - 1].x = m - need / 2; g[i].x = m + need / 2; }
        }
        for (const p of g) p.x = clamp(p.x, 12 + p.w / 2, CW - 12 - p.w / 2);
      }
    }
  };
  for (const s of ['left', 'right', 'top', 'bottom']) spreadSide(s);
  // проверка пересечений выносок: на одной стороне меняем подписи местами
  const leaderOf = p => [p.anchor, leaderEnd(p.x, p.y, p.anchorT, p.side)];
  for (let it = 0; it < 20; it++) {
    let fixed = false;
    for (let i = 0; i < placed.length; i++) for (let j = i + 1; j < placed.length; j++) {
      const a = placed[i], b = placed[j];
      if (a.side !== b.side || !['left', 'right', 'top', 'bottom'].includes(a.side)) continue;
      const [a0, a1] = leaderOf(a), [b0, b1] = leaderOf(b);
      if (!segX(a0, a1, b0, b1)) continue;
      if (a.side === 'left' || a.side === 'right') { const t = a.y; a.y = b.y; b.y = t; } else { const t = a.x; a.x = b.x; b.x = t; }
      fixed = true;
    }
    if (!fixed) break;
  }
  let labelSvg = '';
  for (const p of placed) {
    const col = p.type === 'stretch' ? COL.stretchText : COL.workText;
    const [ex, ey] = leaderEnd(p.x, p.y, p.anchorT, p.side);
    labelSvg += `<line x1="${fx(p.anchor[0])}" y1="${fx(p.anchor[1])}" x2="${fx(ex)}" y2="${fx(ey)}" stroke="${col}" stroke-width="1.6"/>`;
    labelSvg += `<circle cx="${fx(p.anchor[0])}" cy="${fx(p.anchor[1])}" r="4" fill="${col}" stroke="#fff" stroke-width="1.5"/>`;
    labelSvg += `<text x="${fx(p.x)}" y="${fx(p.y)}" font-family="${FONT}" font-size="${SZ}" fill="${col}" text-anchor="${p.anchorT}" dominant-baseline="middle">${esc(p.text)}</text>`;
  }

  // --- заметки, легенда
  let notes = '';
  for (const n of spec.notes || []) {
    const p = resolve(n.at);
    notes += `<text x="${fx(p[0])}" y="${fx(p[1])}" font-family="${FONT}" font-size="${n.size || 16}" fill="${n.color || COL.note}" text-anchor="${n.anchor || 'start'}"${n.italic ? ' font-style="italic"' : ''}>${esc(n.text)}</text>`;
  }
  let legend = '';
  if (hasLegend) {
    let x = 40;
    const y = CH - 24;
    for (const [t, txt] of [['work', 'работает'], ['stretch', 'растягивается']]) {
      if (!types.has(t) && spec.legend !== 'all') continue;
      const col = t === 'work' ? COL.work : COL.stretch, op = t === 'work' ? 0.8 : 0.6;
      legend += `<rect x="${x}" y="${y - 9}" width="18" height="18" rx="4" fill="${col}" fill-opacity="${op}"/><text x="${x + 26}" y="${y}" font-family="${FONT}" font-size="15" fill="${COL.hint}" dominant-baseline="middle">${txt}</text>`;
      x += 26 + textW(txt, 15) + 28;
    }
  }

  // --- заголовок
  let head = '';
  if (spec.title) head += `<text x="40" y="56" font-family="${FONT}" font-size="28" font-weight="bold" fill="${COL.title}">${esc(spec.title)}</text>`;
  if (spec.hint) wrap(spec.hint, 18, 820).slice(0, 2).forEach((ln, i) => { head += `<text x="40" y="${90 + i * 24}" font-family="${FONT}" font-size="18" fill="${COL.hint}">${esc(ln)}</text>`; });

  const floorSvg = spec.floor != null && spec.showFloor !== false && !(spec.equipment || []).some(e => e.type === 'mat' || e.type === 'floor')
    ? `<line x1="50" y1="${fx(spec.floor)}" x2="850" y2="${fx(spec.floor)}" stroke="${COL.floor}" stroke-width="3" stroke-linecap="round"/>` : '';

  const markerDefs = `<marker id="ah" viewBox="0 0 10 10" refX="7" refY="5" markerWidth="4.2" markerHeight="4.2" orient="auto-start-reverse" markerUnits="strokeWidth"><path d="M0,0.5 L10,5 L0,9.5 Z" fill="${COL.arrow}"/></marker>` +
    `<marker id="ahs" viewBox="0 0 10 10" refX="7" refY="5" markerWidth="4.2" markerHeight="4.2" orient="auto-start-reverse" markerUnits="strokeWidth"><path d="M0,0.5 L10,5 L0,9.5 Z" fill="${COL.arrow}"/></marker>`;
  // вертикальная центровка: сцена (пол, снаряды, фигура, стрелки, подписи) ставится посередине между
  // заголовком и низом холста (легендой), чтобы под заголовком не оставалось 150-200 px пустоты
  let dy = 0;
  if (spec.center !== false) {
    const bs = [fb, ...boxes, ...arrowBoxes, ...placed.map(p => { const [a0, b0, a1, b1] = textBox(p.x, p.y, p.anchorT, p.w); return { x0: a0, y0: b0, x1: a1, y1: b1 }; })];
    if (floorSvg) bs.push({ x0: 50, y0: spec.floor - 2, x1: 850, y1: spec.floor + 2 });
    for (const n of spec.notes || []) { const p = resolve(n.at); bs.push({ x0: p[0], y0: p[1] - 14, x1: p[0] + 1, y1: p[1] + 4 }); }
    const top = Math.min(...bs.map(b => b.y0)), bot = Math.max(...bs.map(b => b.y1));
    const above = top - (topLimit - 8), below = bottomLimit - bot;
    if (Math.abs(above - below) > 30) dy = Math.round(clamp((below - above) / 2, -above, below));
  }
  const scene = (floorSvg + equipBack.join('') + '\n' + body + '\n' + equipFront.join('') + '\n' + arrows + arrowLabels.join('') + '\n' + labelSvg + notes);
  CURRENT = null;
  return `<svg xmlns="http://www.w3.org/2000/svg" width="${CW}" height="${CH}" viewBox="0 0 ${CW} ${CH}" font-family="${FONT}">\n` +
    `<rect width="${CW}" height="${CH}" fill="#ffffff"/>\n<defs>${markerDefs}${defs.join('')}</defs>\n` +
    head + '\n' + (dy ? `<g transform="translate(0,${dy})">${scene}</g>` : scene) + legend + '\n</svg>\n';
}

module.exports = { _buildFigure: buildFigure, _outlinePts: (fig, n) => pathPts(outlineOf(fig, n)).map(p => fig.xf(p)), drawExercise, MUSCLE_NAMES: NAMES, ANKLE_HEIGHT: ANKLE_H, COLORS: COL };
