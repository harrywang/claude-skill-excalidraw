// Download a bundled Chrome into ./.cache for users without a system browser.
// Run with:  npm run install-chromium
//
// Re-run any time to upgrade to the latest stable build.
import {
  install,
  computeExecutablePath,
  resolveBuildId,
  detectBrowserPlatform,
  Browser,
} from '@puppeteer/browsers';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const cacheDir = path.join(__dirname, '.cache');
fs.mkdirSync(cacheDir, { recursive: true });

const platform = detectBrowserPlatform();
if (!platform) {
  console.error(`Unsupported platform ${process.platform}/${process.arch}.`);
  process.exit(1);
}

console.log(`Resolving latest stable Chrome for ${platform}…`);
const buildId = await resolveBuildId(Browser.CHROME, platform, 'stable');
console.log(`Downloading Chrome ${buildId} to ${cacheDir} (~150 MB)…`);

let lastPct = -1;
await install({
  browser: Browser.CHROME,
  buildId,
  cacheDir,
  platform,
  downloadProgressCallback: (down, total) => {
    const pct = Math.floor((down / total) * 100);
    if (pct !== lastPct && pct % 10 === 0) {
      lastPct = pct;
      process.stdout.write(`  ${pct}%\n`);
    }
  },
});

const executablePath = computeExecutablePath({
  browser: Browser.CHROME,
  buildId,
  cacheDir,
  platform,
});

// Marker file so render.js can find this without re-resolving anything.
fs.writeFileSync(path.join(cacheDir, 'chrome-path'), executablePath);

console.log(`\nDone. Chrome installed at:\n  ${executablePath}`);
console.log(`render.js will pick this up automatically next time you run a render.`);
