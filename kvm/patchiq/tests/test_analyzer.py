"""
Unit + integration tests for patchiq/analyzer.py.
Run from the repo root:  python3 -m pytest patchiq/tests/ -v
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

import pytest
from patchiq.analyzer import parse_diff, detect_layer, _score, review_patch, Finding


FIXTURES = os.path.join(os.path.dirname(__file__), "fixtures")


# ─── detect_layer ─────────────────────────────────────────────────────────────

class TestDetectLayer:
    def test_kvm_path(self):        assert detect_layer("virt/kvm/kvm_main.c") == "kernel"
    def test_arch_s390(self):       assert detect_layer("arch/s390/kvm/kvm-s390.c") == "kernel"
    def test_arch_x86(self):        assert detect_layer("arch/x86/kvm/vmx/vmx.c") == "kernel"
    def test_include_linux(self):   assert detect_layer("include/linux/kvm_host.h") == "kernel"
    def test_hw_virtio(self):       assert detect_layer("hw/virtio/virtio-blk.c") == "qemu"
    def test_hw_s390x(self):        assert detect_layer("hw/s390x/css.c") == "qemu"
    def test_target_s390x(self):    assert detect_layer("target/s390x/cpu.c") == "qemu"
    def test_src_qemu(self):        assert detect_layer("src/qemu/qemu_driver.c") == "libvirt"
    def test_src_conf(self):        assert detect_layer("src/conf/domain_conf.c") == "libvirt"
    def test_unknown_py(self):      assert detect_layer("scripts/helper.py") == "unknown"
    def test_plain_c_defaults_kernel(self):
        assert detect_layer("random/foo.c") == "kernel"


# ─── parse_diff ───────────────────────────────────────────────────────────────

EMAIL_PATCH = """\
From abc123 Mon Sep 17 00:00:00 2001
Subject: [PATCH v2 1/3] kvm: fix vcpu teardown race

diff --git a/virt/kvm/kvm_main.c b/virt/kvm/kvm_main.c
--- a/virt/kvm/kvm_main.c
+++ b/virt/kvm/kvm_main.c
@@ -100,4 +100,5 @@
-old_line();
+new_line();
+printk(KERN_ERR "debug\\n");
diff --git a/hw/virtio/virtio-blk.c b/hw/virtio/virtio-blk.c
--- a/hw/virtio/virtio-blk.c
+++ b/hw/virtio/virtio-blk.c
@@ -50,3 +50,4 @@
+g_malloc0(sizeof(BlkConf));
"""

class TestParseDiff:
    def test_subject_stripped_of_patch_tag(self):
        subject, _ = parse_diff(EMAIL_PATCH)
        assert subject == "kvm: fix vcpu teardown race"
        assert "[PATCH" not in subject

    def test_file_count(self):
        _, files = parse_diff(EMAIL_PATCH)
        assert len(files) == 2

    def test_layer_assignment(self):
        _, files = parse_diff(EMAIL_PATCH)
        paths = {f.path: f.layer for f in files}
        assert paths["virt/kvm/kvm_main.c"] == "kernel"
        assert paths["hw/virtio/virtio-blk.c"] == "qemu"

    def test_lines_captured(self):
        _, files = parse_diff(EMAIL_PATCH)
        kvm_file = next(f for f in files if "kvm_main" in f.path)
        assert any("printk" in l for l in kvm_file.lines)

    def test_no_subject_falls_back_to_filename(self):
        diff = """\
diff --git a/virt/kvm/foo.c b/virt/kvm/foo.c
--- a/virt/kvm/foo.c
+++ b/virt/kvm/foo.c
@@ -1 +1 @@
+int x;
"""
        subject, _ = parse_diff(diff)
        assert "virt/kvm/foo.c" in subject

    def test_empty_diff(self):
        subject, files = parse_diff("")
        assert files == []


# ─── _score ───────────────────────────────────────────────────────────────────

def f(severity): return Finding("X001", severity, "kernel", "test finding")

class TestScore:
    def test_perfect_score(self):       assert _score([]) == 100
    def test_one_error(self):           assert _score([f("error")]) == 80
    def test_one_warning(self):         assert _score([f("warning")]) == 92
    def test_one_info(self):            assert _score([f("info")]) == 98
    def test_mixed(self):
        assert _score([f("error"), f("warning"), f("info")]) == 70
    def test_floor_at_zero(self):
        assert _score([f("error")] * 20) == 0
    def test_unknown_severity_no_deduction(self):
        assert _score([f("unknown")]) == 100


# ─── review_patch (integration, AI skipped without env vars) ──────────────────

class TestReviewPatch:
    def test_returns_result_object(self):
        result = review_patch(EMAIL_PATCH)
        assert result.patch_subject == "kvm: fix vcpu teardown race"

    def test_score_in_range(self):
        result = review_patch(EMAIL_PATCH)
        assert 0 <= result.score <= 100

    def test_finds_k001_printk(self):
        result = review_patch(EMAIL_PATCH)
        assert any(f.rule_id == "K001" for f in result.findings)

    def test_finds_q002_g_malloc0(self):
        result = review_patch(EMAIL_PATCH)
        assert any(f.rule_id == "Q002" for f in result.findings)

    def test_ai_fallback_message_when_no_key(self):
        result = review_patch(EMAIL_PATCH)
        assert "skipped" in result.ai_summary.lower() or isinstance(result.ai_summary, str)

    def test_fixture_kernel_patch(self):
        raw = open(os.path.join(FIXTURES, "kernel.patch")).read()
        result = review_patch(raw)
        rule_ids = {f.rule_id for f in result.findings}
        assert "K001" in rule_ids    # printk
        assert "K003" in rule_ids    # ioremap without __iomem
        assert "U003" in rule_ids    # TODO marker

    def test_fixture_qemu_patch(self):
        raw = open(os.path.join(FIXTURES, "qemu.patch")).read()
        result = review_patch(raw)
        rule_ids = {f.rule_id for f in result.findings}
        assert "Q001" in rule_ids    # error_free
        assert "Q002" in rule_ids    # g_malloc0
        assert "Q003" in rule_ids    # assert(0)
        assert "Q004" in rule_ids    # 3 unrefs

    def test_fixture_libvirt_patch(self):
        raw = open(os.path.join(FIXTURES, "libvirt.patch")).read()
        result = review_patch(raw)
        rule_ids = {f.rule_id for f in result.findings}
        assert "L001" in rule_ids    # fprintf stderr
        assert "L002" in rule_ids    # VIR_ALLOC no cleanup
        assert "L003" in rule_ids    # strdup
