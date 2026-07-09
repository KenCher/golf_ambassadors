#!/usr/bin/env bash
# run_weekly_report.sh
# Generates the bug report HTML, commits it to gh-pages, and notifies Slack.
# Run manually or via cron every Monday.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
LOG_FILE="$REPO_DIR/logs/weekly_report.log"

mkdir -p "$REPO_DIR/logs"

echo "========================================" | tee -a "$LOG_FILE"
echo "$(date '+%Y-%m-%d %H:%M:%S') — Starting weekly bug report" | tee -a "$LOG_FILE"

# ---------------------------------------------------------------------------
# 1. Load config from .env if it exists (ignored by git)
# ---------------------------------------------------------------------------
ENV_FILE="$REPO_DIR/.env"
if [[ -f "$ENV_FILE" ]]; then
  echo "Loading config from .env …" | tee -a "$LOG_FILE"
  set -o allexport
  source "$ENV_FILE"
  set +o allexport
fi

# ---------------------------------------------------------------------------
# 2. Validate required environment variables
# ---------------------------------------------------------------------------
MISSING=()
[[ -z "${BUGZILLA_URL:-}"      ]] && MISSING+=("BUGZILLA_URL")
[[ -z "${BUGZILLA_API_KEY:-}"  ]] && MISSING+=("BUGZILLA_API_KEY")
[[ -z "${TEAM_EMAILS:-}"       ]] && MISSING+=("TEAM_EMAILS")
[[ -z "${SLACK_WEBHOOK_URL:-}" ]] && MISSING+=("SLACK_WEBHOOK_URL")

if [[ ${#MISSING[@]} -gt 0 ]]; then
  echo "ERROR: Missing required variables: ${MISSING[*]}" | tee -a "$LOG_FILE"
  echo "Set them in $REPO_DIR/.env or export them before running." | tee -a "$LOG_FILE"
  exit 1
fi

# ---------------------------------------------------------------------------
# 3. Generate the HTML report
# ---------------------------------------------------------------------------
echo "Generating HTML report …" | tee -a "$LOG_FILE"
cd "$REPO_DIR"
PAGES_URL="https://cheruiyo.github.io/us-kvm-status/" \
  python3 scripts/generate_bug_report.py 2>&1 | tee -a "$LOG_FILE"

# ---------------------------------------------------------------------------
# 4. Commit and push to gh-pages
# ---------------------------------------------------------------------------
echo "Deploying to gh-pages …" | tee -a "$LOG_FILE"

# Check if gh-pages branch exists locally; create it if not
if ! git show-ref --quiet refs/heads/gh-pages; then
  git checkout --orphan gh-pages
  git reset --hard
  git commit --allow-empty -m "init gh-pages"
  git checkout main
fi

# Use a temporary worktree so we don't have to switch branches
TMP_DIR=$(mktemp -d)
git worktree add "$TMP_DIR" gh-pages 2>/dev/null || {
  git worktree remove --force "$TMP_DIR" 2>/dev/null || true
  git worktree add "$TMP_DIR" gh-pages
}

cp "$REPO_DIR/output/index.html" "$TMP_DIR/index.html"

cd "$TMP_DIR"
git add index.html
if git diff --cached --quiet; then
  echo "No changes to deploy." | tee -a "$LOG_FILE"
else
  git commit -m "chore: weekly bug report $(date '+%Y-%m-%d')"
  git push origin gh-pages 2>&1 | tee -a "$LOG_FILE"
  echo "Deployed successfully." | tee -a "$LOG_FILE"
fi

# Clean up worktree
cd "$REPO_DIR"
git worktree remove "$TMP_DIR" --force

# ---------------------------------------------------------------------------
# 5. Notify Slack via Workflow webhook
# ---------------------------------------------------------------------------
echo "Sending Slack notification …" | tee -a "$LOG_FILE"
python3 - <<EOF 2>&1 | tee -a "$LOG_FILE"
import os, urllib.request, json

webhook_url = os.environ["SLACK_WEBHOOK_URL"]
report_url  = "https://cheruiyo.github.io/us-kvm-status/"

payload = {"report_url": report_url}
req = urllib.request.Request(
  webhook_url,
  data=json.dumps(payload).encode(),
  headers={"Content-Type": "application/json"}
)
with urllib.request.urlopen(req) as resp:
  print(f"Slack webhook response: {resp.status}")
print("Slack notification sent.")
EOF

echo "$(date '+%Y-%m-%d %H:%M:%S') — Done." | tee -a "$LOG_FILE"
echo "========================================" | tee -a "$LOG_FILE"
