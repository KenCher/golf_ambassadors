# GolfAmbassadors Portal - User Guide

## Overview

The GolfAmbassadors Portal is a comprehensive team golf scoring application that allows team members to:
- Enter and track their golf scores hole-by-hole
- Calculate Stableford points automatically
- Track handicaps and net scores
- Manage participant selection and entry fees
- Share results transparently with the team
- Generate detailed scoring tables showing front 9, back 9, and total scores

## Getting Started

### 1. Access the Portal

Open `public/golf-ambassadors.html` in your web browser. The application works entirely in the browser and saves data locally.

### 2. Initial Setup

#### Competition Setup Tab (⚙️ Setup)

1. **Set Competition Name**
   - Enter a name for your competition (e.g., "Monthly Challenge", "Spring Tournament")
   - Click "Set Name" to save

2. **Configure the Course**
   - Enter the course name
   - Select number of holes (9 or 18)
   - Click "Generate Course Setup"
   - Customize par and handicap for each hole
   - Click "Save Course Setup"

3. **Set Entry Fee**
   - Enter the entry fee per player (default: $20)
   - Click "Save Entry Fee"

### 3. Add Team Members

#### Participants Tab (👥 Participants)

1. **Add Players**
   - Enter player name
   - Enter their handicap index
   - Click "Add Player"
   - Repeat for all team members

2. **Select Participants**
   - Check the box next to each player participating in this competition
   - Selected players will be highlighted in blue

3. **Track Payments**
   - Click on the payment badge (⏳ Pending / ✓ Paid) to toggle payment status
   - Green badge = Paid
   - Orange badge = Pending

4. **View Competition Summary**
   - Total number of participants
   - Total prize pool (participants × entry fee)

### 4. Enter Scores

#### Scorecard Tab (📋 Scorecard)

1. **Score Entry**
   - Each row represents a player
   - Each column represents a hole with its par
   - Enter the gross score for each hole
   - Scores are automatically saved as you type

2. **View Totals**
   - The rightmost column shows the total gross score for each player

3. **Calculate Results**
   - Click "Calculate All Scores" to generate Stableford points
   - This will take you to the Results tab

4. **Clear Scores**
   - Click "Clear All Scores" to reset all entries (confirmation required)

### 5. View Results

#### Results Tab (🏆 Results)

The results table shows:
- **Rank**: Position based on total Stableford points
- **Player**: Player name
- **Handicap**: Player's handicap index
- **Front 9 Points**: Stableford points for holes 1-9
- **Back 9 Points**: Stableford points for holes 10-18
- **Total Points**: Combined Stableford points (highest wins)
- **Gross Score**: Total strokes taken
- **Net Score**: Gross score minus handicap strokes
- **Payment**: Payment status

#### Prize Distribution

The system suggests a prize distribution:
- **3+ players**: 50% / 30% / 20% split
- **2 players**: 60% / 40% split
- **1 player**: 100% (winner takes all)

### 6. Share Results

#### Share Tab (📤 Share)

Multiple export options:

1. **Export to CSV**
   - Downloads a spreadsheet-compatible file
   - Contains all player data and scores

2. **Export to JSON**
   - Downloads complete competition data
   - Can be used to backup or restore the competition

3. **Copy Summary**
   - Copies formatted results to clipboard
   - Perfect for pasting into emails or messages

4. **Print Results**
   - Opens print dialog
   - Creates a printer-friendly version

## Stableford Scoring System

The portal uses the Modified Stableford scoring system:

| Score vs Par | Points |
|--------------|--------|
| Albatross (-3 or better) | 5 points |
| Eagle (-2) | 4 points |
| Birdie (-1) | 3 points |
| Par (0) | 2 points |
| Bogey (+1) | 1 point |
| Double Bogey or worse (+2 or more) | 0 points |

### How Handicap Strokes Work

1. Each player receives strokes based on their handicap
2. Strokes are distributed across holes according to the hole's handicap rating
3. The hardest holes (lowest handicap number) receive strokes first
4. Net score = Gross score - Strokes received on that hole
5. Stableford points are calculated based on net score vs par

**Example:**
- Player with 18 handicap gets 1 stroke on every hole
- Player with 9 handicap gets 1 stroke on the 9 hardest holes
- Player with 27 handicap gets 1 stroke on every hole + 1 extra on the 9 hardest holes

## Features

### ✅ Participant Selection
- Add unlimited team members
- Select who participates in each competition
- Track multiple competitions with the same team

### 💰 Payment Tracking
- Set entry fee per competition
- Track who has paid
- Calculate total prize pool automatically
- One-click payment status toggle

### 📊 Comprehensive Scoring
- Hole-by-hole score entry
- Automatic Stableford points calculation
- Front 9 and Back 9 breakdown
- Gross and net score tracking
- Real-time leaderboard

### 🔄 Data Persistence
- All data saved automatically to browser storage
- No server required
- Data persists between sessions
- Export/backup options available

### 📱 Mobile Friendly
- Responsive design works on phones and tablets
- Touch-friendly interface
- Optimized for on-course use

### 🤝 Team Transparency
- All scores visible to all team members
- Payment status tracking
- Fair handicap-based competition
- Multiple export formats for sharing

## Tips & Best Practices

1. **Set Up Course First**
   - Configure the course before adding scores
   - Verify par and handicap ratings are correct

2. **Add All Team Members**
   - Add everyone to the system once
   - Select participants for each competition

3. **Enter Scores Promptly**
   - Enter scores during or immediately after the round
   - Scores auto-save as you type

4. **Track Payments**
   - Update payment status as money is collected
   - Use the summary to verify total pot

5. **Export Results**
   - Export after each competition for records
   - Share results with the team for transparency

6. **Backup Your Data**
   - Periodically export to JSON
   - Keep backups of important competitions

## Troubleshooting

### Scores Not Saving
- Ensure JavaScript is enabled in your browser
- Check browser console for errors
- Try refreshing the page

### Data Lost
- Check if you're using the same browser
- Browser data may be cleared if using private/incognito mode
- Restore from JSON backup if available

### Incorrect Calculations
- Verify handicap values are correct
- Check hole par and handicap ratings
- Ensure all scores are entered

### Export Not Working
- Check browser allows downloads
- Try a different export format
- Ensure popup blockers aren't interfering

## Technical Details

- **Technology**: Pure HTML, CSS, and JavaScript
- **Storage**: Browser localStorage
- **Compatibility**: Modern browsers (Chrome, Firefox, Safari, Edge)
- **No Server Required**: Runs entirely in the browser
- **Data Format**: JSON for exports and storage

## Support

For issues or questions:
1. Check this guide first
2. Verify all setup steps are complete
3. Try clearing browser cache and reloading
4. Export data before troubleshooting

## Version History

- **v1.0** - Initial release with full Stableford scoring, participant tracking, and payment management

---

**Made with Bob** - GolfAmbassadors Portal