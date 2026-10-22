// usage: node render.js in.svg out.png
const { chromium } = require(require('child_process').execSync('npm root -g').toString().trim() + '/playwright');
const fs = require('fs');
(async () => {
  const [, , inp, out] = process.argv;
  const svg = fs.readFileSync(inp, 'utf8');
  const b = await chromium.launch();
  const p = await b.newPage({ viewport: { width: 900, height: 650 } });
  await p.setContent(`<html><body style="margin:0;background:#fff">${svg}</body></html>`);
  const el = await p.$('svg');
  await el.screenshot({ path: out });
  await b.close();
})();
