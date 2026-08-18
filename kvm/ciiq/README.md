# CIIQ — CI Intelligence & Insight Query

> Root-cause analysis for KVM · QEMU · libvirt CI failures on IBM Z (s390x).  
> Paste a CI mail → instant structured report with age-based verdicts, node
> health, fixed-test tracking, and a downloadable HTML summary — no VPN, no
> tuxmaker SSH, no credentials required.

---

## What it does

Each morning the IBM Z KVM/Linux CI farm sends a daily mail listing which of
the ~16 test suites failed, with TAP annotation tables like:

```
[ED GK  kN][  6x   6d] tests.test_vfio_pci_nvme.VfioPciNvmeRebootTestCase.runTest
```

CIIQ turns that mail + the optional git delta into a structured root-cause
report:

- **Offline analysis** — entirely browser-side, no server or credentials needed
- **Per-suite verdicts** — each failure row gets an age-based verdict (new
  regression / pre-existing / infra / do-not-revert)
- **Node health** — dead nodes (0/N suites) and all-kernel fault clusters
  detected automatically
- **Fixed test tracking** — tests resolved since last run shown in §5
- **Code regression detection** — failures spanning all kernel flavours in ≤14d
  are flagged as code regressions vs. hardware faults
- **Introducing commit** — identified from the git log (local engine or WatsonX)
- **Minimum fix set** — numbered `git revert` commands with A/B/C fix options
- **HTML export** — self-contained downloadable report, shareable by email

---

## Three editions

| Script | Backend | Port | When to use |
|--------|---------|------|-------------|
| `./run.sh` | `app.py` — local rule engine | 5100 | No credentials, instant |
| `./run-wx.sh` | `app-wx.py` — WatsonX + local fallback | 5100 | IBM Cloud API key available |
| `./run-orch.sh` | `app-orch.py` — multi-turn ReAct agent | 5200 | WatsonX + tool-calling model |

All three share the same `templates/ciiq.html` UI and the same REST API shape.
`app-wx.py` imports `app.py` as its local engine — if WatsonX is unreachable or
credentials are missing, every button falls back automatically to the local
engine.

---

## Quick start

```bash
cd ~/kvm/ciiq

# First time: copy the env template and add credentials (optional)
cp .env.example .env
nano .env          # add CIIQ_WATSONX_API_KEY, CIIQ_WATSONX_PROJECT_ID

# Start (installs deps into .venv on first run)
./run-wx.sh        # WatsonX edition (recommended)
# or
./run.sh           # local-only, no credentials needed

open http://localhost:5100
```

Stop, restart, production mode:

```bash
./run-wx.sh stop   # stop gunicorn daemon
./run-wx.sh prod   # gunicorn, 4 workers, background, logs → ciiq.log
./run-wx.sh        # (re)start dev server
```

---

## Daily triage workflow

```
New CI mail arrives
        │
        ▼
1. Paste mail text into "Import CI Mail" box (sidebar)

   Option A — server available:
     Click "↳ Parse & Load"
     • run_date, run_id, web_url, kernel key auto-fill
     • Suite log textareas populate with raw annotated failure text
     • PASS/FAIL badges update
     • Crash dump table prepopulated

   Option B — offline / no server:
     Click "⚡ Analyse Offline"
     • parseMail() runs entirely in the browser (no fetch)
     • Produces §0–§7 report immediately
     • Also populates suite log textareas and run metadata fields

2. (Optional) Fill Git Delta panel  (or click "Load Example")
   • git log tab   — git log --oneline $GOOD..$BAD -- arch/s390/kvm/
   • diff --stat   — git diff --stat $GOOD..$BAD
   • patch hunks   — git diff $GOOD..$BAD -- arch/s390/kvm/
   • env / pkgs    — rpm -qa | grep -E 's390-tools|qemu|libvirt|kernel'

3. Click "⚙ Local Analysis"  (or "⚡ Analyse All" with WatsonX creds)
   → KVM / QEMU / libvirt tabs fill with structured Markdown reports

4. Click "🔗 Correlate"
   → Cross-project dependency chain, minimum fix set, triage order

5. Click "⬇ Export Report"
   → Downloads ciiq-run-<ID>-root-cause-report.html
      Self-contained, shareable, matches the reference report format
```

### Updating defaults for a new run

```bash
./update_run.sh 1600 2026-08-17
# patches .env, .env.example, and ciiq.html then prints restart instructions
```

---

## Button reference

| Button | Function | Needs server | Needs credentials | Populates Correlate |
|--------|----------|:---:|:---:|:---:|
| **⚡ Analyse Offline** | Parses mail in browser → §0–§7 HTML report | ✗ | ✗ | ✗ |
| **⚙ Local Analysis** | Server-side heuristic engine → 3 project Markdown reports | ✓ | ✗ | ✓ |
| **⚡ Analyse All Projects** | WatsonX (or local fallback) → 3 project Markdown reports | ✓ | Optional | ✓ |
| **🔗 Correlate** | Cross-project root cause, minimum fix set, triage order, reproducer | ✓ | Optional | — |
| **⬇ Export Report** | Generates downloadable self-contained HTML report | ✓ | ✗ | — |

### ⚡ Analyse Offline
Runs entirely in the browser — no server, no network, no credentials. Parses
the pasted CI mail with `parseMail()`, classifies failures with
`classifyFailures()`, then renders `renderReport()` inline. Also populates all
suite log textareas, PASS/FAIL badges, run bar fields, and the kernel key env
tab as a side-effect.

### ⚙ Local Analysis
Always calls `/api/analyse/local` (hardcoded — no credential check). Collects
suite log textareas + PASS/FAIL badges + git delta, sends to the Python
heuristic engine, renders per-project Markdown in the KVM / QEMU / libvirt
tabs. Saves results into `analysisCache` to enable Correlate.

### ⚡ Analyse All Projects
Checks for WatsonX credentials first. With credentials → `/api/analyse/all`
(LLM path). Without → `/api/analyse/local` (same as Local Analysis). On HTTP
429 rate-limit, automatically retries the full batch against the local engine.

### 🔗 Correlate
Requires `analysisCache` to be non-empty (run Local Analysis or Analyse All
first). Sends the three per-project analysis texts + git delta to
`/api/correlate`. Produces a 5-section cross-project report: shared root cause,
dependency cascade (kernel → QEMU → libvirt), minimum revert set (ordered `git
revert` commands), triage order (which suite to run first), and shortest
tuxmaker reproducer.

---

## Off-VPN / offline operation

Tuxmaker SSH (`tuxmaker.boeblingen.de.ibm.com:22`) is only reachable on VPN.
CIIQ degrades gracefully:

| Feature | On VPN | Off VPN / no server |
|---------|--------|---------------------|
| **⚡ Analyse Offline** | Works | Works — browser-only, no fetch |
| **↳ Parse & Load** | Works | Works — calls `/api/ingest` on localhost |
| **Load Run Logs** | Reads from tuxmaker | Returns "SSH failed" — use mail import |
| **Git delta** tabs | Auto-fetches from tuxmaker | Manual paste |
| **⚙ Local Analysis** | Works always | Works always |
| **WatsonX analysis** | Works if IAM reachable | Works (IAM is internet-accessible) |
| **⬇ Export Report** | Works always | Works always |

---

## TAP annotation format

The CI mail uses a compact annotation prefix on each failure line:

```
[ED GK  kN][  6x   6d] tests.test_vfio_pci_nvme.VfioPciNvmeRebootTestCase.runTest
 ^^^^^^^^^    ^^  ^^^
 kernel       |   age (days since first failure)
 flavours     count (how many times today)
```

### Kernel letter codes

| Letter | Kernel flavour |
|--------|---------------|
| `E` | kernel-debug |
| `D` | kernel-devel |
| `F` | kernel-fedora |
| `G` | kernel-git |
| `K` | kernel-kasan |
| `m` | kernel-mm |
| `d` | kernel-mm-debug |
| `k` | kernel-mm-kasan |
| `N` | kernel-next |

### Age-based verdicts

| Age | Verdict | Meaning |
|-----|---------|---------|
| 0d, kernels = all | **⚠ Code regression — all kernels** | Cross-kernel failure cluster; likely hardware/hypervisor fault if on one node, else a code regression |
| 0d | **New today — monitor** | First appearance; watch next run before acting |
| 1–3d | **New regression (≤3d)** | Likely introduced by this delta |
| 4–29d | **Recent — check delta** | May be in scope of the current change |
| 30–89d | **Likely pre-existing** | Verify before reverting |
| ≥ 90d | **Pre-existing — do not revert** | Long-standing flap unrelated to current delta |
| `ci-error:` | **Infrastructure failure** or **Infra — long-standing** | Not a code issue |

---

## ⚡ Offline engine (browser-only)

The offline engine lives entirely inside `templates/ciiq.html` as a
self-contained IIFE. It requires no server, no credentials, and no network
access. Paste the CI mail → click **⚡ Analyse Offline** → report appears.

### Report sections

| § | Title | Content |
|---|-------|---------|
| 0 | Run Summary | Suite table (status/runs/fail/first-failure), kernel key pills |
| 1 | System Dumps | Crash dump cross-reference table |
| 2 | Root Cause — Per Suite | Annotation table per failing suite with age pill + verdict |
| 3 | Node Health & Infrastructure | Dead nodes, all-kernel fault clusters |
| 4 | Failure Classification by Age | Categorised counts: new/regression/pre-existing/infra |
| 5 | Fixed Test Cases Since Last Run | Tests resolved since last run with age |
| 6 | Recommendations | Priority-ordered action list (🔴/🟡/🟢) |
| 7 | Alternate Fixes | For each introducing commit: revert / forward-fix / mitigation |

---

## Local analysis engine (`app.py`)

Pure-Python heuristic engine — no LLM, no network. `analyse_project()` produces
a 6-section Markdown report per project:

1. **Introducing Commit(s)** — git log parse + diff --stat
2. **Root Cause** — top-5 error signatures, representative lines, s390x context
3. **Affected Subsystems** — from log keyword matching
4. **Why this project is affected** — migration / KVM / ABI reasoning
5. **Recommended Fix** — `git revert <sha>` with commit subject
6. **Verification Command** — `run-suite.sh <suite> HEAD` on tuxmaker

### Error patterns (26 total)

**Kernel crashes:** `BUG:` · `Kernel panic` · `Oops` · `GPF` · `segfault` ·
`NULL pointer dereference` · `use-after-free` · `stack overflow` · `deadlock` ·
`WARN_ON` / `WARNING:`

**Test / process errors:** `TIMEOUT` / `timeout` · `FAIL` / `FAILED` · `ERROR:` · `Aborted` ·
`AssertionError` · `No such device` · `Permission denied` · `Invalid argument` ·
`OOM` · `migration failed`

**CI TAP infrastructure:** `ci-error: test suite script failure` · `ci-error: invalid tap` ·
`ci-error: ssh connection error` · `ci-error: test suite timeout` ·
`ci-error: install test suite packages` · `timeout; duration=<N>`

### Subsystems (10)

`KVM core` · `s390x arch` · `memory mgmt` · `VFIO` · `virtio` ·
`live migration` · `CPU model` · `QMP/monitor` · `libvirt driver` · `QEMU block`

---

## 🔗 Correlate engine

After per-project analysis populates `analysisCache`, Correlate produces a
5-section cross-project report:

| § | Title | Content |
|---|-------|---------|
| 1 | Cross-Project Correlation | Common commits across all three projects as shared suspects |
| 2 | Dependency Chain | s390x stack cascade: kernel ABI → QEMU KVM_SET/GET_ONE_REG → libvirt QMP |
| 3 | Minimum Fix Set | Numbered `git revert` commands in reverse-chronological order (up to 3) |
| 4 | Triage Order | KVM selftests → QEMU s390x-kvm → libvirt-s390x (fastest to slowest to confirm) |
| 5 | Reproducer | Shortest tuxmaker command sequence to reproduce without full CI |

---

## Python backend functions (`app.py`)

### Bootstrap / config

| Function | Signature | Purpose |
|----------|-----------|---------|
| `_expand_env` | `(value: str) → str` | Replace `${VAR}` patterns with env variable values |
| `load_config` | `() → dict` | Load and env-expand `config.yaml` |
| `err` | `(msg: str, code: int = 400) → Response` | Return a JSON error response |
| `require_json` | decorator | Assert `Content-Type: application/json` before handler runs |

### Analysis engine

| Function | Signature | Purpose |
|----------|-----------|---------|
| `_strip_tap_annotations` | `(text: str) → str` | Remove `[ABCD][Nx Nd]` prefixes from log lines before pattern matching |
| `_scan_log` | `(text: str) → dict` | Scan a log snippet; return `{hits, signatures, top_errors, raw_lines}` |
| `_extract_commits` | `(git_log: str) → list[dict]` | Parse `git log --oneline` into `[{sha, subject}]` |
| `analyse_project` | `(project, delta, suite_logs, run_date, run_id, suite_status=None) → str` | Run the 6-section local heuristic analysis for one project. Returns Markdown. |
| `correlate_projects` | `(delta, analyses, run_date, run_id) → str` | Merge per-project analyses into cross-project dependency chain, minimum fix set, and triage order. Returns Markdown. |
| `_add_history` | `(project, status, summary) → None` | Append an analysis result to the Flask session history list |

### CI mail parser

| Function | Signature | Purpose |
|----------|-----------|---------|
| `_parse_ci_mail` | `(text: str) → dict` | Parse a full CI daily mail. Returns `{run_date, run_id, web_url, log_path, kernel_key, suite_logs, suite_status, dumps}`. Stores raw TAP-annotated body in `suite_logs` so the JS engine can render age verdicts. |

Compiled regexes used by `_parse_ci_mail`:

| Constant | Pattern | Matches |
|----------|---------|---------|
| `_INGEST_DATE_RE` | `Daily run:\s*(\d{4}-\d{2}-\d{2})` | Run date header |
| `_INGEST_WEBUI_RE` | `Web UI:\s*(https?://\S+)` | Web UI URL |
| `_INGEST_RUNID_RE` | `/ci-run/(\d+)` | Run ID from URL |
| `_INGEST_LOGPATH_RE` | `Full log:\s*(\S+)` | Log directory path |
| `_INGEST_KERNEL_RE` | `^([A-Za-z]):\s+kernel-(\S+)\s+\(([^)]+)\)` | Kernel key legend entries |
| `_INGEST_SECTION_RE` | `^Test failures for test suite '([^']+)'…` | Per-suite failure sections |

### Flask endpoints

| Method | Route | Purpose |
|--------|-------|---------|
| `GET` | `/` | Serve `ciiq.html` via Jinja2 (injects run_date, run_id, web_url from config) |
| `GET` | `/api/config` | Return sanitised config (suites, model, run defaults — no secrets) |
| `POST` | `/api/analyse/<project>` | Analyse one project (`kvm`/`qemu`/`libvirt`) |
| `POST` | `/api/analyse/all` | Analyse all three projects in parallel |
| `POST` | `/api/analyse/local` | Alias for `all` — used by the "⚙ Local Analysis" button |
| `POST` | `/api/correlate` | Cross-project correlation and minimum fix set |
| `GET` | `/api/runs` | List available CI run dates from the tuxmaker log directory |
| `GET` | `/api/run/<date>/suites` | Return suite names and log snippets for a specific run date |
| `GET` | `/api/delta/<date>` | Return cached or live-fetched git delta for a run date |
| `POST` | `/api/ingest` | Parse a raw CI mail → structured JSON for the UI |
| `POST` | `/api/report` | Generate and return the downloadable HTML report |
| `GET` | `/api/history` | Return session analysis history |
| `DELETE` | `/api/history` | Clear session analysis history |

### SSH helpers (tuxmaker)

| Function | Signature | Purpose |
|----------|-----------|---------|
| `_ssh_run` | `(cmd: str, timeout: int = 30) → str` | Run a command on tuxmaker via SSH; returns stdout or raises on failure |
| `_ssh_list_runs` | `() → list[dict]` | List available run dates from the CI log directory on tuxmaker |

---

## JavaScript functions (`templates/ciiq.html`)

### UI helpers

| Function | Purpose |
|----------|---------|
| `wxConfig()` | Build the WatsonX credential object from sidebar fields or `window.serverCreds` |
| `runInfo()` | Collect run metadata (date, id, url) from the run bar fields |
| `delta()` | Collect git delta tabs (sha_good, sha_bad, git_log, diff_stat, patch, env) |
| `collectLogs(proj)` | Collect suite log textarea values for one project into `{suite: text}` |
| `collectSuiteStatus()` | Read all PASS/FAIL badges from the suite table into `{suite: "PASS"\|"FAIL"}` |
| `setBody(id, html, cls)` | Set inner HTML + CSS class of an analysis result panel |
| `setCorr(html, cls)` | Set the Correlate panel HTML + CSS class |
| `showTok(pre, model, inT, outT)` | Show token-count badge (model, input tokens, output tokens) |
| `spin(label)` | Return an animated spinner HTML string |
| `setConnDot(state)` | Update the WatsonX connection indicator dot (`ok`/`err`/`''`) |
| `setStatus(id, type, msg)` | Set status bar text with `ok`/`err`/`info` styling |
| `h(s)` | HTML-escape a string (client-side) |
| `fmt(raw)` | Convert Markdown to HTML (headers, bold, code, lists, horizontal rules) |
| `syncRunBar()` | Keep run-date, run-id, and run-url fields mutually consistent |

### Analysis flow

| Function | Purpose |
|----------|---------|
| `analyseAll()` | Check credentials → POST to `/api/analyse/all` or `/api/analyse/local`; 429 auto-fallback |
| `analyseLocal()` | Always POST to `/api/analyse/local`; guards empty logs |
| `correlate()` | POST `analysisCache` to `/api/correlate`; 429 auto-fallback to `/api/correlate/local` |
| `exportReport()` | Collect all fields and POST to `/api/report`; trigger browser download |
| `analyseOffline()` | Browser-only: call `parseMail` → `classifyFailures` → `renderReport`; populate UI |

### ⚡ Offline engine (IIFE)

| Function | Purpose |
|----------|---------|
| `parseMail(raw)` | Parse complete CI daily mail → `ParsedMail` object |
| `classifyFailures(parsed)` | Classify all annotated failure lines into 5 buckets |
| `renderReport(parsed, mailText)` | Render full §0–§7 HTML report as string |
| `analyseOffline()` | Orchestrates: parse → classify → render → populate UI |
| `offlinePrintReport()` | Open new window with report + print CSS; trigger print dialog |

**ParsedMail schema:**

```js
{
  run_date:       string,          // "2026-08-16"
  run_id:         string,          // "1599"
  web_url:        string,          // "https://…/ci-run/1599"
  log_path:       string,          // "/home/ciuser/logs/daily/20260816/"
  kernel_key:     { letter: { name, build } },
  suite_status:   { suite: "FAIL"|"PASS" },
  suite_failures: { suite: string },  // raw annotated failure body
  combined_stats: { suite: { runs, tests, pass, fail } },
  dumps:          [{ nr, suite, kernel, model, type, system, dump, reason }],
  fixed:          [{ nr, suite, test, runs, skip, pass, fixed, last }],
  systems:        [{ system, cpus, memory, model, type, runtime, suites, dumps }]
}
```

**`classifyFailures` buckets:**

| Bucket | Rule |
|--------|------|
| `code_regressions` | All kernel flavours present + age ≤ 14d |
| `node_faults` | Suite has ≥ 6 all-kernel failures on same node |
| `infra_issues` | Line contains `ci-error:` |
| `new_today` | `age === 0` |
| `pre_existing` | `age ≥ 90` |

---

## WatsonX setup

1. Get an IBM Cloud API key:  
   `cloud.ibm.com` → Manage → Access → API keys → Create

2. Get a WatsonX project ID:  
   `watsonx.ai` → Projects → your project → Manage → General → Project ID

3. Add to `.env`:
   ```
   CIIQ_WATSONX_API_KEY=your_key_here
   CIIQ_WATSONX_PROJECT_ID=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
   CIIQ_WATSONX_REGION=eu-de
   CIIQ_SECRET_KEY=any-random-string
   ```

4. Start with `./run-wx.sh` — the connection dot turns green when the IAM
   token exchange succeeds.

### Confirmed models (2026-08)

| Model ID | Notes |
|----------|-------|
| `meta-llama/llama-3-3-70b-instruct` ✓ | Default — confirmed us-south + eu-de |
| `meta-llama/llama-4-maverick-17b-128e-instruct-fp8` ✓ | Faster, smaller context |
| `mistralai/mistral-small-3-1-24b-instruct-2503` ✓ | Good throughput |
| `ibm/granite-8b-code-instruct` ✓ | Code-focused |

> **Note:** `ibm/granite-3-8b-instruct` and `ibm/granite-3-2b-instruct` return
> HTTP 404 — they have been removed from the API.

---

## REST API reference

All endpoints accept `Content-Type: application/json` and return JSON
(except `/api/report` which returns `text/html`).

### `POST /api/ingest`

```json
{ "mail_text": "Daily run: 2026-08-16\nWeb UI: https://…/ci-run/1599\n…" }
```

Returns:
```json
{
  "ok": true,
  "run_date": "2026-08-16",
  "run_id": "1599",
  "web_url": "https://…/ci-run/1599",
  "kernel_key": { "E": {"name":"debug","build":"7.2.0-…+debug"}, … },
  "suite_logs": { "hades": "[N][1x 16d] tests.test_se…", … },
  "suite_status": { "hades": "FAIL", "s390-tools": "PASS", … },
  "dumps": [{"suite":"ci-reipl","kernel":"mm","system":"b46lp60kvm01",…}]
}
```

### `POST /api/analyse/local`

```json
{
  "run_date": "2026-08-16",
  "run_id":   "1599",
  "delta": {
    "sha_good": "a1b2c3d4", "sha_bad": "f7e8d9c0",
    "git_log":  "f7e8d9c kvm/s390: add intercept for 0xb9af\n…",
    "git_diff_stat": "arch/s390/kvm/intercept.c | 47 ++++++--\n…",
    "git_patch":     "diff --git a/arch/s390/kvm/intercept.c\n…",
    "env_versions":  "s390-tools-2.34.0\n…"
  },
  "suite_logs": { "hades": "…", "kvm-unit-tests-kvm": "…" },
  "suite_status": { "hades-monolithic": "PASS", "s390-tools": "PASS" }
}
```

Returns:
```json
{
  "ok": true,
  "results": {
    "kvm": { "analysis": "## Run 2026-08-16 …", "engine": "local" }
  },
  "errors": {},
  "engine": "local"
}
```

### `POST /api/correlate`

```json
{
  "run_date": "2026-08-16",
  "run_id":   "1599",
  "delta":    { "git_log": "f7e8d9c kvm/s390: …" },
  "analyses": { "kvm": "…", "qemu": "…", "libvirt": "…" }
}
```

### `POST /api/report`

Same body shape as `/api/analyse/local`. Returns `text/html` with
`Content-Disposition: attachment; filename="ciiq-run-1599-root-cause-report.html"`.

---

## HTML report export (`/api/report`)

`POST /api/report` generates a fully self-contained HTML file:

| # | Title |
|---|-------|
| 0 | Run summary table + kernel build legend |
| 1 | System crashes & dump table |
| 2 | Introducing commits (dark callout block with SHA range) |
| 3 | Root cause per failing suite (annotation table with verdict column) |
| 4 | Affected subsystems |
| 5 | Minimum fix set (numbered `git revert` commands + combined block) |
| 6 | Triage order |
| 7 | Reproducer — shortest tuxmaker command sequence |

The file is named `ciiq-run-<ID>-root-cause-report.html` and downloads
immediately. No server needed to view it — share by email.

---

## Configuration files

| File | Purpose |
|------|---------|
| `config.yaml` | Suites, log paths, server port — local edition |
| `config-wx.yaml` | Same + `watsonx:` block with model, region, max_tokens |
| `config-orch.yaml` | Orchestrate edition — agent_model, max_agent_turns |
| `.env` | Credentials — gitignored, never committed |
| `.env.example` | Template — copy to `.env` and fill in |

---

## File structure

```
ciiq/
├── app.py                 Local heuristic engine — all endpoints
├── app-wx.py              WatsonX edition — imports app.py as local engine
├── app-orch.py            Orchestrate/ReAct edition — tool-calling agent loop
├── config.yaml            Suite list, log paths, server port
├── config-wx.yaml         WatsonX model, region, credentials references
├── config-orch.yaml       Orchestrate edition config (port 5200)
├── requirements.txt       flask, flask-cors, requests, pyyaml, python-dotenv,
│                          gunicorn, ibm-watsonx-ai
├── run.sh                 Setup + start/stop for local edition
├── run-wx.sh              Setup + start/stop for WatsonX edition
├── run-orch.sh            Setup + start/stop for Orchestrate edition
├── update_run.sh          Patch defaults to a new run ID/date
├── extract_delta.sh       SSH to tuxmaker → fetch git delta → JSON cache
├── prefetch_delta.py      Python helper called by run scripts at startup
├── delta_cache/           Cached git deltas (JSON, one file per run date)
├── .env.example           Credentials template
├── CHANGELOG.md
├── CONTRIBUTING.md
└── templates/
    └── ciiq.html          Single-page web UI + offline engine (~2240 lines)
```

---

## Troubleshooting

**`Address already in use` on port 5100**
```bash
lsof -ti:5100 | xargs kill -9 && ./run-wx.sh
```

**WatsonX HTTP 404 — model not found**  
Select a confirmed ✓ model from the dropdown (e.g. `llama-3-3-70b-instruct`)
or set `CIIQ_WATSONX_MODEL` in `.env`.

**WatsonX HTTP 401 — IAM token error**  
API key expired. Regenerate at `cloud.ibm.com` → Manage → Access → API keys.

**"Correlate" shows error / does nothing**  
Run at least one per-project analysis first — Correlate requires `analysisCache`
to be non-empty.

**"0 suites passed" when some suites show PASS**  
Use **⚙ Local Analysis** (not the individual Analyse KVM/QEMU/libvirt buttons)
so the `suite_status` badge state is sent with the request.

**`⚡ Analyse Offline` button does nothing / all buttons dead**  
A JS syntax error in `ciiq.html` prevents the event listener block from running.
Check the browser console. Run `node --check` on the extracted script block:
```bash
node --check /tmp/ciiq_check.js  # extracted from templates/ciiq.html
```

**`hades-withHW` missing from §0 Run Summary**  
The combined stats regex requires `[a-zA-Z0-9._-]+` — verify it hasn't been
accidentally reverted to `[a-z0-9._-]+` in `parseMail` (ciiq.html line ~1551).

**Missing Python module on startup**
```bash
./run-wx.sh setup    # re-runs pip install into .venv
```

**Off VPN — "Suite logs loaded. Git delta: SSH failed"**  
Expected. Paste `git log`, `git diff --stat`, and `rpm -qa` output manually.
The analysis is identical with pasted content.

---

*CIIQ — IBM KVM CI Intelligence & Insight Query*  
*Made with IBM Bob*
