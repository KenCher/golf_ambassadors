"""
PatchIQ — HTML report generator.
Produces a self-contained HTML page from a ReviewResult.
"""

from datetime import datetime
from typing import Optional
from patchiq.analyzer import ReviewResult


# Severity colour map
_SEV_STYLE = {
    "error":   ("🔴", "#f8d7da", "#721c24"),
    "warning": ("🟡", "#fff3cd", "#856404"),
    "info":    ("🔵", "#d1ecf1", "#0c5460"),
}

_LAYER_BADGE = {
    "kernel":  ("#2d6a4f", "#d8f3dc"),
    "qemu":    ("#1d3557", "#a8dadc"),
    "libvirt": ("#6d2b6d", "#e8d5f5"),
    "unknown": ("#555",    "#eee"),
}


def _score_colour(score: int) -> str:
    if score >= 80:
        return "#155724"
    if score >= 50:
        return "#856404"
    return "#721c24"


def _score_bg(score: int) -> str:
    if score >= 80:
        return "#d4edda"
    if score >= 50:
        return "#fff3cd"
    return "#f8d7da"


def _badge(layer: str) -> str:
    fg, bg = _LAYER_BADGE.get(layer, _LAYER_BADGE["unknown"])
    return (
        f'<span style="background:{bg};color:{fg};padding:2px 8px;'
        f'border-radius:10px;font-size:0.8em;font-weight:600;">{layer}</span>'
    )


def generate_html(result: ReviewResult, output_path: Optional[str] = None) -> str:
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    score = result.score
    sc_fg = _score_colour(score)
    sc_bg = _score_bg(score)

    # ── findings table rows ────────────────────────────────────────────────
    finding_rows = ""
    if result.findings:
        for f in result.findings:
            icon, bg, fg = _SEV_STYLE.get(f.severity, ("⚪", "#eee", "#333"))
            line_html = f'<code style="font-size:0.75em;color:#555;">{f.line[:90].strip()}</code>' if f.line else ""
            finding_rows += f"""
            <tr style="background:{bg};">
              <td style="padding:8px 12px;color:{fg};font-weight:600;">{icon} {f.severity.upper()}</td>
              <td style="padding:8px 12px;">{_badge(f.layer)}</td>
              <td style="padding:8px 12px;font-family:monospace;font-size:0.85em;color:#333;">{f.rule_id}</td>
              <td style="padding:8px 12px;color:#1f2328;">{f.message}<br>{line_html}</td>
            </tr>"""
    else:
        finding_rows = """
            <tr>
              <td colspan="4" style="padding:16px;text-align:center;color:#155724;font-weight:600;">
                ✅ No style issues found
              </td>
            </tr>"""

    # ── AI suggestions ─────────────────────────────────────────────────────
    suggestions_html = ""
    if result.ai_suggestions:
        items = "".join(f"<li style='margin-bottom:6px;'>{s}</li>" for s in result.ai_suggestions)
        suggestions_html = f"<ul style='margin:0;padding-left:20px;'>{items}</ul>"
    else:
        suggestions_html = "<p style='color:#57606a;'>No additional suggestions.</p>"

    # ── file list ──────────────────────────────────────────────────────────
    file_rows = ""
    for fd in result.files:
        added   = sum(1 for l in fd.lines if l.startswith('+') and not l.startswith('+++'))
        removed = sum(1 for l in fd.lines if l.startswith('-') and not l.startswith('---'))
        file_rows += f"""
          <tr>
            <td style="padding:8px 12px;font-family:monospace;font-size:0.85em;">{fd.path}</td>
            <td style="padding:8px 12px;">{_badge(fd.layer)}</td>
            <td style="padding:8px 12px;color:#155724;font-weight:600;">+{added}</td>
            <td style="padding:8px 12px;color:#721c24;font-weight:600;">-{removed}</td>
          </tr>"""

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>PatchIQ Review — {result.patch_subject[:60]}</title>
  <style>
    * {{ margin:0; padding:0; box-sizing:border-box; }}
    body {{ font-family:-apple-system,"Segoe UI",system-ui,sans-serif; font-size:14px;
            background:#f0f2f5; padding:24px; color:#1f2328; line-height:1.6; }}
    .container {{ max-width:960px; margin:0 auto; }}
    .card {{ background:#fff; border-radius:8px; border:1px solid #e5e7eb;
             margin-bottom:20px; overflow:hidden; }}
    .card-header {{ background:#1d3557; color:#fff; padding:14px 20px;
                    font-size:1em; font-weight:600; }}
    .card-body  {{ padding:20px; }}
    table {{ width:100%; border-collapse:collapse; }}
    th {{ background:#f7f8fa; padding:10px 12px; text-align:left;
          font-weight:600; color:#57606a; border-bottom:2px solid #e5e7eb; }}
    td {{ border-bottom:1px solid #e5e7eb; vertical-align:top; }}
    .score-badge {{ display:inline-block; padding:6px 20px; border-radius:20px;
                    font-size:2em; font-weight:700;
                    background:{sc_bg}; color:{sc_fg}; }}
    footer {{ text-align:center; font-size:11px; color:#57606a;
              margin-top:24px; padding-top:12px; border-top:1px solid #e5e7eb; }}
  </style>
</head>
<body>
<div class="container">

  <!-- Header -->
  <div class="card">
    <div style="background:linear-gradient(135deg,#1d3557,#457b9d);color:#fff;padding:28px 28px 20px;">
      <div style="font-size:0.85em;opacity:0.8;margin-bottom:4px;">PatchIQ — AI-powered patch review</div>
      <h1 style="font-size:1.4em;font-weight:700;margin-bottom:12px;">{result.patch_subject}</h1>
      <div style="display:flex;align-items:center;gap:20px;flex-wrap:wrap;">
        <div>
          <div style="font-size:0.75em;opacity:0.75;">PATCH SCORE</div>
          <span class="score-badge">{score}/100</span>
        </div>
        <div>
          <div style="font-size:0.75em;opacity:0.75;">FILES CHANGED</div>
          <div style="font-size:1.5em;font-weight:700;">{len(result.files)}</div>
        </div>
        <div>
          <div style="font-size:0.75em;opacity:0.75;">FINDINGS</div>
          <div style="font-size:1.5em;font-weight:700;">{len(result.findings)}</div>
        </div>
        <div style="margin-left:auto;font-size:0.8em;opacity:0.75;">Generated: {now}</div>
      </div>
    </div>
  </div>

  <!-- AI Summary -->
  <div class="card">
    <div class="card-header">🤖 AI Review Summary (watsonx)</div>
    <div class="card-body">
      <p style="margin-bottom:14px;color:#1f2328;">{result.ai_summary}</p>
      <div style="font-weight:600;margin-bottom:8px;color:#1d3557;">Suggestions</div>
      {suggestions_html}
    </div>
  </div>

  <!-- Style findings -->
  <div class="card">
    <div class="card-header">🔍 Style &amp; Correctness Findings ({len(result.findings)})</div>
    <div class="card-body" style="padding:0;">
      <table>
        <thead>
          <tr>
            <th style="width:12%;">Severity</th>
            <th style="width:12%;">Layer</th>
            <th style="width:10%;">Rule</th>
            <th>Detail</th>
          </tr>
        </thead>
        <tbody>{finding_rows}</tbody>
      </table>
    </div>
  </div>

  <!-- Files changed -->
  <div class="card">
    <div class="card-header">📂 Files Changed</div>
    <div class="card-body" style="padding:0;">
      <table>
        <thead>
          <tr>
            <th>Path</th><th style="width:12%;">Layer</th>
            <th style="width:8%;">Added</th><th style="width:8%;">Removed</th>
          </tr>
        </thead>
        <tbody>{file_rows}</tbody>
      </table>
    </div>
  </div>

  <footer>Made with IBM Bob &nbsp;·&nbsp; PatchIQ — AI-powered review for the open source stack</footer>
</div>
</body>
</html>"""

    if output_path:
        with open(output_path, "w") as fh:
            fh.write(html)

    return html
