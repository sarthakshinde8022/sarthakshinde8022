#!/usr/bin/env python3
"""
Hand-author a neofetch-style info card SVG: a terminal title bar, then
key/value rows that fade + slide in on a short stagger, like the panel
is printing next to the ASCII portrait.

A value can contain "\n" to wrap onto multiple lines within its row
(useful for Highlights as it grows) - row height adjusts automatically.

Set STATIC=1 to emit a frozen final frame (handy for local Quick Look
previews where SVG animation doesn't play).
"""
import os

OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "..", "info-card.svg")
STATIC = os.environ.get("STATIC") == "1"

# --- content: edit these to keep the card current ----------------------
TITLE = "sarthak@github"
ROWS = [
    ("Now", "B.Tech ECE (AI/ML) student, DES Pune University"),
    ("Base", "Digital Image Processing (PDIP)"),
    ("Stack", "Python - Embedded C - MySQL - Streamlit"),
    ("Highlights", "ECO-EYE (IoT security) - Art3mis (content) - JayBot (Discord RPG)\nDBMS Fleet Logbook - Derain Dehazing"),
]
# -----------------------------------------------------------------------

WIDTH = 490
TITLEBAR_H = 30
PAD_X = 18
FIRST_ROW_Y = TITLEBAR_H + 26
LABEL_TO_VALUE = 17     # gap from label baseline to first value line
VALUE_LINE_H = 15        # gap between wrapped value lines
ROW_GAP = 14              # gap after a row's last value line, before next label

BG = "#0d1117"
BORDER = "#30363d"
LABEL_COLOR = "#39d353"
VALUE_COLOR = "#c9d1d9"
DOT_COLORS = ["#ff5f56", "#ffbd2e", "#27c93f"]


def row_style(index: int) -> str:
    if STATIC:
        return "opacity:1;"
    delay = index * 0.25
    return f"opacity:0; animation: rowIn 0.45s ease-out forwards; animation-delay:{delay:.2f}s;"


def main():
    parts = []

    # First pass: compute each row's starting y and total card height,
    # since a multi-line value changes how tall a row is.
    row_layout = []
    y_cursor = FIRST_ROW_Y
    for label, value in ROWS:
        lines = value.split("\n")
        row_layout.append((label, lines, y_cursor))
        y_cursor += LABEL_TO_VALUE + VALUE_LINE_H * (len(lines) - 1) + ROW_GAP

    HEIGHT = y_cursor + 8

    parts.append(
        f'<svg viewBox="0 0 {WIDTH} {HEIGHT}" xmlns="http://www.w3.org/2000/svg" '
        f'font-family="ui-monospace, SFMono-Regular, Menlo, monospace">'
    )

    if not STATIC:
        parts.append("""
        <style>
          @keyframes rowIn {
            from { opacity: 0; transform: translateX(-8px); }
            to   { opacity: 1; transform: translateX(0); }
          }
          .row { opacity: 0; animation: rowIn 0.45s ease-out forwards; }
        </style>
        """)

    # Card background + border
    parts.append(
        f'<rect x="0.5" y="0.5" width="{WIDTH - 1}" height="{HEIGHT - 1}" rx="8" ry="8" '
        f'fill="{BG}" stroke="{BORDER}"/>'
    )

    # Title bar
    parts.append(f'<rect x="0.5" y="0.5" width="{WIDTH - 1}" height="{TITLEBAR_H}" rx="8" ry="8" fill="#161b22"/>')
    parts.append(f'<rect x="0.5" y="{TITLEBAR_H - 8}" width="{WIDTH - 1}" height="8" fill="#161b22"/>')
    for i, color in enumerate(DOT_COLORS):
        cx = PAD_X + i * 18
        parts.append(f'<circle cx="{cx}" cy="{TITLEBAR_H / 2}" r="5" fill="{color}"/>')
    parts.append(
        f'<text x="{WIDTH / 2}" y="{TITLEBAR_H / 2 + 4}" text-anchor="middle" '
        f'font-size="12" fill="#8b949e">{TITLE}</text>'
    )

    # Key/value rows (value may span multiple lines)
    for i, (label, lines, y) in enumerate(row_layout):
        style = row_style(i)
        cls = "" if STATIC else 'class="row"'
        parts.append(f'<g {cls} style="{style}">')
        parts.append(
            f'<text x="{PAD_X}" y="{y}" font-size="13" font-weight="bold" fill="{LABEL_COLOR}">{label}:</text>'
        )
        for li, line in enumerate(lines):
            line_y = y + LABEL_TO_VALUE + li * VALUE_LINE_H
            parts.append(f'<text x="{PAD_X}" y="{line_y}" font-size="12" fill="{VALUE_COLOR}">{line}</text>')
        parts.append("</g>")

    parts.append("</svg>")

    with open(OUTPUT_PATH, "w") as f:
        f.write("\n".join(parts))

    print(f"Wrote {OUTPUT_PATH} ({WIDTH}x{HEIGHT}){' [static]' if STATIC else ''}")


if __name__ == "__main__":
    main()