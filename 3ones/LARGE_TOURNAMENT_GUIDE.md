# Large Tournament Guide (70+ Players)

## Overview
Golf4us now supports large tournaments with 70+ players through enhanced features including CSV bulk import, group management, player search, and pagination.

---

## Quick Start for Large Tournaments

### Step 1: Prepare Your Player List
Create a CSV file with player names and handicap indexes:

**Format:** `Name, Handicap Index`

**Example (players_template.csv):**
```csv
John Doe, 12.5
Jane Smith, 8.3
Mike Johnson, 15.2
Sarah Williams, 6.7
Robert Brown, 18.4
```

### Step 2: Import Players
1. Open the app and go to **👥 Players** tab
2. Click **"Choose File"** under "Bulk Import (CSV)"
3. Select your CSV file
4. Players will be imported automatically

### Step 3: Organize into Groups
1. Go to **👥 Groups** tab
2. Select group size (typically 4 for foursomes)
3. Click **"Auto-Create Groups"**
4. Groups are randomly assigned

### Step 4: Manage Scores
- Use **🔍 Search** to quickly find players
- Navigate through pages (20 players per page)
- Enter scores in **✏️ Score** tab

---

## Features for Large Tournaments

### 📥 CSV Bulk Import
- **Import 70+ players in seconds**
- Supports standard CSV format
- Automatic handicap calculation
- Error reporting for invalid entries

**CSV Requirements:**
- Format: `Name, Handicap Index`
- One player per line
- Handicap as decimal number (e.g., 12.5)
- No headers required

### 🔍 Player Search
- **Real-time search** by player name
- **Case-insensitive** matching
- Instantly filters player list
- Works with pagination

### 📄 Pagination
- **20 players per page** for easy navigation
- Previous/Next buttons
- Page counter (e.g., "Page 2 of 4")
- Maintains search filters

### 👥 Group Management
- **Auto-create groups** by size (2-5 players)
- Random assignment for fairness
- View all groups with player details
- Quick access to group scoring

### 🗑️ Player Management
- **Delete individual players** with confirmation
- **Add single players** manually
- **View player statistics** (handicap, scores, holes completed)
- **Skins pool indicator** (💰 icon)

---

## Recommended Workflows

### Workflow 1: Single Scorekeeper (Small to Medium)
**Best for:** 20-40 players, one person managing all scores

1. Import all players via CSV
2. Create groups for organization
3. Enter scores as groups finish holes
4. Generate final PDF report

### Workflow 2: Multiple Scorekeepers (Large)
**Best for:** 40-70+ players, multiple scorekeepers

1. **Tournament Organizer:**
   - Import all 70 players via CSV
   - Create groups (e.g., 18 groups of 4)
   - Export tournament data
   - Share app file with scorekeepers

2. **Each Scorekeeper:**
   - Receives app file
   - Manages their assigned groups (4-5 groups each)
   - Enters scores for their groups only
   - Exports their data at end of round

3. **Tournament Organizer:**
   - Collects all exported JSON files
   - Manually compiles final results
   - Generates master PDF report

### Workflow 3: Self-Scoring (Very Large)
**Best for:** 70+ players, each player manages own score

1. Share app file with all players
2. Each player enters only their own scores
3. Players submit scorecards (PDF or screenshot)
4. Organizer compiles final results

---

## Tips for Large Tournaments

### Before the Tournament
✅ **Prepare CSV file** with all player names and handicaps  
✅ **Test import** with sample data  
✅ **Create groups** in advance  
✅ **Assign scorekeepers** to specific groups  
✅ **Share app file** with all scorekeepers

### During the Tournament
✅ **Use search** to quickly find players  
✅ **Enter scores by group** for efficiency  
✅ **Save frequently** (auto-saves to browser)  
✅ **Export data** periodically as backup

### After the Tournament
✅ **Collect all scorekeeper data** (if using multiple)  
✅ **Generate PDF reports** for sharing  
✅ **Verify all scores** before finalizing  
✅ **Share results** with all participants

---

## Troubleshooting

### CSV Import Issues
**Problem:** "Invalid data" errors  
**Solution:** Check CSV format - must be `Name, Handicap` with comma separator

**Problem:** Some players not imported  
**Solution:** Ensure each line has both name and valid handicap number

### Performance with 70+ Players
**Problem:** App feels slow  
**Solution:** Use pagination and search to limit displayed players

**Problem:** Dropdown lists too long  
**Solution:** Use search feature to filter players first

### Group Management
**Problem:** Need to reorganize groups  
**Solution:** Click "Clear Groups" and recreate with different settings

**Problem:** Want specific group assignments  
**Solution:** Currently random only - manually note assignments after creation

---

## Data Management

### Export Tournament Data
1. Go to **⚙️ Setup** tab (or Settings)
2. Click **"Export Data"**
3. Save JSON file as backup
4. Share with other scorekeepers if needed

### Import Tournament Data
1. Click **"Import Data"**
2. Select JSON file
3. Confirms before overwriting existing data

### Merge Multiple Scorekeeper Data
**Manual Process:**
1. Collect all JSON exports from scorekeepers
2. Open each file in text editor
3. Combine player scores into master file
4. Import master file into app
5. Generate final PDF

---

## Best Practices

### For Tournament Organizers
- 📋 Maintain master player list in spreadsheet
- 💾 Export data frequently as backup
- 👥 Assign 4-5 groups per scorekeeper
- 📱 Test app with scorekeepers before tournament
- 🎯 Have backup scoring method ready

### For Scorekeepers
- 🔍 Use search to find players quickly
- ✅ Verify scores before moving to next hole
- 💾 Export data after each 9 holes
- 📞 Communicate issues to organizer immediately
- 🔋 Keep device charged

### For Players (Self-Scoring)
- ✏️ Enter scores hole-by-hole
- 📊 Check leaderboard for accuracy
- 💾 Take screenshot of final scorecard
- 📧 Submit scorecard to organizer
- ⚠️ Report any issues immediately

---

## Feature Comparison

| Feature | Small (4-20) | Medium (20-40) | Large (40-70+) |
|---------|--------------|----------------|----------------|
| Manual Entry | ✅ Best | ⚠️ Slow | ❌ Too Slow |
| CSV Import | ✅ Optional | ✅ Recommended | ✅ Required |
| Single Scorekeeper | ✅ Easy | ⚠️ Manageable | ❌ Difficult |
| Multiple Scorekeepers | ⚠️ Overkill | ✅ Recommended | ✅ Required |
| Group Management | ✅ Optional | ✅ Helpful | ✅ Essential |
| Search/Filter | ⚠️ Nice | ✅ Helpful | ✅ Essential |
| Pagination | ⚠️ Not Needed | ✅ Helpful | ✅ Essential |

---

## Support

For questions or issues:
1. Check this guide first
2. Review QUICK_START.md for basic features
3. Test with sample data before tournament
4. Have backup scoring method ready

---

## Future Enhancements

Planned features for large tournaments:
- 🔄 Automatic data merging from multiple scorekeepers
- 📊 Real-time score sync across devices
- 🎯 Custom group assignments (not random)
- 📱 QR code sharing for quick app distribution
- ☁️ Cloud backup and sync
- 📈 Advanced tournament statistics

---

**Version:** 2.0 - Large Tournament Support  
**Last Updated:** 2026-03-17