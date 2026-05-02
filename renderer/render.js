// Render an .excalidraw JSON file to PNG using the real @excalidraw/excalidraw
// library inside a headless Chromium. Usage:
//
//   node render.js <input.excalidraw> [output.png] [--scale=2]
//
// Defaults: writes to <input>.png at scale=2.
import puppeteer from 'puppeteer';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

function parseArgs(argv) {
  const args = { positional: [], scale: 2 };
  for (const a of argv) {
    if (a.startsWith('--scale=')) args.scale = Number(a.split('=')[1]);
    else args.positional.push(a);
  }
  return args;
}

const args = parseArgs(process.argv.slice(2));
const inputPath = args.positional[0];
if (!inputPath) {
  console.error('usage: node render.js <input.excalidraw> [output.png] [--scale=N]');
  process.exit(1);
}
const outputPath = args.positional[1]
  ?? inputPath.replace(/\.excalidraw$/, '.png');

const raw = fs.readFileSync(inputPath, 'utf8');
const data = JSON.parse(raw);

const browser = await puppeteer.launch({
  headless: 'new',
  args: ['--no-sandbox', '--disable-setuid-sandbox'],
});
try {
  const page = await browser.newPage();
  page.on('pageerror', (e) => console.error('[page error]', e.message));
  page.on('console', (msg) => {
    if (msg.type() === 'error') console.error('[console]', msg.text());
  });

  const hostUrl = 'file://' + path.join(__dirname, 'render.html');
  await page.goto(hostUrl, { waitUntil: 'networkidle0', timeout: 60000 });
  await page.waitForFunction(
    () => window.renderReady === true || window.renderError,
    { timeout: 60000 }
  );

  const err = await page.evaluate(() => window.renderError || null);
  if (err) throw new Error('Excalidraw load failed: ' + err);

  const debug = await page.evaluate(() => ({
    keys: window.exportKeys,
    fns: Object.fromEntries(Object.entries(window.exportFns).map(([k, v]) => [k, typeof v])),
  }));
  console.error('[excalidraw] exports:', debug.keys.join(', '));
  console.error('[excalidraw] fns:', debug.fns);

  const dataUrl = await page.evaluate(async (elements, appState, files, scale) => {
    const exportToBlob = window.exportFns.exportToBlob;
    if (typeof exportToBlob !== 'function') {
      throw new Error('exportToBlob not found. exports=' + window.exportKeys.join(','));
    }
    const blob = await exportToBlob({
      elements,
      appState: {
        ...(appState || {}),
        exportBackground: true,
        exportWithDarkMode: false,
        viewBackgroundColor: (appState && appState.viewBackgroundColor) || '#ffffff',
      },
      files: files || null,
      mimeType: 'image/png',
      quality: 1,
      getDimensions: (w, h) => ({ width: w * scale, height: h * scale, scale }),
    });
    return await new Promise((res, rej) => {
      const r = new FileReader();
      r.onload = () => res(r.result);
      r.onerror = () => rej(r.error);
      r.readAsDataURL(blob);
    });
  }, data.elements, data.appState ?? {}, data.files ?? {}, args.scale);

  const base64 = dataUrl.split(',')[1];
  fs.writeFileSync(outputPath, Buffer.from(base64, 'base64'));
  console.log(`Wrote ${outputPath}`);
} finally {
  await browser.close();
}
