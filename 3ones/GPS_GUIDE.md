# Golf4us GPS Guide

Complete guide to using GPS features in the Golf4us tournament management app.

## Table of Contents

1. [Overview](#overview)
2. [Getting Started](#getting-started)
3. [Mobile GPS Interface](#mobile-gps-interface)
4. [GPS API Reference](#gps-api-reference)
5. [Course Setup](#course-setup)
6. [Distance Calculations](#distance-calculations)
7. [Best Practices](#best-practices)
8. [Troubleshooting](#troubleshooting)

## Overview

Golf4us now includes comprehensive GPS functionality for on-course navigation and distance measurement. Features include:

- **Real-time GPS tracking** with high accuracy
- **Distance calculations** to greens, hazards, and layup points
- **Elevation adjustments** for accurate club selection
- **Shot tracking** with automatic distance measurement
- **Course mapping** with visual representations
- **Mobile-optimized interface** for smartphone use

## Getting Started

### Requirements

- Modern web browser with Geolocation API support
- HTTPS connection (required for GPS access)
- Location services enabled on device
- GPS-enabled device (smartphone, tablet, or GPS-enabled laptop)

### Quick Start

1. **Open the mobile GPS interface:**
   ```
   https://your-domain.com/gps-mobile.html
   ```

2. **Grant location permissions** when prompted

3. **Wait for GPS lock** (usually 5-30 seconds)

4. **Start playing!** Distance to green updates automatically

## Mobile GPS Interface

### Features

#### Distance Display
- Large, easy-to-read distance to green
- Real-time updates as you move
- Compass bearing and direction indicator
- GPS accuracy indicator

#### Hole Information
- Current hole number and par
- Total yardage
- Handicap rating
- Elevation change (if available)

#### Shot Tracking
- Mark shot locations with one tap
- Automatic distance calculation between shots
- Shot history for current hole
- Total distance walked

#### Additional Info
- Distance to fairway center
- Nearby hazards with distances
- Layup point suggestions
- GPS accuracy status

### Using the Mobile Interface

1. **Enable GPS:**
   - Tap "Allow" when prompted for location access
   - Wait for GPS to acquire signal (green indicator)

2. **View Distance:**
   - Distance to green shown in large numbers
   - Arrow points toward green
   - Compass direction displayed (N, NE, E, etc.)

3. **Mark Shots:**
   - Tap "Mark Shot" button after each shot
   - Distance from previous shot calculated automatically
   - View shot history in the tracker section

4. **Navigate Holes:**
   - Tap "Next Hole" to advance
   - Hole information updates automatically
   - Shot history resets for new hole

## GPS API Reference

### GPSTracker Class

```javascript
import { GPSTracker } from './src/utils/GPSTracker.js';

const tracker = new GPSTracker();
```

#### Methods

**getCurrentPosition()**
```javascript
const position = await tracker.getCurrentPosition();
// Returns: { latitude, longitude, altitude, accuracy, timestamp }
```

**startTracking(callback)**
```javascript
tracker.startTracking((position) => {
  console.log('New position:', position);
});
```

**stopTracking()**
```javascript
tracker.stopTracking();
```

**getDistanceToTarget(targetLat, targetLon)**
```javascript
const distance = tracker.getDistanceToTarget(36.5680, -121.9505);
// Returns: distance in yards
```

**getBearingToTarget(targetLat, targetLon)**
```javascript
const bearing = tracker.getBearingToTarget(36.5680, -121.9505);
// Returns: bearing in degrees (0-360)
```

**calculateShotDistance()**
```javascript
const shotDistance = tracker.calculateShotDistance();
// Returns: distance of last shot in yards
```

### DistanceCalculator Class

```javascript
import { DistanceCalculator } from './src/utils/DistanceCalculator.js';
```

#### Methods

**calculateDistance(lat1, lon1, lat2, lon2, unit)**
```javascript
const distance = DistanceCalculator.calculateDistance(
  36.5674, -121.9500,  // Point 1
  36.5680, -121.9505,  // Point 2
  'yards'              // Unit: 'yards', 'meters', 'feet', 'miles'
);
```

**calculateAdjustedDistance(horizontalDistance, elevationChange)**
```javascript
const adjusted = DistanceCalculator.calculateAdjustedDistance(
  150,  // horizontal distance in yards
  15    // elevation change in feet (+ = uphill, - = downhill)
);
// Returns: { actual, playing, horizontal, elevation }
```

**calculateClubSelection(distance, elevation, windSpeed, windDir, targetBearing)**
```javascript
const recommendation = DistanceCalculator.calculateClubSelection(
  165,  // distance in yards
  10,   // elevation change in feet
  15,   // wind speed in mph (optional)
  90,   // wind direction in degrees (optional)
  45    // target bearing in degrees (optional)
);
// Returns: { club, adjustedDistance, actualDistance, elevationAdjustment, windAdjustment }
```

**calculateLayupPoint(currentLat, currentLon, targetLat, targetLon, layupDistance)**
```javascript
const layup = DistanceCalculator.calculateLayupPoint(
  36.5674, -121.9500,  // Current position
  36.5680, -121.9505,  // Target (green)
  100                   // Desired layup distance from target
);
// Returns: { lat, lon, distanceFromCurrent, distanceToTarget, bearing }
```

### GPSCourseMapper Class

```javascript
import { GPSCourseMapper } from './src/utils/GPSTracker.js';

const mapper = new GPSCourseMapper(course);
```

#### Methods

**setHoleLocation(holeNumber, teeBox, green, hazards)**
```javascript
mapper.setHoleLocation(
  1,                                    // Hole number
  { lat: 36.5674, lon: -121.9500 },   // Tee box
  { lat: 36.5680, lon: -121.9505 },   // Green
  [                                     // Hazards (optional)
    { type: 'water', lat: 36.5676, lon: -121.9503, name: 'Creek' },
    { type: 'bunker', lat: 36.5679, lon: -121.9504, name: 'Bunker' }
  ]
);
```

**getDistanceToGreen(holeNumber, currentLat, currentLon)**
```javascript
const distance = mapper.getDistanceToGreen(1, 36.5675, -121.9501);
// Returns: distance in yards
```

**getNearestHazard(holeNumber, currentLat, currentLon)**
```javascript
const hazard = mapper.getNearestHazard(1, 36.5675, -121.9501);
// Returns: { type, lat, lon, name, distance }
```

## Course Setup

### Adding GPS Data to Holes

```javascript
import { Course, Hole } from './src/models/Course.js';

// Create course
const course = new Course('Pebble Beach Golf Links');
course.setCourseLocation(36.5674, -121.9500);

// Create hole
const hole = new Hole(1, 4, 11, 380);

// Add GPS coordinates
hole.setTeeBox(36.5674, -121.9500, 50);      // lat, lon, elevation (ft)
hole.setGreen(36.5680, -121.9505, 65);       // lat, lon, elevation (ft)
hole.setFairwayCenter(36.5677, -121.9502);   // lat, lon

// Add hazards
hole.addHazard('water', 36.5676, -121.9503, 'Creek');
hole.addHazard('bunker', 36.5679, -121.9504, 'Greenside Bunker');
hole.addHazard('trees', 36.5675, -121.9501, 'Left Trees');

// Add layup points
hole.addLayupPoint(100, 36.5678, -121.9503);  // 100 yards from green

course.addHole(hole);
```

### Collecting GPS Coordinates

**Method 1: On-Course Collection**
1. Walk the course with GPS-enabled device
2. Mark tee boxes, greens, and hazards
3. Record coordinates using the mobile interface
4. Export data for course setup

**Method 2: Satellite Imagery**
1. Use Google Maps or similar service
2. Right-click on locations to get coordinates
3. Note: May be less accurate than on-course collection

**Method 3: Course Management Software**
1. Many courses have GPS data available
2. Request data from course management
3. Import into Golf4us format

## Distance Calculations

### Basic Distance

```javascript
const distance = DistanceCalculator.calculateDistance(
  currentLat, currentLon,
  targetLat, targetLon,
  'yards'
);
```

### Elevation-Adjusted Distance

```javascript
// Uphill shot: add distance
const uphill = DistanceCalculator.calculateAdjustedDistance(150, 15);
console.log(`Play as: ${uphill.playing} yards`); // ~165 yards

// Downhill shot: subtract distance
const downhill = DistanceCalculator.calculateAdjustedDistance(150, -15);
console.log(`Play as: ${downhill.playing} yards`); // ~135 yards
```

### Wind-Adjusted Distance

```javascript
const club = DistanceCalculator.calculateClubSelection(
  165,  // distance
  10,   // elevation
  20,   // 20 mph wind
  0,    // headwind (0° = into wind)
  0     // shot direction
);
console.log(`Adjusted: ${club.adjustedDistance} yards`); // ~185 yards
```

## Best Practices

### GPS Accuracy

1. **Wait for Good Signal:**
   - Green indicator = excellent (< 10m)
   - Yellow indicator = good (10-20m)
   - Red indicator = fair (> 20m)

2. **Open Sky:**
   - GPS works best with clear view of sky
   - Trees and buildings reduce accuracy
   - May take longer to acquire signal in valleys

3. **Battery Management:**
   - GPS uses significant battery
   - Bring portable charger for long rounds
   - Consider airplane mode between holes

### Distance Measurement

1. **Account for Elevation:**
   - Always use elevation-adjusted distances
   - Uphill plays longer, downhill shorter
   - Rule of thumb: 1 yard per foot of elevation

2. **Consider Wind:**
   - Headwind: add distance
   - Tailwind: subtract distance
   - Crosswind: minimal distance effect

3. **Green Depth:**
   - Distance is to center of green
   - Adjust for pin position (front/back)
   - Consider green depth (typically 20-30 yards)

### Shot Tracking

1. **Mark Every Shot:**
   - Provides accurate distance data
   - Helps analyze your game
   - Useful for club selection

2. **Review After Round:**
   - Export GPS data for analysis
   - Identify patterns in your game
   - Improve course management

## Troubleshooting

### GPS Not Working

**Problem:** "GPS permission denied"
- **Solution:** Enable location services in browser settings
- Chrome: Settings → Privacy → Site Settings → Location
- Safari: Settings → Privacy → Location Services

**Problem:** "GPS unavailable"
- **Solution:** Check device has GPS capability
- Ensure location services enabled at system level
- Try restarting browser/device

**Problem:** Poor accuracy (> 20m)
- **Solution:** Move to open area with clear sky view
- Wait longer for GPS to acquire more satellites
- Restart GPS tracking

### Distance Issues

**Problem:** Distance seems incorrect
- **Solution:** Verify course GPS coordinates are accurate
- Check that you're on correct hole
- Ensure GPS has good accuracy (< 10m)

**Problem:** Elevation adjustment not working
- **Solution:** Verify hole has elevation data set
- Check elevation values are in feet
- Recalculate with manual elevation input

### Mobile Interface Issues

**Problem:** Interface not loading
- **Solution:** Ensure HTTPS connection (required for GPS)
- Clear browser cache
- Try different browser

**Problem:** Battery draining quickly
- **Solution:** Reduce screen brightness
- Close other apps
- Use airplane mode between holes
- Bring portable charger

## Support

For additional help:
- Check the main README.md for general usage
- Review code examples in src/index.js
- Open an issue on the project repository

---

**Built with ❤️ for golfers by golfers**