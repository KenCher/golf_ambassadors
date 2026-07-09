/**
 * OpenStreetMap API Integration for Golf Course Discovery
 * Fetches golf courses dynamically based on GPS location
 */

class OpenStreetMapAPI {
    constructor() {
        this.overpassAPI = 'https://overpass-api.de/api/interpreter';
        this.nominatimAPI = 'https://nominatim.openstreetmap.org';
    }

    /**
     * Find golf courses near a location
     * @param {number} lat - Latitude
     * @param {number} lon - Longitude
     * @param {number} radiusKm - Search radius in kilometers (default 10km)
     * @returns {Promise<Array>} Array of golf courses
     */
    async findNearbyGolfCourses(lat, lon, radiusKm = 10) {
        try {
            // Overpass QL query to find golf courses
            const query = `
                [out:json][timeout:25];
                (
                    node["leisure"="golf_course"](around:${radiusKm * 1000},${lat},${lon});
                    way["leisure"="golf_course"](around:${radiusKm * 1000},${lat},${lon});
                    relation["leisure"="golf_course"](around:${radiusKm * 1000},${lat},${lon});
                );
                out center tags;
            `;

            const response = await fetch(this.overpassAPI, {
                method: 'POST',
                body: query,
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded'
                }
            });

            if (!response.ok) {
                throw new Error('Failed to fetch from OpenStreetMap');
            }

            const data = await response.json();
            return this.parseGolfCourses(data.elements, lat, lon);
        } catch (error) {
            console.error('Error fetching golf courses from OSM:', error);
            return [];
        }
    }

    /**
     * Parse OSM data into golf course objects
     */
    parseGolfCourses(elements, userLat, userLon) {
        const courses = [];

        elements.forEach(element => {
            const tags = element.tags || {};
            
            // Get course location
            let courseLat, courseLon;
            if (element.lat && element.lon) {
                courseLat = element.lat;
                courseLon = element.lon;
            } else if (element.center) {
                courseLat = element.center.lat;
                courseLon = element.center.lon;
            } else {
                return; // Skip if no coordinates
            }

            // Extract course information
            const course = {
                id: `osm-${element.id}`,
                name: tags.name || 'Unknown Golf Course',
                location: {
                    lat: courseLat,
                    lon: courseLon
                },
                city: tags['addr:city'] || this.extractCity(tags),
                state: tags['addr:state'] || '',
                holes: this.parseHoles(tags.holes) || 18,
                par: parseInt(tags.par) || 72,
                phone: tags.phone || tags['contact:phone'] || '',
                website: tags.website || tags['contact:website'] || '',
                operator: tags.operator || '',
                access: tags.access || 'public',
                source: 'OpenStreetMap',
                osmId: element.id,
                osmType: element.type
            };

            // Calculate distance
            course.distance = this.calculateDistance(
                userLat, userLon,
                courseLat, courseLon
            );

            courses.push(course);
        });

        // Sort by distance
        return courses.sort((a, b) => a.distance - b.distance);
    }

    /**
     * Get detailed information about a specific golf course
     */
    async getCourseDetails(osmId, osmType = 'way') {
        try {
            const query = `
                [out:json][timeout:25];
                ${osmType}(${osmId});
                out body;
                >;
                out skel qt;
            `;

            const response = await fetch(this.overpassAPI, {
                method: 'POST',
                body: query
            });

            const data = await response.json();
            return this.parseDetailedCourse(data.elements);
        } catch (error) {
            console.error('Error fetching course details:', error);
            return null;
        }
    }

    /**
     * Parse detailed course data including potential hole information
     */
    parseDetailedCourse(elements) {
        if (!elements || elements.length === 0) return null;

        const mainElement = elements[0];
        const tags = mainElement.tags || {};
        const nodes = elements.filter(e => e.type === 'node');

        // Try to extract hole information if available
        const holes = this.extractHoleData(tags, nodes);

        return {
            ...tags,
            holes: holes,
            nodeCount: nodes.length
        };
    }

    /**
     * Extract hole data from OSM tags if available
     */
    extractHoleData(tags, nodes) {
        const holes = [];
        
        // Check for hole-specific tags (rare in OSM)
        for (let i = 1; i <= 18; i++) {
            const holePar = tags[`hole:${i}:par`];
            const holeLength = tags[`hole:${i}:length`];
            
            if (holePar || holeLength) {
                holes.push({
                    number: i,
                    par: parseInt(holePar) || 4,
                    yardage: parseInt(holeLength) || 400,
                    strokeIndex: this.estimateStrokeIndex(i, parseInt(holePar) || 4)
                });
            }
        }

        return holes.length > 0 ? holes : null;
    }

    /**
     * Search for golf courses by name
     */
    async searchCourseByName(name, lat, lon, radiusKm = 50) {
        try {
            const query = `
                [out:json][timeout:25];
                (
                    node["leisure"="golf_course"]["name"~"${name}",i](around:${radiusKm * 1000},${lat},${lon});
                    way["leisure"="golf_course"]["name"~"${name}",i](around:${radiusKm * 1000},${lat},${lon});
                    relation["leisure"="golf_course"]["name"~"${name}",i](around:${radiusKm * 1000},${lat},${lon});
                );
                out center tags;
            `;

            const response = await fetch(this.overpassAPI, {
                method: 'POST',
                body: query
            });

            const data = await response.json();
            return this.parseGolfCourses(data.elements, lat, lon);
        } catch (error) {
            console.error('Error searching courses:', error);
            return [];
        }
    }

    /**
     * Helper: Calculate distance between two points (Haversine formula)
     */
    calculateDistance(lat1, lon1, lat2, lon2) {
        const R = 6371; // Earth's radius in km
        const dLat = this.toRad(lat2 - lat1);
        const dLon = this.toRad(lon2 - lon1);
        
        const a = Math.sin(dLat / 2) * Math.sin(dLat / 2) +
                  Math.cos(this.toRad(lat1)) * Math.cos(this.toRad(lat2)) *
                  Math.sin(dLon / 2) * Math.sin(dLon / 2);
        
        const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
        return R * c; // Distance in km
    }

    toRad(degrees) {
        return degrees * Math.PI / 180;
    }

    /**
     * Helper: Parse holes count
     */
    parseHoles(holesStr) {
        if (!holesStr) return null;
        const num = parseInt(holesStr);
        return isNaN(num) ? null : num;
    }

    /**
     * Helper: Extract city from tags
     */
    extractCity(tags) {
        return tags['addr:city'] || 
               tags.city || 
               tags['is_in:city'] || 
               '';
    }

    /**
     * Helper: Estimate stroke index based on hole number and par
     */
    estimateStrokeIndex(holeNumber, par) {
        // Standard stroke index pattern
        const pattern = {
            18: [7,1,15,5,11,17,3,13,9,8,2,16,6,12,18,4,14,10],
            9: [5,1,7,3,9,2,6,4,8]
        };
        
        return pattern[18][holeNumber - 1] || holeNumber;
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = OpenStreetMapAPI;
}

// Made with Bob
