/**
 * Course Model
 * Represents a golf course with hole information and GPS coordinates
 */
export class Course {
  constructor(name, holes = []) {
    this.name = name;
    this.holes = holes; // Array of Hole objects
    this.gpsEnabled = false;
    this.courseLocation = null; // {lat, lon} for course center
  }

  /**
   * Set course GPS location
   * @param {number} latitude - Course center latitude
   * @param {number} longitude - Course center longitude
   */
  setCourseLocation(latitude, longitude) {
    this.courseLocation = { lat: latitude, lon: longitude };
    this.gpsEnabled = true;
  }

  /**
   * Check if course has GPS data
   * @returns {boolean} True if GPS enabled
   */
  hasGPSData() {
    return this.gpsEnabled && this.holes.some(hole => hole.hasGPSCoordinates());
  }

  /**
   * Add a hole to the course
   * @param {Hole} hole - Hole object
   */
  addHole(hole) {
    this.holes.push(hole);
  }

  /**
   * Get hole by number
   * @param {number} holeNumber - Hole number (1-18)
   * @returns {Hole|null} Hole object or null
   */
  getHole(holeNumber) {
    return this.holes.find(hole => hole.number === holeNumber) || null;
  }

  /**
   * Get total par for the course
   * @returns {number} Total par
   */
  getTotalPar() {
    return this.holes.reduce((sum, hole) => sum + hole.par, 0);
  }

  /**
   * Get course rating
   * @returns {number} Course rating
   */
  getCourseRating() {
    return this.holes.reduce((sum, hole) => sum + hole.rating, 0) / this.holes.length;
  }

  /**
   * Get slope rating
   * @returns {number} Slope rating
   */
  getSlopeRating() {
    return this.holes.reduce((sum, hole) => sum + hole.slope, 0) / this.holes.length;
  }

  /**
   * Get course data as JSON
   * @returns {Object} Course data
   */
  toJSON() {
    return {
      name: this.name,
      holes: this.holes.map(hole => hole.toJSON()),
      totalPar: this.getTotalPar()
    };
  }
}

/**
 * Hole Model
 * Represents a single hole on the course with GPS coordinates
 */
export class Hole {
  constructor(number, par, handicap, yardage = 0) {
    this.number = number; // Hole number (1-18)
    this.par = par; // Par for the hole
    this.handicap = handicap; // Stroke index (1-18, difficulty ranking)
    this.yardage = yardage; // Length in yards
    this.rating = 0; // Hole rating (for course rating calculation)
    this.slope = 113; // Default slope rating
    
    // GPS coordinates
    this.teeBox = null; // {lat, lon, elevation}
    this.green = null; // {lat, lon, elevation}
    this.fairwayCenter = null; // {lat, lon}
    this.hazards = []; // Array of {type, lat, lon, name}
    this.layupPoints = []; // Array of {distance, lat, lon}
  }

  /**
   * Set tee box GPS coordinates
   * @param {number} latitude - Tee box latitude
   * @param {number} longitude - Tee box longitude
   * @param {number} elevation - Elevation in feet (optional)
   */
  setTeeBox(latitude, longitude, elevation = null) {
    this.teeBox = { lat: latitude, lon: longitude, elevation };
  }

  /**
   * Set green GPS coordinates
   * @param {number} latitude - Green latitude
   * @param {number} longitude - Green longitude
   * @param {number} elevation - Elevation in feet (optional)
   */
  setGreen(latitude, longitude, elevation = null) {
    this.green = { lat: latitude, lon: longitude, elevation };
  }

  /**
   * Set fairway center GPS coordinates
   * @param {number} latitude - Fairway latitude
   * @param {number} longitude - Fairway longitude
   */
  setFairwayCenter(latitude, longitude) {
    this.fairwayCenter = { lat: latitude, lon: longitude };
  }

  /**
   * Add a hazard with GPS coordinates
   * @param {string} type - Hazard type (water, bunker, trees, etc.)
   * @param {number} latitude - Hazard latitude
   * @param {number} longitude - Hazard longitude
   * @param {string} name - Hazard name (optional)
   */
  addHazard(type, latitude, longitude, name = '') {
    this.hazards.push({ type, lat: latitude, lon: longitude, name });
  }

  /**
   * Add a layup point with GPS coordinates
   * @param {number} distance - Distance from tee in yards
   * @param {number} latitude - Point latitude
   * @param {number} longitude - Point longitude
   */
  addLayupPoint(distance, latitude, longitude) {
    this.layupPoints.push({ distance, lat: latitude, lon: longitude });
  }

  /**
   * Check if hole has GPS coordinates
   * @returns {boolean} True if tee box and green coordinates are set
   */
  hasGPSCoordinates() {
    return this.teeBox !== null && this.green !== null;
  }

  /**
   * Get elevation change from tee to green
   * @returns {number|null} Elevation change in feet (positive = uphill)
   */
  getElevationChange() {
    if (!this.teeBox?.elevation || !this.green?.elevation) {
      return null;
    }
    return this.green.elevation - this.teeBox.elevation;
  }

  /**
   * Get hole data as JSON
   * @returns {Object} Hole data
   */
  toJSON() {
    return {
      number: this.number,
      par: this.par,
      handicap: this.handicap,
      yardage: this.yardage,
      rating: this.rating,
      slope: this.slope,
      gps: {
        teeBox: this.teeBox,
        green: this.green,
        fairwayCenter: this.fairwayCenter,
        hazards: this.hazards,
        layupPoints: this.layupPoints
      }
    };
  }
}

// Made with Bob
