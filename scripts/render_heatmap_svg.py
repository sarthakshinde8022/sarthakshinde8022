#!/usr/bin/env python3
"""
Render data/contributions.json as a 53-week x 7-day calendar heatmap SVG.
Boxes reveal diagonally (line-after-line slide-down) once on load, then
freeze — no looping "glow". Includes a Less->More legend and a stats
footer line.
"""
import json
import os
from datetime import datetime

DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "contributions.json")
OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "..", "contrib-heatmap.svg")

# none -> brightest (level 5 is a custom neon top end for the user's own best days)
PALETTE = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353", "#69f0a0"]

BOX = 11
GAP = 3
CELL = BOX + GAP
LEFT_PAD = 28       # room for weekday labels
TOP_PAD = 22         # room for month labels
RIGHT_PAD = 10
BOTTOM_PAD = 34      # room for legend + footer

MONTH_ABBR = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
              "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def level_for(count: int, nonzero_sorted: list[int]) -> int:
    """GitHub gives us level 0-4 already; we add a custom level 5 for a
    user's own top ~5% days so their best days get the neon top end."""
    if count == 0:
        return 0
    if not nonzero_sorted:
        return 1
    idx = int(len(nonzero_sorted) * 0.95)
    threshold = nonzero_sorted[min(idx, len(nonzero_sorted) - 1)]
    if count >= threshold and count > 0:
        return 5
    # fall back to compressing into levels 1-4 by simple quantile
    idx25 = nonzero_sorted[int(len(nonzero_sorted) * 0.25)]
    idx50 = nonzero_sorted[int(len(nonzero_sorted) * 0.50)]
    idx75 = nonzero_sorted[int(len(nonzero_sorted) * 0.75)]
    if count <= idx25:
        return 1
    if count <= idx50:
        return 2
    if count <= idx75:
        return 3
    return 4


def build_weeks(days: list[dict]) -> list[list[dict | None]]:
    """Group days into weeks (columns), Sun-Sat (rows), matching GitHub's
    calendar layout. Pads the first/last week with None for missing days."""
    parsed = []
    for d in days:
        dt = datetime.strptime(d["date"], "%Y-%m-%d").date()
        parsed.append((dt, d))
    parsed.sort(key=lambda x: x[0])

    weeks: list[list[dict | None]] = []
    # GitHub weeks run Sun-Sat; pad the first week so day-of-week columns align.
    week: list[dict | None] = [None] * (parsed[0][0].isoweekday() % 7)
    for dt, d in parsed:
        dow = dt.isoweekday() % 7  # Sunday -> 0 ... Saturday -> 6
        if dow == 0 and week and any(c is not None for c in week):
            weeks.append(week)
            week = []
        while len(week) < dow:
            week.append(None)
        week.append(d)
        if len(week) == 7:
            weeks.append(week)
            week = []
    if week:
        while len(week) < 7:
            week.append(None)
        weeks.append(week)
    return weeks


def main():
    with open(DATA_PATH) as f:
        payload = json.load(f)

    days = payload["days"]
    stats = payload["stats"]
    weeks = build_weeks(days)

    nonzero_counts = sorted(d["count"] for d in days if d["count"] > 0)

    width = LEFT_PAD + len(weeks) * CELL + RIGHT_PAD
    height = TOP_PAD + 7 * CELL + BOTTOM_PAD

    svg_parts = []
    svg_parts.append(
        f'<svg viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg" '
        f'font-family="ui-monospace, SFMono-Regular, Menlo, monospace">'
    )

    svg_parts.append(f"""
    <style>
      rect.cell {{
        opacity: 0;
        transform: translateY(-6px);
        animation: slideIn 0.35s ease-out forwards;
      }}
      @keyframes slideIn {{
        from {{ opacity: 0; transform: translateY(-6px); }}
        to   {{ opacity: 1; transform: translateY(0); }}
      }}
      text {{ fill: #8b949e; font-size: 9px; }}
    </style>
    <rect width="{width}" height="{height}" fill="none"/>
    """)

    # Month labels: print a month abbreviation above the first week column
    # in which that month appears.
    last_month = None
    for week_idx, week in enumerate(weeks):
        for day in week:
            if day is None:
                continue
            dt = datetime.strptime(day["date"], "%Y-%m-%d").date()
            if dt.month != last_month:
                x = LEFT_PAD + week_idx * CELL
                svg_parts.append(f'<text x="{x}" y="{TOP_PAD - 8}">{MONTH_ABBR[dt.month - 1]}</text>')
                last_month = dt.month
            break

    # Weekday labels (Mon/Wed/Fri, GitHub-style, sparse to avoid clutter)
    weekday_labels = {1: "Mon", 3: "Wed", 5: "Fri"}
    for row, label in weekday_labels.items():
        y = TOP_PAD + row * CELL + BOX - 1
        svg_parts.append(f'<text x="0" y="{y}">{label}</text>')

    # Day cells, diagonal stagger by (week + row)
    max_diag = len(weeks) + 7
    for week_idx, week in enumerate(weeks):
        for row, day in enumerate(week):
            if day is None:
                continue
            x = LEFT_PAD + week_idx * CELL
            y = TOP_PAD + row * CELL
            lvl = level_for(day["count"], nonzero_counts)
            color = PALETTE[lvl]
            diag = week_idx + row
            delay = (diag / max_diag) * 1.4  # whole grid reveals over ~1.4s + 0.35s tail
            svg_parts.append(
                f'<rect class="cell" x="{x}" y="{y}" width="{BOX}" height="{BOX}" '
                f'rx="2" ry="2" fill="{color}" style="animation-delay:{delay:.2f}s">'
                f'<title>{day["count"]} contributions on {day["date"]}</title></rect>'
            )

    # Legend: Less [boxes] More
    legend_y = TOP_PAD + 7 * CELL + 16
    legend_x = LEFT_PAD
    svg_parts.append(f'<text x="{legend_x - 22}" y="{legend_y + 8}">Less</text>')
    lx = legend_x
    for lvl, color in enumerate(PALETTE):
        svg_parts.append(f'<rect x="{lx}" y="{legend_y}" width="{BOX}" height="{BOX}" rx="2" ry="2" fill="{color}"/>')
        lx += CELL
    svg_parts.append(f'<text x="{lx + 4}" y="{legend_y + 8}">More</text>')

    # Stats footer
    footer = (
        f'{stats["total_contributions"]:,} contributions in the last year   '
        f'\u00b7   longest streak {stats["longest_streak"]}d'
    )
    svg_parts.append(f'<text x="{legend_x}" y="{legend_y + 24}" font-size="10" fill="#c9d1d9">{footer}</text>')

    svg_parts.append("</svg>")

    with open(OUTPUT_PATH, "w") as f:
        f.write("\n".join(svg_parts))

    print(f"Wrote {OUTPUT_PATH} ({width}x{height}, {len(weeks)} weeks)")


if __name__ == "__main__":
    main()
