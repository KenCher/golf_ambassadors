# Weekly Bug Report — Setup Guide

A GitHub Actions workflow that runs every Monday at 08:00 UTC, fetches open
Bugzilla bugs for your team, publishes a self-contained HTML dashboard to
**GitHub Pages**, and posts a link to the **#GEQEG2C80** Slack channel.

- **Repo:** https://github.ibm.com/cheruiyo/us-kvm-status
- **Live dashboard:** https://cheruiyo.github.io/us-kvm-status/
- **Slack channel:** `GEQEG2C80`

---

## Files

| File | Purpose |
|------|---------|
| `.github/workflows/weekly-bug-report.yml` | Scheduled workflow |
| `scripts/generate_bug_report.py` | Fetches bugs and renders HTML |
| `output/index.html` | Generated report (committed to `gh-pages`) |

---

## One-time Setup

### 1. Add repository secrets

Go to **Settings → Secrets and variables → Actions → New repository secret**
and add the following secrets:

| Secret name | Value |
|-------------|-------|
| `BUGZILLA_URL` | `https://bugzilla.linux.ibm.com` |
| `BUGZILLA_API_KEY` | Your Bugzilla API key — generate under *Preferences → API Keys* in Bugzilla. Leave empty if your Bugzilla allows unauthenticated reads. |
| `TEAM_EMAILS` | Comma-separated team member emails, e.g. `farman@us.ibm.com,jaredros@us.ibm.com` |
| `SLACK_BOT_TOKEN` | A Slack Bot token (`xoxb-…`) with `chat:write` scope, added to channel `GEQEG2C80`. See below. |

### 2. Create a Slack Bot token

1. Go to https://api.slack.com/apps → **Create New App** → **From scratch**
2. Name it (e.g. `KVM Bug Report`), pick your workspace
3. Under **OAuth & Permissions → Scopes → Bot Token Scopes**, add `chat:write`
4. Click **Install to Workspace** and copy the **Bot User OAuth Token** (`xoxb-…`)
5. In Slack, open channel `GEQEG2C80`, click the channel name → **Integrations → Add an App**, add your new bot
6. Paste the token as the `SLACK_BOT_TOKEN` secret in the repo

### 3. Enable GitHub Pages

1. Go to **Settings → Pages**
2. Set **Source** to `Deploy from a branch`
3. Set **Branch** to `gh-pages`, folder `/` (root)
4. Click **Save**

The report will be live at:
```
https://cheruiyo.github.io/us-kvm-status/
```

### 4. Trigger a test run

Go to **Actions → Weekly Bug Report → Run workflow** to run it immediately
without waiting for Monday.

---

## Schedule

Runs every **Monday at 08:00 UTC** (`cron: '0 8 * * MON'`).  
To change the time, edit the `cron` line in
`.github/workflows/weekly-bug-report.yml`.

---

## Local testing

```bash
export BUGZILLA_URL="https://bugzilla.linux.ibm.com"
export BUGZILLA_API_KEY="your_key_here"
export TEAM_EMAILS="farman@us.ibm.com,jaredros@us.ibm.com"
export PAGES_URL="https://cheruiyo.github.io/us-kvm-status/"

pip install requests
python scripts/generate_bug_report.py
open output/index.html
```
