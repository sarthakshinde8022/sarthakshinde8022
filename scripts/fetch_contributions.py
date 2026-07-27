#!/usr/bin/env python3
"""
Scrape the public contribution calendar for GITHUB_USERNAME and write
data/contributions.json with raw daily counts plus derived stats
(current streak, longest streak, best day, monthly totals).

No GraphQL API, no personal access token — this hits the same public
HTML fragment GitHub's own profile page uses:
    https://github.com/users/<username>/contributions
"""
import json
import os
import re
import sys
from collections import defaultdict
from datetime import date, datetime, timezone

import requests
from bs4 import BeautifulSoup

# --- config -----------------------------------------------------------
GITHUB_USERNAME = os.environ.get("GITHUB_USERNAME", "YOUR_USERNAME_HERE")
OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "contributions.json")
CONTRIB_URL = "https://github.com/users/{username}/contributions"
# -----------------------------------------------------------------------

COUNT_RE = re.compile(r"^(No|\d+)\s+contributions?", re.IGNORECASE)


def fetch_html(username: str) -> str:
    url = CONTRIB_URL.format(username=username)
    resp = requests.get(
        url,
        headers={"User-Agent": "Mozilla/5.0 (profile-readme-bot)"},
        timeout=20,
    )
    resp.raise_for_status()
    return resp.text


def parse_days(html: str) -> list[dict]:
    """Return a list of {date, count, level} sorted oldest -> newest."""
    soup = BeautifulSoup(html, "html.parser")

    # Every day cell is a <td class="ContributionCalendar-day" data-date=... data-level=... id=...>
    cells = soup.select("td.ContributionCalendar-day[data-date]")
    if not cells:
        raise RuntimeError(
            "No contribution cells found — GitHub may have changed its markup, "
            "or the username has no public contribution graph."
        )

    # Tooltips carry the human-readable count, keyed by the day cell's id
    # via the tool-tip's `for` attribute: "5 contributions on July 28th."
    tooltip_by_id = {}
    for tip in soup.select("tool-tip[for]"):
        tooltip_by_id[tip.get("for")] = tip.get_text(strip=True)

    days = []
    for cell in cells:
        d = cell["data-date"]
        level = int(cell.get("data-level", 0))
        cell_id = cell.get("id")
        count = None
        tip_text = tooltip_by_id.get(cell_id, "")
        m = COUNT_RE.match(tip_text)
        if m:
            count = 0 if m.group(1).lower() == "no" else int(m.group(1))
        if count is None:
            # Fallback: no tooltip found, estimate from level (0 = 0 contributions)
            count = 0 if level == 0 else level
        days.append({"date": d, "count": count, "level": level})

    days.sort(key=lambda x: x["date"])
    return days


def compute_stats(days: list[dict]) -> dict:
    total = sum(d["count"] for d in days)

    # Longest streak + current streak (consecutive days with count > 0)
    longest = current = 0
    running = 0
    today = date.today()
    for d in days:
        if d["count"] > 0:
            running += 1
            longest = max(longest, running)
        else:
            running = 0
    # current streak counts back from the most recent day that has data
    for d in reversed(days):
        day_date = datetime.strptime(d["date"], "%Y-%m-%d").date()
        if day_date > today:
            continue
        if d["count"] > 0:
            current += 1
        else:
            break

    best_day = max(days, key=lambda d: d["count"], default=None)

    monthly = defaultdict(int)
    for d in days:
        month_key = d["date"][:7]  # YYYY-MM
        monthly[d["count"] and month_key or month_key] += d["count"]

    return {
        "total_contributions": total,
        "current_streak": current,
        "longest_streak": longest,
        "best_day": best_day,
        "monthly_totals": dict(sorted(monthly.items())),
    }


def main():
    username = GITHUB_USERNAME
    if len(sys.argv) > 1:
        username = sys.argv[1]
    if username == "YOUR_USERNAME_HERE":
        print("Set GITHUB_USERNAME env var or pass username as first arg.", file=sys.stderr)
        sys.exit(1)

    html = fetch_html(username)
    days = parse_days(html)
    stats = compute_stats(days)

    payload = {
        "username": username,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "days": days,
        "stats": stats,
    }

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, "w") as f:
        json.dump(payload, f, indent=2)

    print(f"Wrote {OUTPUT_PATH}: {len(days)} days, {stats['total_contributions']} total contributions")


if __name__ == "__main__":
    main()
