const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();
  page.on('console', (msg) => {
    console.log(`[console:${msg.type()}] ${msg.text()}`);
  });
  page.on('pageerror', (err) => {
    console.log(`[pageerror] ${err.message}`);
  });
  await page.goto('http://127.0.0.1:4173/', { waitUntil: 'load', timeout: 60000 }).catch((err) => {
    console.log(`[goto-error] ${err.message}`);
  });
  await page.waitForTimeout(5000);
  console.log('[status] content:', await page.content());
  await browser.close();
})();
