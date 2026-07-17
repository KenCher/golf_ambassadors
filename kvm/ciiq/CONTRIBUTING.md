# Contributing to CIIQ

CIIQ is an internal IBM tool for the KVM & Linux open source team.
This guide covers dev setup, adding new suites/endpoints, and the PR checklist.

---

## One-command setup (new team member)

```bash
git clone git@github.ibm.com:cheruiyo/Watsonx_challenge_2026.git
cd Watsonx_challenge_2026/kvm/ciiq

# Copy and fill in credentials
cp .env.example .env
nano .env          # set CIIQ_WATSONX_API_KEY and CIIQ_WATSONX_PROJECT_ID

# Install deps + start (auto-kills any stale process on :5100)
./run.sh

# Open the UI
open http://localhost:5100
```

> **Credential values** — ask Ken Cheruiyot or check the team password manager.
> Project ID: `62f9a86d-cf41-425d-9c66-5b5801b3054e` (us-south, IBM KVM CIIQ project)

---

## Dev environment

```bash
cd kvm/ciiq
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
source .env               # load credentials into shell
FLASK_ENV=development python app.py
```

Visit `http://localhost:5100`.  
Flask auto-reloads on file save in development mode.

---

## Coding standards

- Formatter/linter: **ruff** — run `ruff check . --fix && ruff format .`  
  (or let the pre-commit hook handle it — see `patchiq/.pre-commit-config.yaml`)
- Line length: 100 characters
- Docstrings: Google-style for public functions
- New endpoints must be documented in `README.md` API Reference section

---

## Adding a new CI suite

1. **Add the suite** to `config.yaml` under the correct project:
   ```yaml
   projects:
     kvm:
       suites:
         - { name: "my-new-suite", category: "test", default_status: "FAIL" }
   ```
2. **Verify** the suite name matches the directory name under `ci.log_base/YYYYMMDD/`
3. **Test** locally: click **Load Run Logs** in the UI — the new suite should appear
4. No Python changes required for new suites

## Adding a new API endpoint

1. Add the route function to `app.py` following the existing pattern
2. Add `@require_json` decorator if the endpoint accepts a request body
3. Return `jsonify({"ok": True, ...})` on success, `err(msg, code)` on failure
4. Document the new endpoint in `README.md` under API Reference
5. Add a smoke test in `.github/workflows/ci.yml`

---

## Running lints locally

```bash
pip install ruff
ruff check kvm/ciiq/
ruff format --check kvm/ciiq/
```

---

## Pull request checklist

- [ ] `ruff check` and `ruff format --check` clean
- [ ] New suites added to `config.yaml` (not hardcoded in Python)
- [ ] New endpoints documented in `README.md`
- [ ] `CHANGELOG.md` updated under `[Unreleased]`
- [ ] `.env.example` updated if new env vars were added
- [ ] No real credentials committed (Vault Radar will block the push)

---

*CIIQ — IBM KVM & Linux CI Intelligence & Insight Query*
