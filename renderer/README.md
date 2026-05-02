# Excalidraw renderer (`puppeteer-core` + your existing browser)

Renders `.excalidraw` JSON files to PNG using the actual
`@excalidraw/excalidraw` library inside whichever Chromium-based browser
you already have on your system. Output preserves the genuine hand-drawn
rough.js aesthetic.

## Setup (once)

```bash
cd ~/.claude/skills/excalidraw/renderer
npm install
```

Installs `puppeteer-core` (~5 MB) and a couple of transitive deps. **No
Chromium is downloaded.** The renderer drives whichever Chromium-based
browser you already have installed — autodetected in this order:

- **macOS**: Google Chrome → Chrome Canary → Chromium → Brave → Edge → Arc
- **Linux**: `google-chrome` → `chromium` → `brave-browser` → `microsoft-edge` (whichever is on PATH)
- **Windows**: Chrome (Program Files / x86 / LocalAppData) → Edge

To force a specific browser, set `PUPPETEER_EXECUTABLE_PATH`:

```bash
PUPPETEER_EXECUTABLE_PATH=/Applications/Brave\ Browser.app/Contents/MacOS/Brave\ Browser \
  node render.js diagram.excalidraw
```

If you have **no** Chromium-based browser, you have three options:

```bash
# 1. Install Chrome system-wide (recommended)
#    https://www.google.com/chrome/

# 2. Or download a bundled Chrome into this skill's local .cache/
#    (~150 MB, one-time; uses @puppeteer/browsers under the hood)
npm run install-chromium

# 3. Or point at any other Chromium-based browser you have
PUPPETEER_EXECUTABLE_PATH=/path/to/your/browser node render.js …
```

`render.js` autodetects in this order: env var → system browser → bundled
download in `.cache/`. The first match wins.

## Usage

```bash
node render.js <input.excalidraw> [output.png] [--scale=N]
```

- Output defaults to the input path with `.png` extension.
- `--scale` defaults to `2` (retina-quality export).

Examples:

```bash
node render.js diagram.excalidraw                     # → diagram.png
node render.js diagram.excalidraw out.png --scale=3   # 3× retina
```

## How it works

1. The renderer launches the system Chrome in headless mode via
   `puppeteer-core`.
2. The browser loads `render.html`, which dynamically imports
   `@excalidraw/excalidraw@0.17.6` from `esm.sh`.
3. `render.js` feeds the input file's `elements` / `appState` / `files`
   into `Excalidraw.exportToBlob()`.
4. The PNG blob is read as a data URL, decoded, and written to disk.

## Notes

- Requires internet on first render (esm.sh CDN). The browser caches the
  module afterwards.
- For SVG output instead of PNG, swap `exportToBlob` for `exportToSvg` in
  `render.js`.
- `node_modules/` and `package-lock.json` are gitignored.
