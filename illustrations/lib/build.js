#!/usr/bin/env node
// usage: node build.js spec.json [out.svg] [--no-png]
// Собирает SVG по spec и сразу рендерит PNG рядом (через render.js).
const fs = require('fs');
const path = require('path');
const { execFileSync } = require('child_process');
const { drawExercise } = require('./figure');

const args = process.argv.slice(2);
const noPng = args.includes('--no-png');
const [inp, outArg] = args.filter(a => !a.startsWith('--'));
if (!inp) { console.error('usage: node build.js spec.json [out.svg] [--no-png]'); process.exit(1); }
const spec = JSON.parse(fs.readFileSync(inp, 'utf8'));
const outSvg = outArg || inp.replace(/\.json$/i, '') + '.svg';
fs.writeFileSync(outSvg, drawExercise(spec));
console.log('svg:', outSvg);
if (!noPng) {
  const png = outSvg.replace(/\.svg$/i, '') + '.png';
  execFileSync(process.execPath, [path.join(__dirname, 'render.js'), outSvg, png], { stdio: 'inherit' });
  console.log('png:', png);
}
