# Hybrid Course Search System Guide

## Overview

The Golf4us (G4K) system now uses a **hybrid approach** for finding golf courses:
1. **Local Database First** - Instant results from known courses
2. **GPS Location Search** - Find nearby courses using OpenStreetMap
3. **Web Search Fallback** - Optional future enhancement with Python script

This provides the best of both worlds: fast, reliable results for known courses, plus the ability to discover new courses.

## System Architecture

### Current Implementation (JavaScript)

```
User Search Request
        ↓
┌───────────────────────┐
│  Local Course DB      │ ← Instant Results
│  (JavaScript Array)   │
└───────────────────────┘
        ↓ (if not found)
┌───────────────────────┐
│  OpenStreetMap API    │ ← GPS/Location Search
│  (Overpass API)       │
└───────────────────────┘
        ↓ (optional)
┌───────────────────────┐
│  Python Script        │ ← Future Enhancement
│  (Web Scraping)       │
└───────────────────────┘
```

## Known Courses Database

### Current Courses (9 total)

**Local Courses (Poughkeepsie, NY area):**
1. **McCann Memorial Golf Course** - Public, Par 72, 6,524 yards
2. **Casperkill Golf Club** - Par 72, 6,690 yards (Robert Trent Jones design)
3. **Salmon Creek Country Club** - Par 72, 6,430 yards
4. **Deerfield Country Club** - 27 holes, Par 72 combinations

**Famous Courses (Sample Database):**
5. **Pebble Beach Golf Links** - CA
6. **Augusta National Golf Club** - GA
7. **Pinehurst No. 2** - NC
8. **Torrey Pines Golf Course** - CA
9. **Bethpage Black Course** - NY

### Database Location

The course database is stored in `public/g4k-course-finder.html`:

```javascript
const sampleCourses = [
    {
        id: 'mccann-memorial',
        name: 'McCann Memorial Golf Course',
        city: 'Poughkeepsie',
        state: 'NY',
        holes: 18,
        par: 72,
        location: { lat: 41.6856, lon: -73.8648 }
    },
    // ... more courses
];
```

## How It Works

### 1. Search by Name

When a user searches for a course by name:

```javascript
// Search local database first
const lowerQuery = query.toLowerCase();
let courses = sampleCourses.filter(course =>
    course.name.toLowerCase().includes(lowerQuery) ||
    course.city.toLowerCase().includes(lowerQuery) ||
    course.state.toLowerCase().includes(lowerQuery)
);

// If found locally, return immediately (instant results)
if (courses.length > 0) {
    displayResults(courses);
    return;
}

// If not found, try OpenStreetMap API
searchOpenStreetMap(query);
```

**Benefits:**
- ✅ Instant results for known courses
- ✅ No API calls needed
- ✅ Works offline for known courses
- ✅ Guaranteed accurate data

### 2. GPS Location Search

When a user clicks "Find Courses Near Me":

```javascript
// Get user's GPS coordinates
navigator.geolocation.getCurrentPosition(position => {
    const lat = position.coords.latitude;
    const lon = position.coords.longitude;
    
    // Search OpenStreetMap Overpass API
    searchNearby(lat, lon, radius);
});
```

**Benefits:**
- ✅ Discovers courses not in local database
- ✅ Shows distance from user
- ✅ Real-time data from OpenStreetMap
- ✅ Works anywhere in the world

### 3. Tournament Manager Integration

Courses can be loaded directly into the tournament manager:

```javascript
// Preset dropdown in tournament-manager.html
<select id="preset-course" onchange="loadPresetCourse()">
    <option value="mccann">McCann Memorial Golf Course</option>
    <option value="casperkill">Casperkill Golf Club</option>
    <option value="salmon-creek">Salmon Creek Country Club</option>
    <option value="deerfield">Deerfield Country Club</option>
</select>
```

**Benefits:**
- ✅ One-click course loading
- ✅ Complete scorecard data (par, handicaps, yardages)
- ✅ No manual data entry
- ✅ Verified course information

## Adding New Courses

### Method 1: Add to Local Database (Recommended)

1. **Create JSON scorecard file** (e.g., `public/new-course-scorecard.json`)
2. **Add to course finder** (`public/g4k-course-finder.html`)
3. **Add to tournament manager** (`public/tournament-manager.html`)

Example:

```javascript
// In g4k-course-finder.html
{
    id: 'new-course',
    name: 'New Golf Course',
    city: 'City Name',
    state: 'ST',
    holes: 18,
    par: 72,
    location: { lat: 00.0000, lon: -00.0000 }
}

// In tournament-manager.html
<option value="new-course">New Golf Course (City, ST)</option>

// In loadPresetCourse() function
if (preset === 'new-course') {
    name = 'New Golf Course';
    holes = [
        {number: 1, par: 4, handicap: 9},
        // ... all 18 holes
    ];
}
```

### Method 2: Use Python Script (Future Enhancement)

The Python script `golf_scorecard.py` can search for courses online:

```python
# Known courses in Python script
KNOWN_COURSES = {
    "mccann memorial golf course": {
        "par": 72,
        "tees": {...},
        "holes": {...}
    }
}
```

**To integrate:**
1. Convert Python script to Node.js backend
2. Create API endpoint: `/api/search-course?name=...`
3. Frontend calls API when course not found locally
4. Returns detailed scorecard data

## Data Files Structure

### Course JSON Format

```json
{
  "courseName": "Course Name",
  "city": "City",
  "state": "ST",
  "location": {
    "lat": 00.0000,
    "lon": -00.0000
  },
  "holes": 18,
  "par": 72,
  "teeBoxes": {
    "blue": {
      "name": "Blue",
      "totalYards": 6500,
      "rating": 71.5,
      "slope": 125
    }
  },
  "holes": [
    {
      "number": 1,
      "par": 4,
      "handicap": 9,
      "yardages": {
        "blue": 380,
        "white": 360,
        "gold": 330,
        "red": 310
      }
    }
  ]
}
```

## Usage Examples

### Example 1: Quick Tournament Setup

```
1. Open tournament-manager.html
2. Select "McCann Memorial Golf Course" from dropdown
3. Course loads with all 18 holes, pars, and handicaps
4. Add players and start tournament
```

### Example 2: Find Nearby Courses

```
1. Open g4k-course-finder.html
2. Click "📍 Find Courses Near Me"
3. Allow location access
4. See list of nearby courses with distances
5. Click course to load in tournament manager
```

### Example 3: Search by Name

```
1. Open g4k-course-finder.html
2. Click "🔍 Search by Name"
3. Type "McCann" or "Poughkeepsie"
4. Instant results from local database
5. Select course to use
```

## Performance Comparison

| Method | Speed | Accuracy | Offline | Coverage |
|--------|-------|----------|---------|----------|
| Local DB | ⚡ Instant | ✅ 100% | ✅ Yes | Limited |
| GPS Search | 🔄 2-5 sec | ⚠️ Varies | ❌ No | Global |
| Python Script | 🔄 5-10 sec | ⚠️ Varies | ❌ No | Global |

## Best Practices

### For Tournament Organizers

1. **Use preset courses** when available (fastest, most accurate)
2. **Add your home course** to local database for future use
3. **Verify handicap rankings** with official scorecard before tournament
4. **Test course loading** before tournament day

### For Developers

1. **Add popular local courses** to the database
2. **Include complete scorecard data** (par, handicaps, yardages)
3. **Verify GPS coordinates** for accurate location search
4. **Document data sources** in metadata

### For Users

1. **Search by name first** (faster than GPS)
2. **Use GPS search** to discover new courses
3. **Save course data** for offline use
4. **Report inaccuracies** to improve database

## Future Enhancements

### Phase 1: Current (✅ Complete)
- Local course database with 9 courses
- GPS location search via OpenStreetMap
- Tournament manager integration
- Complete scorecard data for 4 local courses

### Phase 2: Backend Integration (Planned)
- Convert Python script to Node.js API
- Add `/api/search-course` endpoint
- Web scraping for unknown courses
- Automatic scorecard data extraction

### Phase 3: User Contributions (Future)
- User-submitted course data
- Community verification system
- Course photo uploads
- Review and rating system

### Phase 4: Advanced Features (Future)
- Course condition updates
- Weather integration
- Tee time booking
- Score history tracking

## Troubleshooting

### Course Not Found

**Problem:** Search returns no results

**Solutions:**
1. Check spelling of course name
2. Try searching by city name
3. Use GPS location search
4. Add course to local database manually

### GPS Not Working

**Problem:** "Find Courses Near Me" fails

**Solutions:**
1. Allow location access in browser
2. Check if HTTPS is enabled
3. Try manual search by city name
4. Use desktop browser (better GPS support)

### Incorrect Course Data

**Problem:** Par or handicaps don't match scorecard

**Solutions:**
1. Verify with official course scorecard
2. Update JSON file with correct data
3. Report issue for database correction
4. Use custom course entry feature

## Technical Details

### OpenStreetMap Overpass API

Query format for nearby courses:

```javascript
const query = `
[out:json][timeout:25];
(
  node["leisure"="golf_course"](around:${radius},${lat},${lon});
  way["leisure"="golf_course"](around:${radius},${lat},${lon});
  relation["leisure"="golf_course"](around:${radius},${lat},${lon});
);
out body;
>;
out skel qt;
`;
```

### GPS Accuracy

- **Typical accuracy:** 5-50 meters
- **Best conditions:** Clear sky, outdoor location
- **Worst conditions:** Indoor, urban canyons
- **Fallback:** Manual city/state search

## Support and Resources

### Documentation Files
- `MCCANN_MEMORIAL_GUIDE.md` - McCann Memorial course details
- `CASPERKILL_SCORECARD_GUIDE.md` - Casperkill course details
- `DEERFIELD_SCORECARD_GUIDE.md` - Deerfield course details
- `SALMON_CREEK_GUIDE.md` - Salmon Creek course details

### Code Files
- `public/g4k-course-finder.html` - Course search interface
- `public/tournament-manager.html` - Tournament management
- `public/*-scorecard.json` - Course data files

### Python Script (Optional)
- `golf_scorecard.py` - Course search script
- Can be integrated as Node.js backend in future

## Conclusion

The hybrid course search system provides:
- ✅ **Fast results** for known courses (instant)
- ✅ **Global coverage** via GPS search
- ✅ **Accurate data** from verified sources
- ✅ **Easy integration** with tournament manager
- ✅ **Offline capability** for known courses
- ✅ **Extensible design** for future enhancements

This approach balances speed, accuracy, and coverage to provide the best user experience for golf tournament management.