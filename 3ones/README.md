# Golf Tournament App

A comprehensive golf tournament management application with live leaderboard tracking, skins game calculations (gross and net), USGA handicap system integration, and **GPS-enabled course navigation**.

## Features

### 🏆 Tournament Management
- Create and manage golf tournaments
- Support for multiple tournament formats (stroke play, match play, scramble, etc.)
- Real-time score tracking
- Player registration and management

### 📊 Live Leaderboard
- Real-time leaderboard updates as scores are entered
- Gross and net scoring displays
- Score-to-par calculations
- Tie handling
- Progress tracking (holes completed)
- Multiple display formats (console, HTML, JSON)

### 💰 Skins Game Calculator
- **Gross Skins**: Based on actual scores
- **Net Skins**: Based on handicap-adjusted scores
- Automatic carryover handling for tied holes
- Payout calculations based on entry fees
- Detailed hole-by-hole results

### ⛳ Handicap System
- USGA Handicap Index support
- Course Handicap calculation
- Playing Handicap calculation with format-specific allowances
- Strokes-per-hole allocation based on hole difficulty
- Net score calculations
- Equitable Stroke Control (ESC) support

### 📍 GPS Features (NEW!)
- **Real-time GPS tracking** on the course
- **Distance to green** with live updates
- **Automatic course detection** via OpenStreetMap
- **Shot tracking** with distance measurements
- **Course mapping tool** for accurate hole data
- **Custom course database** with local storage
- **Mobile-optimized interface** for on-course use
- **Compass bearing** to target
- **GPS accuracy indicators**
- **Hybrid data approach**: Custom courses + OpenStreetMap + Manual mapping
- **Offline support** for saved courses

### 📝 Scorecards
- Individual player scorecards
- Front 9 / Back 9 / Total display
- Gross and net scores
- Handicap information
- GPS-tracked shot history (optional)

## Installation

```bash
# Clone or download the project
cd golf-tournament-app

# No dependencies required - uses Node.js built-in modules
node src/index.js
```

## Quick Start

### Running the Demo

```bash
npm start
# or
node src/index.js
```

The demo will:
1. Create a sample tournament at Pebble Beach
2. Add 6 players with different handicaps
3. Simulate 9 holes of play
4. Display gross and net leaderboards
5. Show a sample scorecard
6. Calculate gross and net skins
7. Calculate skins payouts

### Basic Usage

```javascript
import { Player, Course, Hole, Tournament, SkinsCalculator, Leaderboard } from './src/index.js';

// 1. Create a course
const course = new Course('My Golf Course');
for (let i = 1; i <= 18; i++) {
  const hole = new Hole(i, 4, i, 400); // number, par, handicap, yardage
  course.addHole(hole);
}

// 2. Create a tournament
const tournament = new Tournament('Club Championship', course, 'stroke-play');

// 3. Add players
const player1 = new Player('p1', 'John Doe', 10.5); // id, name, handicap index
tournament.addPlayer(player1);

// 4. Start tournament
tournament.start();

// 5. Record scores
tournament.recordScore('p1', 1, 5); // playerId, holeNumber, strokes

// 6. Get leaderboard
const leaderboard = tournament.getLeaderboard(false); // false = gross, true = net
console.log(Leaderboard.formatConsole(leaderboard));

// 7. Calculate skins
const players = tournament.getAllPlayers();
const strokesPerHole = {};
players.forEach(p => strokesPerHole[p.id] = p.strokesPerHole);

const grossSkins = SkinsCalculator.calculateSkins(players, {}, false);
const netSkins = SkinsCalculator.calculateSkins(players, strokesPerHole, true);
```

## API Reference

### Player Class

```javascript
const player = new Player(id, name, handicapIndex);

// Methods
player.addScore(holeNumber, strokes);
player.getHoleScore(holeNumber);
player.getHolesCompleted();
player.isRoundComplete();
player.toJSON();
```

### Course & Hole Classes

```javascript
const course = new Course(name);
const hole = new Hole(number, par, handicap, yardage);

// Course methods
course.addHole(hole);
course.getHole(holeNumber);
course.getTotalPar();
course.getCourseRating();
course.getSlopeRating();
```

### Tournament Class

```javascript
const tournament = new Tournament(name, course, format);

// Methods
tournament.addPlayer(player);
tournament.removePlayer(playerId);
tournament.getPlayer(playerId);
tournament.getAllPlayers();
tournament.start();
tournament.end();
tournament.recordScore(playerId, holeNumber, strokes);
tournament.getLeaderboard(useNet);
tournament.getSummary();
```

### HandicapCalculator

```javascript
import { HandicapCalculator } from './src/utils/HandicapCalculator.js';

// Calculate course handicap
const courseHandicap = HandicapCalculator.calculateCourseHandicap(
  handicapIndex,
  slopeRating,
  courseRating,
  par
);

// Calculate playing handicap
const playingHandicap = HandicapCalculator.calculatePlayingHandicap(
  courseHandicap,
  handicapAllowance
);

// Calculate strokes per hole
const strokesPerHole = HandicapCalculator.calculateStrokesPerHole(
  playingHandicap,
  holes
);

// Calculate net score
const netScore = HandicapCalculator.calculateNetScore(grossScore, strokesReceived);

// Get handicap allowance for format
const allowance = HandicapCalculator.getHandicapAllowance('stroke-play');
```

### SkinsCalculator

```javascript
import { SkinsCalculator } from './src/utils/SkinsCalculator.js';

// Calculate skins (gross or net)
const skins = SkinsCalculator.calculateSkins(players, strokesPerHole, isNet);

// Calculate both gross and net
const bothSkins = SkinsCalculator.calculateBothSkins(players, strokesPerHole);

// Calculate payout
const payout = SkinsCalculator.calculatePayout(skinsResults, entryFee, numberOfPlayers);

// Get summary
const summary = SkinsCalculator.getSkinsSummary(skinsResults);

// Format results
const formatted = SkinsCalculator.formatResults(skinsResults);
```

### Leaderboard

```javascript
import { Leaderboard } from './src/components/Leaderboard.js';

// Format for console
const consoleOutput = Leaderboard.formatConsole(leaderboard, useNet);

// Format as HTML
const htmlOutput = Leaderboard.formatHTML(leaderboard, useNet);

// Format as JSON
const jsonOutput = Leaderboard.formatJSON(leaderboard, useNet);

// Get summary statistics
const summary = Leaderboard.getSummary(leaderboard);

// Format player scorecard
const scorecard = Leaderboard.formatScorecard(player, course);
```

## Tournament Formats

The app supports various tournament formats with appropriate handicap allowances:

- **stroke-play**: 95% handicap allowance
- **match-play**: 100% handicap allowance
- **four-ball-stroke**: 85% handicap allowance
- **four-ball-match**: 90% handicap allowance
- **scramble-4**: 25% handicap allowance (4-person)
- **scramble-2**: 35% handicap allowance (2-person)
- **best-ball**: 90% handicap allowance
- **stableford**: 95% handicap allowance

## Handicap Calculations

### Course Handicap Formula
```
Course Handicap = Handicap Index × (Slope Rating ÷ 113) + (Course Rating - Par)
```

### Playing Handicap Formula
```
Playing Handicap = Course Handicap × Handicap Allowance
```

### Strokes Per Hole
Strokes are allocated based on the hole's handicap (stroke index):
- If playing handicap is 18 or less, player receives 1 stroke on holes with handicap ≤ playing handicap
- If playing handicap is greater than 18, player receives 2 strokes on some holes

### Net Score
```
Net Score = Gross Score - Strokes Received
```

## Skins Game Rules

### How Skins Work
1. A "skin" is won when a player has the lowest score on a hole with no ties
2. If there's a tie for lowest score, the skin carries over to the next hole
3. The next hole is worth 2 skins (original + carryover)
4. Carryovers continue to accumulate until someone wins outright

### Gross vs Net Skins
- **Gross Skins**: Based on actual strokes taken
- **Net Skins**: Based on strokes minus handicap allowance per hole

### Payout Calculation
```
Total Pot = Entry Fee × Number of Players
Value Per Skin = Total Pot ÷ Total Skins Won
Player Payout = Skins Won × Value Per Skin
```

## Project Structure

```
golf-tournament-app/
├── src/
│   ├── models/
│   │   ├── Player.js          # Player data model
│   │   ├── Course.js          # Course and Hole models
│   │   └── Tournament.js      # Tournament management
│   ├── utils/
│   │   ├── HandicapCalculator.js  # USGA handicap calculations
│   │   └── SkinsCalculator.js     # Skins game logic
│   ├── components/
│   │   └── Leaderboard.js     # Leaderboard display components
│   └── index.js               # Main entry point and demo
├── tests/                     # Test files (to be added)
├── public/                    # Public assets (for web version)
├── package.json
└── README.md
```

## GPS Usage

### 🎯 Quick Start with GPS

Golf4us now includes a complete GPS system with three main tools:

1. **GPS App** (`public/gps-app.html`) - Main tracking app
2. **Course Database Manager** (`public/course-database.html`) - Manage custom courses
3. **Course Mapper** (`public/course-mapper.html`) - Record accurate hole data

### Mobile GPS App

The main GPS tracking application with automatic course detection:

```bash
# Open on mobile device (HTTPS required for GPS)
open public/gps-app.html
```

**Features:**
- ✅ Automatic course detection via OpenStreetMap
- ✅ Real-time distance to green
- ✅ Compass bearing and direction
- ✅ Shot tracking and history
- ✅ Hole information with par and yardage
- ✅ GPS accuracy indicator
- ✅ Custom course database integration
- ✅ Offline support for saved courses

### Course Database Manager

Manage your custom course library:

```bash
# Open in any browser
open public/course-database.html
```

**Features:**
- Add courses manually with scorecard data
- Import courses from JSON files
- View and edit all saved courses
- Export database for backup
- Share courses with friends

### Course Mapper Tool

Walk the course and record accurate GPS coordinates:

```bash
# Open on mobile device at the golf course
open public/course-mapper.html
```

**Features:**
- Record tee box and green coordinates
- Enter hole details (par, stroke index, yardage)
- Export as JSON for import into database
- Works offline after initial load

### Data Sources

Golf4us uses a **hybrid approach** for course data:

1. **Custom Courses** - Manually mapped with accurate data (highest priority)
2. **OpenStreetMap** - Automatic discovery of nearby courses
3. **Fallback Database** - Pre-configured popular courses

See `HYBRID_DATA_APPROACH.md` for complete details.

### Using GPS in Your Code

```javascript
import { GPSTracker, GPSCourseMapper } from './src/utils/GPSTracker.js';
import { DistanceCalculator } from './src/utils/DistanceCalculator.js';

// Initialize GPS tracker
const gpsTracker = new GPSTracker();

// Request GPS permission and get current position
try {
  const position = await gpsTracker.getCurrentPosition();
  console.log('Current position:', position);
} catch (error) {
  console.error('GPS error:', error);
}

// Start continuous tracking
gpsTracker.startTracking((position) => {
  console.log('Position update:', position);
});

// Calculate distance to target
const distance = gpsTracker.getDistanceToTarget(targetLat, targetLon);
console.log(`Distance to green: ${distance} yards`);

// Get bearing to target
const bearing = gpsTracker.getBearingToTarget(targetLat, targetLon);
const direction = GPSTracker.getCompassDirection(bearing);
console.log(`Direction: ${direction} (${bearing}°)`);

// Stop tracking when done
gpsTracker.stopTracking();
```

### Setting Up Course GPS Data

```javascript
import { Course, Hole } from './src/models/Course.js';

const course = new Course('Pebble Beach');

// Set course location
course.setCourseLocation(36.5674, -121.9500);

// Create hole with GPS coordinates
const hole1 = new Hole(1, 4, 11, 380);

// Set tee box coordinates
hole1.setTeeBox(36.5674, -121.9500, 50); // lat, lon, elevation

// Set green coordinates
hole1.setGreen(36.5680, -121.9505, 65);

// Set fairway center
hole1.setFairwayCenter(36.5677, -121.9502);

// Add hazards
hole1.addHazard('water', 36.5676, -121.9503, 'Creek');
hole1.addHazard('bunker', 36.5679, -121.9504, 'Greenside Bunker');

course.addHole(hole1);
```

### Distance Calculations

```javascript
import { DistanceCalculator } from './src/utils/DistanceCalculator.js';

// Calculate distance between two points
const distance = DistanceCalculator.calculateDistance(
  lat1, lon1, lat2, lon2, 'yards'
);

// Calculate adjusted distance with elevation
const adjusted = DistanceCalculator.calculateAdjustedDistance(
  150, // horizontal distance in yards
  15   // elevation change in feet (positive = uphill)
);
console.log(`Playing distance: ${adjusted.playing} yards`);

// Get club recommendation
const club = DistanceCalculator.calculateClubSelection(
  165,  // distance in yards
  10,   // elevation change in feet
  15,   // wind speed in mph
  90,   // wind direction in degrees
  45    // target bearing in degrees
);
console.log(`Recommended club: ${club.club}`);
console.log(`Adjusted distance: ${club.adjustedDistance} yards`);
```

### GPS Visualization

```javascript
import { GPSVisualization } from './src/components/GPSVisualization.js';

// Render ASCII map
const map = GPSVisualization.renderHoleMap(hole, playerPosition);
console.log(map);

// Generate SVG map
const svg = GPSVisualization.renderSVGMap(hole, playerPosition, 600, 400);

// Create GPS dashboard HTML
const dashboard = GPSVisualization.renderGPSDashboard({
  hole: hole,
  playerPosition: position,
  distanceToGreen: 165,
  distanceToFairway: 45,
  bearing: 45,
  accuracy: 8
});
```

## Future Enhancements

- [ ] Web-based UI with real-time updates
- [ ] Database integration for data persistence
- [x] GPS distance tracking
- [x] Mobile app version
- [ ] Multiple round tournaments
- [ ] Team competitions
- [ ] Stableford scoring format
- [ ] Match play bracket system
- [ ] Statistics and analytics
- [ ] Player profiles and history
- [ ] Course database integration
- [ ] Weather integration
- [ ] Live scoring via mobile devices
- [ ] Automated notifications
- [ ] Export to PDF/Excel
- [ ] Augmented reality course overlay
- [ ] Apple Watch / Wear OS integration

## Contributing

Contributions are welcome! Please feel free to submit pull requests or open issues for bugs and feature requests.

## License

MIT License - feel free to use this project for your golf tournaments!

## Support

For questions or support, please open an issue on the project repository.

---

**Built with ❤️ for golfers by golfers**