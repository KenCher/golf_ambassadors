#!/usr/bin/env python3
"""
Fetch and display current status of all work items from Monday.com board
"""

import requests
import json
from datetime import datetime

# Monday.com API configuration
API_TOKEN = "eyJhbGciOiJIUzI1NiJ9.eyJ0aWQiOjYyOTQxMTE0NywiYWFpIjoxMSwidWlkIjo1MDkyMjk2MSwiaWFkIjoiMjAyNi0wMy0wNVQxNjoxNzozOC4wMDBaIiwicGVyIjoibWU6d3JpdGUiLCJhY3RpZCI6MTM1MzY5ODEsInJnbiI6InVzZTEifQ.swejQV61Cb4d7VEFTww2nBDnpUt19U05NTHbb9lpg9g"
API_URL = "https://api.monday.com/v2"
BOARD_ID = "18402712591"

headers = {
    "Authorization": API_TOKEN,
    "Content-Type": "application/json"
}

# Email to full name mapping (all lowercase keys for case-insensitive matching)
EMAIL_TO_NAME = {
    'ramesh.errabolu@ibm.com': 'Ramesh Errabolu',
    'aaron.m.brown@ibm.com': 'Aaron Brown',
    'rreyes@us.ibm.com': 'Rorie Reyes',
    'jdaley@ibm.com': 'Josh Daley',
    'will.bezenah@ibm.com': 'Will Bezenah',
    'jh.kim@ibm.com': 'Jaehoon Kim',
    'farhan.ali4@ibm.com': 'Farhan Ali',
    'peter.jin@ibm.com': 'Peter Jin',
    'dmfreim@us.ibm.com': 'Doug Freimuth',
    'konstantin.shkolnyy@ibm.com': 'Konstantin Shkolnyy',
    'jjherne@us.ibm.com': 'Jason Herne',
    'zhuoying.cai@ibm.com': 'Joy Cai',
    'collin.walling@ibm.com': 'Collin Walling',
    'eric.farman@ibm.com': 'Eric Farman',
    'tony.krowiak@ibm.com': 'Tony Krowiak',
    'aekrowia@us.ibm.com': 'Anthony Krowiak',
    'cam@ibm.com': 'Camron Miller',
    'matthew.rosato@ibm.com': 'Matt Rosato',
    'omar.sandoval@ibm.com': 'Omar Sandoval',
    'omar.elghoul@ibm.com': 'Omar Elghoul',
    'jared.rossi@ibm.com': 'Jared Rossi',
    'mjwebber@us.ibm.com': 'Mathew Weber',
    'hanli11@ibm.com': 'Han Li',
    # Additional mappings for usernames (lowercase for matching)
    'hanli11': 'Han Li',
    'jaredros': 'Jared Rossi',
    'farman': 'Eric Farman',
    'mjwebber': 'Mathew Weber',
    'aekrowia': 'Anthony Krowiak',
    'mjrosato': 'Matt Rosato',
    'cameron miller': 'Camron Miller',
    'omar elghoul': 'Omar Elghoul',
    'omar.elghoul': 'Omar Elghoul',
    'farhan ali4': 'Farhan Ali'
}

def normalize_owner_name(name):
    """Normalize owner names by applying mappings"""
    if not name:
        return 'Unassigned'
    
    # Handle comma-separated multiple owners
    if ',' in name:
        parts = [p.strip() for p in name.split(',')]
        normalized = []
        for part in parts:
            part_lower = part.lower()
            if part_lower in EMAIL_TO_NAME:
                normalized.append(EMAIL_TO_NAME[part_lower])
            elif '@' in part:
                username = part.split('@')[0].lower()
                if username in EMAIL_TO_NAME:
                    normalized.append(EMAIL_TO_NAME[username])
                else:
                    normalized.append(part.split('@')[0].replace('.', ' ').title())
            else:
                normalized.append(part)
        return ', '.join(normalized)
    
    # Single owner
    name_lower = name.lower()
    if name_lower in EMAIL_TO_NAME:
        return EMAIL_TO_NAME[name_lower]
    elif '@' in name:
        username = name.split('@')[0].lower()
        if username in EMAIL_TO_NAME:
            return EMAIL_TO_NAME[username]
        return name.split('@')[0].replace('.', ' ').title()
    return name

def get_column_value(column_values, column_name):
    """Extract column value by name or id - board-specific version"""
    for col in column_values:
        col_id = col.get('id', '')
        text = col.get('text')
        value = col.get('value')
        
        # Status column - project_status
        if column_name.lower() == 'status':
            if col_id == 'project_status':
                if text:
                    return text
                if value and value != '{}' and value:
                    try:
                        parsed = json.loads(value)
                        return parsed.get('label') or parsed.get('text')
                    except:
                        pass
        
        # Owner column - project_owner
        elif column_name.lower() in ['person', 'owner']:
            if col_id == 'project_owner':
                if text:
                    return normalize_owner_name(text)
                if value and value != '{}' and value:
                    try:
                        parsed = json.loads(value)
                        persons = parsed.get('personsAndTeams', [])
                        if persons and len(persons) > 0:
                            names = []
                            for p in persons:
                                name = p.get('name', '')
                                if name:
                                    names.append(normalize_owner_name(name))
                            if names:
                                return ', '.join(names)
                    except:
                        pass
        
        # Priority column - color_mm15394
        elif column_name.lower() == 'priority':
            if col_id == 'color_mm15394':
                if text:
                    return text
                if value and value != '{}' and value:
                    try:
                        parsed = json.loads(value)
                        return parsed.get('label') or parsed.get('text')
                    except:
                        pass
    
    return None

# Module-level cache filled by resolve_current_status_column()
_CURRENT_STATUS_COL_ID    = None   # e.g. 'text_mm4sze8e'
_CURRENT_STATUS_COL_LABEL = None   # e.g. '06/29'
_PREVIOUS_STATUS_COL_ID   = None   # second-most-recent
_PREVIOUS_STATUS_COL_LABEL = None  # e.g. '06/22'


def resolve_current_status_column(columns):
    """Find the two most-recent Updates MM/DD columns from board column metadata.
    Populates module-level cache for current and previous week."""
    global _CURRENT_STATUS_COL_ID, _CURRENT_STATUS_COL_LABEL
    global _PREVIOUS_STATUS_COL_ID, _PREVIOUS_STATUS_COL_LABEL
    import re as _re

    date_cols = []
    for col in columns:
        col_id    = col.get('id', '')
        col_title = col.get('title', '')
        m = _re.match(r'Updates\s+(\d{1,2})/(\d{1,2})', col_title, _re.IGNORECASE)
        if m:
            month, day = int(m.group(1)), int(m.group(2))
            try:
                from datetime import datetime as _dt
                date_obj = _dt(datetime.now().year, month, day)
                date_cols.append((date_obj, col_id, f'{month:02d}/{day:02d}'))
            except ValueError:
                pass

    if not date_cols:
        _CURRENT_STATUS_COL_ID    = 'text_mm4sze8e'
        _CURRENT_STATUS_COL_LABEL = '??/??'
        _PREVIOUS_STATUS_COL_ID   = None
        _PREVIOUS_STATUS_COL_LABEL = None
        return

    date_cols.sort(reverse=True)           # most recent first
    _CURRENT_STATUS_COL_ID    = date_cols[0][1]
    _CURRENT_STATUS_COL_LABEL = date_cols[0][2]
    print(f"✅ Current status column:  '{date_cols[0][2]}' (id={_CURRENT_STATUS_COL_ID})")
    if len(date_cols) >= 2:
        _PREVIOUS_STATUS_COL_ID    = date_cols[1][1]
        _PREVIOUS_STATUS_COL_LABEL = date_cols[1][2]
        print(f"✅ Previous status column: '{date_cols[1][2]}' (id={_PREVIOUS_STATUS_COL_ID})")


def get_current_status(column_values):
    """Extract the current weekly status from the most-recent Updates column."""
    col_id = _CURRENT_STATUS_COL_ID or 'text_mm4sze8e'
    for col in column_values:
        if col.get('id') == col_id:
            text = col.get('text') or ''
            return text.strip() if text.strip() else ''
    return ''


def get_previous_status(column_values):
    """Extract the previous weekly status from the second-most-recent Updates column."""
    if not _PREVIOUS_STATUS_COL_ID:
        return ''
    for col in column_values:
        if col.get('id') == _PREVIOUS_STATUS_COL_ID:
            text = col.get('text') or ''
            return text.strip() if text.strip() else ''
    return ''



def _heuristic_classify_sentences(text):
    """Classify free-form status text (no section headers) into completed/current/blockers.

    Splits on sentence boundaries and assigns each sentence based on keyword signals.
    Returns dict: {'completed': [...], 'current': [...], 'blockers': [...]}
    or None if the text is truly free-form with no recognisable work keywords.
    """
    import re

    CURRENT_SIGNALS = re.compile(
        r'\b(working on|continuing to work|still working|working to|'
        r'investigating|trying to|looking into|setting up|reviewing|'
        r'will test|will work|in process of|currently waiting|'
        r'waiting for review|looking to reuse)\b',
        re.IGNORECASE)
    COMPLETED_SIGNALS = re.compile(
        r'\b(posted|submitted|sent|merged|fixed|resolved|completed|'
        r'received feedback|addressed|reworked|verified|confirmed|'
        r'made the changes|had meeting|had to build|had a meeting)\b',
        re.IGNORECASE)
    BLOCKERS_SIGNALS = re.compile(
        r'\b(blocked|blocker|no blockers?|waiting on|depends on|'
        r'cannot|can\'t|stuck)\b',
        re.IGNORECASE)
    NO_CHANGE = re.compile(
        r'^(same as|no change|no updates?|no recent|none,?\s*blocked)\b',
        re.IGNORECASE)

    # Split into sentences on ". " or "\n"
    raw_sentences = re.split(r'(?<=[.!?])\s+|\n+', text.strip())
    sentences = [s.strip() for s in raw_sentences if s.strip()]

    if not sentences:
        return None

    # If genuinely no work signals, stay as plain text
    has_any_signal = any(
        CURRENT_SIGNALS.search(s) or COMPLETED_SIGNALS.search(s) or BLOCKERS_SIGNALS.search(s)
        for s in sentences
    )
    if not has_any_signal:
        return None

    result = {'completed': [], 'current': [], 'blockers': []}

    for sentence in sentences:
        if NO_CHANGE.match(sentence):
            # "No change from last week" → completed: None
            continue
        if BLOCKERS_SIGNALS.search(sentence):
            # Only add as actual blocker if it isn't a "no blockers" statement
            if not re.search(r'no blockers?', sentence, re.IGNORECASE):
                result['blockers'].append(sentence)
        elif CURRENT_SIGNALS.search(sentence):
            result['current'].append(sentence)
        elif COMPLETED_SIGNALS.search(sentence):
            result['completed'].append(sentence)
        else:
            # Default unknown sentences to currently working on
            result['current'].append(sentence)

    # If only blockers were found and nothing else, treat as free-form
    if not result['completed'] and not result['current'] and not result['blockers']:
        return None

    return result


def _bullet(line):
    """Normalise a body line to a clean bullet string: '  • text'."""
    import re
    line = line.strip()
    # Strip existing dash/bullet/asterisk prefixes
    line = re.sub(r'^[-•*•]\s*', '', line).strip()
    if not line:
        return ''
    return f'• {line}'   # • text

def _bulletize_html(lines):
    """Return an HTML string of bullet lines joined by <br>."""
    bullets = [_bullet(l) for l in lines if l.strip()]
    if not bullets:
        return '• None'
    return '<br>'.join(bullets)

def _bulletize_pptx(lines):
    """Return list of bullet strings for pptx body lines."""
    bullets = [_bullet(l) for l in lines if l.strip()]
    return bullets if bullets else ['• None']

def format_current_status(text, dimmed=False):
    """Format current status with colour-coded, line-separated section headers.

    dimmed=True renders with muted colours (previous-week column)."""
    import re

    if not text or not text.strip():
        return '<span style="color:#aaa;">—</span>'

    # Normalise emoji shortcodes to nothing
    text = re.sub(r':white_check_mark:\s*', '', text)
    text = re.sub(r':arrows_counterclockwise:\s*', '', text)
    text = re.sub(r':construction:\s*', '', text)
    text = re.sub(r':x:\s*', '', text)
    text = re.sub(r'[✅🔄🚧❌]\s*', '', text)

    # Pre-process: if headers appear inline (not at start of line), split them onto their own lines
    INLINE_SPLIT = re.compile(
        r'(?<!\n)'                                  # not already at line start
        r'(?=[ \t]*(?:'
        r'completed\s+last\s+week'
        r'|completed(?=[ \t]*[:\-;])'
        r'|currently\s+working\s+on'
        r'|current\s+working\s+on'
        r'|current\s+work(?:ing)?'
        r'|current(?=[ \t]*[:\-;])'
        r'|blockers?\s*(?:\(if\s+any\))?'
        r')[:\-;]?[ \t])',
        re.IGNORECASE
    )
    text = INLINE_SPLIT.sub('\n', text)

    # Match a header line: keyword at start, optional separator, optional inline body
    HEADER_RE = re.compile(
        r'(?mi)^[ \t]*('
        r'completed\s+last\s+week'
        r'|completed(?=[ \t]*[:\-;][ \t]*)'
        r'|currently\s+working\s+on'
        r'|current\s+working\s+on'
        r'|current\s+work(?:ing)?'
        r'|current(?=[ \t]*[:\-;][ \t]*)'
        r'|blockers?\s*(?:\(if\s+any\))?'
        r')[:\-;]?[ \t]*(.*)?$'
    )

    _base = 'display:block;margin-top:10px;margin-bottom:3px;font-weight:bold;text-transform:uppercase;font-size:0.9em;'
    if dimmed:
        COMPLETED_STYLE = _base + 'color:#5a7a5a;opacity:0.75;'
        WORKING_STYLE   = _base + 'color:#3a5a7a;opacity:0.75;'
        BLOCKERS_STYLE  = _base + 'color:#7a3a3a;opacity:0.75;'
    else:
        COMPLETED_STYLE = _base + 'color:#155724;'
        WORKING_STYLE   = _base + 'color:#004085;'
        BLOCKERS_STYLE  = _base + 'color:#721c24;'

    def classify(header):
        h = header.lower().strip()
        if 'completed' in h: return 'completed'
        if 'current'   in h: return 'current'
        if 'block'     in h: return 'blockers'
        return None

    style_map = {'completed': COMPLETED_STYLE, 'current': WORKING_STYLE, 'blockers': BLOCKERS_STYLE}
    label_map = {'completed': 'COMPLETED LAST WEEK', 'current': 'CURRENTLY WORKING ON', 'blockers': 'BLOCKERS'}

    # Split text into sections
    sections = []
    current_kind = None
    current_lines = []

    for line in text.split('\n'):
        m = HEADER_RE.match(line)
        if m:
            if current_lines or current_kind is not None:
                sections.append({'kind': current_kind, 'lines': current_lines})
            current_kind = classify(m.group(1))
            current_lines = []
            inline = (m.group(2) or '').strip()
            if inline:
                current_lines.append(inline)
        else:
            current_lines.append(line)

    if current_lines or current_kind is not None:
        sections.append({'kind': current_kind, 'lines': current_lines})

    # No recognised sections — try heuristic keyword classification
    if not any(s['kind'] for s in sections):
        heuristic = _heuristic_classify_sentences(text)
        if heuristic:
            has_blockers = bool(heuristic['blockers'])
            parts = []
            parts.append(f'<span style="{COMPLETED_STYLE}">COMPLETED LAST WEEK</span>')
            parts.append(f'<span style="font-size:0.9em;">{_bulletize_html(heuristic["completed"] or ["None"])}</span>')
            parts.append(f'<span style="{WORKING_STYLE}">CURRENTLY WORKING ON</span>')
            parts.append(f'<span style="font-size:0.9em;">{_bulletize_html(heuristic["current"] or ["None"])}</span>')
            parts.append(f'<span style="{BLOCKERS_STYLE}">BLOCKERS</span>')
            parts.append(f'<span style="font-size:0.9em;">{_bulletize_html(heuristic["blockers"] or ["None"])}</span>')
            return ''.join(parts)
        # Truly free-form: plain text passthrough
        body = text.strip().replace('\n', '<br>')
        return f'<span style="font-size:0.9em;">{body}</span>'

    has_blockers = any(s['kind'] == 'blockers' for s in sections)

    parts = []
    for sec in sections:
        kind = sec['kind']
        body_lines = [l.rstrip() for l in sec['lines'] if l.strip()]

        if kind:
            parts.append(f'<span style="{style_map[kind]}">{label_map[kind]}</span>')
            parts.append('<span style="font-size:0.9em;">' + _bulletize_html(body_lines) + '</span>')
        else:
            if body_lines:
                parts.append('<span style="font-size:0.9em;">' + _bulletize_html(body_lines) + '</span>')

    if not has_blockers:
        parts.append(f'<span style="{BLOCKERS_STYLE}">BLOCKERS</span>')
        parts.append('<span style="font-size:0.9em;">• None</span>')

    return ''.join(parts)


def format_status_for_pptx(text):
    """Parse status text and return list of (line_text, kind) tuples for PowerPoint rendering.

    kind is one of: 'completed', 'current', 'blockers', 'body', 'blank'
    Handles all observed variants — same logic as format_current_status().
    Injects BLOCKERS / None when section is absent.
    """
    import re

    if not text or not text.strip():
        return [('No updates', 'body')]

    # Normalise emoji shortcodes
    text = re.sub(r':white_check_mark:\s*', '', text)
    text = re.sub(r':arrows_counterclockwise:\s*', '', text)
    text = re.sub(r':construction:\s*', '', text)
    text = re.sub(r':x:\s*', '', text)
    text = re.sub(r'[\U00002705\U0001F504\U0001F6A7\U0000274C]\s*', '', text)

    # Pre-split inline headers onto their own lines
    INLINE_SPLIT = re.compile(
        r'(?<!\n)'
        r'(?=[ \t]*(?:'
        r'completed\s+last\s+week'
        r'|completed(?=[ \t]*[:\-;])'
        r'|currently\s+working\s+on'
        r'|current\s+working\s+on'
        r'|current\s+work(?:ing)?'
        r'|current(?=[ \t]*[:\-;])'
        r'|blockers?\s*(?:\(if\s+any\))?'
        r')[:\-;]?[ \t])',
        re.IGNORECASE
    )
    text = INLINE_SPLIT.sub('\n', text)

    HEADER_RE = re.compile(
        r'(?mi)^[ \t]*('
        r'completed\s+last\s+week'
        r'|completed(?=[ \t]*[:\-;][ \t]*)'
        r'|currently\s+working\s+on'
        r'|current\s+working\s+on'
        r'|current\s+work(?:ing)?'
        r'|current(?=[ \t]*[:\-;][ \t]*)'
        r'|blockers?\s*(?:\(if\s+any\))?'
        r')[:\-;]?[ \t]*(.*)?$'
    )

    def classify(h):
        h = h.lower().strip()
        if 'completed' in h: return 'completed'
        if 'current'   in h: return 'current'
        if 'block'     in h: return 'blockers'
        return None

    LABELS = {
        'completed': 'COMPLETED LAST WEEK',
        'current':   'CURRENTLY WORKING ON',
        'blockers':  'BLOCKERS',
    }

    # Build sections
    sections = []
    cur_kind = None
    cur_lines = []

    for line in text.split('\n'):
        m = HEADER_RE.match(line)
        if m:
            if cur_lines or cur_kind is not None:
                sections.append((cur_kind, cur_lines))
            cur_kind = classify(m.group(1))
            cur_lines = []
            inline = (m.group(2) or '').strip()
            if inline:
                cur_lines.append(inline)
        else:
            cur_lines.append(line)

    if cur_lines or cur_kind is not None:
        sections.append((cur_kind, cur_lines))

    # Free-form — try heuristic keyword classification
    if not any(k for k, _ in sections):
        heuristic = _heuristic_classify_sentences(text)
        if heuristic:
            result = []
            result.append((LABELS['completed'], 'completed'))
            for s in _bulletize_pptx(heuristic['completed'] or []):
                result.append((s, 'body'))
            result.append(('', 'blank'))
            result.append((LABELS['current'], 'current'))
            for s in _bulletize_pptx(heuristic['current'] or []):
                result.append((s, 'body'))
            result.append(('', 'blank'))
            result.append((LABELS['blockers'], 'blockers'))
            for s in _bulletize_pptx(heuristic['blockers'] or []):
                result.append((s, 'body'))
            return result
        # Truly free-form passthrough
        result = []
        for line in text.strip().split('\n'):
            if line.strip():
                result.append((line.strip(), 'body'))
        return result or [('No updates', 'body')]

    has_blockers = any(k == 'blockers' for k, _ in sections)

    result = []
    for kind, lines in sections:
        body_lines = [l.strip() for l in lines if l.strip()]
        if kind:
            result.append((LABELS[kind], kind))
            for bl in (_bulletize_pptx(body_lines) if body_lines else ['• None']):
                result.append((bl, 'body'))
        else:
            for bl in body_lines:
                result.append((_bullet(bl) if bl.strip() else bl, 'body'))
        result.append(('', 'blank'))

    if not has_blockers:
        result.append((LABELS['blockers'], 'blockers'))
        result.append(('• None', 'body'))

    # Remove leading and trailing blank lines
    while result and result[0][1] == 'blank':
        result.pop(0)
    while result and result[-1][1] == 'blank':
        result.pop()

    return result


def debug_columns(items):
    """Debug function to see all available columns"""
    if items and len(items) > 0:
        print("\n" + "="*100)
        print("DEBUG: Available columns in first item:")
        print("="*100)
        for col in items[0]['column_values']:
            col_id = col.get('id', 'N/A')
            text = col.get('text') or 'N/A'
            value = str(col.get('value', 'N/A'))[:60]
            print(f"  ID: {col_id:25} | Text: {text[:40]:40} | Value: {value}")
        print("="*100 + "\n")

def fetch_board_status():
    """Fetch all items and their status from Monday board"""
    query = f"""
    query {{
        boards(ids: {BOARD_ID}) {{
            id
            name
            columns {{
                id
                title
            }}
            items_page(limit: 500) {{
                items {{
                    id
                    name
                    column_values {{
                        id
                        text
                        value
                    }}
                    updated_at
                    created_at
                }}
            }}
        }}
    }}
    """
    
    try:
        response = requests.post(API_URL, json={"query": query}, headers=headers)
        response.raise_for_status()
        data = response.json()
        
        if "errors" in data:
            print("❌ API Errors:")
            print(json.dumps(data["errors"], indent=2))
            return None
        
        if not data.get("data", {}).get("boards"):
            print("❌ Board not found or no access")
            return None
        
        board = data["data"]["boards"][0]
        items = board.get('items_page', {}).get('items', [])
        
        columns = board.get('columns', [])
        return {
            'board_name': board['name'],
            'board_id': board['id'],
            'items': items,
            'columns': columns,
        }
        
    except Exception as e:
        print(f"❌ Error fetching data: {e}")
        return None

def extract_vs_id(name):
    """Extract VS or BU ID from item name"""
    import re
    # Match VS#### first (digits)
    match = re.search(r'VS\d+', name, re.IGNORECASE)
    if match:
        return match.group(0).upper()
    # Match VSxxxx / VSxxx placeholder variants
    match = re.search(r'VS[xX]+', name)
    if match:
        return 'VSxxxx' 
    # Match BU#### / BUZ#### / BU-#### variants
    match = re.search(r'BU[Z\d\-]\d*', name, re.IGNORECASE)
    if match:
        return match.group(0).upper()
    return None

def display_status_report(board_data):
    """Display formatted status report"""
    if not board_data:
        return
    
    items = board_data['items']
    
    print("=" * 100)
    print(f"📊 MONDAY.COM BOARD STATUS REPORT")
    print(f"Board: {board_data['board_name']} (ID: {board_data['board_id']})")
    print(f"Total Items: {len(items)}")
    print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 100)
    print()
    
    # Group by status
    status_groups = {}
    
    for item in items:
        vs_id = extract_vs_id(item['name'])
        status = get_column_value(item['column_values'], 'status') or 'Not Started'
        owner = get_column_value(item['column_values'], 'person') or \
                get_column_value(item['column_values'], 'owner') or 'Unassigned'
        priority = get_column_value(item['column_values'], 'priority') or 'Medium'
        
        updated = datetime.fromisoformat(item['updated_at'].replace('Z', '+00:00'))
        updated_str = updated.strftime('%Y-%m-%d')
        
        if status not in status_groups:
            status_groups[status] = []
        
        status_groups[status].append({
            'vs_id': vs_id,
            'name': item['name'],
            'owner': owner,
            'priority': priority,
            'updated': updated_str
        })
    
    # Display by status
    status_order = ['Done', 'In Progress', 'Working on it', 'Stuck', 'Blocked', 'Not Started', 'Waiting']
    
    for status in status_order:
        if status in status_groups:
            items_list = status_groups[status]
            print(f"\n{'='*100}")
            print(f"📌 {status.upper()} ({len(items_list)} items)")
            print(f"{'='*100}")
            
            for item in sorted(items_list, key=lambda x: x['vs_id'] or ''):
                vs_display = f"[{item['vs_id']}]" if item['vs_id'] else ('[BU]' if item.get('name','').upper().startswith('BU') else '[VSxxxx]' if item.get('name','').upper().startswith('VS') else '[CI]')
                print(f"  {vs_display:12} {item['name'][:60]:60} | Owner: {item['owner']:15} | Priority: {item['priority']:8} | Updated: {item['updated']}")
    
    # Display remaining statuses
    for status, items_list in status_groups.items():
        if status not in status_order:
            print(f"\n{'='*100}")
            print(f"📌 {status.upper()} ({len(items_list)} items)")
            print(f"{'='*100}")
            
            for item in sorted(items_list, key=lambda x: x['vs_id'] or ''):
                vs_display = f"[{item['vs_id']}]" if item['vs_id'] else ('[BU]' if item.get('name','').upper().startswith('BU') else '[VSxxxx]' if item.get('name','').upper().startswith('VS') else '[CI]')
                print(f"  {vs_display:12} {item['name'][:60]:60} | Owner: {item['owner']:15} | Priority: {item['priority']:8} | Updated: {item['updated']}")
    
    # Group by owner
    print(f"\n{'='*100}")
    print("👥 WORK ITEMS BY TEAM MEMBER")
    print(f"{'='*100}")
    
    owner_groups = {}
    for item in items:
        vs_id = extract_vs_id(item['name'])
        status = get_column_value(item['column_values'], 'status') or 'Not Started'
        owner = get_column_value(item['column_values'], 'person') or \
                get_column_value(item['column_values'], 'owner') or 'Unassigned'
        priority = get_column_value(item['column_values'], 'priority') or 'Medium'
        
        updated = datetime.fromisoformat(item['updated_at'].replace('Z', '+00:00'))
        updated_str = updated.strftime('%Y-%m-%d')
        
        if owner not in owner_groups:
            owner_groups[owner] = []
        
        owner_groups[owner].append({
            'vs_id': vs_id,
            'name': item['name'],
            'status': status,
            'priority': priority,
            'updated': updated_str
        })
    
    # Display by owner (sorted by number of items)
    for owner, items_list in sorted(owner_groups.items(), key=lambda x: len(x[1]), reverse=True):
        print(f"\n{'─'*100}")
        print(f"👤 {owner.upper()} ({len(items_list)} items)")
        print(f"{'─'*100}")
        
        # Group this owner's items by status
        owner_status_groups = {}
        for item in items_list:
            status = item['status']
            if status not in owner_status_groups:
                owner_status_groups[status] = []
            owner_status_groups[status].append(item)
        
        # Display items grouped by status
        for status in ['Done', 'In Progress', 'Working on it', 'Stuck', 'Blocked', 'Not Started', 'Waiting']:
            if status in owner_status_groups:
                status_items = owner_status_groups[status]
                print(f"\n  📌 {status} ({len(status_items)} items):")
                for item in sorted(status_items, key=lambda x: x['vs_id'] or ''):
                    vs_display = f"[{item['vs_id']}]" if item['vs_id'] else ('[BU]' if item.get('name','').upper().startswith('BU') else '[VSxxxx]' if item.get('name','').upper().startswith('VS') else '[CI]')
                    print(f"    {vs_display:12} {item['name'][:55]:55} | Priority: {item['priority']:8} | Updated: {item['updated']}")
        
        # Display remaining statuses
        for status, status_items in owner_status_groups.items():
            if status not in ['Done', 'In Progress', 'Working on it', 'Stuck', 'Blocked', 'Not Started', 'Waiting']:
                print(f"\n  📌 {status} ({len(status_items)} items):")
                for item in sorted(status_items, key=lambda x: x['vs_id'] or ''):
                    vs_display = f"[{item['vs_id']}]" if item['vs_id'] else ('[BU]' if item.get('name','').upper().startswith('BU') else '[VSxxxx]' if item.get('name','').upper().startswith('VS') else '[CI]')
                    print(f"    {vs_display:12} {item['name'][:55]:55} | Priority: {item['priority']:8} | Updated: {item['updated']}")
    
    # Summary statistics
    print(f"\n{'='*100}")
    print("📈 SUMMARY STATISTICS")
    print(f"{'='*100}")
    print("\nBy Status:")
    for status, items_list in sorted(status_groups.items(), key=lambda x: len(x[1]), reverse=True):
        print(f"  {status:20} : {len(items_list):3} items")
    
    print("\nBy Team Member:")
    for owner, items_list in sorted(owner_groups.items(), key=lambda x: len(x[1]), reverse=True):
        print(f"  {owner:20} : {len(items_list):3} items")
    print(f"{'='*100}")

def save_to_json(board_data, filename='monday_status.json'):
    """Save status data to JSON file"""
    if not board_data:
        return
    
    output = {
        'generated_at': datetime.now().isoformat(),
        'board_name': board_data['board_name'],
        'board_id': board_data['board_id'],
        'total_items': len(board_data['items']),
        'items': []
    }
    
    for item in board_data['items']:
        vs_id = extract_vs_id(item['name'])
        output['items'].append({
            'vs_id': vs_id,
            'name': item['name'],
            'status': get_column_value(item['column_values'], 'status') or 'Not Started',
            'owner': get_column_value(item['column_values'], 'person') or \
                     get_column_value(item['column_values'], 'owner') or 'Unassigned',
            'priority': get_column_value(item['column_values'], 'priority') or 'Medium',
            'updated_at': item['updated_at'],
            'created_at': item['created_at']
        })
    
    with open(filename, 'w') as f:
        json.dump(output, f, indent=2)
    
    print(f"\n✅ Status data saved to: {filename}")

def generate_html_report(board_data, filename='monday_status_report.html'):
    """Generate HTML report with status visualization"""
    if not board_data:
        return

    # Resolve the latest two Updates columns dynamically from board metadata
    resolve_current_status_column(board_data.get('columns', []))
    current_col_label  = _CURRENT_STATUS_COL_LABEL  or '??/??'
    previous_col_label = _PREVIOUS_STATUS_COL_LABEL or 'Prev'

    items = board_data['items']
    
    # Group by status
    status_groups = {}
    for item in items:
        vs_id = extract_vs_id(item['name'])
        status = get_column_value(item['column_values'], 'status') or 'Not Started'
        owner = get_column_value(item['column_values'], 'person') or \
                get_column_value(item['column_values'], 'owner') or 'Unassigned'
        priority = get_column_value(item['column_values'], 'priority') or 'Medium'
        
        updated = datetime.fromisoformat(item['updated_at'].replace('Z', '+00:00'))
        updated_str = updated.strftime('%Y-%m-%d')
        
        if status not in status_groups:
            status_groups[status] = []
        
        current_status  = get_current_status(item['column_values'])
        previous_status = get_previous_status(item['column_values'])
        status_groups[status].append({
            'vs_id': vs_id,
            'name': item['name'],
            'owner': owner,
            'priority': priority,
            'updated': updated_str,
            'current_status': current_status,
            'previous_status': previous_status,
        })
    
    # Calculate summary statistics
    total_items = len(items)
    done_count = len([i for i in items if 'done' in (get_column_value(i['column_values'], 'status') or '').lower()])
    progress_count = len([i for i in items if 'progress' in (get_column_value(i['column_values'], 'status') or '').lower()])
    blocked_count = len([i for i in items if 'blocked' in (get_column_value(i['column_values'], 'status') or '').lower()])
    
    # Count items by owner
    owner_counts = {}
    for item in items:
        owner = get_column_value(item['column_values'], 'owner') or 'Unassigned'
        owner_counts[owner] = owner_counts.get(owner, 0) + 1
    
    # Count items by priority
    priority_counts = {}
    for item in items:
        priority = get_column_value(item['column_values'], 'priority') or 'Not Set'
        priority_counts[priority] = priority_counts.get(priority, 0) + 1
    
    # Generate HTML
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>US KVM &amp; Linux Development Status — {board_data['board_name']}</title>
    <style>
        /* ── IBM Carbon Design System tokens ── */
        :root {{
            --ibm-blue-60:  #0043ce;
            --ibm-blue-70:  #002d9c;
            --ibm-blue-10:  #edf5ff;
            --ibm-gray-10:  #f4f4f4;
            --ibm-gray-20:  #e0e0e0;
            --ibm-gray-50:  #8d8d8d;
            --ibm-gray-80:  #393939;
            --ibm-gray-100: #161616;
            --ibm-green-50: #198038;
            --ibm-green-10: #defbe6;
            --ibm-red-50:   #da1e28;
            --ibm-red-10:   #fff1f1;
            --ibm-yellow-30:#f1c21b;
            --ibm-yellow-10:#fcf4d6;
            --ibm-teal-50:  #007d79;
            --ibm-teal-10:  #d9fbfb;
            --ibm-purple-50:#8a3ffc;
            --ibm-purple-10:#f6f2ff;
            --text-primary:    var(--ibm-gray-100);
            --text-secondary:  var(--ibm-gray-80);
            --text-helper:     var(--ibm-gray-50);
            --border:          var(--ibm-gray-20);
            --surface:         var(--ibm-gray-10);
        }}
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: 'IBM Plex Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            font-size: 14px; line-height: 1.5;
            background: #f4f4f4;
            color: var(--text-primary);
        }}
        /* ── Page wrapper ── */
        .page-wrap {{
            max-width: 1440px; margin: 0 auto;
            background: #ffffff;
            border: 1px solid var(--border);
        }}
        /* ── Top bar ── */
        .topbar {{
            background: var(--ibm-gray-100);
            height: 4px;
            width: 100%;
        }}
        /* ── Header ── */
        header {{
            background: #ffffff;
            border-bottom: 1px solid var(--border);
            padding: 0 40px;
            display: flex; align-items: center; justify-content: space-between;
            height: 80px;
        }}
        .header-left {{
            display: flex; align-items: center; gap: 20px;
        }}
        .ibm-logo {{
            font-size: 22px; font-weight: 700; letter-spacing: -0.5px;
            color: var(--ibm-gray-100);
        }}
        .ibm-logo span {{ color: var(--ibm-blue-60); }}
        .header-divider {{
            width: 1px; height: 28px; background: var(--border);
        }}
        .header-title {{
            font-size: 14px; font-weight: 400;
            color: var(--text-secondary);
            letter-spacing: 0.16px;
        }}
        .header-right {{
            text-align: right;
            font-size: 12px; color: var(--text-helper);
            letter-spacing: 0.32px;
        }}
        .header-right strong {{
            display: block;
            font-size: 13px; color: var(--text-primary);
            font-weight: 600; margin-bottom: 2px;
        }}
        /* ── Hero band ── */
        .hero {{
            background: var(--ibm-blue-60);
            color: #ffffff;
            padding: 36px 40px;
        }}
        .hero h1 {{
            font-size: 28px; font-weight: 300;
            letter-spacing: -0.32px; margin-bottom: 6px;
        }}
        .hero h1 strong {{ font-weight: 600; }}
        .hero p {{
            font-size: 13px; opacity: 0.75; letter-spacing: 0.16px;
        }}
        /* ── KPI strip ── */
        .kpi-strip {{
            display: grid;
            grid-template-columns: repeat(5, 1fr);
            border-bottom: 1px solid var(--border);
        }}
        .kpi-card {{
            padding: 24px 28px;
            border-right: 1px solid var(--border);
        }}
        .kpi-card:last-child {{ border-right: none; }}
        .kpi-number {{
            font-size: 36px; font-weight: 300;
            color: var(--ibm-blue-60);
            line-height: 1; margin-bottom: 6px;
        }}
        .kpi-label {{
            font-size: 11px; font-weight: 600;
            text-transform: uppercase; letter-spacing: 1.5px;
            color: var(--text-helper);
        }}
        .kpi-card.done   .kpi-number {{ color: var(--ibm-green-50); }}
        .kpi-card.blocked .kpi-number {{ color: var(--ibm-red-50); }}
        /* ── Content area ── */
        .content {{ padding: 32px 40px; background: #ffffff; }}
        /* ── Section headings ── */
        .section-heading {{
            font-size: 11px; font-weight: 600;
            text-transform: uppercase; letter-spacing: 1.5px;
            color: var(--text-helper);
            padding: 28px 0 10px;
            border-bottom: 1px solid var(--border);
            margin-bottom: 16px;
        }}
        /* ── Summary tables ── */
        .summary-table {{
            width: 100%; margin-bottom: 28px;
            border: 1px solid var(--border);
        }}
        .summary-table-header {{
            background: var(--surface);
            padding: 12px 16px;
            font-size: 12px; font-weight: 600;
            color: var(--text-secondary);
            letter-spacing: 0.16px;
            border-bottom: 1px solid var(--border);
        }}
        .summary-table table {{ width: 100%; border-collapse: collapse; }}
        .summary-table th {{
            background: var(--ibm-blue-60); color: #ffffff;
            padding: 11px 16px; text-align: left;
            font-size: 12px; font-weight: 600;
            letter-spacing: 0.16px;
        }}
        .summary-table td {{
            padding: 10px 16px;
            border-bottom: 1px solid var(--border);
            font-size: 13px; color: var(--text-primary);
        }}
        .summary-table tr:last-child td {{ border-bottom: none; }}
        .summary-table tr:hover td {{ background: var(--ibm-blue-10); }}
        .summary-grid {{
            display: grid; grid-template-columns: 1fr 1fr;
            gap: 24px; margin-bottom: 28px;
        }}
        /* ── Collapsible status sections ── */
        .status-section {{ margin-bottom: 2px; }}
        .status-header {{
            background: var(--surface);
            border: 1px solid var(--border);
            padding: 14px 20px;
            cursor: pointer;
            display: flex; justify-content: space-between; align-items: center;
            transition: background 0.15s;
        }}
        .status-header:hover {{ background: var(--ibm-blue-10); }}
        .status-header h2 {{
            font-size: 13px; font-weight: 600;
            color: var(--text-primary);
            letter-spacing: 0.16px;
        }}
        .status-count {{
            background: var(--ibm-blue-60); color: #ffffff;
            padding: 2px 12px; border-radius: 12px;
            font-size: 11px; font-weight: 600;
            letter-spacing: 0.32px;
        }}
        .toggle-icon {{ font-size: 10px; color: var(--text-helper); margin-left: 10px; transition: transform 0.2s; }}
        .toggle-icon.active {{ transform: rotate(180deg); }}
        /* ── Items table ── */
        .items-table {{ width: 100%; border-collapse: collapse; margin-bottom: 1px; }}
        .items-table th {{
            background: var(--ibm-gray-80); color: #ffffff;
            padding: 10px 14px; text-align: left;
            font-size: 11px; font-weight: 600;
            letter-spacing: 0.32px; text-transform: uppercase;
        }}
        .items-table td {{
            padding: 11px 14px;
            border-bottom: 1px solid var(--border);
            font-size: 13px; vertical-align: top;
        }}
        .items-table tr:last-child td {{ border-bottom: none; }}
        .items-table tr:hover td {{ background: var(--ibm-blue-10); }}
        /* ── VS/BU ID tag ── */
        .vs-id {{
            font-family: 'IBM Plex Mono', 'Courier New', monospace;
            font-size: 11px; font-weight: 600;
            color: var(--ibm-blue-60);
            background: var(--ibm-blue-10);
            padding: 2px 7px; border-radius: 3px;
            white-space: nowrap;
        }}
        /* ── Status pills ── */
        .status-badge {{
            display: inline-block; padding: 2px 10px; border-radius: 3px;
            font-size: 11px; font-weight: 600; letter-spacing: 0.32px;
            white-space: nowrap;
        }}
        .status-done     {{ background: var(--ibm-green-10); color: var(--ibm-green-50); }}
        .status-progress {{ background: var(--ibm-blue-10);  color: var(--ibm-blue-60);  }}
        .status-blocked  {{ background: var(--ibm-red-10);   color: var(--ibm-red-50);   }}
        .status-review   {{ background: var(--ibm-yellow-10);color: #8e6a00;             }}
        .status-other    {{ background: var(--ibm-gray-10);  color: var(--ibm-gray-80);  }}
        /* ── Priority ── */
        .priority-critical {{ color: var(--ibm-red-50);   font-weight: 700; }}
        .priority-high     {{ color: #b45309;              font-weight: 600; }}
        .priority-medium   {{ color: var(--ibm-gray-80);                     }}
        .priority-low      {{ color: var(--ibm-green-50);                    }}
        /* ── Section band ── */
        .band {{
            background: var(--ibm-blue-60); color: #ffffff;
            padding: 12px 20px; margin: 28px 0 0;
            font-size: 11px; font-weight: 600;
            letter-spacing: 1.5px; text-transform: uppercase;
        }}
        /* ── Collapsible ── */
        .collapsible-content {{ display: none; }}
        .collapsible-content.active {{ display: block; }}
        /* ── Scrollable status cell ── */
        .status-cell {{ max-height: 160px; overflow-y: auto; }}
    </style>
</head>
<body>
<div class="page-wrap">
    <div class="topbar"></div>

    <!-- Header -->
    <header>
        <div class="header-left">
            <div class="ibm-logo"><span>IBM</span></div>
            <div class="header-divider"></div>
            <div class="header-title">US KVM &amp; Linux Development</div>
        </div>
        <div class="header-right">
            <strong>{board_data['board_name']}</strong>
            Generated {datetime.now().strftime('%B %d, %Y  %H:%M')}
        </div>
    </header>

    <!-- Hero -->
    <div class="hero">
        <h1><strong>Development Status Report</strong></h1>
        <p>KVM &amp; Linux work items — current week status and progress tracking</p>
    </div>

    <!-- KPI strip -->
    <div class="kpi-strip">
        <div class="kpi-card">
            <div class="kpi-number">{total_items}</div>
            <div class="kpi-label">Total Work Items</div>
        </div>
        <div class="kpi-card done">
            <div class="kpi-number">{done_count}</div>
            <div class="kpi-label">Done</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-number">{progress_count}</div>
            <div class="kpi-label">In Progress</div>
        </div>
        <div class="kpi-card blocked">
            <div class="kpi-number">{blocked_count}</div>
            <div class="kpi-label">Blocked</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-number">{len(status_groups)}</div>
            <div class="kpi-label">Status Categories</div>
        </div>
    </div>
            
            <!-- Executive Summary Table -->
            <div class="summary-table" style="margin-bottom: 30px;">
                <div class="summary-table-header">Executive Summary — Work Items Status</div>
                <table>
                    <thead>
                        <tr>
                            <th>Status Category</th>
                            <th style="text-align: right;">Count</th>
                            <th style="text-align: right;">Percentage</th>
                            <th>Key Items</th>
                        </tr>
                    </thead>
                    <tbody>
"""
    
    # Add executive summary rows
    for status, items_list in sorted(status_groups.items(), key=lambda x: len(x[1]), reverse=True)[:10]:
        count = len(items_list)
        percentage = round((count / total_items) * 100, 1)
        # Get first 3 VS IDs
        vs_ids = [item['vs_id'] for item in items_list if item['vs_id']][:3]
        key_items = ', '.join(vs_ids) if vs_ids else 'Various items'
        if len(items_list) > 3:
            key_items += f' (+{len(items_list)-3} more)'
        
        html += f"""
                        <tr>
                            <td><strong>{status}</strong></td>
                            <td style="text-align: right; font-weight: bold;">{count}</td>
                            <td style="text-align: right;">{percentage}%</td>
                            <td style="font-size: 0.9em;">{key_items}</td>
                        </tr>
"""
    
    html += """
                    </tbody>
                </table>
            </div>
            
            <div class="summary-grid">
                <div class="summary-table">
                    <div class="summary-table-header">Items by Owner</div>
                    <table>
                        <thead>
                            <tr>
                                <th>Owner</th>
                                <th style="text-align: right;">Item Count</th>
                                <th style="text-align: right;">% of Total</th>
                            </tr>
                        </thead>
                        <tbody>
"""
    
    # Add owner rows sorted by count
    for owner, count in sorted(owner_counts.items(), key=lambda x: x[1], reverse=True):
        percentage = round((count / total_items) * 100, 1)
        html += f"""
                            <tr>
                                <td>{owner}</td>
                                <td style="text-align: right; font-weight: bold;">{count}</td>
                                <td style="text-align: right;">{percentage}%</td>
                            </tr>
"""
    
    html += """
                        </tbody>
                    </table>
                </div>
                
                <div class="summary-table">
                    <div class="summary-table-header">Items by Priority</div>
                    <table>
                        <thead>
                            <tr>
                                <th>Priority</th>
                                <th style="text-align: right;">Item Count</th>
                                <th style="text-align: right;">% of Total</th>
                            </tr>
                        </thead>
                        <tbody>
"""
    
    # Add priority rows in order: Critical, High, Medium, Low, Not Set
    priority_order = ['Critical ⚠️️', 'High', 'Medium', 'Low', 'Not Set']
    for priority in priority_order:
        if priority in priority_counts:
            count = priority_counts[priority]
            percentage = round((count / total_items) * 100, 1)
            html += f"""
                            <tr>
                                <td>{priority}</td>
                                <td style="text-align: right; font-weight: bold;">{count}</td>
                                <td style="text-align: right;">{percentage}%</td>
                            </tr>
"""
    
    html += """
                        </tbody>
                    </table>
                </div>
            </div>
            
            <!-- Team Member Sections -->
            <h2 style="margin: 30px 0 20px 0; class="band">
                Work Items by Team Member
            </h2>
"""
    
    # Group by owner for HTML
    owner_groups_html = {}
    for item in items:
        vs_id = extract_vs_id(item['name'])
        status = get_column_value(item['column_values'], 'status') or 'Not Started'
        owner = get_column_value(item['column_values'], 'person') or \
                get_column_value(item['column_values'], 'owner') or 'Unassigned'
        priority = get_column_value(item['column_values'], 'priority') or 'Medium'
        
        updated = datetime.fromisoformat(item['updated_at'].replace('Z', '+00:00'))
        updated_str = updated.strftime('%Y-%m-%d')
        
        if owner not in owner_groups_html:
            owner_groups_html[owner] = []
        
        current_status  = get_current_status(item['column_values'])
        previous_status = get_previous_status(item['column_values'])
        owner_groups_html[owner].append({
            'vs_id': vs_id,
            'name': item['name'],
            'status': status,
            'priority': priority,
            'updated': updated_str,
            'current_status': current_status,
            'previous_status': previous_status,
        })
    
    # Add team member sections
    for owner, items_list in sorted(owner_groups_html.items(), key=lambda x: len(x[1]), reverse=True):
        # Group this owner's items by status
        owner_status_groups = {}
        for item in items_list:
            status = item['status']
            if status not in owner_status_groups:
                owner_status_groups[status] = []
            owner_status_groups[status].append(item)
        
        html += f"""
            <div class="status-section">
                <div class="status-header" onclick="toggleSection(this)">
                    <h2>👤 {owner}</h2>
                    <div>
                        <span class="status-count">{len(items_list)} items</span>
                        <span class="toggle-icon">▼</span>
                    </div>
                </div>
                <div class="collapsible-content">
"""
        
        # Display items grouped by status for this owner
        # Preferred display order first, then any remaining statuses not in the list
        _STATUS_PREF = ['In Progress', 'Working on it', 'Upstream review', 'In Debug',
                        'Code development', 'Test Development', 'Test Review',
                        'Internal Review', 'In Test', 'In Regression', 'In Setup',
                        'Monitoring', 'Future step', 'Not started', 'Not Started',
                        'Waiting', 'Stuck', 'Blocked', 'On hold', 'Done']
        _status_iter = [s for s in _STATUS_PREF if s in owner_status_groups] +                        [s for s in owner_status_groups if s not in _STATUS_PREF]
        for status in _status_iter:
            if status in owner_status_groups:
                status_items = owner_status_groups[status]
                status_class = 'status-done' if 'done' in status.lower() else \
                              'status-progress' if 'progress' in status.lower() else \
                              'status-blocked' if 'blocked' in status.lower() else \
                              'status-review' if 'review' in status.lower() else 'status-other'
                
                html += f"""
                    <h3 style="margin: 12px 0 6px 0; padding: 8px 14px; background: var(--ibm-gray-10); border-left: 3px solid var(--ibm-blue-60);">
                        <span class="status-badge {status_class}">{status}</span> ({len(status_items)} items)
                    </h3>
                    <table class="items-table">
                        <thead>
                            <tr>
                                <th style="width: 8%;">VS ID</th>
                                <th style="width: 22%;">Item Name</th>
                                <th style="width: 25%;">Previous ({previous_col_label})</th>
                                <th style="width: 25%;">Current ({current_col_label})</th>
                                <th style="width: 10%;">Priority</th>
                                <th style="width: 10%;">Last Updated</th>
                            </tr>
                        </thead>
                        <tbody>
"""
                
                for item in sorted(status_items, key=lambda x: x['vs_id'] or 'ZZZ'):
                    vs_display = item['vs_id'] if item['vs_id'] else ('BU' if item['name'].upper().startswith('BU') else 'VSxxxx' if item['name'].upper().startswith('VS') else 'CI')
                    priority_class = f"priority-{item['priority'].lower().split()[0].replace('⚠️️','').replace('⚠','').strip()}" if item['priority'] else ''
                    current_html  = format_current_status(item.get('current_status', ''))
                    previous_html = format_current_status(item.get('previous_status', ''), dimmed=True)
                    
                    html += f"""
                            <tr>
                                <td><span class="vs-id">{vs_display}</span></td>
                                <td>{item['name']}</td>
                                <td class="status-cell prev-cell" style="font-size:0.85em; line-height:1.6;">{previous_html}</td>
                                <td class="status-cell" style="font-size:0.85em; line-height:1.6;">{current_html}</td>
                                <td class="{priority_class}">{item['priority']}</td>
                                <td>{item['updated']}</td>
                            </tr>
"""
                
                html += """
                        </tbody>
                    </table>
"""
        
        html += """
                </div>
            </div>
"""
    
    html += """
            <h2 style="margin: 30px 0 20px 0; class="band">
                Work Items by Status
            </h2>
"""
    
    # Add status sections
    for status, items_list in sorted(status_groups.items(), key=lambda x: len(x[1]), reverse=True):
        status_class = 'status-done' if 'done' in status.lower() else \
                      'status-progress' if 'progress' in status.lower() else \
                      'status-blocked' if 'blocked' in status.lower() else \
                      'status-review' if 'review' in status.lower() else 'status-other'
        
        html += f"""
            <div class="status-section">
                <div class="status-header" onclick="toggleSection(this)">
                    <h2><span class="status-badge {status_class}">{status}</span></h2>
                    <div>
                        <span class="status-count">{len(items_list)} items</span>
                        <span class="toggle-icon">▼</span>
                    </div>
                </div>
                <div class="collapsible-content">
                    <table class="items-table">
                        <thead>
                            <tr>
                                <th style="width: 7%;">VS ID</th>
                                <th style="width: 18%;">Item Name</th>
                                <th style="width: 8%;">Owner</th>
                                <th style="width: 22%;">Previous ({previous_col_label})</th>
                                <th style="width: 22%;">Current ({current_col_label})</th>
                                <th style="width: 9%;">Priority</th>
                                <th style="width: 14%;">Last Updated</th>
                            </tr>
                        </thead>
                        <tbody>
"""
        
        for item in sorted(items_list, key=lambda x: x['vs_id'] or 'ZZZ'):
            vs_display = item['vs_id'] if item['vs_id'] else ('BU' if item['name'].upper().startswith('BU') else 'VSxxxx' if item['name'].upper().startswith('VS') else 'CI')
            priority_class = f"priority-{item['priority'].lower().split()[0].replace('⚠️️','').replace('⚠','').strip()}" if item['priority'] else ''
            current_html  = format_current_status(item.get('current_status', ''))
            previous_html = format_current_status(item.get('previous_status', ''), dimmed=True)
            
            html += f"""
                            <tr>
                                <td><span class="vs-id">{vs_display}</span></td>
                                <td>{item['name']}</td>
                                <td>{item['owner']}</td>
                                <td class="status-cell prev-cell" style="font-size:0.85em; line-height:1.6;">{previous_html}</td>
                                <td class="status-cell" style="font-size:0.85em; line-height:1.6;">{current_html}</td>
                                <td class="{priority_class}">{item['priority']}</td>
                                <td>{item['updated']}</td>
                            </tr>
"""
        
        html += """
                        </tbody>
                    </table>
                </div>
            </div>
"""
    
    html += """
        </div><!-- /content -->
</div><!-- /page-wrap -->
    
    <script>
        function toggleSection(header) {
            const content = header.nextElementSibling;
            const icon = header.querySelector('.toggle-icon');
            content.classList.toggle('active');
            icon.classList.toggle('active');
        }
        
        // Expand first section by default
        document.addEventListener('DOMContentLoaded', function() {
            const firstHeader = document.querySelector('.status-header');
            if (firstHeader) {
                toggleSection(firstHeader);
            }
        });
    </script>
</body>
</html>
"""
    
    with open(filename, 'w') as f:
        f.write(html)
    
    print(f"\n✅ HTML report saved to: {filename}")

if __name__ == "__main__":
    print("🔄 Fetching status from Monday.com board...")
    print()
    
    board_data = fetch_board_status()
    
    if board_data:
        # Resolve the current status column once for all functions
        resolve_current_status_column(board_data.get('columns', []))

        # Uncomment to debug columns:
        # debug_columns(board_data['items'])
        
        display_status_report(board_data)
        save_to_json(board_data)
        generate_html_report(board_data)
        print(f"\n✅ Status report complete!")
    else:
        print("\n❌ Failed to fetch board data")

# Made with Bob
