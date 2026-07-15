"""
PatchIQ — Diff parser and watsonx AI review engine.

Flow:
  raw diff text
      → parse_diff()       split into per-file hunks
      → detect_layer()     kernel | qemu | libvirt
      → run_rules()        deterministic style checks
      → ai_review()        watsonx LLM narrative review
      → ReviewResult       collected findings + AI summary
"""

import re
import os
import json
import requests
from dataclasses import dataclass, field
from typing import List, Dict, Optional

from patchiq.rules import run_rules

# ---------------------------------------------------------------------------
# watsonx configuration  — set env vars or edit defaults below
# ---------------------------------------------------------------------------
WX_API_KEY   = os.getenv("WATSONX_API_KEY", "")
WX_PROJECT   = os.getenv("WATSONX_PROJECT_ID", "")
WX_URL       = os.getenv("WATSONX_URL", "https://us-south.ml.cloud.ibm.com")
WX_MODEL     = os.getenv("WATSONX_MODEL", "ibm/granite-13b-chat-v2")

IAM_TOKEN_URL = "https://iam.cloud.ibm.com/identity/token"

_iam_token_cache: Dict[str, str] = {}


def _get_iam_token() -> str:
    if _iam_token_cache.get("token"):
        return _iam_token_cache["token"]
    if not WX_API_KEY:
        return ""
    resp = requests.post(IAM_TOKEN_URL, data={
        "grant_type": "urn:ibm:params:oauth:grant-type:apikey",
        "apikey": WX_API_KEY,
    })
    resp.raise_for_status()
    token = resp.json()["access_token"]
    _iam_token_cache["token"] = token
    return token


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class FileDiff:
    path: str
    layer: str          # kernel | qemu | libvirt | unknown
    lines: List[str]    # raw unified diff lines for this file


@dataclass
class Finding:
    rule_id: str
    severity: str       # error | warning | info
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
    score: int          # 0-100  (100 = clean patch)


# ---------------------------------------------------------------------------
# Layer detection
# ---------------------------------------------------------------------------

_LAYER_PATTERNS = {
    "kernel": re.compile(
        r'(arch/s390|arch/x86|drivers/vfio|drivers/virtio|virt/kvm|'
        r'include/linux|include/kvm|net/|block/|fs/)',
        re.IGNORECASE
    ),
    "qemu": re.compile(
        r'(hw/virtio|hw/s390x|hw/vfio|hw/block|hw/net|'
        r'target/s390x|migration/|monitor/|softmmu/)',
        re.IGNORECASE
    ),
    "libvirt": re.compile(
        r'(src/qemu|src/conf|src/util|src/libvirt|'
        r'src/driver|tests/qemu)',
        re.IGNORECASE
    ),
}


def detect_layer(path: str) -> str:
    for layer, pattern in _LAYER_PATTERNS.items():
        if pattern.search(path):
            return layer
    # Fallback: extension heuristics
    if path.endswith(('.c', '.h')):
        return "kernel"    # default C to kernel
    return "unknown"


# ---------------------------------------------------------------------------
# Diff parser
# ---------------------------------------------------------------------------

def parse_diff(raw: str) -> tuple[str, List[FileDiff]]:
    """
    Parse a unified diff.  Returns (subject, [FileDiff]).
    Subject is extracted from the 'Subject:' header if present (email patch),
    otherwise derived from the first changed file.
    """
    subject = ""
    files: List[FileDiff] = []
    current_path = None
    current_lines: List[str] = []

    for line in raw.splitlines():
        # Email patch subject header
        if line.startswith("Subject:"):
            subject = re.sub(r'^\[PATCH[^\]]*\]\s*', '', line[8:].strip())
            continue

        # New file header
        m = re.match(r'^diff --git a/(.+?) b/', line)
        if m:
            if current_path is not None:
                layer = detect_layer(current_path)
                files.append(FileDiff(current_path, layer, current_lines))
            current_path = m.group(1)
            current_lines = [line]
            continue

        if current_path is not None:
            current_lines.append(line)

    # Flush last file
    if current_path is not None:
        layer = detect_layer(current_path)
        files.append(FileDiff(current_path, layer, current_lines))

    if not subject and files:
        subject = f"Changes to {files[0].path}"

    return subject, files


# ---------------------------------------------------------------------------
# watsonx AI review
# ---------------------------------------------------------------------------

_SYSTEM_PROMPT = """\
You are PatchIQ, an expert code reviewer for the KVM and Linux open source stack.
Your audience is experienced kernel, QEMU, and libvirt developers.
Be concise, technical, and constructive. Focus on correctness, safety, and upstream acceptance.
Format your response as JSON with keys: "summary" (string) and "suggestions" (list of strings).
"""


def _build_prompt(subject: str, file_diffs: List[FileDiff]) -> str:
    sections = []
    for fd in file_diffs[:6]:          # cap to 6 files to stay within context
        diff_snippet = '\n'.join(fd.lines[:120])   # cap lines per file
        sections.append(f"### {fd.path} ({fd.layer})\n```diff\n{diff_snippet}\n```")

    return (
        f"Review this patch titled: \"{subject}\"\n\n"
        + "\n\n".join(sections)
        + "\n\nProvide a JSON response with 'summary' and 'suggestions'."
    )


def ai_review(subject: str, files: List[FileDiff]) -> tuple[str, List[str]]:
    """
    Call watsonx to generate a narrative review.
    Returns (summary_string, [suggestion, ...]).
    Falls back gracefully if API key is not configured.
    """
    if not WX_API_KEY or not WX_PROJECT:
        return (
            "AI review skipped — set WATSONX_API_KEY and WATSONX_PROJECT_ID to enable.",
            []
        )

    try:
        token = _get_iam_token()
        prompt = _build_prompt(subject, files)

        payload = {
            "model_id": WX_MODEL,
            "project_id": WX_PROJECT,
            "input": f"<|system|>\n{_SYSTEM_PROMPT}\n<|user|>\n{prompt}\n<|assistant|>\n",
            "parameters": {
                "decoding_method": "greedy",
                "max_new_tokens": 800,
                "stop_sequences": ["<|user|>"],
            },
        }

        resp = requests.post(
            f"{WX_URL}/ml/v1/text/generation?version=2023-05-29",
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=30,
        )
        resp.raise_for_status()
        generated = resp.json()["results"][0]["generated_text"].strip()

        # Parse JSON from the response
        json_match = re.search(r'\{.*\}', generated, re.DOTALL)
        if json_match:
            parsed = json.loads(json_match.group())
            return parsed.get("summary", ""), parsed.get("suggestions", [])

        return generated, []

    except Exception as exc:
        return f"AI review unavailable: {exc}", []


# ---------------------------------------------------------------------------
# Scoring
# ---------------------------------------------------------------------------

def _score(findings: List[Finding]) -> int:
    deductions = {"error": 20, "warning": 8, "info": 2}
    total = sum(deductions.get(f.severity, 0) for f in findings)
    return max(0, 100 - total)


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def review_patch(raw_diff: str) -> ReviewResult:
    """Full pipeline: parse → style rules → AI review → score."""
    subject, files = parse_diff(raw_diff)

    all_findings: List[Finding] = []
    for fd in files:
        if fd.layer != "unknown":
            raw_findings = run_rules(fd.lines, fd.layer)
            for rf in raw_findings:
                all_findings.append(Finding(
                    rule_id=rf["rule_id"],
                    severity=rf["severity"],
                    layer=rf["layer"],
                    message=rf["message"],
                    line=rf.get("line"),
                ))

    ai_summary, ai_suggestions = ai_review(subject, files)
    score = _score(all_findings)

    return ReviewResult(
        patch_subject=subject,
        files=files,
        findings=all_findings,
        ai_summary=ai_summary,
        ai_suggestions=ai_suggestions,
        score=score,
    )
