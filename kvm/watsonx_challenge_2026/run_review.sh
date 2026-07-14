#!/bin/bash
# ──────────────────────────────────────────────────────────────
#  PatchIQ — Run a patch review from the command line
#
#  Usage:
#    ./watsonx_challenge_2026/run_review.sh                    # review HEAD commit
#    ./watsonx_challenge_2026/run_review.sh my_fix.patch       # review a patch file
#    ./watsonx_challenge_2026/run_review.sh origin/main..HEAD  # review a commit range
#    git diff HEAD~1 | ./watsonx_challenge_2026/run_review.sh  # pipe a diff
# ──────────────────────────────────────────────────────────────

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"
HTML_OUT="watsonx_challenge_2026_review_$(date '+%Y%m%d_%H%M%S').html"

echo ""
echo "╔══════════════════════════════════════════════════════════╗"
echo "║         🔎 PatchIQ — AI Patch Reviewer                  ║"
echo "║    KVM · Kernel · QEMU · libvirt                         ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""

# Validate watsonx env vars (warn, not block)
if [ -z "${WATSONX_API_KEY:-}" ] || [ -z "${WATSONX_PROJECT_ID:-}" ]; then
    echo "⚠️  WATSONX_API_KEY / WATSONX_PROJECT_ID not set"
    echo "   Style checks will run but AI review will be skipped."
    echo "   Export both env vars to enable the watsonx AI review."
    echo ""
fi

cd "$REPO_ROOT"

# ── determine mode ─────────────────────────────────────────────
if [ ! -t 0 ]; then
    # stdin has data — pipe mode
    echo "📥 Reading diff from stdin..."
    python3 -m watsonx_challenge_2026.cli pipe --html "$HTML_OUT"

elif [ "${1:-}" = "" ]; then
    # No argument — default to HEAD
    echo "📌 Reviewing HEAD commit..."
    python3 -m watsonx_challenge_2026.cli commit HEAD --html "$HTML_OUT"

elif [[ "${1:-}" == *..* ]]; then
    # Looks like a git range
    echo "📌 Reviewing range: $1"
    python3 -m watsonx_challenge_2026.cli range "$1" --html "$HTML_OUT"

elif [ -f "${1:-}" ]; then
    # It's a file
    echo "📄 Reviewing patch file: $1"
    python3 -m watsonx_challenge_2026.cli patch "$1" --html "$HTML_OUT"

else
    # Treat as a git ref
    echo "📌 Reviewing commit: $1"
    python3 -m watsonx_challenge_2026.cli commit "${1:-HEAD}" --html "$HTML_OUT"
fi

echo ""
echo "╔══════════════════════════════════════════════════════════╗"
echo "║                  ✅ Review Complete                      ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""
echo "   HTML report: $HTML_OUT"
echo ""

# Auto-open on macOS
if [[ "$OSTYPE" == "darwin"* ]] && [ -f "$HTML_OUT" ]; then
    read -p "🌐 Open HTML report in browser? (y/n) " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        open "$HTML_OUT"
    fi
fi
