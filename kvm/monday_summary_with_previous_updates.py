#!/usr/bin/env python3
"""
Monday.com Summary Generator with Previous and Current Updates Columns
Shows both the previous week's updates and current week's updates side-by-side
with AI-powered categorization (COMPLETED/NEXT/BLOCKERS)
Can import notes from previous PowerPoint presentations
"""

import requests
import json
import re
from datetime import datetime
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.enum.text import PP_ALIGN, MSO_VERTICAL_ANCHOR
from pptx.dml.color import RGBColor
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from email_to_name_mapper import convert_email_to_name
from monday_summary_ai_analysis import parse_update_into_bullets, format_categorized_bullets

# Path to previous presentation for importing item text
PREVIOUS_PPTX_PATH = os.path.join(os.path.dirname(__file__), "KVM Status Only.pptx")
PREVIOUS_NOTES_JSON = os.path.join(os.path.dirname(__file__), "extracted_item_text.json")

# Monday.com API configuration
API_TOKEN = "eyJhbGciOiJIUzI1NiJ9.eyJ0aWQiOjYyOTQxMTE0NywiYWFpIjoxMSwidWlkIjo1MDkyMjk2MSwiaWFkIjoiMjAyNi0wMy0wNVQxNjoxNzozOC4wMDBaIiwicGVyIjoibWU6d3JpdGUiLCJhY3RpZCI6MTM1MzY5ODEsInJnbiI6InVzZTEifQ.swejQV61Cb4d7VEFTww2nBDnpUt19U05NTHbb9lpg9g"
API_URL = "https://api.monday.com/v2"
BOARD_ID = "18402712591"

headers = {
    "Authorization": API_TOKEN,
    "Content-Type": "application/json"
}

COLUMN_MAP = {}
LABEL_SETTINGS = {}  # Store label settings (colors and names)


def hex_to_rgb(hex_color):
    """Convert hex color to RGB tuple"""
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


def get_label_settings():
    """Fetch label column settings to get color mappings"""
    query = f"""
    query {{
        boards(ids: {BOARD_ID}) {{
            columns(ids: "color_mm28vyxv") {{
                id
                title
                type
                settings_str
            }}
        }}
    }}
    """
    
    response = requests.post(API_URL, json={"query": query}, headers=headers)
    data = response.json()
    
    if "errors" in data or not data.get("data", {}).get("boards"):
        return {}
    
    columns = data["data"]["boards"][0].get("columns", [])
    if not columns:
        return {}
    
    settings_str = columns[0].get("settings_str", "{}")
    settings = json.loads(settings_str)
    
    # Extract label names and colors
    label_info = {}
    labels = settings.get("labels", {})
    label_colors = settings.get("labels_colors", {})
    
    for label_id, label_name in labels.items():
        color_info = label_colors.get(label_id, {})
        hex_color = color_info.get("color", "#000000")
        label_info[int(label_id)] = {
            "name": label_name,
            "color": hex_to_rgb(hex_color)
        }
    
    return label_info


def get_board_items_with_updates():
    """Fetch all board items with column information"""
    query = f"""
    query {{
        boards(ids: {BOARD_ID}) {{
            id
            name
            columns {{
                id
                title
                type
            }}
            items_page(limit: 100) {{
                items {{
                    id
                    name
                    column_values {{
                        id
                        text
                        value
                    }}
                }}
            }}
        }}
    }}
    """
    
    response = requests.post(API_URL, json={"query": query}, headers=headers)
    data = response.json()
    
    if "errors" in data:
        print("API Errors:")
        print(json.dumps(data["errors"], indent=2))
        return None
    
    boards = data.get("data", {}).get("boards", [])
    if not boards:
        return None
        
    board = boards[0]
    
    # Build column map
    global COLUMN_MAP
    for col in board.get("columns", []):
        COLUMN_MAP[col["id"]] = col["title"]
    
    # Load label settings
    global LABEL_SETTINGS
    LABEL_SETTINGS = get_label_settings()
    if LABEL_SETTINGS:
        print(f"✅ Loaded {len(LABEL_SETTINGS)} label definitions")
    
    return board


def get_updates_columns_by_date(item):
    """
    Find all 'Updates MM/DD' columns and 'is Current (MM/DD)' columns and return them sorted by date (most recent first)
    Returns list of tuples: (date_obj, column_text, column_title)
    Supports both single-digit and double-digit month/day formats (e.g., "6/15" and "06/15")
    """
    date_columns = []
    
    for col in item.get("column_values", []):
        col_id = col.get("id", "")
        col_text = col.get("text", "")
        col_title = COLUMN_MAP.get(col_id, "")
        
        # Match pattern like "Updates 05/04", "Updates 04/27", or "Updates 6/15" (single or double digit)
        match = re.match(r'Updates\s+(\d{1,2})/(\d{1,2})', col_title, re.IGNORECASE)
        if not match:
            # Also match pattern like "is Current (05/11)" or "is Current (6/15)" with parentheses
            match = re.match(r'is\s+Current\s+\((\d{1,2})/(\d{1,2})\)', col_title, re.IGNORECASE)
        if not match:
            # Also match pattern like "is Current 05/11" or "is Current 6/15" without parentheses
            match = re.match(r'is\s+Current\s+(\d{1,2})/(\d{1,2})', col_title, re.IGNORECASE)
        if not match:
            # Also match pattern like "Current (05/11)", "Current 05/11", "Current (6/15)", or "Current 6/15"
            match = re.match(r'Current\s+[\(]?(\d{1,2})/(\d{1,2})[\)]?', col_title, re.IGNORECASE)
        if not match:
            # Also match pattern like "Current Updates 05/11" or "Current Updates 6/15"
            match = re.match(r'Current\s+Updates?\s+(\d{1,2})/(\d{1,2})', col_title, re.IGNORECASE)
        
        if match and col_text and col_text.strip() and col_text.strip().lower() != "n/a":
            month, day = match.groups()
            try:
                # Use current year for date comparison
                date_obj = datetime(datetime.now().year, int(month), int(day))
                date_columns.append((date_obj, col_text, col_title))
            except ValueError:
                continue
    
    # Sort by date, most recent first
    date_columns.sort(reverse=True)
    return date_columns


def get_column_value(item, column_name):
    """Extract column value by name"""
    for col in item.get("column_values", []):
        col_id = col.get("id", "")
        col_title = COLUMN_MAP.get(col_id, "")
        
        if column_name.lower() in col_title.lower():
            return col.get("text", "")
    return None


def get_status(item):
    """Extract status"""
    for col in item.get("column_values", []):
        col_id = col.get("id", "")
        if col_id == "project_status":
            return col.get("text", "")
    return ""


def get_owner(item):
    """Extract owner"""
    for col in item.get("column_values", []):
        col_id = col.get("id", "")
        if col_id == "project_owner":
            text = col.get("text", "")
            if text:
                return convert_email_to_name(text)
    return "Unassigned"


def extract_vs_id(name):
    """Extract VS ID from item name"""
    match = re.search(r'VS\d+', name, re.IGNORECASE)
    return match.group(0).upper() if match else None


def get_feature(item):
    """Extract feature/component (QEMU, Kernel, etc.) from item"""
    for col in item.get("column_values", []):
        col_id = col.get("id", "")
        col_title = COLUMN_MAP.get(col_id, "")
        # Look for columns that might contain feature/component info
        if "feature" in col_title.lower() or "component" in col_title.lower():
            text = col.get("text", "")
            if text:
                return text
    
    # If no explicit feature column, try to infer from item name or other fields
    item_name = item.get('name', '').lower()
    if 'qemu' in item_name and 'kernel' in item_name:
        return "QEMU & Kernel"
    elif 'qemu' in item_name:
        return "QEMU"
    elif 'kernel' in item_name:
        return "Kernel"
    
    return ""


def get_label(item):
    """Extract label information from item"""
    for col in item.get("column_values", []):
        col_id = col.get("id", "")
        if col_id == "color_mm28vyxv":  # Label column ID
            text = col.get("text", "")
            value_str = col.get("value", "")
            
            if text and value_str:
                try:
                    value = json.loads(value_str)
                    label_index = value.get("index")
                    
                    if label_index is not None and label_index in LABEL_SETTINGS:
                        label_info = LABEL_SETTINGS[label_index]
                        return {
                            "name": label_info["name"],
                            "color": label_info["color"]
                        }
                except (json.JSONDecodeError, KeyError):
                    pass
            
            # Fallback: just return the text without color
            if text:
                return {"name": text, "color": (128, 128, 128)}  # Gray default
    
    return None


def lighten_color(rgb_tuple, factor=0.5):
    """Lighten an RGB color by mixing with white"""
    r, g, b = rgb_tuple
    # Mix with white (255, 255, 255)
    r = int(r + (255 - r) * factor)
    g = int(g + (255 - g) * factor)
    b = int(b + (255 - b) * factor)
    return (r, g, b)


def load_previous_item_text():
    """Load Item column text with formatting from previous PowerPoint presentation"""
    # If JSON doesn't exist or we want fresh data, extract from PowerPoint
    if os.path.exists(PREVIOUS_PPTX_PATH):
        try:
            print(f"Extracting item text with formatting from: {PREVIOUS_PPTX_PATH}")
            prs = Presentation(PREVIOUS_PPTX_PATH)
            item_data = {}
            
            for slide_idx in range(len(prs.slides)):
                slide = prs.slides[slide_idx]
                
                for shape in slide.shapes:
                    if shape.has_table:
                        table = shape.table
                        headers = [cell.text.strip() for cell in table.rows[0].cells]
                        
                        if 'Item' not in headers:
                            continue
                        
                        item_col = headers.index('Item')
                        
                        for row_idx in range(1, len(table.rows)):
                            item_cell = table.rows[row_idx].cells[item_col]
                            item_cell_text = item_cell.text.strip()
                            
                            if not item_cell_text:
                                continue
                            
                            # Extract just the item name (first line) as the key
                            item_name = item_cell_text.split('\n')[0].strip()
                            # Remove 'link' from the key if present
                            item_name = item_name.replace('link', '').strip()
                            
                            # Store the cell reference for formatting
                            item_data[item_name] = {
                                'cell': item_cell,
                                'text': item_cell_text,
                                'slide': slide_idx + 1
                            }
            
            print(f"Extracted item text with formatting from {len(item_data)} items")
            return item_data
            
        except Exception as e:
            print(f"Warning: Could not extract item text from PowerPoint: {e}")
    
    return {}


def apply_formatted_text_to_cell(cell, source_cell, lighten_colors=True):
    """Copy formatted text from source cell to target cell with optional color lightening"""
    cell.text = ""  # Clear existing text
    text_frame = cell.text_frame
    text_frame.word_wrap = True
    
    # Copy each paragraph with formatting
    for para_idx, source_para in enumerate(source_cell.text_frame.paragraphs):
        if para_idx == 0:
            target_para = text_frame.paragraphs[0]
        else:
            target_para = text_frame.add_paragraph()
        
        # Copy paragraph-level formatting
        target_para.alignment = source_para.alignment
        target_para.level = source_para.level
        
        # Copy each run with formatting
        for run_idx, source_run in enumerate(source_para.runs):
            if run_idx == 0 and para_idx == 0:
                target_run = target_para.runs[0] if target_para.runs else target_para.add_run()
            else:
                target_run = target_para.add_run()
            
            target_run.text = source_run.text
            
            # Copy font formatting
            if source_run.font.size:
                target_run.font.size = Pt(9)  # Use consistent size
            if source_run.font.name:
                target_run.font.name = source_run.font.name
            if source_run.font.bold is not None:
                target_run.font.bold = source_run.font.bold
            if source_run.font.italic is not None:
                target_run.font.italic = source_run.font.italic
            
            # Copy hyperlinks
            if source_run.hyperlink and source_run.hyperlink.address:
                target_run.hyperlink.address = source_run.hyperlink.address
            
            # Copy and lighten colors
            if source_run.font.color.type == 1:  # RGB color
                rgb = source_run.font.color.rgb
                if lighten_colors:
                    # Lighten the color
                    lightened = lighten_color((rgb[0], rgb[1], rgb[2]), factor=0.4)
                    target_run.font.color.rgb = RGBColor(*lightened)
                else:
                    target_run.font.color.rgb = RGBColor(rgb[0], rgb[1], rgb[2])


def normalize_item_name(name):
    """Normalize item name for matching by removing extra spaces in VS IDs"""
    import re
    # Replace "VS ####" with "VS####" (remove space between VS and number)
    return re.sub(r'VS\s+(\d+)', r'VS\1', name)


def get_item_display_text(item, previous_items=None):
    """Get the display text for an item, using previous presentation text if available"""
    item_name = item.get('name', '')
    normalized_current = normalize_item_name(item_name)
    
    # If we have previous item data, try to use it
    if previous_items:
        # Try exact match first
        if item_name in previous_items:
            return previous_items[item_name]
        
        # Try normalized match
        for prev_item_name, prev_data in previous_items.items():
            normalized_prev = normalize_item_name(prev_item_name)
            if normalized_current == normalized_prev:
                return prev_data
        
        # Try partial match (for items with similar names)
        for prev_item_name, prev_data in previous_items.items():
            # Check if VS ID matches
            vs_id = extract_vs_id(item_name)
            if vs_id and vs_id in prev_item_name:
                return prev_data
    
    # If no match found, return None (will use current item name)
    return None


def extract_notes(item):
    """Extract notes from item"""
    for col in item.get("column_values", []):
        col_id = col.get("id", "")
        col_title = COLUMN_MAP.get(col_id, "")
        if "note" in col_title.lower():
            return col.get("text", "")
    return ""


def create_presentation_with_previous_updates(board_data):
    """Create PowerPoint with Previous Updates and Current Updates columns across multiple slides"""
    prs = Presentation()
    # Set to 16:9 widescreen format (standard for modern displays)
    prs.slide_width = Inches(13.333)  # 16:9 aspect ratio
    prs.slide_height = Inches(7.5)
    
    items = board_data.get("items_page", {}).get("items", [])
    
    print(f"\nProcessing {len(items)} items...")
    
    # Load previous item text from PowerPoint
    print("\nLoading previous item text from PowerPoint...")
    previous_items = load_previous_item_text()
    if previous_items:
        print(f"✅ Loaded item text for {len(previous_items)} items from previous presentation")
    else:
        print("⚠️  No previous item text found")
    
    # First, determine the current and previous dates from ALL available update columns
    # by looking at column titles (not just columns with data)
    all_update_columns = []
    for col_id, col_title in COLUMN_MAP.items():
        # Match pattern like "Updates 05/04", "Updates 04/27", or "Updates 6/15" (single or double digit)
        match = re.match(r'Updates\s+(\d{1,2})/(\d{1,2})', col_title, re.IGNORECASE)
        if not match:
            # Also match pattern like "is Current (05/11)" or "is Current (6/15)" with parentheses
            match = re.match(r'is\s+Current\s+\((\d{1,2})/(\d{1,2})\)', col_title, re.IGNORECASE)
        if not match:
            # Also match pattern like "is Current 05/11" or "is Current 6/15" without parentheses
            match = re.match(r'is\s+Current\s+(\d{1,2})/(\d{1,2})', col_title, re.IGNORECASE)
        if not match:
            # Also match pattern like "Current (05/11)", "Current 05/11", "Current (6/15)", or "Current 6/15"
            match = re.match(r'Current\s+[\(]?(\d{1,2})/(\d{1,2})[\)]?', col_title, re.IGNORECASE)
        if not match:
            # Also match pattern like "Current Updates 05/11" or "Current Updates 6/15"
            match = re.match(r'Current\s+Updates?\s+(\d{1,2})/(\d{1,2})', col_title, re.IGNORECASE)
        
        if match:
            month, day = match.groups()
            try:
                date_obj = datetime(datetime.now().year, int(month), int(day))
                all_update_columns.append((date_obj, col_title))
            except ValueError:
                continue
    
    # Sort by date, most recent first
    all_update_columns.sort(reverse=True)
    
    # Set current and previous dates from available columns
    current_date = None
    previous_date = None
    if len(all_update_columns) >= 1:
        date_match = re.search(r'(\d{2}/\d{2})', all_update_columns[0][1])
        current_date = date_match.group(1) if date_match else all_update_columns[0][1].replace("Updates ", "")
        print(f"\n✅ Current date column: {all_update_columns[0][1]} → {current_date}")
    if len(all_update_columns) >= 2:
        date_match = re.search(r'(\d{2}/\d{2})', all_update_columns[1][1])
        previous_date = date_match.group(1) if date_match else all_update_columns[1][1].replace("Updates ", "")
        print(f"✅ Previous date column: {all_update_columns[1][1]} → {previous_date}")
    
    # Include ALL items (even those without updates)
    items_with_updates = []
    items_without_updates = []
    
    for item in items:
        updates_columns = get_updates_columns_by_date(item)
        if updates_columns:
            items_with_updates.append(item)
        else:
            # Include items without updates too
            items_without_updates.append(item)
    
    # Combine all items
    all_items_to_show = items_with_updates + items_without_updates
    
    print(f"Found {len(items_with_updates)} items with updates")
    print(f"Found {len(items_without_updates)} items without updates")
    print(f"Total items to display: {len(all_items_to_show)}")
    print(f"Previous date: {previous_date}, Current date: {current_date}")
    
    # Title slide
    title_slide_layout = prs.slide_layouts[0]
    slide = prs.slides.add_slide(title_slide_layout)
    title = slide.shapes.title
    subtitle = slide.placeholders[1]
    
    title.text = "US KVM & Linux Status"
    subtitle.text = f"{datetime.now().strftime('%B %d, %Y')}\nBy Kennedy Cheruiyot"
    
    # Categorize items - separate bringup/tools, bugs/fixes (incl. BU* cases), blocked/on hold, done, CI failures, and other items
    bringup_items = []
    bug_items = []      # Includes BU* bug cases (grouped together at the end of this section)
    blocked_items = []
    done_items = []
    ci_failure_items = []
    other_items = []

    bu_items = []       # BU* cases collected separately so they can be sorted, then appended to bug_items

    for item in all_items_to_show:
        item_name = item['name'].lower()
        item_name_raw = item['name']
        status = get_status(item).lower()

        # Check if it's a CI failure item (starts with test_) - track separately
        if item_name.startswith('test_'):
            ci_failure_items.append(item)
        # Check if it's blocked or on hold (by status)
        elif 'blocked' in status or 'on hold' in status or 'stuck' in status:
            blocked_items.append(item)
        # Check if it's done/completed (excluding CI failures which are tracked separately)
        elif 'done' in status or 'integrated' in status or 'completed' in status:
            done_items.append(item)
        # Check if it's a bringup/tools item
        elif 'io1814' in item_name or 'bring-up setup' in item_name or 'bringup' in item_name:
            bringup_items.append(item)
        # BU* bug cases (BUZ*, BU<digits>, BU-<digits>) — collect separately to sort, then add to bug_items
        elif re.match(r'^BU[Z\d\-]', item_name_raw, re.IGNORECASE):
            bu_items.append(item)
        # Other bug/fix items (contains 'bug', starts with 'bz', contains 'rhbz', or s390-tools/zipl related)
        elif ('bug' in item_name or item_name.startswith('bz') or 'rhbz' in item_name or
              's390-tools' in item_name or 'zipl' in item_name):
            bug_items.append(item)
        else:
            other_items.append(item)

    # Sort BU items numerically (strip leading letters after BU, e.g. BUZ217146 → 217146)
    def bu_sort_key(item):
        m = re.search(r'(\d+)', item['name'])
        return int(m.group(1)) if m else 0
    bu_items.sort(key=bu_sort_key)

    # Append BU* items after other bug items so they are grouped at the end of Bugs and Fixes
    bug_items = bug_items + bu_items

    print(f"\nCategorization:")
    print(f"  Bringup and tools: {len(bringup_items)} items")
    print(f"  Bugs and Fixes:    {len(bug_items)} items  (incl. {len(bu_items)} BU* cases)")
    print(f"  Blocked/On Hold:   {len(blocked_items)} items")
    print(f"  Done:              {len(done_items)} items")
    print(f"  CI Failures:       {len(ci_failure_items)} items")
    print(f"  Other items:       {len(other_items)} items")
    
    # Helper function to create slides for a group of items
    def create_slides_for_group(items_list, section_title):
        items_per_slide = 3
        total_items = len(items_list)
        
        for start_idx in range(0, total_items, items_per_slide):
            end_idx = min(start_idx + items_per_slide, total_items)
            slide_items = items_list[start_idx:end_idx]
            
            blank_slide_layout = prs.slide_layouts[6]
            slide = prs.slides.add_slide(blank_slide_layout)
            
            # Add title only for specific sections (not for "Updates")
            if section_title != "Updates":
                # Centered title at top
                title_box = slide.shapes.add_textbox(Inches(0.1), Inches(0.05), Inches(13.233), Inches(0.35))
                title_frame = title_box.text_frame
                title_frame.text = section_title
                title_para = title_frame.paragraphs[0]
                title_para.font.size = Pt(20)
                title_para.font.bold = True
                title_para.alignment = PP_ALIGN.CENTER  # Center the title
                table_top = Inches(0.45)
                available_height = 7.05  # Slide height (7.5) - top margin (0.45)
            else:
                # No title for regular updates section
                table_top = Inches(0.05)
                available_height = 7.45  # Slide height (7.5) - top margin (0.05)
            
            # Table - full width for 16:9 widescreen
            rows = len(slide_items) + 1
            cols = 7  # Item, Feature, Owner, Status, Previous Updates, Current Updates, Notes
            
            left = Inches(0)
            top = table_top
            width = Inches(13.333)  # Full 16:9 widescreen width
            
            # Calculate row heights to fill available space perfectly
            header_height_val = 0.45
            # Calculate exact row height to fill remaining space
            remaining_height = available_height - header_height_val
            row_height_val = remaining_height / len(slide_items)
            
            # Use exact available height to fill slide
            height = Inches(available_height)
            
            table = slide.shapes.add_table(rows, cols, left, top, width, height).table
            
            # Set exact row heights
            table.rows[0].height = Inches(header_height_val)
            for i in range(1, rows):
                table.rows[i].height = Inches(row_height_val)
            
            # Adjust column widths to fill full 16:9 width (total = 13.333")
            table.columns[0].width = Inches(2.3)   # Item
            table.columns[1].width = Inches(0.75)  # Feature (slightly wider)
            table.columns[2].width = Inches(0.9)   # Owner
            table.columns[3].width = Inches(0.8)   # Status
            table.columns[4].width = Inches(3.0)   # Previous (narrower)
            table.columns[5].width = Inches(4.45)  # Current (adjusted)
            table.columns[6].width = Inches(1.133) # Notes
            
            # Header row with dates - centered
            headers = ["Item", "Feature", "Owner", "Status",
                       f"Previous ({previous_date})" if previous_date else "Previous Updates",
                       f"Current ({current_date})" if current_date else "Current Updates",
                       "Notes"]
            for col_idx, header in enumerate(headers):
                cell = table.cell(0, col_idx)
                cell.text = header
                cell.fill.solid()
                cell.fill.fore_color.rgb = RGBColor(68, 114, 196)
                paragraph = cell.text_frame.paragraphs[0]
                paragraph.font.bold = True
                paragraph.font.size = Pt(10)
                paragraph.font.name = 'Calibri'
                paragraph.font.color.rgb = RGBColor(255, 255, 255)
                paragraph.alignment = PP_ALIGN.CENTER  # Center the headers
                cell.vertical_anchor = MSO_VERTICAL_ANCHOR.MIDDLE
            
            # Data rows
            for row_idx, item in enumerate(slide_items, start=1):
                # Item name (use previous presentation text with formatting if available)
                cell = table.cell(row_idx, 0)
                prev_item_data = get_item_display_text(item, previous_items)
                
                if prev_item_data and 'cell' in prev_item_data:
                    # Copy formatted text from previous presentation with lightened colors
                    apply_formatted_text_to_cell(cell, prev_item_data['cell'], lighten_colors=True)
                else:
                    # Use current item name with default formatting
                    cell.text = item.get('name', '')
                    for paragraph in cell.text_frame.paragraphs:
                        paragraph.font.size = Pt(9)
                        paragraph.font.name = 'Calibri'
                        paragraph.font.bold = True
                        paragraph.alignment = PP_ALIGN.LEFT  # Left align item text
                
                # Add label below item name with colored text (bold and highlighted)
                label_info = get_label(item)
                if label_info:
                    # Add a new paragraph for the label
                    label_paragraph = cell.text_frame.add_paragraph()
                    label_run = label_paragraph.add_run()
                    label_run.text = "▶ " + label_info["name"]  # Add arrow for emphasis
                    label_run.font.size = Pt(9)  # Slightly larger for better visibility
                    label_run.font.name = 'Calibri'
                    label_run.font.bold = True
                    
                    # Set the label color with enhanced distinctive colors
                    label_name = label_info["name"].lower()
                    if "10.3" in label_name:
                        # KVM RHEL 10.3 - Bright Orange/Red
                        label_run.font.color.rgb = RGBColor(255, 69, 0)  # Orange Red
                    elif "10.4" in label_name:
                        # KVM RHEL 10.4 - Bright Blue
                        label_run.font.color.rgb = RGBColor(0, 100, 255)  # Dodger Blue
                    elif "10.5" in label_name:
                        # KVM RHEL 10.5 - Bright Purple
                        label_run.font.color.rgb = RGBColor(138, 43, 226)  # Blue Violet
                    elif "tooling" in label_name or "bringup" in label_name:
                        # Tooling & Bringup - Dark Orange
                        label_run.font.color.rgb = RGBColor(255, 140, 0)  # Dark Orange
                    elif "test" in label_name:
                        # Test-related - Teal
                        label_run.font.color.rgb = RGBColor(0, 128, 128)  # Teal
                    else:
                        # Use original color from Monday.com but make it more vibrant
                        orig_color = label_info["color"]
                        # Increase saturation by 20%
                        r, g, b = orig_color
                        label_run.font.color.rgb = RGBColor(
                            min(255, int(r * 1.2)),
                            min(255, int(g * 1.2)),
                            min(255, int(b * 1.2))
                        )
                    
                    label_paragraph.space_before = Pt(2)
                    label_paragraph.alignment = PP_ALIGN.LEFT  # Left align label text
                
                cell.text_frame.word_wrap = True
                cell.vertical_anchor = MSO_VERTICAL_ANCHOR.MIDDLE
                
                # Feature (smaller font with colored text)
                cell = table.cell(row_idx, 1)
                feature = get_feature(item)
                cell.text = feature if feature else ""
                
                for paragraph in cell.text_frame.paragraphs:
                    paragraph.font.size = Pt(7)  # Smaller font
                    paragraph.font.name = 'Calibri'
                    paragraph.alignment = PP_ALIGN.CENTER
                    paragraph.font.bold = True  # Make feature text bold
                    
                    # Apply font color based on feature type
                    if feature:
                        feature_lower = feature.lower()
                        # Check for Kernel & QEMU & Libvirt first (most specific)
                        if 'libvirt' in feature_lower and 'qemu' in feature_lower and 'kernel' in feature_lower:
                            # Kernel & QEMU & Libvirt - Dark Magenta/Violet
                            paragraph.font.color.rgb = RGBColor(148, 0, 211)  # Dark Violet
                        elif 'qemu' in feature_lower and 'kernel' in feature_lower:
                            # QEMU & Kernel - Purple
                            paragraph.font.color.rgb = RGBColor(128, 0, 128)
                        elif 'libvirt' in feature_lower:
                            # Libvirt - Green
                            paragraph.font.color.rgb = RGBColor(0, 128, 0)
                        elif 'qemu' in feature_lower:
                            # QEMU - Blue
                            paragraph.font.color.rgb = RGBColor(0, 112, 192)
                        elif 'kernel' in feature_lower:
                            # Kernel - Red
                            paragraph.font.color.rgb = RGBColor(192, 0, 0)
                        elif 'tooling' in feature_lower or 'tools' in feature_lower:
                            # Tooling - Orange
                            paragraph.font.color.rgb = RGBColor(255, 102, 0)
                        elif 'bring' in feature_lower:
                            # Bring-up - Dark Yellow/Gold
                            paragraph.font.color.rgb = RGBColor(204, 153, 0)
                        else:
                            # Other - Dark Gray
                            paragraph.font.color.rgb = RGBColor(89, 89, 89)
                
                cell.text_frame.word_wrap = True
                cell.vertical_anchor = MSO_VERTICAL_ANCHOR.MIDDLE
                
                # Owner
                cell = table.cell(row_idx, 2)
                cell.text = get_owner(item)
                for paragraph in cell.text_frame.paragraphs:
                    paragraph.font.size = Pt(9)
                    paragraph.font.name = 'Calibri'
                    paragraph.alignment = PP_ALIGN.LEFT
                cell.text_frame.word_wrap = True
                cell.vertical_anchor = MSO_VERTICAL_ANCHOR.MIDDLE
                
                # Status
                cell = table.cell(row_idx, 3)
                status = get_status(item)
                cell.text = status
                for paragraph in cell.text_frame.paragraphs:
                    paragraph.font.size = Pt(9)
                    paragraph.font.name = 'Calibri'
                    paragraph.font.bold = True
                    paragraph.alignment = PP_ALIGN.LEFT
                cell.text_frame.word_wrap = True
                cell.vertical_anchor = MSO_VERTICAL_ANCHOR.MIDDLE
                
                # Color code status with lighter background colors
                if "done" in status.lower() or "integrated" in status.lower():
                    cell.fill.solid()
                    cell.fill.fore_color.rgb = RGBColor(220, 255, 220)  # Lighter green
                elif "upstream" in status.lower():
                    cell.fill.solid()
                    cell.fill.fore_color.rgb = RGBColor(230, 245, 255)  # Light blue
                elif "blocked" in status.lower() or "stuck" in status.lower():
                    cell.fill.solid()
                    cell.fill.fore_color.rgb = RGBColor(255, 220, 220)  # Lighter red
                elif "review" in status.lower():
                    cell.fill.solid()
                    cell.fill.fore_color.rgb = RGBColor(255, 245, 220)  # Lighter orange
                elif "in progress" in status.lower() or "working" in status.lower():
                    cell.fill.solid()
                    cell.fill.fore_color.rgb = RGBColor(255, 255, 220)  # Light yellow
                
                # Get updates columns sorted by date
                updates_columns = get_updates_columns_by_date(item)
                
                # Previous Updates (second most recent) - with AI formatting and dimmed text
                cell = table.cell(row_idx, 4)
                cell.text = ""
                text_frame = cell.text_frame
                text_frame.word_wrap = True
                cell.vertical_anchor = MSO_VERTICAL_ANCHOR.MIDDLE  # Center vertically
                
                if len(updates_columns) >= 2:
                    previous_update = updates_columns[1][1]  # Get text from second item
                    previous_update_date = updates_columns[1][2].replace("Updates ", "")  # e.g., "04/27"
                    
                    # Check if date is different from column header
                    date_is_different = previous_date and previous_update_date != previous_date
                    
                    # Parse and format with AI
                    categorized = parse_update_into_bullets(previous_update)
                    formatted = format_categorized_bullets(categorized, use_emojis=False, max_items_per_category=5, max_chars_per_item=500)
                    
                    lines = formatted.strip().split('\n')
                    for idx, line in enumerate(lines):
                        if idx == 0:
                            p = text_frame.paragraphs[0]
                            if date_is_different:
                                # Add prominent date prefix with warning styling
                                p.text = f"⚠️ DATE: {previous_update_date} ⚠️\n"
                                p.font.size = Pt(9)  # Slightly larger
                                p.font.name = 'Calibri'
                                p.font.bold = True
                                p.font.color.rgb = RGBColor(255, 0, 0)  # Red for high visibility
                                p.alignment = PP_ALIGN.LEFT
                                # Add the rest of the line in a new run
                                run = p.add_run()
                                run.text = line
                                run.font.size = Pt(8)
                                run.font.name = 'Calibri'
                                # Color the section header (dimmed for previous updates)
                                if line.startswith('COMPLETED LAST WEEK'):
                                    run.font.bold = True
                                    run.font.color.rgb = RGBColor(100, 150, 100)  # Dimmed green
                                elif line.startswith('CURRENTLY WORKING ON'):
                                    run.font.bold = True
                                    run.font.color.rgb = RGBColor(100, 140, 180)  # Dimmed blue
                                elif line.startswith('BLOCKERS'):
                                    run.font.bold = True
                                    run.font.color.rgb = RGBColor(180, 100, 100)  # Dimmed red
                                else:
                                    run.font.color.rgb = RGBColor(128, 128, 128)  # Gray for regular text
                            else:
                                p.text = line
                                p.font.size = Pt(8)
                                p.font.name = 'Calibri'
                                p.alignment = PP_ALIGN.LEFT
                                # Color the section headers (dimmed for previous updates)
                                if line.startswith('COMPLETED LAST WEEK'):
                                    p.font.bold = True
                                    p.font.color.rgb = RGBColor(100, 150, 100)  # Dimmed green
                                elif line.startswith('CURRENTLY WORKING ON'):
                                    p.font.bold = True
                                    p.font.color.rgb = RGBColor(100, 140, 180)  # Dimmed blue
                                elif line.startswith('BLOCKERS'):
                                    p.font.bold = True
                                    p.font.color.rgb = RGBColor(180, 100, 100)  # Dimmed red
                                else:
                                    p.font.color.rgb = RGBColor(128, 128, 128)  # Gray for regular text
                        else:
                            p = text_frame.add_paragraph()
                            p.text = line
                            p.font.size = Pt(8)
                            p.font.name = 'Calibri'
                            p.alignment = PP_ALIGN.LEFT
                            
                            # Color the section headers (dimmed for previous updates)
                            if line.startswith('COMPLETED LAST WEEK'):
                                p.font.bold = True
                                p.font.color.rgb = RGBColor(100, 150, 100)  # Dimmed green
                            elif line.startswith('CURRENTLY WORKING ON'):
                                p.font.bold = True
                                p.font.color.rgb = RGBColor(100, 140, 180)  # Dimmed blue
                            elif line.startswith('BLOCKERS'):
                                p.font.bold = True
                                p.font.color.rgb = RGBColor(180, 100, 100)  # Dimmed red
                            else:
                                p.font.color.rgb = RGBColor(128, 128, 128)  # Gray for regular text
                else:
                    p = text_frame.paragraphs[0]
                    p.text = "No previous updates"
                    p.font.size = Pt(8)
                
                # Current Updates (most recent) - with AI formatting
                cell = table.cell(row_idx, 5)
                cell.text = ""
                text_frame = cell.text_frame
                text_frame.word_wrap = True
                cell.vertical_anchor = MSO_VERTICAL_ANCHOR.MIDDLE  # Center vertically
                
                if len(updates_columns) >= 1:
                    current_update = updates_columns[0][1]  # Get text from first item
                    current_update_date = updates_columns[0][2].replace("Updates ", "")  # e.g., "05/04"
                    
                    # Check if date is different from column header
                    date_is_different = current_date and current_update_date != current_date
                    
                    # Parse and format with AI
                    categorized = parse_update_into_bullets(current_update)
                    formatted = format_categorized_bullets(categorized, use_emojis=False, max_items_per_category=5, max_chars_per_item=500)
                    
                    lines = formatted.strip().split('\n')
                    for idx, line in enumerate(lines):
                        if idx == 0:
                            p = text_frame.paragraphs[0]
                            if date_is_different:
                                # Add prominent date prefix with warning styling
                                p.text = f"⚠️ DATE: {current_update_date} ⚠️\n"
                                p.font.size = Pt(9)  # Slightly larger
                                p.font.name = 'Calibri'
                                p.font.bold = True
                                p.font.color.rgb = RGBColor(255, 0, 0)  # Red for high visibility
                                p.alignment = PP_ALIGN.LEFT
                                # Add the rest of the line in a new run
                                run = p.add_run()
                                run.text = line
                                run.font.size = Pt(8)
                                run.font.name = 'Calibri'
                                # Color the section header
                                if line.startswith('COMPLETED LAST WEEK'):
                                    run.font.bold = True
                                    run.font.color.rgb = RGBColor(0, 128, 0)
                                elif line.startswith('CURRENTLY WORKING ON'):
                                    run.font.bold = True
                                    run.font.color.rgb = RGBColor(0, 112, 192)
                                elif line.startswith('BLOCKERS'):
                                    run.font.bold = True
                                    run.font.color.rgb = RGBColor(192, 0, 0)
                            else:
                                p.text = line
                                p.font.size = Pt(8)
                                p.font.name = 'Calibri'
                                p.alignment = PP_ALIGN.LEFT
                                # Color the section headers
                                if line.startswith('COMPLETED LAST WEEK'):
                                    p.font.bold = True
                                    p.font.color.rgb = RGBColor(0, 128, 0)
                                elif line.startswith('CURRENTLY WORKING ON'):
                                    p.font.bold = True
                                    p.font.color.rgb = RGBColor(0, 112, 192)
                                elif line.startswith('BLOCKERS'):
                                    p.font.bold = True
                                    p.font.color.rgb = RGBColor(192, 0, 0)
                        else:
                            p = text_frame.add_paragraph()
                            p.text = line
                            p.font.size = Pt(8)
                            p.font.name = 'Calibri'
                            p.alignment = PP_ALIGN.LEFT
                            
                            # Color the section headers
                            if line.startswith('COMPLETED LAST WEEK'):
                                p.font.bold = True
                                p.font.color.rgb = RGBColor(0, 128, 0)
                            elif line.startswith('CURRENTLY WORKING ON'):
                                p.font.bold = True
                                p.font.color.rgb = RGBColor(0, 112, 192)
                            elif line.startswith('BLOCKERS'):
                                p.font.bold = True
                                p.font.color.rgb = RGBColor(192, 0, 0)
                else:
                    p = text_frame.paragraphs[0]
                    p.text = "No updates"
                    p.font.size = Pt(8)
                
                # Notes column
                cell = table.cell(row_idx, 6)
                notes = extract_notes(item)
                cell.text = notes if notes else ""
                for paragraph in cell.text_frame.paragraphs:
                    paragraph.font.size = Pt(8)
                    paragraph.font.name = 'Calibri'
                cell.text_frame.word_wrap = True
                cell.vertical_anchor = MSO_VERTICAL_ANCHOR.MIDDLE  # Center vertically
            
            # Add slide number in bottom right corner
            slide_number = len(prs.slides)
            
            # Add slide number text box in bottom right
            slide_num_box = slide.shapes.add_textbox(
                Inches(12.5),  # Right side
                Inches(7.3),   # Bottom
                Inches(0.8),   # Width
                Inches(0.15)   # Height
            )
            slide_num_frame = slide_num_box.text_frame
            slide_num_frame.text = f"{slide_number}"
            slide_num_para = slide_num_frame.paragraphs[0]
            slide_num_para.font.size = Pt(10)
            slide_num_para.font.color.rgb = RGBColor(128, 128, 128)  # Gray
            slide_num_para.alignment = PP_ALIGN.RIGHT
   
    # Create slides for each group in requested order
    # 1. Bringup and tools section
    if bringup_items:
        print(f"\nCreating slides for Bringup and tools ({len(bringup_items)} items)...")
        create_slides_for_group(bringup_items, "Bringup and Tools")

    # 2. VS* Updates (in progress items) — comes before Bugs and Fixes
    if other_items:
        print(f"\nCreating slides for Updates ({len(other_items)} items)...")
        create_slides_for_group(other_items, "Updates")

    # 3. Bugs and Fixes (non-BU bugs first, then BU* cases grouped at end)
    if bug_items:
        bu_count = len(bu_items)
        print(f"\nCreating slides for Bugs and Fixes ({len(bug_items)} items, {bu_count} BU* cases at end)...")
        create_slides_for_group(bug_items, "Bugs and Fixes")

    # 4. Blocked/On Hold section
    if blocked_items:
        print(f"\nCreating slides for Blocked/On Hold ({len(blocked_items)} items)...")
        create_slides_for_group(blocked_items, "Blocked / On Hold")

    # 5. CI Failures section
    if ci_failure_items:
        print(f"\nCreating slides for CI Failures ({len(ci_failure_items)} items)...")
        create_slides_for_group(ci_failure_items, "CI Failures")

    # 6. Done items (at the end)
    if done_items:
        print(f"\nCreating slides for Done items ({len(done_items)} items)...")
        create_slides_for_group(done_items, "Done")
    
    # Save presentation
    filename = f"monday_updates_comparison_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pptx"
    prs.save(filename)
    print(f"\n✅ Presentation saved: {filename}")
    return filename


if __name__ == "__main__":
    print("="*80)
    print("Monday.com Updates Comparison Generator")
    print("Shows Previous and Current Updates Side-by-Side")
    print("="*80)
    print()
    
    print("Fetching board data from Monday.com...")
    board_data = get_board_items_with_updates()
    
    if board_data:
        create_presentation_with_previous_updates(board_data)
        print("\n✅ Complete!")
    else:
        print("\n❌ Failed to fetch board data")

# Made with Bob
