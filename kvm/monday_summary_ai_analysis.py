#!/usr/bin/env python3
"""
Monday.com AI-Style Summary Generator
Uses intelligent analysis to create meaningful 3-bullet summaries
instead of simple truncation
"""

import requests
import json
import re
from datetime import datetime
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.enum.text import PP_ALIGN, MSO_VERTICAL_ANCHOR
from pptx.dml.color import RGBColor
import os
from email_to_name_mapper import convert_email_to_name

# Monday.com API configuration
API_TOKEN = "eyJhbGciOiJIUzI1NiJ9.eyJ0aWQiOjYyOTQxMTE0NywiYWFpIjoxMSwidWlkIjo1MDkyMjk2MSwiaWFkIjoiMjAyNi0wMy0wNVQxNjoxNzozOC4wMDBaIiwicGVyIjoibWU6d3JpdGUiLCJhY3RpZCI6MTM1MzY5ODEsInJnbiI6InVzZTEifQ.swejQV61Cb4d7VEFTww2nBDnpUt19U05NTHbb9lpg9g"
API_URL = "https://api.monday.com/v2"
BOARD_ID = "18402712591"

headers = {
    "Authorization": API_TOKEN,
    "Content-Type": "application/json"
}

COLUMN_MAP = {}


def get_board_items_with_updates():
    """Fetch all board items"""
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
    return boards[0] if boards else None


def find_column_by_title(item, possible_titles, exact_match=False):
    """Find column by title"""
    for col in item.get("column_values", []):
        col_id = col.get("id", "")
        col_text = col.get("text", "")
        
        if not col_text or col_text.strip() == "" or col_text.strip().lower() == "n/a":
            continue
        
        col_title = COLUMN_MAP.get(col_id, "")
        
        for possible_title in possible_titles:
            if exact_match:
                if col_title and col_title.lower() == possible_title.lower():
                    return col_text
            else:
                if col_title and possible_title.lower() in col_title.lower():
                    return col_text
    return None


def get_latest_update(item):
    """Extract the latest update from the most recent 'Updates MM/DD' column"""
    import re
    from datetime import datetime
    
    # First, try to find columns with date pattern "Updates MM/DD"
    date_columns = []
    for col in item.get("column_values", []):
        col_id = col.get("id", "")
        col_text = col.get("text", "")
        col_title = COLUMN_MAP.get(col_id, "")
        
        # Match pattern like "Updates 05/04" or "Updates 04/27"
        match = re.match(r'Updates\s+(\d{2})/(\d{2})', col_title, re.IGNORECASE)
        if match and col_text and col_text.strip() and col_text.strip().lower() != "n/a":
            month, day = match.groups()
            try:
                # Use current year for date comparison
                date_obj = datetime(datetime.now().year, int(month), int(day))
                date_columns.append((date_obj, col_text, col_title))
            except ValueError:
                continue
    
    # If we found date columns, return the most recent one
    if date_columns:
        date_columns.sort(reverse=True)  # Sort by date, most recent first
        return date_columns[0][1]  # Return the text from the most recent column
    
    # Fallback to original logic if no date columns found
    # Try exact match first for "Latest Updates"
    latest_update = find_column_by_title(item, ["latest updates"], exact_match=True)
    
    if not latest_update:
        # Try "Latest Update" (singular)
        latest_update = find_column_by_title(item, ["latest update"], exact_match=True)
    
    if not latest_update:
        # Try partial match with longer strings first to avoid matching "Updates" before "Latest Updates"
        latest_update = find_column_by_title(item, ["latest"], exact_match=False)
    
    if not latest_update:
        # Last resort: try "Updates" or "Update"
        latest_update = find_column_by_title(item, ["updates", "update"], exact_match=False)
    
    return latest_update or ""


def parse_update_into_bullets(update_text):
    """
    Parse the latest update text and extract:
    - Completed: What has been completed since the last status meeting
    - Current work: What's being worked on next / now
    - Blockers: Any blockers or issues
    - Notes: Important context or notes

    Returns a dictionary with these categories.
    """
    if not update_text or update_text.strip() == "":
        return {
            "completed": [],
            "next": [],
            "blockers": [],
            "notes": []
        }

    result = {
        "completed": [],
        "next": [],
        "blockers": [],
        "notes": []
    }

    def clean_line(line, check_section_prefix=False):
        line = line.strip()
        
        # Remove leading colon and semicolon
        line = re.sub(r'^[:;]+\s*', '', line)
        
        # Remove emoji codes FIRST
        emoji_codes = [
            ':white_check_mark:', ':arrows_counterclockwise:', ':construction:',
            ':blue_book:', ':notebook:', ':book:', ':checkered_flag:'
        ]
        for emoji in emoji_codes:
            line = line.replace(emoji, '')
        
        # Remove bullet points and dashes FIRST
        line = re.sub(r'^\s*[-•*]+\s*', '', line)
        line = re.sub(r'^\s*\d+[\.)]\s*', '', line)
        
        # If checking for section prefix, extract content after section header
        if check_section_prefix:
            # Check if line starts with a section header followed by content
            section_prefix_patterns = [
                (r'^(Blockers?\s*(\(if any\))?)\s+(.+)', 3),  # "Blockers (if any) content"
                (r'^(Currently Working On|Currently Working|Current Work)\s+(.+)', 3 if r'\(' in line else 2),  # "Currently Working content"
                (r'^(Other)\s+(.+)', 2),  # "Other content"
                (r'^(Notes?)\s+(.+)', 2),  # "Notes content"
            ]
            
            for pattern, group_idx in section_prefix_patterns:
                match = re.match(pattern, line, re.IGNORECASE)
                if match:
                    # Return the content after the section header
                    return match.group(group_idx).strip()
        
        # Split on section headers that appear mid-line
        # This handles cases like "...url Currently Working On" or "...text Blockers (if any)"
        section_split_patterns = [
            r'\s+(Currently Working On|Currently Working|Current Work)\s*$',
            r'\s+(Blockers?\s*(\(if any\))?)\s*$',
            r'\s+(Other)\s*$',
            r'\s+(Notes?)\s*$'
        ]
        
        for pattern in section_split_patterns:
            match = re.search(pattern, line, re.IGNORECASE)
            if match:
                # Keep only the part before the section header
                line = line[:match.start()].strip()
                break
        
        # Clean up extra whitespace
        line = re.sub(r'\s+', ' ', line)
        
        return line.strip()

    def is_section_header(line):
        """Check if a line is a section header"""
        line_lower = line.lower().strip()
        
        # Remove emoji codes
        for emoji in [':white_check_mark:', ':arrows_counterclockwise:', ':construction:', ':blue_book:']:
            line_lower = line_lower.replace(emoji, '')
        line_lower = line_lower.strip()
        
        # Check for section headers (with or without emoji/brackets)
        section_patterns = [
            r'^completed\s+last\s+week',
            r'^completed\s+this\s+week',
            r'^completed',
            r'^currently\s+working\s+on',
            r'^currently\s+working',
            r'^current\s+work',
            r'^working\s+on',
            r'^blockers?\s*\(if\s+any\)',
            r'^blockers?',
            r'^notes?',
            r'^important\s+notes?',
            r'^other',
            r'^on\s+moving\s+forward'
        ]
        
        for pattern in section_patterns:
            if re.match(pattern, line_lower):
                return True
        return False

    def classify_section_header(line):
        """Classify which section a header belongs to"""
        line_lower = line.lower().strip()
        
        # Remove emoji codes
        for emoji in [':white_check_mark:', ':arrows_counterclockwise:', ':construction:', ':blue_book:']:
            line_lower = line_lower.replace(emoji, '')
        line_lower = line_lower.strip()

        if re.match(r'^completed', line_lower):
            return "completed"
        if re.match(r'^(currently\s+working(\s+on)?|current\s+work|working\s+on|on\s+moving\s+forward)', line_lower):
            return "next"
        if re.match(r'^blockers?', line_lower):
            return "blockers"
        if re.match(r'^(notes?|important\s+notes?|other)', line_lower):
            return "notes"
        return None

    # Pre-process: Check if text is single-line format with inline section headers
    # Format: "Completed Last Week - item1 - item2 Currently Working On - item3 Blockers - None"
    # This happens when text has no newlines but has section headers appearing inline
    if '\n' not in update_text and len(update_text) > 100:
        # Check if multiple section headers appear in the text
        text_lower = update_text.lower()
        section_count = 0
        if 'completed last week' in text_lower or 'completed this week' in text_lower:
            section_count += 1
        if 'currently working' in text_lower:
            section_count += 1
        if 'blockers' in text_lower:
            section_count += 1
        
        # If we have multiple sections in a single line, split them
        if section_count >= 2:
            # First, ensure the text starts with a section header by adding a newline at the start if needed
            if not re.match(r'^\s*(Completed Last Week|Completed This Week|Currently Working)', update_text, re.IGNORECASE):
                # Text doesn't start with a section header, add one
                update_text = 'Completed Last Week\n' + update_text
            
            # Insert newlines before section headers (but not at the very start)
            # Match section headers that have content before them
            update_text = re.sub(r'(\S)\s+(Completed Last Week|Completed This Week)\s+', r'\1\n\n\2\n', update_text, flags=re.IGNORECASE)
            update_text = re.sub(r'(\S)\s+(Currently Working On|Currently Working)\s+', r'\1\n\n\2\n', update_text, flags=re.IGNORECASE)
            update_text = re.sub(r'(\S)\s+(Blockers?\s*(\(if any\))?)\s+', r'\1\n\n\2\n', update_text, flags=re.IGNORECASE)
            update_text = re.sub(r'(\S)\s+(Other)\s+', r'\1\n\n\2\n', update_text, flags=re.IGNORECASE)
            
            # Handle the case where text starts with a section header
            update_text = re.sub(r'^(Completed Last Week|Completed This Week|Currently Working On|Currently Working)\s+', r'\1\n', update_text, flags=re.IGNORECASE)
            
            # Now split items that are separated by multiple spaces and dashes
            # Pattern: "    - item" becomes "\n- item"
            update_text = re.sub(r'\s{2,}-\s+', r'\n- ', update_text)
    
    # Pre-process: Check if text uses emoji codes as section delimiters (single-line format)
    # Format: ":white_check_mark: Completed ... :arrows_counterclockwise: Currently Working ... :construction: Blockers ..."
    if ':white_check_mark:' in update_text or ':arrows_counterclockwise:' in update_text or ':construction:' in update_text:
        # Split on emoji section markers and convert to proper format
        # Replace emoji codes with special marker that won't appear in text
        update_text = re.sub(r':white_check_mark:\s*', '\n\n###COMPLETED###\n', update_text, flags=re.IGNORECASE)
        update_text = re.sub(r':arrows_counterclockwise:\s*', '\n\n###WORKING###\n', update_text, flags=re.IGNORECASE)
        update_text = re.sub(r':construction:\s*', '\n\n###BLOCKERS###\n', update_text, flags=re.IGNORECASE)
        update_text = re.sub(r':blue_book:\s*', '\n\n###NOTES###\n', update_text, flags=re.IGNORECASE)
        
        # Remove section header text that appears after the marker
        # e.g., "###COMPLETED###\nCompleted Last Week  content" -> "###COMPLETED###\ncontent"
        update_text = re.sub(r'###COMPLETED###\s*\n\s*Completed Last Week\s+', '###COMPLETED###\n', update_text, flags=re.IGNORECASE)
        update_text = re.sub(r'###WORKING###\s*\n\s*Currently Working On\s+', '###WORKING###\n', update_text, flags=re.IGNORECASE)
        update_text = re.sub(r'###BLOCKERS###\s*\n\s*Blockers?\s*(\(if any\))?\s+', '###BLOCKERS###\n', update_text, flags=re.IGNORECASE)
        
        # Now replace markers with actual section headers
        update_text = update_text.replace('###COMPLETED###', 'Completed Last Week')
        update_text = update_text.replace('###WORKING###', 'Currently Working On')
        update_text = update_text.replace('###BLOCKERS###', 'Blockers (if any)')
        update_text = update_text.replace('###NOTES###', 'Notes')
        
        # Also split on sentence boundaries to create separate items
        # Split long sentences into separate lines for better parsing
        update_text = re.sub(r'\.\s+([A-Z])', r'.\n\1', update_text)
    
    # Remove any remaining emoji codes
    for emoji in [':white_check_mark:', ':arrows_counterclockwise:', ':construction:', ':blue_book:', ':notebook:', ':book:', ':checkered_flag:']:
        update_text = update_text.replace(emoji, ' ')
    
    # Check if the text has structured sections with headers (inline or separate lines)
    text_lower = update_text.lower()
    has_completed_section = 'completed last week' in text_lower or 'completed this week' in text_lower or re.search(r'\bcompleted\b', text_lower)
    has_working_section = 'currently working' in text_lower or 'current work' in text_lower or re.search(r'\bcurrent\b', text_lower)
    has_blockers_section = 'blockers' in text_lower or 'blocker' in text_lower
    
    if has_completed_section or has_working_section or has_blockers_section:
        # Use the structured parsing from monday_summary_with_updates.py
        # Find section positions - support multiple variations
        # Match section headers on their own line (with optional prefix like "from" and suffix like ":")
        # The key is that the section header should be the MAIN content of the line, not buried in a sentence
        completed_match = re.search(r'(^|\n)\s*(?:from\s+)?(Completed Last Week|Completed This Week|Completed)\s*:?\s*$', update_text, re.IGNORECASE | re.MULTILINE)
        working_match = re.search(r'(^|\n)\s*(Currently Working On|Currently Working|Current Work)\s*$', update_text, re.IGNORECASE | re.MULTILINE)
        # Match "Blockers" with optional colon and content on same line (e.g., "Blockers: None")
        blockers_match = re.search(r'(^|\n)\s*Blockers?\s*(\(if any\))?\s*:?', update_text, re.IGNORECASE | re.MULTILINE)
        other_match = re.search(r'\n\s*Other\s*:?\s*$', update_text, re.IGNORECASE | re.MULTILINE)
        
        if completed_match:
            # Account for the capture group - use group(2) for the actual header text
            start = completed_match.end()
            end = len(update_text)
            if working_match and working_match.start() > start:
                end = min(end, working_match.start())
            if blockers_match and blockers_match.start() > start:
                end = min(end, blockers_match.start())
            
            completed_text = update_text[start:end].strip()
            # Split by lines - handle both bulleted and non-bulleted formats
            lines = completed_text.split('\n')
            current_section = "completed"  # Track which section we're in
            
            # Check if this is an indented format (most lines start with spaces)
            # If 50% or more of lines are indented, treat as indented format
            non_empty_lines = [l for l in lines if l.strip()]
            indented_count = sum(1 for l in non_empty_lines if l.startswith('   ') or l.startswith('\t'))
            is_indented_format = len(non_empty_lines) > 0 and indented_count >= len(non_empty_lines) * 0.5
            
            for line in lines:
                # Only skip indented lines if this is NOT an indented format
                # (i.e., skip sub-bullets in bulleted lists, but not in fully indented formats)
                if not is_indented_format and (line.startswith('   ') or line.startswith('\t')):
                    continue
                
                line = line.strip()
                if not line:
                    continue
                
                # Check if line ends with a section header (switches section for next lines)
                if re.search(r'(Currently Working On|Currently Working|Current Work)\s*$', line, re.IGNORECASE):
                    # This line ends with "Currently Working On" - switch section
                    current_section = "next"
                    # Process the part before "Currently Working On"
                    cleaned = clean_line(line)
                    if cleaned and len(cleaned) >= 10:
                        result["completed"].append(cleaned)
                    continue
                
                # Check if this line contains a section header prefix (malformed update)
                # If so, extract the content and route to the correct section
                line_stripped = line.lstrip('- \t:')
                
                # Check for "Currently Working" prefix
                if re.match(r'^(Currently Working On|Currently Working|Current Work)\s+', line_stripped, re.IGNORECASE):
                    content = clean_line(line, check_section_prefix=True)
                    if content and len(content) >= 10:
                        result["next"].append(content)
                    current_section = "next"
                    continue
                
                # Check for "Blockers" prefix (with or without colon)
                if re.match(r'^Blockers?\s*(\(if any\))?\s+', line_stripped, re.IGNORECASE):
                    content = clean_line(line, check_section_prefix=True)
                    if content and len(content) >= 10 and content.lower() not in ['none', 'n/a', 'na', 'no blockers', 'nothing']:
                        result["blockers"].append(content)
                    current_section = "blockers"
                    continue
                
                # Check for "Other" or "Notes" prefix
                if re.match(r'^(Other|Notes?)\s+', line_stripped, re.IGNORECASE):
                    content = clean_line(line, check_section_prefix=True)
                    if content and len(content) >= 10:
                        result["notes"].append(content)
                    current_section = "notes"
                    continue
                
                # Otherwise, add to current section
                cleaned = clean_line(line)
                if not cleaned:
                    continue
                # Skip section headers that got captured
                cleaned_lower = cleaned.lower()
                skip_patterns = [
                    'none', 'n/a', 'na', 'no updates', 'nothing',
                    'completed last week:', 'completed this week:', 'completed:',
                    'currently working on:', 'currently working:', 'current work:',
                    'blockers:', 'blocker:', 'other:', 'notes:'
                ]
                if any(cleaned_lower.startswith(pattern) for pattern in skip_patterns):
                    continue
                # Skip very short fragments (likely incomplete)
                if len(cleaned) < 10:
                    continue
                result[current_section].append(cleaned)
        
        if working_match:
            start = working_match.end()
            end = len(update_text)
            if blockers_match and blockers_match.start() > start:
                end = blockers_match.start()
            
            working_text = update_text[start:end].strip()
            # Split by lines - handle both bulleted and non-bulleted formats
            lines = working_text.split('\n')
            
            # Check if this is an indented format (most lines start with spaces)
            non_empty_lines = [l for l in lines if l.strip()]
            indented_count = sum(1 for l in non_empty_lines if l.startswith('   ') or l.startswith('\t'))
            is_indented_format = len(non_empty_lines) > 0 and indented_count >= len(non_empty_lines) * 0.5
            
            for line in lines:
                # Only skip indented lines if this is NOT an indented format
                if not is_indented_format and (line.startswith('   ') or line.startswith('\t')):
                    continue
                
                line = line.strip()
                if not line:
                    continue
                
                cleaned = clean_line(line)
                if not cleaned:
                    continue
                # Skip section headers that got captured
                cleaned_lower = cleaned.lower()
                skip_patterns = [
                    'none', 'n/a', 'na', 'no updates', 'nothing',
                    'completed last week:', 'completed this week:', 'completed:',
                    'currently working on:', 'currently working:', 'current work:',
                    'blockers:', 'blocker:', 'other:', 'notes:'
                ]
                if any(cleaned_lower.startswith(pattern) for pattern in skip_patterns):
                    continue
                # Skip very short fragments (likely incomplete)
                if len(cleaned) < 10:
                    continue
                result["next"].append(cleaned)
        
        if blockers_match:
            start = blockers_match.end()
            end = len(update_text)
            # Check if there's an "Other" section after blockers
            if other_match and other_match.start() > start:
                end = other_match.start()
            
            blockers_text = update_text[start:end].strip()
            # Split by lines - handle both bulleted and non-bulleted formats
            lines = blockers_text.split('\n')
            
            # Check if this is an indented format (most lines start with spaces)
            non_empty_lines = [l for l in lines if l.strip()]
            indented_count = sum(1 for l in non_empty_lines if l.startswith('   ') or l.startswith('\t'))
            is_indented_format = len(non_empty_lines) > 0 and indented_count >= len(non_empty_lines) * 0.5
            
            for line in lines:
                # Only skip indented lines if this is NOT an indented format
                if not is_indented_format and (line.startswith('   ') or line.startswith('\t')):
                    continue
                
                line = line.strip()
                if not line:
                    continue
                
                # Check if line starts with "Blockers (if any)" followed by content
                cleaned = clean_line(line, check_section_prefix=True)
                if not cleaned:
                    continue
                # Skip section headers and common non-blocker phrases
                cleaned_lower = cleaned.lower()
                skip_patterns = [
                    'none', 'n/a', 'na', 'no blockers', 'nothing', 'no updates',
                    'completed last week:', 'completed this week:', 'completed:',
                    'currently working on:', 'currently working:', 'current work:',
                    'blockers:', 'blocker:', 'other:', 'notes:'
                ]
                if any(cleaned_lower.startswith(pattern) for pattern in skip_patterns):
                    continue
                # Skip very short fragments (likely incomplete)
                if len(cleaned) < 10:
                    continue
                result["blockers"].append(cleaned)
        
        # Handle "Other" section as notes
        if other_match:
            start = other_match.end()
            other_text = update_text[start:].strip()
            # Split by lines starting with dash (main bullets only, not indented)
            lines = other_text.split('\n')
            for line in lines:
                # Skip if it's indented (sub-bullet)
                if line.startswith('   ') or line.startswith('\t'):
                    continue
                # Only process lines that start with a dash at the beginning
                if line.startswith('-') or (line.startswith(' ') and line.lstrip().startswith('-') and line.index('-') <= 1):
                    cleaned = clean_line(line)
                    if not cleaned:
                        continue
                    # Skip section headers that got captured
                    cleaned_lower = cleaned.lower()
                    skip_patterns = [
                        'none', 'n/a', 'na', 'no updates', 'nothing',
                        'completed last week:', 'completed this week:', 'completed:',
                        'currently working on:', 'currently working:', 'current work:',
                        'blockers:', 'blocker:', 'other:', 'notes:'
                    ]
                    if any(cleaned_lower.startswith(pattern) for pattern in skip_patterns):
                        continue
                    # Skip very short fragments (likely incomplete)
                    if len(cleaned) < 10:
                        continue
                    result["notes"].append(cleaned)
        
        if any(result.values()):
            return result
    
    # Split into lines for fallback parsing
    lines = [line.rstrip() for line in update_text.splitlines()]
    
    # Parse line by line
    current_section = None
    saw_structured_headers = False
    
    for raw_line in lines:
        line = raw_line.strip()
        if not line:
            continue
        
        # Check if this is a section header
        if is_section_header(line):
            section = classify_section_header(line)
            if section:
                current_section = section
                saw_structured_headers = True
                continue
        
        # If we're in a section, add the line as a bullet
        if current_section:
            cleaned = clean_line(line)
            if cleaned:
                # Skip "None" entries
                normalized = cleaned.lower().strip()
                skip_patterns = [
                    "none", "n/a", "na", "no blockers", "nothing", "none."
                ]
                
                if normalized not in skip_patterns and not re.match(r'blockers?\s*[\(\[]?if\s+any[\)\]]?\s*[\]:]?\s*none\.?', normalized):
                    result[current_section].append(cleaned)

    if saw_structured_headers and any(result.values()):
        return result

    # Fallback to heuristic sentence parsing for free-form updates
    sentences = re.split(r'[.!?]\s+|\n+', update_text)
    expanded_sentences = []
    for sentence in sentences:
        if sentence.strip():
            parts = re.split(r'[,;]\s+', sentence)
            for part in parts:
                cleaned = clean_line(part)
                if cleaned and len(cleaned) > 2:
                    expanded_sentences.append(cleaned)

    completed_keywords = ['completed', 'done', 'finished', 'merged', 'integrated',
                        'resolved', 'fixed', 'implemented', 'delivered', 'achieved',
                        'successfully', 'approved', 'signed off', 'cleared', 'accepted',
                        'landed', 'committed', 'deployed', 'released', 'shipped',
                        'posted v', 'sent v', 'submitted', 'i solved', 'i fixed',
                        'i completed', 'i finished', 'i merged', 'i resolved']
    
    next_keywords = ['next', 'will', 'plan', 'planning', 'upcoming', 'scheduled',
                    'going to', 'working on', 'need to', 'todo', 'to do',
                    'in progress', 'starting', 'begin', 'continue', 'still needs',
                    'needs more', 'clean up', 'loose ends', 'investigating',
                    'i am performing', 'i am working', 'i am preparing', 'preparing']
    
    blocker_keywords = ['blocked', 'blocker', 'blocking', 'stuck',
                       'pending approval', 'delayed', 'risk', 'concern', 'challenge',
                       'dependency', 'depends on', 'cannot', "can't", 'unable',
                       'waiting for', 'waiting on', 'held up', 'blocked by', 'blocked on']

    for sentence in expanded_sentences:
        sentence_lower = sentence.lower()

        if any(keyword in sentence_lower for keyword in blocker_keywords):
            result["blockers"].append(sentence)
        elif any(keyword in sentence_lower for keyword in completed_keywords):
            result["completed"].append(sentence)
        elif any(keyword in sentence_lower for keyword in next_keywords):
            result["next"].append(sentence)
        else:
            # Only use past tense as completed if it's an action verb, not descriptive
            # Avoid classifying explanatory sentences like "The problem was that..."
            if re.search(r'\b(was|were|had|did|got)\b', sentence_lower):
                # Check if it's an explanatory sentence (starts with "the", "this", "that", "it")
                if not re.match(r'^\s*(the|this|that|it|a|an)\b', sentence_lower):
                    result["completed"].append(sentence)
                else:
                    result["next"].append(sentence)
            elif re.search(r'\b(will|shall|going|need|should|must)\b', sentence_lower):
                result["next"].append(sentence)
            else:
                result["next"].append(sentence)

    if not result["completed"] and not result["next"] and not result["blockers"] and update_text:
        result["next"].append(update_text.strip())

    return result


def format_categorized_bullets(categorized, use_emojis=False, max_items_per_category=10, max_chars_per_item=500):
    """
    Format the categorized bullets into a readable string for PowerPoint.
    Increased max_chars_per_item to 500 to avoid truncation of important updates.
    Filters out emoji-only entries like :white_check_mark:, :arrows_counterclockwise:, :construction:
    """
    if use_emojis:
        complete_label = "✅ COMPLETED LAST WEEK"
        next_label = "🔄 CURRENTLY WORKING ON"
        blockers_label = "🚫 BLOCKERS"
        notes_label = "📝 NOTES"
    else:
        complete_label = "COMPLETED LAST WEEK"
        next_label = "CURRENTLY WORKING ON"
        blockers_label = "BLOCKERS"
        notes_label = "NOTES"
    
    # Emoji codes to filter out
    emoji_only_patterns = [
        ':white_check_mark:',
        ':arrows_counterclockwise:',
        ':construction:',
        ':white_check_mark',
        ':arrows_counterclockwise',
        ':construction'
    ]
    
    def is_emoji_only(text):
        """Check if text is only emoji codes or blocker-none statements"""
        cleaned = text.strip().lower()
        # Check if it's just an emoji code
        if cleaned in emoji_only_patterns:
            return True
        # Check if it's only emoji codes with spaces/bullets
        cleaned_no_bullet = re.sub(r'^[•\-\*\s]+', '', cleaned)
        if cleaned_no_bullet in emoji_only_patterns:
            return True
        # Check if it's a blocker-none statement
        blocker_none_patterns = [
            "blockers (if any) none", "blockers if any none", "blockers: none",
            "blocker: none", "blockers - none", "blocker - none", "blockers none",
            "blockers (if any) none.", "blockers if any none.", "blockers: none.",
            "blocker: none.", "blockers - none.", "blocker - none.", "blockers none.",
            "blockers:] none", "blocker:] none", "blockers:] none.", "blocker:] none."
        ]
        if cleaned in blocker_none_patterns:
            return True
        # Check with regex for variations (with optional period and bracket at end)
        if re.match(r'blockers?\s*[\(\[]?if any[\)\]]?\s*[\]:]?\s*-?\s*none\.?', cleaned):
            return True
        return False
    
    lines = []
    
    # COMPLETED LAST WEEK section - ALWAYS show
    lines.append(complete_label)
    if categorized.get("completed"):
        # Filter out emoji-only entries
        valid_items = [item for item in categorized["completed"] if not is_emoji_only(item)]
        if valid_items:
            for item in valid_items[:max_items_per_category]:
                # Truncate if too long
                if len(item) > max_chars_per_item:
                    item = item[:max_chars_per_item-3] + "..."
                lines.append(f"  • {item}")
        else:
            lines.append("  • None")
    else:
        lines.append("  • None")
    
    # CURRENTLY WORKING ON section - ALWAYS show
    lines.append("")  # Blank line between sections
    lines.append(next_label)
    if categorized.get("next"):
        # Filter out emoji-only entries
        valid_items = [item for item in categorized["next"] if not is_emoji_only(item)]
        if valid_items:
            for item in valid_items[:max_items_per_category]:
                if len(item) > max_chars_per_item:
                    item = item[:max_chars_per_item-3] + "..."
                lines.append(f"  • {item}")
        else:
            lines.append("  • None")
    else:
        lines.append("  • None")
    
    # BLOCKERS section - ALWAYS show
    lines.append("")  # Blank line between sections
    lines.append(blockers_label)
    
    if categorized.get("blockers"):
        # Filter out any "None", "No blockers" entries, and emoji-only entries
        actual_blockers = [
            item for item in categorized["blockers"]
            if item.lower().strip() not in ["none", "n/a", "na", "no blockers", "none."]
            and not is_emoji_only(item)
        ]
        
        if actual_blockers:
            for item in actual_blockers[:max_items_per_category]:
                if len(item) > max_chars_per_item:
                    item = item[:max_chars_per_item-3] + "..."
                lines.append(f"  • {item}")
        else:
            lines.append("  • None")
    else:
        lines.append("  • None")
    
    # Notes section - only show if there are notes
    if categorized.get("notes"):
        valid_notes = [item for item in categorized["notes"] if not is_emoji_only(item)]
        if valid_notes:
            if lines:
                lines.append("")
            lines.append(notes_label)
            for item in valid_notes[:max_items_per_category]:
                if len(item) > max_chars_per_item:
                    item = item[:max_chars_per_item-3] + "..."
                lines.append(f"  • {item}")
    
    return "\n".join(lines) if lines else "No updates available"


def ai_analyze_and_summarize(text):
    """
    Wrapper function for backward compatibility.
    Uses parse_update_into_bullets and formats the result.
    """
    categorized = parse_update_into_bullets(text)
    return format_categorized_bullets(
        categorized,
        use_emojis=False,
        max_items_per_category=5,  # Increased to show more items
        max_chars_per_item=500  # Increased to avoid truncation
    )


def get_column_value(item, column_name):
    """Extract column value"""
    for col in item.get("column_values", []):
        col_text = col.get("text", "")
        if col.get("id") == column_name or (col_text and col_text.lower() == column_name.lower()):
            return col_text
    return ""


def extract_owner(item):
    """Extract owner and convert email to full name"""
    owner = get_column_value(item, "project_owner") or ""
    if not owner:
        owner = (get_column_value(item, "owner") or get_column_value(item, "developer") or
                get_column_value(item, "assignee") or get_column_value(item, "person") or
                get_column_value(item, "people") or "")
    # Convert email to full name using the mapper
    return convert_email_to_name(owner) if owner else "N/A"


def extract_notes(item):
    """Extract notes"""
    notes = find_column_by_title(item, ["notes"], exact_match=True)
    if not notes:
        notes = find_column_by_title(item, ["note", "description", "desc"])
    return notes or ""


def create_ai_summary_presentation(board_data):
    """Create PowerPoint with professional weekly status summaries"""
    prs = Presentation()
    # Set to 16:9 widescreen format (standard for modern displays)
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    
    items = board_data.get("items_page", {}).get("items", [])
    print(f"\nAnalyzing {len(items)} items for weekly status summary...")
    
    # Title slide
    title_slide_layout = prs.slide_layouts[0]
    slide = prs.slides.add_slide(title_slide_layout)
    title = slide.shapes.title
    subtitle = slide.placeholders[1]
    
    title.text = "US KVM & Linux Status"
    subtitle.text = f"{datetime.now().strftime('%B %d, %Y')}\nBy Kennedy Cheruiyot"
    
    # 3 items per slide for better readability with detailed summaries
    items_per_slide = 3
    total_items = len(items)
    
    for start_idx in range(0, total_items, items_per_slide):
        end_idx = min(start_idx + items_per_slide, total_items)
        slide_items = items[start_idx:end_idx]
        
        blank_slide_layout = prs.slide_layouts[6]
        slide = prs.slides.add_slide(blank_slide_layout)
        
        # Title - full width for 16:9
        title_box = slide.shapes.add_textbox(Inches(0), Inches(0.3), Inches(13.333), Inches(0.5))
        title_frame = title_box.text_frame
        title_frame.text = "US KVM and Linux Weekly Status"
        title_para = title_frame.paragraphs[0]
        title_para.font.size = Pt(24)
        title_para.font.bold = True
        title_para.alignment = PP_ALIGN.LEFT
        
        # Table - full width for 16:9
        rows = len(slide_items) + 1
        cols = 5  # Item, Owner, Status, Latest Updates, Notes
        
        left = Inches(0)
        top = Inches(1.0)
        width = Inches(13.333)  # Full 16:9 width
        
        row_height_val = 1.8  # Taller for latest updates
        header_height_val = 0.4
        total_height = header_height_val + (row_height_val * len(slide_items))
        height = Inches(total_height)
        
        table = slide.shapes.add_table(rows, cols, left, top, width, height).table
        
        table.rows[0].height = Inches(header_height_val)
        for i in range(1, rows):
            table.rows[i].height = Inches(row_height_val)
        
        # Adjust column widths for 16:9 format (total = 13.333")
        table.columns[0].width = Inches(2.5)   # Item
        table.columns[1].width = Inches(1.0)   # Owner
        table.columns[2].width = Inches(1.0)   # Status
        table.columns[3].width = Inches(5.5)   # Latest Updates (wider)
        table.columns[4].width = Inches(3.333) # Notes (wider)
        
        # Header - centered
        headers = ["Item", "Owner", "Status", "Latest Updates", "Notes"]
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
            # Item
            cell = table.cell(row_idx, 0)
            cell.text = item["name"]
            for paragraph in cell.text_frame.paragraphs:
                paragraph.font.size = Pt(9)
                paragraph.font.name = 'Calibri'
                paragraph.font.bold = True
            cell.text_frame.word_wrap = True
            cell.vertical_anchor = MSO_VERTICAL_ANCHOR.MIDDLE
            for paragraph in cell.text_frame.paragraphs:
                paragraph.alignment = PP_ALIGN.LEFT
            
            # Owner
            cell = table.cell(row_idx, 1)
            cell.text = extract_owner(item)
            for paragraph in cell.text_frame.paragraphs:
                paragraph.font.size = Pt(9)
                paragraph.font.name = 'Calibri'
                paragraph.alignment = PP_ALIGN.LEFT
            cell.text_frame.word_wrap = True
            cell.vertical_anchor = MSO_VERTICAL_ANCHOR.MIDDLE
            
            # Status
            cell = table.cell(row_idx, 2)
            status = get_column_value(item, "project_status") or get_column_value(item, "status") or "N/A"
            cell.text = status
            for paragraph in cell.text_frame.paragraphs:
                paragraph.font.size = Pt(9)
                paragraph.font.name = 'Calibri'
                paragraph.font.bold = True
                paragraph.alignment = PP_ALIGN.LEFT
            cell.text_frame.word_wrap = True
            cell.vertical_anchor = MSO_VERTICAL_ANCHOR.MIDDLE
            
            # Color code status
            if "done" in status.lower() or "integrated" in status.lower():
                cell.fill.solid()
                cell.fill.fore_color.rgb = RGBColor(200, 255, 200)
            elif "blocked" in status.lower() or "stuck" in status.lower():
                cell.fill.solid()
                cell.fill.fore_color.rgb = RGBColor(255, 200, 200)
            elif "review" in status.lower():
                cell.fill.solid()
                cell.fill.fore_color.rgb = RGBColor(255, 235, 200)
            
            # AI Summary - formatted bullet summary text with colored headers
            cell = table.cell(row_idx, 3)
            latest_update = get_latest_update(item)
            ai_summary = ai_analyze_and_summarize(latest_update)

            # Clear existing text
            cell.text = ""
            text_frame = cell.text_frame
            text_frame.word_wrap = True
            cell.vertical_anchor = MSO_VERTICAL_ANCHOR.MIDDLE  # Center vertically
            
            # Parse and format with colors
            if ai_summary:
                lines = ai_summary.strip().split('\n')
                for line in lines:
                    p = text_frame.add_paragraph()
                    p.text = line
                    p.font.size = Pt(8)
                    p.font.name = 'Calibri'
                    p.alignment = PP_ALIGN.LEFT
                    
                    # Color the section headers
                    if line.startswith('COMPLETED LAST WEEK'):
                        p.font.bold = True
                        p.font.color.rgb = RGBColor(0, 128, 0)  # Green
                    elif line.startswith('CURRENTLY WORKING ON'):
                        p.font.bold = True
                        p.font.color.rgb = RGBColor(0, 112, 192)  # Blue
                    elif line.startswith('BLOCKERS'):
                        p.font.bold = True
                        p.font.color.rgb = RGBColor(192, 0, 0)  # Red
                    elif line.startswith('NOTES'):
                        p.font.bold = True
                        p.font.color.rgb = RGBColor(128, 128, 128)  # Gray
                
                # Remove the first empty paragraph that was created
                if len(text_frame.paragraphs) > len(lines):
                    text_frame.paragraphs[0]._element.getparent().remove(text_frame.paragraphs[0]._element)
            else:
                p = text_frame.paragraphs[0]
                p.text = "No updates available"
                p.font.size = Pt(8)
                p.font.name = 'Calibri'
            
            # Notes
            cell = table.cell(row_idx, 4)
            notes = extract_notes(item)
            cell.text = notes if notes else ""
            for paragraph in cell.text_frame.paragraphs:
                paragraph.font.size = Pt(8)
                paragraph.font.name = 'Calibri'
            cell.text_frame.word_wrap = True
            cell.vertical_anchor = MSO_VERTICAL_ANCHOR.MIDDLE
            for paragraph in cell.text_frame.paragraphs:
                paragraph.alignment = PP_ALIGN.LEFT
            
            # Alternate row colors
            if row_idx % 2 == 0:
                for col_idx in range(5):
                    cell = table.cell(row_idx, col_idx)
                    try:
                        _ = cell.fill.fore_color.rgb
                    except:
                        cell.fill.solid()
                        cell.fill.fore_color.rgb = RGBColor(245, 245, 245)
            
            print(f"  ✓ Analyzed: {item['name']}")
        
        # Page number
        page_num = (start_idx // items_per_slide) + 2
        page_box = slide.shapes.add_textbox(Inches(8.5), Inches(7.2), Inches(1.0), Inches(0.3))
        page_frame = page_box.text_frame
        page_frame.text = f"Page {page_num}"
        page_para = page_frame.paragraphs[0]
        page_para.font.size = Pt(10)
        page_para.font.name = 'Calibri'
        page_para.alignment = PP_ALIGN.RIGHT
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"ai_summary_{BOARD_ID}_{timestamp}.pptx"
    prs.save(filename)
    return filename


def main():
    """Main execution"""
    global COLUMN_MAP
    
    print("Fetching board data from Monday.com...")
    print(f"Board ID: {BOARD_ID}\n")
    
    board_data = get_board_items_with_updates()
    
    if not board_data:
        print("\n❌ Failed to fetch board data")
        return
    
    print(f"✓ Successfully fetched board: {board_data['name']}")
    
    columns = board_data.get("columns", [])
    COLUMN_MAP = {col["id"]: col["title"] for col in columns}
    print(f"✓ Loaded {len(COLUMN_MAP)} column definitions\n")
    
    print("="*80)
    print("Creating AI-Analyzed Summary PowerPoint...")
    print("="*80)
    
    try:
        filename = create_ai_summary_presentation(board_data)
        print(f"\n✅ AI summary created successfully!")
        print(f"📄 File: {filename}")
        print(f"📍 Location: {os.path.abspath(filename)}")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        raise SystemExit(1)


if __name__ == "__main__":
    main()

# Made with Bob