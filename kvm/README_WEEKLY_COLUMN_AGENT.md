# Monday.com Weekly Column Agent

Automatically adds a new `Updates MM/DD` text column to your Monday.com board every Monday, ready for the team to fill in their weekly updates.

## How It Works

- Runs on (or before) Monday each week
- Calculates the correct Monday date automatically
- Creates a `long_text` column titled `Updates MM/DD` (e.g. `Updates 07/07`)
- **Idempotent** — safe to run multiple times; skips creation if the column already exists

---

## Quick Start

```bash
# One-time setup
chmod +x run_weekly_column_agent.sh

# Run manually
./run_weekly_column_agent.sh

# Preview without making changes
./run_weekly_column_agent.sh --dry-run

# Use a specific date instead of this Monday
./run_weekly_column_agent.sh --date 07/14
```

Or run directly with Python:
```bash
python3 monday_weekly_column_agent.py
python3 monday_weekly_column_agent.py --dry-run
python3 monday_weekly_column_agent.py --date 07/14
```

---

## Automate with Cron (Runs Every Monday at 8 AM)

```bash
crontab -e
```

Add this line (update the path to match your directory):
```
0 8 * * 1 cd /Users/kencheru/kvm && ./run_weekly_column_agent.sh >> ~/monday_column_agent.log 2>&1
```

**Verify your cron is set:**
```bash
crontab -l
```

---

## Configuration

The agent uses these settings in [`monday_weekly_column_agent.py`](monday_weekly_column_agent.py):

| Variable | Default | Description |
|---|---|---|
| `MONDAY_API_TOKEN` | env var or hardcoded | Your Monday.com API token |
| `BOARD_ID` | `18402712591` | Your Monday.com board ID |
| `COLUMN_TITLE_PREFIX` | `Updates` | Prefix for the column title |

### Override the API token via environment variable (recommended for sharing):
```bash
export MONDAY_API_TOKEN="your_token_here"
./run_weekly_column_agent.sh
```

---

## Requirements

- Python 3.7+
- `requests` package: `pip3 install requests`

---

## Troubleshooting

| Error | Fix |
|---|---|
| `Authentication failed` | Regenerate token at Monday.com → Profile → Admin → API |
| `Column already exists` | Normal — agent skips silently, nothing to do |
| `ModuleNotFoundError: requests` | Run `pip3 install requests` |
| Wrong date created | Use `--date MM/DD` to override |

---

## Integration with Summary Generator

This agent pairs with [`run_monday_summary.sh`](run_monday_summary.sh):

1. **Monday 8 AM** — `run_weekly_column_agent.sh` creates `Updates MM/DD` column
2. **Team fills in updates** throughout the week
3. **Next Monday** — `run_monday_summary.sh` generates the PowerPoint from that data
