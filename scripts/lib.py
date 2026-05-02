"""Build Excalidraw JSON files programmatically.

Use these helpers in a Python script to compose a hand-drawn diagram, then
render to PNG via `renderer/render.js` for the genuine Excalidraw look.

Quick start:

    import sys, pathlib
    sys.path.insert(0, str(pathlib.Path.home() / ".claude/skills/excalidraw"))
    from lib import (text, labeled_box, arrow, save_doc,
                     PAL_GOAL, PAL_AI, PAL_HUMAN, PAL_END, GRAY)

    elements = []
    elements.append(text(40, 30, 1200, "Title", size=28))
    elements += labeled_box(40, 200, 240, 110,
                            ["GOAL", "Start"], PAL_GOAL)
    elements += labeled_box(340, 200, 240, 110,
                            ["Step 1", "do thing"], PAL_AI)
    elements.append(arrow(280, 255, 340, 255))
    save_doc(elements, "/abs/path/to/diagram.excalidraw")
"""
import json
import uuid
from pathlib import Path

# ---------------------------------------------------------------------------
# Palette options
# Each palette is a dict with keys: bg (background), stroke, title (text).

# Refined palette — pale, warm/cool rhythm; one accent (HUMAN) for the outlier.
PAL_GOAL    = {"bg": "#fff7d6", "stroke": "#a8860a", "title": "#7a6207"}
PAL_AI      = {"bg": "#e6efff", "stroke": "#3a5fa3", "title": "#1d3a72"}
PAL_HUMAN   = {"bg": "#ffe1d4", "stroke": "#b9522b", "title": "#7a3416"}
PAL_END     = {"bg": "#e3f5ec", "stroke": "#3a8a64", "title": "#1f5a3e"}
PAL_NEUTRAL = {"bg": "#f1f3f5", "stroke": "#495057", "title": "#212529"}

# Vibrant palette — Excalidraw classic primary tones.
PAL_VIBRANT_YELLOW = {"bg": "#ffec99", "stroke": "#f08c00", "title": "#7a4f00"}
PAL_VIBRANT_BLUE   = {"bg": "#a5d8ff", "stroke": "#1971c2", "title": "#0d3d6e"}
PAL_VIBRANT_RED    = {"bg": "#ffc9c9", "stroke": "#c92a2a", "title": "#7a1818"}
PAL_VIBRANT_GREEN  = {"bg": "#b2f2bb", "stroke": "#2f9e44", "title": "#1f5a2a"}
PAL_VIBRANT_PURPLE = {"bg": "#d0bfff", "stroke": "#6741d9", "title": "#3d2b80"}

# Common text colors
BODY_COLOR   = "#33333a"
GRAY         = "#5c5f66"
TEXT_DEFAULT = "#1e1e1e"


# ---------------------------------------------------------------------------
# Internal helpers

def _uid():
    return uuid.uuid4().hex[:16]


def _base():
    """Common Excalidraw element scaffolding shared by all element types."""
    return {
        "angle": 0,
        "strokeWidth": 2,
        "strokeStyle": "solid",
        "roughness": 1,
        "opacity": 100,
        "groupIds": [],
        "frameId": None,
        "isDeleted": False,
        "boundElements": None,
        "updated": 1714530000000,
        "link": None,
        "locked": False,
        "seed": int(uuid.uuid4().int % 2_000_000_000),
        "versionNonce": int(uuid.uuid4().int % 2_000_000_000),
    }


# ---------------------------------------------------------------------------
# Shape primitives

def rectangle(x, y, w, h, bg, stroke, fill_style="solid", roundness=True):
    el = _base()
    el.update({
        "id": _uid(),
        "type": "rectangle",
        "x": x, "y": y, "width": w, "height": h,
        "strokeColor": stroke,
        "backgroundColor": bg,
        "fillStyle": fill_style,
        "roundness": {"type": 3} if roundness else None,
    })
    return el


def ellipse(x, y, w, h, bg, stroke, fill_style="solid"):
    el = _base()
    el.update({
        "id": _uid(),
        "type": "ellipse",
        "x": x, "y": y, "width": w, "height": h,
        "strokeColor": stroke,
        "backgroundColor": bg,
        "fillStyle": fill_style,
        "roundness": {"type": 2},
    })
    return el


def diamond(x, y, w, h, bg, stroke, fill_style="solid"):
    el = _base()
    el.update({
        "id": _uid(),
        "type": "diamond",
        "x": x, "y": y, "width": w, "height": h,
        "strokeColor": stroke,
        "backgroundColor": bg,
        "fillStyle": fill_style,
        "roundness": {"type": 2},
    })
    return el


# ---------------------------------------------------------------------------
# Text

def text(x, y, w, content, size=18, color=TEXT_DEFAULT, align="center"):
    """A free-floating single-line text element.

    For multi-line content centered inside a shape, use `labeled_box`.
    """
    line_height = 1.25
    h = max(int(size * line_height + 2), 20)
    el = _base()
    el.update({
        "id": _uid(),
        "type": "text",
        "x": x, "y": y, "width": w, "height": h,
        "strokeColor": color,
        "backgroundColor": "transparent",
        "fillStyle": "solid",
        "roundness": None,
        "fontSize": size,
        "fontFamily": 5,  # Excalifont
        "text": content,
        "textAlign": align,
        "verticalAlign": "top",
        "containerId": None,
        "originalText": content,
        "lineHeight": line_height,
        "autoResize": True,
    })
    return el


# ---------------------------------------------------------------------------
# Composite: shape + multi-line text vertically centered inside it

def labeled_box(x, y, w, h, lines, palette, sizes=None,
                body_color=BODY_COLOR, shape="rectangle"):
    """A shape filled with several lines of text, vertically centered.

    Args:
        x, y, w, h: bounding box.
        lines: list of strings (one per line).
        palette: dict with `bg`, `stroke`, optional `title` keys, e.g. PAL_AI.
        sizes: optional list of font sizes per line. Defaults to [17, 15, 15, …]
            (slightly larger first line as a title).
        body_color: color for non-title lines.
        shape: "rectangle" | "ellipse" | "diamond".

    Returns a list of elements (the shape + one text per line). The list can
    be `+=`'d into the elements list passed to `save_doc`.
    """
    bg = palette["bg"]
    stroke = palette["stroke"]
    title_color = palette.get("title", body_color)

    if sizes is None:
        sizes = [17] + [15] * (len(lines) - 1)

    if shape == "rectangle":
        elements = [rectangle(x, y, w, h, bg, stroke)]
    elif shape == "ellipse":
        elements = [ellipse(x, y, w, h, bg, stroke)]
    elif shape == "diamond":
        elements = [diamond(x, y, w, h, bg, stroke)]
    else:
        raise ValueError(f"Unknown shape: {shape!r}")

    line_height = 1.25
    line_pixel_heights = [int(s * line_height + 2) for s in sizes]
    block_height = sum(line_pixel_heights)
    cursor_y = y + (h - block_height) / 2
    for i, (content, size) in enumerate(zip(lines, sizes)):
        color = title_color if i == 0 else body_color
        elements.append(text(x, cursor_y, w, content, size=size, color=color))
        cursor_y += line_pixel_heights[i]
    return elements


# ---------------------------------------------------------------------------
# Arrows

def arrow(x1, y1, x2, y2, color="#495057", label=None, label_color=None):
    """Straight arrow from (x1, y1) to (x2, y2).

    If `label` is provided, a small text label is added near the midpoint.
    Returns either a single element (no label) or a list (with label).
    """
    el = _base()
    el.update({
        "id": _uid(),
        "type": "arrow",
        "x": x1, "y": y1,
        "width": abs(x2 - x1),
        "height": abs(y2 - y1),
        "strokeColor": color,
        "backgroundColor": "transparent",
        "fillStyle": "solid",
        "roundness": {"type": 2},
        "points": [[0, 0], [x2 - x1, y2 - y1]],
        "lastCommittedPoint": None,
        "startBinding": None,
        "endBinding": None,
        "startArrowhead": None,
        "endArrowhead": "arrow",
        "elbowed": False,
    })
    if not label:
        return el

    mx = (x1 + x2) / 2
    my = (y1 + y2) / 2
    is_horizontal = abs(x2 - x1) >= abs(y2 - y1)
    label_y = my - 24 if is_horizontal else my - 12
    return [
        el,
        text(mx - 60, label_y, 120, label,
             size=12, color=label_color or GRAY),
    ]


# ---------------------------------------------------------------------------
# Persistence

def save_doc(elements, path, view_bg="#ffffff"):
    """Write a list of elements as a .excalidraw file.

    Flattens any nested lists (helpers like `labeled_box` and `arrow(label=…)`
    return lists of elements).
    """
    flat = []
    for e in elements:
        if isinstance(e, list):
            flat.extend(e)
        else:
            flat.append(e)
    doc = {
        "type": "excalidraw",
        "version": 2,
        "source": "https://excalidraw.com",
        "elements": flat,
        "appState": {
            "viewBackgroundColor": view_bg,
            "gridSize": 20,
        },
        "files": {},
    }
    Path(path).write_text(json.dumps(doc, indent=2))
    return path
