# Golf Tournament App - Usage Guide

## Quick Start Guide

### 1. Running the Demo

The easiest way to see the app in action is to run the demo:

```bash
cd golf-tournament-app
node src/index.js
```

This will:
- Create a sample tournament at Pebble Beach Golf Links
- Add 6 professional golfers with different handicaps
- Simulate 9 holes of play
- Display live leaderboards (gross and net)
- Show a sample scorecard
- Calculate skins games (gross and net)
- Calculate skins payouts

### 2. Opening the Web Interface

Open `public/index.html` in your web browser to see the interactive web interface with:
- Live leaderboard display
- Score entry form
- Skins game tracking
- Player management

## Step-by-Step Tutorial

### Creating Your First Tournament

```javascript
import { Player, Course, Hole, Tournament } from './src/index.js';

// Step 1: Create a course
const course = new Course('Pine Valley Golf Club');

// Step 2: Add holes (number, par, handicap/stroke index, yardage)
const holes = [
  { number: 1, par: 4, handicap: 10, yardage: 427 },
  { number: 2, par: 4, handicap: 6, yardage: 367 },
  // ... add all 18 holes
];

holes.forEach(h => {
  course.addHole(new Hole(h.number, h.par, h.handicap, h.yardage));
});

// Step 3: Create tournament
const tournament = new Tournament('Club Championship 2026', course, 'stroke-play');

// Step 4: Add players
const player1 = new Player('p1', 'John Smith', 12.5); // id, name, handicap index
const player2 = new Player('p2', 'Jane Doe', 8.3);
tournament.addPlayer(player1);
tournament.addPlayer(player2);

// Step 5: Start tournament
tournament.start();
```

### Recording Scores

```javascript
// Record scores as players complete holes
tournament.recordScore('p1', 1, 5);  // Player p1, Hole 1, 5 strokes
tournament.recordScore('p1', 2, 4);  // Player p1, Hole 2, 4 strokes
tournament.recordScore('p2', 1, 4);  // Player p2, Hole 1, 4 strokes
tournament.recordScore('p2', 2, 3);  // Player p2, Hole 2, 3 strokes
```

### Viewing the Leaderboard

```javascript
import { Leaderboard } from './src/components/Leaderboard.js';

// Get gross leaderboard
const grossLeaderboard = tournament.getLeaderboard(false);
console.log(Leaderboard.formatConsole(grossLeaderboard, false));

// Get net leaderboard
const netLeaderboard = tournament.getLeaderboard(true);
console.log(Leaderboard.formatConsole(netLeaderboard, true));

// Get leaderboard summary
const summary = Leaderboard.getSummary(grossLeaderboard);
console.log(`Leader: ${summary.leader.name} (${summary.leader.scoreToParStr})`);
```

### Calculating Skins

```javascript
import { SkinsCalculator } from './src/utils/SkinsCalculator.js';

// Get all players
const players = tournament.getAllPlayers();

// Prepare strokes per hole for net skins
const strokesPerHole = {};
players.forEach(player => {
  strokesPerHole[player.id] = player.strokesPerHole;
});

// Calculate gross skins
const grossSkins = SkinsCalculator.calculateSkins(players, {}, false);
console.log(SkinsCalculator.formatResults(grossSkins));

// Calculate net skins
const netSkins = SkinsCalculator.calculateSkins(players, strokesPerHole, true);
console.log(SkinsCalculator.formatResults(netSkins));

// Calculate payouts ($20 entry per player)
const payout = SkinsCalculator.calculatePayout(grossSkins, 20, players.length);
console.log(`Total Pot: $${payout.totalPot}`);
Object.values(payout.payouts).forEach(p => {
  console.log(`${p.name}: ${p.skins} skins = $${p.amount.toFixed(2)}`);
});
```

### Viewing Scorecards

```javascript
// Display a player's scorecard
const player = tournament.getPlayer('p1');
console.log(Leaderboard.formatScorecard(player, course));
```

### Saving and Loading Data

```javascript
import { DataPersistence } from './src/utils/DataPersistence.js';

// Save tournament
await DataPersistence.saveTournament(tournament, 'my-tournament.json');

// Load tournament
const savedData = await DataPersistence.loadTournament('my-tournament.json');

// Export to CSV
const csv = DataPersistence.exportToCSV(tournament, false);
console.log(csv);

// Export detailed scorecard
const detailedCSV = DataPersistence.exportDetailedScorecard(tournament);

// Export skins results
const skinsCSV = DataPersistence.exportSkinsToCSV(grossSkins);

// Browser only: Download as file
DataPersistence.downloadFile(csv, 'leaderboard.csv', 'text/csv');

// Browser only: Auto-save every minute
const autoSaveId = DataPersistence.startAutoSave(tournament, 60000);
// Stop auto-save when done
DataPersistence.stopAutoSave(autoSaveId);
```

## Common Use Cases

### 1. Weekly Club Tournament

```javascript
// Setup
const course = createYourCourse();
const tournament = new Tournament('Weekly Medal', course, 'stroke-play');

// Add members
members.forEach(member => {
  const player = new Player(member.id, member.name, member.handicap);
  tournament.addPlayer(player);
});

// During play - record scores via mobile/tablet
tournament.recordScore(playerId, holeNumber, strokes);

// Display live leaderboard on clubhouse TV
setInterval(() => {
  const leaderboard = tournament.getLeaderboard(true); // Net scores
  displayOnScreen(Leaderboard.formatHTML(leaderboard, true));
}, 30000); // Update every 30 seconds
```

### 2. Skins Game with Friends

```javascript
// Setup skins game
const tournament = new Tournament('Saturday Skins', course, 'stroke-play');
addPlayers(tournament);
tournament.start();

// Record scores
recordAllScores(tournament);

// Calculate both gross and net skins
const results = SkinsCalculator.calculateBothSkins(
  tournament.getAllPlayers(),
  getStrokesPerHole(tournament)
);

// Show results
console.log('GROSS SKINS:');
console.log(SkinsCalculator.formatResults(results.gross));
console.log('\nNET SKINS:');
console.log(SkinsCalculator.formatResults(results.net));

// Calculate payouts
const grossPayout = SkinsCalculator.calculatePayout(results.gross, 20, 4);
const netPayout = SkinsCalculator.calculatePayout(results.net, 20, 4);
```

### 3. Multi-Day Tournament

```javascript
// Day 1
const day1 = new Tournament('Championship - Round 1', course, 'stroke-play');
addPlayers(day1);
day1.start();
// ... record scores ...
await DataPersistence.saveTournament(day1, 'championship-day1.json');

// Day 2
const day2 = new Tournament('Championship - Round 2', course, 'stroke-play');
addPlayers(day2);
day2.start();
// ... record scores ...
await DataPersistence.saveTournament(day2, 'championship-day2.json');

// Combine results (you would need to implement this)
const combinedScores = combineMultipleRounds([day1, day2]);
```

## Tips and Best Practices

### 1. Handicap Management
- Always use official USGA Handicap Index values
- Update handicaps regularly (typically monthly)
- Verify course rating and slope rating for accurate calculations

### 2. Score Entry
- Enter scores hole-by-hole for real-time leaderboard updates
- Double-check scores before submission
- Use ESC (Equitable Stroke Control) for handicap posting

### 3. Skins Games
- Decide on gross vs. net before starting
- Clearly communicate carryover rules
- Consider separate pots for front 9, back 9, and total

### 4. Tournament Formats
- Choose appropriate handicap allowance for your format
- Stroke play: 95% allowance
- Match play: 100% allowance
- Team events: Lower allowances (85-90%)

### 5. Data Management
- Save tournament data regularly
- Export results to CSV for record-keeping
- Use auto-save feature for long tournaments

## Troubleshooting

### Issue: Handicap calculations seem wrong
**Solution**: Verify course rating and slope rating are correct. Default is 72/113.

### Issue: Skins not calculating correctly
**Solution**: Ensure all players have scores entered for the same holes.

### Issue: Leaderboard not updating
**Solution**: Make sure to call `tournament.recordScore()` after each score entry.

### Issue: Net scores not showing
**Solution**: Verify players have valid handicap indexes and playing handicaps are calculated.

## Advanced Features

### Custom Scoring Formats

You can extend the app to support custom formats:

```javascript
// Example: Stableford scoring
class StablefordTournament extends Tournament {
  calculateStablefordPoints(player, hole) {
    const netScore = player.getHoleScore(hole.number) - 
                     player.strokesPerHole[hole.number];
    const points = Math.max(0, 2 + hole.par - netScore);
    return points;
  }
}
```

### Real-time Updates

For web applications, implement WebSocket or polling:

```javascript
// Polling example
setInterval(async () => {
  const leaderboard = tournament.getLeaderboard(true);
  updateUI(leaderboard);
}, 5000); // Update every 5 seconds
```

## Support

For questions, issues, or feature requests, please refer to the main README.md file.

---

**Happy Golfing! ⛳**