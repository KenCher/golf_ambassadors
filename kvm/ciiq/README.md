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

CIIQ strips these prefixes before log scanning (so error patterns fire
correctly) and re-parses them in the HTML report renderer to produce
per-row age-based verdicts:

### Age-based verdicts

| Age | Verdict | Meaning |
|-----|---------|---------|
| 0d, kernels = all | **⚠ Code regression — all kernels** | Cross-kernel failure cluster; likely hardware/hypervisor fault if on one node, else a code regression |
| 0d | **New today — monitor** | First appearance; watch next run before acting |
| 1–3d | **New regression (≤3d)** | Likely introduced by this delta |
| 4–29d | **Recent — check delta** | May be in scope of the current change |
| 30–89d | **Likely pre-existing** | Verify before reverting |
| ≥ 90d | **Pre-existing — do not revert** | Long-standing flap unrelated to current delta |
| "ci-error:" | **Infrastructure failure** or **Infra — long-standing** | Not a code issue |

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
| `analyse_project` | `(project, delta, suite_logs, run_date, run_id, suite_status=None) → str` | Run the 6-section local heuristic analysis for one project (kvm/qemu/libvirt). Returns Markdown. |
| `correlate_projects` | `(delta, analyses, run_date, run_id) → str` | Merge per-project analyses into a cross-project dependency chain, minimum fix set, and triage order. Returns Markdown. |
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
| `_INGEST_SECTION_RE` | `^Test failures for test suite '([^']+)'…` | Per-suite failure sections (multiline, preserves annotations) |

### HTML report renderer

| Function | Signature | Purpose |
|----------|-----------|---------|
| `_h` | `(s: str) → str` | HTML-escape a string |
| `_code` | `(s: str) → str` | Wrap string in `<code>` |
| `_pre` | `(s: str) → str` | Wrap string in `<pre>` |
| `_section` | `(num: int, title: str) → str` | Render a numbered section heading |
| `_parse_annotation` | `(line: str) → tuple[str, int, int, str]` | Parse a TAP annotation line into `(kernels, count, age_days, text)` |
| `_ann_html` | `(kernels, count, age) → str` | Render an annotation row as an HTML `<tr>` with verdict pill |
| `_render_html_report` | `(parsed, delta, analyses, run_date, run_id, suite_logs=None, suite_status=None) → str` | Render the full self-contained HTML report (7 sections, inline CSS, no external assets) |

### Flask endpoints

| Method | Route | Handler | Purpose |
|--------|-------|---------|---------|
| `GET` | `/` | `index` | Serve `ciiq.html` via Jinja2 (injects run_date, run_id, web_url from config) |
| `GET` | `/api/config` | `api_config` | Return sanitised config (suites, model, run defaults — no secrets) |
| `POST` | `/api/analyse/<project>` | `api_analyse_project` | Analyse one project (`kvm`/`qemu`/`libvirt`) |
| `POST` | `/api/analyse/all` | `api_analyse_all` | Analyse all three projects in parallel |
| `POST` | `/api/analyse/local` | `api_analyse_local` | Alias for `all` — used by the "⚙ Local Analysis" button |
| `POST` | `/api/correlate` | `api_correlate` | Cross-project correlation and minimum fix set |
| `GET` | `/api/runs` | `api_runs` | List available CI run dates from the tuxmaker log directory |
| `GET` | `/api/run/<date>/suites` | `api_run_suites` | Return suite names and log snippets for a specific run date |
| `GET` | `/api/delta/<date>` | `api_delta` | Return cached or live-fetched git delta for a run date |
| `POST` | `/api/ingest` | `api_ingest` | Parse a raw CI mail → structured JSON for the UI |
| `POST` | `/api/report` | `api_report` | Generate and return the downloadable HTML report |
| `GET` | `/api/history` | `api_history` | Return session analysis history |
| `DELETE` | `/api/history` | `api_clear_history` | Clear session analysis history |

### SSH helpers (tuxmaker)

| Function | Signature | Purpose |
|----------|-----------|---------|
| `_ssh_run` | `(cmd: str, timeout: int = 30) → str` | Run a command on tuxmaker via SSH; returns stdout or raises on failure |
| `_ssh_list_runs` | `() → list[dict]` | List available run dates from the CI log directory on tuxmaker |

---

## JavaScript functions (`templates/ciiq.html`)

All JS lives in a single inline `<script>` block. The offline engine runs
inside an IIFE that exposes nothing to the global scope intentionally; it
accesses the DOM through closures.

### UI helpers

| Function | Signature | Purpose |
|----------|-----------|---------|
| `wxConfig` | `() → dict` | Build the WatsonX credential object from sidebar fields or `window.serverCreds` |
| `runInfo` | `() → dict` | Collect run metadata (date, id, url) from the run bar fields |
| `delta` | `() → dict` | Collect git delta tabs (sha_good, sha_bad, git_log, diff_stat, patch, env) |
| `collectLogs` | `(proj: string) → dict` | Collect suite log textarea values for one project into `{suite: text}` |
| `collectSuiteStatus` | `() → dict` | Read all PASS/FAIL badges from the suite table into `{suite: "PASS"|"FAIL"}` |
| `setBody` | `(id, html, cls) → void` | Set inner HTML + CSS class of an analysis result panel |
| `setCorr` | `(html, cls) → void` | Set the Correlate panel HTML + CSS class |
| `showTok` | `(pre, model, inT, outT) → void` | Show token-count badge (model, input tokens, output tokens) |
| `spin` | `(label) → string` | Return an animated spinner HTML string |
| `setConnDot` | `(state) → void` | Update the WatsonX connection indicator dot (`ok`/`err`/`''`) |
| `setStatus` | `(id, type, msg) → void` | Set status bar text with `ok`/`err`/`info` styling |
| `h` | `(s) → string` | HTML-escape a string (client-side) |
| `fmt` | `(raw) → string` | Convert Markdown to HTML (headers, bold, code, lists, horizontal rules) |
| `syncRunBar` | `() → void` | Keep run-date, run-id, and run-url fields mutually consistent; update the run topbar |

### API calls

| Function | Signature | Purpose |
|----------|-----------|---------|
| `apiPost` | `(path, body) → Promise` | `fetch` wrapper: POST JSON, parse response, throw on `!r.ok` |
| `testConnection` | `() → void` | Test WatsonX credentials by calling `/api/config` |

### Analysis flow

| Function | Signature | Purpose |
|----------|-----------|---------|
| `analyse` | `(proj: string) → void` | Run analysis for one project; shows spinner, posts to `/api/analyse/<proj>`, renders result |
| `analyseAll` | `() → void` | Run WatsonX analysis for all three projects sequentially |
| `analyseLocal` | `() → void` | Run the local heuristic engine (`/api/analyse/local`) for all projects; no WatsonX required |
| `correlate` | `() → void` | Post cached per-project analyses to `/api/correlate`; render the cross-project report |
| `_showCorrResult` | `(r, modelLabel) → void` | Render a correlation result into the Correlate panel |
| `loadRunLogs` | `() → void` | Fetch suite logs for the current run date from tuxmaker via `/api/run/<date>/suites` |
| `exportReport` | `() → void` | Collect all fields and POST to `/api/report`; trigger browser download of the HTML report |

### Session / history

| Function | Signature | Purpose |
|----------|-----------|---------|
| `refreshHistory` | `() → void` | Fetch and render the session analysis history from `/api/history` |
| `loadExample` | `() → void` | Seed all input fields with run-1592 example data (git log, diff stat, suite logs) |

### CI mail import

| Function | Signature | Purpose |
|----------|-----------|---------|
| `ingestMail` | `() → void` | POST the pasted mail text to `/api/ingest`; populate run metadata, suite log textareas, PASS/FAIL badges, kernel key env tab, and fail counter from the response |

### ⚡ Offline engine (IIFE — `ciiq.html` lines 1486–2237)

These functions run entirely in the browser with no server calls.

#### Parser

| Function | Signature | Purpose |
|----------|-----------|---------|
| `esc` | `(s) → string` | HTML-escape for safe insertion into rendered report |
| `code` | `(s) → string` | Wrap in `<code>…</code>` |
| `age_pill` | `(d: number) → string` | Render an age badge: `0d NEW` (red), `6d` (amber), `96d` (grey) |
| `verdict` | `(age, kernelStr, text) → string` | Return coloured verdict HTML for a failure row based on age and kernel spread |
| `parseAnn` | `(line: string) → object\|null` | Parse one TAP annotation line `[EDGK][Nx Nd] test.name` → `{kernels, count, age, text}` or `null` |
| `parseMail` | `(raw: string) → ParsedMail` | Parse a complete CI daily mail into a structured object — see **ParsedMail schema** below |

**ParsedMail schema** (returned by `parseMail`):

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

`parseMail` parsing steps:

1. **Metadata** — `Daily run:`, `Web UI:`, `Full log:` headers
2. **Kernel key** — `E: kernel-debug (…)` legend lines
3. **Combined table** — `SUITE RUNS TESTS PASS FAIL …` rows → `suite_status` + `combined_stats`  
   *Note: suite names may contain uppercase (e.g. `hades-withHW`) — regex uses `[a-zA-Z0-9._-]`*
4. **Suite failure sections** — `Test failures for test suite 'X'` blocks with raw annotated lines
5. **Dumps** — `Dumps of unresponsive systems` table
6. **Fixed tests** — `Fixed test cases` table; continuation lines (test names that wrap across two rows) are spliced back into the test-name column before the RUNS token, not appended at the end of the row
7. **Test systems** — `Test systems` table with multi-word runtime (`3h 24m 50s`) and dead-node runtime (`-`)

#### Rule engine

| Function | Signature | Purpose |
|----------|-----------|---------|
| `classifyFailures` | `(parsed: ParsedMail) → Classification` | Classify all annotated failure lines into five buckets |

**Classification schema**:

```js
{
  code_regressions: [{ suite, text, age, kernels, count }],  // all-kernel, ≤14d
  node_faults:      [{ suite, count }],                       // all-kernel clusters
  infra_issues:     [{ suite, text, age }],                   // ci-error:* lines
  new_today:        [{ suite, text, count }],                 // age === 0
  pre_existing:     [{ suite, text, age }]                    // age ≥ 90
}
```

Rules applied by `classifyFailures`:

- A failure spanning **all kernel flavours** present in the mail in **≤14d** → `code_regressions`
- A suite with ≥6 all-kernel failures → `node_faults` (hardware/hypervisor suspect)
- Lines matching `ci-error:` → `infra_issues`
- `age === 0` → `new_today`
- `age >= 90` → `pre_existing`

#### Renderer

| Function | Signature | Purpose |
|----------|-----------|---------|
| `renderReport` | `(parsed: ParsedMail, mailText: string) → string` | Render the full §0–§7 offline HTML report as a string; returned HTML is set as `offline-out` innerHTML |

`renderReport` section breakdown:

| Call | Section | Data source |
|------|---------|-------------|
| `section(0, 'Run Summary')` | Suite table (suite/status/runs/fail/first-failure-line) + kernel key pills | `parsed.combined_stats`, `parsed.suite_failures`, `parsed.kernel_key` |
| `section(1, 'System Dumps')` | Crash dump table | `parsed.dumps` |
| `section(2, 'Root Cause — Per Suite')` | Per-suite annotation tables with `age_pill` + `verdict` | `parsed.suite_failures` |
| `section(3, 'Node Health & Infrastructure')` | Dead nodes (0/N suites), all-kernel clusters | `parsed.systems`, `cf.node_faults` |
| `section(4, 'Failure Classification by Age')` | Category table with full test names (no truncation) | `cf.*` |
| `section(5, 'Fixed Test Cases Since Last Run')` | Resolved-test cards with suite badge + last-failure date | `parsed.fixed` |
| `section(6, 'Recommendations')` | Priority-ordered 🔴/🟡/🟢 action list | `dead`, `cf.*` |
| `section(7, 'Alternate Fixes')` | Per introducing-commit: A revert / B forward-fix / C mitigation | `delta().git_log` |

#### Controls

| Function | Signature | Purpose |
|----------|-----------|---------|
| `analyseOffline` | `() → void` | Orchestrates the offline flow: call `parseMail`, populate UI fields (run bar, suite textareas, badges, kernel key env tab, fail counter), render report, update status bar |
| `offlinePrintReport` | `() → void` | Open a new window with the rendered report + print-specific CSS, trigger browser print dialog (Save as PDF) |
| `offlineToggleMinimise` | `(btn: HTMLElement) → void` | Toggle the report body between collapsed (topbar only) and expanded; updates button label `−`/`+` |

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

## Local analysis engine (`app.py`)

Pure-Python heuristic engine — no LLM, no network. `analyse_project()` produces
a 6-section Markdown report:

1. **Introducing Commit(s)** — git log parse + diff --stat
2. **Root Cause** — top-5 error signatures, representative lines, s390x context
3. **Affected Subsystems** — from log keyword matching
4. **Why this project is affected** — migration / KVM / ABI reasoning
5. **Recommended Fix** — `git revert <sha>` with commit subject
6. **Verification Command** — `run-suite.sh <suite> HEAD` on tuxmaker

### Error patterns (26 total)

Kernel: `BUG:` · `Kernel panic` · `Oops` · `GPF` · `segfault` ·
`NULL pointer dereference` · `use-after-free` · `stack overflow` · `deadlock` ·
`WARN_ON`/`WARNING:`

Test/infra: `TIMEOUT`/`timeout` · `FAIL`/`FAILED` · `ERROR:` · `Aborted` ·
`AssertionError` · `No such device` · `Permission denied` · `Invalid argument` ·
`OOM` · `migration failed`

CI TAP: `ci-error: test suite script failure` · `ci-error: invalid tap` ·
`ci-error: ssh connection error` · `ci-error: test suite timeout` ·
`ci-error: install test suite packages` · `timeout; duration=<N>`

### Subsystems (10)

`KVM core` · `s390x arch` · `memory mgmt` · `VFIO` · `virtio` ·
`live migration` · `CPU model` · `QMP/monitor` · `libvirt driver` · `QEMU block`

---

## HTML report export (`/api/report`)

`POST /api/report` generates a fully self-contained HTML file. Sections:

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
immediately. No server needed to view it — share by email or drop into
`.bob/artifacts/`.

---

## REST API reference

All endpoints accept `Content-Type: application/json` and return JSON
(except `/api/report` which returns `text/html`).

### `POST /api/ingest`

Parse a raw CI daily mail and return structured data to populate the UI.

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
  "log_path": "/home/ciuser/logs/daily/20260816/",
  "kernel_key": { "E": {"name":"debug","build":"7.2.0-…+debug"}, … },
  "suite_logs": {
    "hades": "[        N][  1x  16d] tests.test_se.BasicAPTestCase.runTest\n…",
    "hades-withHW": "[ED GK  kN][  6x   6d] tests.test_vfio_pci_nvme…\n…"
  },
  "suite_status": { "hades": "FAIL", "s390-tools": "PASS", … },
  "dumps": [{"suite":"ci-reipl","kernel":"mm","system":"b46lp60kvm01","dump_id":"D52247",…}]
}
```

`suite_logs` values retain the raw `[ABCD][Nx Nd]` annotation prefixes —
the browser offline engine and the `_render_html_report` renderer both consume
them directly.

### `POST /api/analyse/local`  ·  `POST /api/analyse/all`

```json
{
  "run_date": "2026-08-16",
  "run_id":   "1599",
  "delta": {
    "sha_good":      "a1b2c3d4",
    "sha_bad":       "f7e8d9c0",
    "git_log":       "f7e8d9c kvm/s390: add intercept for 0xb9af\n…",
    "git_diff_stat": "arch/s390/kvm/intercept.c | 47 ++++++--\n…",
    "git_patch":     "diff --git a/arch/s390/kvm/intercept.c\n+…",
    "env_versions":  "# TODAY run #1599\ns390-tools-2.34.0\n…"
  },
  "suite_logs": {
    "kvm-unit-tests-kvm": "[E   K  kN][  9x  96d] firq-linear: timeout; duration=30",
    "hades-withHW":       "[ED GK  kN][  6x   6d] tests.test_vfio_pci_nvme…"
  },
  "suite_status": {
    "hades-monolithic": "PASS",
    "s390-tools":       "PASS",
    "kvm-unit-tests-tcg": "PASS"
  }
}
```

Response:
```json
{
  "ok": true,
  "results": {
    "kvm": { "analysis": "## Run 2026-08-16  1599 — KVM Analysis\n…", "engine": "local" }
  },
  "errors": {},
  "engine": "local"
}
```

`suite_logs` can be flat (`{suite: text}`) or nested (`{project: {suite: text}}`).
Flat is auto-split by matching suite names against `config.yaml`.

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

## Test suite

```bash
cd ~/kvm/ciiq              # or from the playground:
node ciiq_test_runner.js   # 29 assertions against the real run-1599 CI mail
```

The test runner (`ciiq_test_runner.js` in the playground workspace) uses
`vm.runInContext` to load the browser JS without a DOM and runs `parseMail`
against the full run-1599 mail. It asserts:

- All metadata fields (run_date, run_id, log_path, 9 kernel letters)
- 6 FAIL + 3 PASS suite status
- Annotated line counts per suite (1/4/2/35/2/5)
- All 3 crash dumps with correct suite/system/dump_id
- All 5 fixed test names (including 4 two-line-wrapped entries)
- 46 test systems, 3 dead nodes, `b46lp63` suites/model
- 9 combined stats entries including `hades-withHW` (uppercase in suite name)

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
Check the browser console. Run `node --check` on the extracted script block to
find the error:
```bash
node --check /tmp/ciiq_check.js  # extracted from templates/ciiq.html
```

**`hades-withHW` missing from §0 Run Summary**  
The combined stats regex requires lowercase-start suite names but `hades-withHW`
contains uppercase `HW`. The regex is `[a-zA-Z0-9._-]+` — verify it hasn't
been accidentally reverted to `[a-z0-9._-]+` in `parseMail` (ciiq.html line ~1551).

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
