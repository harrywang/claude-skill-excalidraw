# Excalidraw renderer (Puppeteer + real `@excalidraw/excalidraw`)

Renders `.excalidraw` JSON files to PNG using the actual Excalidraw library
inside a headless Chromium. Output preserves the genuine hand-drawn
rough.js aesthetic.

## Setup (once)

```bash
cd ~/.claude/skills/excalidraw/renderer
npm install
```

Puppeteer downloads Chromium (~150 MB) on first install.

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

1. Puppeteer launches a headless Chromium.
2. It loads `render.html`, which dynamically imports
   `@excalidraw/excalidraw@0.17.6` from `esm.sh`.
3. The Node script feeds the `.excalidraw` JSON's `elements`, `appState`,
   and `files` into `Excalidraw.exportToBlob()`.
4. The PNG blob is read as a data URL, decoded, and written to disk.

## Notes

- Requires internet on first render (esm.sh CDN). The browser caches the
  module afterwards.
- For SVG output, swap `exportToBlob` for `exportToSvg` in `render.js`.
- `node_modules/` and `package-lock.json` are gitignored.
