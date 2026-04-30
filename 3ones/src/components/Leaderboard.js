/**
 * Leaderboard Component
 * Displays live tournament leaderboard
 */
export class Leaderboard {
  /**
   * Format leaderboard for console display
   * @param {Array} leaderboard - Leaderboard data from Tournament.getLeaderboard()
   * @param {boolean} useNet - Display net scores
   * @returns {string} Formatted leaderboard
   */
  static formatConsole(leaderboard, useNet = false) {
    let output = '\n';
    output += '═══════════════════════════════════════════════════════════════\n';
    output += `                    LIVE LEADERBOARD (${useNet ? 'NET' : 'GROSS'})                    \n`;
    output += '═══════════════════════════════════════════════════════════════\n';
    output += 'Pos  Player                    Score  Thru  To Par  Handicap\n';
    output += '───────────────────────────────────────────────────────────────\n';

    leaderboard.forEach(entry => {
      const pos = entry.tied ? `T${entry.rank}` : entry.rank.toString();
      const name = entry.name.padEnd(24);
      const score = entry.score > 0 ? entry.score.toString().padStart(3) : '---';
      const thru = entry.holesCompleted === 18 ? 'F' : entry.holesCompleted.toString();
      const toPar = entry.score > 0 ? entry.scoreToParStr.padStart(5) : '  ---';
      const handicap = entry.playingHandicap.toString().padStart(3);

      output += `${pos.padStart(3)}  ${name}  ${score}    ${thru.padStart(2)}   ${toPar}     ${handicap}\n`;
    });

    output += '═══════════════════════════════════════════════════════════════\n';
    
    return output;
  }

  /**
   * Format leaderboard as HTML
   * @param {Array} leaderboard - Leaderboard data
   * @param {boolean} useNet - Display net scores
   * @returns {string} HTML string
   */
  static formatHTML(leaderboard, useNet = false) {
    let html = `
      <div class="leaderboard">
        <h2>Live Leaderboard (${useNet ? 'Net' : 'Gross'})</h2>
        <table class="leaderboard-table">
          <thead>
            <tr>
              <th>Pos</th>
              <th>Player</th>
              <th>Score</th>
              <th>Thru</th>
              <th>To Par</th>
              <th>Handicap</th>
            </tr>
          </thead>
          <tbody>
    `;

    leaderboard.forEach(entry => {
      const pos = entry.tied ? `T${entry.rank}` : entry.rank;
      const score = entry.score > 0 ? entry.score : '---';
      const thru = entry.holesCompleted === 18 ? 'F' : entry.holesCompleted;
      const toPar = entry.score > 0 ? entry.scoreToParStr : '---';
      const rowClass = entry.isComplete ? 'complete' : 'in-progress';

      html += `
            <tr class="${rowClass}">
              <td class="pos">${pos}</td>
              <td class="player">${entry.name}</td>
              <td class="score">${score}</td>
              <td class="thru">${thru}</td>
              <td class="to-par ${entry.scoreToPar < 0 ? 'under' : entry.scoreToPar > 0 ? 'over' : 'even'}">${toPar}</td>
              <td class="handicap">${entry.playingHandicap}</td>
            </tr>
      `;
    });

    html += `
          </tbody>
        </table>
      </div>
    `;

    return html;
  }

  /**
   * Format leaderboard as JSON for API
   * @param {Array} leaderboard - Leaderboard data
   * @param {boolean} useNet - Display net scores
   * @returns {Object} JSON object
   */
  static formatJSON(leaderboard, useNet = false) {
    return {
      type: useNet ? 'net' : 'gross',
      timestamp: new Date().toISOString(),
      entries: leaderboard.map(entry => ({
        position: entry.rank,
        tied: entry.tied,
        player: {
          id: entry.playerId,
          name: entry.name,
          handicapIndex: entry.handicapIndex,
          playingHandicap: entry.playingHandicap
        },
        score: {
          gross: entry.grossScore,
          net: entry.netScore,
          display: entry.score,
          toPar: entry.scoreToPar,
          toParDisplay: entry.scoreToParStr
        },
        progress: {
          holesCompleted: entry.holesCompleted,
          isComplete: entry.isComplete
        }
      }))
    };
  }

  /**
   * Get live updates summary
   * @param {Array} leaderboard - Current leaderboard
   * @returns {Object} Summary statistics
   */
  static getSummary(leaderboard) {
    const completed = leaderboard.filter(e => e.isComplete).length;
    const inProgress = leaderboard.filter(e => !e.isComplete && e.holesCompleted > 0).length;
    const notStarted = leaderboard.filter(e => e.holesCompleted === 0).length;
    
    const leader = leaderboard[0];
    const lowScore = leader && leader.score > 0 ? leader.score : null;

    return {
      totalPlayers: leaderboard.length,
      completed: completed,
      inProgress: inProgress,
      notStarted: notStarted,
      leader: leader ? {
        name: leader.name,
        score: leader.score,
        toPar: leader.scoreToParStr,
        holesCompleted: leader.holesCompleted
      } : null,
      lowScore: lowScore
    };
  }

  /**
   * Format player scorecard
   * @param {Player} player - Player object
   * @param {Course} course - Course object
   * @returns {string} Formatted scorecard
   */
  static formatScorecard(player, course) {
    let output = '\n';
    output += '═══════════════════════════════════════════════════════════════\n';
    output += `                    ${player.name.toUpperCase()} - SCORECARD\n`;
    output += `                    Handicap: ${player.playingHandicap}\n`;
    output += '═══════════════════════════════════════════════════════════════\n';
    
    // Front 9
    output += 'Hole:  ';
    for (let i = 1; i <= 9; i++) output += `${i.toString().padStart(3)} `;
    output += ' OUT\n';
    
    output += 'Par:   ';
    for (let i = 1; i <= 9; i++) {
      const hole = course.getHole(i);
      output += `${hole.par.toString().padStart(3)} `;
    }
    const frontPar = course.holes.slice(0, 9).reduce((sum, h) => sum + h.par, 0);
    output += ` ${frontPar.toString().padStart(3)}\n`;
    
    output += 'Score: ';
    let frontScore = 0;
    for (let i = 1; i <= 9; i++) {
      const score = player.getHoleScore(i);
      output += score ? `${score.toString().padStart(3)} ` : '  - ';
      frontScore += score || 0;
    }
    output += ` ${frontScore > 0 ? frontScore.toString().padStart(3) : '  -'}\n`;
    
    output += '\n';
    
    // Back 9
    output += 'Hole:  ';
    for (let i = 10; i <= 18; i++) output += `${i.toString().padStart(3)} `;
    output += '  IN TOTAL\n';
    
    output += 'Par:   ';
    for (let i = 10; i <= 18; i++) {
      const hole = course.getHole(i);
      output += `${hole.par.toString().padStart(3)} `;
    }
    const backPar = course.holes.slice(9, 18).reduce((sum, h) => sum + h.par, 0);
    const totalPar = course.getTotalPar();
    output += ` ${backPar.toString().padStart(3)} ${totalPar.toString().padStart(3)}\n`;
    
    output += 'Score: ';
    let backScore = 0;
    for (let i = 10; i <= 18; i++) {
      const score = player.getHoleScore(i);
      output += score ? `${score.toString().padStart(3)} ` : '  - ';
      backScore += score || 0;
    }
    const total = player.totalStrokes;
    output += ` ${backScore > 0 ? backScore.toString().padStart(3) : '  -'} ${total > 0 ? total.toString().padStart(3) : '  -'}\n`;
    
    output += '═══════════════════════════════════════════════════════════════\n';
    output += `Gross Score: ${total > 0 ? total : '---'}  |  Net Score: ${player.netScore > 0 ? player.netScore : '---'}\n`;
    output += '═══════════════════════════════════════════════════════════════\n';
    
    return output;
  }
}

// Made with Bob
