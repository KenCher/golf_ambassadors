import { HandicapCalculator } from '../utils/HandicapCalculator.js';

/**
 * Tournament Model
 * Manages tournament state, players, and scoring
 */
export class Tournament {
  constructor(name, course, format = 'stroke-play') {
    this.name = name;
    this.course = course;
    this.format = format;
    this.players = new Map(); // Map of player ID to Player object
    this.startTime = null;
    this.endTime = null;
    this.status = 'setup'; // setup, in-progress, completed
  }

  /**
   * Add a player to the tournament
   * @param {Player} player - Player object
   */
  addPlayer(player) {
    this.players.set(player.id, player);
    
    // Calculate playing handicap for this player
    const courseHandicap = HandicapCalculator.calculateCourseHandicap(
      player.handicapIndex,
      this.course.getSlopeRating(),
      this.course.getCourseRating(),
      this.course.getTotalPar()
    );
    
    const handicapAllowance = HandicapCalculator.getHandicapAllowance(this.format);
    player.playingHandicap = HandicapCalculator.calculatePlayingHandicap(
      courseHandicap,
      handicapAllowance
    );
    
    // Calculate strokes per hole
    player.strokesPerHole = HandicapCalculator.calculateStrokesPerHole(
      player.playingHandicap,
      this.course.holes
    );
  }

  /**
   * Remove a player from the tournament
   * @param {string} playerId - Player ID
   */
  removePlayer(playerId) {
    this.players.delete(playerId);
  }

  /**
   * Get a player by ID
   * @param {string} playerId - Player ID
   * @returns {Player|undefined} Player object
   */
  getPlayer(playerId) {
    return this.players.get(playerId);
  }

  /**
   * Get all players as array
   * @returns {Array} Array of Player objects
   */
  getAllPlayers() {
    return Array.from(this.players.values());
  }

  /**
   * Start the tournament
   */
  start() {
    this.startTime = new Date();
    this.status = 'in-progress';
  }

  /**
   * End the tournament
   */
  end() {
    this.endTime = new Date();
    this.status = 'completed';
  }

  /**
   * Record a score for a player on a hole
   * @param {string} playerId - Player ID
   * @param {number} holeNumber - Hole number (1-18)
   * @param {number} strokes - Number of strokes
   */
  recordScore(playerId, holeNumber, strokes) {
    const player = this.getPlayer(playerId);
    if (player) {
      player.addScore(holeNumber, strokes);
      
      // Calculate net score
      const strokesReceived = player.strokesPerHole[holeNumber] || 0;
      const netScore = HandicapCalculator.calculateNetScore(strokes, strokesReceived);
      
      // Update player's total net score
      this.updatePlayerNetScore(player);
    }
  }

  /**
   * Update player's total net score
   * @param {Player} player - Player object
   */
  updatePlayerNetScore(player) {
    player.netScore = HandicapCalculator.calculateTotalNetScore(
      player.scores,
      player.strokesPerHole
    );
  }

  /**
   * Get leaderboard (sorted by score)
   * @param {boolean} useNet - Use net scores instead of gross
   * @returns {Array} Sorted array of players with rankings
   */
  getLeaderboard(useNet = false) {
    const players = this.getAllPlayers();
    
    // Sort players by score
    const sorted = players.sort((a, b) => {
      const scoreA = useNet ? a.netScore : a.totalStrokes;
      const scoreB = useNet ? b.netScore : b.totalStrokes;
      
      // Players with no scores go to bottom
      if (scoreA === 0 && scoreB === 0) return 0;
      if (scoreA === 0) return 1;
      if (scoreB === 0) return -1;
      
      return scoreA - scoreB;
    });

    // Add rankings and calculate score relative to par
    let currentRank = 1;
    let previousScore = null;
    let tiedCount = 0;

    return sorted.map((player, index) => {
      const score = useNet ? player.netScore : player.totalStrokes;
      const holesCompleted = player.getHolesCompleted();
      
      // Calculate ranking (handle ties)
      if (score === previousScore && score > 0) {
        tiedCount++;
      } else {
        currentRank = index + 1;
        tiedCount = 0;
      }
      previousScore = score;

      // Calculate score relative to par
      const parForHolesPlayed = this.course.holes
        .slice(0, holesCompleted)
        .reduce((sum, hole) => sum + hole.par, 0);
      
      const scoreToPar = score > 0 ? score - parForHolesPlayed : 0;
      const scoreToParStr = scoreToPar === 0 ? 'E' : 
                           scoreToPar > 0 ? `+${scoreToPar}` : 
                           `${scoreToPar}`;

      return {
        rank: currentRank,
        tied: tiedCount > 0,
        playerId: player.id,
        name: player.name,
        handicapIndex: player.handicapIndex,
        playingHandicap: player.playingHandicap,
        grossScore: player.totalStrokes,
        netScore: player.netScore,
        score: score,
        holesCompleted: holesCompleted,
        scoreToPar: scoreToPar,
        scoreToParStr: scoreToParStr,
        isComplete: player.isRoundComplete()
      };
    });
  }

  /**
   * Get tournament summary
   * @returns {Object} Tournament summary data
   */
  getSummary() {
    return {
      name: this.name,
      course: this.course.name,
      format: this.format,
      status: this.status,
      playerCount: this.players.size,
      startTime: this.startTime,
      endTime: this.endTime,
      leaderboard: this.getLeaderboard()
    };
  }

  /**
   * Export tournament data as JSON
   * @returns {Object} Tournament data
   */
  toJSON() {
    return {
      name: this.name,
      course: this.course.toJSON(),
      format: this.format,
      status: this.status,
      players: this.getAllPlayers().map(p => p.toJSON()),
      startTime: this.startTime,
      endTime: this.endTime
    };
  }
}

// Made with Bob
