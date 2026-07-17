"""
PatchIQ — Diff parser and local rule-based review engine.

Flow:
  raw diff text
      → parse_diff()       split into per-file hunks
      → detect_layer()     kernel | qemu | libvirt
      → run_rules()        deterministic style checks
      → local_review()     heuristic narrative (no external API needed)
      → ReviewResult       collected findings + summary
"""

import re
from dataclasses import dataclass
from typing import List, Optional, Tuple

from patchiq.rules import run_rules

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
    if path.endswith(('.c', '.h')):
        return "kernel"    # default C to kernel
    return "unknown"


# ---------------------------------------------------------------------------
# Diff parser
# ---------------------------------------------------------------------------

def parse_diff(raw: str) -> Tuple[str, List[FileDiff]]:
    """
    Parse a unified diff.  Returns (subject, [FileDiff]).
    Subject is extracted from the 'Subject:' header if present (email patch),
    otherwise derived from the first changed file.
    """
    subject = ""
    files: List[FileDiff] = []
    current_path: Optional[str] = None
    current_lines: List[str] = []

    for line in raw.splitlines():
        if line.startswith("Subject:"):
            subject = re.sub(r'^\[PATCH[^\]]*\]\s*', '', line[8:].strip())
            continue

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

    if current_path is not None:
        layer = detect_layer(current_path)
        files.append(FileDiff(current_path, layer, current_lines))

    if not subject and files:
        subject = f"Changes to {files[0].path}"

    return subject, files


# ---------------------------------------------------------------------------
# Local narrative engine  (no external API)
# ---------------------------------------------------------------------------

# Patterns that indicate interesting code patterns in added lines
_SECURITY_RE  = re.compile(r'\b(copy_from_user|copy_to_user|__user|kmalloc|kzalloc|'
                            r'kfree|mutex_lock|spin_lock|rcu_read_lock)\b')
_LOCKING_RE   = re.compile(r'\b(mutex|spinlock|rwlock|semaphore|rcu)\b', re.IGNORECASE)
_MEMORY_RE    = re.compile(r'\b(kmalloc|kzalloc|vzalloc|vmalloc|kfree|vfree)\b')
_ERROR_RE     = re.compile(r'\b(ENOMEM|EINVAL|EFAULT|EBUSY|goto\s+\w+err|'
                            r'return\s+-E[A-Z]+)\b')
_IOCTL_RE     = re.compile(r'\b(ioctl|KVM_[A-Z_]+|VFIO_[A-Z_]+)\b')
_TEST_RE      = re.compile(r'\b(assert|ASSERT|kselftest|kunit_test|g_assert)\b')


def _added_lines(file_diffs: List[FileDiff]) -> List[str]:
    lines = []
    for fd in file_diffs:
        for line in fd.lines:
            if line.startswith('+') and not line.startswith('+++'):
                lines.append(line[1:])
    return lines


def _stats(file_diffs: List[FileDiff]) -> dict:
    added = removed = 0
    for fd in file_diffs:
        for line in fd.lines:
            if line.startswith('+') and not line.startswith('+++'):
                added += 1
            elif line.startswith('-') and not line.startswith('---'):
                removed += 1
    return {"added": added, "removed": removed}


def local_review(subject: str, files: List[FileDiff]) -> Tuple[str, List[str]]:
    """
    Generate a heuristic narrative summary and actionable suggestions without
    calling any external API.  Based purely on diff content analysis.
    """
    if not files:
        return "Empty diff — nothing to review.", []

    layers = sorted({f.layer for f in files if f.layer != "unknown"})
    stats  = _stats(files)
    added  = _added_lines(files)

    # Counts of interesting patterns in added lines
    security_hits = sum(1 for l in added if _SECURITY_RE.search(l))
    locking_hits  = sum(1 for l in added if _LOCKING_RE.search(l))
    memory_hits   = sum(1 for l in added if _MEMORY_RE.search(l))
    error_hits    = sum(1 for l in added if _ERROR_RE.search(l))
    ioctl_hits    = sum(1 for l in added if _IOCTL_RE.search(l))
    test_hits     = sum(1 for l in added if _TEST_RE.search(l))

    # --- Summary ---
    layer_str  = "/".join(layers) if layers else "general"
    size_desc  = (
        "small" if stats["added"] < 30 else
        "medium" if stats["added"] < 150 else
        "large"
    )
    churn_desc = (
        f"+{stats['added']}/-{stats['removed']} lines across "
        f"{len(files)} file{'s' if len(files) != 1 else ''}"
    )

    focus_parts = []
    if locking_hits:
        focus_parts.append("locking/synchronisation")
    if memory_hits:
        focus_parts.append("memory allocation/free")
    if security_hits:
        focus_parts.append("user-kernel boundary")
    if ioctl_hits:
        focus_parts.append("KVM/VFIO ioctl interface")
    if error_hits:
        focus_parts.append("error handling")

    focus_str = (
        "Touches: " + ", ".join(focus_parts) + "."
        if focus_parts else "General code change."
    )

    summary = (
        f"This is a {size_desc} {layer_str} patch ({churn_desc}). "
        f"{focus_str}"
    )
    if test_hits:
        summary += " Includes test coverage — good practice."

    # --- Suggestions ---
    suggestions: List[str] = []

    if memory_hits and not error_hits:
        suggestions.append(
            "Memory allocation detected but no error-path return found in added lines. "
            "Verify all kmalloc/kzalloc results are checked and freed on every error path."
        )

    if locking_hits and security_hits:
        suggestions.append(
            "Locking and user-kernel copy operations coexist. Confirm the lock is held "
            "correctly across copy_from_user/copy_to_user to avoid TOCTOU races."
        )

    if ioctl_hits and not locking_hits:
        suggestions.append(
            "IOCTL/KVM uAPI changes without visible lock acquisition. Ensure the vcpu "
            "mutex or kvm->lock is held for the duration of state mutations."
        )

    if stats["added"] > 200 and not test_hits:
        suggestions.append(
            f"Large patch (+{stats['added']} lines) with no test additions detected. "
            "Consider adding a KVM selftest or kunit test to cover the new behaviour."
        )

    if stats["removed"] == 0 and stats["added"] > 50:
        suggestions.append(
            "Pure addition with no removed lines — double-check for dead code or "
            "duplicate logic that should replace, not augment, existing functionality."
        )

    if not suggestions:
        suggestions.append(
            "No major concerns flagged by static analysis. Review the style findings "
            "above and ensure the commit message references the relevant bug or "
            "mailing list discussion."
        )

    return summary, suggestions


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
    """Full pipeline: parse → style rules → local narrative → score."""
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

    ai_summary, ai_suggestions = local_review(subject, files)
    score = _score(all_findings)

    return ReviewResult(
        patch_subject=subject,
        files=files,
        findings=all_findings,
        ai_summary=ai_summary,
        ai_suggestions=ai_suggestions,
        score=score,
    )
