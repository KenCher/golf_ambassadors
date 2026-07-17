#!/usr/bin/env python3
"""
compare_engines.py — run both the local and watsonx engines on a patch
and print the narratives side by side for comparison.

Usage (from kvm/ directory):
    python3 patchiq/compare_engines.py                          # all 3 fixtures
    python3 patchiq/compare_engines.py my_fix.patch             # a real patch
    git diff HEAD~1 | python3 patchiq/compare_engines.py -      # stdin

Outputs a structured side-by-side comparison to the terminal,
and saves an HTML file: compare_YYYYMMDD_HHMMSS.html
"""

import os, sys, types, textwrap, datetime

# ── 1. Load .env credentials (no dotenv dependency) ──────────────────────
_env = os.path.join(os.path.dirname(__file__), ".env")
if os.path.isfile(_env):
    for _line in open(_env):
        _line = _line.strip()
        if _line and not _line.startswith("#") and "=" in _line:
            k, v = _line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())

# ── 2. Bootstrap path ────────────────────────────────────────────────────
_here  = os.path.dirname(os.path.abspath(__file__))
_root  = os.path.dirname(_here)
if _root not in sys.path:
    sys.path.insert(0, _root)

import patchiq.analyzer as _local_mod
import patchiq.rules    as _rules_mod

# ── 3. Load wx engine from analyzer-wx.py without touching sys.modules ───
_wx_src = open(os.path.join(_here, "analyzer-wx.py")).read()
_wx_mod = types.ModuleType("patchiq_wx")
exec(compile(_wx_src, "analyzer-wx.py", "exec"), _wx_mod.__dict__)
_wx_mod.run_rules  = _rules_mod.run_rules
_wx_mod.WX_API_KEY = os.environ.get("WATSONX_API_KEY", "")
_wx_mod.WX_PROJECT = os.environ.get("WATSONX_PROJECT_ID", "")
_wx_mod._iam_token_cache.clear()   # clear any stale cache

local_review = _local_mod.review_patch
wx_review    = _wx_mod.review_patch

# ── 4. Input ─────────────────────────────────────────────────────────────
FIXTURES = [
    os.path.join(_here, "tests", "fixtures", "kernel.patch"),
    os.path.join(_here, "tests", "fixtures", "qemu.patch"),
    os.path.join(_here, "tests", "fixtures", "libvirt.patch"),
]

def get_diff() -> list[tuple[str, str]]:
    """Return [(label, raw_diff), ...]"""
    if len(sys.argv) > 1:
        arg = sys.argv[1]
        if arg == "-":
            return [("stdin", sys.stdin.read())]
        if os.path.isfile(arg):
            return [(os.path.basename(arg), open(arg).read())]
        print(f"File not found: {arg}", file=sys.stderr)
        sys.exit(1)
    # default: all 3 fixtures
    return [(os.path.basename(f), open(f).read()) for f in FIXTURES]

# ── 5. ANSI helpers ──────────────────────────────────────────────────────
_BOLD  = "\033[1m"
_DIM   = "\033[2m"
_CYAN  = "\033[96m"
_GREEN = "\033[92m"
_AMBER = "\033[93m"
_RED   = "\033[91m"
_RESET = "\033[0m"
_W     = 78  # column width per engine

def _wrap(text: str, width: int = _W - 4) -> list[str]:
    return textwrap.wrap(text, width) or [""]

def _sev_colour(sev: str) -> str:
    return {"error": _RED, "warning": _AMBER, "info": _CYAN}.get(sev, "")

def _print_side_by_side(left_lines: list[str], right_lines: list[str]) -> None:
    max_rows = max(len(left_lines), len(right_lines))
    for i in range(max_rows):
        l = left_lines[i]  if i < len(left_lines)  else ""
        r = right_lines[i] if i < len(right_lines) else ""
        print(f"  {l:<{_W}}  │  {r}")

# ── 6. Main comparison ───────────────────────────────────────────────────
def compare(label: str, raw: str) -> dict:
    print(f"\n{'═'*(_W*2+8)}")
    print(f"  {_BOLD}Patch: {label}{_RESET}")
    print(f"{'═'*(_W*2+8)}")

    print(f"\n  {_DIM}Running local engine...{_RESET}", end="", flush=True)
    lr = local_review(raw)
    print(f" done ({lr.score}/100)")

    wx_available = bool(_wx_mod.WX_API_KEY and _wx_mod.WX_PROJECT)
    if wx_available:
        print(f"  {_DIM}Calling watsonx Granite (may take ~15s)...{_RESET}", end="", flush=True)
    else:
        print(f"  {_DIM}watsonx: credentials not set — showing fallback{_RESET}", end="", flush=True)
    wr = wx_review(raw)
    print(f" done ({wr.score}/100)")

    # ── Scores
    print(f"\n  {'─'*(_W*2+8)}")
    lsc = f"{_GREEN if lr.score>=80 else _AMBER if lr.score>=60 else _RED}{lr.score}/100{_RESET}"
    wsc = f"{_GREEN if wr.score>=80 else _AMBER if wr.score>=60 else _RED}{wr.score}/100{_RESET}"
    print(f"  {_BOLD}{'LOCAL ENGINE':^{_W}}{_RESET}  │  {_BOLD}{'WATSONX GRANITE':^{_W}}{_RESET}")
    print(f"  {'Score: '+lsc:^{_W+10}}  │  {'Score: '+wsc:^{_W+10}}")
    print(f"  {'─'*(_W*2+8)}")

    # ── Findings (identical in both, just confirm)
    assert lr.findings == wr.findings or len(lr.findings)==len(wr.findings), \
        "Findings differ — rule engine mismatch"
    print(f"\n  {_BOLD}FINDINGS ({len(lr.findings)}) — identical in both editions{_RESET}")
    for f in lr.findings:
        c = _sev_colour(f.severity)
        icon = {"error":"🔴","warning":"🟡","info":"🔵"}.get(f.severity,"⚪")
        print(f"  {icon} [{f.rule_id}] {f.message[:100]}")

    # ── Narrative comparison
    print(f"\n  {'─'*(_W*2+8)}")
    print(f"  {_BOLD}{'SUMMARY':^{_W}}{_RESET}  │  {_BOLD}{'SUMMARY':^{_W}}{_RESET}")
    print(f"  {'─'*(_W*2+8)}")
    ll = _wrap(lr.ai_summary)
    rl = _wrap(wr.ai_summary)
    _print_side_by_side(ll, rl)

    # ── Suggestions
    print(f"\n  {_BOLD}SUGGESTIONS{_RESET}")
    print(f"  {'─'*(_W*2+8)}")
    max_s = max(len(lr.ai_suggestions), len(wr.ai_suggestions))
    for i in range(max_s):
        ls = lr.ai_suggestions[i] if i < len(lr.ai_suggestions) else "(none)"
        ws = wr.ai_suggestions[i] if i < len(wr.ai_suggestions) else "(none)"
        ll = _wrap(f"{i+1}. {ls}")
        rl = _wrap(f"{i+1}. {ws}")
        _print_side_by_side(ll, rl)
        if i < max_s - 1:
            print()

    return {
        "label":    label,
        "score":    lr.score,
        "findings": [(f.rule_id, f.severity, f.message) for f in lr.findings],
        "local":    {"summary": lr.ai_summary, "suggestions": lr.ai_suggestions},
        "wx":       {"summary": wr.ai_summary, "suggestions": wr.ai_suggestions},
    }

# ── 7. HTML report generator ─────────────────────────────────────────────
_HTML_HEAD = (
    "<!DOCTYPE html>\n"
    "<html lang=\'en\'><head><meta charset=\'UTF-8\'>\n"
    "<title>PatchIQ Engine Comparison</title>\n"
    "<style>\n"
    "body{font-family:-apple-system,\'Segoe UI\',system-ui,sans-serif;font-size:13px;"
    "line-height:1.6;max-width:1100px;margin:0 auto;padding:24px 20px 48px;color:#1f2328}\n"
    "h1{font-size:20px;font-weight:700;margin-bottom:4px}\n"
    ".sub{color:#57606a;font-size:11px;margin-bottom:24px}\n"
    ".patch-section{margin-bottom:36px;border:1px solid #e5e7eb;border-radius:6px;overflow:hidden}\n"
    ".patch-header{background:#1f2328;color:#fff;padding:10px 16px;font-size:14px;font-weight:700}\n"
    ".score-row{display:flex;gap:12px;padding:10px 16px;background:#f7f8fa;border-bottom:1px solid #e5e7eb}\n"
    ".score-chip{border-radius:12px;padding:3px 12px;font-size:12px;font-weight:700;border:1.5px solid}\n"
    ".sc-ok{background:#f0fdf4;border-color:#86efac;color:#14532d}\n"
    ".sc-warn{background:#fffbeb;border-color:#fcd34d;color:#78350f}\n"
    ".sc-err{background:#fff0f0;border-color:#fca5a5;color:#991b1b}\n"
    ".findings{padding:10px 16px;border-bottom:1px solid #e5e7eb}\n"
    ".findings h3{font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:.6px;color:#57606a;margin:0 0 6px}\n"
    ".finding{font-size:12px;margin-bottom:3px}\n"
    ".compare-grid{display:grid;grid-template-columns:1fr 1fr;gap:0}\n"
    ".col{padding:12px 16px}\n"
    ".col:first-child{border-right:2px solid #e5e7eb}\n"
    ".col-header{font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:.6px;"
    "margin-bottom:8px;padding-bottom:4px;border-bottom:1px solid #e5e7eb}\n"
    ".col-header.local{color:#16a34a}\n"
    ".col-header.wx{color:#3b82d4}\n"
    ".summary{font-size:13px;margin-bottom:10px;background:#f7f8fa;padding:8px 10px;"
    "border-radius:4px;border:1px solid #e5e7eb}\n"
    ".sug{font-size:12px;margin-bottom:4px;padding-left:14px;text-indent:-14px}\n"
    "footer{margin-top:36px;padding-top:12px;border-top:1px solid #e5e7eb;"
    "text-align:center;font-size:11px;color:#8b949e}\n"
    "</style></head><body>\n"
    "<h1>PatchIQ &mdash; Engine Comparison Report</h1>\n"
    "<p class=\'sub\'>Local heuristic vs watsonx Granite (ibm/granite-3-8b-instruct) &middot; %s</p>\n"
)

def _sc(score: int) -> str:
    cls = "sc-ok" if score >= 80 else "sc-warn" if score >= 60 else "sc-err"
    return f'<span class="score-chip {cls}">{score}/100</span>'

def build_html(results: list[dict]) -> str:
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    parts = [_HTML_HEAD % ts]
    sev_icon = {"error": "🔴", "warning": "🟡", "info": "🔵"}
    for r in results:
        findings_html = "\n".join(
            f'<div class="finding">{sev_icon.get(sev,"⚪")} [{rid}] {msg[:120]}</div>'
            for rid, sev, msg in r["findings"]
        ) or "<em>No findings</em>"
        sugs_l = "\n".join(
            f'<div class="sug">{i+1}. {s}</div>'
            for i, s in enumerate(r["local"]["suggestions"])
        ) or "<em>No suggestions</em>"
        sugs_w = "\n".join(
            f'<div class="sug">{i+1}. {s}</div>'
            for i, s in enumerate(r["wx"]["suggestions"])
        ) or "<em>No suggestions</em>"
        parts.append(f"""
<div class="patch-section">
  <div class="patch-header">{r['label']}</div>
  <div class="score-row">
    <strong>Score (both editions identical):</strong> {_sc(r['score'])}
    <strong>Findings:</strong> <span class="score-chip" style="background:#f7f8fa;border-color:#d0d7de;color:#1f2328">{len(r['findings'])}</span>
  </div>
  <div class="findings"><h3>Style Findings — identical in both editions</h3>{findings_html}</div>
  <div class="compare-grid">
    <div class="col">
      <div class="col-header local">🟢 Local Engine (offline, instant)</div>
      <div class="summary">{r['local']['summary']}</div>
      {sugs_l}
    </div>
    <div class="col">
      <div class="col-header wx">🔵 watsonx Granite (ibm/granite-3-8b-instruct)</div>
      <div class="summary">{r['wx']['summary']}</div>
      {sugs_w}
    </div>
  </div>
</div>""")
    parts.append("<footer>Made with IBM Bob</footer></body></html>")
    return "\n".join(parts)

# ── 8. Run ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    diffs   = get_diff()
    results = []

    print(f"\n  {'─'*(_W*2+8)}")
    print(f"  PatchIQ Engine Comparison")
    print(f"  Local engine  : {'✅ ready'}")
    cred_status = "✅ API key set" if _wx_mod.WX_API_KEY else "⚠️  no credentials (will show fallback)"
    print(f"  watsonx engine: {cred_status}")
    print(f"  Patches       : {[l for l,_ in diffs]}")
    print(f"  {'─'*(_W*2+8)}")

    for label, raw in diffs:
        r = compare(label, raw)
        results.append(r)

    ts_str  = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    html_out = f"patchiq_compare_{ts_str}.html"
    html_path = os.path.join(_root, html_out)
    open(html_path, "w").write(build_html(results))

    print(f"\n{'═'*(_W*2+8)}")
    print(f"  ✅  Comparison complete")
    print(f"  📄  HTML report: {html_out}")
    import platform
    if platform.system() == "Darwin":
        import subprocess
        ans = input("  🌐  Open in browser? (y/n) ").strip().lower()
        if ans == "y":
            subprocess.run(["open", html_path])
