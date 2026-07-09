#!/opt/homebrew/bin/python3
"""
Monday.com Weekly Column Agent
Automatically adds a new "Updates MM/DD" text column to the board every Monday.
Safe to run multiple times — skips creation if today's column already exists.

Usage:
    python3 monday_weekly_column_agent.py           # Run once (manual / cron)
    python3 monday_weekly_column_agent.py --dry-run # Preview without making changes
    python3 monday_weekly_column_agent.py --date 06/30  # Use a specific date
"""

import os
import sys
import json
import requests
import argparse
from datetime import datetime, timedelta

# ── Configuration ──────────────────────────────────────────────────────────────
API_TOKEN = os.getenv(
    "MONDAY_API_TOKEN",
    "eyJhbGciOiJIUzI1NiJ9.eyJ0aWQiOjYyOTQxMTE0NywiYWFpIjoxMSwidWlkIjo1MDkyMjk2MSwiaWFkIjoiMjAyNi0wMy0wNVQxNjoxNzozOC4wMDBaIiwicGVyIjoibWU6d3JpdGUiLCJhY3RpZCI6MTM1MzY5ODEsInJnbiI6InVzZTEifQ.swejQV61Cb4d7VEFTww2nBDnpUt19U05NTHbb9lpg9g"
)
API_URL   = "https://api.monday.com/v2"
BOARD_ID  = "18402712591"

HEADERS = {
    "Authorization": API_TOKEN,
    "Content-Type": "application/json",
}

# Column title pattern:  "Updates MM/DD"
COLUMN_TITLE_PREFIX = "Updates"


# ── Helpers ────────────────────────────────────────────────────────────────────

def gql(query: str, variables=None) -> dict:
    """Execute a GraphQL request against the Monday API."""
    payload = {"query": query}
    if variables:
        payload["variables"] = variables
    resp = requests.post(API_URL, json=payload, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    if "errors" in data:
        raise RuntimeError(f"Monday API error: {json.dumps(data['errors'], indent=2)}")
    return data["data"]


def get_existing_columns() -> list[dict]:
    """Return all columns on the board."""
    query = f"""
    query {{
        boards(ids: {BOARD_ID}) {{
            columns {{
                id
                title
                type
            }}
        }}
    }}
    """
    data = gql(query)
    return data["boards"][0]["columns"]


def column_exists(columns: list[dict], title: str) -> bool:
    """Check if a column with the given title already exists."""
    return any(col["title"] == title for col in columns)


def create_text_column(title) -> dict:
    """Create a new long-text column with the given title. Returns the new column."""
    mutation = """
    mutation ($boardId: ID!, $title: String!, $columnType: ColumnType!) {
        create_column(
            board_id:    $boardId,
            title:       $title,
            column_type: $columnType
        ) {
            id
            title
            type
        }
    }
    """
    variables = {
        "boardId":    BOARD_ID,
        "title":      title,
        "columnType": "long_text",
    }
    data = gql(mutation, variables)
    return data["create_column"]


def target_monday(override_date=None) -> datetime:
    """
    Return the datetime for the Monday this column should represent.
    - If --date MM/DD supplied, parse it.
    - Otherwise use today (allows running any day of the week before Monday
      by targeting the *next* Monday, or on Monday itself).
    """
    if override_date:
        year = datetime.now().year
        dt = datetime.strptime(f"{year}/{override_date}", "%Y/%m/%d")
        return dt

    today = datetime.now()
    # If today IS Monday use today; otherwise find next Monday
    days_until_monday = (0 - today.weekday()) % 7  # weekday 0 = Monday
    if days_until_monday == 0:
        return today
    return today + timedelta(days=days_until_monday)


# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Add a dated 'Updates MM/DD' column to the Monday.com board."
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Print what would happen without making any changes."
    )
    parser.add_argument(
        "--date", metavar="MM/DD",
        help="Manually specify the date for the column (e.g. 07/07). "
             "Defaults to this Monday's date."
    )
    args = parser.parse_args()

    print("=" * 50)
    print("  Monday.com Weekly Column Agent")
    print("=" * 50)

    # Determine target date
    target = target_monday(args.date)
    column_title = f"{COLUMN_TITLE_PREFIX} {target.strftime('%m/%d')}"

    print(f"\n📅  Target date : {target.strftime('%A, %B %d, %Y')}")
    print(f"📋  Column title: {column_title}")

    if args.dry_run:
        print("\n⚠️  DRY RUN — no changes will be made.")

    # Fetch existing columns
    print("\n🔍  Fetching existing board columns...")
    try:
        columns = get_existing_columns()
    except Exception as e:
        print(f"\n❌  Failed to fetch columns: {e}")
        sys.exit(1)

    print(f"    Found {len(columns)} columns on board {BOARD_ID}.")

    # Check for duplicates
    if column_exists(columns, column_title):
        print(f"\n✅  Column '{column_title}' already exists — nothing to do.")
        return

    # Create the column
    print(f"\n➕  Creating column '{column_title}'...")
    if args.dry_run:
        print(f"    [DRY RUN] Would create long_text column: '{column_title}'")
        print("\n✅  Dry run complete.")
        return

    try:
        new_col = create_text_column(column_title)
    except Exception as e:
        print(f"\n❌  Failed to create column: {e}")
        sys.exit(1)

    print(f"\n✅  Created column:")
    print(f"    ID    : {new_col['id']}")
    print(f"    Title : {new_col['title']}")
    print(f"    Type  : {new_col['type']}")
    print()
    print("Done! The new column is now visible on your Monday.com board.")
    print("Team members can fill in their updates for the week.")


if __name__ == "__main__":
    main()
