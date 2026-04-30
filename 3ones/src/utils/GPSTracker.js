/**
 * GPS Tracker Utility
 * Handles GPS location tracking, distance calculations, and course mapping
 */

export class GPSTracker {
  constructor() {
    this.currentPosition = null;
    this.watchId = null;
    this.isTracking = false;
    this.positionHistory = [];
    this.accuracy = null;
  }

  /**
   * Check if GPS is available
   * @returns {boolean} True if geolocation is supported
   */
  static isGPSAvailable() {
    return 'geolocation' in navigator;
  }

  /**
   * Request GPS permission and get current position
   * @returns {Promise<Object>} Position object with coords
   */
  async getCurrentPosition() {
    if (!GPSTracker.isGPSAvailable()) {
      throw new Error('GPS is not available on this device');
    }

    return new Promise((resolve, reject) => {
      navigator.geolocation.getCurrentPosition(
        (position) => {
          this.currentPosition = {
            latitude: position.coords.latitude,
            longitude: position.coords.longitude,
            altitude: position.coords.altitude,
            accuracy: position.coords.accuracy,
            timestamp: position.timestamp
          };
          this.accuracy = position.coords.accuracy;
          resolve(this.currentPosition);
        },
        (error) => {
          reject(this.handleGPSError(error));
        },
        {
          enableHighAccuracy: true,
          timeout: 10000,
          maximumAge: 0
        }
      );
    });
  }

  /**
   * Start continuous GPS tracking
   * @param {Function} callback - Called with each position update
   * @returns {number} Watch ID
   */
  startTracking(callback) {
    if (!GPSTracker.isGPSAvailable()) {
      throw new Error('GPS is not available on this device');
    }

    this.isTracking = true;
    this.watchId = navigator.geolocation.watchPosition(
      (position) => {
        this.currentPosition = {
          latitude: position.coords.latitude,
          longitude: position.coords.longitude,
          altitude: position.coords.altitude,
          accuracy: position.coords.accuracy,
          timestamp: position.timestamp
        };
        this.accuracy = position.coords.accuracy;
        this.positionHistory.push(this.currentPosition);
        
        if (callback) {
          callback(this.currentPosition);
        }
      },
      (error) => {
        console.error('GPS tracking error:', this.handleGPSError(error));
      },
      {
        enableHighAccuracy: true,
        timeout: 5000,
        maximumAge: 0
      }
    );

    return this.watchId;
  }

  /**
   * Stop GPS tracking
   */
  stopTracking() {
    if (this.watchId !== null) {
      navigator.geolocation.clearWatch(this.watchId);
      this.watchId = null;
      this.isTracking = false;
    }
  }

  /**
   * Calculate distance between two GPS coordinates using Haversine formula
   * @param {number} lat1 - Latitude of point 1
   * @param {number} lon1 - Longitude of point 1
   * @param {number} lat2 - Latitude of point 2
   * @param {number} lon2 - Longitude of point 2
   * @returns {number} Distance in yards
   */
  static calculateDistance(lat1, lon1, lat2, lon2) {
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
    const distanceYards = distanceMeters * 1.09361; // Convert to yards

    return Math.round(distanceYards);
  }

  /**
   * Calculate distance from current position to target
   * @param {number} targetLat - Target latitude
   * @param {number} targetLon - Target longitude
   * @returns {number} Distance in yards
   */
  getDistanceToTarget(targetLat, targetLon) {
    if (!this.currentPosition) {
      throw new Error('Current position not available');
    }

    return GPSTracker.calculateDistance(
      this.currentPosition.latitude,
      this.currentPosition.longitude,
      targetLat,
      targetLon
    );
  }

  /**
   * Calculate bearing (direction) to target
   * @param {number} targetLat - Target latitude
   * @param {number} targetLon - Target longitude
   * @returns {number} Bearing in degrees (0-360)
   */
  getBearingToTarget(targetLat, targetLon) {
    if (!this.currentPosition) {
      throw new Error('Current position not available');
    }

    const φ1 = this.currentPosition.latitude * Math.PI / 180;
    const φ2 = targetLat * Math.PI / 180;
    const Δλ = (targetLon - this.currentPosition.longitude) * Math.PI / 180;

    const y = Math.sin(Δλ) * Math.cos(φ2);
    const x = Math.cos(φ1) * Math.sin(φ2) -
              Math.sin(φ1) * Math.cos(φ2) * Math.cos(Δλ);
    const θ = Math.atan2(y, x);
    const bearing = (θ * 180 / Math.PI + 360) % 360;

    return Math.round(bearing);
  }

  /**
   * Get compass direction from bearing
   * @param {number} bearing - Bearing in degrees
   * @returns {string} Compass direction (N, NE, E, etc.)
   */
  static getCompassDirection(bearing) {
    const directions = ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW'];
    const index = Math.round(bearing / 45) % 8;
    return directions[index];
  }

  /**
   * Calculate shot distance (distance traveled)
   * @returns {number} Distance in yards
   */
  calculateShotDistance() {
    if (this.positionHistory.length < 2) {
      return 0;
    }

    const start = this.positionHistory[this.positionHistory.length - 2];
    const end = this.positionHistory[this.positionHistory.length - 1];

    return GPSTracker.calculateDistance(
      start.latitude,
      start.longitude,
      end.latitude,
      end.longitude
    );
  }

  /**
   * Get total distance traveled
   * @returns {number} Total distance in yards
   */
  getTotalDistanceTraveled() {
    if (this.positionHistory.length < 2) {
      return 0;
    }

    let totalDistance = 0;
    for (let i = 1; i < this.positionHistory.length; i++) {
      const prev = this.positionHistory[i - 1];
      const curr = this.positionHistory[i];
      totalDistance += GPSTracker.calculateDistance(
        prev.latitude,
        prev.longitude,
        curr.latitude,
        curr.longitude
      );
    }

    return Math.round(totalDistance);
  }

  /**
   * Clear position history
   */
  clearHistory() {
    this.positionHistory = [];
  }

  /**
   * Handle GPS errors
   * @param {Object} error - Geolocation error object
   * @returns {string} Error message
   */
  handleGPSError(error) {
    switch (error.code) {
      case error.PERMISSION_DENIED:
        return 'GPS permission denied. Please enable location services.';
      case error.POSITION_UNAVAILABLE:
        return 'GPS position unavailable. Please check your device settings.';
      case error.TIMEOUT:
        return 'GPS request timed out. Please try again.';
      default:
        return 'An unknown GPS error occurred.';
    }
  }

  /**
   * Get GPS status information
   * @returns {Object} Status object
   */
  getStatus() {
    return {
      isAvailable: GPSTracker.isGPSAvailable(),
      isTracking: this.isTracking,
      hasPosition: this.currentPosition !== null,
      accuracy: this.accuracy,
      historyCount: this.positionHistory.length
    };
  }

  /**
   * Export position history as JSON
   * @returns {string} JSON string of position history
   */
  exportHistory() {
    return JSON.stringify(this.positionHistory, null, 2);
  }
}

/**
 * GPS Course Mapper
 * Maps golf course holes with GPS coordinates
 */
export class GPSCourseMapper {
  constructor(course) {
    this.course = course;
    this.holeLocations = new Map(); // Map of hole number to GPS coordinates
  }

  /**
   * Set GPS coordinates for a hole
   * @param {number} holeNumber - Hole number
   * @param {Object} teeBox - Tee box coordinates {lat, lon}
   * @param {Object} green - Green coordinates {lat, lon}
   * @param {Array} hazards - Array of hazard coordinates
   */
  setHoleLocation(holeNumber, teeBox, green, hazards = []) {
    this.holeLocations.set(holeNumber, {
      holeNumber,
      teeBox,
      green,
      hazards,
      distance: GPSTracker.calculateDistance(
        teeBox.lat,
        teeBox.lon,
        green.lat,
        green.lon
      )
    });
  }

  /**
   * Get hole location data
   * @param {number} holeNumber - Hole number
   * @returns {Object|null} Hole location data
   */
  getHoleLocation(holeNumber) {
    return this.holeLocations.get(holeNumber) || null;
  }

  /**
   * Calculate distance to green from current position
   * @param {number} holeNumber - Hole number
   * @param {number} currentLat - Current latitude
   * @param {number} currentLon - Current longitude
   * @returns {number} Distance in yards
   */
  getDistanceToGreen(holeNumber, currentLat, currentLon) {
    const holeLocation = this.holeLocations.get(holeNumber);
    if (!holeLocation) {
      throw new Error(`Hole ${holeNumber} location not found`);
    }

    return GPSTracker.calculateDistance(
      currentLat,
      currentLon,
      holeLocation.green.lat,
      holeLocation.green.lon
    );
  }

  /**
   * Get nearest hazard from current position
   * @param {number} holeNumber - Hole number
   * @param {number} currentLat - Current latitude
   * @param {number} currentLon - Current longitude
   * @returns {Object|null} Nearest hazard with distance
   */
  getNearestHazard(holeNumber, currentLat, currentLon) {
    const holeLocation = this.holeLocations.get(holeNumber);
    if (!holeLocation || !holeLocation.hazards.length) {
      return null;
    }

    let nearest = null;
    let minDistance = Infinity;

    holeLocation.hazards.forEach(hazard => {
      const distance = GPSTracker.calculateDistance(
        currentLat,
        currentLon,
        hazard.lat,
        hazard.lon
      );

      if (distance < minDistance) {
        minDistance = distance;
        nearest = { ...hazard, distance };
      }
    });

    return nearest;
  }

  /**
   * Export course map as JSON
   * @returns {Object} Course map data
   */
  exportMap() {
    const mapData = {
      courseName: this.course.name,
      holes: []
    };

    this.holeLocations.forEach((location, holeNumber) => {
      mapData.holes.push(location);
    });

    return mapData;
  }

  /**
   * Import course map from JSON
   * @param {Object} mapData - Course map data
   */
  importMap(mapData) {
    if (mapData.holes) {
      mapData.holes.forEach(hole => {
        this.setHoleLocation(
          hole.holeNumber,
          hole.teeBox,
          hole.green,
          hole.hazards
        );
      });
    }
  }
}

// Made with Bob