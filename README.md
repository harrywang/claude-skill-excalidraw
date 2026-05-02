# claude-skill-excalidraw

A Claude Code skill for generating **hand-drawn Excalidraw diagrams** from a
description, rendering them to PNG using the **actual `@excalidraw/excalidraw`
library** inside a headless Chromium, and embedding them in Obsidian (or any
Markdown) notes.

The output is the genuine rough.js sketchy aesthetic — not a CSS approximation,
not a clean-line SVG, the same renderer that drives [excalidraw.com](https://excalidraw.com).

![Snake pipeline example](examples/snake_pipeline.png)

## Why this skill exists

There are several Excalidraw tooling options floating around, but each had a gap:

- **The native `excalidraw-diagram-generator` skill** outputs `.excalidraw`
  JSON only. Without the Excalidraw plugin in Obsidian (or excalidraw.com open
  in a browser), the file doesn't render.
- **Hand-rolled SVGs** mimic the look but feel sterile — straight lines,
  uniform strokes, none of the warmth.
- **`roughjs` directly** gets close but isn't pixel-identical to what
  Excalidraw produces, and doesn't handle bound text or arrowheads well.
- **`excalidraw_export` on npm** depends on the native `canvas` package which
  fails to compile on modern Node + macOS without extra system libraries.

This skill takes the only path that's both **faithful** and **reliable**:
it loads the real `@excalidraw/excalidraw@0.17.6` ESM bundle inside a
Puppeteer-driven Chromium and calls `exportToBlob()` on your elements. The
output is exactly what excalidraw.com would give you.

It bundles everything end-to-end:

1. **Compose** `.excalidraw` JSON with a small set of Python helpers
   (`rectangle`, `labeled_box`, `arrow`, etc.) and a refined default palette.
2. **Render** to PNG via the bundled local renderer (one-time `npm install`).
3. **Embed** `![[diagram.png]]` in the current note.

## Install

```bash
git clone https://github.com/harrywang/claude-skill-excalidraw \
  ~/.claude/skills/excalidraw

cd ~/.claude/skills/excalidraw/renderer
npm install
```

The `npm install` step downloads Chromium (~150 MB) once via Puppeteer.
First render takes a few extra seconds while the `@excalidraw/excalidraw`
bundle is fetched from `esm.sh`; subsequent renders are ~2–3 s.

## Usage

### Inside Claude Code (intended path)

Just ask. The skill auto-triggers on prompts like:

- "Create a pipeline diagram for this post"
- "Make a flowchart of the auth flow"
- "Visualize this process"
- "Mind map the project structure"

Claude will:

1. Decide where to save (next to the current note).
2. Write a Python build script that imports `lib.py`.
3. Run it to produce `<name>.excalidraw`.
4. Run the renderer to produce `<name>.png`.
5. Insert `![[<name>.png]]` into the note.

The build script is single-use and gets deleted after running. The
`.excalidraw` source stays alongside the note as the editable original —
drop it into [excalidraw.com](https://excalidraw.com) anytime to tweak.

### As a standalone tool

You can use the helpers and renderer directly without Claude:

```python
# build_my_diagram.py
import sys, pathlib
sys.path.insert(0, str(pathlib.Path.home() / ".claude/skills/excalidraw"))
from lib import (
    text, labeled_box, arrow, save_doc,
    PAL_GOAL, PAL_AI, PAL_HUMAN, PAL_END, GRAY,
)

elements = []
elements.append(text(40, 30, 1200, "My Pipeline", size=28))
elements += labeled_box(40,  200, 240, 110, ["GOAL", "Start"], PAL_GOAL)
elements += labeled_box(340, 200, 240, 110, ["1. Step", "do thing"], PAL_AI)
elements += labeled_box(640, 200, 240, 110, ["DONE", "result"], PAL_END)
elements.append(arrow(280, 255, 340, 255))
elements.append(arrow(580, 255, 640, 255))
save_doc(elements, "my-diagram.excalidraw")
```

```bash
python3 build_my_diagram.py
node ~/.claude/skills/excalidraw/renderer/render.js my-diagram.excalidraw
# → my-diagram.png
```

## Helper API

All helpers live in [`lib.py`](lib.py).

### Shapes

| Function | Purpose |
|---|---|
| `rectangle(x, y, w, h, bg, stroke)` | Bare rounded rectangle |
| `ellipse(x, y, w, h, bg, stroke)` | Bare ellipse |
| `diamond(x, y, w, h, bg, stroke)` | Bare diamond (decision shape) |

### Composite (most-used)

```python
labeled_box(x, y, w, h, lines, palette, sizes=None, shape="rectangle")
```

Returns a list: `[shape, text_line_1, text_line_2, …]`. The text is
vertically centered inside the shape, with the first line slightly larger
as a title.

- `palette` is one of the `PAL_*` dicts (see below) — `{bg, stroke, title}`.
- `shape` can be `"rectangle"`, `"ellipse"`, or `"diamond"`.
- `sizes` can override the default `[17, 15, 15, …]` sizing.

### Text and arrows

```python
text(x, y, w, content, size=18, color, align="center")
arrow(x1, y1, x2, y2, color="#495057", label=None)
```

`arrow(label="yes")` returns a list: `[arrow, label_text]` so the label
sits near the arrow midpoint.

### Persistence

```python
save_doc(elements, path, view_bg="#ffffff")
```

Flattens nested lists automatically — you can append `labeled_box(...)`
results with `+=` and pass the whole list straight to `save_doc`.

## Palettes

`lib.py` ships two palette families.

### Refined (default — recommended)

Pale, warm/cool rhythm. Use **one `PAL_AI`** for all worker steps and
reserve **one `PAL_HUMAN`** (or any other contrasting palette) for the
single step you want the eye to land on. Rainbow = noisy; one-accent = clear.

| Palette       | bg        | stroke    | title     | When to use                          |
|---------------|-----------|-----------|-----------|--------------------------------------|
| `PAL_GOAL`    | `#fff7d6` | `#a8860a` | `#7a6207` | Start node / intent                  |
| `PAL_AI`      | `#e6efff` | `#3a5fa3` | `#1d3a72` | Worker / process steps               |
| `PAL_HUMAN`   | `#ffe1d4` | `#b9522b` | `#7a3416` | Single accent / outlier              |
| `PAL_END`     | `#e3f5ec` | `#3a8a64` | `#1f5a3e` | Terminal / success                   |
| `PAL_NEUTRAL` | `#f1f3f5` | `#495057` | `#212529` | Generic / unimportant                |

### Vibrant (Excalidraw classic)

The original Excalidraw primaries — louder, useful for kid-friendly or
high-contrast diagrams.

`PAL_VIBRANT_YELLOW`, `PAL_VIBRANT_BLUE`, `PAL_VIBRANT_RED`,
`PAL_VIBRANT_GREEN`, `PAL_VIBRANT_PURPLE`.

## Layout patterns

The skill ships sample coordinate systems for common layouts. See
[`SKILL.md`](SKILL.md) for the full table; quick reference:

| Layout | Use for | Coordinates |
|---|---|---|
| **Linear** | 3–5 step flowcharts | `y=200`, `x = 40, 340, 640, 940`, arrows at `y+h/2` |
| **Snake** | 6–8 step pipelines that wrap | Two rows, alternating direction (see `examples/snake_pipeline.py`) |
| **Decision flow** | Yes/no branching | `labeled_box(..., shape="diamond")` + labelled arrows |
| **Mind map** | Concept hierarchy | Central node + radial branches at `2π · i / N` |
| **Grid** | Relationship diagrams | `cols × rows` with arrows between related boxes |

## How it works

```
your prompt
   ↓
SKILL.md (read by Claude)
   ↓
Claude writes a small Python build script
   ↓ uses lib.py helpers
diagram.excalidraw  ← editable source
   ↓
node renderer/render.js
   ↓ Puppeteer launches headless Chromium
   ↓ render.html imports @excalidraw/excalidraw from esm.sh
   ↓ Excalidraw.exportToBlob({elements, appState, files})
diagram.png  ← embed in note
```

The renderer is just two files (`render.html`, `render.js`) plus a single
npm dep (`puppeteer`). No `canvas` native build, no React polyfills.

## Editing diagrams later

The `.excalidraw` JSON is the authoritative source. To make changes:

1. Drag the `.excalidraw` file onto [excalidraw.com](https://excalidraw.com).
2. Edit visually.
3. **File → Save** to overwrite the original (it's plain JSON).
4. Re-run `node ~/.claude/skills/excalidraw/renderer/render.js path/to/file.excalidraw`
   to regenerate the PNG.

For small mechanical edits (changing a label, swapping a color), you can
also edit the JSON directly in your editor — keys are stable and human-readable.

## Troubleshooting

| Symptom | Fix |
|---|---|
| `Could not find Chromium` | Re-run `npm install` in `renderer/` (or `npx puppeteer browsers install chrome`) |
| Text overflows boxes | Reduce `size` or shorten lines. Three short lines fit cleanly in `240 × 110` |
| Arrows misaligned | Recompute `y = box_y + box_height / 2`; arrow `x` start = `box_x + box_width`, end = next `box_x` |
| Diagram empty / blank | Confirm `npm install` succeeded; rerun with full logs (`node render.js … 2>&1`) |
| First render is slow | Puppeteer downloads Chromium on first run (~150 MB, one-time); next renders are ~3 s |
| Module load timeout | esm.sh CDN is occasionally slow — re-run; the bundle gets cached locally after first load |

## Repo layout

```
claude-skill-excalidraw/
├── README.md              ← you are here
├── SKILL.md               ← Claude Code skill instructions
├── LICENSE                ← MIT
├── lib.py                 ← Python helpers (importable)
├── examples/
│   ├── snake_pipeline.py  ← worked example
│   └── snake_pipeline.png ← rendered output
└── renderer/
    ├── render.html        ← loads @excalidraw/excalidraw from esm.sh
    ├── render.js          ← Puppeteer driver, exportToBlob → PNG
    ├── package.json
    ├── .gitignore         ← excludes node_modules, package-lock.json
    └── README.md
```

## License

MIT — see [LICENSE](LICENSE).
