/**
 * Distance Calculator Utility
 * Advanced distance calculations for golf GPS features
 */

export class DistanceCalculator {
  /**
   * Calculate distance between two GPS coordinates using Haversine formula
   * @param {number} lat1 - Latitude of point 1
   * @param {number} lon1 - Longitude of point 1
   * @param {number} lat2 - Latitude of point 2
   * @param {number} lon2 - Longitude of point 2
   * @param {string} unit - Unit of measurement ('yards', 'meters', 'feet', 'miles')
   * @returns {number} Distance in specified unit
   */
  static calculateDistance(lat1, lon1, lat2, lon2, unit = 'yards') {
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

    // Convert to requested unit
    switch (unit.toLowerCase()) {
      case 'yards':
        return Math.round(distanceMeters * 1.09361);
      case 'feet':
        return Math.round(distanceMeters * 3.28084);
      case 'miles':
        return (distanceMeters * 0.000621371).toFixed(2);
      case 'meters':
      default:
        return Math.round(distanceMeters);
    }
  }

  /**
   * Calculate adjusted distance accounting for elevation change
   * @param {number} horizontalDistance - Horizontal distance in yards
   * @param {number} elevationChange - Elevation change in feet (positive = uphill)
   * @returns {number} Adjusted distance in yards
   */
  static calculateAdjustedDistance(horizontalDistance, elevationChange) {
    // Convert elevation to yards
    const elevationYards = elevationChange / 3;
    
    // Use Pythagorean theorem for actual distance
    const actualDistance = Math.sqrt(
      Math.pow(horizontalDistance, 2) + Math.pow(elevationYards, 2)
    );

    // Apply playing distance adjustment (uphill plays longer, downhill shorter)
    // Rule of thumb: 1 yard per foot of elevation change
    const playingDistance = horizontalDistance + elevationChange;

    return {
      actual: Math.round(actualDistance),
      playing: Math.round(playingDistance),
      horizontal: horizontalDistance,
      elevation: elevationChange
    };
  }

  /**
   * Calculate bearing (direction) between two points
   * @param {number} lat1 - Starting latitude
   * @param {number} lon1 - Starting longitude
   * @param {number} lat2 - Target latitude
   * @param {number} lon2 - Target longitude
   * @returns {number} Bearing in degrees (0-360)
   */
  static calculateBearing(lat1, lon1, lat2, lon2) {
    const φ1 = lat1 * Math.PI / 180;
    const φ2 = lat2 * Math.PI / 180;
    const Δλ = (lon2 - lon1) * Math.PI / 180;

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
   * @param {boolean} detailed - Return 16-point compass if true, 8-point if false
   * @returns {string} Compass direction
   */
  static getCompassDirection(bearing, detailed = false) {
    if (detailed) {
      const directions = [
        'N', 'NNE', 'NE', 'ENE', 'E', 'ESE', 'SE', 'SSE',
        'S', 'SSW', 'SW', 'WSW', 'W', 'WNW', 'NW', 'NNW'
      ];
      const index = Math.round(bearing / 22.5) % 16;
      return directions[index];
    } else {
      const directions = ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW'];
      const index = Math.round(bearing / 45) % 8;
      return directions[index];
    }
  }

  /**
   * Calculate distance to layup point
   * @param {number} currentLat - Current latitude
   * @param {number} currentLon - Current longitude
   * @param {number} targetLat - Target latitude
   * @param {number} targetLon - Target longitude
   * @param {number} layupDistance - Desired layup distance in yards
   * @returns {Object} Layup point coordinates and distance
   */
  static calculateLayupPoint(currentLat, currentLon, targetLat, targetLon, layupDistance) {
    const totalDistance = this.calculateDistance(currentLat, currentLon, targetLat, targetLon);
    const bearing = this.calculateBearing(currentLat, currentLon, targetLat, targetLon);
    
    // Calculate layup point coordinates
    const distanceToLayup = totalDistance - layupDistance;
    const layupPoint = this.calculateDestinationPoint(
      currentLat, currentLon, bearing, distanceToLayup
    );

    return {
      lat: layupPoint.lat,
      lon: layupPoint.lon,
      distanceFromCurrent: Math.round(distanceToLayup),
      distanceToTarget: layupDistance,
      bearing: bearing
    };
  }

  /**
   * Calculate destination point given distance and bearing
   * @param {number} lat - Starting latitude
   * @param {number} lon - Starting longitude
   * @param {number} bearing - Bearing in degrees
   * @param {number} distance - Distance in yards
   * @returns {Object} Destination coordinates {lat, lon}
   */
  static calculateDestinationPoint(lat, lon, bearing, distance) {
    const R = 6371000; // Earth's radius in meters
    const distanceMeters = distance / 1.09361; // Convert yards to meters
    const δ = distanceMeters / R;
    const θ = bearing * Math.PI / 180;
    const φ1 = lat * Math.PI / 180;
    const λ1 = lon * Math.PI / 180;

    const φ2 = Math.asin(
      Math.sin(φ1) * Math.cos(δ) +
      Math.cos(φ1) * Math.sin(δ) * Math.cos(θ)
    );

    const λ2 = λ1 + Math.atan2(
      Math.sin(θ) * Math.sin(δ) * Math.cos(φ1),
      Math.cos(δ) - Math.sin(φ1) * Math.sin(φ2)
    );

    return {
      lat: φ2 * 180 / Math.PI,
      lon: λ2 * 180 / Math.PI
    };
  }

  /**
   * Calculate club selection based on distance and conditions
   * @param {number} distance - Distance to target in yards
   * @param {number} elevationChange - Elevation change in feet
   * @param {number} windSpeed - Wind speed in mph (optional)
   * @param {number} windDirection - Wind direction in degrees (optional)
   * @param {number} targetBearing - Bearing to target in degrees (optional)
   * @returns {Object} Club recommendation and adjusted distance
   */
  static calculateClubSelection(distance, elevationChange, windSpeed = 0, windDirection = 0, targetBearing = 0) {
    // Calculate adjusted distance for elevation
    const elevationAdjustment = elevationChange; // 1 yard per foot
    let adjustedDistance = distance + elevationAdjustment;

    // Calculate wind effect if provided
    if (windSpeed > 0) {
      const windEffect = this.calculateWindEffect(windSpeed, windDirection, targetBearing);
      adjustedDistance += windEffect;
    }

    // Standard club distances (can be customized per player)
    const clubs = [
      { name: 'Driver', distance: 250 },
      { name: '3-Wood', distance: 230 },
      { name: '5-Wood', distance: 210 },
      { name: '3-Hybrid', distance: 195 },
      { name: '4-Iron', distance: 185 },
      { name: '5-Iron', distance: 175 },
      { name: '6-Iron', distance: 165 },
      { name: '7-Iron', distance: 155 },
      { name: '8-Iron', distance: 145 },
      { name: '9-Iron', distance: 135 },
      { name: 'PW', distance: 120 },
      { name: 'GW', distance: 105 },
      { name: 'SW', distance: 90 },
      { name: 'LW', distance: 75 }
    ];

    // Find closest club
    let recommendedClub = clubs[clubs.length - 1];
    let minDiff = Math.abs(adjustedDistance - recommendedClub.distance);

    for (const club of clubs) {
      const diff = Math.abs(adjustedDistance - club.distance);
      if (diff < minDiff) {
        minDiff = diff;
        recommendedClub = club;
      }
    }

    return {
      club: recommendedClub.name,
      adjustedDistance: Math.round(adjustedDistance),
      actualDistance: distance,
      elevationAdjustment: Math.round(elevationAdjustment),
      windAdjustment: windSpeed > 0 ? Math.round(adjustedDistance - distance - elevationAdjustment) : 0
    };
  }

  /**
   * Calculate wind effect on shot distance
   * @param {number} windSpeed - Wind speed in mph
   * @param {number} windDirection - Wind direction in degrees
   * @param {number} shotDirection - Shot direction in degrees
   * @returns {number} Distance adjustment in yards
   */
  static calculateWindEffect(windSpeed, windDirection, shotDirection) {
    // Calculate relative wind angle
    const relativeAngle = Math.abs(windDirection - shotDirection);
    const angleRadians = relativeAngle * Math.PI / 180;

    // Headwind/tailwind component
    const headTailComponent = Math.cos(angleRadians);
    
    // Crosswind component (less effect on distance)
    const crossComponent = Math.sin(angleRadians);

    // Wind effect: roughly 1 yard per mph for headwind/tailwind
    // Crosswind has minimal distance effect
    const distanceEffect = windSpeed * headTailComponent * 0.8;

    return Math.round(distanceEffect);
  }

  /**
   * Calculate total distance for a path (multiple waypoints)
   * @param {Array} waypoints - Array of {lat, lon} objects
   * @returns {number} Total distance in yards
   */
  static calculatePathDistance(waypoints) {
    if (waypoints.length < 2) return 0;

    let totalDistance = 0;
    for (let i = 1; i < waypoints.length; i++) {
      totalDistance += this.calculateDistance(
        waypoints[i - 1].lat,
        waypoints[i - 1].lon,
        waypoints[i].lat,
        waypoints[i].lon
      );
    }

    return Math.round(totalDistance);
  }

  /**
   * Calculate area of a polygon (e.g., green, hazard)
   * @param {Array} points - Array of {lat, lon} objects forming polygon
   * @returns {number} Area in square yards
   */
  static calculateArea(points) {
    if (points.length < 3) return 0;

    // Use spherical excess formula for accuracy
    let area = 0;
    const R = 6371000; // Earth's radius in meters

    for (let i = 0; i < points.length; i++) {
      const p1 = points[i];
      const p2 = points[(i + 1) % points.length];
      
      const φ1 = p1.lat * Math.PI / 180;
      const φ2 = p2.lat * Math.PI / 180;
      const Δλ = (p2.lon - p1.lon) * Math.PI / 180;

      area += Δλ * (2 + Math.sin(φ1) + Math.sin(φ2));
    }

    area = Math.abs(area * R * R / 2);
    
    // Convert to square yards
    return Math.round(area * 1.19599);
  }

  /**
   * Check if point is within radius of target
   * @param {number} lat - Point latitude
   * @param {number} lon - Point longitude
   * @param {number} targetLat - Target latitude
   * @param {number} targetLon - Target longitude
   * @param {number} radius - Radius in yards
   * @returns {boolean} True if within radius
   */
  static isWithinRadius(lat, lon, targetLat, targetLon, radius) {
    const distance = this.calculateDistance(lat, lon, targetLat, targetLon);
    return distance <= radius;
  }

  /**
   * Format distance for display
   * @param {number} distance - Distance in yards
   * @param {boolean} includeUnit - Include unit in output
   * @returns {string} Formatted distance
   */
  static formatDistance(distance, includeUnit = true) {
    if (distance < 1000) {
      return includeUnit ? `${distance} yd` : distance.toString();
    } else {
      const miles = (distance / 1760).toFixed(1);
      return includeUnit ? `${miles} mi` : miles;
    }
  }
}

// Made with Bob