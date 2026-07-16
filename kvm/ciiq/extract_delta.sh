#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
#  CIIQ — Git Delta Extraction Helper
#  Run this on TUXMAKER (or locally if the repo is mounted) to gather
#  everything CIIQ needs before running an analysis.
#
#  Usage:
#    ./extract_delta.sh <run_date_today> [run_date_yesterday]
#
#  Examples:
#    ./extract_delta.sh 20260714
#    ./extract_delta.sh 20260714 20260713
#
#  Output:
#    ciiq_delta_<TODAY>.json   — paste-ready JSON for the CIIQ API
#    ciiq_delta_<TODAY>.txt    — human-readable summary
#
#  Dependencies: git, rpm or dpkg, ssh (if running remotely), jq (optional)
# ─────────────────────────────────────────────────────────────────────────────

set -euo pipefail

TODAY="${1:-$(date +%Y%m%d)}"
YESTERDAY="${2:-$(date -d 'yesterday' +%Y%m%d 2>/dev/null || date -v-1d +%Y%m%d)}"

LOG_BASE="${CIIQ_LOG_BASE:-/home/ciuser/logs/daily}"
KERNEL_REPO="${CIIQ_KERNEL_REPO:-/home/ciuser/linux}"
OUTPUT_DIR="${CIIQ_OUTPUT_DIR:-.}"

SHA_FILE_TODAY="${LOG_BASE}/${TODAY}/kernel.sha"
SHA_FILE_YESTERDAY="${LOG_BASE}/${YESTERDAY}/kernel.sha"
OUT_JSON="${OUTPUT_DIR}/ciiq_delta_${TODAY}.json"
OUT_TXT="${OUTPUT_DIR}/ciiq_delta_${TODAY}.txt"

echo "=== CIIQ Git Delta Extractor ==="
echo "Today:     ${TODAY}"
echo "Yesterday: ${YESTERDAY}"
echo "Kernel:    ${KERNEL_REPO}"
echo ""

# ── Resolve SHAs ──────────────────────────────────────────────────────────────
if [[ -f "${SHA_FILE_TODAY}" ]]; then
    SHA_BAD=$(cat "${SHA_FILE_TODAY}" | tr -d '[:space:]')
    echo "[+] Bad  SHA (today):     ${SHA_BAD}"
else
    echo "[!] WARNING: ${SHA_FILE_TODAY} not found — using HEAD"
    SHA_BAD="HEAD"
fi

if [[ -f "${SHA_FILE_YESTERDAY}" ]]; then
    SHA_GOOD=$(cat "${SHA_FILE_YESTERDAY}" | tr -d '[:space:]')
    echo "[+] Good SHA (yesterday): ${SHA_GOOD}"
else
    echo "[!] WARNING: ${SHA_FILE_YESTERDAY} not found — using HEAD~10"
    SHA_GOOD="HEAD~10"
fi

cd "${KERNEL_REPO}"

# ── Extract git log ────────────────────────────────────────────────────────────
echo "[+] Extracting git log..."
GIT_LOG=$(git log --oneline "${SHA_GOOD}..${SHA_BAD}" -- \
    arch/s390/kvm/ \
    include/uapi/linux/kvm.h \
    drivers/s390/ \
    arch/s390/boot/ \
    tools/testing/selftests/kvm/ \
    2>/dev/null || echo "(no commits in focused paths)")

GIT_LOG_FULL=$(git log --oneline "${SHA_GOOD}..${SHA_BAD}" 2>/dev/null | head -40 || echo "(error)")

# ── Extract diff stat ──────────────────────────────────────────────────────────
echo "[+] Extracting diff stat..."
GIT_DIFF_STAT=$(git diff --stat "${SHA_GOOD}..${SHA_BAD}" 2>/dev/null | tail -60 || echo "(error)")

# ── Extract key patch hunks ────────────────────────────────────────────────────
echo "[+] Extracting key patch hunks..."
GIT_PATCH=$(git diff "${SHA_GOOD}..${SHA_BAD}" -- \
    arch/s390/kvm/ \
    include/uapi/linux/kvm.h \
    2>/dev/null | head -200 || echo "(error)")

# ── Package versions ───────────────────────────────────────────────────────────
echo "[+] Collecting package versions..."
if command -v rpm &>/dev/null; then
    PKG_VERSIONS=$(rpm -qa 2>/dev/null | grep -E 's390-tools|qemu|libvirt|kernel' | sort || echo "(rpm not available)")
elif command -v dpkg &>/dev/null; then
    PKG_VERSIONS=$(dpkg -l 2>/dev/null | grep -E 's390-tools|qemu|libvirt|linux-image' | awk '{print $2"-"$3}' | sort || echo "(dpkg error)")
else
    PKG_VERSIONS="(no package manager found)"
fi

# ── Failure log snippets from each suite ──────────────────────────────────────
echo "[+] Collecting failure log snippets..."
declare -A SUITE_LOGS
SUITE_LIST=(canton-prototype ci-reipl hades hades-monolithic hades-withHW kvm-selftests kvm-unit-tests-kvm s390-tools qemu-s390x-kvm qemu-migration-s390 libvirt-s390x libvirt-migration libvirt-qemu-driver)

for SUITE in "${SUITE_LIST[@]}"; do
    LOG_DIR="${LOG_BASE}/${TODAY}/${SUITE}"
    if [[ -d "${LOG_DIR}" ]]; then
        SNIPPET=$(grep -rE "(FAIL|FAILED|BUG|Oops|panic|assert|ERROR|error:|No such|Invalid argument|unexpected)" \
            "${LOG_DIR}" 2>/dev/null | head -8 | sed 's/\t/ /g' || echo "")
        SUITE_LOGS["${SUITE}"]="${SNIPPET}"
    else
        SUITE_LOGS["${SUITE}"]="(log directory not found: ${LOG_DIR})"
    fi
done

# ── Write text summary ────────────────────────────────────────────────────────
{
echo "CIIQ Delta Report — ${TODAY}"
echo "SHA good: ${SHA_GOOD}"
echo "SHA bad:  ${SHA_BAD}"
echo ""
echo "=== GIT LOG (focused subsystems) ==="
echo "${GIT_LOG}"
echo ""
echo "=== GIT DIFF --STAT ==="
echo "${GIT_DIFF_STAT}"
echo ""
echo "=== KEY PATCH HUNKS ==="
echo "${GIT_PATCH}"
echo ""
echo "=== PACKAGE VERSIONS ==="
echo "${PKG_VERSIONS}"
} > "${OUT_TXT}"

# ── Write JSON for CIIQ API ───────────────────────────────────────────────────
python3 - <<PYEOF
import json, sys

suite_logs = {}
$(for SUITE in "${SUITE_LIST[@]}"; do
    echo "suite_logs['${SUITE}'] = '''${SUITE_LOGS[${SUITE}]:-}'''"
done)

data = {
    "run_date": "${TODAY}",
    "sha_good": "${SHA_GOOD}",
    "sha_bad":  "${SHA_BAD}",
    "git_log":       """${GIT_LOG}""",
    "git_diff_stat": """${GIT_DIFF_STAT}""",
    "git_patch":     """${GIT_PATCH}""",
    "env_versions":  """${PKG_VERSIONS}""",
    "suite_logs":    suite_logs,
}
with open("${OUT_JSON}", "w") as f:
    json.dump(data, f, indent=2)
print(f"[+] JSON written to ${OUT_JSON}")
PYEOF

echo ""
echo "=== Done ==="
echo "Text summary: ${OUT_TXT}"
echo "JSON for CIIQ: ${OUT_JSON}"
echo ""
echo "To run analysis:"
echo "  curl -X POST http://localhost:5100/api/analyse/all \\"
echo "       -H 'Content-Type: application/json' \\"
echo "       -d @${OUT_JSON}"
