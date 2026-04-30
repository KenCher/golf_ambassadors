/**
 * Player Model
 * Represents a golfer in the tournament with GPS tracking
 */
export class Player {
  constructor(id, name, handicapIndex) {
    this.id = id;
    this.name = name;
    this.handicapIndex = handicapIndex; // USGA Handicap Index
    this.scores = []; // Array of hole scores for current round
    this.totalStrokes = 0;
    this.netScore = 0;
    
    // GPS tracking data
    this.gpsEnabled = false;
    this.currentLocation = null; // {lat, lon, accuracy, timestamp}
    this.shotHistory = []; // Array of shot locations with GPS data
    this.distanceTracking = []; // Distance traveled per hole
  }

  /**
   * Enable GPS tracking for this player
   */
  enableGPS() {
    this.gpsEnabled = true;
  }

  /**
   * Disable GPS tracking for this player
   */
  disableGPS() {
    this.gpsEnabled = false;
  }

  /**
   * Update player's current GPS location
   * @param {number} latitude - Current latitude
   * @param {number} longitude - Current longitude
   * @param {number} accuracy - GPS accuracy in meters
   */
  updateLocation(latitude, longitude, accuracy = null) {
    this.currentLocation = {
      lat: latitude,
      lon: longitude,
      accuracy,
      timestamp: Date.now()
    };
  }

  /**
   * Record a shot with GPS location
   * @param {number} holeNumber - Hole number
   * @param {number} latitude - Shot latitude
   * @param {number} longitude - Shot longitude
   * @param {number} shotNumber - Shot number on this hole
   */
  recordShotLocation(holeNumber, latitude, longitude, shotNumber) {
    const shot = {
      holeNumber,
      shotNumber,
      lat: latitude,
      lon: longitude,
      timestamp: Date.now()
    };
    
    // Calculate distance from previous shot if available
    if (this.shotHistory.length > 0) {
      const lastShot = this.shotHistory[this.shotHistory.length - 1];
      if (lastShot.holeNumber === holeNumber) {
        shot.distance = this.calculateDistance(
          lastShot.lat, lastShot.lon,
          latitude, longitude
        );
      }
    }
    
    this.shotHistory.push(shot);
  }

  /**
   * Get all shots for a specific hole
   * @param {number} holeNumber - Hole number
   * @returns {Array} Array of shot objects
   */
  getHoleShots(holeNumber) {
    return this.shotHistory.filter(shot => shot.holeNumber === holeNumber);
  }

  /**
   * Calculate total distance walked for a hole
   * @param {number} holeNumber - Hole number
   * @returns {number} Total distance in yards
   */
  getHoleDistance(holeNumber) {
    const shots = this.getHoleShots(holeNumber);
    if (shots.length < 2) return 0;
    
    let totalDistance = 0;
    for (let i = 1; i < shots.length; i++) {
      totalDistance += this.calculateDistance(
        shots[i - 1].lat, shots[i - 1].lon,
        shots[i].lat, shots[i].lon
      );
    }
    return Math.round(totalDistance);
  }

  /**
   * Calculate distance between two GPS coordinates
   * @param {number} lat1 - Latitude 1
   * @param {number} lon1 - Longitude 1
   * @param {number} lat2 - Latitude 2
   * @param {number} lon2 - Longitude 2
   * @returns {number} Distance in yards
   */
  calculateDistance(lat1, lon1, lat2, lon2) {
    const R = 6371000; // Earth's radius in meters
    const φ1 = lat1 * Math.PI / 180;
    const φ2 = lat2 * Math.PI / 180;
    const Δφ = (lat2 - lat1) * Math.PI / 180;
    const Δλ = (lon2 - lon1) * Math.PI / 180;

    const a = Math.sin(Δφ / 2) * Math.sin(Δφ / 2) +
              Math.cos(φ1) * Math.cos(φ2) *
              Math.sin(Δλ / 2) * Math.sin(Δλ / 2);
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));

    const distanceMeters = R * c;
    return Math.round(distanceMeters * 1.09361); // Convert to yards
  }

  /**
   * Get total distance walked for the round
   * @returns {number} Total distance in yards
   */
  getTotalDistanceWalked() {
    let total = 0;
    for (let hole = 1; hole <= 18; hole++) {
      total += this.getHoleDistance(hole);
    }
    return total;
  }

  /**
   * Clear GPS data for a new round
   */
  clearGPSData() {
    this.currentLocation = null;
    this.shotHistory = [];
    this.distanceTracking = [];
  }

  /**
   * Add a score for a hole
   * @param {number} holeNumber - Hole number (1-18)
   * @param {number} strokes - Number of strokes taken
   */
  addScore(holeNumber, strokes) {
    this.scores[holeNumber - 1] = strokes;
    this.calculateTotalStrokes();
  }

  /**
   * Calculate total strokes for completed holes
   */
  calculateTotalStrokes() {
    this.totalStrokes = this.scores.reduce((sum, score) => {
      return sum + (score || 0);
    }, 0);
  }

  /**
   * Get score for a specific hole
   * @param {number} holeNumber - Hole number (1-18)
   * @returns {number|null} Score or null if not played
   */
  getHoleScore(holeNumber) {
    return this.scores[holeNumber - 1] || null;
  }

  /**
   * Get number of holes completed
   * @returns {number} Number of holes with scores
   */
  getHolesCompleted() {
    return this.scores.filter(score => score !== undefined && score !== null).length;
  }

  /**
   * Check if round is complete
   * @returns {boolean} True if all 18 holes are scored
   */
  isRoundComplete() {
    return this.getHolesCompleted() === 18;
  }

  /**
   * Get player data as JSON
   * @returns {Object} Player data
  /**
   * Get player data as JSON
   * @returns {Object} Player data
   */
  toJSON() {
    return {
      id: this.id,
      name: this.name,
      handicapIndex: this.handicapIndex,
      scores: this.scores,
      totalStrokes: this.totalStrokes,
      netScore: this.netScore,
      holesCompleted: this.getHolesCompleted(),
      gps: {
        enabled: this.gpsEnabled,
        currentLocation: this.currentLocation,
        shotHistory: this.shotHistory,
        totalDistanceWalked: this.getTotalDistanceWalked()
      }
    };
  }

  /**
   * Export GPS data for analysis
   * @returns {Object} GPS tracking data
   */
  exportGPSData() {
    return {
      playerId: this.id,
      playerName: this.name,
      gpsEnabled: this.gpsEnabled,
      shotHistory: this.shotHistory,
      distanceByHole: Array.from({ length: 18 }, (_, i) => ({
        hole: i + 1,
        distance: this.getHoleDistance(i + 1),
        shots: this.getHoleShots(i + 1).length
      })),
      totalDistance: this.getTotalDistanceWalked()
    };
  }
}

// Made with Bob
