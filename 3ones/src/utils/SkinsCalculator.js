/**
 * Skins Calculator
 * Calculates skins game results for gross and net scoring
 */
export class SkinsCalculator {
  /**
   * Calculate skins for a round (gross or net)
   * A skin is won when a player has the lowest score on a hole with no ties
   *
   * @param {Array} players - Array of Player objects
   * @param {Object} strokesPerHole - Map of player ID to strokes per hole (for net scoring)
   * @param {boolean} isNet - True for net skins, false for gross skins
   * @param {boolean} allowCarryover - True to allow carryovers, false to push to next hole
   * @returns {Object} Skins results
   */
  static calculateSkins(players, strokesPerHole = {}, isNet = false, allowCarryover = true) {
    const results = {
      skins: [], // Array of skin results per hole
      playerSkins: {}, // Count of skins won per player
      carryovers: 0, // Number of holes with carryovers
      totalValue: 0 // Total value of all skins
    };

    // Initialize player skins count
    players.forEach(player => {
      results.playerSkins[player.id] = {
        name: player.name,
        count: 0,
        holes: [],
        value: 0
      };
    });

    let carryoverValue = 1; // Start with 1 skin value per hole

    // Check each hole
    for (let holeNumber = 1; holeNumber <= 18; holeNumber++) {
      const holeScores = [];

      // Get scores for this hole from all players
      players.forEach(player => {
        const grossScore = player.getHoleScore(holeNumber);
        
        if (grossScore !== null) {
          let score = grossScore;
          
          // Apply handicap strokes for net scoring
          if (isNet && strokesPerHole[player.id]) {
            const strokes = strokesPerHole[player.id][holeNumber] || 0;
            score = grossScore - strokes;
          }
          
          holeScores.push({
            playerId: player.id,
            playerName: player.name,
            score: score,
            grossScore: grossScore
          });
        }
      });

      // Find the lowest score
      if (holeScores.length > 0) {
        const lowestScore = Math.min(...holeScores.map(s => s.score));
        const winners = holeScores.filter(s => s.score === lowestScore);

        if (winners.length === 1) {
          // Single winner - award the skin(s)
          const winner = winners[0];
          
          results.skins.push({
            hole: holeNumber,
            winner: winner.playerName,
            winnerId: winner.playerId,
            score: winner.score,
            grossScore: winner.grossScore,
            value: carryoverValue,
            isNet: isNet
          });

          results.playerSkins[winner.playerId].count += carryoverValue;
          results.playerSkins[winner.playerId].holes.push(holeNumber);
          results.playerSkins[winner.playerId].value += carryoverValue;
          
          // Reset carryover
          carryoverValue = 1;
        } else {
          // Tie - handle based on carryover setting
          if (allowCarryover) {
            // Carryover to next hole
            results.skins.push({
              hole: holeNumber,
              winner: null,
              score: lowestScore,
              tied: winners.map(w => w.playerName),
              value: carryoverValue,
              carryover: true,
              isNet: isNet
            });
            
            carryoverValue += 1;
            results.carryovers++;
          } else {
            // No carryover - skin is lost (push)
            results.skins.push({
              hole: holeNumber,
              winner: null,
              score: lowestScore,
              tied: winners.map(w => w.playerName),
              value: 0,
              push: true,
              isNet: isNet
            });
            
            // Reset carryover value
            carryoverValue = 1;
          }
        }
      } else {
        // No scores recorded for this hole
        if (allowCarryover) {
          results.skins.push({
            hole: holeNumber,
            winner: null,
            score: null,
            value: carryoverValue,
            noScores: true
          });
          carryoverValue += 1;
        } else {
          results.skins.push({
            hole: holeNumber,
            winner: null,
            score: null,
            value: 0,
            noScores: true
          });
          carryoverValue = 1;
        }
      }
    }

    // Calculate total value
    results.totalValue = Object.values(results.playerSkins)
      .reduce((sum, player) => sum + player.value, 0);

    return results;
  }

  /**
   * Calculate both gross and net skins
   * 
   * @param {Array} players - Array of Player objects
   * @param {Object} strokesPerHole - Map of player ID to strokes per hole
   * @returns {Object} Combined results for gross and net skins
   */
  static calculateBothSkins(players, strokesPerHole = {}) {
    return {
      gross: this.calculateSkins(players, {}, false),
      net: this.calculateSkins(players, strokesPerHole, true)
    };
  }

  /**
   * Calculate skins payout based on entry fee
   * 
   * @param {Object} skinsResults - Results from calculateSkins
   * @param {number} entryFee - Entry fee per player
   * @param {number} numberOfPlayers - Total number of players
   * @returns {Object} Payout per player
   */
  static calculatePayout(skinsResults, entryFee, numberOfPlayers) {
    const totalPot = entryFee * numberOfPlayers;
    const payout = {};

    if (skinsResults.totalValue > 0) {
      const valuePerSkin = totalPot / skinsResults.totalValue;

      Object.entries(skinsResults.playerSkins).forEach(([playerId, data]) => {
        if (data.count > 0) {
          payout[playerId] = {
            name: data.name,
            skins: data.count,
            amount: data.value * valuePerSkin
          };
        }
      });
    }

    return {
      totalPot: totalPot,
      valuePerSkin: skinsResults.totalValue > 0 ? totalPot / skinsResults.totalValue : 0,
      payouts: payout
    };
  }

  /**
   * Get skins summary for display
   * 
   * @param {Object} skinsResults - Results from calculateSkins
   * @returns {Array} Summary array sorted by skins won
   */
  static getSkinsSummary(skinsResults) {
    return Object.entries(skinsResults.playerSkins)
      .map(([playerId, data]) => ({
        playerId: playerId,
        name: data.name,
        skins: data.count,
        holes: data.holes,
        value: data.value
      }))
      .sort((a, b) => b.skins - a.skins);
  }

  /**
   * Format skins results for display
   * 
   * @param {Object} skinsResults - Results from calculateSkins
   * @returns {string} Formatted string
   */
  static formatResults(skinsResults) {
    let output = `\n=== SKINS GAME RESULTS (${skinsResults.skins[0]?.isNet ? 'NET' : 'GROSS'}) ===\n\n`;
    
    // Hole by hole
    output += 'Hole-by-Hole:\n';
    skinsResults.skins.forEach(skin => {
      if (skin.winner) {
        output += `Hole ${skin.hole}: ${skin.winner} (${skin.score}) - ${skin.value} skin(s)\n`;
      } else if (skin.carryover) {
        output += `Hole ${skin.hole}: TIE (${skin.score}) - Carryover (${skin.value} skin value)\n`;
      } else if (skin.push) {
        output += `Hole ${skin.hole}: TIE (${skin.score}) - Push (no carryover)\n`;
      } else if (skin.noScores) {
        output += `Hole ${skin.hole}: No scores recorded\n`;
      }
    });

    // Summary
    output += '\nSummary:\n';
    const summary = this.getSkinsSummary(skinsResults);
    summary.forEach(player => {
      if (player.skins > 0) {
        output += `${player.name}: ${player.skins} skin(s) on holes ${player.holes.join(', ')}\n`;
      }
    });

    output += `\nTotal Skins: ${skinsResults.totalValue}\n`;
    output += `Carryovers: ${skinsResults.carryovers}\n`;

    return output;
  }
}

// Made with Bob
