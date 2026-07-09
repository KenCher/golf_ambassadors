# How to Record Accurate Deerfield Hole Data 📍

## The Problem
The Deerfield Country Club hole coordinates in the app are not accurate because they were auto-generated. To get precise GPS distances, you need to record the actual tee and green locations.

## Solution: Use the Course Mapper Tool

### Step 1: Prepare the Course Mapper

**On your Mac:**
```bash
cd /Users/kencheru/onboarding/Golf4us
node server.cjs
```

**On your Android phone (same WiFi):**
- Open Chrome
- Go to: `http://YOUR_MAC_IP:8000/course-mapper.html`
- Or email `public/course-mapper.html` to yourself and open it

### Step 2: At Deerfield Today

**For Each Hole You Play:**

1. **At the Tee Box:**
   - Open Course Mapper app
   - Wait for GPS to lock (green indicator)
   - Tap "📍 Record Tee Position"
   - Enter hole details:
     - Hole Number: 1, 2, 3, etc.
     - Par: 3, 4, or 5
     - Yardage: (from scorecard)
     - Stroke Index: (from scorecard)
   - Tap "Save Tee"

2. **At the Green:**
   - Walk to center of green
   - Tap "📍 Record Green Position"
   - Tap "Save Green"
   - Hole data is now recorded!

3. **Repeat for Each Hole**

### Step 3: Export and Use

**After Your Round:**

1. **In Course Mapper:**
   - Tap "📥 Export Course Data"
   - Save the JSON file

2. **Import to GPS App:**
   - Open `public/course-database.html`
   - Click "Import Course"
   - Select your exported JSON file
   - Course is now saved with accurate data!

3. **Next Time:**
   - GPS app will use your accurate hole data
   - Distances will be precise
   - Hole layout will show correct positions

---

## Quick Alternative: Manual Recording

If you don't want to use Course Mapper, you can manually note coordinates:

**At Each Tee Box:**
- Open GPS app
- Note your current coordinates (shown in console)
- Write down: Hole #, Tee Lat, Tee Lon

**At Each Green:**
- Walk to center of green
- Note coordinates
- Write down: Green Lat, Green Lon

**After Round:**
- Send me the coordinates
- I'll update the database for you

---

## Today's Workaround

Since you're playing today and don't have accurate hole data yet:

### The GPS App Will Still Work!

**What Works:**
- ✅ Distance to green (uses course center as fallback)
- ✅ Compass direction
- ✅ Score tracking
- ✅ Shot marking
- ✅ Hole layout visualization (approximate)

**What's Approximate:**
- ⚠️ Exact green positions (within ~50-100 yards)
- ⚠️ Hole layout shapes (generic par 3/4/5 shapes)

**The app calculates distance to the course center**, which gives you a general idea. It's not perfect, but it's usable for your first round.

---

## For Best Results Next Time

1. **Today:** Play with current app (approximate distances)
2. **Record Data:** Use Course Mapper to record accurate positions
3. **Import:** Add accurate data to course database
4. **Next Round:** Enjoy precise GPS distances!

---

## Exit/Change Course Feature

**Already Built In!**

To exit current round:
1. Tap "Change Course" button (top right of hole info)
2. Confirm you want to exit
3. Returns to course selection screen

You can:
- ✅ Change to different course
- ✅ Start new round
- ✅ Select different tee boxes

---

## Tips for Today

### Getting Best Distance Estimates:

1. **Wait for Good GPS Signal**
   - Accuracy should be <20m
   - Green indicator means GPS is working

2. **Use Relative Distances**
   - Even if absolute distance is off by 50 yards
   - The change in distance as you walk is accurate
   - Watch how distance decreases as you approach green

3. **Mark Your Shots**
   - Tap "📍 Mark Shot" after each shot
   - This gives you accurate shot distances
   - Even if green distance is approximate

4. **Use Hole Layout Visually**
   - Shows your progress along the hole
   - Helps understand where you are
   - Generic shape but useful for orientation

### Battery Management:

- Lower screen brightness
- Close other apps
- Bring portable charger
- Phone will use more battery with GPS active

---

## Summary

**Today:** Use app with approximate distances (good enough!)
**After Today:** Record accurate hole data with Course Mapper
**Next Time:** Enjoy precise GPS distances at Deerfield!

The "Change Course" button is already there - just tap it anytime to exit and return to course selection.

Have a great round! ⛳🏌️📱