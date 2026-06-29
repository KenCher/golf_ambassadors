#!/bin/bash
# Monday.com Status Sync - Generates status report + PowerPoint with BU* items grouped
# BU work items are grouped together in their own slide section, sorted by BU number.

PYTHON=/opt/homebrew/bin/python3
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "╔════════════════════════════════════════════════════════════╗"
echo "║     📊 Monday.com Status Sync (BU Items Grouped)          ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""
echo "🔄 Fetching current status from Monday.com board..."
echo ""

# Check Python
if ! command -v "$PYTHON" &> /dev/null; then
    echo "❌ Python not found at $PYTHON — falling back to system python3"
    PYTHON=python3
fi

echo "✅ Python: $($PYTHON --version)"
echo ""

# Check required packages
$PYTHON -c "import requests, pptx" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "⚠️  Installing required packages..."
    pip3 install --user requests python-pptx 2>/dev/null || \
    pip3 install --break-system-packages requests python-pptx 2>/dev/null
    $PYTHON -c "import requests, pptx" 2>/dev/null
    if [ $? -ne 0 ]; then
        echo "❌ Could not install packages. Run: pip3 install requests python-pptx"
        exit 1
    fi
fi

# Step 1: Generate JSON + HTML status report
$PYTHON get_monday_status.py
if [ $? -ne 0 ]; then
    echo ""
    echo "❌ Error: Failed to fetch board status. Check API token and network."
    exit 1
fi

echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║              ✅ Status Report Generated!                  ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""
echo "📄 Output files:"
echo "   • monday_status.json         - JSON data export"
echo "   • monday_status_report.html  - Interactive HTML report"
echo ""

# Step 2: Generate PowerPoint with BU* items grouped
echo "📊 Generating PowerPoint with BU work items grouped..."
echo "   Slide sections:"
echo "   1. Bringup and Tools"
echo "   2. BU Work Items  (BU* items sorted by number)"
echo "   3. Updates        (all other in-progress items)"
echo "   4. Bugs and Fixes"
echo "   5. Blocked / On Hold"
echo "   6. CI Failures"
echo "   7. Done"
echo ""

$PYTHON monday_summary_with_previous_updates.py

if [ $? -eq 0 ]; then
    echo ""
    echo "╔════════════════════════════════════════════════════════════╗"
    echo "║           ✅ PowerPoint Created with BU Grouping!         ║"
    echo "╚════════════════════════════════════════════════════════════╝"
    echo ""

    # Find the most recent generated file
    LATEST_PPT=$(ls -t monday_updates_comparison_*.pptx 2>/dev/null | head -1)
    if [ -n "$LATEST_PPT" ]; then
        echo "📁 Generated: $LATEST_PPT"
        echo ""

        if [[ "$OSTYPE" == "darwin"* ]]; then
            read -p "📊 Open PowerPoint now? (y/n) " -n 1 -r
            echo ""
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                open "$LATEST_PPT"
                echo "✅ Opened $LATEST_PPT"
            fi
        fi
    fi
else
    echo ""
    echo "⚠️  PowerPoint generation failed. HTML report is still available."
    echo "   Run: open monday_status_report.html"
    exit 1
fi

echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║                  🎉 Sync Complete!                        ║"
echo "╚════════════════════════════════════════════════════════════╝"

# Made with Bob
