# Monday.com Summary Generator - User Guide

## Overview
This script generates a professional PowerPoint presentation from your Monday.com board with side-by-side comparison of previous and current updates.

## Features
- ✅ Automatically detects the most recent update columns (e.g., "Updates 05/11")
- ✅ Shows Previous and Current updates side-by-side
- ✅ AI-powered categorization (COMPLETED/CURRENT WORK/BLOCKERS)
- ✅ Color-coded features (Kernel, QEMU, Libvirt, etc.)
- ✅ Distinctive label colors for different RHEL versions
- ✅ Slide numbers on each page
- ✅ Prominent date warnings when data is from different dates
- ✅ Organized sections: Bringup, Updates, Bugs, Blocked, CI Failures, Done

## Prerequisites

### 1. Python Installation
You need Python 3.7 or higher installed on your system.

**Check if Python is installed:**
```bash
python3 --version
```

**If not installed:**
- **macOS**: `brew install python3` (requires Homebrew)
- **Linux**: `sudo apt-get install python3` (Ubuntu/Debian) or `sudo yum install python3` (RHEL/CentOS)
- **Windows**: Download from [python.org](https://www.python.org/downloads/)

### 2. Required Python Packages
Install the required packages:

```bash
pip3 install requests python-pptx openai
```

Or use the requirements file:
```bash
pip3 install -r requirements.txt
```

### 3. Required Files
Make sure you have these files in the same directory:
- `monday_summary_with_previous_updates.py` (main script)
- `email_to_name_mapper.py` (email to name conversion)
- `monday_summary_ai_analysis.py` (AI analysis functions)
- `KVM Status Only.pptx` (optional - for importing previous item formatting)

## Configuration

### Monday.com API Token
The script uses a Monday.com API token that's already configured in the script. If you need to use a different board or token:

1. Go to Monday.com → Your Profile → Admin → API
2. Generate a new API token
3. Update the `API_TOKEN` variable in the script (line 30)

### Board ID
The script is configured for board ID `18402712591`. To use a different board:
1. Find your board ID in the Monday.com URL: `https://yourcompany.monday.com/boards/YOUR_BOARD_ID`
2. Update the `BOARD_ID` variable in the script (line 32)

## How to Run

### Option 1: Simple Command Line
```bash
python3 monday_summary_with_previous_updates.py
```

### Option 2: Using a Shell Script
Create a file named `run_summary.sh`:
```bash
#!/bin/bash
cd /path/to/your/directory
python3 monday_summary_with_previous_updates.py
```

Make it executable:
```bash
chmod +x run_summary.sh
```

Run it:
```bash
./run_summary.sh
```

### Option 3: Schedule Automatic Runs (Optional)
To run automatically every Monday at 9 AM:

**macOS/Linux (crontab):**
```bash
crontab -e
```
Add this line:
```
0 9 * * 1 cd /path/to/directory && python3 monday_summary_with_previous_updates.py
```

**Windows (Task Scheduler):**
1. Open Task Scheduler
2. Create Basic Task
3. Set trigger: Weekly, Monday, 9:00 AM
4. Action: Start a program
5. Program: `python3`
6. Arguments: `monday_summary_with_previous_updates.py`
7. Start in: `C:\path\to\directory`

## Output

The script generates a PowerPoint file named:
```
monday_updates_comparison_YYYYMMDD_HHMMSS.pptx
```

Example: `monday_updates_comparison_20260511_151947.pptx`

## Understanding the Output

### Slide Structure
1. **Title Slide**: "US KVM and Linux BI-Weekly Updates"
2. **Bringup and Tools**: IO1814 and setup items
3. **Updates**: In-progress work items
4. **Bugs and Fixes**: Bug-related items
5. **Blocked/On Hold**: Items that are stuck
6. **CI Failures**: Test failure items
7. **Done**: Completed items

### Column Headers
- **Item**: Work item name with label
- **Feature**: Component (Kernel, QEMU, Libvirt, etc.)
- **Owner**: Assigned person
- **Status**: Current status with color coding
- **Previous (MM/DD)**: Previous week's updates
- **Current (MM/DD)**: Current week's updates
- **Notes**: Additional notes

### Color Coding

**Feature Colors:**
- 🔴 Kernel - Red
- 🔵 QEMU - Blue
- 🟢 Libvirt - Green
- 🟪 Kernel & QEMU - Purple
- 🟣 Kernel & QEMU & Libvirt - Dark Violet
- 🟠 Tooling/Tools - Orange
- 🟡 Bring-up - Gold

**Label Colors:**
- 🔴 KVM RHEL 10.3 - Bright Orange Red
- 🔵 KVM RHEL 10.4 - Bright Blue
- 🟣 KVM RHEL 10.5 - Bright Purple
- 🟠 Tooling & Bringup - Dark Orange

**Status Colors:**
- 🟢 Done/Integrated - Light Green
- 🔵 Upstream - Light Blue
- 🔴 Blocked/Stuck - Light Red
- 🟠 Review - Light Orange
- 🟡 In Progress - Light Yellow

### Date Warnings
When an item's data is from a different date than the column header, you'll see:
```
⚠️ DATE: MM/DD ⚠️
```
This appears in **red** at the top of the update text.

## Troubleshooting

### "Module not found" Error
```bash
pip3 install requests python-pptx openai
```

### "API Error" or "Authentication Failed"
- Check that the API token is valid
- Verify you have access to the Monday.com board
- Ensure the board ID is correct

### "No items found"
- Verify the board has items with updates
- Check that update columns exist (e.g., "Updates 05/11")
- Ensure items have data in the update columns

### Script Runs but No Output
- Check the console output for error messages
- Verify you have write permissions in the directory
- Look for the generated .pptx file in the same directory as the script

### "KVM Status Only.pptx not found" Warning
This is optional. The script will work without it, but won't import previous item formatting. To fix:
- Place the previous PowerPoint file in the same directory
- Or update the `PREVIOUS_PPTX_PATH` variable in the script

## Customization

### Change Update Column Pattern
If your board uses different column names, update line 161:
```python
match = re.match(r'Updates\s+(\d{2})/(\d{2})', col_title, re.IGNORECASE)
```

### Adjust Items Per Slide
Change line 538:
```python
items_per_slide = 3  # Change to 2, 4, etc.
```

### Modify Colors
Update the color definitions in the script:
- Feature colors: Lines 665-690
- Label colors: Lines 641-665
- Status colors: Lines 717-731

## Support

For issues or questions:
1. Check the console output for error messages
2. Verify all prerequisites are installed
3. Ensure the Monday.com API token and board ID are correct
4. Contact the script maintainer with the error message

## Version History
- **v1.0** (2026-05-11): Initial release with all features

---
**Last Updated**: May 11, 2026