# 🔬 CIIQ — CI Intelligence & Insight Query

> **Local rule-based root-cause analyser for KVM, QEMU, and libvirt CI failures on IBM Z (s390x).**  
> Identifies introducing commits and root causes by scanning CI logs and git deltas.  
> **No credentials or internet access required.**

[![Python 3.9+](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/flask-3.x-lightgrey.svg)](https://flask.palletsprojects.com/)
[![Engine: Local](https://img.shields.io/badge/engine-local%20heuristic-brightgreen.svg)](#)

---

## Overview

CIIQ identifies the **introducing commit** behind CI failures by combining the real git delta (what changed between the last passing and failing run) with structured log pattern analysis — returning a commit hash, affected subsystems, and concrete fix commands entirely locally.

### Two editions

| Edition | Engine | File | Notes |
|---------|--------|------|-------|
| **Local** (default) | Heuristic log scanner + git delta parser | `app.py` | No credentials needed |
| **watsonx** | IBM Granite via watsonx.ai | `app-wx.py` | Requires IBM Cloud API key |

To use the watsonx edition: `cp app-wx.py app.py` and `./run-wx.sh`.

---

## Architecture

```
Browser UI (ciiq.html)
        │  REST/JSON over HTTP
        ▼
Flask backend (app.py)  ←── config.yaml (log paths, suites)
        │
        ├── GET  /                        Serve web UI
        ├── GET  /api/config              Return config (no secrets)
        ├── POST /api/analyse/kvm         Analyse KVM suites
        ├── POST /api/analyse/qemu        Analyse QEMU suites
        ├── POST /api/analyse/libvirt     Analyse libvirt suites
        ├── POST /api/analyse/all         Analyse all three projects
        ├── POST /api/correlate           Cross-project correlation
        ├── GET  /api/runs                List CI run dates from log dir
        ├── GET  /api/run/<date>/suites   Auto-populate suite log snippets
        ├── GET  /api/history             Session analysis history
        └── DELETE /api/history           Clear history
                │
                ▼
        Local Analysis Engine
        ├── _scan_log()        20 error-pattern regexes + 10 subsystem patterns
        ├── _extract_commits() git log → [{sha, subject}]
        ├── analyse_project()  per-project Markdown report (6 sections)
        └── correlate_projects() cross-project cascade + minimum fix set
```

---

## Quick Start

```bash
cd /path/to/kvm/ciiq/

# First time — install deps
./run.sh setup

# Start the server (auto-kills any stale process on :5100)
./run.sh

# Open in browser
open http://localhost:5100
```

### Stop / restart

```bash
./run.sh stop   # graceful shutdown (gunicorn) or Ctrl+C (dev)
./run.sh        # restart
```

### Production (shared team server)

```bash
./run.sh prod      # gunicorn, 4 workers, background, logs to ciiq.log
./run.sh stop      # graceful shutdown
tail -f ciiq.log   # live logs
```

---

## Daily Workflow

### 1 — Extract the git delta (on tuxmaker)

```bash
# Option A: use the helper script
cd /home/ciuser/ciiq
./extract_delta.sh 20260714 20260713   # generates ciiq_delta_20260714.json

# Option B: manual
TODAY=20260714; YEST=20260713
GOOD=$(cat /home/ciuser/logs/daily/$YEST/kernel.sha)
BAD=$(cat /home/ciuser/logs/daily/$TODAY/kernel.sha)
cd /home/ciuser/linux

git log --oneline $GOOD..$BAD -- arch/s390/kvm/ include/uapi/linux/kvm.h
git diff --stat $GOOD..$BAD
git diff $GOOD..$BAD -- arch/s390/kvm/ | head -200
```

### 2 — Open CIIQ

```
http://localhost:5100
```

### 3 — Paste the git delta

Fill in the **Git Delta** panel tabs:

| Tab | Source |
|-----|--------|
| git log | `git log --oneline $GOOD..$BAD` |
| diff --stat | `git diff --stat $GOOD..$BAD` |
| patch hunks | `git diff $GOOD..$BAD -- arch/s390/kvm/` |
| env / pkgs | `rpm -qa \| grep -E 's390-tools\|qemu\|libvirt'` |

### 4 — Load failure logs

Click **Load Run Logs** (reads `/home/ciuser/logs/daily/YYYYMMDD/`) or paste `FAIL / BUG / ERROR / panic` lines from suite logs.

### 5 — Analyse

Click **⚡ Analyse All Projects** — CIIQ scans all logs and produces a structured report instantly (no API call).

### 6 — Correlate

Click **🔗 Correlate** for the cross-project dependency chain and minimum revert set.

### 7 — File the bug

| CIIQ section | Bugzilla field |
|---|---|
| Introducing Commit | `commit` / URL |
| Root Cause | Description body |
| Affected Subsystems | Component tags |
| Recommended Fix | Patch attachment |
| Verification command | Steps to Reproduce |

---

## Local Analysis Engine

### Error patterns detected

The engine scans logs for 20 error signatures:

`kernel BUG` · `kernel panic` · `kernel Oops` · `GPF` · `segfault` · `NULL deref` · `use-after-free` · `stack overflow` · `deadlock` · `kernel WARNING` · `timeout` · `test FAIL` · `ERROR` · `abort` · `assertion` · `device not found` · `permission denied` · `EINVAL` · `OOM` · `migration failure`

### Subsystems identified

`KVM core` · `s390x arch` · `memory mgmt` · `VFIO` · `virtio` · `live migration` · `CPU model` · `QMP/monitor` · `libvirt driver` · `QEMU block`

### Report structure (per project)

Each `analyse_project()` call generates 6 Markdown sections:

1. **Introducing Commit(s)** — parsed from git log, with diff --stat
2. **Root Cause** — top-5 error signatures, representative failure lines, project context
3. **Affected Subsystems** — matched from log content
4. **Why this project is affected** — migration / KVM / ABI reasoning
5. **Recommended Fix** — specific `git revert` command with commit hash
6. **Verification Command** — targeted tuxmaker command

---

## API Reference

All endpoints accept and return JSON.

### POST `/api/analyse/<project>`

```bash
curl -X POST http://localhost:5100/api/analyse/kvm \
  -H 'Content-Type: application/json' \
  -d '{
    "run_date": "2026-07-14",
    "run_id":   "1566",
    "delta": {
      "sha_good":      "a1b2c3d4",
      "sha_bad":       "f7e8d9c0",
      "git_log":       "f7e8d9c kvm/s390: add intercept for 0xb9af\n...",
      "git_diff_stat": "arch/s390/kvm/intercept.c | 47 ++++++--",
      "git_patch":     "diff --git a/arch/s390/kvm/intercept.c\n+..."
    },
    "suite_logs": {
      "hades":         "BUG: unable to handle NULL pointer dereference",
      "kvm-selftests": "FAILED: test_set_guest_debug\ntimeout waiting for vcpu"
    }
  }'
```

Response:
```json
{
  "ok": true,
  "project": "kvm",
  "analysis": "## Run 2026-07-14  #1566  — KVM Analysis\n...",
  "engine": "local"
}
```

### POST `/api/analyse/all`

Accepts `suite_logs` in **nested** or **flat** format (auto-split):

```bash
# flat format — auto-split by suite name
curl -X POST http://localhost:5100/api/analyse/all \
  -H 'Content-Type: application/json' \
  -d @ciiq_delta_20260714.json
```

### POST `/api/correlate`

```bash
curl -X POST http://localhost:5100/api/correlate \
  -H 'Content-Type: application/json' \
  -d '{
    "run_date": "2026-07-14",
    "delta": { "git_log": "f7e8d9c kvm/s390: ..." },
    "analyses": {
      "kvm":     "... analysis from /api/analyse/kvm ...",
      "qemu":    "...",
      "libvirt": "..."
    }
  }'
```

### GET `/api/run/<date>/suites`

```bash
curl http://localhost:5100/api/run/20260714/suites
```

---

## Configuration (`config.yaml`)

```yaml
ci:
  log_base:         "/home/ciuser/logs/daily"
  webui_base:       "https://lnxgwne1.boeblingen.de.ibm.com/linux-ci/webui/ci-run"
  tuxmaker_host:    "tuxmaker"
  kernel_repo:      "/home/ciuser/linux"

server:
  host:   "0.0.0.0"
  port:   5100
  debug:  false
```

No `watsonx:` block in the local edition. For credentials, see `config-wx.yaml`.

---

## Supported Suites

| Project | Suite | Category |
|---------|-------|----------|
| KVM | `canton-prototype` | kernel |
| KVM | `ci-reipl` | infra |
| KVM | `hades` | kernel |
| KVM | `hades-monolithic` | kernel |
| KVM | `hades-withHW` | hw |
| KVM | `kvm-selftests` | test |
| KVM | `kvm-unit-tests-kvm` | test |
| KVM | `s390-tools` | config |
| QEMU | `qemu-s390x-kvm` | kernel |
| QEMU | `qemu-migration-s390` | config |
| QEMU | `qemu-unit-tests` | test |
| QEMU | `qemu-tcg-s390x` | test |
| libvirt | `libvirt-s390x` | config |
| libvirt | `libvirt-migration` | config |
| libvirt | `libvirt-qemu-driver` | kernel |
| libvirt | `libvirt-unit-tests` | test |

---

## File Structure

```
ciiq/
├── app.py               Local heuristic engine — 9 REST endpoints
├── app-wx.py            watsonx Granite edition (preserved)
├── config.yaml          Team config — log paths, suites, server port
├── config-wx.yaml       watsonx edition config (preserved)
├── requirements.txt     flask, flask-cors, pyyaml, python-dotenv, gunicorn
├── run.sh               Setup + dev/prod/stop (local edition)
├── run-wx.sh            Setup + dev/prod/stop (watsonx edition, preserved)
├── extract_delta.sh     Tuxmaker git delta extractor → JSON
├── .env.example         Credentials template (watsonx edition only)
├── CONTRIBUTING.md
├── CHANGELOG.md
├── .github/workflows/ci.yml  Python 3.10–3.12 smoke tests
└── templates/
    └── ciiq.html        Full browser UI
```

---

## Troubleshooting

**`Address already in use` on port 5100**
```bash
lsof -ti:5100 | xargs kill -9
./run.sh
```

**"No suite logs found" after clicking Load Run Logs**
- The log directory `ci.log_base` is not mounted locally
- Run `./extract_delta.sh` on tuxmaker and paste snippets manually

**Missing module error on startup**
```bash
./run.sh setup    # re-installs dependencies into .venv
```

---

*CIIQ — IBM KVM CI Intelligence & Insight Query (local edition)*  
*Made with IBM Bob*
