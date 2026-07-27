#!/usr/bin/env python3
"""
Downsample source-prepped.png to a character grid and map brightness to
a density ramp, then render as an SVG where each row wipes in
left-to-right (with a small block cursor riding the edge), staggered
top to bottom. Prints once and freezes - no looping.

    python scripts/make_ascii_svg.py
"""
import sys
from pathlib import Path

import numpy as np
from PIL import Image

# bright (sparse) -> dark (dense); leading space clears the background to nothing
RAMP = " .`:-=+*cs#%@"

INPUT_PATH = Path(__file__).parent.parent / "source-prepped.png"
OUTPUT_PATH = Path(__file__).parent.parent / "ascii-portrait.svg"

COLS = 100          # character grid width
CHAR_W = 3.6         # px per character cell, tuned for monospace at this font-size
CHAR_H = 7.2         # ~2x CHAR_W, typical monospace cell aspect
FONT_SIZE = 8
FILL_COLOR = "#c9d1d9"   # single light-gray fill - no per-character rainbow

ROW_WIPE_DUR = 0.5       # seconds for one row to wipe in
ROW_STAGGER = 0.028      # seconds between successive row starts


def image_to_ascii_rows(img: Image.Image, cols: int) -> list[str]:
    aspect = img.height / img.width
    # correct for character cell aspect ratio so the portrait isn't squashed
    rows = max(1, round(cols * aspect * (CHAR_W / CHAR_H)))
    small = img.resize((cols, rows), Image.LANCZOS)
    arr = np.array(small.convert("L"), dtype=np.float32)

    ramp_len = len(RAMP) - 1
    ascii_rows = []
    for r in range(rows):
        line_chars = []
        for c in range(cols):
            brightness = arr[r, c] / 255.0  # 0 = black, 1 = white
            # invert: bright pixel -> sparse (low index) char
            idx = int(round((1.0 - brightness) * ramp_len))
            idx = max(0, min(ramp_len, idx))
            line_chars.append(RAMP[idx])
        ascii_rows.append("".join(line_chars))
    return ascii_rows


def escape_xml(s: str) -> str:
    return (
        s.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def build_svg(ascii_rows: list[str], cols: int) -> str:
    n_rows = len(ascii_rows)
    width = cols * CHAR_W
    height = n_rows * CHAR_H

    parts = []
    parts.append(
        f'<svg viewBox="0 0 {width:.1f} {height:.1f}" xmlns="http://www.w3.org/2000/svg" '
        f'font-family="ui-monospace, SFMono-Regular, Menlo, monospace">'
    )
    parts.append(f'<rect width="{width:.1f}" height="{height:.1f}" fill="none"/>')

    clip_id_prefix = "wipe"
    for r, line in enumerate(ascii_rows):
        y = r * CHAR_H
        text_y = y + CHAR_H * 0.82
        begin = r * ROW_STAGGER
        clip_id = f"{clip_id_prefix}{r}"

        # Clip rect wipes left -> right, then freezes fully open
        parts.append(f'<clipPath id="{clip_id}">')
        parts.append(
            f'<rect x="0" y="{y:.1f}" width="0" height="{CHAR_H:.1f}">'
            f'<animate attributeName="width" from="0" to="{width:.1f}" '
            f'begin="{begin:.3f}s" dur="{ROW_WIPE_DUR}s" fill="freeze" calcMode="linear"/>'
            f"</rect>"
        )
        parts.append("</clipPath>")

        parts.append(f'<g clip-path="url(#{clip_id})">')
        parts.append(
            f'<text x="0" y="{text_y:.1f}" font-size="{FONT_SIZE}" fill="{FILL_COLOR}" '
            f'xml:space="preserve">{escape_xml(line)}</text>'
        )
        parts.append("</g>")

        # small block cursor riding the wipe edge, same timing, then vanish
        cursor_w = CHAR_W * 0.9
        parts.append(
            f'<rect x="0" y="{y:.1f}" width="{cursor_w:.1f}" height="{CHAR_H:.1f}" fill="{FILL_COLOR}" opacity="0.85">'
            f'<animate attributeName="x" from="0" to="{width - cursor_w:.1f}" '
            f'begin="{begin:.3f}s" dur="{ROW_WIPE_DUR}s" fill="freeze" calcMode="linear"/>'
            f'<animate attributeName="opacity" from="0.85" to="0" '
            f'begin="{begin + ROW_WIPE_DUR:.3f}s" dur="0.15s" fill="freeze"/>'
            f"</rect>"
        )

    parts.append("</svg>")
    return "\n".join(parts)


def main():
    if not INPUT_PATH.exists():
        print(
            f"{INPUT_PATH} not found - run `python scripts/prep_photo.py <photo>` first.",
            file=sys.stderr,
        )
        sys.exit(1)

    img = Image.open(INPUT_PATH)
    ascii_rows = image_to_ascii_rows(img, COLS)
    svg = build_svg(ascii_rows, COLS)

    OUTPUT_PATH.write_text(svg)
    print(f"Wrote {OUTPUT_PATH} ({COLS} cols x {len(ascii_rows)} rows)")


if __name__ == "__main__":
    main()
