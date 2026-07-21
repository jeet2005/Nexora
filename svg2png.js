const { chromium } = require('@playwright/test');
const path = require('path');
const fs = require('fs');

(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage();
  const svgPath = path.join(__dirname, 'frontend', 'public', 'favicon.svg');
  const svgContent = fs.readFileSync(svgPath, 'utf8');
  
  // Set content directly
  await page.setContent(`
    <!DOCTYPE html>
    <html>
      <body style="margin: 0; padding: 0; display: flex; justify-content: center; align-items: center; background: transparent; width: 256px; height: 256px;">
        ${svgContent}
      </body>
    </html>
  `);
  
  // Wait for svg to render
  await page.waitForTimeout(500);

  // Take screenshot
  const el = await page.$('svg');
  if (el) {
    await el.screenshot({ path: path.join(__dirname, 'frontend', 'public', 'favicon.png'), omitBackground: true });
    console.log('Successfully created favicon.png');
  } else {
    console.error('SVG element not found in page');
  }
  
  await browser.close();
})();
