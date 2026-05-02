"""Worked example: snake-layout pipeline (the Baidu indexing flow).

Demonstrates:
- Title + subtitle + footer text
- Snake layout: Row 1 flows left → right, vertical drop, Row 2 flows right → left
- Single-accent palette: PAL_AI for the worker, PAL_HUMAN for the lone outlier
- Cream PAL_GOAL start node, mint PAL_END finish node

Run with uv (recommended) or any Python 3.10+:

    uv run python ~/.claude/skills/excalidraw/scripts/snake_pipeline.py \
        path/to/output-folder/baidu-pipeline.excalidraw

Then render to PNG:

    node ~/.claude/skills/excalidraw/renderer/render.js \
        path/to/output-folder/baidu-pipeline.excalidraw
"""
import sys
import pathlib

# Import helpers from the same scripts/ folder
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from lib import (
    text, labeled_box, arrow, save_doc,
    PAL_GOAL, PAL_AI, PAL_HUMAN, PAL_END, GRAY,
)


def build():
    W, H = 240, 110
    ROW1_Y = 180
    ROW2_Y = 410

    elements = []

    # Title + subtitle
    elements.append(text(40, 30, 1200, "PaperFox.ai → Baidu Indexing Pipeline", size=28))
    elements.append(text(40, 70, 1200,
                         "AI did the slog · human did what only humans can",
                         size=16, color=GRAY))

    # Row 1 (left → right): goal → 1. Navigate → human → 2. Meta tag
    elements += labeled_box(40,  ROW1_Y, W, H,
                            ["GOAL", "Index PaperFox.ai", "on Baidu"], PAL_GOAL)
    elements += labeled_box(340, ROW1_Y, W, H,
                            ["1. Navigate Console",
                             "Chrome drives Baidu UI",
                             "(translates Chinese)"], PAL_AI)
    elements += labeled_box(640, ROW1_Y, W, H,
                            ["HUMAN ONLY", "ID verify", "+ CAPTCHA"], PAL_HUMAN)
    elements += labeled_box(940, ROW1_Y, W, H,
                            ["2. Inject Meta Tag",
                             "into root layout",
                             "(no copy-paste)"], PAL_AI)

    # Row 2 (right → left): 3. Push URLs → 4. Skill → 5. Auto-pipeline → done
    elements += labeled_box(940, ROW2_Y, W, H,
                            ["3. Push URLs via API",
                             "replaces 11 manual",
                             "web-form clicks"], PAL_AI)
    elements += labeled_box(640, ROW2_Y, W, H,
                            ["4. Encode as Skill",
                             "/baidu-push <conf-slug>",
                             "(reusable next time)"], PAL_AI)
    elements += labeled_box(340, ROW2_Y, W, H,
                            ["5. Daily Auto-Pipeline",
                             "141 URLs · 10/day",
                             "remote agent · ~14d"], PAL_AI)
    elements += labeled_box(40,  ROW2_Y, W, H,
                            ["INDEXED ON BAIDU", "running on autopilot", ""], PAL_END)

    # Row 1 arrows (left → right)
    y_mid_1 = ROW1_Y + H / 2
    elements.append(arrow(280, y_mid_1, 340, y_mid_1))
    elements.append(arrow(580, y_mid_1, 640, y_mid_1))
    elements.append(arrow(880, y_mid_1, 940, y_mid_1))

    # Vertical connector down at x = right-most box center
    elements.append(arrow(1060, ROW1_Y + H, 1060, ROW2_Y))

    # Row 2 arrows (right → left)
    y_mid_2 = ROW2_Y + H / 2
    elements.append(arrow(940, y_mid_2, 880, y_mid_2))
    elements.append(arrow(640, y_mid_2, 580, y_mid_2))
    elements.append(arrow(340, y_mid_2, 280, y_mid_2))

    # Footer
    elements.append(text(40, 565, 1200,
                         "Pattern: human names the goal + makes the few human-only decisions · AI does the rest",
                         size=14, color=GRAY))

    return elements


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "snake_pipeline.excalidraw"
    save_doc(build(), out)
    print(f"Wrote {out}")
