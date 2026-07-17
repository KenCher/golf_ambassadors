"""
PatchIQ — Orchestrate / Agentic edition
Uses IBM watsonx tool-calling (llama-3-3-70b-instruct via chat/completions) to run a
multi-turn ReAct loop:

  Turn 1 — Model receives the diff and tool definitions, calls scan_diff()
  Turn 2 — scan_diff() result fed back, model calls check_rules()
  Turn 3 — rule findings fed back, model calls summarise_findings()
  Turn 4 — final summary returned as ReviewResult.ai_summary / ai_suggestions

This is the "Orchestrate pattern": the model PLANS which tool to call and
ACTS on the result before producing its final answer — rather than just
completing a single prompt.

Differences from analyzer-wx.py:
  - Uses /ml/v1/text/chat  (OpenAI-compatible chat/completions) instead of
    /ml/v1/text/generation
  - Uses tool_choice='auto' — the model decides which tool to call
  - Model: meta-llama/llama-3-3-70b-instruct  (supports tool calling)
  - Multi-turn: up to 6 turns before fallback
  - All tool implementations are local Python functions — no extra infra needed

For watsonx Orchestrate SaaS:
  Replace the IAM+REST calls below with your WXO zone_token and
  POST to https://dl.watson-orchestrate.ibm.com/api/v1/chat/completions
  The tool definitions below become "external skills" registered in WXO.
"""

import re
import os
import json
import requests
from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple

from patchiq.rules import run_rules

# ── Credentials ──────────────────────────────────────────────────────────────
WX_API_KEY  = os.getenv("WATSONX_API_KEY",  "")
WX_PROJECT  = os.getenv("WATSONX_PROJECT_ID","")
WX_URL      = os.getenv("WATSONX_URL",  "https://us-south.ml.cloud.ibm.com")
# Llama-3-3-70B is the model that supports OpenAI-compatible tool calling on watsonx
AGENT_MODEL = os.getenv("WATSONX_AGENT_MODEL", "meta-llama/llama-3-3-70b-instruct")

IAM_URL = "https://iam.cloud.ibm.com/identity/token"
_token_cache: Dict[str, object] = {}


def _iam_token() -> str:
    import time
    now = time.time()
    if _token_cache.get("t") and now < _token_cache.get("exp", 0):
        return _token_cache["t"]
    if not WX_API_KEY:
        return ""
    r = requests.post(IAM_URL,
        data={"grant_type": "urn:ibm:params:oauth:grant-type:apikey",
              "apikey": WX_API_KEY}, timeout=15)
    r.raise_for_status()
    d = r.json()
    _token_cache["t"]   = d["access_token"]
    _token_cache["exp"] = now + d.get("expires_in", 3600) - 60
    return _token_cache["t"]


# ── Data structures (identical to analyzer-wx.py) ────────────────────────────
@dataclass
class FileDiff:
    path: str
    layer: str
    lines: List[str]


@dataclass
class Finding:
    rule_id: str
    severity: str
    layer: str
    message: str
    line: Optional[str] = None


@dataclass
class ReviewResult:
    patch_subject: str
    files: List[FileDiff]
    findings: List[Finding]
    ai_summary: str
    ai_suggestions: List[str]
    score: int


# ── Layer detection ───────────────────────────────────────────────────────────
_LAYER_PATTERNS = {
    "kernel": re.compile(
        r'(arch/s390|arch/x86|drivers/vfio|drivers/virtio|virt/kvm|'
        r'include/linux|include/kvm|net/|block/|fs/)', re.IGNORECASE),
    "qemu": re.compile(
        r'(hw/virtio|hw/s390x|hw/vfio|hw/block|hw/net|'
        r'target/s390x|migration/|monitor/|softmmu/)', re.IGNORECASE),
    "libvirt": re.compile(
        r'(src/qemu|src/conf|src/util|src/libvirt|src/driver|tests/qemu)',
        re.IGNORECASE),
}


def detect_layer(path: str) -> str:
    for layer, pat in _LAYER_PATTERNS.items():
        if pat.search(path):
            return layer
    return "kernel" if path.endswith(('.c', '.h')) else "unknown"


# ── Diff parser ───────────────────────────────────────────────────────────────
def parse_diff(raw: str) -> Tuple[str, List[FileDiff]]:
    subject = ""
    files: List[FileDiff] = []
    cur_path: Optional[str] = None
    cur_lines: List[str] = []

    for line in raw.splitlines():
        if line.startswith("Subject:"):
            subject = re.sub(r'^\[PATCH[^\]]*\]\s*', '', line[8:].strip())
            continue
        m = re.match(r'^diff --git a/(.+?) b/', line)
        if m:
            if cur_path:
                files.append(FileDiff(cur_path, detect_layer(cur_path), cur_lines))
            cur_path, cur_lines = m.group(1), [line]
            continue
        if cur_path:
            cur_lines.append(line)

    if cur_path:
        files.append(FileDiff(cur_path, detect_layer(cur_path), cur_lines))
    if not subject and files:
        subject = f"Changes to {files[0].path}"
    return subject, files


# ── Tool implementations (the "skills") ──────────────────────────────────────

def _tool_scan_diff(diff_snippet: str, layer: str) -> dict:
    """
    Tool: scan_diff
    Parse a unified diff snippet and return structural metadata.
    This is what the model calls first to understand the patch shape.
    """
    lines   = diff_snippet.splitlines()
    added   = [l[1:] for l in lines if l.startswith('+') and not l.startswith('+++')]
    removed = [l[1:] for l in lines if l.startswith('-') and not l.startswith('---')]

    # Simple pattern counts
    import re as _re
    counts = {
        "added_lines":   len(added),
        "removed_lines": len(removed),
        "has_locking":   bool(_re.search(r'\b(mutex|spin_lock|rcu_read_lock|down_read)\b',
                                         '\n'.join(added))),
        "has_alloc":     bool(_re.search(r'\b(kmalloc|kzalloc|vmalloc|g_new|g_malloc)\b',
                                         '\n'.join(added))),
        "has_user_copy": bool(_re.search(r'\b(copy_from_user|copy_to_user|get_user|put_user)\b',
                                         '\n'.join(added))),
        "has_ioctl":     bool(_re.search(r'\b(KVM_[A-Z_]+|VFIO_[A-Z_]+|ioctl)\b',
                                         '\n'.join(added))),
        "has_tests":     bool(_re.search(r'\b(kselftest|kunit|g_assert|assert_true)\b',
                                         '\n'.join(added))),
        "layer":         layer,
    }
    sample_added = added[:6]  # first 6 added lines as context
    return {"metadata": counts, "sample_added_lines": sample_added}


def _tool_check_rules(diff_lines_json: str, layer: str) -> dict:
    """
    Tool: check_rules
    Run the deterministic PatchIQ rule engine on the diff and return all findings.
    """
    diff_lines = json.loads(diff_lines_json)
    raw = run_rules(diff_lines, layer)
    return {
        "findings":       raw,
        "finding_count":  len(raw),
        "errors":         sum(1 for f in raw if f["severity"] == "error"),
        "warnings":       sum(1 for f in raw if f["severity"] == "warning"),
        "info":           sum(1 for f in raw if f["severity"] == "info"),
        "score_estimate": max(0, 100 - sum(
            {"error": 20, "warning": 8, "info": 2}.get(f["severity"], 0) for f in raw
        )),
    }


def _tool_summarise_findings(
    subject: str,
    scan_result_json: str,
    rules_result_json: str
) -> dict:
    """
    Tool: summarise_findings
    Combine the scan metadata and rule findings into a final summary dict.
    The model calls this last to produce structured output.
    """
    scan  = json.loads(scan_result_json)
    rules = json.loads(rules_result_json)
    meta  = scan.get("metadata", {})

    suggestions = []
    if meta.get("has_alloc") and rules.get("errors", 0) == 0 and rules.get("warnings", 0) == 0:
        suggestions.append(
            "Memory allocation detected. Verify all kmalloc/kzalloc results are NULL-checked "
            "and freed on every error path."
        )
    if meta.get("has_locking") and meta.get("has_user_copy"):
        suggestions.append(
            "Lock acquisition and user-space copy coexist. Confirm the lock is held across "
            "copy_from_user/copy_to_user to prevent TOCTOU races."
        )
    if meta.get("has_ioctl") and not meta.get("has_locking"):
        suggestions.append(
            "KVM/VFIO ioctl pattern found without visible lock acquisition. Ensure "
            "kvm->lock or vcpu->mutex covers all state mutations."
        )
    if meta.get("added_lines", 0) > 150 and not meta.get("has_tests"):
        suggestions.append(
            f"Large patch (+{meta.get('added_lines')} lines) with no test additions. "
            "Consider adding a KVM selftest or kunit test."
        )
    for f in rules.get("findings", [])[:3]:
        suggestions.append(f"[{f['rule_id']}] {f['message']}")

    layer = meta.get("layer", "unknown")
    size  = ("small" if meta.get("added_lines", 0) < 30
             else "medium" if meta.get("added_lines", 0) < 150 else "large")
    focus = ", ".join(k for k, v in {
        "locking": meta.get("has_locking"),
        "memory allocation": meta.get("has_alloc"),
        "user-kernel boundary": meta.get("has_user_copy"),
        "KVM/VFIO ioctl": meta.get("has_ioctl"),
    }.items() if v) or "general logic"

    summary = (
        f"Agentic review of '{subject}': {size} {layer} patch "
        f"(+{meta.get('added_lines',0)}/-{meta.get('removed_lines',0)} lines). "
        f"Focus areas: {focus}. "
        f"Rule engine: {rules.get('errors',0)} errors, {rules.get('warnings',0)} warnings, "
        f"{rules.get('info',0)} info. Score: {rules.get('score_estimate',100)}/100."
    )

    return {"summary": summary, "suggestions": suggestions[:6]}


# ── Tool registry ─────────────────────────────────────────────────────────────
_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "scan_diff",
            "description": (
                "Parse a unified diff snippet and return structural metadata: "
                "line counts, whether locking/allocation/user-copy/ioctl patterns appear, "
                "and the detected layer (kernel/qemu/libvirt)."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "diff_snippet": {"type": "string",
                                     "description": "Raw unified diff lines for one file"},
                    "layer":        {"type": "string",
                                     "enum": ["kernel", "qemu", "libvirt", "unknown"],
                                     "description": "Detected code layer"},
                },
                "required": ["diff_snippet", "layer"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "check_rules",
            "description": (
                "Run the PatchIQ deterministic style-rule engine on the diff lines "
                "and return all findings with rule_id, severity, and message."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "diff_lines_json": {"type": "string",
                                        "description": "JSON array of raw diff line strings"},
                    "layer":           {"type": "string",
                                        "enum": ["kernel", "qemu", "libvirt"],
                                        "description": "Code layer to select rules"},
                },
                "required": ["diff_lines_json", "layer"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "summarise_findings",
            "description": (
                "Combine scan metadata and rule findings into a final structured summary "
                "with a narrative description and a list of actionable suggestions."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "subject":            {"type": "string",
                                           "description": "Patch subject/title"},
                    "scan_result_json":   {"type": "string",
                                           "description": "JSON result from scan_diff"},
                    "rules_result_json":  {"type": "string",
                                           "description": "JSON result from check_rules"},
                },
                "required": ["subject", "scan_result_json", "rules_result_json"],
            },
        },
    },
]

_TOOL_FNS = {
    "scan_diff":          lambda a: _tool_scan_diff(a["diff_snippet"], a["layer"]),
    "check_rules":        lambda a: _tool_check_rules(a["diff_lines_json"], a["layer"]),
    "summarise_findings": lambda a: _tool_summarise_findings(
                                        a["subject"], a["scan_result_json"],
                                        a["rules_result_json"]),
}


# ── Chat / ReAct loop ─────────────────────────────────────────────────────────
def _chat(messages: list, max_turns: int = 8) -> dict:
    """
    Run a multi-turn tool-calling loop:
    1. Send messages + tool definitions to the model
    2. If model returns tool_calls, execute the tool and append result
    3. Repeat until model produces a text response (no tool_calls) or max_turns hit
    Returns the final assistant message dict.
    """
    token = _iam_token()
    url   = f"{WX_URL}/ml/v1/text/chat?version=2024-05-01"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type":  "application/json",
    }

    for turn in range(max_turns):
        resp = requests.post(url, headers=headers, json={
            "model_id":   AGENT_MODEL,
            "project_id": WX_PROJECT,
            "messages":   messages,
            "tools":      _TOOLS,
            "tool_choice": "auto",
            "parameters": {"max_new_tokens": 800},
        }, timeout=60)
        resp.raise_for_status()
        msg = resp.json()["choices"][0]["message"]
        messages.append(msg)

        if not msg.get("tool_calls"):
            # Model produced a final text response
            return msg

        # Execute all tool calls and add results to the conversation
        for tc in msg["tool_calls"]:
            fn_name = tc["function"]["name"]
            fn_args = json.loads(tc["function"]["arguments"])
            fn      = _TOOL_FNS.get(fn_name)
            if fn:
                result = fn(fn_args)
            else:
                result = {"error": f"Unknown tool: {fn_name}"}

            messages.append({
                "role":         "tool",
                "tool_call_id": tc["id"],
                "content":      json.dumps(result),
            })

    # Fallback if max_turns exhausted
    return {"role": "assistant", "content": "Max turns reached without final answer."}


# ── Agentic AI review ─────────────────────────────────────────────────────────
_SYSTEM = (
    "You are PatchIQ Agent, an expert code reviewer for the KVM and Linux open source stack. "
    "You have three tools: scan_diff, check_rules, and summarise_findings. "
    "Follow this exact sequence — call each tool EXACTLY ONCE:\n"
    "Step 1: Call scan_diff with the diff snippet and layer.\n"
    "Step 2: Call check_rules with the diff lines as a JSON array and the layer.\n"
    "Step 3: Call summarise_findings ONCE with the subject and the JSON results from steps 1 and 2.\n"
    "Step 4: After summarise_findings returns, write its summary field as your final reply. "
    "Do NOT call summarise_findings or any other tool a second time."
)


def ai_review(subject: str, files: List[FileDiff]) -> Tuple[str, List[str]]:
    """
    Agentic AI review using watsonx tool calling.
    Runs a ReAct loop: scan_diff → check_rules → summarise_findings → final answer.
    Falls back gracefully if credentials are not set.
    """
    if not WX_API_KEY or not WX_PROJECT:
        return (
            "Agentic review skipped — set WATSONX_API_KEY and WATSONX_PROJECT_ID to enable.",
            [],
        )

    # Pick the first non-unknown file for the agentic loop
    target = next((f for f in files if f.layer != "unknown"), files[0] if files else None)
    if not target:
        return "No reviewable files in patch.", []

    diff_snippet  = "\n".join(target.lines[:100])
    diff_lines_j  = json.dumps(target.lines[:100])

    user_msg = (
        f"Review this patch titled: \"{subject}\"\n\n"
        f"File: {target.path} (layer: {target.layer})\n\n"
        f"Please call scan_diff, then check_rules, then summarise_findings "
        f"to produce a structured review."
    )

    messages = [
        {"role": "system",  "content": _SYSTEM},
        {"role": "user",    "content": user_msg},
    ]

    try:
        final_msg = _chat(messages)
        content   = final_msg.get("content", "")

        # Try to parse JSON from the response
        jm = re.search(r'\{.*\}', content, re.DOTALL)
        if jm:
            try:
                parsed = json.loads(jm.group())
                return parsed.get("summary", content), parsed.get("suggestions", [])
            except json.JSONDecodeError:
                pass

        # Extract summary from summarise_findings tool results in conversation
        for msg in reversed(messages):
            if msg.get("role") == "tool":
                try:
                    result = json.loads(msg["content"])
                    if "summary" in result and "suggestions" in result:
                        return result["summary"], result["suggestions"]
                except Exception:
                    pass

        return content or "Agentic review completed — see style findings.", []

    except Exception as exc:
        return f"Agentic review unavailable: {exc}", []


# ── Scoring ───────────────────────────────────────────────────────────────────
def _score(findings: List[Finding]) -> int:
    deductions = {"error": 20, "warning": 8, "info": 2}
    return max(0, 100 - sum(deductions.get(f.severity, 0) for f in findings))


# ── Public entry point ────────────────────────────────────────────────────────
def review_patch(raw_diff: str) -> ReviewResult:
    """Full pipeline: parse → style rules → agentic AI review → score."""
    subject, files = parse_diff(raw_diff)

    all_findings: List[Finding] = []
    for fd in files:
        if fd.layer != "unknown":
            for rf in run_rules(fd.lines, fd.layer):
                all_findings.append(Finding(
                    rule_id=rf["rule_id"], severity=rf["severity"],
                    layer=rf["layer"],    message=rf["message"],
                    line=rf.get("line"),
                ))

    ai_summary, ai_suggestions = ai_review(subject, files)
    return ReviewResult(
        patch_subject=subject, files=files, findings=all_findings,
        ai_summary=ai_summary, ai_suggestions=ai_suggestions,
        score=_score(all_findings),
    )
