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

import os
import re
import logging
from datetime import datetime
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
    (re.compile(r'\bERROR:\s|\berror:\s'),              "ERROR"),
    (re.compile(r'\bAborted\b|\baborted\b'),            "abort"),
    (re.compile(r'\bAssertionError\b'),                "assertion"),
    (re.compile(r'\bNo such device\b', re.IGNORECASE), "device not found"),
    (re.compile(r'\bPermission denied\b', re.IGNORECASE), "permission denied"),
    (re.compile(r'\bInvalid argument\b', re.IGNORECASE), "EINVAL"),
    (re.compile(r'\bOut of memory\b|\bOOM\b', re.IGNORECASE), "OOM"),
    (re.compile(r'\bmigration failed\b', re.IGNORECASE), "migration failure"),
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


def _scan_log(text: str) -> dict:
    """Scan a single log blob and return structured findings."""
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
) -> str:
    """
    Produce a structured Markdown analysis for one project using only local
    heuristics — no external API.
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

    for suite, log_text in suite_logs.items():
        scan = _scan_log(log_text or "")
        if scan["hits"]:
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
    if all_hits:
        top_errors = sorted(all_hits.items(), key=lambda x: -x[1])[:5]
        error_summary = ", ".join(f"{k} (×{v})" for k, v in top_errors)
        lines.append(
            f"Detected error signatures: **{error_summary}**. "
            f"{len(failing_suites)} suite(s) produced errors; "
            f"{len(passing_suites)} suite(s) passed."
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
            "All suites appear to have passed, or logs were not provided."
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
    return render_template("ciiq.html")


# ─────────────────────────────────────────────────────────────────────────────
#  Routes — Config
# ─────────────────────────────────────────────────────────────────────────────
@app.get("/api/config")
def api_config():
    """Return sanitised config."""
    ci = CFG.get("ci", {})
    return jsonify(
        {
            "ok": True,
            "engine": "local",
            "ci": {
                "log_base":      ci.get("log_base"),
                "webui_base":    ci.get("webui_base"),
                "tuxmaker_host": ci.get("tuxmaker_host"),
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
#  Routes — Analyse all three projects
# ─────────────────────────────────────────────────────────────────────────────
@app.post("/api/analyse/all")
@require_json
def api_analyse_all():
    body     = request.get_json()
    raw_logs = body.get("suite_logs", {})
    delta    = body.get("delta", {})
    run_date = body.get("run_date", datetime.today().strftime("%Y-%m-%d"))
    run_id   = body.get("run_id", "#????")

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

    results: dict[str, str] = {}
    errors:  dict[str, str] = {}

    for project in ("kvm", "qemu", "libvirt"):
        suite_logs = all_logs.get(project, {})
        if not suite_logs:
            log.warning("No suite logs for %s — skipping", project)
            continue
        try:
            text = analyse_project(project, delta, suite_logs, run_date, run_id)
            results[project] = text
            _add_history(project, "ok", text)
        except Exception as exc:
            errors[project] = str(exc)
            _add_history(project, "err", str(exc))
            log.exception("Error analysing %s", project)

    return jsonify(
        {
            "ok":       True,
            "results":  results,
            "errors":   errors,
            "engine":   "local",
            "run_date": run_date,
            "run_id":   run_id,
        }
    )


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


# ─────────────────────────────────────────────────────────────────────────────
#  Routes — Available CI runs
# ─────────────────────────────────────────────────────────────────────────────
@app.get("/api/runs")
def api_runs():
    """List run dates found under CI log_base (if accessible)."""
    log_base = CFG["ci"]["log_base"]
    runs = []
    if os.path.isdir(log_base):
        for entry in sorted(os.listdir(log_base), reverse=True):
            full = os.path.join(log_base, entry)
            if os.path.isdir(full) and re.match(r"^\d{8}$", entry):
                sha_file = os.path.join(full, "kernel.sha")
                runs.append(
                    {
                        "date_raw": entry,
                        "date_fmt": f"{entry[:4]}-{entry[4:6]}-{entry[6:]}",
                        "has_sha":  os.path.isfile(sha_file),
                        "path":     full,
                    }
                )
    return jsonify({"ok": True, "runs": runs[:30], "log_base": log_base})


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
