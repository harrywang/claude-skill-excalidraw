// Render an .excalidraw JSON file to PNG using the real @excalidraw/excalidraw
// library inside the system's installed Chrome (or any Chromium-based browser
// already on the machine — no Chromium download required). Usage:
//
//   node render.js <input.excalidraw> [output.png] [--scale=2]
//
// Defaults: writes to <input>.png at scale=2.
//
// To override the Chrome path explicitly, set PUPPETEER_EXECUTABLE_PATH.
import puppeteer from 'puppeteer-core';
import fs from 'node:fs';
import path from 'node:path';
import os from 'node:os';
import { execSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

function findChrome() {
  // 1. Explicit override via env var.
  if (process.env.PUPPETEER_EXECUTABLE_PATH) {
    return process.env.PUPPETEER_EXECUTABLE_PATH;
  }

  // 2. System-installed browser.
  const platform = os.platform();
  const candidates = [];
  if (platform === 'darwin') {
    candidates.push(
      '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
      '/Applications/Google Chrome Canary.app/Contents/MacOS/Google Chrome Canary',
      '/Applications/Chromium.app/Contents/MacOS/Chromium',
      '/Applications/Brave Browser.app/Contents/MacOS/Brave Browser',
      '/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge',
      '/Applications/Arc.app/Contents/MacOS/Arc',
    );
  } else if (platform === 'linux') {
    for (const cmd of ['google-chrome', 'google-chrome-stable',
                       'chromium', 'chromium-browser',
                       'brave-browser', 'microsoft-edge']) {
      try {
        const p = execSync(`command -v ${cmd}`, { stdio: ['ignore', 'pipe', 'ignore'] })
          .toString().trim();
        if (p) candidates.push(p);
      } catch {}
    }
  } else if (platform === 'win32') {
    const pf = process.env['ProgramFiles'] ?? 'C:\\Program Files';
    const pf86 = process.env['ProgramFiles(x86)'] ?? 'C:\\Program Files (x86)';
    const localApp = process.env['LOCALAPPDATA'] ?? '';
    candidates.push(
      `${pf}\\Google\\Chrome\\Application\\chrome.exe`,
      `${pf86}\\Google\\Chrome\\Application\\chrome.exe`,
      `${localApp}\\Google\\Chrome\\Application\\chrome.exe`,
      `${pf}\\Microsoft\\Edge\\Application\\msedge.exe`,
      `${pf86}\\Microsoft\\Edge\\Application\\msedge.exe`,
    );
  }
  for (const c of candidates) {
    if (c && fs.existsSync(c)) return c;
  }

  // 3. Locally-cached Chrome (downloaded earlier via `npm run install-chromium`).
  const cachedMarker = path.join(__dirname, '.cache', 'chrome-path');
  if (fs.existsSync(cachedMarker)) {
    const cached = fs.readFileSync(cachedMarker, 'utf8').trim();
    if (cached && fs.existsSync(cached)) return cached;
  }

  // 4. Out of options.
  throw new Error(
    'No Chrome / Chromium / Brave / Edge found on your system.\n' +
    '\n' +
    'Pick one:\n' +
    '  • Install Chrome:           https://www.google.com/chrome/\n' +
    '  • Or download a bundled Chrome locally to this skill (one-time, ~150 MB):\n' +
    '        cd ' + __dirname + ' && npm run install-chromium\n' +
    '  • Or set PUPPETEER_EXECUTABLE_PATH=/path/to/your/browser'
  );
}

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

const executablePath = findChrome();
const browser = await puppeteer.launch({
  headless: 'new',
  executablePath,
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
