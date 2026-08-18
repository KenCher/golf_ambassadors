"""
CIIQ — CI Intelligence & Insight Query
Flask backend: WatsonX-powered root-cause analyser for KVM, QEMU, and libvirt CI failures.

Endpoints
---------
GET  /                          Serve the CIIQ UI
GET  /api/config                Return sanitised config (no secrets)
POST /api/token                 Exchange IBM Cloud API key for IAM Bearer token
POST /api/analyse/<project>     Run WatsonX analysis for one project
POST /api/analyse/all           Run all three projects sequentially
POST /api/correlate             Run cross-project correlation
GET  /api/runs                  List available CI run dates from log dir
GET  /api/run/<date>/suites     Return suite names + log snippets for a date
GET  /api/history               Return session analysis history
DELETE /api/history             Clear session history
"""

import os
import json
import re
import subprocess
import time
import logging
from datetime import datetime, timedelta
from functools import wraps

import requests
import yaml
from flask import Flask, jsonify, request, render_template, session
from flask_cors import CORS
from dotenv import load_dotenv

# ─────────────────────────────────────────────────────────────────────────────
#  Bootstrap
# ─────────────────────────────────────────────────────────────────────────────
load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
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

# Load the local rule-based engine once at startup
def _load_local_engine():
    import importlib.util, pathlib
    spec = importlib.util.spec_from_file_location(
        "ciiq_local", pathlib.Path(__file__).parent / "app.py"
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

_LOCAL_ENGINE = _load_local_engine()

app = Flask(__name__, template_folder="templates", static_folder="static")
app.secret_key = CFG.get("server", {}).get("secret_key") or os.urandom(32)
CORS(app)

# ─────────────────────────────────────────────────────────────────────────────
#  IAM token cache (per-process; good for single-worker deployments)
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
        data={
            "grant_type": "urn:ibm:params:oauth:grant-type:apikey",
            "apikey": api_key,
        },
        timeout=15,
    )
    resp.raise_for_status()
    data = resp.json()
    if "access_token" not in data:
        raise ValueError(f"IAM error: {data.get('errorMessage', json.dumps(data))}")

    _iam_cache["token"] = data["access_token"]
    _iam_cache["expires_at"] = now + data.get("expires_in", 3600) - 60
    log.info("IAM token refreshed (expires in ~%ds)", data.get("expires_in", 3600))
    return _iam_cache["token"]


# ─────────────────────────────────────────────────────────────────────────────
#  WatsonX inference
# ─────────────────────────────────────────────────────────────────────────────
WX_CFG = CFG.get("watsonx", {})


def wx_endpoint(region: str, custom_url: str = "") -> str:
    """Return the full WatsonX text generation URL for a given region or custom endpoint."""
    if custom_url:
        return custom_url
    return (
        f"https://{region}.ml.cloud.ibm.com/ml/v1/text/generation"
        "?version=2024-05-01"
    )


def wx_generate(prompt: str, token: str, overrides: dict | None = None) -> dict:
    """Call WatsonX text generation and return the full response dict.

    Retries up to 3 times on HTTP 429 (rate-limit) with exponential backoff:
    wait 5s, 15s, 45s before giving up.
    """
    params = {
        "region":     overrides.get("region",     WX_CFG.get("region",     "us-south"))                    if overrides else WX_CFG.get("region",     "us-south"),
        "model":      overrides.get("model",      WX_CFG.get("model",      "meta-llama/llama-3-3-70b-instruct")) if overrides else WX_CFG.get("model", "meta-llama/llama-3-3-70b-instruct"),
        "max_tokens": int(overrides.get("max_tokens", WX_CFG.get("max_tokens", 2048)))                      if overrides else int(WX_CFG.get("max_tokens", 2048)),
        "custom_url": overrides.get("custom_url", "")                                                       if overrides else "",
        "project_id": overrides.get("project_id", WX_CFG.get("project_id", ""))                            if overrides else WX_CFG.get("project_id", ""),
    }

    url = wx_endpoint(params["region"], params["custom_url"])
    payload = {
        "model_id": params["model"],
        "input": prompt,
        "parameters": {
            "decoding_method": "greedy",
            "max_new_tokens": params["max_tokens"],
            "min_new_tokens": 80,
            "repetition_penalty": 1.05,
        },
        "project_id": params["project_id"],
    }

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
    }

    # Three attempts total: try → wait 5s → try → wait 15s → try → give up.
    # _RETRY_WAITS[i] is the sleep after the i-th attempt (0-indexed).
    # Attempt 3 (i=2) has no wait — we raise immediately on that failure.
    _RETRY_WAITS = (5, 15)   # waits between attempt 1→2 and 2→3

    for attempt in range(1, 4):           # 1, 2, 3
        log.info("WatsonX call → model=%s tokens=%d attempt=%d/3",
                 params["model"], params["max_tokens"], attempt)
        resp = requests.post(url, headers=headers, json=payload, timeout=120)

        if resp.status_code != 429:
            resp.raise_for_status()
            return resp.json()

        # 429 received
        if attempt == 3:
            # All three attempts exhausted — raise with the 429 response attached
            log.error("WatsonX 429 rate-limit — all 3 attempts exhausted, giving up")
            resp.raise_for_status()

        wait = int(resp.headers.get("Retry-After", _RETRY_WAITS[attempt - 1]))
        log.warning("WatsonX 429 rate-limit — waiting %ds before attempt %d/3",
                    wait, attempt + 1)
        time.sleep(wait)

    # Unreachable — loop always returns or raises above
    raise RuntimeError("wx_generate: loop exited without returning")  # pragma: no cover


# ─────────────────────────────────────────────────────────────────────────────
#  Prompt builders
# ─────────────────────────────────────────────────────────────────────────────
PERSONAS = {
    "kvm": (
        "You are a senior IBM s390x KVM kernel engineer with expert knowledge of "
        "arch/s390/kvm/, the SIE mechanism, intercept handling, pfault, VSIE, "
        "protected virtualisation, and the KVM UAPI."
    ),
    "qemu": (
        "You are a senior QEMU engineer specialising in s390x KVM acceleration, "
        "CPU state serialisation, live migration, the KVM_SET_ONE_REG interface, "
        "and QEMU machine types for IBM Z."
    ),
    "libvirt": (
        "You are a senior libvirt engineer with deep knowledge of the QEMU driver, "
        "s390x domain configuration, virsh migrate, QMP monitor communication, "
        "and libvirt's CPU model detection for IBM Z."
    ),
}


def _git_context(delta: dict) -> str:
    parts = ["=== GIT DELTA (last passing run → failing run) ==="]
    if delta.get("sha_good") or delta.get("sha_bad"):
        parts.append(
            f"Last passing SHA: {delta.get('sha_good', '(not provided)')}\n"
            f"Failing run SHA:  {delta.get('sha_bad',  '(not provided)')}"
        )
    if delta.get("git_log"):
        parts.append(f"--- git log ---\n{delta['git_log']}")
    if delta.get("git_diff_stat"):
        parts.append(f"--- git diff --stat ---\n{delta['git_diff_stat']}")
    if delta.get("git_patch"):
        parts.append(f"--- key patch hunks ---\n{delta['git_patch']}")
    if delta.get("env_versions"):
        parts.append(f"--- environment / package versions ---\n{delta['env_versions']}")
    return "\n\n".join(parts)


def build_project_prompt(
    project: str,
    delta: dict,
    suite_logs: dict,
    run_date: str,
    run_id: str,
) -> str:
    persona = PERSONAS.get(project, "You are an expert CI engineer.")
    git_ctx = _git_context(delta)

    logs_block = "\n\n".join(
        f"Suite: {suite}\n{log_text}"
        for suite, log_text in suite_logs.items()
        if log_text and log_text.strip()
    )

    return (
        f"{persona}\n\n"
        f"CI RUN CONTEXT\n"
        f"Failing run: {run_date}  ID {run_id}  "
        f"Log: {CFG['ci']['log_base']}/{run_date.replace('-','')}/\n"
        f"Last passing run: day before {run_date}\n\n"
        f"{git_ctx}\n\n"
        f"=== FAILURE LOGS ===\n{logs_block}\n\n"
        f"TASK — answer precisely and concisely:\n"
        f"1. **Introducing Commit(s)**: Based on the git log and diff above, which specific "
        f"commit(s) introduced the regression? Give commit hash/subject if visible.\n"
        f"2. **Root Cause**: Explain in one paragraph exactly what the change broke and why "
        f"each failing suite fails as a consequence.\n"
        f"3. **Affected Subsystems**: List the kernel/{project}/libvirt subsystems touched.\n"
        f"4. **Why {project} is uniquely affected**: Explain the code path in {project} "
        f"that exercises the changed code.\n"
        f"5. **Recommended Fix**: Exact revert command, workaround, or code change with file path.\n"
        f"6. **Verification command**: Single `git bisect` or targeted test on tuxmaker to confirm.\n\n"
        f"Format with ## headings per section. Reference exact function names, file paths, "
        f"and line numbers where visible from the diff."
    )


def build_correlation_prompt(
    delta: dict,
    kvm_result: str,
    qemu_result: str,
    libvirt_result: str,
    run_date: str,
    run_id: str,
) -> str:
    git_ctx = _git_context(delta)
    return (
        f"You are a Linux virtualisation stack expert covering KVM kernel, QEMU, "
        f"and libvirt on IBM s390x.\n\n"
        f"CI RUN: {run_date} {run_id}\n\n"
        f"{git_ctx}\n\n"
        f"=== PER-PROJECT ANALYSES ===\n\n"
        f"## KVM\n{kvm_result or '(not yet analysed)'}\n\n"
        f"## QEMU\n{qemu_result or '(not yet analysed)'}\n\n"
        f"## libvirt\n{libvirt_result or '(not yet analysed)'}\n\n"
        f"TASK:\n"
        f"1. **Cross-Project Correlation**: Which failures share the same introducing commit?\n"
        f"2. **Dependency chain**: Map the cascade (e.g. kernel change → QEMU break → libvirt break).\n"
        f"3. **Minimum fix set**: Fewest commits to revert/patch to restore all three projects. "
        f"List each: project · file · action (revert/patch/bump).\n"
        f"4. **Triage order**: Which fix unblocks the most suites first?\n"
        f"5. **Reproducer**: Shortest command sequence on tuxmaker to reproduce without full CI.\n\n"
        f"Format with ## headings. Be concise — output will be filed directly into Bugzilla."
    )


# ─────────────────────────────────────────────────────────────────────────────
#  History helpers (stored in Flask session)
# ─────────────────────────────────────────────────────────────────────────────
def _add_history(project: str, status: str, summary: str) -> None:
    if "ciiq_history" not in session:
        session["ciiq_history"] = []
    session["ciiq_history"].insert(
        0,
        {
            "ts": datetime.now().strftime("%H:%M:%S"),
            "project": project,
            "status": status,
            "summary": summary[:200],
        },
    )
    session.modified = True


# ─────────────────────────────────────────────────────────────────────────────
#  Request helpers
# ─────────────────────────────────────────────────────────────────────────────
_PLACEHOLDER_VALUES = {
    "your_ibm_cloud_api_key_here",
    "your_watsonx_project_id_here",
    "placeholder",
    "test-key-placeholder",
    "test-proj-placeholder",
}


def _resolve_api_key(body: dict) -> str:
    """Prefer key from request body, fall back to config/env. Returns '' for placeholder values."""
    val = (
        body.get("api_key")
        or WX_CFG.get("api_key")
        or os.environ.get("CIIQ_WATSONX_API_KEY")
        or ""
    )
    return "" if val in _PLACEHOLDER_VALUES else val


def _resolve_project_id(body: dict) -> str:
    """Prefer project_id from request body, fall back to config/env. Returns '' for placeholders."""
    val = (
        body.get("project_id")
        or WX_CFG.get("project_id")
        or os.environ.get("CIIQ_WATSONX_PROJECT_ID")
        or ""
    )
    return "" if val in _PLACEHOLDER_VALUES else val


def err(msg: str, code: int = 400):
    """Return a standard JSON error response with ok=False."""
    return jsonify({"ok": False, "error": msg}), code


def require_json(f):
    """Decorator: reject requests that are not JSON (Content-Type: application/json)."""
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
    """Return sanitised config — no secrets."""
    wx = CFG.get("watsonx", {})
    ci = CFG.get("ci", {})
    cache_dir = os.path.join(BASE_DIR, ci.get("delta_cache_dir", "delta_cache"))
    latest_run_date = ""
    if os.path.isdir(cache_dir):
        cached = sorted(
            [f for f in os.listdir(cache_dir) if re.match(r"ciiq_delta_\d{8}\.json", f)],
            reverse=True,
        )
        if cached:
            raw = cached[0][len("ciiq_delta_"):-len(".json")]
            latest_run_date = "{}-{}-{}".format(raw[:4], raw[4:6], raw[6:])
    # Env vars override cache-derived values
    env_run_date = os.environ.get("CIIQ_LATEST_RUN_DATE", "").strip()
    env_run_id   = os.environ.get("CIIQ_LATEST_RUN_ID",   "").strip()
    env_region   = os.environ.get("CIIQ_WATSONX_REGION",  "").strip()
    if env_run_date:
        latest_run_date = env_run_date
    return jsonify(
        {
            "ok": True,
            "watsonx": {
                "region":        env_region or wx.get("region"),
                "model":         wx.get("model"),
                "max_tokens":    wx.get("max_tokens"),
                "has_api_key":   bool(wx.get("api_key")),
                "has_project_id":bool(wx.get("project_id")),
            },
            "ci": {
                "log_base":        ci.get("log_base"),
                "webui_base":      ci.get("webui_base"),
                "tuxmaker_host":   ci.get("tuxmaker_host"),
                "latest_run_date": latest_run_date,
                "latest_run_id":   env_run_id,
            },
            "projects": {
                proj: [s["name"] for s in data["suites"]]
                for proj, data in CFG.get("projects", {}).items()
            },
        }
    )


# ─────────────────────────────────────────────────────────────────────────────
#  Routes — IAM token
# ─────────────────────────────────────────────────────────────────────────────
@app.post("/api/token")
@require_json
def api_token():
    body = request.get_json()
    api_key = _resolve_api_key(body)
    if not api_key:
        return err("No API key provided (body.api_key or CIIQ_WATSONX_API_KEY env var)")
    try:
        token = get_iam_token(api_key)
        return jsonify({"ok": True, "token_preview": token[:12] + "…"})
    except Exception as exc:
        log.exception("IAM token error")
        return err(str(exc), 502)


# ─────────────────────────────────────────────────────────────────────────────
#  Routes — Single-project analysis
# ─────────────────────────────────────────────────────────────────────────────
@app.post("/api/analyse/<project>")
@require_json
def api_analyse_project(project: str):
    if project not in ("kvm", "qemu", "libvirt"):
        return err(f"Unknown project '{project}'. Must be kvm, qemu, or libvirt.")

    body = request.get_json()
    api_key    = _resolve_api_key(body)
    project_id = _resolve_project_id(body)

    if not api_key:
        return err("api_key required")
    if not project_id:
        return err("project_id required")

    delta      = body.get("delta", {})
    suite_logs = body.get("suite_logs", {})
    run_date   = body.get("run_date", datetime.today().strftime("%Y-%m-%d"))
    run_id     = body.get("run_id", "#????")
    overrides  = body.get("wx_overrides", {})
    overrides["project_id"] = project_id

    if not suite_logs:
        return err("suite_logs is required (dict of suite_name → log_text)")

    try:
        token  = get_iam_token(api_key)
        prompt = build_project_prompt(project, delta, suite_logs, run_date, run_id)
        result = wx_generate(prompt, token, overrides)

        if "results" not in result or not result["results"]:
            raise ValueError(f"Unexpected WatsonX response: {json.dumps(result)[:300]}")

        r0 = result["results"][0]
        text = r0.get("generated_text", "")

        _add_history(project, "ok", text)
        return jsonify(
            {
                "ok": True,
                "project": project,
                "analysis": text,
                "model": overrides.get("model", WX_CFG.get("model")),
                "input_tokens":     r0.get("input_token_count"),
                "generated_tokens": r0.get("generated_token_count"),
                "run_date": run_date,
                "run_id":   run_id,
            }
        )

    except requests.HTTPError as exc:
        msg = f"HTTP {exc.response.status_code}: {exc.response.text[:400]}"
        _add_history(project, "err", msg)
        log.exception("WatsonX HTTP error for %s", project)
        return err(msg, 502)
    except Exception as exc:
        _add_history(project, "err", str(exc))
        log.exception("Analysis error for %s", project)
        return err(str(exc), 500)


# ─────────────────────────────────────────────────────────────────────────────
#  Routes — Analyse all three projects
# ─────────────────────────────────────────────────────────────────────────────
@app.post("/api/analyse/local")
@require_json
def api_analyse_local():
    """Run the local rule-based analysis engine (no WatsonX API key needed)."""
    _analyse  = _LOCAL_ENGINE.analyse_project
    _correlate = _LOCAL_ENGINE.correlate_projects

    body     = request.get_json()
    delta    = body.get("delta", {})
    raw_logs = body.get("suite_logs", {})
    run_date = body.get("run_date", datetime.today().strftime("%Y-%m-%d"))
    run_id   = body.get("run_id", "#????")

    PROJ_SUITES = {
        proj: [s["name"] for s in CFG.get("projects", {}).get(proj, {}).get("suites", [])]
        for proj in ("kvm", "qemu", "libvirt")
    }
    is_flat = raw_logs and not any(k in raw_logs for k in ("kvm", "qemu", "libvirt"))
    if is_flat:
        all_logs: dict = {"kvm": {}, "qemu": {}, "libvirt": {}}
        for suite_name, suite_log in raw_logs.items():
            for proj, suites in PROJ_SUITES.items():
                if suite_name in suites:
                    all_logs[proj][suite_name] = suite_log
                    break
    else:
        all_logs = raw_logs

    results, errors = {}, {}
    for project in ("kvm", "qemu", "libvirt"):
        suite_logs = all_logs.get(project, {})
        if not suite_logs:
            continue
        try:
            text = _analyse(project, delta, suite_logs, run_date, run_id)
            results[project] = {"analysis": text, "engine": "local"}
            _add_history(project, "ok", text)
        except Exception as exc:
            errors[project] = str(exc)
            log.exception("Local analysis error for %s", project)

    return jsonify({"ok": True, "results": results, "errors": errors,
                    "engine": "local", "run_date": run_date, "run_id": run_id})


@app.post("/api/analyse/all")
@require_json
def api_analyse_all():
    body = request.get_json()
    api_key    = _resolve_api_key(body)
    project_id = _resolve_project_id(body)

    if not api_key:
        return err("api_key required")
    if not project_id:
        return err("project_id required")

    delta      = body.get("delta", {})
    raw_logs   = body.get("suite_logs", {})   # { project: { suite: log } } OR flat { suite: log }
    run_date   = body.get("run_date", datetime.today().strftime("%Y-%m-%d"))
    run_id     = body.get("run_id", "#????")
    overrides  = body.get("wx_overrides", {})
    overrides["project_id"] = project_id

    # Auto-split flat suite_logs into per-project buckets using config suites
    PROJ_SUITES: dict[str, list[str]] = {
        proj: [s["name"] for s in CFG.get("projects", {}).get(proj, {}).get("suites", [])]
        for proj in ("kvm", "qemu", "libvirt")
    }
    # Detect flat format: if keys are suite names (not project names)
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

    results = {}
    errors  = {}
    stagger = WX_CFG.get("call_stagger_ms", 500) / 1000.0

    try:
        token = get_iam_token(api_key)
    except Exception as exc:
        return err(f"IAM token error: {exc}", 502)

    for project in ("kvm", "qemu", "libvirt"):
        suite_logs = all_logs.get(project, {})
        if not suite_logs:
            log.warning("No suite logs provided for %s — skipping", project)
            continue
        try:
            prompt = build_project_prompt(project, delta, suite_logs, run_date, run_id)
            resp   = wx_generate(prompt, token, overrides)
            r0     = resp["results"][0]
            text   = r0.get("generated_text", "")
            results[project] = {
                "analysis":         text,
                "input_tokens":     r0.get("input_token_count"),
                "generated_tokens": r0.get("generated_token_count"),
            }
            _add_history(project, "ok", text)
            log.info("Completed %s — sleeping %.1fs", project, stagger)
            time.sleep(stagger)
        except Exception as exc:
            errors[project] = str(exc)
            _add_history(project, "err", str(exc))
            log.exception("Error analysing %s", project)

    return jsonify(
        {
            "ok": True,
            "results": results,
            "errors":  errors,
            "model":   overrides.get("model", WX_CFG.get("model")),
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
    body = request.get_json()
    api_key    = _resolve_api_key(body)
    project_id = _resolve_project_id(body)

    if not api_key:
        return err("api_key required")
    if not project_id:
        return err("project_id required")

    delta      = body.get("delta", {})
    analyses   = body.get("analyses", {})
    run_date   = body.get("run_date", datetime.today().strftime("%Y-%m-%d"))
    run_id     = body.get("run_id", "#????")
    overrides  = body.get("wx_overrides", {})
    overrides["project_id"] = project_id

    try:
        token  = get_iam_token(api_key)
        prompt = build_correlation_prompt(
            delta,
            analyses.get("kvm", ""),
            analyses.get("qemu", ""),
            analyses.get("libvirt", ""),
            run_date,
            run_id,
        )
        result = wx_generate(prompt, token, overrides)
        r0     = result["results"][0]
        text   = r0.get("generated_text", "")

        _add_history("correlation", "ok", text)
        return jsonify(
            {
                "ok": True,
                "correlation": text,
                "model": overrides.get("model", WX_CFG.get("model")),
                "input_tokens":     r0.get("input_token_count"),
                "generated_tokens": r0.get("generated_token_count"),
            }
        )

    except requests.HTTPError as exc:
        msg = f"HTTP {exc.response.status_code}: {exc.response.text[:400]}"
        _add_history("correlation", "err", msg)
        return err(msg, 502)
    except Exception as exc:
        _add_history("correlation", "err", str(exc))
        log.exception("Correlation error")
        return err(str(exc), 500)


@app.post("/api/correlate/local")
@require_json
def api_correlate_local():
    """Run local (rule-based) cross-project correlation — no WatsonX API key needed."""
    body      = request.get_json()
    delta     = body.get("delta", {})
    analyses  = body.get("analyses", {})
    run_date  = body.get("run_date", datetime.today().strftime("%Y-%m-%d"))
    run_id    = body.get("run_id", "#????")
    try:
        text = _LOCAL_ENGINE.correlate_projects(
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
        log.exception("Local correlation error")
        return err(str(exc), 500)



# SSH helpers

_SSH_RUNS_CACHE      = []      # last successful SSH run list
_SSH_RUNS_CACHE_TS   = 0.0    # epoch time of last fetch
_SSH_RUNS_CACHE_TTL  = 60     # seconds before re-fetching

def _ssh_run(cmd, timeout=30):
    """Run cmd on tuxmaker via SSH."""
    ci = CFG.get("ci", {})
    host = ci.get("tuxmaker_host", "tuxmaker")
    user = ci.get("tuxmaker_user", "")
    target = "{}@{}".format(user, host) if user else host
    argv = ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=5", target, cmd]
    try:
        r = subprocess.run(argv, capture_output=True, text=True, timeout=timeout)
        return r.returncode, r.stdout, r.stderr
    except subprocess.TimeoutExpired:
        return 1, "", "SSH timed out"
    except FileNotFoundError:
        return 1, "", "ssh not found"


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
    rc, out, _ = _ssh_run(
        "ls -1 {} 2>/dev/null | grep -E '^[0-9]{{8}}$' | sort -r | head -30".format(log_base)
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
    """List run dates from local log_base if mounted, else via SSH."""
    log_base = CFG["ci"]["log_base"]
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
    log.info("log_base not local -- listing runs via SSH")
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
                                        l.rstrip()
                                        for l in f
                                        if re.search(
                                            r"(FAIL|FAILED|BUG|Oops|panic|assert|ERROR|"
                                            r"error:|No such|Invalid argument|unexpected|"
                                            r"timeout|abort)",
                                            l,
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


@app.get("/api/delta/<date>")
def api_delta(date):
    """Fetch git delta for a run date from tuxmaker via SSH. Caches locally."""
    date_raw = date.replace("-", "")
    if not re.match(r"^\d{8}$", date_raw):
        return err("Invalid date -- use YYYYMMDD or YYYY-MM-DD")
    ci = CFG.get("ci", {})
    cache_dir = os.path.join(BASE_DIR, ci.get("delta_cache_dir", "delta_cache"))
    os.makedirs(cache_dir, exist_ok=True)
    cache_file = os.path.join(cache_dir, "ciiq_delta_{}.json".format(date_raw))
    if os.path.isfile(cache_file):
        try:
            with open(cache_file) as fh:
                data = json.load(fh)
            return jsonify({"ok": True, "delta": data, "source": "cache"})
        except (OSError, json.JSONDecodeError):
            pass
    log_base = ci.get("log_base", "/home/ciuser/logs/daily")
    kernel_repo = ci.get("kernel_repo", "/home/ciuser/linux")
    yesterday = (datetime.strptime(date_raw, "%Y%m%d") - timedelta(days=1)).strftime("%Y%m%d")
    sha_cmd = (
        "SB=$(cat {lb}/{today}/kernel.sha 2>/dev/null | tr -d '[:space:]' || echo HEAD); "
        "SG=$(cat {lb}/{yest}/kernel.sha  2>/dev/null | tr -d '[:space:]' || echo HEAD~10); "
        "printf '%s %s' $SB $SG"
    ).format(lb=log_base, today=date_raw, yest=yesterday)
    rc, sha_out, sha_err = _ssh_run(sha_cmd, timeout=15)
    if rc != 0:
        return jsonify({"ok": False, "error": "SSH failed: {}".format(sha_err[:200]), "delta": {}})
    parts = sha_out.strip().split()
    sha_bad  = parts[0] if parts else "HEAD"
    sha_good = parts[1] if len(parts) > 1 else "HEAD~10"
    def git_ssh(args):
        _, out, _ = _ssh_run("cd {} && {}".format(kernel_repo, args), timeout=30)
        return out
    data = {
        "run_date": date_raw,
        "sha_good": sha_good,
        "sha_bad":  sha_bad,
        "git_log": git_ssh("git log --oneline {}..{} -- arch/s390/kvm/ include/uapi/linux/kvm.h "
            "drivers/s390/ arch/s390/boot/ tools/testing/selftests/kvm/ 2>/dev/null | head -40 || true".format(sha_good, sha_bad)),
        "git_diff_stat": git_ssh("git diff --stat {}..{} 2>/dev/null | tail -60 || true".format(sha_good, sha_bad)),
        "git_patch": git_ssh("git diff {}..{} -- arch/s390/kvm/ include/uapi/linux/kvm.h 2>/dev/null | head -200 || true".format(sha_good, sha_bad)),
    }
    try:
        with open(cache_file, "w") as fh:
            json.dump(data, fh, indent=2)
    except OSError:
        pass
    return jsonify({"ok": True, "delta": data, "source": "ssh"})


# ─────────────────────────────────────────────────────────────────────────────
#  Routes — CI mail ingest (delegates to local engine parser)
# ─────────────────────────────────────────────────────────────────────────────
@app.post("/api/ingest")
@require_json
def api_ingest():
    """Parse a raw CI mail report — delegates to the local engine's _parse_ci_mail."""
    body = request.get_json()
    text = body.get("mail_text", "")
    if not text or not text.strip():
        return jsonify({"ok": False, "error": "mail_text is required"}), 400
    try:
        parsed = _LOCAL_ENGINE._parse_ci_mail(text)
        log.info(
            "Ingest: run=%s id=%s suites=%d dumps=%d",
            parsed["run_date"], parsed["run_id"],
            len(parsed["suite_logs"]), len(parsed["dumps"]),
        )
        return jsonify({"ok": True, **parsed})
    except Exception as exc:
        log.exception("Ingest parse error")
        return jsonify({"ok": False, "error": str(exc)}), 500


# ─────────────────────────────────────────────────────────────────────────────
#  Routes — HTML report (delegates to local engine renderer)
# ─────────────────────────────────────────────────────────────────────────────
@app.post("/api/report")
@require_json
def api_report():
    """Generate a self-contained HTML root-cause report — delegates to local engine."""
    from flask import Response
    body      = request.get_json()
    render    = _LOCAL_ENGINE._render_html_report
    parse     = _LOCAL_ENGINE._parse_ci_mail
    scan      = _LOCAL_ENGINE._scan_log
    run_date  = body.get("run_date",     datetime.today().strftime("%Y-%m-%d"))
    run_id    = body.get("run_id",       "????")
    delta_    = body.get("delta",        {})
    mail_text = body.get("mail_text",    "")
    raw_logs  = body.get("suite_logs",   {})
    ui_status = body.get("suite_status", {})  # UI badges — authoritative
    try:
        if mail_text and mail_text.strip():
            parsed = parse(mail_text)
            if parsed["run_date"]: run_date = parsed["run_date"]
            if parsed["run_id"]:   run_id   = parsed["run_id"]
        else:
            parsed = {"run_date": run_date, "run_id": run_id, "web_url": "", "log_path": "",
                      "kernel_key": {}, "suite_logs": {}, "suite_status": {}, "dumps": []}
        flat: dict = {}
        if isinstance(raw_logs, dict):
            for k, v in raw_logs.items():
                if k in ("kvm", "qemu", "libvirt") and isinstance(v, dict): flat.update(v)
                else: flat[k] = v
        for suite, text in flat.items():
            if text and text.strip():
                if suite not in parsed["suite_logs"]: parsed["suite_logs"][suite] = text
                if suite not in parsed["suite_status"]:
                    parsed["suite_status"][suite] = "FAIL" if scan(text)["hits"] else "PASS"
        # UI badge values always win — they are the ground truth
        if ui_status:
            parsed["suite_status"].update(ui_status)
        ci = CFG.get("ci", {})
        wb = ci.get("webui_base", "https://lnxgwne1.boeblingen.de.ibm.com/linux-ci/webui/ci-run")
        html = render(parsed=parsed, delta=delta_, suite_logs=flat,
                      run_date=run_date, run_id=run_id, webui_base=wb)
        fname = "ciiq-run-{}-root-cause-report.html".format(run_id)
        return Response(html, mimetype="text/html",
                        headers={"Content-Disposition": 'attachment; filename="{}"'.format(fname)})
    except Exception as exc:
        log.exception("Report render error")
        return jsonify({"ok": False, "error": str(exc)}), 500


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
