#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
#  CIIQ — Orchestrate / Agentic Edition Run Script
#  Uses IBM watsonx tool-calling (llama-3-3-70b-instruct) ReAct agent loop.
#
#  Usage:
#    ./run-orch.sh           — install deps + start dev server on :5200
#    ./run-orch.sh setup     — install deps only
#    ./run-orch.sh prod      — start gunicorn on :5200 (background)
#    ./run-orch.sh stop      — stop gunicorn
# ─────────────────────────────────────────────────────────────────────────────

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV="${SCRIPT_DIR}/.venv"
PID_FILE="${SCRIPT_DIR}/.ciiq-orch.pid"
LOG_FILE="${SCRIPT_DIR}/ciiq-orch.log"

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; BLUE='\033[0;34m'; NC='\033[0m'
info()    { echo -e "${BLUE}[CIIQ-orch]${NC} $*"; }
success() { echo -e "${GREEN}[CIIQ-orch]${NC} $*"; }
warn()    { echo -e "${YELLOW}[CIIQ-orch]${NC} $*"; }
error()   { echo -e "${RED}[CIIQ-orch]${NC} $*" >&2; }

check_python() {
  PYTHON=$(command -v python3 || command -v python || { error "Python 3.9+ required"; exit 1; })
  info "Python: $($PYTHON --version)"
}

setup_venv() {
  [[ ! -d "${VENV}" ]] && $PYTHON -m venv "${VENV}"
  source "${VENV}/bin/activate"
  pip install --quiet --upgrade pip
  pip install --quiet -r "${SCRIPT_DIR}/requirements.txt"
  success "Dependencies installed."
}

check_env() {
  ENV_FILE="${SCRIPT_DIR}/.env"
  if [[ ! -f "${ENV_FILE}" ]]; then
    warn "No .env file — creating template"
    cat > "${ENV_FILE}" << 'ENVEOF'
CIIQ_WATSONX_API_KEY=your_ibm_cloud_api_key_here
CIIQ_WATSONX_PROJECT_ID=your_watsonx_project_id_here
CIIQ_SECRET_KEY=change_this_random_string
ENVEOF
    warn "Edit ${ENV_FILE} with your credentials before starting."
  else
    info ".env found — credentials will be loaded."
  fi
}

start_dev() {
  local port="${CIIQ_PORT:-5200}"
  lsof -ti:"${port}" | xargs kill -9 2>/dev/null || true
  source "${VENV}/bin/activate"
  info "Starting CIIQ Orchestrate edition (dev, port ${port})..."
  info "  Agent model: llama-3-3-70b-instruct (tool calling)"
  info "  → http://localhost:${port}"
  cd "${SCRIPT_DIR}"
  FLASK_APP=app-orch.py FLASK_ENV=development python app-orch.py
}

start_prod() {
  source "${VENV}/bin/activate"
  PORT="${CIIQ_PORT:-5200}"
  WORKERS="${CIIQ_WORKERS:-2}"
  info "Starting CIIQ Orchestrate edition (gunicorn, port ${PORT}, ${WORKERS} workers)..."
  cd "${SCRIPT_DIR}"
  gunicorn \
    --workers "${WORKERS}" \
    --bind "0.0.0.0:${PORT}" \
    --timeout 300 \
    --log-level info \
    --access-logfile "${LOG_FILE}" \
    --error-logfile  "${LOG_FILE}" \
    --pid "${PID_FILE}" \
    --daemon \
    "app-orch:app"
  success "CIIQ Orchestrate running at http://0.0.0.0:${PORT}  (PID: $(cat "${PID_FILE}"))"
  info "  Logs: tail -f ${LOG_FILE}"
  info "  Stop: ./run-orch.sh stop"
}

stop_prod() {
  if [[ -f "${PID_FILE}" ]]; then
    kill "$(cat "${PID_FILE}")" && rm -f "${PID_FILE}" && success "Stopped."
  else
    warn "No PID file found."
  fi
}

CMD="${1:-}"
check_python
case "${CMD}" in
  setup) setup_venv; check_env; success "Setup complete. Run './run-orch.sh' to start." ;;
  prod)  setup_venv; check_env; start_prod ;;
  stop)  stop_prod ;;
  "")    setup_venv; check_env; start_dev ;;
  *)     echo "Usage: $0 [setup|prod|stop]"; exit 1 ;;
esac
