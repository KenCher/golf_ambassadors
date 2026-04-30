# Scorecard Par Display Fix Guide

## The Problem
When loading a preset course (like Casperkill) after adding players, the scorecard showed all Par 4s instead of the correct par values (5,4,3,4,5,4,4,3,4...).

## The Solution
Updated `tournament-manager.html` with two fixes:

### Fix 1: Update Course Data When Loading Preset
When you select a preset course, the system now:
1. Updates `customCourse` with correct hole data
2. Resets all players' score arrays to match new course
3. Automatically refreshes the scorecard
4. Shows correct par values immediately

### Fix 2: Force Refresh on Tab Switch
When you switch to the Scorecard tab, it now:
1. Always calls `updateScorecard()` 
2. Ensures current course data is used
3. Displays correct par values

## How to Test the Fix

### Test 1: Load Course After Adding Players
1. Open `tournament-manager.html` in browser
2. **Add some players first** (John Doe, Jane Smith, etc.)
3. Go to "Course Setup" tab
4. Select "Casperkill Golf Club" from preset dropdown
5. Go to "Scorecard" tab
6. **Expected Result:** Par row should show: 5,4,3,4,5,4,4,3,4,5,4,3,4,4,4,3,4,5

### Test 2: Load Course Before Adding Players
1. Refresh the page (Ctrl+R or Cmd+R)
2. Go to "Course Setup" tab
3. Select "Casperkill Golf Club" from preset dropdown
4. Go to "Players" tab
5. Add some players
6. Go to "Scorecard" tab
7. **Expected Result:** Par row should show: 5,4,3,4,5,4,4,3,4,5,4,3,4,4,4,3,4,5

### Test 3: Switch Between Courses
1. Load "Casperkill Golf Club"
2. Add players
3. Check scorecard (should show Casperkill pars)
4. Go back to "Course Setup"
5. Select "McCann Memorial Golf Course"
6. Go to "Scorecard" tab
7. **Expected Result:** Par row should show: 4,5,4,5,3,4,4,3,4,4,4,3,4,5,3,4,5,4

## Troubleshooting

### If You Still See All Par 4s:

**Step 1: Clear Browser Cache**
- Chrome/Edge: Ctrl+Shift+Delete (Cmd+Shift+Delete on Mac)
- Select "Cached images and files"
- Click "Clear data"

**Step 2: Hard Refresh**
- Windows: Ctrl+F5 or Ctrl+Shift+R
- Mac: Cmd+Shift+R

**Step 3: Verify File Was Updated**
Check that `public/tournament-manager.html` contains these lines around line 603-611:

```javascript
// Update existing players' score arrays to match new course length
players.forEach(player => {
    scores[player.id] = Array(holes.length).fill(null);
});

// Refresh scorecard if players exist
if (players.length > 0) {
    updateScorecard();
}
```

**Step 4: Check Browser Console**
- Press F12 to open Developer Tools
- Go to Console tab
- Look for any JavaScript errors
- If you see errors, report them

### If getCourseHoles() Returns Wrong Data:

The `getCourseHoles()` function should return `customCourse.holes` if it exists:

```javascript
function getCourseHoles() {
    if (customCourse && customCourse.holes) {
        return customCourse.holes;
    }
    // Fallback to default 18-hole par 72 course
    return Array.from({length: 18}, (_, i) => ({
        number: i + 1,
        par: [4,4,4,3,5,4,4,3,4,4,4,4,3,5,4,4,3,5][i],
        handicap: i + 1
    }));
}
```

If `customCourse` is null or undefined, it falls back to default Par 72.

## Expected Par Values by Course

### Casperkill Golf Club
**Front 9:** 5, 4, 3, 4, 5, 4, 4, 3, 4 (Par 36)
**Back 9:** 5, 4, 3, 4, 4, 4, 3, 4, 5 (Par 36)
**Total:** Par 72

### McCann Memorial Golf Course
**Front 9:** 4, 5, 4, 5, 3, 4, 4, 3, 4 (Par 36)
**Back 9:** 4, 4, 3, 4, 5, 3, 4, 5, 4 (Par 36)
**Total:** Par 72

### Salmon Creek Country Club
**Front 9:** 4, 5, 4, 3, 4, 4, 4, 4, 4 (Par 36)
**Back 9:** 3, 4, 5, 4, 5, 4, 3, 4, 4 (Par 36)
**Total:** Par 72

### Deerfield Country Club (North/South)
**Front 9:** 5, 4, 4, 3, 5, 4, 4, 3, 4 (Par 36)
**Back 9:** 4, 3, 5, 4, 3, 5, 4, 5, 3 (Par 36)
**Total:** Par 72

## Verification Checklist

- [ ] Browser cache cleared
- [ ] Page hard refreshed
- [ ] Preset course selected from dropdown
- [ ] Course name shows in header (e.g., "⛳ Casperkill Golf Club")
- [ ] Scorecard tab shows correct par values
- [ ] Par values match expected values above
- [ ] Switching courses updates par values correctly

## Still Having Issues?

If the scorecard still shows all Par 4s after following all steps:

1. **Check if customCourse is set:**
   - Open browser console (F12)
   - Type: `customCourse`
   - Press Enter
   - Should show: `{holes: Array(18)}`
   - If it shows `null` or `undefined`, the course didn't load

2. **Check the holes array:**
   - In console, type: `customCourse.holes`
   - Should show array of 18 objects with par values
   - Example: `[{number: 1, par: 5, handicap: 1}, ...]`

3. **Manually trigger update:**
   - In console, type: `updateScorecard()`
   - Press Enter
   - Scorecard should refresh with correct pars

4. **Check for JavaScript errors:**
   - Look for red error messages in console
   - Common issues: syntax errors, undefined variables
   - Report any errors found

## Success Indicators

✅ Course name displays in header
✅ Par row shows varied values (not all 4s)
✅ Par values match official scorecard
✅ Switching courses updates par values
✅ No JavaScript errors in console

## Contact/Support

If issues persist after following this guide:
- Check that all files are saved
- Verify you're editing the correct file
- Try a different browser
- Check file permissions
- Review browser console for errors