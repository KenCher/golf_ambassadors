#!/bin/bash
#
# Monday.com Weekly Column Agent - Launcher
# Adds a new "Updates MM/DD" column to the board every Monday.
#
# Schedule with cron to run automatically every Monday at 8 AM:
#   crontab -e
#   0 8 * * 1 cd /path/to/kvm && ./run_weekly_column_agent.sh >> ~/monday_column_agent.log 2>&1
#

echo "=========================================="
echo "  Monday.com Weekly Column Agent"
echo "=========================================="
echo "  $(date)"
echo "=========================================="
echo ""

# Change to the directory where this script lives
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Use explicit Python path so launchd finds the right version (not /usr/bin/python3)
PYTHON=/opt/homebrew/bin/python3

# Check Python 3
if ! command -v "$PYTHON" &> /dev/null; then
    echo "❌ Python 3 not found at $PYTHON"
    echo "   Try: brew install python3"
    exit 1
fi

echo "✅ Python: $($PYTHON --version)"
echo ""

# Check required package
$PYTHON -c "import requests" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "⚠️  Missing package: requests — installing..."
    pip3 install --user requests 2>/dev/null || pip3 install --break-system-packages requests 2>/dev/null
    $PYTHON -c "import requests" 2>/dev/null
    if [ $? -ne 0 ]; then
        echo "❌ Could not install 'requests'. Run: pip3 install requests"
        exit 1
    fi
fi

# Parse optional flags passed through to Python script
#   --dry-run   : preview only
#   --date MM/DD: use a specific date instead of this Monday
EXTRA_ARGS="$@"

echo "Running agent..."
echo ""
$PYTHON monday_weekly_column_agent.py $EXTRA_ARGS

EXIT_CODE=$?

echo ""
if [ $EXIT_CODE -eq 0 ]; then
    echo "=========================================="
    echo "✅  Agent finished successfully."
    echo "=========================================="
else
    echo "=========================================="
    echo "❌  Agent exited with error (code $EXIT_CODE)."
    echo "    Check the output above for details."
    echo "=========================================="
fi

exit $EXIT_CODE
