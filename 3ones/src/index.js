import { Player } from './models/Player.js';
import { Course, Hole } from './models/Course.js';
import { Tournament } from './models/Tournament.js';
import { SkinsCalculator } from './utils/SkinsCalculator.js';
import { Leaderboard } from './components/Leaderboard.js';

/**
 * Golf Tournament App - Demo
 * Demonstrates all features: tournament management, live leaderboard, skins games, handicap calculations
 */

// Create a sample course
function createSampleCourse() {
  const course = new Course('Pebble Beach Golf Links');
  
  // Add 18 holes with par, handicap (stroke index), and yardage
  const holeData = [
    { number: 1, par: 4, handicap: 11, yardage: 380 },
    { number: 2, par: 5, handicap: 7, yardage: 502 },
    { number: 3, par: 4, handicap: 15, yardage: 388 },
    { number: 4, par: 4, handicap: 5, yardage: 327 },
    { number: 5, par: 3, handicap: 17, yardage: 188 },
    { number: 6, par: 5, handicap: 1, yardage: 523 },
    { number: 7, par: 3, handicap: 13, yardage: 106 },
    { number: 8, par: 4, handicap: 3, yardage: 431 },
    { number: 9, par: 4, handicap: 9, yardage: 464 },
    { number: 10, par: 4, handicap: 12, yardage: 446 },
    { number: 11, par: 4, handicap: 16, yardage: 380 },
    { number: 12, par: 3, handicap: 18, yardage: 202 },
    { number: 13, par: 4, handicap: 8, yardage: 399 },
    { number: 14, par: 5, handicap: 2, yardage: 573 },
    { number: 15, par: 4, handicap: 10, yardage: 397 },
    { number: 16, par: 4, handicap: 14, yardage: 402 },
    { number: 17, par: 3, handicap: 6, yardage: 178 },
    { number: 18, par: 5, handicap: 4, yardage: 543 }
  ];

  holeData.forEach(data => {
    const hole = new Hole(data.number, data.par, data.handicap, data.yardage);
    course.addHole(hole);
  });

  return course;
}

// Create sample players
function createSamplePlayers() {
  return [
    new Player('p1', 'Tiger Woods', 2.5),
    new Player('p2', 'Phil Mickelson', 5.8),
    new Player('p3', 'Rory McIlroy', 1.2),
    new Player('p4', 'Jordan Spieth', 3.4),
    new Player('p5', 'Brooks Koepka', 2.1),
    new Player('p6', 'Justin Thomas', 4.2)
  ];
}

// Simulate scores for players
function simulateScores(tournament) {
  const players = tournament.getAllPlayers();
  
  // Simulate 9 holes completed for demonstration
  for (let hole = 1; hole <= 9; hole++) {
    const holeInfo = tournament.course.getHole(hole);
    
    players.forEach(player => {
      // Generate realistic scores (par +/- 2)
      const variance = Math.floor(Math.random() * 5) - 2; // -2 to +2
      const score = Math.max(holeInfo.par + variance, 2); // Minimum score of 2
      tournament.recordScore(player.id, hole, score);
    });
  }
}

// Main demo function
function runDemo() {
  console.log('\n╔════════════════════════════════════════════════════════════╗');
  console.log('║         GOLF TOURNAMENT APP - DEMONSTRATION                ║');
  console.log('╚════════════════════════════════════════════════════════════╝\n');

  // 1. Create tournament
  console.log('📋 Creating tournament...\n');
  const course = createSampleCourse();
  const tournament = new Tournament('Spring Classic 2026', course, 'stroke-play');
  
  console.log(`Tournament: ${tournament.name}`);
  console.log(`Course: ${course.name}`);
  console.log(`Par: ${course.getTotalPar()}`);
  console.log(`Format: ${tournament.format}\n`);

  // 2. Add players
  console.log('👥 Adding players...\n');
  const players = createSamplePlayers();
  players.forEach(player => {
    tournament.addPlayer(player);
    console.log(`✓ ${player.name} (Handicap Index: ${player.handicapIndex}, Playing Handicap: ${player.playingHandicap})`);
  });

  // 3. Start tournament
  console.log('\n🏌️ Starting tournament...\n');
  tournament.start();

  // 4. Simulate some scores
  console.log('⛳ Simulating scores (9 holes)...\n');
  simulateScores(tournament);

  // 5. Display live leaderboard (Gross)
  console.log('\n📊 GROSS LEADERBOARD:');
  const grossLeaderboard = tournament.getLeaderboard(false);
  console.log(Leaderboard.formatConsole(grossLeaderboard, false));

  // 6. Display live leaderboard (Net)
  console.log('\n📊 NET LEADERBOARD:');
  const netLeaderboard = tournament.getLeaderboard(true);
  console.log(Leaderboard.formatConsole(netLeaderboard, true));

  // 7. Display sample scorecard
  console.log('\n📝 SAMPLE SCORECARD:');
  const samplePlayer = tournament.getPlayer('p1');
  console.log(Leaderboard.formatScorecard(samplePlayer, course));

  // 8. Calculate skins games
  console.log('\n💰 SKINS GAME RESULTS:\n');
  
  // Prepare strokes per hole for net skins
  const strokesPerHole = {};
  tournament.getAllPlayers().forEach(player => {
    strokesPerHole[player.id] = player.strokesPerHole;
  });

  // Calculate gross skins
  const grossSkins = SkinsCalculator.calculateSkins(tournament.getAllPlayers(), {}, false);
  console.log(SkinsCalculator.formatResults(grossSkins));

  // Calculate net skins
  const netSkins = SkinsCalculator.calculateSkins(tournament.getAllPlayers(), strokesPerHole, true);
  console.log(SkinsCalculator.formatResults(netSkins));

  // 9. Calculate skins payout
  console.log('\n💵 SKINS PAYOUT (Entry: $20 per player):\n');
  const grossPayout = SkinsCalculator.calculatePayout(grossSkins, 20, tournament.players.size);
  console.log('GROSS SKINS:');
  console.log(`Total Pot: $${grossPayout.totalPot}`);
  console.log(`Value per Skin: $${grossPayout.valuePerSkin.toFixed(2)}\n`);
  Object.values(grossPayout.payouts).forEach(payout => {
    console.log(`${payout.name}: ${payout.skins} skin(s) = $${payout.amount.toFixed(2)}`);
  });

  const netPayout = SkinsCalculator.calculatePayout(netSkins, 20, tournament.players.size);
  console.log('\nNET SKINS:');
  console.log(`Total Pot: $${netPayout.totalPot}`);
  console.log(`Value per Skin: $${netPayout.valuePerSkin.toFixed(2)}\n`);
  Object.values(netPayout.payouts).forEach(payout => {
    console.log(`${payout.name}: ${payout.skins} skin(s) = $${payout.amount.toFixed(2)}`);
  });

  // 10. Display summary
  console.log('\n\n📈 TOURNAMENT SUMMARY:\n');
  const summary = Leaderboard.getSummary(grossLeaderboard);
  console.log(`Total Players: ${summary.totalPlayers}`);
  console.log(`Completed: ${summary.completed}`);
  console.log(`In Progress: ${summary.inProgress}`);
  console.log(`Not Started: ${summary.notStarted}`);
  if (summary.leader) {
    console.log(`\nCurrent Leader: ${summary.leader.name}`);
    console.log(`Score: ${summary.leader.score} (${summary.leader.toPar})`);
    console.log(`Through: ${summary.leader.holesCompleted} holes`);
  }

  console.log('\n╔════════════════════════════════════════════════════════════╗');
  console.log('║                    DEMO COMPLETE                           ║');
  console.log('╚════════════════════════════════════════════════════════════╝\n');
}

// Run the demo
runDemo();

// Export for use as a module
export { Player, Course, Hole, Tournament, SkinsCalculator, Leaderboard };

// Made with Bob
