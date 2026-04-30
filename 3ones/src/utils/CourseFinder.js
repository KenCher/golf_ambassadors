/**
 * Course Finder Utility
 * Finds nearby golf courses using GPS location
 */

export class CourseFinder {
  constructor() {
    // Sample course database - in production, this would come from an API
    this.courses = [
      {
        id: 'pebble-beach',
        name: 'Pebble Beach Golf Links',
        location: { lat: 36.5674, lon: -121.9500 },
        city: 'Pebble Beach',
        state: 'CA',
        holes: 18,
        par: 72,
        rating: 75.5,
        slope: 145
      },
      {
        id: 'augusta-national',
        name: 'Augusta National Golf Club',
        location: { lat: 33.5030, lon: -82.0200 },
        city: 'Augusta',
        state: 'GA',
        holes: 18,
        par: 72,
        rating: 76.2,
        slope: 148
      },
      {
        id: 'st-andrews',
        name: 'St Andrews Old Course',
        location: { lat: 56.3398, lon: -2.8050 },
        city: 'St Andrews',
        state: 'Scotland',
        holes: 18,
        par: 72,
        rating: 74.9,
        slope: 139
      },
      {
        id: 'pinehurst-no2',
        name: 'Pinehurst No. 2',
        location: { lat: 35.1895, lon: -79.4689 },
        city: 'Pinehurst',
        state: 'NC',
        holes: 18,
        par: 72,
        rating: 76.1,
        slope: 145
      },
      {
        id: 'torrey-pines',
        name: 'Torrey Pines Golf Course',
        location: { lat: 32.8989, lon: -117.2521 },
        city: 'La Jolla',
        state: 'CA',
        holes: 18,
        par: 72,
        rating: 75.4,
        slope: 144
      }
    ];
  }

  /**
   * Calculate distance between two GPS coordinates
   * @param {number} lat1 - Latitude 1
   * @param {number} lon1 - Longitude 1
   * @param {number} lat2 - Latitude 2
   * @param {number} lon2 - Longitude 2
   * @returns {number} Distance in miles
   */
  calculateDistance(lat1, lon1, lat2, lon2) {
    const R = 3959; // Earth's radius in miles
    const φ1 = lat1 * Math.PI / 180;
    const φ2 = lat2 * Math.PI / 180;
    const Δφ = (lat2 - lat1) * Math.PI / 180;
    const Δλ = (lon2 - lon1) * Math.PI / 180;

    const a = Math.sin(Δφ / 2) * Math.sin(Δφ / 2) +
              Math.cos(φ1) * Math.cos(φ2) *
              Math.sin(Δλ / 2) * Math.sin(Δλ / 2);
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));

    return R * c;
  }

  /**
   * Find courses near current location
   * @param {number} currentLat - Current latitude
   * @param {number} currentLon - Current longitude
   * @param {number} maxDistance - Maximum distance in miles (default: 50)
   * @returns {Array} Array of nearby courses with distances
   */
  findNearbyCourses(currentLat, currentLon, maxDistance = 50) {
    const nearbyCourses = this.courses.map(course => {
      const distance = this.calculateDistance(
        currentLat,
        currentLon,
        course.location.lat,
        course.location.lon
      );

      return {
        ...course,
        distance: distance,
        distanceText: distance < 1 
          ? `${(distance * 5280).toFixed(0)} ft`
          : `${distance.toFixed(1)} mi`
      };
    });

    // Filter by max distance and sort by distance
    return nearbyCourses
      .filter(course => course.distance <= maxDistance)
      .sort((a, b) => a.distance - b.distance);
  }

  /**
   * Find the closest course to current location
   * @param {number} currentLat - Current latitude
   * @param {number} currentLon - Current longitude
   * @returns {Object|null} Closest course or null if none found
   */
  findClosestCourse(currentLat, currentLon) {
    const nearbyCourses = this.findNearbyCourses(currentLat, currentLon);
    return nearbyCourses.length > 0 ? nearbyCourses[0] : null;
  }

  /**
   * Get course by ID
   * @param {string} courseId - Course ID
   * @returns {Object|null} Course object or null
   */
  getCourseById(courseId) {
    return this.courses.find(course => course.id === courseId) || null;
  }

  /**
   * Search courses by name
   * @param {string} query - Search query
   * @returns {Array} Matching courses
   */
  searchCourses(query) {
    const lowerQuery = query.toLowerCase();
    return this.courses.filter(course => 
      course.name.toLowerCase().includes(lowerQuery) ||
      course.city.toLowerCase().includes(lowerQuery) ||
      course.state.toLowerCase().includes(lowerQuery)
    );
  }

  /**
   * Add a custom course to the database
   * @param {Object} course - Course object
   */
  addCourse(course) {
    if (!course.id || !course.name || !course.location) {
      throw new Error('Course must have id, name, and location');
    }
    this.courses.push(course);
  }

  /**
   * Get all courses
   * @returns {Array} All courses
   */
  getAllCourses() {
    return [...this.courses];
  }

  /**
   * Check if user is on a course (within 1 mile)
   * @param {number} currentLat - Current latitude
   * @param {number} currentLon - Current longitude
   * @returns {Object|null} Course if on one, null otherwise
   */
  isOnCourse(currentLat, currentLon) {
    const closest = this.findClosestCourse(currentLat, currentLon);
    return (closest && closest.distance < 1) ? closest : null;
  }

  /**
   * Get course recommendations based on location
   * @param {number} currentLat - Current latitude
   * @param {number} currentLon - Current longitude
   * @param {number} limit - Maximum number of recommendations
   * @returns {Array} Recommended courses
   */
  getRecommendations(currentLat, currentLon, limit = 5) {
    return this.findNearbyCourses(currentLat, currentLon, 100)
      .slice(0, limit);
  }

  /**
   * Format course information for display
   * @param {Object} course - Course object
   * @returns {string} Formatted course info
   */
  formatCourseInfo(course) {
    return `${course.name}\n${course.city}, ${course.state}\n${course.holes} holes • Par ${course.par}\nRating: ${course.rating} • Slope: ${course.slope}`;
  }
}

// Made with Bob