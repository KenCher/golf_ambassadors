"""
CIIQ — CI Intelligence & Insight Query  (Orchestrate / Agentic edition)
Uses IBM watsonx tool-calling (llama-3-3-70b-instruct) to run a multi-turn
ReAct agent loop for CI root-cause analysis.

How it works:
  The agent receives the git delta + suite logs and a set of tool definitions.
  It autonomously PLANS which tools to call and in what order:

  Turn 1  → model calls scan_ci_logs(suite, log_text, project)
             for each failing suite it judges important
  Turn 2  → model calls extract_git_commits(git_log, project)
             to identify the introducing commit
  Turn 3  → model calls correlate_failures(kvm, qemu, libvirt)
             to build the cross-project map
  Turn 4  → model calls draft_bugzilla_comment(...)
             to produce the final structured output
  Turn 5  → model produces final text response

Compared to app-wx.py (single prompt):
  - Model DECIDES which suites are most relevant, not all of them
  - Model ACTIVELY correlates findings rather than receiving pre-written text
  - Model DRAFTS the Bugzilla comment in a structured tool call
  - Produces token-usage trace per tool call for visibility

For watsonx Orchestrate SaaS:
  The four tool functions below become "external skills" registered in WXO.
  Replace the IAM+REST calls with your WXO zone_token and POST to:
  https://dl.watson-orchestrate.ibm.com/api/v1/chat/completions

Endpoints (identical URL structure to app.py / app-wx.py):
  GET  /                         Serve CIIQ UI
  GET  /api/config               Config + engine type ("orchestrate")
  POST /api/token                IAM token exchange
  POST /api/analyse/<project>    Agentic single-project analysis
  POST /api/analyse/all          Agentic all-three-projects analysis
  POST /api/correlate            Agentic cross-project correlation
  GET  /api/runs                 List CI run dates
  GET  /api/run/<date>/suites    Suite log snippets
  GET  /api/history              Session history
  DELETE /api/history            Clear history
"""

import os
import re
import json
import time
import logging
from datetime import datetime
from functools import wraps
from typing import Optional

import requests
import yaml
from flask import Flask, jsonify, request, render_template, session
from flask_cors import CORS
from dotenv import load_dotenv

# ─────────────────────────────────────────────────────────────────────────────
#  Bootstrap
# ─────────────────────────────────────────────────────────────────────────────
load_dotenv()

BASE_DIR    = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(BASE_DIR, "config-orch.yaml")
if not os.path.isfile(CONFIG_PATH):
    CONFIG_PATH = os.path.join(BASE_DIR, "config.yaml")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)
log = logging.getLogger("ciiq.orch")


def _expand_env(value: str) -> str:
    return re.sub(r"\$\{(\w+)\}", lambda m: os.environ.get(m.group(1), ""), value)


def load_config() -> dict:
    with open(CONFIG_PATH) as f:
        raw = yaml.safe_load(f)

    def expand(obj):
        if isinstance(obj, str):   return _expand_env(obj)
        if isinstance(obj, dict):  return {k: expand(v) for k, v in obj.items()}
        if isinstance(obj, list):  return [expand(i) for i in obj]
        return obj

    return expand(raw)


CFG = load_config()

app = Flask(__name__, template_folder="templates", static_folder="static")
app.secret_key = CFG.get("server", {}).get("secret_key") or os.urandom(32)
CORS(app)

WX_CFG = CFG.get("watsonx", {})

# ─────────────────────────────────────────────────────────────────────────────
#  IAM token cache
# ─────────────────────────────────────────────────────────────────────────────
_iam_cache: dict = {"token": None, "expires_at": 0.0}


def get_iam_token(api_key: str) -> str:
    """Return a valid IBM IAM Bearer token, refreshing if needed."""
    now = time.time()
    if _iam_cache["token"] and now < _iam_cache["expires_at"]:
        return _iam_cache["token"]
    log.info("Refreshing IAM token...")
    resp = requests.post(
        "https://iam.cloud.ibm.com/identity/token",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        data={"grant_type": "urn:ibm:params:oauth:grant-type:apikey", "apikey": api_key},
        timeout=15,
    )
    resp.raise_for_status()
    d = resp.json()
    _iam_cache["token"]      = d["access_token"]
    _iam_cache["expires_at"] = now + d.get("expires_in", 3600) - 60
    log.info("IAM token refreshed")
    return _iam_cache["token"]


# ─────────────────────────────────────────────────────────────────────────────
#  Agentic tool definitions — the "skills" the model can call
# ─────────────────────────────────────────────────────────────────────────────

# Error and subsystem patterns (same as app.py local engine)
_ERROR_PATTERNS = [
    (re.compile(r'\bBUG:\s',            re.I), "kernel BUG"),
    (re.compile(r'\bKernel panic\b',    re.I), "kernel panic"),
    (re.compile(r'\bOops\b'),                   "kernel Oops"),
    (re.compile(r'\bgeneral protection fault\b', re.I), "GPF"),
    (re.compile(r'\bsegfault\b|\bsegmentation fault\b', re.I), "segfault"),
    (re.compile(r'\bNULL pointer dereference\b', re.I), "NULL deref"),
    (re.compile(r'\buse-after-free\b',  re.I), "use-after-free"),
    (re.compile(r'\bdeadlock\b',        re.I), "deadlock"),
    (re.compile(r'\bWARN_ON\b|\bWARNING:\s'),    "kernel WARNING"),
    (re.compile(r'\bTIMEOUT\b|\btimeout\b'),     "timeout"),
    (re.compile(r'\bFAIL\b|\bFAILED\b'),         "test FAIL"),
    (re.compile(r'\bERROR:\s|\berror:\s'),        "ERROR"),
    (re.compile(r'\bAborted\b'),                 "abort"),
    (re.compile(r'\bNo such device\b',  re.I), "device not found"),
    (re.compile(r'\bOut of memory\b|\bOOM\b', re.I), "OOM"),
    (re.compile(r'\bmigration failed\b', re.I), "migration failure"),
]
_SUBSYSTEM_RE = {
    "KVM core":       re.compile(r'\bkvm\b|\bKVM\b|\bSIE\b|\bvcpu\b'),
    "s390x arch":     re.compile(r'\bs390\b|\bs390x\b|\bz/VM\b'),
    "memory mgmt":    re.compile(r'\bgfn\b|\bpfn\b|\bpfault\b|\bHugePage\b'),
    "VFIO":           re.compile(r'\bvfio\b|\bVFIO\b|\biommu\b'),
    "virtio":         re.compile(r'\bvirtio\b|\bvirtqueue\b'),
    "live migration": re.compile(r'\bmigrat\b|\blive mig\b', re.I),
    "CPU model":      re.compile(r'\bcpu model\b|\bfacility\b', re.I),
    "QMP/monitor":    re.compile(r'\bQMP\b|\bqmp\b'),
    "libvirt driver": re.compile(r'\bvirDomain\b|\bqemuDomain\b'),
    "QEMU block":     re.compile(r'\bblkdev\b|\bblk_\b|\bqcow\b', re.I),
}
_COMMIT_RE = re.compile(r'^([0-9a-f]{7,40})\s+(.+)', re.MULTILINE)

_EXPERT_CONTEXT = {
    "kvm": (
        "KVM s390x uses the SIE mechanism. Intercept handling, VSIE, pfault, "
        "protected virtualisation, and vcpu mutex discipline are the key areas."
    ),
    "qemu": (
        "QEMU s390x uses KVM_SET/GET_ONE_REG for CPU state. Live migration streams, "
        "machine type compatibility, and QMP communication are common failure points."
    ),
    "libvirt": (
        "libvirt communicates with QEMU via QMP. s390x domain configuration, "
        "virsh migrate, and CPU model detection are common regression areas."
    ),
}


def _tool_scan_ci_logs(suite: str, log_text: str, project: str) -> dict:
    """
    Tool: scan_ci_logs
    Scan a single CI suite log and return structured findings.
    This is what the model calls for each failing suite.
    """
    hits:       dict[str, int]  = {}
    subsystems: list[str]       = []
    error_lines: list[str]      = []

    for pat, label in _ERROR_PATTERNS:
        c = len(pat.findall(log_text))
        if c:
            hits[label] = c

    for name, pat in _SUBSYSTEM_RE.items():
        if pat.search(log_text):
            subsystems.append(name)

    for line in log_text.splitlines():
        if any(p.search(line) for p, _ in _ERROR_PATTERNS[:10]):
            s = line.strip()
            if s and s not in error_lines:
                error_lines.append(s)
            if len(error_lines) >= 3:
                break

    return {
        "suite":       suite,
        "project":     project,
        "status":      "FAIL" if hits else "PASS",
        "error_sigs":  hits,
        "subsystems":  subsystems,
        "sample_lines": error_lines,
        "severity":    "critical" if any(
                           k in hits for k in ("kernel BUG","kernel panic","NULL deref")
                       ) else "warning" if hits else "none",
    }


def _tool_extract_git_commits(git_log: str, project: str) -> dict:
    """
    Tool: extract_git_commits
    Parse git log output and return structured commit list with relevance hints.
    """
    commits = []
    for m in _COMMIT_RE.finditer(git_log):
        sha, subject = m.group(1), m.group(2).strip()
        # Score relevance to the project
        relevance = "high" if any(
            kw in subject.lower() for kw in
            [project, "kvm", "s390", "vcpu", "migration", "qemu", "libvirt"]
        ) else "low"
        commits.append({"sha": sha, "subject": subject, "relevance": relevance})

    top = [c for c in commits if c["relevance"] == "high"] or commits[:3]
    return {
        "project":          project,
        "total_commits":    len(commits),
        "relevant_commits": top[:5],
        "top_suspect":      top[0] if top else None,
        "context":          _EXPERT_CONTEXT.get(project, ""),
    }


def _tool_correlate_failures(
    kvm_findings: str,
    qemu_findings: str,
    libvirt_findings: str,
    git_commits: str,
) -> dict:
    """
    Tool: correlate_failures
    Cross-correlate per-project scan results and commit list to identify
    shared root cause, dependency chain, and minimum fix set.
    """
    kvm_f  = json.loads(kvm_findings)  if kvm_findings  else {}
    qemu_f = json.loads(qemu_findings) if qemu_findings else {}
    lib_f  = json.loads(libvirt_findings) if libvirt_findings else {}
    commits = json.loads(git_commits) if git_commits else {}

    # Find shared error signatures
    all_sigs: dict[str, list[str]] = {}
    for proj, findings in [("kvm", kvm_f), ("qemu", qemu_f), ("libvirt", lib_f)]:
        for sig in findings.get("error_sigs", {}).keys():
            all_sigs.setdefault(sig, []).append(proj)
    shared = {sig: projs for sig, projs in all_sigs.items() if len(projs) > 1}

    # Determine cascade
    failing  = [p for p, f in [("kvm",kvm_f),("qemu",qemu_f),("libvirt",lib_f)]
                if f.get("status") == "FAIL" or f.get("error_sigs")]
    cascade  = " → ".join(failing) if failing else "No cascade detected"

    top_commit = commits.get("top_suspect") if isinstance(commits, dict) else None
    min_fix = (
        f"git revert {top_commit['sha']}  # \"{top_commit['subject']}\""
        if top_commit else "No specific commit identified — provide git_log"
    )

    return {
        "shared_error_signatures": shared,
        "failing_projects":        failing,
        "cascade":                 cascade,
        "likely_root_commit":      top_commit,
        "minimum_fix":             min_fix,
        "triage_order":            failing[::-1],  # fix deepest layer first
    }


def _tool_draft_bugzilla_comment(
    run_date: str,
    run_id: str,
    project: str,
    scan_result: str,
    commit_result: str,
    correlation_result: str,
) -> dict:
    """
    Tool: draft_bugzilla_comment
    Produce a complete structured Bugzilla-ready comment from the gathered evidence.
    This is always the final tool the model calls.
    """
    scan   = json.loads(scan_result)   if scan_result   else {}
    commit = json.loads(commit_result) if commit_result else {}
    corr   = json.loads(correlation_result) if correlation_result else {}
    if not isinstance(corr, dict): corr = {}

    top    = commit.get("top_suspect") or corr.get("likely_root_commit") or {}
    if not isinstance(top, dict): top = {}
    sigs   = scan.get("error_sigs",  {}) if isinstance(scan, dict) else {}
    subs   = scan.get("subsystems",  []) if isinstance(scan, dict) else []
    samples= scan.get("sample_lines", []) if isinstance(scan, dict) else []
    ts     = top if isinstance(top, dict) and top.get("sha") else None
    fix    = (corr.get("minimum_fix")
              or (f"git revert {ts['sha']}  # \"{ts['subject']}\""
                  if ts else "Bisect between last-good and current HEAD"))

    lines = [
        f"## CI Failure Report — Run {run_date}  {run_id}  [{project.upper()}]",
        f"*Generated by CIIQ Orchestrate agent*",
        "",
        f"### Introducing Commit",
        f"`{top.get('sha','unknown')}` {top.get('subject','(no commit identified)')}",
        "",
        f"### Root Cause",
        f"Error signatures: {', '.join(f'{k}(×{v})' for k,v in list(sigs.items())[:4]) or 'none detected'}.",
        "",
    ]
    if samples:
        lines += ["Representative failure lines:"]
        for s in samples[:3]:
            lines.append(f"> `{s[:120]}`")
        lines.append("")

    lines += [
        f"### Affected Subsystems",
        "\n".join(f"- {s}" for s in subs) or "- (not determined)",
        "",
        f"### Cross-Project Impact",
        f"Cascade: {corr.get('cascade','unknown')}",
        "",
        f"### Recommended Fix",
        f"```bash\n{fix}\n```",
        "",
        f"### Verification",
        f"```bash",
        f"cd /home/ciuser && ./run-suite.sh {scan.get('suite','<suite>')} $(git rev-parse HEAD)",
        f"```",
    ]

    return {
        "comment": "\n".join(lines),
        "summary": f"{project.upper()} failure traced to {top.get('sha','?')}: "
                   f"{top.get('subject','unknown')}",
    }


# ─────────────────────────────────────────────────────────────────────────────
#  Tool registry
# ─────────────────────────────────────────────────────────────────────────────
_AGENT_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "scan_ci_logs",
            "description": (
                "Scan a CI suite log text for error signatures, subsystem identifiers, "
                "and representative failure lines. Returns structured findings including "
                "severity level and a list of matched error patterns."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "suite":    {"type": "string", "description": "CI suite name (e.g. 'hades')"},
                    "log_text": {"type": "string", "description": "Raw log text to scan"},
                    "project":  {"type": "string", "enum": ["kvm","qemu","libvirt"],
                                 "description": "Project this suite belongs to"},
                },
                "required": ["suite", "log_text", "project"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "extract_git_commits",
            "description": (
                "Parse git log output into a structured commit list with relevance scores "
                "for the given project. Identifies the most likely introducing commit."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "git_log": {"type": "string", "description": "Output of git log --oneline"},
                    "project": {"type": "string", "enum": ["kvm","qemu","libvirt"]},
                },
                "required": ["git_log", "project"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "correlate_failures",
            "description": (
                "Cross-correlate per-project scan results and commit data to identify "
                "shared root cause, dependency cascade (kernel→QEMU→libvirt), and the "
                "minimum set of reverts to restore all three projects."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "kvm_findings":      {"type": "string",
                                          "description": "JSON result from scan_ci_logs for KVM"},
                    "qemu_findings":     {"type": "string",
                                          "description": "JSON result from scan_ci_logs for QEMU"},
                    "libvirt_findings":  {"type": "string",
                                          "description": "JSON result from scan_ci_logs for libvirt"},
                    "git_commits":       {"type": "string",
                                          "description": "JSON result from extract_git_commits"},
                },
                "required": ["kvm_findings", "qemu_findings", "libvirt_findings", "git_commits"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "draft_bugzilla_comment",
            "description": (
                "Produce a complete Bugzilla-ready comment from the gathered evidence. "
                "Call this as the LAST tool after all scans and correlation are done."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "run_date":           {"type": "string"},
                    "run_id":             {"type": "string"},
                    "project":            {"type": "string", "enum": ["kvm","qemu","libvirt","all"]},
                    "scan_result":        {"type": "string",
                                           "description": "JSON result from scan_ci_logs"},
                    "commit_result":      {"type": "string",
                                           "description": "JSON result from extract_git_commits"},
                    "correlation_result": {"type": "string",
                                           "description": "JSON result from correlate_failures"},
                },
                "required": ["run_date", "run_id", "project",
                             "scan_result", "commit_result", "correlation_result"],
            },
        },
    },
]

_TOOL_FNS = {
    "scan_ci_logs":        lambda a: _tool_scan_ci_logs(
                               a["suite"], a["log_text"], a["project"]),
    "extract_git_commits": lambda a: _tool_extract_git_commits(
                               a["git_log"], a["project"]),
    "correlate_failures":  lambda a: _tool_correlate_failures(
                               a.get("kvm_findings","{}"),
                               a.get("qemu_findings","{}"),
                               a.get("libvirt_findings","{}"),
                               a.get("git_commits","{}")),
    "draft_bugzilla_comment": lambda a: _tool_draft_bugzilla_comment(
                               a["run_date"], a["run_id"], a["project"],
                               a.get("scan_result","{}"),
                               a.get("commit_result","{}"),
                               a.get("correlation_result","{}")),
}


# ─────────────────────────────────────────────────────────────────────────────
#  Agent loop
# ─────────────────────────────────────────────────────────────────────────────
_SYSTEM_PROMPT = """\
You are CIIQ Agent, an expert CI failure analyst for IBM KVM, QEMU, and libvirt on s390x.

You have four tools: scan_ci_logs, extract_git_commits, correlate_failures, draft_bugzilla_comment.

Follow this EXACT sequence — call each tool in order, never skip a step:
Step 1: Call scan_ci_logs once for EACH failing suite listed (one call per suite).
Step 2: Call extract_git_commits with the git log text and project name.
Step 3: Call correlate_failures with all scan results and commit result as JSON strings. Use "{}" for missing projects.
Step 4: Call draft_bugzilla_comment ONCE with results from steps 1, 2, and 3.
Step 5: Output the "comment" field from step 4 as your final text reply.

IMPORTANT: You MUST call correlate_failures before draft_bugzilla_comment.
Do NOT produce any text response until after step 4 completes.
"""


def _agent_loop(
    token: str,
    messages: list,
    model: str,
    project_id: str,
    max_turns: int = 8,
) -> tuple[str, list[dict]]:
    """
    Run a multi-turn tool-calling loop.
    Returns (final_text, tool_call_trace).
    """
    url     = f"{WX_CFG.get('region','us-south')}"
    wx_url  = f"https://{url}.ml.cloud.ibm.com/ml/v1/text/chat?version=2024-05-01"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    trace   = []

    for turn in range(max_turns):
        for _retry in range(4):
            resp = requests.post(wx_url, headers=headers, json={
                "model_id":   model,
                "project_id": project_id,
                "messages":   messages,
                "tools":      _AGENT_TOOLS,
                "tool_choice": "auto",
                "parameters": {"max_new_tokens": int(WX_CFG.get("max_tokens", 1200))},
            }, timeout=120)
            if resp.status_code == 429:
                wait = int(resp.headers.get("Retry-After", 30)) + 5
                log.warning("Rate limited — waiting %ds before retry %d/3", wait, _retry+1)
                time.sleep(wait)
                continue
            resp.raise_for_status()
            break
        else:
            raise RuntimeError("Exceeded rate-limit retries")

        data = resp.json()
        msg  = data["choices"][0]["message"]
        messages.append(msg)
        usage = data.get("usage", {})
        log.info("Agent turn %d — in:%s out:%s tool_calls:%d",
                 turn + 1,
                 usage.get("prompt_tokens", "?"),
                 usage.get("completion_tokens", "?"),
                 len(msg.get("tool_calls") or []))

        if not msg.get("tool_calls"):
            return msg.get("content", ""), trace

        # Execute all tool calls
        for tc in msg["tool_calls"]:
            fn_name = tc["function"]["name"]
            fn_args = json.loads(tc["function"]["arguments"])
            fn      = _TOOL_FNS.get(fn_name)
            result  = fn(fn_args) if fn else {"error": f"Unknown tool: {fn_name}"}
            trace.append({"tool": fn_name, "args": fn_args, "result": result})
            log.info("  → %s(%s) → %s", fn_name,
                     list(fn_args.keys()), list(result.keys()))
            messages.append({
                "role":         "tool",
                "tool_call_id": tc["id"],
                "content":      json.dumps(result),
            })

    return "Max agent turns reached.", trace


def _run_agent(
    project: str,
    delta: dict,
    suite_logs: dict,
    run_date: str,
    run_id: str,
    token: str,
    project_id: str,
) -> tuple[str, list[dict]]:
    """Build the initial prompt and launch the agent loop."""
    model = WX_CFG.get("agent_model", "meta-llama/llama-3-3-70b-instruct")

    # Summarise available suites for the model
    suite_summary = "\n".join(
        f"- {suite}: {'(has log)' if log_txt and log_txt.strip() else '(empty)'}"
        for suite, log_txt in suite_logs.items()
    )

    user_msg = (
        f"Analyse CI failures for project: {project.upper()}\n"
        f"Run date: {run_date}  Run ID: {run_id}\n\n"
        f"Available suites:\n{suite_summary}\n\n"
        f"Git delta summary:\n"
        f"  Last passing SHA: {delta.get('sha_good','(not provided)')}\n"
        f"  Failing SHA:      {delta.get('sha_bad','(not provided)')}\n"
        f"  git log:\n{delta.get('git_log','(not provided)')[:600]}\n\n"
        f"Full suite logs follow. Scan each failing suite, extract the introducing commit, "
        f"then draft a Bugzilla comment with your findings.\n\n"
        + "\n\n".join(
            f"=== Suite: {suite} ===\n{txt[:800]}"
            for suite, txt in suite_logs.items()
            if txt and txt.strip()
        )
    )

    messages = [
        {"role": "system", "content": _SYSTEM_PROMPT},
        {"role": "user",   "content": user_msg},
    ]

    return _agent_loop(token, messages, model, project_id)


# ─────────────────────────────────────────────────────────────────────────────
#  History helpers
# ─────────────────────────────────────────────────────────────────────────────
def _add_history(project: str, status: str, summary: str) -> None:
    if "ciiq_history" not in session:
        session["ciiq_history"] = []
    session["ciiq_history"].insert(0, {
        "ts":      datetime.now().strftime("%H:%M:%S"),
        "project": project,
        "status":  status,
        "summary": summary[:200],
        "engine":  "orchestrate",
    })
    session.modified = True


# ─────────────────────────────────────────────────────────────────────────────
#  Request helpers
# ─────────────────────────────────────────────────────────────────────────────
_PLACEHOLDERS = {
    "your_ibm_cloud_api_key_here", "your_watsonx_project_id_here",
    "placeholder", "test-key-placeholder",
}


def _resolve_api_key(body: dict) -> str:
    v = body.get("api_key") or WX_CFG.get("api_key") or \
        os.environ.get("CIIQ_WATSONX_API_KEY", "")
    return "" if v in _PLACEHOLDERS else v


def _resolve_project_id(body: dict) -> str:
    v = body.get("project_id") or WX_CFG.get("project_id") or \
        os.environ.get("CIIQ_WATSONX_PROJECT_ID", "")
    return "" if v in _PLACEHOLDERS else v


def err(msg: str, code: int = 400):
    return jsonify({"ok": False, "error": msg}), code


def require_json(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not request.is_json:
            return err("Request must be JSON")
        return f(*args, **kwargs)
    return wrapper


# ─────────────────────────────────────────────────────────────────────────────
#  Routes
# ─────────────────────────────────────────────────────────────────────────────
@app.get("/")
def index():
    return render_template("ciiq.html")


@app.get("/api/config")
def api_config():
    ci = CFG.get("ci", {})
    return jsonify({
        "ok": True,
        "engine": "orchestrate",
        "agent_model":   WX_CFG.get("agent_model"),
        "max_turns":     WX_CFG.get("max_agent_turns", 8),
        "has_api_key":   bool(WX_CFG.get("api_key")),
        "has_project_id":bool(WX_CFG.get("project_id")),
        "ci": {
            "log_base":      ci.get("log_base"),
            "webui_base":    ci.get("webui_base"),
            "tuxmaker_host": ci.get("tuxmaker_host"),
        },
        "projects": {
            proj: [s["name"] for s in data["suites"]]
            for proj, data in CFG.get("projects", {}).items()
        },
        "tools": [t["function"]["name"] for t in _AGENT_TOOLS],
    })


@app.post("/api/token")
@require_json
def api_token():
    body    = request.get_json()
    api_key = _resolve_api_key(body)
    if not api_key:
        return err("api_key required")
    try:
        tok = get_iam_token(api_key)
        return jsonify({"ok": True, "token_preview": tok[:12] + "…"})
    except Exception as exc:
        return err(str(exc), 502)


@app.post("/api/analyse/<project>")
@require_json
def api_analyse_project(project: str):
    if project not in ("kvm", "qemu", "libvirt"):
        return err(f"Unknown project '{project}'")

    body       = request.get_json()
    api_key    = _resolve_api_key(body)
    project_id = _resolve_project_id(body)
    if not api_key:    return err("api_key required")
    if not project_id: return err("project_id required")

    delta      = body.get("delta", {})
    suite_logs = body.get("suite_logs", {})
    run_date   = body.get("run_date", datetime.today().strftime("%Y-%m-%d"))
    run_id     = body.get("run_id", "#????")

    if not suite_logs:
        return err("suite_logs required (dict of suite_name → log_text)")

    try:
        token  = get_iam_token(api_key)
        text, trace = _run_agent(project, delta, suite_logs, run_date, run_id,
                                  token, project_id)
        _add_history(project, "ok", text)
        return jsonify({
            "ok":        True,
            "project":   project,
            "analysis":  text,
            "engine":    "orchestrate",
            "model":     WX_CFG.get("agent_model"),
            "tool_trace": trace,
            "run_date":  run_date,
            "run_id":    run_id,
        })
    except requests.HTTPError as exc:
        msg = f"HTTP {exc.response.status_code}: {exc.response.text[:400]}"
        _add_history(project, "err", msg)
        return err(msg, 502)
    except Exception as exc:
        _add_history(project, "err", str(exc))
        log.exception("Agent error for %s", project)
        return err(str(exc), 500)


@app.post("/api/analyse/all")
@require_json
def api_analyse_all():
    body       = request.get_json()
    api_key    = _resolve_api_key(body)
    project_id = _resolve_project_id(body)
    if not api_key:    return err("api_key required")
    if not project_id: return err("project_id required")

    raw_logs   = body.get("suite_logs", {})
    delta      = body.get("delta", {})
    run_date   = body.get("run_date", datetime.today().strftime("%Y-%m-%d"))
    run_id     = body.get("run_id", "#????")

    # Auto-split flat logs
    PROJ_SUITES = {
        proj: [s["name"] for s in CFG.get("projects",{}).get(proj,{}).get("suites",[])]
        for proj in ("kvm","qemu","libvirt")
    }
    is_flat = raw_logs and not any(k in raw_logs for k in ("kvm","qemu","libvirt"))
    if is_flat:
        all_logs: dict[str,dict] = {"kvm":{},"qemu":{},"libvirt":{}}
        for sn, sl in raw_logs.items():
            for proj, suites in PROJ_SUITES.items():
                if sn in suites:
                    all_logs[proj][sn] = sl
                    break
    else:
        all_logs = raw_logs

    results, errors, all_traces = {}, {}, {}
    stagger = WX_CFG.get("call_stagger_ms", 300) / 1000.0

    try:
        token = get_iam_token(api_key)
    except Exception as exc:
        return err(f"IAM token error: {exc}", 502)

    for project in ("kvm", "qemu", "libvirt"):
        slogs = all_logs.get(project, {})
        if not slogs:
            log.warning("No suite logs for %s — skipping", project)
            continue
        try:
            text, trace = _run_agent(project, delta, slogs, run_date, run_id,
                                      token, project_id)
            results[project] = {"analysis": text}
            all_traces[project] = trace
            _add_history(project, "ok", text)
            log.info("Completed %s — sleeping %.1fs", project, stagger)
            time.sleep(stagger)
        except Exception as exc:
            errors[project] = str(exc)
            _add_history(project, "err", str(exc))
            log.exception("Agent error for %s", project)

    return jsonify({
        "ok":        True,
        "results":   results,
        "errors":    errors,
        "engine":    "orchestrate",
        "model":     WX_CFG.get("agent_model"),
        "tool_traces": all_traces,
        "run_date":  run_date,
        "run_id":    run_id,
    })


@app.post("/api/correlate")
@require_json
def api_correlate():
    body       = request.get_json()
    api_key    = _resolve_api_key(body)
    project_id = _resolve_project_id(body)
    if not api_key:    return err("api_key required")
    if not project_id: return err("project_id required")

    delta     = body.get("delta", {})
    analyses  = body.get("analyses", {})
    run_date  = body.get("run_date", datetime.today().strftime("%Y-%m-%d"))
    run_id    = body.get("run_id",   "#????")
    model     = WX_CFG.get("agent_model", "meta-llama/llama-3-3-70b-instruct")

    # Build fake scan results from the analyses text for the correlation tool
    dummy_scan = json.dumps({"error_sigs": {}, "status": "FAIL",
                              "suite": "all", "subsystems": [],
                              "sample_lines": [], "severity": "warning"})
    commit_r   = json.dumps(_tool_extract_git_commits(
                     delta.get("git_log",""), "all"))
    corr_r     = json.dumps(_tool_correlate_failures(
                     dummy_scan, dummy_scan, dummy_scan, commit_r))
    bz         = _tool_draft_bugzilla_comment(
                     run_date, run_id, "all",
                     dummy_scan, commit_r, corr_r)

    # Also ask the model to synthesise a narrative from all three analyses
    try:
        token = get_iam_token(api_key)
        messages = [
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user",   "content": (
                f"Correlate these three project analyses for CI run {run_date} {run_id}:\n\n"
                f"## KVM\n{analyses.get('kvm','(not provided)')[:600]}\n\n"
                f"## QEMU\n{analyses.get('qemu','(not provided)')[:600]}\n\n"
                f"## libvirt\n{analyses.get('libvirt','(not provided)')[:600]}\n\n"
                f"Git delta:\n{delta.get('git_log','(not provided)')[:400]}\n\n"
                f"Call correlate_failures and draft_bugzilla_comment to produce the final report."
            )},
        ]
        text, trace = _agent_loop(token, messages, model, project_id)
        _add_history("correlation", "ok", text)
        return jsonify({
            "ok":          True,
            "correlation": text or bz["comment"],
            "engine":      "orchestrate",
            "model":       model,
            "tool_trace":  trace,
        })
    except Exception as exc:
        _add_history("correlation", "err", str(exc))
        log.exception("Correlation error")
        # Fall back to the locally-computed correlation
        return jsonify({
            "ok":          True,
            "correlation": bz["comment"],
            "engine":      "orchestrate-local-fallback",
            "error":       str(exc),
        })


@app.get("/api/runs")
def api_runs():
    log_base = CFG["ci"]["log_base"]
    runs = []
    if os.path.isdir(log_base):
        for entry in sorted(os.listdir(log_base), reverse=True):
            full = os.path.join(log_base, entry)
            if os.path.isdir(full) and re.match(r"^\d{8}$", entry):
                runs.append({
                    "date_raw": entry,
                    "date_fmt": f"{entry[:4]}-{entry[4:6]}-{entry[6:]}",
                    "has_sha":  os.path.isfile(os.path.join(full, "kernel.sha")),
                    "path":     full,
                })
    return jsonify({"ok": True, "runs": runs[:30], "log_base": log_base})


@app.get("/api/run/<date>/suites")
def api_run_suites(date: str):
    log_base = CFG["ci"]["log_base"]
    run_dir  = os.path.join(log_base, date.replace("-",""))
    suite_logs: dict[str,dict[str,str]] = {"kvm":{},"qemu":{},"libvirt":{}}

    for proj, data in CFG.get("projects",{}).items():
        for s in data.get("suites",[]):
            name    = s["name"]
            suite_d = os.path.join(run_dir, name)
            snippet = ""
            if os.path.isdir(suite_d):
                for root, _, files in os.walk(suite_d):
                    for fname in files:
                        if fname.endswith((".log",".txt",".out")):
                            try:
                                with open(os.path.join(root,fname), errors="replace") as f:
                                    lines = [l.rstrip() for l in f if re.search(
                                        r"(FAIL|BUG|Oops|panic|ERROR|error:|timeout|abort)",
                                        l, re.I)]
                                    snippet += "\n".join(lines[:10]) + "\n"
                            except OSError:
                                pass
            suite_logs[proj][name] = snippet.strip()

    sha_bad = ""
    sha_file = os.path.join(run_dir, "kernel.sha")
    if os.path.isfile(sha_file):
        sha_bad = open(sha_file).read().strip()

    return jsonify({"ok":True,"date":date,"suite_logs":suite_logs,
                    "sha_bad":sha_bad,"sha_good":""})


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
        port=int(srv.get("port", 5200)),
        debug=srv.get("debug", False),
    )
