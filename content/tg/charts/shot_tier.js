const { chromium } = require('playwright');
(async () => { const b = await chromium.launch(); const p = await b.newPage({ viewport: { width: 1080, height: 1350 } });
await p.goto('file://' + __dirname + '/04_tierlist_grud.html', { waitUntil: 'networkidle' }); await p.waitForTimeout(500);
await p.screenshot({ path: __dirname + '/tier.png' }); await b.close(); })();
