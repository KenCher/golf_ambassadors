# CIIQ — CI Intelligence & Insight Query

> WatsonX-powered root-cause analysis for KVM, QEMU, and libvirt CI failures on IBM Z (s390x).

CIIQ identifies the **exact introducing commit** behind each CI failure by combining the real git delta (what changed between the last passing and failing run) with IBM Granite AI analysis — returning a commit hash, file path, and concrete fix command rather than a pattern-matched guess.

---

## Architecture

```
Browser UI (ciiq.html)
        │  REST/JSON over HTTP
        ▼
Flask backend (app.py)  ←── .env / config.yaml (credentials, region, model)
        │
        ├── GET  /                     Serve web UI
        ├── GET  /api/config           Return sanitised config (no secrets)
        ├── POST /api/token            Exchange API key → IAM Bearer token
        ├── POST /api/analyse/kvm      Analyse KVM suites only
        ├── POST /api/analyse/qemu     Analyse QEMU suites only
        ├── POST /api/analyse/libvirt  Analyse libvirt suites only
        ├── POST /api/analyse/all      Analyse all three projects sequentially
        ├── POST /api/correlate        Cross-project dependency + minimum fix set
        ├── GET  /api/runs             List CI run dates from log directory
        ├── GET  /api/run/<date>/suites  Auto-populate suite log snippets
        ├── GET  /api/history          Session history
        └── DELETE /api/history        Clear history
                │
                ▼
        WatsonX.ai (us-south.ml.cloud.ibm.com)
        Model: ibm/granite-3-8b-instruct
        Project: CIIQ (62f9a86d) + Machine Learning-in WML instance
```

---

## Quick Start

```bash
cd /Users/kencheru/kvm/ciiq/

# First time only — install deps
./run.sh setup

# Start the server (auto-kills any stale process on :5100)
./run.sh

# Open in browser
open http://localhost:5100
```

### Stop / restart

```bash
# Stop
lsof -ti:5100 | xargs kill -9

# Restart (run.sh auto-clears the port)
./run.sh
```

### Production (shared team server)

```bash
./run.sh prod      # gunicorn, 4 workers, runs in background, logs to ciiq.log
./run.sh stop      # graceful shutdown
tail -f ciiq.log   # live log stream
```

---

## Credentials

Credentials live in `.env` — **never commit this file**.

```bash
cp .env.example .env
# Edit .env and fill in:
CIIQ_WATSONX_API_KEY=<your IBM Cloud API key>
CIIQ_WATSONX_PROJECT_ID=62f9a86d-cf41-425d-9c66-5b5801b3054e
CIIQ_SECRET_KEY=<any random string for Flask sessions>
```

When `.env` has valid credentials the browser UI shows a green dot automatically — no need to enter keys in the sidebar. The sidebar fields are for per-user overrides only.

### WatsonX project requirements

The project must have a **Watson Machine Learning (WML) service instance** associated.
The CIIQ project (`62f9a86d`) is already configured with `Machine Learning-in` (`826236c5`, us-south).

If you create a new project, associate WML via:
```bash
# Patch the project using the IBM Cloud platform API
curl -X PATCH https://api.dataplatform.cloud.ibm.com/v2/projects/<PROJECT_ID> \
  -H "Authorization: Bearer $IAM_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"compute":[{"name":"Machine Learning-in","type":"machine_learning",
       "guid":"826236c5-358a-4c26-9194-b93999aec27e",
       "crn":"crn:v1:bluemix:public:pm-20:us-south:...",
       "credentials":{"apikey":"<wdp-writer key>","url":"https://us-south.ml.cloud.ibm.com",
       "instance_id":"826236c5-358a-4c26-9194-b93999aec27e"}}]}'
```

---

## Daily Workflow

### 1 — Extract the git delta (on tuxmaker)

```bash
# Option A: use the helper script (generates ciiq_delta_YYYYMMDD.json)
cd /home/ciuser/ciiq
./extract_delta.sh 20260714 20260713

# Option B: manual commands
TODAY=20260714; YEST=20260713
GOOD=$(cat /home/ciuser/logs/daily/$YEST/kernel.sha)
BAD=$(cat /home/ciuser/logs/daily/$TODAY/kernel.sha)
cd /home/ciuser/linux

git log --oneline $GOOD..$BAD -- arch/s390/kvm/ include/uapi/linux/kvm.h drivers/s390/ arch/s390/boot/
git diff --stat $GOOD..$BAD
git diff $GOOD..$BAD -- arch/s390/kvm/ include/uapi/linux/kvm.h | head -200
rpm -qa | grep -E 's390-tools|qemu|libvirt|kernel' | sort
```

### 2 — Open CIIQ

```
http://localhost:5100
```

Set the **Run Date** and **Run ID** in the sidebar.

### 3 — Paste the git delta

Fill in the four tabs of the **Git Delta** panel:

| Tab | Command | Paste |
|-----|---------|-------|
| git log | `git log --oneline $GOOD..$BAD -- arch/s390/kvm/ ...` | Commit list |
| diff --stat | `git diff --stat $GOOD..$BAD` | File change summary |
| patch hunks | `git diff $GOOD..$BAD -- arch/s390/kvm/ include/uapi/linux/kvm.h` | Key diffs |
| env / pkgs | `rpm -qa \| grep -E 's390-tools\|qemu\|libvirt'` | Package versions |

### 4 — Load failure logs

Click **Load Run Logs** to auto-populate suite textareas from `/home/ciuser/logs/daily/YYYYMMDD/`.

Or paste failure lines manually — any `FAIL / BUG / ERROR / panic / assert` lines from the suite logs.

### 5 — Analyse

Click **⚡ Analyse All Projects** — CIIQ calls WatsonX for KVM, QEMU, and libvirt in sequence (~30–90 s total).

Once all analyses are done, the **Correlation** panel auto-prompts. Click **🔗 Correlate** for:
- Cross-project root-cause (which single commit broke all three)
- Dependency chain: KVM → QEMU → libvirt
- Minimum fix set (fewest reverts to restore CI)
- Triage order (which fix unblocks the most suites first)
- Reproducer command for tuxmaker

### 6 — File the bug

Copy the output into Bugzilla:

| CIIQ section | → Bugzilla field |
|---|---|
| Introducing Commit | `commit` / `URL` field |
| Root Cause | Description body |
| Affected Subsystems | Component tags |
| Recommended Fix | Patch attachment or whiteboard |
| Verification command | Steps to Reproduce |

---

## API Reference

All endpoints accept and return JSON. When the server has `.env` credentials, `api_key` and `project_id` fields in request bodies are optional.

### POST `/api/token`
Exchange an IBM Cloud API key for an IAM Bearer token (smoke test).
```bash
curl -X POST http://localhost:5100/api/token \
  -H 'Content-Type: application/json' -d '{}'
```

### POST `/api/analyse/<project>`
Analyse one project. `project` = `kvm` | `qemu` | `libvirt`.
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
      "git_diff_stat": "arch/s390/kvm/intercept.c | 47 ++++++--\n...",
      "git_patch":     "diff --git a/arch/s390/kvm/intercept.c\n+...",
      "env_versions":  "s390-tools-2.34.0\nqemu-8.2.1"
    },
    "suite_logs": {
      "hades":         "kvm-s390: intercept of unimplemented instruction 0xb9af",
      "kvm-selftests": "KVM_S390_MEM_OP ioctl unexpectedly succeeded with new flags"
    }
  }'
```

Response:
```json
{
  "ok": true,
  "project": "kvm",
  "analysis": "## 1. Introducing Commit(s)...",
  "model": "ibm/granite-3-8b-instruct",
  "input_tokens": 681,
  "generated_tokens": 935
}
```

### POST `/api/analyse/all`
Analyse all three projects in one call. Accepts `suite_logs` in two formats:

**Nested** (per-project):
```json
{ "suite_logs": { "kvm": {"hades":"..."}, "qemu": {"qemu-s390x-kvm":"..."}, "libvirt": {...} } }
```

**Flat** (auto-split by config suites):
```json
{ "suite_logs": { "hades": "...", "qemu-s390x-kvm": "...", "libvirt-s390x": "..." } }
```

Use the `extract_delta.sh` JSON output directly:
```bash
curl -X POST http://localhost:5100/api/analyse/all \
  -H 'Content-Type: application/json' \
  -d @ciiq_delta_20260714.json
```

### POST `/api/correlate`
Cross-project root-cause correlation. Call after running per-project analyses.
```bash
curl -X POST http://localhost:5100/api/correlate \
  -H 'Content-Type: application/json' \
  -d '{
    "run_date": "2026-07-14",
    "delta": { ... },
    "analyses": {
      "kvm":     "... analysis text from /api/analyse/kvm ...",
      "qemu":    "... analysis text ...",
      "libvirt": "... analysis text ..."
    }
  }'
```

### GET `/api/run/<date>/suites`
Auto-populate suite logs from the tuxmaker log directory.
```bash
curl http://localhost:5100/api/run/20260714/suites
```

### GET `/api/runs`
List all available run dates found under `ci.log_base`.

### GET/DELETE `/api/history`
Retrieve or clear the session's analysis history.

---

## Configuration (`config.yaml`)

```yaml
watsonx:
  api_key:          "${CIIQ_WATSONX_API_KEY}"     # from .env
  project_id:       "${CIIQ_WATSONX_PROJECT_ID}"  # from .env
  region:           "us-south"                    # WML instance region
  model:            "ibm/granite-3-8b-instruct"
  max_tokens:       2048
  call_stagger_ms:  500    # delay between KVM/QEMU/libvirt calls

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

### Environment variable overrides

| Variable | Config key overridden |
|---|---|
| `CIIQ_WATSONX_API_KEY` | `watsonx.api_key` |
| `CIIQ_WATSONX_PROJECT_ID` | `watsonx.project_id` |
| `CIIQ_SECRET_KEY` | `server.secret_key` |
| `CIIQ_LOG_BASE` | `ci.log_base` |
| `CIIQ_KERNEL_REPO` | `ci.kernel_repo` |
| `CIIQ_PORT` | `server.port` |
| `CIIQ_WORKERS` | gunicorn workers (prod mode) |

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

## Supported Models

| Model | Best for | Relative speed |
|-------|----------|---------------|
| `ibm/granite-3-8b-instruct` | Fast daily triage (default) | Fast |
| `ibm/granite-13b-chat-v2` | More detailed analysis | Medium |
| `ibm/granite-34b-code-instruct` | Deep code reasoning | Slow |
| `meta-llama/llama-3-3-70b-instruct` | Complex multi-file correlations | Slow |

---

## File Structure

```
ciiq/
├── app.py               Flask backend — 12 REST endpoints, WatsonX integration,
│                        IAM token cache, prompt builders, session history
├── config.yaml          Team configuration (region, model, log paths, suites)
├── requirements.txt     Python deps: flask, flask-cors, requests, pyyaml,
│                        python-dotenv, gunicorn
├── run.sh               Setup + dev/prod start/stop (auto-kills stale :5100 process)
├── extract_delta.sh     Tuxmaker helper — generates ciiq_delta_YYYYMMDD.json
├── .env                 Credentials (gitignored — never commit)
├── .env.example         Credentials template
├── templates/
│   └── ciiq.html        Full web UI — git delta panel, suite tables,
│                        per-project + correlation result boxes, session history
└── README.md            This file
```

---

## Troubleshooting

**`Address already in use` on port 5100**
```bash
lsof -ti:5100 | xargs kill -9
./run.sh    # run.sh also auto-clears the port on startup
```

**`IAM token error` / 401**
- Verify `CIIQ_WATSONX_API_KEY` is an IBM Cloud API key (not a WatsonX API key)
- Test: `curl -X POST https://iam.cloud.ibm.com/identity/token -d "grant_type=urn:ibm:params:oauth:grant-type:apikey&apikey=YOUR_KEY"`

**`no_associated_service_instance_error` / 403**
- The WatsonX project has no WML service linked
- Fix: use the IBM Cloud console → your project → Manage → Services → Add Watson Machine Learning
- Or use the API PATCH shown in the Credentials section above

**`Failed to find project_id` / 404 on eu-de**
- The CIIQ project and its WML instance are in `us-south` — ensure `config.yaml` has `region: "us-south"`

**WatsonX 429 (rate limit)**
- Increase `call_stagger_ms` in `config.yaml` to `1000` or `2000`
- Or switch to `granite-3-8b-instruct` which has higher throughput limits

**"No suite logs found" after clicking Load Run Logs**
- The log directory `/home/ciuser/logs/daily/YYYYMMDD/` is not mounted locally
- Run `./extract_delta.sh` on tuxmaker and paste snippets manually

---

*CIIQ — IBM KVM CI Intelligence & Insight Query*
*Made with IBM Bob*
