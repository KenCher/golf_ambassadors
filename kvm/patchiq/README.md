# 🔎 PatchIQ

> **AI-powered patch review for the KVM and Linux open source stack.**  
> From kernel to QEMU to libvirt — reviews code the way an upstream maintainer would.

[![Python 3.8+](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![watsonx](https://img.shields.io/badge/AI-watsonx%20Granite-blue.svg)](https://www.ibm.com/watsonx)

---

## Overview

PatchIQ is a developer-side patch review tool for the IBM KVM & Linux open source team. It analyses a unified diff and produces:

| Output | Description |
|--------|-------------|
| **Style findings** | Deterministic rule-based checks per layer (kernel/KVM, QEMU, libvirt) |
| **AI narrative** | watsonx Granite summary + actionable suggestions |
| **Patch score** | 0–100 quality score (errors −20, warnings −8, info −2) |
| **HTML report** | Self-contained report you can share or archive |

PatchIQ runs fully offline for style checks. The watsonx AI narrative is optional and requires IBM Cloud credentials.

---

## Requirements

- Python 3.8 or higher
- `pip install requests`
- *(Optional)* IBM Cloud API key + watsonx project ID for AI review

---

## Quick start

```bash
# 1. Clone the repo
git clone git@github.ibm.com:cheruiyo/Watsonx_challenge_2026.git
cd Watsonx_challenge_2026

# 2. Install the one runtime dependency
pip install requests

# 3. (Optional) Enable watsonx AI review
export WATSONX_API_KEY="your-ibm-cloud-api-key"
export WATSONX_PROJECT_ID="your-watsonx-project-id"

# 4. Review your latest commit
./run_review.sh

# 5. Review a patch file
./run_review.sh my_fix.patch

# 6. Review a commit range before pushing
./run_review.sh origin/main..HEAD

# 7. Pipe a diff directly
git diff HEAD~1 | ./run_review.sh
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
| `pipe` | Diff from stdin | `git diff HEAD~1 \| python3 -m patchiq.cli pipe` |

Add `--html report.html` to any command to save the full HTML report.

---

## How it works

PatchIQ runs a four-stage pipeline on every patch:

```
raw unified diff
    │
    ▼
parse_diff()      — split into per-file hunks, extract Subject header
    │
    ▼
detect_layer()    — classify each file: kernel | qemu | libvirt | unknown
    │
    ▼
run_rules()       — deterministic style checks per layer
    │
    ▼
ai_review()       — watsonx Granite 13B: summary + suggestions (optional)
    │
    ▼
ReviewResult      — findings + score + HTML report
```

Layer detection is **automatic** based on file paths in the diff:

| Path pattern | Layer |
|---|---|
| `virt/kvm/`, `arch/s390/`, `arch/x86/`, `drivers/vfio/`, `include/linux/` | **kernel** |
| `hw/virtio/`, `hw/s390x/`, `hw/vfio/`, `target/s390x/`, `migration/` | **qemu** |
| `src/qemu/`, `src/conf/`, `src/util/`, `src/libvirt/` | **libvirt** |
| Any `.c` / `.h` not matched above | **kernel** (fallback) |

Multi-layer patches (e.g. kernel + QEMU in the same commit) are handled automatically — each file gets its own layer and the correct rules applied.

---

## Rule coverage

### Kernel / KVM
| ID | Severity | Description |
|----|----------|-------------|
| K001 | warning | Prefer `pr_info` / `pr_err` / `pr_debug` over bare `printk()` |
| K002 | info | Direct return after allocation — consider `goto` for cleanup |
| K003 | warning | `ioremap` result should be assigned to an `__iomem` pointer |
| K004 | warning | `vcpu->arch` / `vcpu->regs` write without visible lock acquisition |

### QEMU
| ID | Severity | Description |
|----|----------|-------------|
| Q001 | warning | `error_free()` discards errors — use `error_propagate()` instead |
| Q002 | info | Prefer `g_new0(Type, n)` over `g_malloc0(sizeof(Type))` |
| Q003 | info | Prefer `g_assert_not_reached()` over `assert(0)` / `abort()` |
| Q004 | warning | More `object_unref()` calls than `object_ref()` — possible double-free |

### libvirt
| ID | Severity | Description |
|----|----------|-------------|
| L001 | warning | Use `virReportError()` instead of `fprintf(stderr, ...)` |
| L002 | info | `VIR_ALLOC` used but no `cleanup:` label found |
| L003 | warning | Use `virStrdup()` instead of bare `strdup()` |

### Universal (all layers)
| ID | Severity | Description |
|----|----------|-------------|
| U001 | warning | Line exceeds character limit (100 for kernel/libvirt, 80 for QEMU) |
| U002 | warning | Trailing whitespace |
| U003 | info | Unresolved `TODO` / `FIXME` / `HACK` / `XXX` marker |

---

## watsonx AI review

When `WATSONX_API_KEY` and `WATSONX_PROJECT_ID` are set, PatchIQ calls the watsonx text generation API:

- **Model:** `ibm/granite-13b-chat-v2` (override with `WATSONX_MODEL` env var)
- **Endpoint:** `https://us-south.ml.cloud.ibm.com` (override with `WATSONX_URL`)
- **Input:** Up to 6 files, 120 lines each, with a kernel-expert system prompt
- **Output:** JSON with `summary` (string) and `suggestions` (list)

Without credentials, style checks run in full and the AI section shows a graceful skip message.

---

## Scoring

Each finding deducts points from 100:

| Severity | Deduction |
|----------|-----------|
| error | −20 |
| warning | −8 |
| info | −2 |

Score is floored at 0. A patch with no findings scores **100/100**.

---

## Project structure

```
Watsonx_challenge_2026/
├── patchiq/
│   ├── __init__.py          package init (version 0.1.0)
│   ├── analyzer.py          diff parser + watsonx AI review engine
│   ├── rules.py             per-layer style rule definitions
│   ├── cli.py               command-line interface (4 subcommands)
│   ├── report.py            self-contained HTML report generator
│   ├── run_review.sh        shell convenience wrapper
│   ├── README.md            this file
│   └── tests/
│       ├── __init__.py
│       ├── test_rules.py    unit tests — every K/Q/L/U rule
│       ├── test_analyzer.py unit + integration tests — pipeline
│       └── fixtures/
│           ├── kernel.patch
│           ├── qemu.patch
│           └── libvirt.patch
```

---

## Running the tests

```bash
pip install pytest
python3 -m pytest tests/ -v
```

The test suite has **68 tests** covering every rule (positive and negative cases), the diff parser, layer detection, scoring logic, and end-to-end pipeline with fixture patches. No network access or watsonx credentials are required to run the tests.

---

## Git alias (optional)

Add to `~/.gitconfig` for one-keystroke reviews from any repo:

```ini
[alias]
    review = "!f() { cd $(git rev-parse --show-toplevel) && python3 -m patchiq.cli range ${1:-HEAD~1..HEAD} --html /tmp/patchiq_review.html && open /tmp/patchiq_review.html; }; f"
```

```bash
git review                  # review last commit
git review HEAD~5..HEAD     # review last 5 commits
```

---

## Contributing

To add a new rule:

1. Add a `check_*()` function to [`rules.py`](rules.py) following the existing pattern
2. Register it in the appropriate `RULE_SETS` list
3. Add a positive and negative unit test in [`tests/test_rules.py`](tests/test_rules.py)
4. Add a fixture line to the relevant patch in [`tests/fixtures/`](tests/fixtures/)

---

*PatchIQ — Built for the watsonx challenge 2026 by the IBM KVM & Linux open source team.*
