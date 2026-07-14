# 🔎 PatchIQ

> **AI-powered patch review for the KVM and Linux open source stack.**  
> From kernel to QEMU to libvirt — reviews code the way an upstream maintainer would.

---

## What it does

PatchIQ analyses a unified diff and produces:

| Output | Description |
|--------|-------------|
| **Style findings** | Rule-based checks per layer (kernel/KVM, QEMU, libvirt) |
| **AI narrative** | watsonx Granite summary + actionable suggestions |
| **Patch score** | 0–100 quality score based on findings |
| **HTML report** | Self-contained report you can share or archive |

---

## Quick start

```bash
# 1. Install dependencies
pip install requests

# 2. Set watsonx credentials (optional — style checks work without it)
export WATSONX_API_KEY="your-ibm-cloud-api-key"
export WATSONX_PROJECT_ID="your-watsonx-project-id"

# 3. Review your latest commit
./watsonx_challenge_2026/run_review.sh

# 4. Review a patch file
./watsonx_challenge_2026/run_review.sh my_fix.patch

# 5. Review a commit range
./watsonx_challenge_2026/run_review.sh origin/main..HEAD

# 6. Pipe a diff directly
git diff HEAD~1 | ./watsonx_challenge_2026/run_review.sh
```

---

## CLI reference

```
python -m watsonx_challenge_2026.cli patch  <file.patch>  [--html out.html]
python -m watsonx_challenge_2026.cli commit [ref]         [--html out.html]
python -m watsonx_challenge_2026.cli range  <base..head>  [--html out.html]
python -m watsonx_challenge_2026.cli pipe                 [--html out.html]
```

---

## Rule coverage

### Kernel / KVM
| Rule | Description |
|------|-------------|
| K001 | Prefer `pr_info/pr_err` over bare `printk()` |
| K002 | Direct return after allocation — consider `goto` for cleanup |
| K003 | `ioremap` result should be assigned to `__iomem` pointer |
| K004 | vCPU state write without visible lock acquisition |

### QEMU
| Rule | Description |
|------|-------------|
| Q001 | `error_free()` discards errors — use `error_propagate()` |
| Q002 | Prefer `g_new0()` over `g_malloc0(sizeof(...))` |
| Q003 | Prefer `g_assert_not_reached()` over `assert(0)`/`abort()` |
| Q004 | More `object_unref()` calls than `object_ref()` — possible double-free |

### libvirt
| Rule | Description |
|------|-------------|
| L001 | Use `virReportError()` instead of `fprintf(stderr,...)` |
| L002 | `VIR_ALLOC` used but no `cleanup:` label found |
| L003 | Use `virStrdup()` instead of `strdup()` |

### Universal (all layers)
| Rule | Description |
|------|-------------|
| U001 | Line exceeds character limit (100 kernel/libvirt, 80 QEMU) |
| U002 | Trailing whitespace |
| U003 | Unresolved `TODO`/`FIXME`/`HACK`/`XXX` marker |

---

## Project structure

```
watsonx_challenge_2026/
├── __init__.py      package init
├── analyzer.py      diff parser + watsonx AI review engine
├── rules.py         per-layer style rule definitions
├── cli.py           command-line interface
├── report.py        HTML report generator
├── run_review.sh    shell convenience wrapper
└── README.md        this file
```

---

## watsonx model

Uses **IBM Granite 13B Chat v2** (`ibm/granite-13b-chat-v2`) by default.  
Override with `WATSONX_MODEL` env var.

---

*PatchIQ — Built for the watsonx challenge by the KVM & Linux open source team.*
