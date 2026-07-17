#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
#  CIIQ — One-command team onboarding script
#
#  Run this once on a new machine:
#    curl -sSf https://github.ibm.com/raw/cheruiyo/Watsonx_challenge_2026/main/kvm/ciiq/setup.sh | bash
#  Or from the cloned repo:
#    bash kvm/ciiq/setup.sh
#
#  What it does:
#    1. Checks Python 3.10+
#    2. Creates .venv and installs dependencies
#    3. Creates .env from .env.example if not present
#    4. Prints the credentials you need to fill in
#    5. Starts CIIQ dev server at http://localhost:5100
# ─────────────────────────────────────────────────────────────────────────────
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${SCRIPT_DIR}"

# ── Colours ───────────────────────────────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; BLUE='\033[0;34m'; BOLD='\033[1m'; NC='\033[0m'
info()    { echo -e "${BLUE}▸${NC} $*"; }
ok()      { echo -e "${GREEN}✓${NC} $*"; }
warn()    { echo -e "${YELLOW}⚠${NC} $*"; }
die()     { echo -e "${RED}✗ ERROR:${NC} $*" >&2; exit 1; }
banner()  { echo -e "\n${BOLD}$*${NC}"; }

banner "═══════════════════════════════════════════"
banner " CIIQ — CI Intelligence & Insight Query"
banner " IBM KVM & Linux Open Source Team"
banner "═══════════════════════════════════════════"
echo ""

# ── 1. Check Python ───────────────────────────────────────────────────────────
banner "Step 1 — Python"
if ! command -v python3 &>/dev/null; then
    die "python3 not found. Install Python 3.10+ and retry."
fi
PY_VER=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
PY_MAJOR=$(python3 -c "import sys; print(sys.version_info.major)")
PY_MINOR=$(python3 -c "import sys; print(sys.version_info.minor)")
if [[ "${PY_MAJOR}" -lt 3 ]] || [[ "${PY_MAJOR}" -eq 3 && "${PY_MINOR}" -lt 10 ]]; then
    die "Python 3.10+ required (found ${PY_VER}). Upgrade and retry."
fi
ok "Python ${PY_VER}"

# ── 2. Create venv + install deps ─────────────────────────────────────────────
banner "Step 2 — Virtual environment"
if [[ ! -d ".venv" ]]; then
    info "Creating .venv..."
    python3 -m venv .venv
fi
source .venv/bin/activate
info "Upgrading pip..."
pip install --quiet --upgrade pip
info "Installing dependencies..."
pip install --quiet -r requirements.txt
ok "Dependencies installed"
pip show flask requests pyyaml python-dotenv gunicorn | grep "^Name:" | awk '{print "  " $2}'

# ── 3. Credentials ────────────────────────────────────────────────────────────
banner "Step 3 — Credentials"
if [[ -f ".env" ]]; then
    ok ".env already exists — skipping"
else
    cp .env.example .env
    warn ".env created from template — fill in your credentials:"
    echo ""
    echo -e "  ${BOLD}File:${NC} ${SCRIPT_DIR}/.env"
    echo ""
    echo -e "  ${YELLOW}CIIQ_WATSONX_API_KEY${NC}     — IBM Cloud API key"
    echo -e "                             cloud.ibm.com → Manage → Access → API keys"
    echo ""
    echo -e "  ${YELLOW}CIIQ_WATSONX_PROJECT_ID${NC}  — watsonx project ID"
    echo -e "                             ${BOLD}62f9a86d-cf41-425d-9c66-5b5801b3054e${NC} (team project)"
    echo ""
    echo -e "  ${YELLOW}CIIQ_SECRET_KEY${NC}           — any random string for Flask sessions"
    echo -e "                             auto-generate: python3 -c \"import secrets; print(secrets.token_hex(32))\""
    echo ""
    read -rp "  Open .env in your editor now? (y/n) " EDIT
    if [[ "${EDIT}" =~ ^[Yy]$ ]]; then
        "${EDITOR:-nano}" .env
    else
        warn "Remember to edit .env before starting the server."
    fi
fi

# ── 4. Validate credentials ───────────────────────────────────────────────────
banner "Step 4 — Validate credentials"
source .env 2>/dev/null || true
API_KEY="${CIIQ_WATSONX_API_KEY:-}"
PROJ_ID="${CIIQ_WATSONX_PROJECT_ID:-}"

if [[ -z "${API_KEY}" || "${API_KEY}" == *"your_"* || "${API_KEY}" == *"placeholder"* ]]; then
    warn "CIIQ_WATSONX_API_KEY is not set — AI analysis will be disabled until you fill in .env"
else
    info "Testing IBM IAM token exchange..."
    HTTP=$(curl -s -o /dev/null -w "%{http_code}" \
        -X POST "https://iam.cloud.ibm.com/identity/token" \
        -H "Content-Type: application/x-www-form-urlencoded" \
        -d "grant_type=urn:ibm:params:oauth:grant-type:apikey&apikey=${API_KEY}" \
        --max-time 10 2>/dev/null || echo "000")
    if [[ "${HTTP}" == "200" ]]; then
        ok "IBM IAM credentials valid ✓ — watsonx AI analysis enabled"
    else
        warn "IAM token exchange returned HTTP ${HTTP} — check CIIQ_WATSONX_API_KEY in .env"
    fi
fi

# ── 5. Start server ───────────────────────────────────────────────────────────
banner "Step 5 — Start CIIQ"
echo ""
ok "Setup complete!"
echo ""
echo -e "  ${BOLD}URL:${NC}   http://localhost:5100"
echo -e "  ${BOLD}Stop:${NC}  Ctrl+C  (or  lsof -ti:5100 | xargs kill -9)"
echo ""
echo -e "  ${BOLD}Daily workflow:${NC}"
echo "    1. Run ./extract_delta.sh on tuxmaker to get the git delta JSON"
echo "    2. Open http://localhost:5100"
echo "    3. Paste delta, load suite logs, click Analyse All"
echo "    4. Copy output into Bugzilla"
echo ""

# Auto-open browser on macOS
if [[ "$OSTYPE" == "darwin"* ]]; then
    sleep 1 && open http://localhost:5100 &
fi

exec ./run.sh
