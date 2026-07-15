"""
PatchIQ — Coding style rules for KVM/Linux kernel, QEMU, and libvirt.
Each rule is a dict: { id, layer, severity, description, check(diff_lines) -> [findings] }
"""

import re

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _lines_added(diff_lines):
    """Return only added lines ('+' prefix, skip '+++' file header)."""
    return [l[1:] for l in diff_lines if l.startswith('+') and not l.startswith('+++')]


def _lines_removed(diff_lines):
    return [l[1:] for l in diff_lines if l.startswith('-') and not l.startswith('---')]


def _finding(rule_id, severity, layer, message, line=None):
    return {
        "rule_id": rule_id,
        "severity": severity,
        "layer": layer,
        "message": message,
        "line": line,
    }


# ---------------------------------------------------------------------------
# Universal rules (all layers)
# ---------------------------------------------------------------------------

def check_long_lines(diff_lines, layer="all", limit=100):
    findings = []
    for line in _lines_added(diff_lines):
        if len(line) > limit:
            findings.append(_finding(
                "U001", "warning", layer,
                f"Line exceeds {limit} characters ({len(line)} chars): {line[:80]}...",
                line
            ))
    return findings


def check_trailing_whitespace(diff_lines, layer="all"):
    findings = []
    for line in _lines_added(diff_lines):
        if re.search(r'[ \t]+$', line):
            findings.append(_finding(
                "U002", "warning", layer,
                f"Trailing whitespace: '{line.rstrip()}'",
                line
            ))
    return findings


def check_todo_fixme(diff_lines, layer="all"):
    findings = []
    for line in _lines_added(diff_lines):
        if re.search(r'\b(TODO|FIXME|HACK|XXX)\b', line, re.IGNORECASE):
            findings.append(_finding(
                "U003", "info", layer,
                f"Unresolved marker found: {line.strip()}",
                line
            ))
    return findings


# ---------------------------------------------------------------------------
# Kernel / KVM rules
# ---------------------------------------------------------------------------

def check_kernel_printk(diff_lines):
    """Kernel: prefer pr_* / dev_* over bare printk."""
    findings = []
    for line in _lines_added(diff_lines):
        if re.search(r'\bprintk\s*\(', line):
            findings.append(_finding(
                "K001", "warning", "kernel",
                f"Prefer pr_info/pr_err/pr_debug over printk(): {line.strip()}",
                line
            ))
    return findings


def check_kernel_goto_error(diff_lines):
    """Kernel: error paths should use goto for cleanup."""
    findings = []
    added = _lines_added(diff_lines)
    for i, line in enumerate(added):
        if re.search(r'\breturn\s+-E[A-Z]+', line):
            # Check if there's an allocated resource in recent context (simple heuristic)
            context = ' '.join(added[max(0, i-10):i])
            if re.search(r'\b(kmalloc|kzalloc|vmalloc|alloc_pages|request_irq)\b', context):
                findings.append(_finding(
                    "K002", "info", "kernel",
                    f"Direct return after allocation — consider goto for cleanup: {line.strip()}",
                    line
                ))
    return findings


def check_kernel_sparse_annotations(diff_lines):
    """Kernel: __iomem, __user, __rcu annotations."""
    findings = []
    for line in _lines_added(diff_lines):
        # Pointer to I/O region without __iomem
        if re.search(r'\bvoid\s*\*\s*\w+.*=.*ioremap', line) and '__iomem' not in line:
            findings.append(_finding(
                "K003", "warning", "kernel",
                f"ioremap result should be assigned to __iomem pointer: {line.strip()}",
                line
            ))
    return findings


def check_kvm_vcpu_lock(diff_lines):
    """KVM: vCPU state changes should hold the vCPU mutex."""
    findings = []
    added = _lines_added(diff_lines)
    for i, line in enumerate(added):
        if re.search(r'vcpu->(arch|regs|sregs)[\w.\[\]]*\s*=', line):
            context = ' '.join(added[max(0, i-15):i])
            if not re.search(r'mutex_lock|spin_lock|srcu_read_lock', context):
                findings.append(_finding(
                    "K004", "warning", "kernel/kvm",
                    f"vCPU state write without visible lock acquisition: {line.strip()}",
                    line
                ))
    return findings


# ---------------------------------------------------------------------------
# QEMU rules
# ---------------------------------------------------------------------------

def check_qemu_error_propagation(diff_lines):
    """QEMU: Error* should be propagated, not silently dropped."""
    findings = []
    for line in _lines_added(diff_lines):
        if re.search(r'error_free\s*\(\s*&', line):
            findings.append(_finding(
                "Q001", "warning", "qemu",
                f"error_free() discards an error — propagate with error_propagate() instead: {line.strip()}",
                line
            ))
    return findings


def check_qemu_g_new0(diff_lines):
    """QEMU: prefer g_new0() over g_malloc0(sizeof(...))."""
    findings = []
    for line in _lines_added(diff_lines):
        if re.search(r'g_malloc0\s*\(\s*sizeof\s*\(', line):
            findings.append(_finding(
                "Q002", "info", "qemu",
                f"Prefer g_new0(Type, count) over g_malloc0(sizeof(Type)): {line.strip()}",
                line
            ))
    return findings


def check_qemu_assert_not_reached(diff_lines):
    """QEMU: use g_assert_not_reached() not assert(0)/abort()."""
    findings = []
    for line in _lines_added(diff_lines):
        if re.search(r'\bassert\s*\(\s*0\s*\)|\babort\s*\(\s*\)', line):
            findings.append(_finding(
                "Q003", "info", "qemu",
                f"Prefer g_assert_not_reached() over assert(0)/abort(): {line.strip()}",
                line
            ))
    return findings


def check_qemu_object_ref(diff_lines):
    """QEMU: object_ref/unref pairing — flag unref without ref in same diff."""
    findings = []
    added = ' '.join(_lines_added(diff_lines))
    unref_count = len(re.findall(r'\bobject_unref\b', added))
    ref_count = len(re.findall(r'\bobject_ref\b', added))
    if unref_count > ref_count + 1:
        findings.append(_finding(
            "Q004", "warning", "qemu",
            f"More object_unref() calls ({unref_count}) than object_ref() calls ({ref_count}) — check for double-free",
        ))
    return findings


# ---------------------------------------------------------------------------
# libvirt rules
# ---------------------------------------------------------------------------

def check_libvirt_virreport(diff_lines):
    """libvirt: use virReportError() not fprintf(stderr, ...)."""
    findings = []
    for line in _lines_added(diff_lines):
        if re.search(r'fprintf\s*\(\s*stderr', line):
            findings.append(_finding(
                "L001", "warning", "libvirt",
                f"Use virReportError() instead of fprintf(stderr,...): {line.strip()}",
                line
            ))
    return findings


def check_libvirt_cleanup_label(diff_lines):
    """libvirt: functions with allocations should have a 'cleanup:' label."""
    findings = []
    added = _lines_added(diff_lines)
    full = ' '.join(added)
    has_alloc = bool(re.search(r'\bVIR_ALLOC\b|\bvirAlloc\b', full))
    has_cleanup = bool(re.search(r'\bcleanup\s*:', full))
    if has_alloc and not has_cleanup:
        findings.append(_finding(
            "L002", "info", "libvirt",
            "VIR_ALLOC used but no 'cleanup:' label found — verify resource cleanup path",
        ))
    return findings


def check_libvirt_virstrdup(diff_lines):
    """libvirt: use virStrdup() not strdup()."""
    findings = []
    for line in _lines_added(diff_lines):
        if re.search(r'\bstrdup\s*\(', line):
            findings.append(_finding(
                "L003", "warning", "libvirt",
                f"Use virStrdup() instead of strdup(): {line.strip()}",
                line
            ))
    return findings


# ---------------------------------------------------------------------------
# Rule registry
# ---------------------------------------------------------------------------

RULE_SETS = {
    "kernel": [
        lambda d: check_long_lines(d, "kernel", 100),
        lambda d: check_trailing_whitespace(d, "kernel"),
        lambda d: check_todo_fixme(d, "kernel"),
        check_kernel_printk,
        check_kernel_goto_error,
        check_kernel_sparse_annotations,
        check_kvm_vcpu_lock,
    ],
    "qemu": [
        lambda d: check_long_lines(d, "qemu", 80),
        lambda d: check_trailing_whitespace(d, "qemu"),
        lambda d: check_todo_fixme(d, "qemu"),
        check_qemu_error_propagation,
        check_qemu_g_new0,
        check_qemu_assert_not_reached,
        check_qemu_object_ref,
    ],
    "libvirt": [
        lambda d: check_long_lines(d, "libvirt", 100),
        lambda d: check_trailing_whitespace(d, "libvirt"),
        lambda d: check_todo_fixme(d, "libvirt"),
        check_libvirt_virreport,
        check_libvirt_cleanup_label,
        check_libvirt_virstrdup,
    ],
}


def run_rules(diff_lines, layer):
    """Run all rules for the given layer and return list of findings."""
    findings = []
    for rule_fn in RULE_SETS.get(layer, []):
        findings.extend(rule_fn(diff_lines))
    return findings
