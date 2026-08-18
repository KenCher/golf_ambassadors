"""
CIIQ — CI Intelligence & Insight Query  (local edition)
Flask backend: rule-based root-cause analyser for KVM, QEMU, and libvirt CI failures.
No external API or credentials required.

Endpoints
---------
GET  /                          Serve the CIIQ UI
GET  /api/config                Return sanitised config
POST /api/analyse/<project>     Run local analysis for one project
POST /api/analyse/all           Run all three projects
POST /api/correlate             Run cross-project correlation
GET  /api/runs                  List available CI run dates from log dir
GET  /api/run/<date>/suites     Return suite names + log snippets for a date
GET  /api/history               Return session analysis history
DELETE /api/history             Clear session history

For the watsonx-backed variant see: app-wx.py
"""

import json
import os
import re
import logging
import subprocess
from datetime import datetime, timedelta
from functools import wraps

import yaml
from flask import Flask, jsonify, request, render_template, session
from flask_cors import CORS
from dotenv import load_dotenv

# ─────────────────────────────────────────────────────────────────────────────
#  Bootstrap
# ─────────────────────────────────────────────────────────────────────────────
load_dotenv()

BASE_DIR    = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(BASE_DIR, "config.yaml")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)
log = logging.getLogger("ciiq")


def _expand_env(value: str) -> str:
    """Replace ${VAR} patterns with environment variable values."""
    return re.sub(r"\$\{(\w+)\}", lambda m: os.environ.get(m.group(1), ""), value)


def load_config() -> dict:
    """Load and env-expand config.yaml."""
    with open(CONFIG_PATH) as f:
        raw = yaml.safe_load(f)

    def expand(obj):
        if isinstance(obj, str):
            return _expand_env(obj)
        if isinstance(obj, dict):
            return {k: expand(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [expand(i) for i in obj]
        return obj

    return expand(raw)


CFG = load_config()

app = Flask(__name__, template_folder="templates", static_folder="static")
app.secret_key = CFG.get("server", {}).get("secret_key") or os.urandom(32)
CORS(app)


# ─────────────────────────────────────────────────────────────────────────────
#  Local analysis engine  — no external API
# ─────────────────────────────────────────────────────────────────────────────

# Error patterns we scan for in log text
_ERROR_PATTERNS = [
    (re.compile(r'\bBUG:\s', re.IGNORECASE),        "kernel BUG"),
    (re.compile(r'\bKernel panic\b', re.IGNORECASE), "kernel panic"),
    (re.compile(r'\bOops\b'),                         "kernel Oops"),
    (re.compile(r'\bgeneral protection fault\b', re.IGNORECASE), "GPF"),
    (re.compile(r'\bsegfault\b|\bsegmentation fault\b', re.IGNORECASE), "segfault"),
    (re.compile(r'\bNULL pointer dereference\b', re.IGNORECASE), "NULL deref"),
    (re.compile(r'\buse-after-free\b', re.IGNORECASE), "use-after-free"),
    (re.compile(r'\bstack overflow\b', re.IGNORECASE), "stack overflow"),
    (re.compile(r'\bdeadlock\b', re.IGNORECASE),      "deadlock"),
    (re.compile(r'\bWARN_ON\b|\bWARNING:\s'),          "kernel WARNING"),
    (re.compile(r'\bTIMEOUT\b|\btimeout\b'),           "timeout"),
    (re.compile(r'\bFAIL\b|\bFAILED\b'),               "test FAIL"),
    (re.compile(r'\bERROR:\s|(?<!ci-)(?<!-)\berror:\s'), "ERROR"),
    (re.compile(r'\bAborted\b|\baborted\b'),            "abort"),
    (re.compile(r'\bAssertionError\b'),                "assertion"),
    (re.compile(r'\bNo such device\b', re.IGNORECASE), "device not found"),
    (re.compile(r'\bPermission denied\b', re.IGNORECASE), "permission denied"),
    (re.compile(r'\bInvalid argument\b', re.IGNORECASE), "EINVAL"),
    (re.compile(r'\bOut of memory\b|\bOOM\b', re.IGNORECASE), "OOM"),
    (re.compile(r'\bmigration failed\b', re.IGNORECASE), "migration failure"),
    # CI TAP infrastructure errors (from web UI failure reports)
    (re.compile(r'\bci-error:\s*test suite script failure\b', re.IGNORECASE), "ci-error: script failure"),
    (re.compile(r'\bci-error:\s*invalid tap\b', re.IGNORECASE),               "ci-error: invalid TAP"),
    (re.compile(r'\bci-error:\s*ssh connection error\b', re.IGNORECASE),      "ci-error: SSH failure"),
    (re.compile(r'\bci-error:\s*test suite timeout\b', re.IGNORECASE),        "ci-error: suite timeout"),
    (re.compile(r'\bci-error:\s*install test suite packages\b', re.IGNORECASE), "ci-error: pkg install"),
    (re.compile(r'\btimeout;\s*duration=\d+\b', re.IGNORECASE),               "test timeout"),
]

# Subsystem keywords for attribution
_SUBSYSTEM_PATTERNS = {
    "KVM core":       re.compile(r'\bkvm\b|\bKVM\b|\bSIE\b|\bvcpu\b'),
    "s390x arch":     re.compile(r'\bs390\b|\bs390x\b|\bz/VM\b'),
    "memory mgmt":    re.compile(r'\bgfn\b|\bpfn\b|\bsmmu\b|\bHugePage\b|\bpfault\b'),
    "VFIO":           re.compile(r'\bvfio\b|\bVFIO\b|\biommu\b'),
    "virtio":         re.compile(r'\bvirtio\b|\bvirtqueue\b'),
    "live migration": re.compile(r'\bmigrat\b|\blive mig\b', re.IGNORECASE),
    "CPU model":      re.compile(r'\bcpu model\b|\bcpuflags\b|\bfacility\b', re.IGNORECASE),
    "QMP/monitor":    re.compile(r'\bQMP\b|\bqmp\b|\bmonitor\b'),
    "libvirt driver": re.compile(r'\bvirDomain\b|\bqemuDomain\b|\bvirConnect\b'),
    "QEMU block":     re.compile(r'\bblkdev\b|\bblk_\b|\bqcow\b', re.IGNORECASE),
}

# Commit introducing patterns in git log
_COMMIT_RE = re.compile(
    r'^([0-9a-f]{7,40})\s+(.+)',
    re.MULTILINE,
)

# Category labels per suite category
_CATEGORY_LABELS = {
    "kernel": "kernel / KVM",
    "config": "configuration / boot",
    "test":   "test harness",
    "infra":  "CI infrastructure",
    "hw":     "hardware / bare-metal",
}

# Per-project expert context (no LLM needed)
_EXPERT_CONTEXT = {
    "kvm": (
        "KVM s390x uses the SIE (Start Interpretive Execution) mechanism. "
        "Intercept handling, VSIE, pfault, and protected virtualisation are key areas. "
        "State mutations must happen under vcpu->mutex or kvm->lock."
    ),
    "qemu": (
        "QEMU s390x uses KVM acceleration via KVM_SET_ONE_REG / KVM_GET_ONE_REG. "
        "CPU state serialisation, live migration streams, and machine type compatibility "
        "are the most common regression areas."
    ),
    "libvirt": (
        "libvirt communicates with QEMU via QMP. s390x domain configuration, "
        "virsh migrate, CPU model detection, and the QEMU driver state machine "
        "are common failure points."
    ),
}


# Strip TAP annotation prefix: [EDGK ][  3x  96d] → bare text
_TAP_ANNOTATION_RE = re.compile(r'^\[[A-Za-z \t]{0,20}\]\s*\[\s*\d+x\s*\d+d\]\s*', re.MULTILINE)


def _strip_tap_annotations(text: str) -> str:
    """Remove CI TAP annotation prefixes like '[E  K  ][  3x  96d] ' from log lines."""
    return _TAP_ANNOTATION_RE.sub('', text)


def _scan_log(text: str) -> dict:
    """Scan a single log blob and return structured findings."""
    # Strip TAP run-annotations before pattern matching so they don't interfere
    text = _strip_tap_annotations(text)
    hits: dict[str, int] = {}
    for pattern, label in _ERROR_PATTERNS:
        count = len(pattern.findall(text))
        if count:
            hits[label] = hits.get(label, 0) + count

    subsystems: list[str] = []
    for name, pat in _SUBSYSTEM_PATTERNS.items():
        if pat.search(text):
            subsystems.append(name)

    # Pull up to 3 representative error lines
    error_lines: list[str] = []
    for line in text.splitlines():
        if any(pat.search(line) for pat, _ in _ERROR_PATTERNS[:10]):  # top-10 are serious
            stripped = line.strip()
            if stripped and stripped not in error_lines:
                error_lines.append(stripped)
            if len(error_lines) >= 3:
                break

    return {"hits": hits, "subsystems": subsystems, "error_lines": error_lines}


def _extract_commits(git_log: str) -> list[dict]:
    """Parse git log lines into [{sha, subject}]."""
    results = []
    for m in _COMMIT_RE.finditer(git_log):
        results.append({"sha": m.group(1), "subject": m.group(2).strip()})
    return results[:10]   # cap at 10


def analyse_project(
    project: str,
    delta: dict,
    suite_logs: dict,
    run_date: str,
    run_id: str,
    suite_status: dict | None = None,
) -> str:
    """
    Produce a structured Markdown analysis for one project using only local
    heuristics — no external API.

    suite_status (optional): {suite_name: "PASS"|"FAIL"} from the UI badges.
    When provided, overrides the scan-based PASS/FAIL classification so that
    suites the user has marked PASS (e.g. hades-monolithic with old log content
    still in the textarea) are not incorrectly counted as failures.
    """
    expert_ctx = _EXPERT_CONTEXT.get(project, "")
    commits     = _extract_commits(delta.get("git_log", ""))
    diff_stat   = delta.get("git_diff_stat", "").strip()
    sha_good    = delta.get("sha_good", "(unknown)")
    sha_bad     = delta.get("sha_bad",  "(unknown)")

    # Aggregate scan results across all suites
    all_hits: dict[str, int] = {}
    all_subsystems: set[str] = set()
    all_error_lines: list[str] = []
    failing_suites: list[str] = []
    passing_suites: list[str] = []
    empty_suites: list[str] = []

    for suite, log_text in suite_logs.items():
        if not (log_text or "").strip():
            empty_suites.append(suite)
            continue
        # If caller supplied authoritative status badges, trust them over scan
        if suite_status and suite_status.get(suite) == "PASS":
            passing_suites.append(suite)
            continue
        scan = _scan_log(log_text)
        if suite_status and suite_status.get(suite) == "FAIL":
            # Marked FAIL by caller — always treat as failing even if scan is clean
            failing_suites.append(suite)
            for k, v in scan["hits"].items():
                all_hits[k] = all_hits.get(k, 0) + v
            all_subsystems.update(scan["subsystems"])
            all_error_lines.extend(scan["error_lines"][:2])
        elif scan["hits"]:
            failing_suites.append(suite)
            for k, v in scan["hits"].items():
                all_hits[k] = all_hits.get(k, 0) + v
            all_subsystems.update(scan["subsystems"])
            all_error_lines.extend(scan["error_lines"][:2])
        else:
            passing_suites.append(suite)

    # --- Build Markdown report ---
    lines: list[str] = []

    lines.append(f"## Run {run_date}  {run_id}  —  {project.upper()} Analysis")
    lines.append(f"*Generated by CIIQ local engine — no external API*")
    lines.append("")

    # 1. Introducing commits
    lines.append("## 1. Introducing Commit(s)")
    if commits:
        lines.append(
            f"The following commit(s) landed between the last passing run "
            f"(`{sha_good[:12]}`) and the failing run (`{sha_bad[:12]}`):"
        )
        for c in commits:
            lines.append(f"- `{c['sha']}` {c['subject']}")
        if diff_stat:
            lines.append("")
            lines.append("**Changed files (diff --stat):**")
            lines.append("```")
            lines.append(diff_stat[:1000])
            lines.append("```")
    else:
        lines.append(
            "No git log provided. Supply `delta.git_log` to get commit attribution."
        )
    lines.append("")

    # 2. Root cause
    lines.append("## 2. Root Cause")
    if empty_suites and not all_hits and not passing_suites:
        lines.append(
            f"⚠ **No log content provided.** All {len(empty_suites)} suite log textarea(s) are empty. "
            f"Paste failure snippets from tuxmaker into the log textareas, or click **Load Example** "
            f"to run the analysis against the built-in run 1592 sample data."
        )
    elif all_hits:
        top_errors = sorted(all_hits.items(), key=lambda x: -x[1])[:5]
        error_summary = ", ".join(f"{k} (×{v})" for k, v in top_errors)
        lines.append(
            f"Detected error signatures: **{error_summary}**. "
            f"{len(failing_suites)} suite(s) produced errors; "
            f"{len(passing_suites)} suite(s) passed."
        )
        if empty_suites:
            lines.append(
                f"Note: {len(empty_suites)} suite(s) had no log content and were skipped "
                f"({', '.join(f'`{s}`' for s in empty_suites)})."
            )
        if all_error_lines:
            lines.append("")
            lines.append("Representative failure lines:")
            for el in all_error_lines[:4]:
                lines.append(f"> `{el[:120]}`")
        lines.append("")
        lines.append(f"**{project.upper()} context:** {expert_ctx}")
    else:
        lines.append(
            "No error signatures detected in the provided logs. "
            "All suites appear to have passed."
        )
    lines.append("")

    # 3. Affected subsystems
    lines.append("## 3. Affected Subsystems")
    if all_subsystems:
        for sub in sorted(all_subsystems):
            lines.append(f"- {sub}")
    else:
        lines.append("- Unable to determine (no matching subsystem keywords in logs)")
    lines.append("")

    # 4. Why this project is affected
    lines.append(f"## 4. Why {project.upper()} Is Affected")
    if "migration" in " ".join(failing_suites).lower():
        lines.append(
            f"Migration-related suites are failing. {project.upper()} relies on "
            "a stable CPU state serialisation contract between kernel, QEMU, and libvirt. "
            "A change to any ABI layer can cause migration stream incompatibility."
        )
    elif "kvm" in " ".join(failing_suites).lower() or project == "kvm":
        lines.append(
            "KVM unit/selftests exercise intercept handling and SIE-level state directly. "
            "Any change to vcpu struct layout, intercept table, or facility bits "
            "will surface here first."
        )
    else:
        lines.append(
            f"{project.upper()} shares the kernel/hypervisor ABI. "
            "Changes to low-level CPU, memory, or device interfaces propagate upward "
            "through QEMU and libvirt."
        )
    lines.append("")

    # 5. Recommended fix
    lines.append("## 5. Recommended Fix")
    if commits:
        newest = commits[0]
        lines.append(
            f"Start by reverting the most recent commit and re-running the failing suites:"
        )
        lines.append(f"```bash")
        lines.append(f"git revert {newest['sha']}  # \"{newest['subject']}\"")
        lines.append(f"```")
        lines.append(
            "If the revert restores green, bisect between the commits above to isolate "
            "the exact regression. If multiple commits are involved, revert in reverse order."
        )
    else:
        lines.append(
            "Provide `delta.git_log` and `delta.git_patch` to get a specific revert command. "
            "Without commit data, use `git bisect` between the last green and current HEAD."
        )
    lines.append("")

    # 6. Verification command
    lines.append("## 6. Verification Command")
    suite_example = failing_suites[0] if failing_suites else "<suite-name>"
    lines.append(
        "Run the smallest failing suite in isolation on tuxmaker to confirm:"
    )
    lines.append("```bash")
    lines.append(f"# On tuxmaker:")
    lines.append(f"cd /home/ciuser && ./run-suite.sh {suite_example} $(git rev-parse HEAD)")
    lines.append("```")
    if len(failing_suites) > 1:
        lines.append(
            f"Then run the full {project} suite group: "
            + ", ".join(f"`{s}`" for s in failing_suites)
        )

    return "\n".join(lines)


def correlate_projects(
    delta: dict,
    kvm_result: str,
    qemu_result: str,
    libvirt_result: str,
    run_date: str,
    run_id: str,
) -> str:
    """Produce a cross-project correlation report using heuristics only."""
    commits = _extract_commits(delta.get("git_log", ""))

    lines: list[str] = []
    lines.append(f"## Cross-Project Correlation  —  Run {run_date}  {run_id}")
    lines.append("*Generated by CIIQ local engine — no external API*")
    lines.append("")

    # 1. Shared root cause
    lines.append("## 1. Cross-Project Correlation")
    if commits:
        lines.append(
            f"All three projects share the same kernel tree. "
            f"The {len(commits)} commit(s) in the delta are the common suspect(s):"
        )
        for c in commits[:5]:
            lines.append(f"- `{c['sha']}` {c['subject']}")
    else:
        lines.append(
            "No git delta provided. Cross-project root cause cannot be determined "
            "without commit data. Provide `delta.git_log`."
        )
    lines.append("")

    # 2. Dependency chain
    lines.append("## 2. Dependency Chain")
    lines.append(
        "Typical s390x virtualisation stack cascade:\n"
        "1. **Kernel change** (virt/kvm or arch/s390) alters ABI or CPU state layout\n"
        "2. **QEMU** fails because KVM_SET/GET_ONE_REG, SIE state, or migration stream no longer matches\n"
        "3. **libvirt** fails because the QEMU machine type or CPU model reported via QMP has changed"
    )
    lines.append("")

    # 3. Minimum fix set
    lines.append("## 3. Minimum Fix Set")
    if commits:
        lines.append("Revert in reverse-chronological order:")
        for i, c in enumerate(commits[:3], 1):
            lines.append(f"{i}. `git revert {c['sha']}` — \"{c['subject']}\"")
        lines.append(
            "\nIf individual reverts conflict, use `git revert -n` then resolve manually."
        )
    else:
        lines.append("Provide `delta.git_log` to generate specific revert commands.")
    lines.append("")

    # 4. Triage order
    lines.append("## 4. Triage Order")
    lines.append(
        "1. **KVM selftests / kvm-unit-tests** — fastest to run, confirms kernel-level regression\n"
        "2. **QEMU s390x-kvm** — confirms the userspace→kernel ABI is intact\n"
        "3. **libvirt-s390x** — confirms domain lifecycle (start/stop/migrate) works end-to-end"
    )
    lines.append("")

    # 5. Reproducer
    lines.append("## 5. Reproducer")
    lines.append(
        "Shortest reproducer sequence on tuxmaker (no full CI needed):"
    )
    lines.append("```bash")
    lines.append("# 1. Build kernel at failing SHA")
    lines.append("cd /home/ciuser/linux && git checkout <failing-sha>")
    lines.append("make -j$(nproc) ARCH=s390 bzImage")
    lines.append("")
    lines.append("# 2. Run KVM selftests (fastest confirmation)")
    lines.append("tools/testing/selftests/kvm/run_tests.sh -a s390x 2>&1 | grep -E 'PASS|FAIL'")
    lines.append("")
    lines.append("# 3. If KVM passes, run QEMU migration smoke test")
    lines.append("./run-suite.sh qemu-migration-s390 <failing-sha>")
    lines.append("```")

    return "\n".join(lines)


# ─────────────────────────────────────────────────────────────────────────────
#  History helpers (stored in Flask session)
# ─────────────────────────────────────────────────────────────────────────────
def _add_history(project: str, status: str, summary: str) -> None:
    if "ciiq_history" not in session:
        session["ciiq_history"] = []
    session["ciiq_history"].insert(
        0,
        {
            "ts":      datetime.now().strftime("%H:%M:%S"),
            "project": project,
            "status":  status,
            "summary": summary[:200],
        },
    )
    session.modified = True


# ─────────────────────────────────────────────────────────────────────────────
#  Request helpers
# ─────────────────────────────────────────────────────────────────────────────
def err(msg: str, code: int = 400):
    """Return a standard JSON error response with ok=False."""
    return jsonify({"ok": False, "error": msg}), code


def require_json(f):
    """Decorator: reject requests that are not JSON."""
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not request.is_json:
            return err("Request must be JSON (Content-Type: application/json)")
        return f(*args, **kwargs)
    return wrapper


# ─────────────────────────────────────────────────────────────────────────────
#  Routes — UI
# ─────────────────────────────────────────────────────────────────────────────
@app.get("/")
def index():
    from flask import make_response
    resp = make_response(render_template("ciiq.html"))
    resp.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"
    resp.headers["Pragma"] = "no-cache"
    return resp


# ─────────────────────────────────────────────────────────────────────────────
#  Routes — Config
# ─────────────────────────────────────────────────────────────────────────────
@app.get("/api/config")
def api_config():
    """Return sanitised config."""
    ci = CFG.get("ci", {})
    # Find latest cached run date so the UI can auto-seed without SSH
    cache_dir = os.path.join(BASE_DIR, ci.get("delta_cache_dir", "delta_cache"))
    latest_run_date = os.environ.get("CIIQ_LATEST_RUN_DATE", "").strip()
    latest_run_id   = os.environ.get("CIIQ_LATEST_RUN_ID",   "").strip()
    if not latest_run_date and os.path.isdir(cache_dir):
        cached = sorted(
            [f for f in os.listdir(cache_dir) if re.match(r"ciiq_delta_\d{8}\.json", f)],
            reverse=True,
        )
        if cached:
            raw = cached[0][len("ciiq_delta_"):-len(".json")]  # YYYYMMDD
            latest_run_date = "{}-{}-{}".format(raw[:4], raw[4:6], raw[6:])
    return jsonify(
        {
            "ok": True,
            "engine": "local",
            "ci": {
                "log_base":        ci.get("log_base"),
                "webui_base":      ci.get("webui_base"),
                "tuxmaker_host":   ci.get("tuxmaker_host"),
                "latest_run_date": latest_run_date,
                "latest_run_id":   latest_run_id,
            },
            "projects": {
                proj: [s["name"] for s in data["suites"]]
                for proj, data in CFG.get("projects", {}).items()
            },
        }
    )


# ─────────────────────────────────────────────────────────────────────────────
#  Routes — Single-project analysis
# ─────────────────────────────────────────────────────────────────────────────
@app.post("/api/analyse/<project>")
@require_json
def api_analyse_project(project: str):
    if project not in ("kvm", "qemu", "libvirt"):
        return err(f"Unknown project '{project}'. Must be kvm, qemu, or libvirt.")

    body       = request.get_json()
    delta      = body.get("delta", {})
    suite_logs = body.get("suite_logs", {})
    run_date   = body.get("run_date", datetime.today().strftime("%Y-%m-%d"))
    run_id     = body.get("run_id", "#????")

    if not suite_logs:
        return err("suite_logs is required (dict of suite_name → log_text)")

    try:
        text = analyse_project(project, delta, suite_logs, run_date, run_id)
        _add_history(project, "ok", text)
        return jsonify(
            {
                "ok":       True,
                "project":  project,
                "analysis": text,
                "engine":   "local",
                "run_date": run_date,
                "run_id":   run_id,
            }
        )
    except Exception as exc:
        _add_history(project, "err", str(exc))
        log.exception("Analysis error for %s", project)
        return err(str(exc), 500)


# ─────────────────────────────────────────────────────────────────────────────
#  Routes — Analyse all three projects  (also serves /api/analyse/local)
# ─────────────────────────────────────────────────────────────────────────────
def _run_all_projects(body: dict) -> dict:
    """Shared logic for /api/analyse/all and /api/analyse/local."""
    raw_logs    = body.get("suite_logs", {})
    delta       = body.get("delta", {})
    run_date    = body.get("run_date", datetime.today().strftime("%Y-%m-%d"))
    run_id      = body.get("run_id", "#????")
    # Optional UI-supplied PASS/FAIL badges — {suite_name: "PASS"|"FAIL"}
    ui_status   = body.get("suite_status", {})

    # Auto-split flat suite_logs into per-project buckets
    PROJ_SUITES: dict[str, list[str]] = {
        proj: [s["name"] for s in CFG.get("projects", {}).get(proj, {}).get("suites", [])]
        for proj in ("kvm", "qemu", "libvirt")
    }
    is_flat = raw_logs and not any(k in raw_logs for k in ("kvm", "qemu", "libvirt"))
    if is_flat:
        all_logs: dict[str, dict] = {"kvm": {}, "qemu": {}, "libvirt": {}}
        for suite_name, suite_log in raw_logs.items():
            for proj, suites in PROJ_SUITES.items():
                if suite_name in suites:
                    all_logs[proj][suite_name] = suite_log
                    break
        log.info("Auto-split flat suite_logs → kvm:%d qemu:%d libvirt:%d",
                 len(all_logs["kvm"]), len(all_logs["qemu"]), len(all_logs["libvirt"]))
    else:
        all_logs = raw_logs

    # Results use the app-wx.py shape: {project: {analysis: text, engine: "local"}}
    results: dict[str, dict] = {}
    errors:  dict[str, str]  = {}

    for project in ("kvm", "qemu", "libvirt"):
        suite_logs = all_logs.get(project, {})
        if not suite_logs:
            log.warning("No suite logs for %s — skipping", project)
            continue
        try:
            text = analyse_project(project, delta, suite_logs, run_date, run_id,
                                   suite_status=ui_status or None)
            results[project] = {"analysis": text, "engine": "local"}
            _add_history(project, "ok", text)
        except Exception as exc:
            errors[project] = str(exc)
            _add_history(project, "err", str(exc))
            log.exception("Error analysing %s", project)

    return {
        "ok":       True,
        "results":  results,
        "errors":   errors,
        "engine":   "local",
        "run_date": run_date,
        "run_id":   run_id,
    }


@app.post("/api/analyse/all")
@require_json
def api_analyse_all():
    return jsonify(_run_all_projects(request.get_json()))


@app.post("/api/analyse/local")
@require_json
def api_analyse_local():
    return jsonify(_run_all_projects(request.get_json()))


# ─────────────────────────────────────────────────────────────────────────────
#  Routes — Cross-project correlation
# ─────────────────────────────────────────────────────────────────────────────
@app.post("/api/correlate")
@require_json
def api_correlate():
    body     = request.get_json()
    delta    = body.get("delta", {})
    analyses = body.get("analyses", {})
    run_date = body.get("run_date", datetime.today().strftime("%Y-%m-%d"))
    run_id   = body.get("run_id", "#????")

    try:
        text = correlate_projects(
            delta,
            analyses.get("kvm", ""),
            analyses.get("qemu", ""),
            analyses.get("libvirt", ""),
            run_date,
            run_id,
        )
        _add_history("correlation", "ok", text)
        return jsonify({"ok": True, "correlation": text, "engine": "local"})
    except Exception as exc:
        _add_history("correlation", "err", str(exc))
        log.exception("Correlation error")
        return err(str(exc), 500)



# SSH helpers (auto-fetch from tuxmaker)

_SSH_RUNS_CACHE      = []      # last successful SSH run list
_SSH_RUNS_CACHE_TS   = 0.0    # epoch time of last fetch
_SSH_RUNS_CACHE_TTL  = 60     # seconds before re-fetching

def _ssh_run(cmd, timeout=30):
    """Run cmd on tuxmaker via SSH. Returns (returncode, stdout, stderr)."""
    ci = CFG.get("ci", {})
    host = ci.get("tuxmaker_host", "tuxmaker")
    user = ci.get("tuxmaker_user", "ciuser")
    target = "{}@{}".format(user, host) if user else host
    argv = ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=5", target, cmd]
    try:
        r = subprocess.run(argv, capture_output=True, text=True, timeout=timeout)
        return r.returncode, r.stdout, r.stderr
    except subprocess.TimeoutExpired:
        return 1, "", "SSH timed out"
    except FileNotFoundError:
        return 1, "", "ssh binary not found"


def _ssh_list_runs():
    """List daily run directories on tuxmaker via SSH.
    Uses an in-memory TTL cache first, then a disk cache (survives process restart),
    then SSH. This prevents repeated 5s timeouts on page refresh when off VPN."""
    global _SSH_RUNS_CACHE, _SSH_RUNS_CACHE_TS
    import time
    # 1. In-memory cache (fastest — same process, same worker)
    if _SSH_RUNS_CACHE and (time.time() - _SSH_RUNS_CACHE_TS) < _SSH_RUNS_CACHE_TTL:
        return _SSH_RUNS_CACHE
    # 2. Disk cache — valid for 5 minutes, survives process restarts
    ci = CFG.get("ci", {})
    cache_dir = os.path.join(BASE_DIR, ci.get("delta_cache_dir", "delta_cache"))
    runs_cache_file = os.path.join(cache_dir, "_runs_list.json")
    if os.path.isfile(runs_cache_file):
        try:
            age = time.time() - os.path.getmtime(runs_cache_file)
            if age < 300:  # 5 minutes
                with open(runs_cache_file) as _f:
                    cached = json.load(_f)
                _SSH_RUNS_CACHE    = cached
                _SSH_RUNS_CACHE_TS = time.time()
                return cached
        except (OSError, json.JSONDecodeError):
            pass
    # 3. SSH fetch
    log_base = ci.get("log_base", "/home/ciuser/logs/daily")
    pattern = "^[0-9]{8}$"
    rc, out, _ = _ssh_run(
        "ls -1 {} 2>/dev/null | grep -E '{}' | sort -r | head -30".format(log_base, pattern)
    )
    if rc != 0 or not out.strip():
        return []
    runs = []
    for entry in out.strip().splitlines():
        entry = entry.strip()
        if not re.match(r"^\d{8}$", entry):
            continue
        _, sha_out, _ = _ssh_run(
            "test -f {}/{}/kernel.sha && echo yes || echo no".format(log_base, entry)
        )
        runs.append({
            "date_raw": entry,
            "date_fmt": "{}-{}-{}".format(entry[:4], entry[4:6], entry[6:]),
            "has_sha": sha_out.strip() == "yes",
            "path": "{}/{}".format(log_base, entry),
        })
    _SSH_RUNS_CACHE    = runs
    _SSH_RUNS_CACHE_TS = time.time()
    # Write disk cache
    try:
        os.makedirs(cache_dir, exist_ok=True)
        with open(runs_cache_file, "w") as _f:
            json.dump(runs, _f)
    except OSError:
        pass
    return runs


# ─────────────────────────────────────────────────────────────────────────────
#  Routes — Available CI runs
# ─────────────────────────────────────────────────────────────────────────────
@app.get("/api/runs")
def api_runs():
    """List run dates from local log_base if mounted, else via SSH to tuxmaker."""
    log_base = CFG["ci"]["log_base"]

    # Fast path: log dir is locally mounted (e.g. NFS)
    if os.path.isdir(log_base):
        runs = []
        for entry in sorted(os.listdir(log_base), reverse=True):
            full = os.path.join(log_base, entry)
            if os.path.isdir(full) and re.match(r"^\d{8}$", entry):
                sha_file = os.path.join(full, "kernel.sha")
                runs.append({
                    "date_raw": entry,
                    "date_fmt": "{}-{}-{}".format(entry[:4], entry[4:6], entry[6:]),
                    "has_sha": os.path.isfile(sha_file),
                    "path": full,
                })
        return jsonify({"ok": True, "runs": runs[:30], "log_base": log_base, "source": "local"})

    # Slow path: SSH to tuxmaker to list runs
    log.info("log_base not locally accessible -- listing runs via SSH")
    runs = _ssh_list_runs()
    return jsonify({"ok": True, "runs": runs[:30], "log_base": log_base, "source": "ssh"})


# ─────────────────────────────────────────────────────────────────────────────
#  Routes — Suite log snippets for a specific run date
# ─────────────────────────────────────────────────────────────────────────────
@app.get("/api/run/<date>/suites")
def api_run_suites(date: str):
    """Auto-populate log snippets by reading the CI log directory."""
    log_base = CFG["ci"]["log_base"]
    run_dir  = os.path.join(log_base, date.replace("-", ""))

    suite_logs: dict[str, dict[str, str]] = {"kvm": {}, "qemu": {}, "libvirt": {}}
    project_suites = CFG.get("projects", {})

    for proj, data in project_suites.items():
        for s in data.get("suites", []):
            name    = s["name"]
            suite_d = os.path.join(run_dir, name)
            snippet = ""
            if os.path.isdir(suite_d):
                for root, _, files in os.walk(suite_d):
                    for fname in files:
                        if fname.endswith((".log", ".txt", ".out")):
                            fpath = os.path.join(root, fname)
                            try:
                                with open(fpath, errors="replace") as f:
                                    lines = [
                                        ln.rstrip()
                                        for ln in f
                                        if re.search(
                                            r"(FAIL|FAILED|BUG|Oops|panic|assert|ERROR|"
                                            r"error:|No such|Invalid argument|unexpected|"
                                            r"timeout|abort)",
                                            ln,
                                            re.IGNORECASE,
                                        )
                                    ]
                                    snippet += "\n".join(lines[:10]) + "\n"
                            except OSError:
                                pass
            suite_logs[proj][name] = snippet.strip()

    sha_good, sha_bad = "", ""
    sha_file = os.path.join(run_dir, "kernel.sha")
    if os.path.isfile(sha_file):
        sha_bad = open(sha_file).read().strip()

    return jsonify(
        {
            "ok":         True,
            "date":       date,
            "suite_logs": suite_logs,
            "sha_bad":    sha_bad,
            "sha_good":   sha_good,
        }
    )




# ─────────────────────────────────────────────────────────────────────────────
#  Routes — Git delta (SSH fetch from tuxmaker, with local cache)
# ─────────────────────────────────────────────────────────────────────────────
@app.get("/api/delta/<date>")
def api_delta(date):
    """Fetch git delta for a run date from tuxmaker via SSH. Caches locally."""
    date_raw = date.replace("-", "")
    if not re.match(r"^\d{8}$", date_raw):
        return err("Invalid date -- use YYYYMMDD or YYYY-MM-DD")

    cache_dir  = os.path.join(BASE_DIR, CFG.get("ci", {}).get("delta_cache_dir", "delta_cache"))
    os.makedirs(cache_dir, exist_ok=True)
    cache_file = os.path.join(cache_dir, "ciiq_delta_{}.json".format(date_raw))

    # Return cached version if present and valid
    if os.path.isfile(cache_file):
        try:
            with open(cache_file) as fh:
                data = json.load(fh)
            log.info("Delta cache hit for %s", date_raw)
            return jsonify({"ok": True, "delta": data, "source": "cache"})
        except (OSError, json.JSONDecodeError):
            pass  # stale/corrupt -- re-fetch below

    ci          = CFG.get("ci", {})
    log_base    = ci.get("log_base",    "/home/ciuser/logs/daily")
    kernel_repo = ci.get("kernel_repo", "/home/ciuser/linux")
    yesterday   = (datetime.strptime(date_raw, "%Y%m%d") - timedelta(days=1)).strftime("%Y%m%d")

    # Fetch both SHAs in one SSH call
    sha_cmd = (
        "SB=$(cat {lb}/{today}/kernel.sha 2>/dev/null | tr -d '[:space:]' || echo HEAD); "
        "SG=$(cat {lb}/{yest}/kernel.sha  2>/dev/null | tr -d '[:space:]' || echo HEAD~10); "
        "printf '%s %s' $SB $SG"
    ).format(lb=log_base, today=date_raw, yest=yesterday)

    rc_sha, sha_out, sha_err = _ssh_run(sha_cmd, timeout=15)
    if rc_sha != 0:
        log.warning("SHA fetch failed for %s: %s", date_raw, sha_err[:200])
        sha_bad, sha_good = "HEAD", "HEAD~10"
    else:
        parts    = sha_out.strip().split()
        sha_bad  = parts[0] if len(parts) > 0 else "HEAD"
        sha_good = parts[1] if len(parts) > 1 else "HEAD~10"

    # Fetch git data in three separate SSH calls to avoid any quoting issues
    def ssh_git(git_args):
        cmd = "cd {} && {}".format(kernel_repo, git_args)
        _, out, _ = _ssh_run(cmd, timeout=30)
        return out

    git_log = ssh_git(
        "git log --oneline {}..{} -- arch/s390/kvm/ include/uapi/linux/kvm.h "
        "drivers/s390/ arch/s390/boot/ tools/testing/selftests/kvm/ "
        "2>/dev/null | head -40 || true".format(sha_good, sha_bad)
    )
    git_diff_stat = ssh_git(
        "git diff --stat {}..{} 2>/dev/null | tail -60 || true".format(sha_good, sha_bad)
    )
    git_patch = ssh_git(
        "git diff {}..{} -- arch/s390/kvm/ include/uapi/linux/kvm.h "
        "2>/dev/null | head -200 || true".format(sha_good, sha_bad)
    )

    data = {
        "run_date":      date_raw,
        "sha_good":      sha_good,
        "sha_bad":       sha_bad,
        "git_log":       git_log,
        "git_diff_stat": git_diff_stat,
        "git_patch":     git_patch,
    }

    # Cache the result
    try:
        with open(cache_file, "w") as fh:
            json.dump(data, fh, indent=2)
        log.info("Delta cached for %s", date_raw)
    except OSError as exc:
        log.warning("Could not write delta cache: %s", exc)

    return jsonify({"ok": True, "delta": data, "source": "ssh"})

# ─────────────────────────────────────────────────────────────────────────────
#  Routes — CI mail ingest
# ─────────────────────────────────────────────────────────────────────────────

# Regex patterns for parsing the CI daily mail report
_INGEST_DATE_RE    = re.compile(r'Daily run:\s*(\d{4}-\d{2}-\d{2})')
_INGEST_WEBUI_RE   = re.compile(r'Web UI:\s*(https?://\S+)')
_INGEST_RUNID_RE   = re.compile(r'/ci-run/(\d+)')
_INGEST_LOGPATH_RE = re.compile(r'Full log:\s*(\S+)')
_INGEST_KERNEL_RE  = re.compile(
    r'^([A-Za-z]):\s+kernel-(\S+)\s+\(([^)]+)\)',
    re.MULTILINE,
)
_INGEST_SECTION_RE = re.compile(
    r"^Test failures for test suite '([^']+)'\s*\n=+\n(.*?)"
    r"(?=^Test failures for|^Fixed test|^Dumps of|^Test systems|^Combined|^--\s*$"
    r"|^Note:|^[A-Za-z]: kernel-|\Z)",
    re.MULTILINE | re.DOTALL,
)
_INGEST_SUITE_ROW_RE = re.compile(
    r'^(\S+)\s+(\d+/\d+)\s+(\d+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s*$',
    re.MULTILINE,
)
_INGEST_DUMP_RE = re.compile(
    r'^\s*\d+\s+(\S+)\s+\S+\s+\S+\s+\S+\s+(\S+)\s+\S+\s+\S+\s+\S+\s+\S+\s+(.*?)\s*$',
    re.MULTILINE,
)


def _parse_ci_mail(text: str) -> dict:
    """
    Parse a CI daily mail report into structured data for the CIIQ UI.

    Returns:
      run_date, run_id, web_url, log_path, kernel_key,
      suite_logs   {suite_name: str},
      suite_status {suite_name: "FAIL"|"PASS"},
      dumps        [{suite, kernel, system, dump_id, reason}]
    """
    result: dict = {
        "run_date":     "",
        "run_id":       "",
        "web_url":      "",
        "log_path":     "",
        "kernel_key":   {},   # letter -> {name, build}
        "suite_logs":   {},   # suite -> failure text
        "suite_status": {},   # suite -> FAIL / PASS
        "dumps":        [],
    }

    # ── Run metadata ──────────────────────────────────────────────
    m = _INGEST_DATE_RE.search(text)
    if m:
        result["run_date"] = m.group(1)

    m = _INGEST_WEBUI_RE.search(text)
    if m:
        result["web_url"] = m.group(1).rstrip(")")
        m2 = _INGEST_RUNID_RE.search(result["web_url"])
        if m2:
            result["run_id"] = m2.group(1)

    m = _INGEST_LOGPATH_RE.search(text)
    if m:
        result["log_path"] = m.group(1).rstrip(")")

    # ── Kernel key (E: kernel-debug ...) ─────────────────────────
    for m in _INGEST_KERNEL_RE.finditer(text):
        letter, name, build = m.group(1), m.group(2), m.group(3)
        result["kernel_key"][letter] = {"name": name, "build": build}

    # ── Combined test results table ── derive PASS/FAIL per suite ─
    # Match lines like: canton-prototype  2/2  1  -  1  -  -  1  5m 58s  7m 30s
    summary_re = re.compile(
        r'^([a-z][a-z0-9._-]+)\s+(\d+/\d+)\s+(\d+)\s+(\S+)\s+(\S+)',
        re.MULTILINE,
    )
    for m in summary_re.finditer(text):
        suite = m.group(1)
        fail_col = m.group(5)
        # fail column is "-" for zero or a number
        has_fail = fail_col not in ("-", "0", "FAIL", "PASS")
        if re.match(r'^\d+$', fail_col):
            has_fail = int(fail_col) > 0
        result["suite_status"][suite] = "FAIL" if has_fail else "PASS"

    # ── Per-suite failure sections ────────────────────────────────
    # Store RAW body (with [ABCD][Nx Nd] annotations intact) so the JS offline engine
    # can render the age/verdict table.  The analysis engine strips annotations itself
    # via _strip_tap_annotations() before pattern-matching.
    _CI_ERROR_LINE_RE = re.compile(r'\bci-error:\s*\S', re.IGNORECASE)
    for m in _INGEST_SECTION_RE.finditer(text):
        suite    = m.group(1)
        raw_body = m.group(2).strip()          # keep annotations intact
        if raw_body:
            result["suite_logs"][suite] = raw_body
            result["suite_status"][suite] = "FAIL"
        elif _CI_ERROR_LINE_RE.search(raw_body):
            result["suite_logs"][suite] = raw_body
            result["suite_status"][suite] = "FAIL"

    # ── Crash dumps ───────────────────────────────────────────────
    in_dumps = False
    for line in text.splitlines():
        if line.startswith("Dumps of unresponsive systems"):
            in_dumps = True
            continue
        if in_dumps and re.match(r'^(Fixed|Test systems|Parse|Combined|--)', line):
            in_dumps = False
        if in_dumps:
            # NR  SUITE  KERNEL  MODEL  TYPE  SYSTEM  DUMP  FILENAME  TIMESTAMP  TESTCASE  REASON
            parts = line.split()
            if len(parts) >= 6 and parts[0].isdigit():
                result["dumps"].append({
                    "suite":   parts[1] if len(parts) > 1 else "",
                    "kernel":  parts[2] if len(parts) > 2 else "",
                    "system":  parts[5] if len(parts) > 5 else "",
                    "dump_id": parts[6] if len(parts) > 6 else "",
                    "reason":  parts[-1],
                })

    return result


@app.post("/api/ingest")
@require_json
def api_ingest():
    """
    Parse a raw CI daily mail report and return structured data
    ready to populate the CIIQ UI fields.
    """
    body = request.get_json()
    text = body.get("mail_text", "")
    if not text or not text.strip():
        return err("mail_text is required")

    try:
        parsed = _parse_ci_mail(text)
        log.info(
            "Ingest: run=%s id=%s suites=%d dumps=%d",
            parsed["run_date"], parsed["run_id"],
            len(parsed["suite_logs"]), len(parsed["dumps"]),
        )
        return jsonify({"ok": True, **parsed})
    except Exception as exc:
        log.exception("Ingest parse error")
        return err(str(exc), 500)


# ─────────────────────────────────────────────────────────────────────────────
#  HTML report renderer
# ─────────────────────────────────────────────────────────────────────────────

_REPORT_CSS = """
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
body{font-family:-apple-system,"Segoe UI",system-ui,sans-serif;font-size:14px;line-height:1.65;color:#1f2328;background:#fff;max-width:760px;margin:0 auto;padding:32px 24px 48px}
.topbar{background:#1e3a5f;color:#fff;padding:10px 16px;border-radius:8px;display:flex;align-items:center;gap:12px;margin-bottom:24px;flex-wrap:wrap}
.topbar .logo{background:#3b82d4;font-size:12px;font-weight:800;padding:3px 10px;border-radius:5px;letter-spacing:.06em}
.topbar .title{font-size:14px;font-weight:700;color:#e2e8f0}
.topbar .spacer{flex:1}
.topbar .run-badge{background:#1e40af;border:1px solid #3b82d4;border-radius:5px;padding:3px 10px;font-size:12px;color:#bfdbfe}
.topbar .fail-badge{background:#7f1d1d;border:1px solid #f87171;border-radius:5px;padding:3px 10px;font-size:12px;color:#fca5a5;font-weight:700}
.meta-row{display:flex;gap:16px;flex-wrap:wrap;background:#f7f8fa;border:1px solid #e5e7eb;border-radius:6px;padding:10px 14px;margin-bottom:22px;font-size:12px}
.meta-field .lbl{color:#57606a;text-transform:uppercase;font-size:10px;font-weight:700;letter-spacing:.05em}
.meta-field .val{font-family:"SFMono-Regular",Consolas,monospace;color:#1f2328;font-weight:600}
.meta-field .val a{color:#3b82d4;text-decoration:none}
h2{font-size:14px;font-weight:700;margin:24px 0 10px;padding-bottom:5px;border-bottom:2px solid #e5e7eb;color:#1f2328;display:flex;align-items:center;gap:8px}
h2 .num{background:#1e3a5f;color:#93c5fd;font-size:10px;font-weight:800;padding:2px 7px;border-radius:10px}
h3{font-size:13px;font-weight:700;margin:14px 0 6px}
.callout{border-radius:7px;padding:11px 14px;margin:10px 0;font-size:13px;line-height:1.7}
.callout-commit{background:#0d1117;border:1px solid #30363d;color:#e6edf3;font-family:"SFMono-Regular",Consolas,monospace;font-size:11.5px}
.callout-commit .cc-head{color:#58a6ff;display:block;margin-bottom:6px;font-size:11px;letter-spacing:.04em;text-transform:uppercase;font-weight:700}
.callout-rc{background:#fffbeb;border:1px solid #fde68a}
.callout-rc strong{color:#92400e}
.callout-fix{background:#f0fdf4;border:1px solid #86efac}
.callout-fix strong{color:#166534}
.callout-info{background:#eff6ff;border:1px solid #bfdbfe;font-size:13px}
.callout-info strong{color:#1e40af}
.callout-pass{background:#f0fdf4;border:1px solid #bbf7d0;padding:8px 14px;font-size:12px;color:#166534;border-radius:6px;margin:6px 0}
code{background:#f0f3f8;border:1px solid #d8dde4;border-radius:3px;padding:1px 5px;font-size:11.5px;font-family:"SFMono-Regular",Consolas,monospace;color:#1f2328}
pre{background:#161b22;border:1px solid #30363d;border-radius:5px;padding:10px 12px;font-size:11.5px;font-family:"SFMono-Regular",Consolas,monospace;color:#e6edf3;overflow-x:auto;line-height:1.55;margin:8px 0}
table{width:100%;border-collapse:collapse;font-size:12px;margin:10px 0}
th{background:#f7f8fa;text-align:left;padding:6px 9px;border:1px solid #e5e7eb;font-size:11px;font-weight:700;color:#57606a;text-transform:uppercase;letter-spacing:.04em}
td{padding:5px 9px;border:1px solid #e5e7eb;vertical-align:top;font-size:12px}
tr:nth-child(even) td{background:#fafafa}
.badge{font-size:10px;font-weight:700;padding:1px 7px;border-radius:8px;white-space:nowrap;display:inline-block;vertical-align:middle}
.bk{background:#eff6ff;color:#1e40af;border:1px solid #bfdbfe}
.bi{background:#fffbeb;color:#92400e;border:1px solid #fde68a}
.bt{background:#f0fdf4;color:#166534;border:1px solid #bbf7d0}
.bh{background:#fff1f2;color:#9f1239;border:1px solid #fecdd3}
.bc{background:#fdf4ff;color:#6b21a8;border:1px solid #e9d5ff}
.st-fail{color:#991b1b;font-weight:700}
.st-pass{color:#166534;font-weight:600}
.st-fixed{color:#1e40af;font-weight:600}
.kernel-key{display:flex;flex-wrap:wrap;gap:6px;margin:8px 0 12px}
.kk{font-family:"SFMono-Regular",Consolas,monospace;font-size:11px;background:#161b22;border:1px solid #30363d;border-radius:4px;padding:3px 8px;color:#e6edf3}
.kk .kk-id{color:#79c0ff;font-weight:700;margin-right:4px}
.kk .kk-sha{color:#8b949e;font-size:10px}
.ann{font-family:"SFMono-Regular",Consolas,monospace;font-size:11px;background:#161b22;color:#e6edf3;padding:2px 6px;border-radius:3px;border:1px solid #30363d;white-space:nowrap}
.fix-item{display:flex;gap:10px;padding:10px 0;border-bottom:1px solid #f0f0f0;font-size:13px}
.fix-item:last-child{border-bottom:none}
.fix-num{background:#1e3a5f;color:#93c5fd;font-size:11px;font-weight:700;width:22px;height:22px;border-radius:50%;display:flex;align-items:center;justify-content:center;flex-shrink:0;margin-top:1px}
.fix-tag{font-size:10px;background:#f7f8fa;border:1px solid #e5e7eb;border-radius:3px;padding:1px 5px;color:#57606a;margin-right:5px}
.num-col{font-family:"SFMono-Regular",Consolas,monospace;text-align:right;color:#57606a}
footer{margin-top:40px;padding-top:12px;border-top:1px solid #e5e7eb;text-align:center;font-size:11px;color:#57606a}
"""


def _h(s: str) -> str:
    """HTML-escape a string."""
    return (str(s)
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;"))


def _code(s: str) -> str:
    return f"<code>{_h(s)}</code>"


def _pre(s: str) -> str:
    return f"<pre>{_h(s)}</pre>"


def _section(num: int, title: str) -> str:
    return f'<h2><span class="num">{num}</span>{_h(title)}</h2>'


# Annotation regex: captures kernel letters, count, age
_ANN_RE = re.compile(
    r'^\[([A-Za-z ]{0,20})\]\s*\[\s*(\d+)x\s*(\d+)d\]\s*',
)


def _parse_annotation(line: str) -> tuple[str, int, int, str]:
    """
    Parse a TAP annotation prefix.
    Returns (kernels, count, age_days, rest_of_line).
    kernels is the letter string with spaces (e.g. 'ED GK   N').
    """
    m = _ANN_RE.match(line)
    if not m:
        return ("", 0, 0, line)
    kernels = m.group(1)
    count   = int(m.group(2))
    age     = int(m.group(3))
    rest    = line[m.end():]
    return (kernels, count, age, rest)


def _ann_html(kernels: str, count: int, age: int) -> str:
    """Render an annotation badge as HTML."""
    k_html = _h(kernels.strip()) if kernels.strip() else "—"
    return (
        f'<span class="ann">'
        f'<span style="color:#79c0ff;font-weight:700">{k_html}</span>'
        f'&nbsp;<span style="color:#f87149">{count}×</span>'
        f'&nbsp;<span style="color:#8b949e">{age}d</span>'
        f'</span>'
    )


def _render_html_report(
    parsed: dict,
    delta: dict,
    suite_logs: dict,   # {suite: log_text} — may be from ingest or from UI
    run_date: str,
    run_id: str,
    webui_base: str = "https://lnxgwne1.boeblingen.de.ibm.com/linux-ci/webui/ci-run",
) -> str:
    """
    Produce a complete self-contained HTML root-cause report.
    `parsed`    — output of _parse_ci_mail() or equivalent
    `delta`     — git delta dict (sha_good, sha_bad, git_log, git_diff_stat, ...)
    `suite_logs`— {suite: log_text} with raw TAP lines (annotations OK)
    """
    H = []  # HTML parts

    # ── Aggregate data ────────────────────────────────────────────────────────
    commits      = _extract_commits(delta.get("git_log", ""))
    kernel_key   = parsed.get("kernel_key", {})
    dumps        = parsed.get("dumps", [])
    suite_status = parsed.get("suite_status", {})

    # Build a combined suite_logs dict.
    # For the annotation table we need raw content (with [ABCD][Nx Nd] prefixes).
    # Priority: raw textarea content (has annotations) > ingest-stripped content.
    all_logs: dict[str, str] = {}
    # Start with stripped ingest data as base (catches suites not in textareas)
    for suite, text in (parsed.get("suite_logs") or {}).items():
        all_logs[suite] = text
    # Override with raw textarea content when available — it keeps annotations intact
    for suite, text in (suite_logs or {}).items():
        if text and text.strip():
            all_logs[suite] = text   # raw wins over stripped

    # Count failures
    fail_suites  = [s for s, v in suite_status.items() if v == "FAIL"]
    total_suites = len(suite_status)

    # Scan all logs for aggregate findings
    all_scan = _scan_log("\n".join(all_logs.values()))

    # Derive kernel build string from kernel_key
    kernel_build = ""
    for letter in ("E", "D", "G", "K"):
        if letter in kernel_key:
            build = kernel_key[letter].get("build", "")
            # Extract the short version like 7.2.0-20260809.rc6.git0.1c2c67f1a900
            m = re.search(r'([\d.]+(?:-\S+)?)', build)
            if m:
                kernel_build = m.group(1)
            break

    run_url = f"{webui_base}/{run_id}"
    log_path = f"/home/ciuser/logs/daily/{run_date.replace('-', '')}/"
    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M")

    # ── HEAD ──────────────────────────────────────────────────────────────────
    H.append(f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width,initial-scale=1.0" />
<title>CIIQ — Run {_h(run_id)} Root-Cause Report</title>
<style>{_REPORT_CSS}</style>
</head>
<body>
""")

    # ── Topbar ────────────────────────────────────────────────────────────────
    fail_count_str = f"{len(fail_suites)} / {total_suites} suites" if total_suites else f"{len(fail_suites)} suites"
    H.append(f"""<div class="topbar">
  <span class="logo">CIIQ</span>
  <span class="title">CI Intelligence &amp; Insight Query — Local Analysis</span>
  <div class="spacer"></div>
  <span class="run-badge">Run {_h(run_id)} &middot; {_h(run_date)}</span>
  <span class="fail-badge">{_h(fail_count_str)} FAIL</span>
</div>
""")

    # ── Meta row ─────────────────────────────────────────────────────────────
    H.append(f"""<div class="meta-row">
  <div class="meta-field"><div class="lbl">Run Date</div><div class="val">{_h(run_date)}</div></div>
  <div class="meta-field"><div class="lbl">Run ID</div><div class="val">{_h(run_id)}</div></div>
  <div class="meta-field"><div class="lbl">Log Path</div><div class="val">{_h(log_path)}</div></div>
  <div class="meta-field"><div class="lbl">Web UI</div><div class="val"><a href="{_h(run_url)}" target="_blank">{_h(run_id)} &#8599;</a></div></div>
  {"" if not kernel_build else f'<div class="meta-field"><div class="lbl">Kernel</div><div class="val">{_h(kernel_build)}</div></div>'}
  <div class="meta-field"><div class="lbl">Engine</div><div class="val">local (no LLM)</div></div>
  <div class="meta-field"><div class="lbl">Generated</div><div class="val">{_h(generated_at)}</div></div>
</div>
""")

    # ── Section 0: Run Summary ────────────────────────────────────────────────
    H.append(_section(0, "Run Summary"))

    if suite_status:
        H.append('<table><thead><tr>'
                 '<th>Suite</th><th>Status</th><th>Failure log (first line)</th>'
                 '</tr></thead><tbody>')
        for suite in sorted(suite_status.keys()):
            status = suite_status[suite]
            cls    = "st-fail" if status == "FAIL" else "st-pass"
            log_snippet = ""
            if status == "FAIL":
                raw = all_logs.get(suite, "")
                if raw:
                    first = raw.strip().splitlines()[0] if raw.strip() else ""
                    _, _, _, first = _parse_annotation(first)  # strip annotation
                    log_snippet = _h(first[:100])
            H.append(
                f'<tr><td>{_code(suite)}</td>'
                f'<td class="{_h(cls)}">{_h(status)}</td>'
                f'<td style="font-size:11px;color:#57606a;font-family:monospace">{log_snippet}</td></tr>'
            )
        H.append('</tbody></table>')
    else:
        H.append('<p style="color:#57606a;font-size:13px">No suite status data — import CI mail first.</p>')

    # ── Kernel key ────────────────────────────────────────────────────────────
    if kernel_key:
        H.append('<h3>Kernel builds tested</h3><div class="kernel-key">')
        for letter in sorted(kernel_key.keys()):
            kinfo = kernel_key[letter]
            name  = kinfo.get("name", "")
            build = kinfo.get("build", "")
            # Extract short SHA
            sha_m = re.search(r'\.([0-9a-f]{12,})', build)
            sha   = sha_m.group(1)[:12] if sha_m else ""
            H.append(
                f'<span class="kk">'
                f'<span class="kk-id">{_h(letter)}</span> {_h(name)} '
                f'{"" if not sha else f"<span class=\"kk-sha\">{_h(sha)}</span>"}'
                f'</span>'
            )
        H.append('</div>')

    # ── Section 1: Crash Dumps ────────────────────────────────────────────────
    if dumps:
        H.append(_section(1, "System Crashes &amp; Dumps"))
        H.append('<table><thead><tr>'
                 '<th>#</th><th>Suite</th><th>Kernel</th><th>System</th>'
                 '<th>Dump ID</th><th>Reason</th>'
                 '</tr></thead><tbody>')
        for i, d in enumerate(dumps, 1):
            # Normalise dump_id — parser may store em-dash, hyphen, or empty
            raw_dump_id = d.get("dump_id", "")
            dump_id     = raw_dump_id.strip().strip("—-") or ""
            dump_html   = _code(dump_id) if dump_id else "<em>—</em>"
            # Kernel: show as <code> so it doesn't need a letter prefix
            kernel_str  = d.get("kernel", "")
            kernel_html = _code(kernel_str) if kernel_str else "<em>—</em>"
            H.append(
                f'<tr>'
                f'<td style="font-weight:700;text-align:center;color:#f87149">{i}</td>'
                f'<td>{_code(d.get("suite", ""))}</td>'
                f'<td>{kernel_html}</td>'
                f'<td>{_code(d.get("system", ""))}</td>'
                f'<td>{dump_html}</td>'
                f'<td style="font-size:11px">{_h(d.get("reason", ""))}</td>'
                f'</tr>'
            )
        H.append('</tbody></table>')

    # ── Section 2: Introducing Commits ───────────────────────────────────────
    H.append(_section(2, "Introducing Commits"))
    if commits:
        sha_good = delta.get("sha_good", "")
        sha_bad  = delta.get("sha_bad", "")
        range_txt = ""
        if sha_good or sha_bad:
            range_txt = f'<span class="cc-head">Last passing: {_h(sha_good[:20] if sha_good else "(unknown)")} &rarr; Failing: {_h(sha_bad[:20] if sha_bad else "(unknown)")}</span>'
        commit_lines = "\n".join(
            f'<div style="padding:2px 0"><span style="color:#79c0ff">{_h(c["sha"])}</span> '
            f'<span style="color:#8b949e">&mdash;</span> {_h(c["subject"])}</div>'
            for c in commits
        )
        H.append(f'<div class="callout callout-commit">{range_txt}{commit_lines}</div>')
    else:
        H.append('<p style="color:#57606a;font-size:13px">No git log provided — paste git log output into the Git Delta panel.</p>')

    # ── Section 3: Root Cause Per Suite ──────────────────────────────────────
    H.append(_section(3, "Root Cause — Per Suite"))
    # Strip bare kernel-legend lines (e.g. "E: kernel-debug (...)") from per-suite display.
    # These belong in the Kernel builds section (Section 0), not in per-suite failure content.
    _KERNEL_LEGEND_RE = re.compile(r'^[A-Za-z]:\s+kernel-\S+\s*(\(.*\))?\s*$')

    for suite in sorted(all_logs.keys()):
        if suite_status.get(suite) != "FAIL":
            continue
        raw = all_logs.get(suite, "").strip()
        if not raw:
            continue

        # Strip kernel legend lines before scanning so they don't inflate subsystem detection
        filtered_raw = "\n".join(
            ln for ln in raw.splitlines()
            if not _KERNEL_LEGEND_RE.match(ln.strip())
        )
        if not filtered_raw.strip():
            continue

        scan = _scan_log(filtered_raw)
        H.append(f"<h3>{_code(suite)}</h3>")
        H.append('<div class="callout callout-rc">')

        # Parse annotation lines
        ann_rows = []
        plain_lines = []
        for line in filtered_raw.splitlines():
            stripped = line.strip()
            kernels, count, age, rest = _parse_annotation(line)
            if kernels or count:
                ann_rows.append((kernels, count, age, rest.strip()))
            else:
                plain_lines.append(stripped)

        if ann_rows:
            H.append('<table style="font-size:11.5px;margin:0 0 8px 0"><thead>'
                     '<tr><th>Failure</th><th>Kernels</th><th>Count</th><th>Age</th><th>Verdict</th></tr>'
                     '</thead><tbody>')
            for kernels, count, age, rest in ann_rows:
                # Simple age-based verdict
                if "ci-error" in rest.lower():
                    verdict = "Infrastructure failure"
                elif age >= 90:
                    verdict = '<span style="color:#57606a">Pre-existing (≥90d) — do not revert</span>'
                elif age >= 30:
                    verdict = '<span style="color:#92400e">Likely pre-existing (&gt;30d) — verify</span>'
                elif age <= 3:
                    verdict = '<span style="color:#991b1b;font-weight:700">New regression (≤3d)</span>'
                else:
                    verdict = f'<span style="color:#92400e">Recent ({age}d) — check delta</span>'
                H.append(
                    f'<tr><td style="font-family:monospace;font-size:11px">{_h(rest[:80])}</td>'
                    f'<td><span class="ann">{_h(kernels.strip())}</span></td>'
                    f'<td style="text-align:center">{count}</td>'
                    f'<td style="text-align:right">{age}d</td>'
                    f'<td style="font-size:11px">{verdict}</td></tr>'
                )
            H.append('</tbody></table>')
        elif plain_lines:
            # No annotations — just show top error lines
            for pl in plain_lines[:4]:
                if pl:
                    H.append(f'<div style="font-family:monospace;font-size:11.5px;padding:2px 0">{_h(pl[:120])}</div>')

        # Subsystems found
        if scan["subsystems"]:
            H.append(f'<div style="font-size:11px;color:#57606a;margin-top:6px">'
                     f'Subsystems: {", ".join(_h(s) for s in scan["subsystems"])}</div>')

        H.append('</div>')

    # ── Section 4: Affected Subsystems ───────────────────────────────────────
    if all_scan["subsystems"]:
        H.append(_section(4, "Affected Subsystems"))
        # When there are multiple introducing commits the local engine cannot accurately
        # attribute each subsystem to a specific commit — show all commits as a note
        # rather than misleadingly pinning everything to commits[0].
        if commits and len(commits) == 1:
            H.append('<table><thead><tr><th>Subsystem</th><th>Introducing commit</th></tr></thead><tbody>')
            for sub in sorted(all_scan["subsystems"]):
                H.append(f'<tr><td>{_h(sub)}</td><td>{_code(commits[0]["sha"])}</td></tr>')
        else:
            H.append('<table><thead><tr><th>Subsystem</th></tr></thead><tbody>')
            for sub in sorted(all_scan["subsystems"]):
                H.append(f'<tr><td>{_h(sub)}</td></tr>')
        H.append('</tbody></table>')
        if commits and len(commits) > 1:
            sha_inline = ", ".join(_code(c["sha"]) for c in commits)
            H.append(f'<p style="font-size:11.5px;color:#57606a;margin-top:6px">'
                     f'All subsystems may be affected by any of the {len(commits)} introducing commits: '
                     f'{sha_inline} — see §2 for details.</p>')

    # ── Section 5: Minimum Fix Set ───────────────────────────────────────────
    H.append(_section(5, "Minimum Fix Set"))
    if commits:
        H.append('<div>')
        for i, c in enumerate(commits[:5], 1):
            cmd = 'git revert {}  # "{}"'.format(c["sha"], c["subject"])
            H.append(
                '<div class="fix-item">'
                '<div class="fix-num">' + str(i) + '</div>'
                '<div class="fix-body">'
                '<strong><span class="fix-tag">REVERT</span> ' + _h(c["subject"]) + '</strong>'
                + _pre(cmd) +
                '</div></div>'
            )
        H.append('</div>')
        if len(commits) > 1:
            sha_list = " ".join(c["sha"] for c in commits[:5])
            subjects  = "\n".join("Revert: " + c["subject"] for c in commits[:5])
            combined  = "git revert --no-commit {}\ngit commit -m \"Revert: CI regression run #{}\n{}\"".format(
                sha_list, run_id, subjects)
            H.append(
                '<div class="callout callout-fix" style="margin-top:8px">'
                '<strong>Combined revert:</strong>'
                + _pre(combined) +
                '</div>'
            )
    else:
        H.append('<p style="color:#57606a;font-size:13px">No git log provided — paste output of '
                 '<code>git log --oneline</code> into the Git Delta panel.</p>')

    # ── Section 6: Triage Order ───────────────────────────────────────────────
    H.append(_section(6, "Triage Order"))
    H.append('<table><thead><tr><th>Priority</th><th>Action</th><th>Expected outcome</th></tr></thead><tbody>')
    if commits:
        for i, c in enumerate(commits[:5], 1):
            H.append(
                f'<tr><td><strong>{i}</strong></td>'
                f'<td>Revert {_code(c["sha"])}</td>'
                f'<td style="font-size:12px">Re-run failing suites; confirm green before proceeding</td></tr>'
            )
    else:
        H.append('<tr><td>1</td><td colspan="2">Provide git log to get specific revert commands</td></tr>')
    H.append('</tbody></table>')

    # ── Section 7: Reproducer ────────────────────────────────────────────────
    H.append(_section(7, "Reproducer — Shortest Sequence on Tuxmaker"))
    sha_bad = delta.get("sha_bad", "HEAD")
    sha_good = delta.get("sha_good", "HEAD~10")
    revert_cmd = " ".join(c["sha"] for c in commits) if commits else "<failing-sha>"
    first_failing = (fail_suites[0] if fail_suites else "<suite>")
    H.append(_pre(
        f"# 1. Confirm failing SHA\n"
        f"cat {log_path}kernel.sha\n\n"
        f"# 2. Fastest confirmer — run smallest failing suite\n"
        f"cd /home/ciuser && ./run-suite.sh {first_failing} $(git rev-parse HEAD)\n\n"
        f"# 3. If KVM unit tests are involved — fast PV intercept check (~30s)\n"
        f"cd /home/ciuser/linux\n"
        f"./tools/testing/selftests/kvm/run_tests.sh -a s390x 2>&1 | grep -E 'PASS|FAIL|timeout'\n\n"
        f"# 4. After revert\n"
        f"git revert --no-commit {revert_cmd}\n"
        f"git commit -m 'Revert CI regression run #{run_id}'\n"
        + (f"\n# 5. Confirm all previously-failing suites\n"
           + "\n".join(f"./run-suite.sh {s} HEAD" for s in fail_suites[:6])
           if fail_suites else "")
    ))

    # ── Footer ────────────────────────────────────────────────────────────────
    H.append(f"""
<footer>
  Generated by CIIQ local engine &middot; Run {_h(run_id)} &middot; {_h(run_date)} &middot; No external API<br>
  <span style="color:#aab">Made with IBM Bob</span>
</footer>
</body>
</html>""")

    return "".join(H)


# ─────────────────────────────────────────────────────────────────────────────
#  Route — HTML report
# ─────────────────────────────────────────────────────────────────────────────
@app.post("/api/report")
@require_json
def api_report():
    """
    Generate a self-contained HTML root-cause report and return it as a
    downloadable file.

    Request body (same shape as /api/analyse/local):
      mail_text   — raw CI mail text (optional; used to enrich suite status/dumps)
      delta       — {sha_good, sha_bad, git_log, git_diff_stat, git_patch, env_versions}
      suite_logs  — {suite: log_text}  (flat dict, project-keyed, or omit)
      run_date    — YYYY-MM-DD
      run_id      — numeric run ID string
    """
    body = request.get_json()
    run_date      = body.get("run_date",     datetime.today().strftime("%Y-%m-%d"))
    run_id        = body.get("run_id",       "????")
    delta_        = body.get("delta",        {})
    mail_text     = body.get("mail_text",    "")
    raw_logs      = body.get("suite_logs",   {})
    ui_status     = body.get("suite_status", {})  # UI badges — authoritative

    # Parse CI mail if provided, else build a minimal parsed dict from suite_logs
    if mail_text and mail_text.strip():
        parsed = _parse_ci_mail(mail_text)
        if parsed["run_date"]:
            run_date = parsed["run_date"]
        if parsed["run_id"]:
            run_id = parsed["run_id"]
    else:
        # Build suite_status from whatever logs we have
        parsed = {
            "run_date":     run_date,
            "run_id":       run_id,
            "web_url":      "",
            "log_path":     "",
            "kernel_key":   {},
            "suite_logs":   {},
            "suite_status": {},
            "dumps":        [],
        }

    # Merge flat/nested suite_logs from request into parsed.suite_logs
    PROJ_SUITES = {
        proj: [s["name"] for s in CFG.get("projects", {}).get(proj, {}).get("suites", [])]
        for proj in ("kvm", "qemu", "libvirt")
    }
    flat_logs: dict[str, str] = {}
    if isinstance(raw_logs, dict):
        for k, v in raw_logs.items():
            if k in ("kvm", "qemu", "libvirt") and isinstance(v, dict):
                flat_logs.update(v)
            else:
                flat_logs[k] = v

    for suite, text in flat_logs.items():
        if text and text.strip():
            if suite not in parsed["suite_logs"]:
                parsed["suite_logs"][suite] = text
            if suite not in parsed["suite_status"]:
                scan = _scan_log(text)
                parsed["suite_status"][suite] = "FAIL" if scan["hits"] else "PASS"

    # UI badge values (from collectSuiteStatus) always win — they are the ground truth
    if ui_status:
        parsed["suite_status"].update(ui_status)

    ci = CFG.get("ci", {})
    webui_base = ci.get("webui_base", "https://lnxgwne1.boeblingen.de.ibm.com/linux-ci/webui/ci-run")

    try:
        html = _render_html_report(
            parsed=parsed,
            delta=delta_,
            suite_logs=flat_logs,
            run_date=run_date,
            run_id=run_id,
            webui_base=webui_base,
        )
        from flask import Response
        filename = f"ciiq-run-{run_id}-root-cause-report.html"
        return Response(
            html,
            mimetype="text/html",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )
    except Exception as exc:
        log.exception("Report render error")
        return err(str(exc), 500)


# ─────────────────────────────────────────────────────────────────────────────
#  Routes — Session history
# ─────────────────────────────────────────────────────────────────────────────
@app.get("/api/history")
def api_history():
    return jsonify({"ok": True, "history": session.get("ciiq_history", [])})


@app.delete("/api/history")
def api_clear_history():
    session.pop("ciiq_history", None)
    return jsonify({"ok": True})


# ─────────────────────────────────────────────────────────────────────────────
#  Entry point
# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    srv = CFG.get("server", {})
    app.run(
        host=srv.get("host", "0.0.0.0"),
        port=int(srv.get("port", 5100)),
        debug=srv.get("debug", False),
    )
