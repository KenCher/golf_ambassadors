# How to Start the Deerfield Tournament Manager

## Quick Start

1. **Open Terminal** in the Golf4us folder

2. **Start the server**:
   ```bash
   node server.cjs
   ```

3. **Open your browser** and go to:
   ```
   http://localhost:8000/deerfield-tournament.html
   ```

## Alternative: Use Python (if Node.js not available)

```bash
cd public
python3 -m http.server 8000
```

Then open: `http://localhost:8000/deerfield-tournament.html`

## Why You Need a Server

The app loads course data from a JSON file. Modern browsers block file:// requests for security, so you must use a local web server.

## Features Available

- ✅ Add unlimited players with handicaps
- ✅ Select from 3 course combinations (North/South, North/East, South/East)
- ✅ Live scorecard for all 18 holes
- ✅ Real-time leaderboard (gross & net)
- ✅ Skins game calculator with carryovers
- ✅ Hole-by-hole tracking

## Troubleshooting

**If you see "Error loading course data":**
- Make sure you're using http://localhost:8000 (not file://)
- Check that server.cjs is running
- Verify deerfield-complete-scorecard.json exists in the public folder