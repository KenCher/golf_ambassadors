#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
#  CIIQ — Setup & Run Script
#  Run once to install dependencies, then run the server for the team.
#
#  Usage:
#    ./run.sh            — start CIIQ server (foreground)
#    ./run.sh setup      — install Python deps only
#    ./run.sh prod       — start with gunicorn (production, multiple workers)
#    ./run.sh stop       — stop a running gunicorn instance
# ─────────────────────────────────────────────────────────────────────────────

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV="${SCRIPT_DIR}/.venv"
PID_FILE="${SCRIPT_DIR}/.ciiq.pid"
LOG_FILE="${SCRIPT_DIR}/ciiq.log"

# ── Colours ───────────────────────────────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; BLUE='\033[0;34m'; NC='\033[0m'
info()    { echo -e "${BLUE}[CIIQ]${NC} $*"; }
success() { echo -e "${GREEN}[CIIQ]${NC} $*"; }
warn()    { echo -e "${YELLOW}[CIIQ]${NC} $*"; }
error()   { echo -e "${RED}[CIIQ]${NC} $*" >&2; }

# ── Check Python ──────────────────────────────────────────────────────────────
check_python() {
  if command -v python3 &>/dev/null; then
    PYTHON=python3
  elif command -v python &>/dev/null; then
    PYTHON=python
  else
    error "Python 3.9+ required. Install it and retry."
    exit 1
  fi
  PY_VER=$($PYTHON -c "import sys; print(sys.version_info[:2])")
  info "Python: $($PYTHON --version)  ($PY_VER)"
}

# ── Create venv ───────────────────────────────────────────────────────────────
setup_venv() {
  if [[ ! -d "${VENV}" ]]; then
    info "Creating virtual environment at ${VENV}..."
    $PYTHON -m venv "${VENV}"
  fi
  # shellcheck source=/dev/null
  source "${VENV}/bin/activate"
  info "Upgrading pip..."
  pip install --quiet --upgrade pip
  info "Installing CIIQ dependencies..."
  pip install --quiet -r "${SCRIPT_DIR}/requirements.txt"
  success "Dependencies installed."
}

# ── Check .env / credentials ──────────────────────────────────────────────────
check_env() {
  ENV_FILE="${SCRIPT_DIR}/.env"
  if [[ ! -f "${ENV_FILE}" ]]; then
    warn ".env file not found — creating template at ${ENV_FILE}"
    cat > "${ENV_FILE}" <<'ENVEOF'
# CIIQ Environment Variables
# Fill in your IBM Cloud credentials below.
# Alternatively, edit ciiq/config.yaml and set values directly.

CIIQ_WATSONX_API_KEY=your_ibm_cloud_api_key_here
CIIQ_WATSONX_PROJECT_ID=your_watsonx_project_id_here
CIIQ_SECRET_KEY=change_this_to_a_random_string_for_flask_sessions
ENVEOF
    warn "Edit ${ENV_FILE} with your credentials before starting the server."
    echo ""
  else
    info ".env found — credentials will be loaded from it."
  fi
}

# ── Start dev server ──────────────────────────────────────────────────────────
start_dev() {
  # Auto-clear any stale process on the port
  local port="${CIIQ_PORT:-5100}"
  lsof -ti:"${port}" | xargs kill -9 2>/dev/null || true
  source "${VENV}/bin/activate"
  info "Starting CIIQ development server..."
  info "  → http://localhost:5100"
  info "  Press Ctrl+C to stop."
  echo ""
  cd "${SCRIPT_DIR}"
  FLASK_APP=app.py FLASK_ENV=development python app.py
}

# ── Start production server ───────────────────────────────────────────────────
start_prod() {
  source "${VENV}/bin/activate"
  WORKERS="${CIIQ_WORKERS:-4}"
  PORT="${CIIQ_PORT:-5100}"
  info "Starting CIIQ production server (gunicorn)..."
  info "  Workers:  ${WORKERS}"
  info "  Port:     ${PORT}"
  info "  Log:      ${LOG_FILE}"
  info "  PID:      ${PID_FILE}"
  cd "${SCRIPT_DIR}"
  gunicorn \
    --workers "${WORKERS}" \
    --bind "0.0.0.0:${PORT}" \
    --timeout 180 \
    --log-level info \
    --access-logfile "${LOG_FILE}" \
    --error-logfile "${LOG_FILE}" \
    --pid "${PID_FILE}" \
    --daemon \
    "app:app"
  success "CIIQ running at http://0.0.0.0:${PORT}  (PID: $(cat "${PID_FILE}"))"
  info "  To stop: ./run.sh stop"
  info "  Logs:    tail -f ${LOG_FILE}"
}

# ── Stop production server ────────────────────────────────────────────────────
stop_prod() {
  if [[ -f "${PID_FILE}" ]]; then
    PID=$(cat "${PID_FILE}")
    info "Stopping CIIQ (PID ${PID})..."
    kill "${PID}" && rm -f "${PID_FILE}"
    success "Stopped."
  else
    warn "No PID file found at ${PID_FILE} — CIIQ may not be running."
  fi
}

# ── Main ──────────────────────────────────────────────────────────────────────
CMD="${1:-}"
check_python

case "${CMD}" in
  setup)
    setup_venv
    check_env
    success "Setup complete. Run './run.sh' to start CIIQ."
    ;;
  prod)
    setup_venv
    check_env
    start_prod
    ;;
  stop)
    stop_prod
    ;;
  "")
    setup_venv
    check_env
    start_dev
    ;;
  *)
    echo "Usage: $0 [setup|prod|stop]"
    exit 1
    ;;
esac
