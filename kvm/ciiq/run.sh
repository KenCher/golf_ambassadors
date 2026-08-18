#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
#  CIIQ — Setup & Run Script  (local / no-API edition)
#  No IBM Cloud credentials required.
#
#  Usage:
#    ./run.sh            — install deps + start dev server (foreground)
#    ./run.sh setup      — install Python deps only
#    ./run.sh prod       — start with gunicorn (production)
#    ./run.sh stop       — stop a running gunicorn instance
#
#  For the watsonx-backed variant use: run-wx.sh
# ─────────────────────────────────────────────────────────────────────────────

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV="${SCRIPT_DIR}/.venv"
PID_FILE="${SCRIPT_DIR}/.ciiq.pid"
LOG_FILE="${SCRIPT_DIR}/ciiq.log"

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; BLUE='\033[0;34m'; NC='\033[0m'
info()    { echo -e "${BLUE}[CIIQ]${NC} $*"; }
success() { echo -e "${GREEN}[CIIQ]${NC} $*"; }
warn()    { echo -e "${YELLOW}[CIIQ]${NC} $*"; }
error()   { echo -e "${RED}[CIIQ]${NC} $*" >&2; }

check_python() {
  if command -v python3 &>/dev/null; then
    PYTHON=python3
  elif command -v python &>/dev/null; then
    PYTHON=python
  else
    error "Python 3.9+ required. Install it and retry."
    exit 1
  fi
  info "Python: $($PYTHON --version)"
}

setup_venv() {
  if [[ ! -d "${VENV}" ]]; then
    info "Creating virtual environment at ${VENV}..."
    $PYTHON -m venv "${VENV}"
  fi
  source "${VENV}/bin/activate"
  info "Upgrading pip..."
  pip install --quiet --upgrade pip
  info "Installing CIIQ dependencies..."
  pip install --quiet -r "${SCRIPT_DIR}/requirements.txt"
  success "Dependencies installed."
}

start_dev() {
  local port="${CIIQ_PORT:-5100}"
  lsof -ti:"${port}" | xargs kill -9 2>/dev/null || true
  source "${VENV}/bin/activate"
  prefetch_latest_run
  info "Starting CIIQ development server (local engine)..."
  info "  → http://localhost:${port}"
  info "  Press Ctrl+C to stop."
  echo ""
  cd "${SCRIPT_DIR}"
  FLASK_APP=app.py FLASK_ENV=development python app.py
}

start_prod() {
  source "${VENV}/bin/activate"
  prefetch_latest_run
  WORKERS="${CIIQ_WORKERS:-4}"
  PORT="${CIIQ_PORT:-5100}"
  info "Starting CIIQ production server (gunicorn, local engine)..."
  info "  Workers:  ${WORKERS}"
  info "  Port:     ${PORT}"
  cd "${SCRIPT_DIR}"
  gunicorn \
    --workers "${WORKERS}" \
    --bind "0.0.0.0:${PORT}" \
    --timeout 60 \
    --log-level info \
    --access-logfile "${LOG_FILE}" \
    --error-logfile  "${LOG_FILE}" \
    --pid "${PID_FILE}" \
    --daemon \
    "app:app"
  success "CIIQ running at http://0.0.0.0:${PORT}  (PID: $(cat "${PID_FILE}"))"
  info "  To stop: ./run.sh stop"
  info "  Logs:    tail -f ${LOG_FILE}"
}

stop_prod() {
  if [[ -f "${PID_FILE}" ]]; then
    PID=$(cat "${PID_FILE}")
    info "Stopping CIIQ (PID ${PID})..."
    kill "${PID}" && rm -f "${PID_FILE}"
    success "Stopped."
  else
    warn "No PID file found — CIIQ may not be running."
  fi
}


prefetch_latest_run() {
  # SSH to tuxmaker, find the latest run date, fetch its git delta into local cache.
  # Non-fatal: any failure is logged as a warning and startup continues.
  source "${VENV}/bin/activate"
  info "Checking for latest CI run on tuxmaker..."
  python3 "${SCRIPT_DIR}/prefetch_delta.py" "${SCRIPT_DIR}" 2>&1 | while IFS= read -r line; do
    info "  ${line}"
  done || warn "prefetch: could not reach tuxmaker — start the app and use Load Run Logs to fetch manually"
}

CMD="${1:-}"
check_python

case "${CMD}" in
  setup)
    setup_venv
    success "Setup complete. Run './run.sh' to start CIIQ."
    ;;
  prod)
    setup_venv
    start_prod
    ;;
  stop)
    stop_prod
    ;;
  "")
    setup_venv
    start_dev
    ;;
  *)
    echo "Usage: $0 [setup|prod|stop]"
    exit 1
    ;;
esac
