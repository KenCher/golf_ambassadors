#!/bin/bash
#
# Monday.com Summary Generator - Quick Run Script
# This script runs the Monday.com summary generator with proper categorization
#

echo "=========================================="
echo "Monday.com Summary Generator"
echo "=========================================="
echo ""

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: Python 3 is not installed"
    echo "Please install Python 3 first:"
    echo "  macOS: brew install python3"
    echo "  Linux: sudo apt-get install python3"
    exit 1
fi

echo "✅ Python 3 found: $(python3 --version)"
echo ""

# Check if required packages are installed
echo "Checking required packages..."
python3 -c "import requests, pptx" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "⚠️  Some required packages are missing"
    echo "Installing required packages..."
    
    # Try installing with --user flag first (works with externally-managed environments)
    pip3 install --user requests python-pptx 2>/dev/null
    
    if [ $? -ne 0 ]; then
        # If that fails, try with --break-system-packages (for Homebrew Python)
        pip3 install --break-system-packages requests python-pptx 2>/dev/null
        
        if [ $? -ne 0 ]; then
            echo ""
            echo "❌ Automatic installation failed"
            echo ""
            echo "Please install packages manually using ONE of these methods:"
            echo ""
            echo "Method 1 (Recommended - User install):"
            echo "  pip3 install --user requests python-pptx"
            echo ""
            echo "Method 2 (Homebrew Python):"
            echo "  pip3 install --break-system-packages requests python-pptx"
            echo ""
            echo "Method 3 (Virtual environment):"
            echo "  python3 -m venv venv"
            echo "  source venv/bin/activate"
            echo "  pip3 install requests python-pptx"
            echo ""
            exit 1
        fi
    fi
    
    # Verify installation worked
    python3 -c "import requests, pptx" 2>/dev/null
    if [ $? -ne 0 ]; then
        echo "❌ Package installation verification failed"
        echo "Please install manually and try again"
        exit 1
    fi
fi

echo "✅ All required packages are installed"
echo ""

# Run the summary script with previous updates comparison
echo "Running Monday.com summary generator with update history..."
echo "This will create a PowerPoint with properly categorized updates:"
echo "  • Completed Last Week: What was finished"
echo "  • Currently Working On: What's being worked on now"
echo "  • Blockers: Any blocking issues"
echo ""
python3 monday_summary_with_previous_updates.py

# Check if the script ran successfully
if [ $? -eq 0 ]; then
    echo ""
    echo "=========================================="
    echo "✅ SUCCESS!"
    echo "=========================================="
    
    # Find the most recent generated file
    LATEST_FILE=$(ls -t monday_updates_comparison_*.pptx 2>/dev/null | head -1)
    
    if [ -n "$LATEST_FILE" ]; then
        echo "Generated file: $LATEST_FILE"
        echo ""
        echo "📊 Summary Format:"
        echo "   • COMPLETED: Items finished last week"
        echo "   • CURRENT WORK: What's being worked on now"  
        echo "   • BLOCKERS: Any blocking issues (or 'None')"
        echo ""
        
        # Ask if user wants to open the file
        read -p "Would you like to open the presentation? (y/n) " -n 1 -r
        echo ""
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            # Open the file based on OS
            if [[ "$OSTYPE" == "darwin"* ]]; then
                # macOS
                open "$LATEST_FILE"
                echo "✅ Opened $LATEST_FILE"
            elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
                # Linux
                xdg-open "$LATEST_FILE" 2>/dev/null || echo "Please open $LATEST_FILE manually"
            else
                echo "Please open $LATEST_FILE manually"
            fi
        fi
    fi
else
    echo ""
    echo "=========================================="
    echo "❌ ERROR"
    echo "=========================================="
    echo "The script encountered an error. Please check the output above."
    exit 1
fi

# Made with Bob
