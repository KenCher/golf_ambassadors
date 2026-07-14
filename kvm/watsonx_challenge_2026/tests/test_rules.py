"""
Unit tests for every rule in watsonx_challenge_2026/rules.py.
Run from the repo root:  python3 -m pytest watsonx_challenge_2026/tests/ -v
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from watsonx_challenge_2026.rules import run_rules


# ─── helpers ──────────────────────────────────────────────────────────────────

def make_diff(path, added_lines, removed_lines=None):
    """Minimal unified diff for a single file."""
    lines = [
        f"diff --git a/{path} b/{path}",
        f"--- a/{path}",
        f"+++ b/{path}",
        "@@ -1 +1 @@",
    ]
    for l in (removed_lines or []):
        lines.append("-" + l)
    for l in added_lines:
        lines.append("+" + l)
    return lines


def ids(findings):
    return {f["rule_id"] for f in findings}


# ─── Universal ────────────────────────────────────────────────────────────────

class TestU001LongLine:
    def test_triggers_at_101_kernel(self):
        d = make_diff("virt/kvm/foo.c", ["x" * 101])
        assert "U001" in ids(run_rules(d, "kernel"))

    def test_ok_at_100_kernel(self):
        d = make_diff("virt/kvm/foo.c", ["x" * 100])
        assert "U001" not in ids(run_rules(d, "kernel"))

    def test_qemu_limit_is_80(self):
        d = make_diff("hw/virtio/foo.c", ["x" * 81])
        assert "U001" in ids(run_rules(d, "qemu"))

    def test_qemu_ok_at_80(self):
        d = make_diff("hw/virtio/foo.c", ["x" * 80])
        assert "U001" not in ids(run_rules(d, "qemu"))


class TestU002TrailingWhitespace:
    def test_trailing_space(self):
        d = make_diff("virt/kvm/foo.c", ["int x = 1;   "])
        assert "U002" in ids(run_rules(d, "kernel"))

    def test_trailing_tab(self):
        d = make_diff("virt/kvm/foo.c", ["int x = 1;\t"])
        assert "U002" in ids(run_rules(d, "kernel"))

    def test_clean_line_ok(self):
        d = make_diff("virt/kvm/foo.c", ["int x = 1;"])
        assert "U002" not in ids(run_rules(d, "kernel"))


class TestU003TodoFixme:
    def test_todo(self):
        d = make_diff("virt/kvm/foo.c", ["/* TODO: implement */"])
        assert "U003" in ids(run_rules(d, "kernel"))

    def test_fixme(self):
        d = make_diff("virt/kvm/foo.c", ["/* FIXME: broken */"])
        assert "U003" in ids(run_rules(d, "kernel"))

    def test_hack(self):
        d = make_diff("virt/kvm/foo.c", ["/* HACK: workaround */"])
        assert "U003" in ids(run_rules(d, "kernel"))

    def test_clean_ok(self):
        d = make_diff("virt/kvm/foo.c", ["/* normal comment */"])
        assert "U003" not in ids(run_rules(d, "kernel"))


# ─── Kernel / KVM ─────────────────────────────────────────────────────────────

class TestK001Printk:
    def test_bare_printk(self):
        d = make_diff("virt/kvm/foo.c", ['printk(KERN_INFO "hello\\n");'])
        assert "K001" in ids(run_rules(d, "kernel"))

    def test_pr_info_ok(self):
        d = make_diff("virt/kvm/foo.c", ['pr_info("hello\\n");'])
        assert "K001" not in ids(run_rules(d, "kernel"))

    def test_pr_err_ok(self):
        d = make_diff("virt/kvm/foo.c", ['pr_err("fail\\n");'])
        assert "K001" not in ids(run_rules(d, "kernel"))


class TestK002GotoCleanup:
    def test_return_after_alloc(self):
        d = make_diff("virt/kvm/foo.c", [
            "p = kzalloc(sizeof(*p), GFP_KERNEL);",
            "if (!p)",
            "    return -ENOMEM;",
        ])
        assert "K002" in ids(run_rules(d, "kernel"))

    def test_no_alloc_no_finding(self):
        d = make_diff("virt/kvm/foo.c", ["return -EINVAL;"])
        assert "K002" not in ids(run_rules(d, "kernel"))


class TestK003Iomem:
    def test_ioremap_without_iomem(self):
        d = make_diff("virt/kvm/foo.c", ["void *base = ioremap(addr, size);"])
        assert "K003" in ids(run_rules(d, "kernel"))

    def test_ioremap_with_iomem_ok(self):
        d = make_diff("virt/kvm/foo.c", ["void __iomem *base = ioremap(addr, size);"])
        assert "K003" not in ids(run_rules(d, "kernel"))


class TestK004VcpuLock:
    def test_vcpu_write_no_lock(self):
        # Direct write into vcpu->arch.regs — no lock in context should fire K004
        d = make_diff("virt/kvm/foo.c", [
            "int val = get_val();",
            "vcpu->arch.regs[VCPU_REGS_RAX] = val;",
        ])
        assert "K004" in ids(run_rules(d, "kernel"))

    def test_vcpu_write_with_lock_ok(self):
        d = make_diff("virt/kvm/foo.c", [
            "mutex_lock(&vcpu->mutex);",
            "vcpu->arch.regs[VCPU_REGS_RAX] = 0;",
        ])
        assert "K004" not in ids(run_rules(d, "kernel"))


# ─── QEMU ─────────────────────────────────────────────────────────────────────

class TestQ001ErrorFree:
    def test_error_free(self):
        d = make_diff("hw/virtio/foo.c", ["error_free(&err);"])
        assert "Q001" in ids(run_rules(d, "qemu"))

    def test_error_propagate_ok(self):
        d = make_diff("hw/virtio/foo.c", ["error_propagate(errp, err);"])
        assert "Q001" not in ids(run_rules(d, "qemu"))


class TestQ002GNew0:
    def test_g_malloc0_sizeof(self):
        d = make_diff("hw/virtio/foo.c", ["s = g_malloc0(sizeof(MyStruct));"])
        assert "Q002" in ids(run_rules(d, "qemu"))

    def test_g_new0_ok(self):
        d = make_diff("hw/virtio/foo.c", ["s = g_new0(MyStruct, 1);"])
        assert "Q002" not in ids(run_rules(d, "qemu"))


class TestQ003AssertNotReached:
    def test_assert_zero(self):
        d = make_diff("hw/virtio/foo.c", ["assert(0);"])
        assert "Q003" in ids(run_rules(d, "qemu"))

    def test_abort(self):
        d = make_diff("hw/virtio/foo.c", ["abort();"])
        assert "Q003" in ids(run_rules(d, "qemu"))

    def test_g_assert_not_reached_ok(self):
        d = make_diff("hw/virtio/foo.c", ["g_assert_not_reached();"])
        assert "Q003" not in ids(run_rules(d, "qemu"))


class TestQ004ObjectRefBalance:
    def test_more_unrefs_than_refs(self):
        d = make_diff("hw/virtio/foo.c", [
            "object_unref(obj);",
            "object_unref(obj);",
            "object_unref(obj);",
        ])
        assert "Q004" in ids(run_rules(d, "qemu"))

    def test_balanced_ok(self):
        d = make_diff("hw/virtio/foo.c", [
            "object_ref(obj);",
            "object_unref(obj);",
        ])
        assert "Q004" not in ids(run_rules(d, "qemu"))


# ─── libvirt ──────────────────────────────────────────────────────────────────

class TestL001VirReportError:
    def test_fprintf_stderr(self):
        d = make_diff("src/qemu/foo.c", ['fprintf(stderr, "error: %s\\n", msg);'])
        assert "L001" in ids(run_rules(d, "libvirt"))

    def test_vir_report_ok(self):
        d = make_diff("src/qemu/foo.c", ['virReportError(VIR_ERR_INTERNAL_ERROR, "%s", msg);'])
        assert "L001" not in ids(run_rules(d, "libvirt"))


class TestL002CleanupLabel:
    def test_vir_alloc_no_cleanup(self):
        d = make_diff("src/qemu/foo.c", ["VIR_ALLOC(priv);", "return ret;"])
        assert "L002" in ids(run_rules(d, "libvirt"))

    def test_vir_alloc_with_cleanup_ok(self):
        d = make_diff("src/qemu/foo.c", ["VIR_ALLOC(priv);", "cleanup:", "return ret;"])
        assert "L002" not in ids(run_rules(d, "libvirt"))

    def test_no_alloc_no_finding(self):
        d = make_diff("src/qemu/foo.c", ["return 0;"])
        assert "L002" not in ids(run_rules(d, "libvirt"))


class TestL003Virstrdup:
    def test_bare_strdup(self):
        d = make_diff("src/qemu/foo.c", ['name = strdup(src);'])
        assert "L003" in ids(run_rules(d, "libvirt"))

    def test_virstrdup_ok(self):
        d = make_diff("src/qemu/foo.c", ['if (virStrdup(&name, src) < 0)'])
        assert "L003" not in ids(run_rules(d, "libvirt"))
