const { chromium } = require('playwright');
(async () => { const b = await chromium.launch(); const p = await b.newPage({ viewport: { width: 1080, height: 1350 } });
await p.goto('file://' + __dirname + '/01_zhim_chastota.html', { waitUntil: 'networkidle' }); await p.waitForTimeout(500);
await p.screenshot({ path: __dirname + '/../01_zhim_kazhduyu_trenirovku.png' }); await b.close(); })();
