---
name: excalidraw
description: Generate hand-drawn Excalidraw diagrams (flowchart, pipeline, relationship, mind map, architecture) and render to PNG using the actual @excalidraw/excalidraw library inside a bundled headless browser. Saves both `.excalidraw` source + `.png` next to the current note and embeds the PNG. Use when the user asks for a diagram, flowchart, pipeline, mind map, architecture diagram, or to "draw"/"visualize" something for a note.
---

# Excalidraw → PNG (with embed)

End-to-end workflow:

1. Compose the `.excalidraw` JSON in Python using the helpers in `lib.py`.
2. Render to PNG via the bundled local renderer (real `@excalidraw/excalidraw` library inside Puppeteer).
3. Embed `![[diagram.png]]` in the current note.

## When to use

Trigger phrases:

- "Create a diagram for…", "draw a diagram", "visualize this"
- "Make a flowchart / pipeline / mind map / architecture diagram"
- "Diagram the workflow / process / relationship of…"
- After `/excalidraw` slash command (if bound)

## One-time setup

```bash
cd ~/.claude/skills/excalidraw/renderer
npm install
```

(Downloads Chromium ≈150 MB on first install. Required by Puppeteer.)

## Workflow

For a diagram about a note `vault/path/note.md`:

1. **Decide output folder.** Same folder as the current note. Diagram name should be descriptive: `<topic>-pipeline.excalidraw`, `<topic>-flow.excalidraw`, etc.
2. **Write a build script** alongside the note (e.g. `_build_diagram.py`) that imports `lib.py` and calls helpers to assemble elements.
3. **Run the build script** to write the `.excalidraw` file.
4. **Delete the build script** (single-use).
5. **Render to PNG**:
   ```bash
   node ~/.claude/skills/excalidraw/renderer/render.js path/to/diagram.excalidraw
   ```
   The PNG is written next to the source by default. Use `--scale=N` for higher DPI (default `2`).
6. **Embed** `![[diagram.png]]` at the appropriate place in the note.
7. **Keep both `.excalidraw` and `.png`** alongside the note — the `.excalidraw` is the editable source (open in https://excalidraw.com), the `.png` is what renders in Obsidian and travels well to other platforms (LinkedIn, etc.).

## Build-script template

```python
import sys, pathlib
sys.path.insert(0, str(pathlib.Path.home() / ".claude/skills/excalidraw"))
from lib import (
    text, labeled_box, arrow, save_doc,
    PAL_GOAL, PAL_AI, PAL_HUMAN, PAL_END, PAL_NEUTRAL, GRAY,
)

elements = []

# Title + subtitle
elements.append(text(40, 30, 1200, "Diagram Title", size=28))
elements.append(text(40, 70, 1200, "optional subtitle", size=16, color=GRAY))

# … add labeled_box() and arrow() calls here …

save_doc(elements, "/abs/path/to/diagram.excalidraw")
print("done")
```

## Helper API (see `lib.py` for full source)

- `rectangle(x, y, w, h, bg, stroke)` — bare rounded rectangle
- `ellipse(x, y, w, h, bg, stroke)` — bare ellipse
- `diamond(x, y, w, h, bg, stroke)` — bare diamond (decision shape)
- `text(x, y, w, content, size=18, color, align="center")` — free text line
- `labeled_box(x, y, w, h, lines, palette, sizes=None, shape="rectangle")` — shape + multi-line text vertically centered inside. Most common building block. `shape` can be `"rectangle"`, `"ellipse"`, or `"diamond"`. `palette` is a dict like `PAL_AI`.
- `arrow(x1, y1, x2, y2, color="#495057", label=None)` — straight arrow with optional small label near midpoint
- `save_doc(elements, path)` — write the `.excalidraw` JSON file. Flattens nested lists automatically (helpers like `labeled_box` return lists, you can just `+=` them).

## Refined palette (default for new diagrams)

Each palette is a dict with `bg`, `stroke`, `title` keys.

| Palette       | Use                              | bg        | stroke    | title     |
|---------------|----------------------------------|-----------|-----------|-----------|
| `PAL_GOAL`    | Start node / intent              | `#fff7d6` | `#a8860a` | `#7a6207` |
| `PAL_AI`      | All worker / process steps       | `#e6efff` | `#3a5fa3` | `#1d3a72` |
| `PAL_HUMAN`   | Single accent / outlier step     | `#ffe1d4` | `#b9522b` | `#7a3416` |
| `PAL_END`     | Terminal / success / output      | `#e3f5ec` | `#3a8a64` | `#1f5a3e` |
| `PAL_NEUTRAL` | Generic / unimportant            | `#f1f3f5` | `#495057` | `#212529` |

Design rule: keep most boxes the same color (usually `PAL_AI`) and reserve `PAL_HUMAN` (or any contrasting palette) for the *single* outlier you want the eye to land on. Rainbow = noisy; one-accent = clear.

For a louder Excalidraw-classic look, `lib.py` also exports `PAL_VIBRANT_YELLOW`, `PAL_VIBRANT_BLUE`, `PAL_VIBRANT_RED`, `PAL_VIBRANT_GREEN`, `PAL_VIBRANT_PURPLE`.

## Layout patterns (with sample coordinates)

### Linear (simple flowchart)

```
y = 200, h = 110, box w = 240, gap = 60

x positions:    40 → 340 → 640 → 940
arrow start:   280   580   880
arrow end:     340   640   940
arrow y:        255 (= y + h/2)
```

### Snake (long pipeline that wraps)

```
Row 1 (y = 180): boxes at x = 40, 340, 640, 940 — flow left → right
Vertical drop: arrow at x = 1060 from y = 290 → y = 410
Row 2 (y = 410): boxes at x = 940, 640, 340, 40 — flow right → left
```

This is what the bundled `examples/snake_pipeline.py` uses.

### Mind map (radial)

Central node at `(cx, cy)`, e.g. `(600, 350)`. Branches at angles `2π * i / N` from center, radius ~250. Connect each branch to the center with `arrow(cx, cy, bx, by)`.

### Decision flow (with diamond)

Use `labeled_box(..., shape="diamond")` for yes/no decision nodes. Two outgoing arrows, each with a `label="yes"` / `label="no"`.

### Relationship grid

Boxes laid out in a `cols × rows` grid, edges drawn between related ones with `arrow(...)`. For N entities, `cols = ceil(sqrt(N))`.

## Conventions

- **Canvas**: ~1200 × 600 default. Add canvas height for taller diagrams.
- **Title**: `text(40, 30, 1200, "…", size=28)` (left-aligned title in a wide span looks centered if the diagram fills the span).
- **Subtitle**: `size=16, color=GRAY`.
- **Footer / legend**: `size=14, color=GRAY` near the bottom.
- **Element count**: keep under 25 visual elements (boxes + arrows). Anything more should be split into multiple diagrams.
- **Filenames**: lowercase, hyphenated, ending in `-pipeline`, `-flow`, `-arch`, `-mindmap`, `-rel`. Match `.excalidraw` and `.png` basenames.

## Worked example

See `examples/snake_pipeline.py` for the full Baidu-indexing pipeline reproduced end-to-end. It demonstrates:

- Title + subtitle + footer text
- Snake layout (two rows, alternating direction)
- Single-accent palette (one `PAL_HUMAN` box among `PAL_AI` boxes)
- Vertical connector between rows

Copy it as a starting point.

## Troubleshooting

| Symptom | Fix |
|---|---|
| `Error: Could not find Chromium` | Re-run `npm install` in `renderer/` (or `npx puppeteer browsers install chrome`) |
| Text overflows boxes | Reduce `size` or shorten lines. With `lib.py`'s `labeled_box`, three short lines fit cleanly in a `240 × 110` box |
| Arrows misaligned | Recompute arrow `y` as `box_y + box_height / 2`; arrow `x` start = `box_x + box_width`, end = next `box_x` |
| Diagram empty / blank | Confirm `npm install` succeeded; re-run with logs (`node render.js … 2>&1`) |
| First render is slow | Puppeteer downloads Chromium on first run (~150 MB, one-time). Subsequent renders are fast (~3 s) |

## Editing later

- Drag the `.excalidraw` file onto https://excalidraw.com to edit visually.
- Save back to the same path; re-run `node renderer/render.js …` to regenerate the PNG.
- The `.excalidraw` is plain JSON — small mechanical edits (text, color) can also be done with `Edit`.
