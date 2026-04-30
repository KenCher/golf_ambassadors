# OpenStreetMap Data Update Guide

## Issue: Outdated Course Names in OSM

OpenStreetMap (OSM) data can be outdated, showing old course names or incorrect information. For example:
- **Old Name:** "Brockport Country Club" 
- **Current Name:** "Deerfield Country Club" (renamed years ago)

## How the App Handles This

The Golf4us GPS app uses a **hybrid data approach** with priority levels:

### Data Source Priority (Highest to Lowest):

1. **Custom Courses** (from Course Database Manager)
   - Manually added courses with accurate, up-to-date information
   - Highest priority - always used when available

2. **Fallback Database** (built into gps-app.html)
   - Pre-configured local courses with accurate data
   - Updated manually to reflect current course names
   - Takes precedence over OSM data

3. **OpenStreetMap API** (automatic discovery)
   - Discovers nearby courses automatically
   - May have outdated names or information
   - Only used if not already in fallback database

## Recent Fixes Applied

### ✅ Removed Outdated Entry
- **Removed:** "Brockport Country Club" (old name, wrong location)
- **Kept:** "Deerfield Country Club - North Course" (accurate data)
- **Kept:** "Deerfield Country Club - South Course" (accurate data)

### ✅ Fixed GPS Distance Calculations
- Corrected distance calculation from meters to yards
- Fixed course distance sorting
- Improved accuracy for "distance to green" feature

## How to Update Course Data

### Method 1: Add to Fallback Database (Recommended)

Edit `public/gps-app.html` and add/update courses in the `fallbackCourses` array:

```javascript
{
    id: 'your-course-id',
    name: 'Current Course Name',
    location: { lat: 43.xxxx, lon: -77.xxxx },
    city: 'City',
    state: 'NY',
    holes: 18,
    par: 72,
    teeBoxes: {
        blue: { totalYards: 6500, rating: 71.8, slope: 128 },
        white: { totalYards: 6100, rating: 69.5, slope: 122 }
    },
    holeData: generateDefaultHoles(lat, lon, par)
}
```

### Method 2: Use Course Database Manager

1. Open `public/course-database.html`
2. Click "Add New Course"
3. Enter accurate course information
4. Save to local storage
5. Data will be used in GPS app automatically

### Method 3: Use Course Mapper

1. Visit the golf course
2. Open `public/course-mapper.html` on your phone
3. Walk each hole and record GPS coordinates
4. Export as JSON
5. Import into Course Database Manager

## Preventing OSM Duplicates

The app automatically prevents OSM duplicates by:

1. **Name Matching:** Checks if course names are similar
2. **Location Proximity:** Checks if courses are within 1km
3. **Priority System:** Always uses fallback data over OSM when duplicate detected

Example from code:
```javascript
const isDuplicate = fallbackCourses.some(fallbackCourse => {
    const nameSimilar = fallbackCourse.name.toLowerCase()
        .includes(osmCourse.name.toLowerCase().split('-')[0].trim());
    const distance = calculateDistance(...);
    return nameSimilar && distance < 1000; // Within 1km
});
```

## Updating OpenStreetMap (Optional)

If you want to help fix OSM data for everyone:

1. Create account at https://www.openstreetmap.org
2. Find the golf course on the map
3. Click "Edit" 
4. Update the course name and details
5. Save changes with description: "Updated course name to current name"

**Note:** OSM changes can take time to propagate to the Overpass API used by the app.

## Current Rochester Area Courses in Fallback Database

✅ **Accurate & Up-to-Date:**
- Deerfield Country Club - North Course (Brockport, NY)
- Deerfield Country Club - South Course (Brockport, NY)
- Salmon Creek Country Club (Spencerport, NY)
- Churchville Golf Club (Churchville, NY)
- Braemar Country Club (Spencerport, NY)
- Buttonwood Creek Golf Course (Hilton, NY)
- Mill Creek Golf Club (Rochester, NY)
- Shadow Lake Golf Club (Penfield, NY)
- Greystone Golf Club (Walworth, NY)

## Testing After Updates

1. Clear browser cache and localStorage
2. Reload `public/gps-app.html`
3. Allow GPS access
4. Verify course list shows correct names
5. Check console logs for duplicate detection
6. Confirm distances are accurate

## Troubleshooting

**Problem:** Still seeing old course name
- **Solution:** Clear browser cache and localStorage, reload page

**Problem:** Course appears twice in list
- **Solution:** Check fallback database for exact name match with OSM data

**Problem:** Wrong course location
- **Solution:** Update coordinates in fallback database using Google Maps

**Problem:** OSM returns no courses
- **Solution:** Fallback database will be used automatically

## Best Practices

1. ✅ Always verify course names with official website
2. ✅ Use Google Maps to get accurate coordinates
3. ✅ Test GPS app after making changes
4. ✅ Document changes in git commit messages
5. ✅ Keep fallback database updated with local courses

## Contact & Support

For course data updates or corrections:
- Check official course website for current information
- Use Google Maps to verify location and name
- Update fallback database in `gps-app.html`
- Test thoroughly before deploying

---

**Last Updated:** 2026-04-25
**Status:** Brockport Country Club entry removed, Deerfield data verified accurate