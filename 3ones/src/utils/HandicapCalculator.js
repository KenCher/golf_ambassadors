/**
 * Handicap Calculator
 * Calculates playing handicaps and course handicaps based on USGA rules
 */
export class HandicapCalculator {
  /**
   * Calculate Course Handicap
   * Formula: Handicap Index × (Slope Rating ÷ 113) + (Course Rating - Par)
   * 
   * @param {number} handicapIndex - Player's USGA Handicap Index
   * @param {number} slopeRating - Course slope rating (typically 55-155, standard is 113)
   * @param {number} courseRating - Course rating
   * @param {number} par - Course par
   * @returns {number} Course handicap (rounded)
   */
  static calculateCourseHandicap(handicapIndex, slopeRating = 113, courseRating = 72, par = 72) {
    const courseHandicap = handicapIndex * (slopeRating / 113) + (courseRating - par);
    return Math.round(courseHandicap);
  }

  /**
   * Calculate Playing Handicap
   * For different formats (stroke play, match play, etc.)
   * 
   * @param {number} courseHandicap - Course handicap
   * @param {number} handicapAllowance - Percentage of handicap to use (e.g., 0.95 for 95%)
   * @returns {number} Playing handicap (rounded)
   */
  static calculatePlayingHandicap(courseHandicap, handicapAllowance = 1.0) {
    return Math.round(courseHandicap * handicapAllowance);
  }

  /**
   * Calculate strokes received per hole based on playing handicap
   * 
   * @param {number} playingHandicap - Playing handicap
   * @param {Array} holes - Array of hole objects with handicap (stroke index)
   * @returns {Object} Map of hole number to strokes received
   */
  static calculateStrokesPerHole(playingHandicap, holes) {
    const strokesPerHole = {};
    
    holes.forEach(hole => {
      // Calculate how many strokes this hole receives
      // If playing handicap is 18+, player gets 2 strokes on some holes
      const fullRounds = Math.floor(playingHandicap / 18);
      const remainder = playingHandicap % 18;
      
      let strokes = fullRounds;
      if (hole.handicap <= remainder) {
        strokes += 1;
      }
      
      strokesPerHole[hole.number] = strokes;
    });
    
    return strokesPerHole;
  }

  /**
   * Calculate net score for a hole
   * 
   * @param {number} grossScore - Actual strokes taken
   * @param {number} strokesReceived - Strokes received on this hole
   * @returns {number} Net score
   */
  static calculateNetScore(grossScore, strokesReceived) {
    return grossScore - strokesReceived;
  }

  /**
   * Calculate total net score for a round
   * 
   * @param {Array} grossScores - Array of gross scores per hole
   * @param {Object} strokesPerHole - Map of hole number to strokes received
   * @returns {number} Total net score
   */
  static calculateTotalNetScore(grossScores, strokesPerHole) {
    return grossScores.reduce((total, score, index) => {
      const holeNumber = index + 1;
      const strokes = strokesPerHole[holeNumber] || 0;
      return total + this.calculateNetScore(score, strokes);
    }, 0);
  }

  /**
   * Calculate handicap differential (for updating handicap index)
   * Formula: (Adjusted Gross Score - Course Rating) × (113 ÷ Slope Rating)
   * 
   * @param {number} adjustedGrossScore - Score after ESC adjustments
   * @param {number} courseRating - Course rating
   * @param {number} slopeRating - Slope rating
   * @returns {number} Handicap differential
   */
  static calculateHandicapDifferential(adjustedGrossScore, courseRating, slopeRating) {
    return ((adjustedGrossScore - courseRating) * 113) / slopeRating;
  }

  /**
   * Apply Equitable Stroke Control (ESC)
   * Limits maximum score per hole based on course handicap
   * 
   * @param {number} score - Actual score on hole
   * @param {number} par - Par for the hole
   * @param {number} courseHandicap - Player's course handicap
   * @returns {number} Adjusted score
   */
  static applyESC(score, par, courseHandicap) {
    let maxScore;
    
    if (courseHandicap <= 9) {
      maxScore = par + 2; // Double bogey
    } else if (courseHandicap <= 19) {
      maxScore = 7;
    } else if (courseHandicap <= 29) {
      maxScore = 8;
    } else if (courseHandicap <= 39) {
      maxScore = 9;
    } else {
      maxScore = 10;
    }
    
    return Math.min(score, maxScore);
  }

  /**
   * Calculate recommended handicap allowances for different formats
   * 
   * @param {string} format - Tournament format
   * @returns {number} Handicap allowance percentage
   */
  static getHandicapAllowance(format) {
    const allowances = {
      'stroke-play': 0.95,           // 95% for individual stroke play
      'match-play': 1.0,             // 100% for match play
      'four-ball-stroke': 0.85,      // 85% for four-ball stroke play
      'four-ball-match': 0.90,       // 90% for four-ball match play
      'scramble-4': 0.25,            // 25% for 4-person scramble
      'scramble-2': 0.35,            // 35% for 2-person scramble
      'best-ball': 0.90,             // 90% for best ball
      'stableford': 0.95             // 95% for Stableford
    };
    
    return allowances[format] || 1.0;
  }
}

// Made with Bob
