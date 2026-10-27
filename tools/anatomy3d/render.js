// Рендер сцены из export_pose.py: кости, мышцы по тирам, штанга, стрелки движения. PNG через Playwright + three.js.
// Запуск: node tools/anatomy3d/render.js <scene.json> <out.png> [view.json]
const { chromium } = require(require('child_process').execSync('npm root -g').toString().trim() + '/playwright');
const fs = require('fs');
const path = require('path');
const [, , scenePath, outPath, viewPath] = process.argv;
const view = viewPath ? JSON.parse(fs.readFileSync(viewPath, 'utf8')) : {};
const three = fs.readFileSync(path.join(__dirname, 'vendor', 'three.module.js'));

const page = `<!doctype html><html><head><meta charset="utf-8"><style>
html,body{margin:0;width:${view.w || 1080}px;height:${view.h || 1350}px;overflow:hidden;background:#24282c}
#stage{background:radial-gradient(ellipse at 50% 42%, #767d83 0%, #50565c 50%, #2e3236 100%)}
canvas{display:block}
.legend{font:600 25px/1.35 Inter,sans-serif;color:#eef0f2;padding:30px 48px 36px}
.legend h2{margin:0 0 12px;font:800 34px/1.2 Inter,sans-serif}
.row{display:flex;align-items:flex-start;gap:14px;margin-top:10px}.sw{width:24px;height:24px;border-radius:6px;margin-top:4px;flex:none}
.row b{display:block;font-weight:800}.row span{font-weight:500;color:#cfd4d8}</style>
<script type="importmap">{"imports":{"three":"http://local/three.module.js"}}</script></head><body>
<script type="module">
import * as THREE from 'three';
const S = await (await fetch('http://local/scene.json')).json();
const V = await (await fetch('http://local/view.json')).json();
const W = ${view.w || 1080}, H = ${view.h3d || view.h || 1350};
const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true, preserveDrawingBuffer: true });
renderer.setPixelRatio(1); renderer.setSize(W, H);
renderer.shadowMap.enabled = true; renderer.shadowMap.type = THREE.PCFSoftShadowMap;
renderer.outputColorSpace = THREE.SRGBColorSpace; renderer.toneMapping = THREE.ACESFilmicToneMapping; renderer.toneMappingExposure = 1.05;
const stage = document.createElement('div'); stage.id = 'stage'; stage.appendChild(renderer.domElement); document.body.appendChild(stage);
const scene = new THREE.Scene();
const y0 = S.floor;
const group = new THREE.Group(); group.position.y = -y0; scene.add(group);

// кости
const boneMat = new THREE.MeshStandardMaterial({ color: 0xe8e2d6, roughness: 0.62, metalness: 0.0 });
for (const b of S.bones) {
  const g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.Float32BufferAttribute(b.v, 3));
  g.setIndex(b.f); g.computeVertexNormals();
  const m = new THREE.Mesh(g, boneMat); m.castShadow = true; m.receiveShadow = true; group.add(m);
}

// мышцы: веретено вдоль пути, толщина от максимальной силы
const tierColor = { 1: 0x9b1b2c, 2: 0xe8736c, 3: 0x45a852, 4: 0x3a70d8 };
const mats = {};
for (const t in tierColor) mats[t] = new THREE.MeshStandardMaterial({ color: tierColor[t], roughness: 0.42, metalness: 0.0 });
function spindle(pts, rmax) {
  const curve = new THREE.CatmullRomCurve3(pts.map(p => new THREE.Vector3(...p)), false, 'centripetal');
  const N = 64, R = 18;
  const fr = curve.computeFrenetFrames(N, false);
  const pos = [], idx = [];
  for (let i = 0; i <= N; i++) {
    const t = i / N, c = curve.getPointAt(t);
    const r = rmax * (0.16 + 0.84 * Math.pow(Math.sin(Math.PI * t), 0.75));
    for (let j = 0; j < R; j++) {
      const a = j / R * Math.PI * 2;
      const n = fr.normals[i].clone().multiplyScalar(Math.cos(a)).add(fr.binormals[i].clone().multiplyScalar(Math.sin(a)));
      pos.push(c.x + n.x * r, c.y + n.y * r, c.z + n.z * r);
    }
  }
  for (let i = 0; i < N; i++) for (let j = 0; j < R; j++) {
    const a = i * R + j, b = i * R + (j + 1) % R, c2 = (i + 1) * R + j, d = (i + 1) * R + (j + 1) % R;
    idx.push(a, c2, b, b, c2, d);
  }
  const g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3)); g.setIndex(idx); g.computeVertexNormals();
  return g;
}
for (const mu of S.muscles) {
  if (mu.pts.length < 2) continue;
  const rmax = (V.muscleScale || 1) * (0.004 + 0.00033 * Math.sqrt(mu.force));
  const m = new THREE.Mesh(spindle(mu.pts, rmax), mats[mu.tier]); m.castShadow = true; group.add(m);
}

// штанга
if (V.bar) {
  const metal = new THREE.MeshStandardMaterial({ color: 0x9aa0a6, roughness: 0.35, metalness: 0.8 });
  const plate = new THREE.MeshStandardMaterial({ color: 0x1d1f22, roughness: 0.6, metalness: 0.2 });
  const c = new THREE.Vector3(...V.bar.center);
  const bar = new THREE.Mesh(new THREE.CylinderGeometry(0.014, 0.014, 2.1, 24), metal);
  bar.rotation.x = Math.PI / 2; bar.position.copy(c); bar.castShadow = true; group.add(bar);
  for (const s of [-1, 1]) for (const k of [0, 1]) {
    const p = new THREE.Mesh(new THREE.CylinderGeometry(0.225, 0.225, 0.045, 48), plate);
    p.rotation.x = Math.PI / 2; p.position.set(c.x, c.y, c.z + s * (0.80 + k * 0.05)); p.castShadow = true; group.add(p);
  }
}

// стрелки движения: пунктирная кривая с наконечником
const arrowMat = new THREE.MeshBasicMaterial({ color: 0xf2b134 });
function arrow(points, double) {
  const curve = new THREE.CatmullRomCurve3(points.map(p => new THREE.Vector3(...p)));
  const L = curve.getLength(), dash = 0.035, gap = 0.022;
  for (let s = 0; s < L - 0.06; s += dash + gap) {
    const a = s / L, b = Math.min((s + dash) / L, 1);
    const seg = new THREE.CatmullRomCurve3([curve.getPointAt(a), curve.getPointAt((a + b) / 2), curve.getPointAt(b)]);
    group.add(new THREE.Mesh(new THREE.TubeGeometry(seg, 6, 0.006, 8, false), arrowMat));
  }
  const heads = double ? [1, 0] : [1];
  for (const e of heads) {
    const tip = curve.getPointAt(e), dir = curve.getTangentAt(e).multiplyScalar(e === 1 ? 1 : -1);
    const cone = new THREE.Mesh(new THREE.ConeGeometry(0.022, 0.06, 20), arrowMat);
    cone.position.copy(tip); cone.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), dir.normalize()); group.add(cone);
  }
}
for (const a of (V.arrows || [])) arrow(a.pts, a.double);

// пол с тенью
const floor = new THREE.Mesh(new THREE.PlaneGeometry(8, 8), new THREE.ShadowMaterial({ opacity: 0.32 }));
floor.rotation.x = -Math.PI / 2; floor.receiveShadow = true; scene.add(floor);

// свет
scene.add(new THREE.HemisphereLight(0xffffff, 0x3a3f44, 1.1));
const key = new THREE.DirectionalLight(0xffffff, 2.4); key.position.set(...(V.key || [2.5, 4, 2])); key.castShadow = true;
key.shadow.mapSize.set(2048, 2048); Object.assign(key.shadow.camera, { left: -2, right: 2, top: 2.5, bottom: -1, near: 0.5, far: 12 }); key.shadow.bias = -0.0004;
scene.add(key);
const rim = new THREE.DirectionalLight(0xbfd4ff, 1.2); rim.position.set(-3, 3, -2.5); scene.add(rim);
const fill = new THREE.DirectionalLight(0xffffff, 0.5); fill.position.set(0, 1, 3); scene.add(fill);

// камера
const camera = new THREE.PerspectiveCamera(V.fov || 30, W / H, 0.05, 50);
camera.position.set(...V.cam); camera.lookAt(new THREE.Vector3(...V.target));
renderer.render(scene, camera);
if (V.legend) {
  const d = document.createElement('div'); d.className = 'legend';
  d.innerHTML = (V.title ? '<h2>' + V.title + '</h2>' : '') + V.legend.map(l => '<div class="row"><div class="sw" style="background:#' + tierColor[l.tier].toString(16).padStart(6, '0') + '"></div><div><b>' + l.label + '</b><span>' + l.items + '</span></div></div>').join('');
  document.body.appendChild(d);
}
window.__done = true;
</script></body></html>`;

(async () => {
  const b = await chromium.launch({ args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
  const p = await b.newPage({ viewport: { width: view.w || 1080, height: view.h || 1350 } });
  p.on('console', m => console.log('page:', m.text()));
  p.on('pageerror', e => console.log('error:', e.message));
  await p.route('http://local/**', r => {
    const u = r.request().url();
    if (u.endsWith('/three.module.js')) return r.fulfill({ body: three, contentType: 'application/javascript' });
    if (u.endsWith('/scene.json')) return r.fulfill({ body: fs.readFileSync(scenePath), contentType: 'application/json' });
    if (u.endsWith('/view.json')) return r.fulfill({ body: JSON.stringify(view), contentType: 'application/json' });
    return r.fulfill({ body: page, contentType: 'text/html' });
  });
  await p.goto('http://local/index.html');
  await p.waitForFunction(() => window.__done === true, null, { timeout: 180000 });
  await p.screenshot({ path: outPath });
  await b.close();
})();
