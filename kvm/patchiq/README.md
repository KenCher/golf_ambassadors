# 🔎 PatchIQ

> **Local AI-powered patch review for the KVM and Linux open source stack.**  
> From kernel to QEMU to libvirt — reviews code the way an upstream maintainer would.  
> **No credentials or internet access required.**

[![Python 3.8+](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Engine: Local](https://img.shields.io/badge/engine-local%20heuristic-brightgreen.svg)](#)

---

## Overview

PatchIQ is a developer-side patch review tool for the IBM KVM & Linux open source team. It analyses a unified diff and produces:

| Output | Description |
|--------|-------------|
| **Style findings** | Deterministic rule-based checks per layer (kernel/KVM, QEMU, libvirt) |
| **Narrative summary** | Local heuristic analysis — locking, memory, security, test coverage |
| **Actionable suggestions** | Up to 5 targeted improvement hints per patch |
| **Patch score** | 0–100 quality score (errors −20, warnings −8, info −2) |
| **HTML report** | Self-contained report you can share or archive |

PatchIQ runs **fully offline** — no API keys, no internet connection, no wait time.

### Two editions

| Edition | Engine | File | Notes |
|---------|--------|------|-------|
| **Local** (default) | Heuristic pattern analysis | `analyzer.py` | No credentials needed |
| **watsonx** | IBM Granite via watsonx.ai | `analyzer-wx.py` | Requires IBM Cloud API key |

To use the watsonx edition, swap `analyzer.py` ↔ `analyzer-wx.py` and run `run_review-wx.sh`.

---

## Requirements

- Python 3.8 or higher
- No additional dependencies for local mode
- *(watsonx edition only)* `pip install requests` + IBM Cloud credentials

---

## Quick start

```bash
# 1. Clone the repo
git clone git@github.ibm.com:cheruiyo/us-kvm-status.git
cd us-kvm-status/kvm

# 2. Review your latest commit (no setup needed)
./patchiq/run_review.sh

# 3. Review a patch file
./patchiq/run_review.sh my_fix.patch

# 4. Review a commit range before pushing
./patchiq/run_review.sh origin/main..HEAD

# 5. Pipe a diff directly
git diff HEAD~1 | ./patchiq/run_review.sh
```

Each run prints a terminal report and saves a timestamped HTML file (e.g. `patchiq_review_20260714_094500.html`). On macOS the script offers to open it in your browser automatically.

---

## CLI reference

Run from any directory that contains the patches or git history you want to review:

```
python3 -m patchiq.cli patch  <file.patch>  [--html out.html]
python3 -m patchiq.cli commit [ref]         [--html out.html]
python3 -m patchiq.cli range  <base..head>  [--html out.html]
python3 -m patchiq.cli pipe                 [--html out.html]
```

| Subcommand | Input | Example |
|---|---|---|
| `patch` | A `.patch` file on disk | `python3 -m patchiq.cli patch fix.patch` |
| `commit` | A git ref (default: `HEAD`) | `python3 -m patchiq.cli commit HEAD~2` |
| `range` | A git range | `python3 -m patchiq.cli range origin/main..HEAD` |
| `pipe` | stdin unified diff | `git diff HEAD~1 \| python3 -m patchiq.cli pipe` |

---

## Style rules

### Universal (all layers)

| ID | Severity | Description |
|----|----------|-------------|
| U001 | warning | Line exceeds 100 characters |
| U002 | warning | Trailing whitespace |
| U003 | info | TODO / FIXME left in added code |

### Kernel / KVM (K-rules)

| ID | Severity | Description |
|----|----------|-------------|
| K001 | warning | Bare `printk()` — use `pr_err` / `pr_warn` / `pr_info` |
| K002 | warning | Error path without `goto` label |
| K003 | info | Missing `__user`, `__iomem`, or `__must_check` sparse annotation |
| K004 | error | `vcpu->arch/regs/sregs` mutated without vcpu lock comment |

### QEMU (Q-rules)

| ID | Severity | Description |
|----|----------|-------------|
| Q001 | warning | Error without `error_setg` / `error_propagate` |
| Q002 | info | `g_malloc0` — prefer `g_new0(Type, n)` |
| Q003 | warning | `assert(0)` — use `qemu_build_not_reached()` |
| Q004 | info | `object_ref` without paired `object_unref` |

### libvirt (L-rules)

| ID | Severity | Description |
|----|----------|-------------|
| L001 | warning | `fprintf` to stderr — use `virReportError` |
| L002 | warning | Early return without `cleanup:` label pattern |
| L003 | info | `strdup` — use `virStrdup` for auto-error-reporting |

---

## Scoring

```
score = max(0,  100
              − (errors   × 20)
              − (warnings ×  8)
              − (info     ×  2))
```

A clean patch scores **100/100**. Non-C files (YAML, shell, Markdown) score 100 by design.

---

## Local heuristic engine

The default `analyzer.py` analyses added lines with regex pattern banks:

| Pattern bank | What it detects |
|---|---|
| Security | `copy_from_user`, `copy_to_user`, `__user`, `kmalloc`, mutex/spinlock/RCU |
| Locking | `mutex`, `spinlock`, `rwlock`, `semaphore`, `rcu` |
| Memory | `kmalloc`, `kzalloc`, `vzalloc`, `kfree` |
| Error | `ENOMEM`, `EINVAL`, `goto *err`, `return -E*` |
| IOCTL | `KVM_*`, `VFIO_*`, `ioctl` |
| Tests | `assert`, `kselftest`, `kunit_test`, `g_assert` |

Suggestions are generated based on pattern co-occurrence — e.g. allocation without error path, locking + user-copy, large patch without tests.

---

## watsonx edition

The `-wx` files are the original watsonx-backed versions:

```bash
# Swap in the watsonx engine
cp patchiq/analyzer-wx.py patchiq/analyzer.py   # or run from analyzer-wx.py directly

# Set credentials
export WATSONX_API_KEY="..."
export WATSONX_PROJECT_ID="..."

# Run
./patchiq/run_review-wx.sh
```

The watsonx edition calls `ibm/granite-3-8b-instruct` via `us-south.ml.cloud.ibm.com` and requires an IBM Cloud API key and watsonx project ID.

---

## File structure

```
patchiq/
├── __init__.py              version 0.2.0
├── analyzer.py              Local heuristic engine (no credentials needed)
├── analyzer-wx.py           watsonx Granite edition (preserved)
├── rules.py                 14 style rules (K001–K004, Q001–Q004, L001–L003, U001–U003)
├── cli.py                   4 subcommands: patch / commit / range / pipe
├── report.py                HTML report generator
├── run_review.sh            Shell wrapper — local engine, no .env needed
├── run_review-wx.sh         Shell wrapper — watsonx edition (auto-loads .env)
├── build_pptx.py            16-slide PPTX deck builder
├── PatchIQ_Presentation_2026.pptx
├── pyproject.toml           PEP 517 packaging, ruff/pytest config
├── requirements.txt         (empty for local mode — stdlib only)
├── requirements-dev.txt     pytest, ruff, pre-commit
├── .env.example             Credentials template (watsonx edition)
├── LICENSE                  MIT
├── CHANGELOG.md
├── CONTRIBUTING.md
├── .pre-commit-config.yaml  ruff lint+format hooks
├── .github/workflows/ci.yml Python 3.8–3.12 matrix
└── tests/
    ├── test_rules.py        36 rule unit tests
    ├── test_analyzer.py     32 analyzer/pipeline tests
    └── fixtures/
        ├── kernel.patch     triggers K001–K004, U001–U003 → 56/100
        ├── qemu.patch       triggers Q001–Q004, U003 → 78/100
        └── libvirt.patch    triggers L001–L003 → 82/100
```

---

## Running tests

```bash
cd kvm
python3 -m pytest patchiq/tests/ -v
# 68 tests — all pass, no external dependencies
```

---

*PatchIQ — IBM KVM & Linux open source team*  
*Made with IBM Bob*
