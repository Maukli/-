// usage: node atlas_build.js opts.json out.svg   (рядом пишет out.png через render.js)
//        node atlas_build.js list.json out_dir   (массив opts, файлы по key)
'use strict';
const fs = require('fs');
const path = require('path');
const { execFileSync } = require('child_process');
const { drawMuscle, VIEWS } = require('./atlas');

const [, , inp, out] = process.argv;
if (!inp || !out) { console.error('usage: node atlas_build.js opts.json out.svg'); process.exit(1); }
const data = JSON.parse(fs.readFileSync(inp, 'utf8'));
const render = path.join(__dirname, 'render.js');

function build(opts, svgPath) {
  for (const id of opts.highlight || []) {
    const found = Object.values(VIEWS).some((v) => v.muscles[id] || (v.arm && v.arm[id]));
    if (!found) console.error(`warning: unknown muscle id "${id}"`);
  }
  fs.mkdirSync(path.dirname(path.resolve(svgPath)), { recursive: true });
  fs.writeFileSync(svgPath, drawMuscle(opts));
  const png = svgPath.replace(/\.svg$/i, '') + '.png';
  execFileSync('node', [render, svgPath, png], { stdio: 'inherit' });
  console.log(png);
}

if (Array.isArray(data)) {
  for (const o of data) build(o, path.join(out, `${o.key || 'muscle'}.svg`));
} else build(data, out);
