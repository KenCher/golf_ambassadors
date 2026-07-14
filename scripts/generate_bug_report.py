#!/usr/bin/env python3
"""
generate_bug_report.py
Fetches open Bugzilla bugs for a list of team members and renders
a self-contained HTML dashboard into ./output/index.html
"""

import os
import json
import datetime
import requests
from collections import defaultdict

# ---------------------------------------------------------------------------
# Config from environment variables
# ---------------------------------------------------------------------------
BUGZILLA_URL = os.environ["BUGZILLA_URL"].rstrip("/")   # e.g. https://bugzilla.linux.ibm.com
API_KEY      = os.environ.get("BUGZILLA_API_KEY", "")
TEAM_EMAILS  = [e.strip() for e in os.environ["TEAM_EMAILS"].split(",") if e.strip()]

OUTPUT_DIR  = "output"
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "index.html")

# ---------------------------------------------------------------------------
# Fetch bugs
# ---------------------------------------------------------------------------
def fetch_bugs_for_email(email: str) -> list[dict]:
    params = {
        "assigned_to": email,
        "status":      ["UNCONFIRMED", "NEW", "ASSIGNED", "REOPENED"],
        "limit":       500,
    }
    if API_KEY:
        params["api_key"] = API_KEY
    resp = requests.get(f"{BUGZILLA_URL}/rest/bug", params=params, timeout=30)
    resp.raise_for_status()
    return resp.json().get("bugs", [])


def fetch_all_bugs() -> list[dict]:
    seen = set()
    bugs = []
    for email in TEAM_EMAILS:
        for bug in fetch_bugs_for_email(email):
            if bug["id"] not in seen:
                seen.add(bug["id"])
                bugs.append(bug)
    bugs.sort(key=lambda b: b.get("priority", "P9"))
    return bugs


# ---------------------------------------------------------------------------
# HTML rendering
# ---------------------------------------------------------------------------
CSS = """
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
body {
  font-family: -apple-system, "Segoe UI", system-ui, sans-serif;
  font-size: 14px; line-height: 1.6; color: #1f2328;
  background: #f7f8fa; padding: 24px 16px 48px;
}
.container { max-width: 760px; margin: 0 auto; }
h1 { font-size: 20px; font-weight: 600; margin-bottom: 4px; }
.subtitle { color: #57606a; font-size: 13px; margin-bottom: 24px; }
.stats { display: grid; grid-template-columns: repeat(4,1fr); gap: 12px; margin-bottom: 24px; }
.stat-card { background:#fff; border:1px solid #e5e7eb; border-radius:6px; padding:14px 16px; }
.stat-card .value { font-size:28px; font-weight:700; line-height:1.2; }
.stat-card .label { font-size:12px; color:#57606a; margin-top:2px; }
.p2 .value { color:#c0392b; } .p3 .value { color:#e67e22; }
.section-title { font-size:13px; font-weight:600; text-transform:uppercase;
  letter-spacing:.05em; color:#57606a; margin: 24px 0 8px; }
.bar-chart { display:flex; flex-direction:column; gap:8px; }
.bar-row { display:flex; align-items:center; gap:10px; }
.bar-label { width:160px; font-size:13px; white-space:nowrap; overflow:hidden;
  text-overflow:ellipsis; flex-shrink:0; }
.bar-track { flex:1; background:#e5e7eb; border-radius:3px; height:16px; overflow:hidden; }
.bar-fill { height:100%; border-radius:3px; background:#3b82d4; }
.bar-fill.alt { background:#7c5cd8; }
.bar-count { font-size:12px; color:#57606a; width:20px; text-align:right; flex-shrink:0; }
.card { background:#fff; border:1px solid #e5e7eb; border-radius:6px;
  overflow:hidden; margin-bottom:16px; }
.chart-card { padding:16px; }
table { width:100%; border-collapse:collapse; }
thead th { background:#f7f8fa; font-size:12px; font-weight:600; text-transform:uppercase;
  letter-spacing:.04em; color:#57606a; padding:9px 12px; text-align:left;
  border-bottom:1px solid #e5e7eb; }
tbody tr { border-bottom:1px solid #f0f1f3; }
tbody tr:last-child { border-bottom:none; }
tbody td { padding:9px 12px; font-size:13px; vertical-align:top; }
.bug-id a { color:#3b82d4; text-decoration:none; font-weight:600; font-size:12px; }
.badge { display:inline-block; padding:1px 7px; border-radius:10px; font-size:11px;
  font-weight:600; white-space:nowrap; }
.badge-p2 { background:#fde8e8; color:#c0392b; }
.badge-p3 { background:#fef3e2; color:#b7770d; }
.badge-other { background:#f0f1f3; color:#57606a; }
.tag { display:inline-block; background:#f0f1f3; color:#57606a;
  font-size:11px; padding:1px 6px; border-radius:4px; }
.assignee { font-size:12px; color:#57606a; }
.summary-col { max-width:280px; }
.footer { margin-top:40px; padding-top:12px; border-top:1px solid #e5e7eb;
  text-align:center; font-size:12px; color:#57606a; }
"""


def priority_badge(priority: str) -> str:
    cls = {"P2": "badge-p2", "P3": "badge-p3"}.get(priority, "badge-other")
    return f'<span class="badge {cls}">{priority}</span>'


def short_name(email: str) -> str:
    return email.split("@")[0]


def bar_rows(counts: dict[str, int], max_val: int, use_alt: bool = False) -> str:
    html = []
    fill_cls = "bar-fill alt" if use_alt else "bar-fill"
    for label, count in sorted(counts.items(), key=lambda x: -x[1]):
        pct = round(count / max_val * 100)
        html.append(
            f'<div class="bar-row">'
            f'  <div class="bar-label">{label}</div>'
            f'  <div class="bar-track"><div class="{fill_cls}" style="width:{pct}%"></div></div>'
            f'  <div class="bar-count">{count}</div>'
            f'</div>'
        )
    return "\n".join(html)


def render_html(bugs: list[dict]) -> str:
    generated = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    total = len(bugs)
    p2 = sum(1 for b in bugs if b.get("priority") == "P2")
    p3 = sum(1 for b in bugs if b.get("priority") == "P3")

    # Aggregate
    by_assignee: dict[str, int] = defaultdict(int)
    by_component: dict[str, int] = defaultdict(int)
    for b in bugs:
        by_assignee[short_name(b.get("assigned_to", "unknown"))] += 1
        by_component[b.get("component", "unknown")] += 1

    max_a = max(by_assignee.values(), default=1)
    max_c = max(by_component.values(), default=1)

    # Bug table rows
    bug_rows_html = []
    base_url = BUGZILLA_URL
    for b in bugs:
        bid      = b["id"]
        summary  = b.get("summary", "")[:90] + ("…" if len(b.get("summary","")) > 90 else "")
        priority = b.get("priority", "—")
        component = b.get("component", "—")
        assignee  = short_name(b.get("assigned_to", "—"))
        bug_rows_html.append(
            f'<tr>'
            f'  <td class="bug-id"><a href="{base_url}/show_bug.cgi?id={bid}">#{bid}</a></td>'
            f'  <td class="summary-col">{summary}</td>'
            f'  <td>{priority_badge(priority)}</td>'
            f'  <td><span class="tag">{component}</span></td>'
            f'  <td class="assignee">{assignee}</td>'
            f'</tr>'
        )

    assignees_count = len(by_assignee)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Team Bugzilla Dashboard</title>
<style>{CSS}</style>
</head>
<body>
<div class="container">
  <h1>Team Bugzilla Dashboard</h1>
  <p class="subtitle">Open bugs &middot; Generated {generated}</p>

  <div class="stats">
    <div class="stat-card">
      <div class="value">{total}</div>
      <div class="label">Total Open Bugs</div>
    </div>
    <div class="stat-card p2">
      <div class="value">{p2}</div>
      <div class="label">Priority P2</div>
    </div>
    <div class="stat-card p3">
      <div class="value">{p3}</div>
      <div class="label">Priority P3</div>
    </div>
    <div class="stat-card">
      <div class="value">{assignees_count}</div>
      <div class="label">Assignees</div>
    </div>
  </div>

  <div class="section-title">Bugs by Assignee</div>
  <div class="card chart-card">
    <div class="bar-chart">
      {bar_rows(by_assignee, max_a)}
    </div>
  </div>

  <div class="section-title">Bugs by Component</div>
  <div class="card chart-card">
    <div class="bar-chart">
      {bar_rows(by_component, max_c, use_alt=True)}
    </div>
  </div>

  <div class="section-title">All Open Bugs</div>
  <div class="card">
    <table>
      <thead>
        <tr>
          <th>Bug #</th><th>Summary</th><th>Priority</th><th>Component</th><th>Assignee</th>
        </tr>
      </thead>
      <tbody>
        {"".join(bug_rows_html)}
      </tbody>
    </table>
  </div>

  <div class="footer">Made with IBM Bob</div>
</div>
</body>
</html>"""


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    print(f"Fetching bugs for {len(TEAM_EMAILS)} team members …")
    bugs = fetch_all_bugs()
    print(f"Found {len(bugs)} open bugs.")
    html = render_html(bugs)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Report written to {OUTPUT_FILE}")
