# How to Add More Golf Courses to the Database

## Method 1: Using Python Script (Recommended)

### Step 1: Find Courses with Python Script

Run your `golf_scorecard.py` script to find courses:

```bash
# Search for courses in a specific area
python golf_scorecard.py "Poughkeepsie golf"
python golf_scorecard.py "Hyde Park golf"
python golf_scorecard.py "Fishkill golf"
python golf_scorecard.py "Wappingers Falls golf"
```

### Step 2: Get Course Details

For each course found, you need:
- Course name
- City
- State
- Number of holes (usually 18 or 9)
- Par (usually 72 for 18 holes, 36 for 9 holes)
- GPS coordinates (lat/lon)

### Step 3: Add to Sample Database

Edit `public/g4k-course-finder.html` and add courses to the `sampleCourses` array:

```javascript
{
    id: 'course-id',  // lowercase, no spaces, use hyphens
    name: 'Course Name',
    city: 'City Name',
    state: 'NY',
    holes: 18,
    par: 72,
    location: { lat: 41.xxxx, lon: -73.xxxx }
}
```

### Step 4: Get GPS Coordinates

If you don't have GPS coordinates, you can:

1. **Google Maps:**
   - Search for the course
   - Right-click on the location
   - Click the coordinates to copy them
   - Format: `41.6948, -73.9196`

2. **Python Script:**
   - Some golf course APIs return coordinates
   - Or use geocoding library

3. **Manual Entry:**
   - Use approximate coordinates from Google Maps

## Method 2: Add Courses Manually

### Find Course Information

1. Visit course website
2. Check Google Maps for location
3. Look up scorecard for holes/par
4. Get GPS coordinates from Google Maps

### Add to Database

Location in code: `public/g4k-course-finder.html`, line ~218

```javascript
const sampleCourses = [
    // ... existing courses ...
    {
        id: 'new-course-id',
        name: 'New Golf Course Name',
        city: 'City',
        state: 'NY',
        holes: 18,
        par: 72,
        location: { lat: 41.xxxx, lon: -73.xxxx }
    }
];
```

## Method 3: Create Full Scorecard (For Tournament Use)

If you want to use a course in tournaments (with correct par for each hole):

### Step 1: Create JSON Scorecard File

Create `public/new-course-scorecard.json`:

```json
{
  "courseName": "Course Name",
  "city": "City",
  "state": "NY",
  "location": {
    "lat": 41.xxxx,
    "lon": -73.xxxx
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
        "blue": 380
      }
    }
    // ... all 18 holes
  ]
}
```

### Step 2: Add to Tournament Manager

Edit `public/tournament-manager.html`, find the preset dropdown (~line 287):

```html
<option value="new-course">New Course Name (City, ST)</option>
```

### Step 3: Add to loadPresetCourse Function

In `tournament-manager.html`, find `loadPresetCourse()` function (~line 490):

```javascript
} else if (preset === 'new-course') {
    name = 'New Course Name';
    holes = [
        {number: 1, par: 4, handicap: 9},
        {number: 2, par: 5, handicap: 5},
        // ... all 18 holes
    ];
}
```

## Example: Adding a Course from Python Script

### Python Script Output:
```
✅ Found Fishkill Golf Course

## Tee Summary
| Tee  | Yards | Rating | Slope |
|------|-------|--------|-------|
| Blue |  6200 |   70.5 |   122 |

## Hole-by-Hole (Blue Tees)
| Hole | Par | Yards |
|------|-----|-------|
|    1 |   4 |   350 |
...
```

### Add to g4k-course-finder.html:

```javascript
{
    id: 'fishkill-gc',
    name: 'Fishkill Golf Course',
    city: 'Fishkill',
    state: 'NY',
    holes: 18,
    par: 72,
    location: { lat: 41.5350, lon: -73.8990 }  // Get from Google Maps
}
```

## Current Database

**Poughkeepsie Area (7 courses):**
1. Casperkill Golf Club
2. McCann Memorial Golf Course
3. Dutchess Golf Club
4. Red Hook Golf Club
5. Vassar Golf Course
6. Beekman Country Club
7. Thomas Carvel Country Club

**Famous Courses (5 courses):**
1. Pebble Beach Golf Links
2. Augusta National Golf Club
3. Pinehurst No. 2
4. Torrey Pines Golf Course
5. Bethpage Black Course

**Total:** 12 courses in database

## Tips

1. **Verify GPS Coordinates:**
   - Use Google Maps to confirm location
   - Coordinates should be near the clubhouse
   - Format: `{ lat: 41.xxxx, lon: -73.xxxx }`

2. **Course ID Naming:**
   - Use lowercase
   - Replace spaces with hyphens
   - Keep it short and descriptive
   - Example: "Red Hook Golf Club" → `red-hook-gc`

3. **Distance Filter:**
   - Current setting: 50km radius
   - To change: Edit `MAX_DISTANCE_KM` in `g4k-course-finder.html`
   - Line ~345: `const MAX_DISTANCE_KM = 50;`

4. **Testing:**
   - After adding courses, refresh browser
   - Click "Find Courses Near Me"
   - Verify new courses appear
   - Check distances are reasonable

## Troubleshooting

**Course Not Appearing:**
- Check GPS coordinates are correct
- Verify course is within 50km radius
- Clear browser cache and refresh
- Check for JavaScript errors in console

**Wrong Distance:**
- Verify lat/lon coordinates
- Check coordinate format (decimal degrees)
- Ensure lat/lon aren't swapped

**Course Shows But Can't Select:**
- Check course ID is unique
- Verify all required fields are present
- Look for JavaScript errors in console

## Future Enhancement: Automated Course Discovery

To automatically discover courses using OpenStreetMap:

1. **Fix CORS Issue:**
   - Set up backend proxy server
   - Use Node.js to call Overpass API
   - Return results to frontend

2. **Convert Python Script to API:**
   - Create Node.js endpoint
   - Call from frontend when needed
   - Cache results in database

3. **User Contributions:**
   - Allow users to submit courses
   - Verify and add to database
   - Build community course database