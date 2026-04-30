/**
 * GPS Visualization Component
 * Renders GPS data, course maps, and player positions
 */

export class GPSVisualization {
  /**
   * Create a simple ASCII map of the hole
   * @param {Object} hole - Hole object with GPS data
   * @param {Object} playerPosition - Current player position {lat, lon}
   * @returns {string} ASCII representation of the hole
   */
  static renderHoleMap(hole, playerPosition = null) {
    const width = 40;
    const height = 20;
    const map = Array(height).fill(null).map(() => Array(width).fill(' '));

    // Calculate bounds
    const points = [hole.teeBox, hole.green];
    if (hole.fairwayCenter) points.push(hole.fairwayCenter);
    if (playerPosition) points.push(playerPosition);
    hole.hazards.forEach(h => points.push(h));

    const lats = points.map(p => p.lat);
    const lons = points.map(p => p.lon);
    const minLat = Math.min(...lats);
    const maxLat = Math.max(...lats);
    const minLon = Math.min(...lons);
    const maxLon = Math.max(...lons);

    // Helper to convert GPS to map coordinates
    const toMapCoords = (lat, lon) => {
      const x = Math.floor(((lon - minLon) / (maxLon - minLon)) * (width - 1));
      const y = Math.floor(((maxLat - lat) / (maxLat - minLat)) * (height - 1));
      return { x: Math.max(0, Math.min(width - 1, x)), y: Math.max(0, Math.min(height - 1, y)) };
    };

    // Draw fairway (rough approximation)
    if (hole.fairwayCenter) {
      const tee = toMapCoords(hole.teeBox.lat, hole.teeBox.lon);
      const fairway = toMapCoords(hole.fairwayCenter.lat, hole.fairwayCenter.lon);
      const green = toMapCoords(hole.green.lat, hole.green.lon);
      
      // Simple line drawing
      this.drawLine(map, tee.x, tee.y, fairway.x, fairway.y, '·');
      this.drawLine(map, fairway.x, fairway.y, green.x, green.y, '·');
    }

    // Draw hazards
    hole.hazards.forEach(hazard => {
      const pos = toMapCoords(hazard.lat, hazard.lon);
      const symbol = hazard.type === 'water' ? '≈' : hazard.type === 'bunker' ? '○' : '▲';
      map[pos.y][pos.x] = symbol;
    });

    // Draw tee box
    const teePos = toMapCoords(hole.teeBox.lat, hole.teeBox.lon);
    map[teePos.y][teePos.x] = 'T';

    // Draw green
    const greenPos = toMapCoords(hole.green.lat, hole.green.lon);
    map[greenPos.y][greenPos.x] = 'G';

    // Draw player position
    if (playerPosition) {
      const playerPos = toMapCoords(playerPosition.lat, playerPosition.lon);
      map[playerPos.y][playerPos.x] = '●';
    }

    // Convert to string
    let output = '┌' + '─'.repeat(width) + '┐\n';
    map.forEach(row => {
      output += '│' + row.join('') + '│\n';
    });
    output += '└' + '─'.repeat(width) + '┘\n';
    output += '\nLegend: T=Tee, G=Green, ●=You, ≈=Water, ○=Bunker, ▲=Trees, ·=Fairway\n';

    return output;
  }

  /**
   * Draw a line between two points on the map
   * @param {Array} map - 2D array representing the map
   * @param {number} x1 - Start x
   * @param {number} y1 - Start y
   * @param {number} x2 - End x
   * @param {number} y2 - End y
   * @param {string} char - Character to draw
   */
  static drawLine(map, x1, y1, x2, y2, char) {
    const dx = Math.abs(x2 - x1);
    const dy = Math.abs(y2 - y1);
    const sx = x1 < x2 ? 1 : -1;
    const sy = y1 < y2 ? 1 : -1;
    let err = dx - dy;

    while (true) {
      if (x1 >= 0 && x1 < map[0].length && y1 >= 0 && y1 < map.length) {
        if (map[y1][x1] === ' ') {
          map[y1][x1] = char;
        }
      }

      if (x1 === x2 && y1 === y2) break;
      const e2 = 2 * err;
      if (e2 > -dy) {
        err -= dy;
        x1 += sx;
      }
      if (e2 < dx) {
        err += dx;
        y1 += sy;
      }
    }
  }

  /**
   * Generate SVG map of the hole
   * @param {Object} hole - Hole object with GPS data
   * @param {Object} playerPosition - Current player position
   * @param {number} width - SVG width
   * @param {number} height - SVG height
   * @returns {string} SVG markup
   */
  static renderSVGMap(hole, playerPosition = null, width = 600, height = 400) {
    // Calculate bounds with padding
    const points = [hole.teeBox, hole.green];
    if (hole.fairwayCenter) points.push(hole.fairwayCenter);
    if (playerPosition) points.push(playerPosition);
    hole.hazards.forEach(h => points.push(h));

    const lats = points.map(p => p.lat);
    const lons = points.map(p => p.lon);
    const minLat = Math.min(...lats);
    const maxLat = Math.max(...lats);
    const minLon = Math.min(...lons);
    const maxLon = Math.max(...lons);

    const padding = 40;
    const mapWidth = width - 2 * padding;
    const mapHeight = height - 2 * padding;

    // Helper to convert GPS to SVG coordinates
    const toSVGCoords = (lat, lon) => {
      const x = padding + ((lon - minLon) / (maxLon - minLon)) * mapWidth;
      const y = padding + ((maxLat - lat) / (maxLat - minLat)) * mapHeight;
      return { x, y };
    };

    let svg = `<svg width="${width}" height="${height}" xmlns="http://www.w3.org/2000/svg">`;
    svg += '<defs>';
    svg += '<linearGradient id="fairwayGradient" x1="0%" y1="0%" x2="0%" y2="100%">';
    svg += '<stop offset="0%" style="stop-color:#4ade80;stop-opacity:0.3" />';
    svg += '<stop offset="100%" style="stop-color:#22c55e;stop-opacity:0.3" />';
    svg += '</linearGradient>';
    svg += '</defs>';

    // Background
    svg += `<rect width="${width}" height="${height}" fill="#f0f9ff"/>`;

    // Draw fairway path
    if (hole.fairwayCenter) {
      const tee = toSVGCoords(hole.teeBox.lat, hole.teeBox.lon);
      const fairway = toSVGCoords(hole.fairwayCenter.lat, hole.fairwayCenter.lon);
      const green = toSVGCoords(hole.green.lat, hole.green.lon);
      
      svg += `<path d="M ${tee.x},${tee.y} Q ${fairway.x},${fairway.y} ${green.x},${green.y}" `;
      svg += 'stroke="#22c55e" stroke-width="30" fill="none" opacity="0.3"/>';
    }

    // Draw hazards
    hole.hazards.forEach(hazard => {
      const pos = toSVGCoords(hazard.lat, hazard.lon);
      if (hazard.type === 'water') {
        svg += `<circle cx="${pos.x}" cy="${pos.y}" r="15" fill="#3b82f6" opacity="0.6"/>`;
        svg += `<text x="${pos.x}" y="${pos.y + 5}" text-anchor="middle" fill="white" font-size="12">≈</text>`;
      } else if (hazard.type === 'bunker') {
        svg += `<circle cx="${pos.x}" cy="${pos.y}" r="12" fill="#fbbf24" opacity="0.7"/>`;
      } else {
        svg += `<circle cx="${pos.x}" cy="${pos.y}" r="10" fill="#16a34a" opacity="0.5"/>`;
      }
    });

    // Draw tee box
    const teePos = toSVGCoords(hole.teeBox.lat, hole.teeBox.lon);
    svg += `<rect x="${teePos.x - 15}" y="${teePos.y - 15}" width="30" height="30" fill="#dc2626" rx="5"/>`;
    svg += `<text x="${teePos.x}" y="${teePos.y + 5}" text-anchor="middle" fill="white" font-weight="bold" font-size="16">T</text>`;

    // Draw green
    const greenPos = toSVGCoords(hole.green.lat, hole.green.lon);
    svg += `<circle cx="${greenPos.x}" cy="${greenPos.y}" r="25" fill="#22c55e" opacity="0.7"/>`;
    svg += `<circle cx="${greenPos.x}" cy="${greenPos.y}" r="20" fill="#16a34a" opacity="0.5"/>`;
    svg += `<text x="${greenPos.x}" y="${greenPos.y + 5}" text-anchor="middle" fill="white" font-weight="bold" font-size="16">G</text>`;

    // Draw player position
    if (playerPosition) {
      const playerPos = toSVGCoords(playerPosition.lat, playerPosition.lon);
      svg += `<circle cx="${playerPos.x}" cy="${playerPos.y}" r="8" fill="#6366f1"/>`;
      svg += `<circle cx="${playerPos.x}" cy="${playerPos.y}" r="12" fill="none" stroke="#6366f1" stroke-width="2"/>`;
      
      // Draw line to green
      svg += `<line x1="${playerPos.x}" y1="${playerPos.y}" x2="${greenPos.x}" y2="${greenPos.y}" `;
      svg += 'stroke="#6366f1" stroke-width="2" stroke-dasharray="5,5" opacity="0.5"/>';
    }

    // Add hole info
    svg += `<text x="10" y="25" font-size="18" font-weight="bold" fill="#1e3a8a">Hole ${hole.number}</text>`;
    svg += `<text x="10" y="45" font-size="14" fill="#475569">Par ${hole.par} • ${hole.yardage} yards</text>`;

    svg += '</svg>';
    return svg;
  }

  /**
   * Generate HTML for GPS dashboard
   * @param {Object} data - GPS data including position, hole info, distances
   * @returns {string} HTML markup
   */
  static renderGPSDashboard(data) {
    const { hole, playerPosition, distanceToGreen, distanceToFairway, bearing, accuracy } = data;

    let html = '<div class="gps-dashboard" style="font-family: sans-serif; padding: 20px; background: #f8fafc; border-radius: 10px;">';
    
    // Distance card
    html += '<div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; border-radius: 15px; text-align: center; margin-bottom: 20px;">';
    html += '<div style="font-size: 14px; opacity: 0.9; margin-bottom: 10px;">DISTANCE TO GREEN</div>';
    html += `<div style="font-size: 48px; font-weight: bold;">${distanceToGreen}</div>`;
    html += '<div style="font-size: 18px; opacity: 0.8;">yards</div>';
    html += `<div style="margin-top: 15px; font-size: 16px;">Direction: ${this.getCompassDirection(bearing)} (${bearing}°)</div>`;
    html += '</div>';

    // Info grid
    html += '<div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 15px; margin-bottom: 20px;">';
    
    html += '<div style="background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">';
    html += '<div style="font-size: 12px; color: #64748b; margin-bottom: 5px;">TO FAIRWAY</div>';
    html += `<div style="font-size: 24px; font-weight: bold; color: #1e293b;">${distanceToFairway} yd</div>`;
    html += '</div>';

    html += '<div style="background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">';
    html += '<div style="font-size: 12px; color: #64748b; margin-bottom: 5px;">GPS ACCURACY</div>';
    html += `<div style="font-size: 24px; font-weight: bold; color: #1e293b;">${accuracy} m</div>`;
    html += '</div>';

    html += '</div>';

    // Hole info
    html += '<div style="background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); margin-bottom: 20px;">';
    html += `<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;">`;
    html += `<div style="font-size: 24px; font-weight: bold; color: #1e293b;">Hole ${hole.number}</div>`;
    html += `<div style="background: #e0e7ff; color: #4338ca; padding: 8px 16px; border-radius: 20px; font-weight: 600;">Par ${hole.par}</div>`;
    html += '</div>';
    html += `<div style="color: #64748b;">Yardage: ${hole.yardage} • Handicap: ${hole.handicap}</div>`;
    html += '</div>';

    html += '</div>';
    return html;
  }

  /**
   * Get compass direction from bearing
   * @param {number} bearing - Bearing in degrees
   * @returns {string} Compass direction
   */
  static getCompassDirection(bearing) {
    const directions = ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW'];
    const index = Math.round(bearing / 45) % 8;
    return directions[index];
  }

  /**
   * Generate shot history visualization
   * @param {Array} shots - Array of shot objects with GPS data
   * @returns {string} HTML markup
   */
  static renderShotHistory(shots) {
    if (!shots || shots.length === 0) {
      return '<div style="padding: 20px; text-align: center; color: #64748b;">No shots recorded yet</div>';
    }

    let html = '<div class="shot-history" style="padding: 20px;">';
    html += '<h3 style="margin-bottom: 15px; color: #1e293b;">Shot History</h3>';

    shots.forEach((shot, index) => {
      html += '<div style="background: white; padding: 15px; border-radius: 10px; margin-bottom: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">';
      html += '<div style="display: flex; justify-content: space-between; align-items: center;">';
      html += `<div style="font-weight: bold; color: #1e293b;">Shot ${index + 1}</div>`;
      if (shot.distance) {
        html += `<div style="color: #6366f1; font-weight: 600;">${shot.distance} yards</div>`;
      }
      html += '</div>';
      html += `<div style="font-size: 12px; color: #64748b; margin-top: 5px;">${new Date(shot.timestamp).toLocaleTimeString()}</div>`;
      html += '</div>';
    });

    html += '</div>';
    return html;
  }

  /**
   * Generate heatmap data for player positions
   * @param {Array} positions - Array of position objects {lat, lon, timestamp}
   * @returns {Object} Heatmap data
   */
  static generateHeatmapData(positions) {
    if (!positions || positions.length === 0) {
      return { points: [], bounds: null };
    }

    const lats = positions.map(p => p.lat);
    const lons = positions.map(p => p.lon);

    return {
      points: positions.map(p => ({
        lat: p.lat,
        lon: p.lon,
        weight: 1
      })),
      bounds: {
        minLat: Math.min(...lats),
        maxLat: Math.max(...lats),
        minLon: Math.min(...lons),
        maxLon: Math.max(...lons)
      }
    };
  }

  /**
   * Format GPS coordinates for display
   * @param {number} lat - Latitude
   * @param {number} lon - Longitude
   * @param {number} precision - Decimal places
   * @returns {string} Formatted coordinates
   */
  static formatCoordinates(lat, lon, precision = 6) {
    const latDir = lat >= 0 ? 'N' : 'S';
    const lonDir = lon >= 0 ? 'E' : 'W';
    return `${Math.abs(lat).toFixed(precision)}°${latDir}, ${Math.abs(lon).toFixed(precision)}°${lonDir}`;
  }

  /**
   * Generate compass rose SVG
   * @param {number} bearing - Current bearing
   * @param {number} size - Size of compass
   * @returns {string} SVG markup
   */
  static renderCompassRose(bearing, size = 100) {
    const center = size / 2;
    const radius = size / 2 - 10;

    let svg = `<svg width="${size}" height="${size}" xmlns="http://www.w3.org/2000/svg">`;
    
    // Background circle
    svg += `<circle cx="${center}" cy="${center}" r="${radius}" fill="#1e293b" opacity="0.1"/>`;
    
    // Cardinal directions
    const directions = ['N', 'E', 'S', 'W'];
    directions.forEach((dir, i) => {
      const angle = i * 90;
      const rad = (angle - 90) * Math.PI / 180;
      const x = center + Math.cos(rad) * (radius - 15);
      const y = center + Math.sin(rad) * (radius - 15);
      svg += `<text x="${x}" y="${y + 5}" text-anchor="middle" font-size="14" font-weight="bold" fill="#1e293b">${dir}</text>`;
    });

    // Bearing arrow
    const arrowRad = (bearing - 90) * Math.PI / 180;
    const arrowX = center + Math.cos(arrowRad) * (radius - 5);
    const arrowY = center + Math.sin(arrowRad) * (radius - 5);
    
    svg += `<line x1="${center}" y1="${center}" x2="${arrowX}" y2="${arrowY}" stroke="#6366f1" stroke-width="3"/>`;
    svg += `<circle cx="${arrowX}" cy="${arrowY}" r="5" fill="#6366f1"/>`;
    svg += `<circle cx="${center}" cy="${center}" r="5" fill="#1e293b"/>`;

    svg += '</svg>';
    return svg;
  }
}

// Made with Bob