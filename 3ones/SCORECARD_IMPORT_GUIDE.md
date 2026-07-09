# Scorecard Import Guide

## 📋 How to Import Course Data from Scorecards

This guide shows you how to add accurate course data from physical or digital scorecards into Golf4us.

---

## 🎯 Quick Start

### Option 1: Use Scorecard Importer Tool (Easiest)
1. Open `public/scorecard-importer.html` in your browser
2. Fill in course information
3. Enter hole-by-hole data from scorecard
4. Click "Add to Database"
5. Done! GPS app will now use this data

**Time:** 15-20 minutes per course

### Option 2: Import Pre-Made JSON
1. Download course JSON file (e.g., `deerfield-course-data.json`)
2. Open `public/course-database.html`
3. Go to Import tab
4. Paste JSON content
5. Click Import

**Time:** 2 minutes per course

### Option 3: Manual Entry
1. Open `public/course-database.html`
2. Go to "Add Course Manually" tab
3. Enter all information
4. Save

**Time:** 20-30 minutes per course

---

## 📖 Step-by-Step: Using Scorecard Importer

### Step 1: Gather Scorecard Information

You'll need from the scorecard:
- ✅ Course name
- ✅ Location (city, state)
- ✅ GPS coordinates (use Google Maps)
- ✅ Tee box yardages (Blue, White, Gold, Red)
- ✅ Course ratings and slopes for each tee
- ✅ Par for each hole (1-18)
- ✅ Stroke index (handicap) for each hole
- ✅ Yardage for each hole

### Step 2: Open Scorecard Importer

```bash
open public/scorecard-importer.html
```

Or navigate to it in your browser.

### Step 3: Enter Course Information

**Course Name:** Full official name
- Example: "Deerfield Country Club"

**City & State:** Location
- Example: "Brockport, NY"

**GPS Coordinates:** Find on Google Maps
1. Go to Google Maps
2. Search for the course
3. Right-click on the clubhouse
4. Click "What's here?"
5. Copy coordinates (e.g., 43.2156, -77.7625)

### Step 4: Enter Tee Box Data

For each tee box (Blue, White, Gold, Red), enter:

**Total Yardage:** From scorecard
- Example: Blue = 6800 yards

**Course Rating:** USGA rating
- Example: Blue = 73.5

**Slope Rating:** USGA slope
- Example: Blue = 135

**Where to find this:**
- Usually on the scorecard
- Or on course website
- Or USGA GHIN database

### Step 5: Enter Hole-by-Hole Data

For each of the 18 holes, enter:

**Par:** 3, 4, or 5
- From scorecard

**Stroke Index:** 1-18 (handicap)
- From scorecard (usually labeled "HCP" or "Handicap")
- Lower numbers = harder holes

**Yardage:** Distance in yards
- Use yardage from your preferred tee box
- Or enter multiple times for different tees

### Step 6: Generate and Save

1. Click "Generate JSON" to preview
2. Review the output
3. Click "Add to Database" to save
4. Or click "Download JSON" to save file for later

---

## 📄 Example: Deerfield Country Club

### Scorecard Data

**Course Info:**
- Name: Deerfield Country Club
- Location: Brockport, NY
- Coordinates: 43.2156, -77.7625
- Par: 72

**Tee Boxes:**
| Tee | Yards | Rating | Slope |
|-----|-------|--------|-------|
| Blue | 6800 | 73.5 | 135 |
| White | 6400 | 71.2 | 128 |
| Gold | 5900 | 68.8 | 120 |
| Red | 5200 | 66.5 | 115 |

**Holes (Example - Front 9):**
| Hole | Par | SI | Yards |
|------|-----|----|----|
| 1 | 4 | 7 | 380 |
| 2 | 5 | 1 | 520 |
| 3 | 3 | 15 | 165 |
| 4 | 4 | 5 | 395 |
| 5 | 4 | 11 | 410 |
| 6 | 3 | 17 | 180 |
| 7 | 5 | 3 | 540 |
| 8 | 4 | 13 | 370 |
| 9 | 4 | 9 | 400 |

*(Continue for holes 10-18)*

---

## 🔍 Finding Course Information

### GPS Coordinates
**Google Maps Method:**
1. Search for course name
2. Right-click on clubhouse/parking lot
3. Select "What's here?"
4. Copy coordinates

**Alternative:** Use Course Mapper tool at the course

### Course Rating & Slope
**Sources:**
1. **Course Scorecard** - Usually printed on it
2. **Course Website** - Often in "Course Info" section
3. **USGA GHIN** - https://www.usga.org/course-rating.html
4. **Golf Genius** - If course uses it
5. **Ask Pro Shop** - They always have this info

### Stroke Index (Handicap)
**On Scorecard:**
- Usually labeled "HCP", "Handicap", or "SI"
- Numbers 1-18
- 1 = hardest hole, 18 = easiest hole

**If Missing:**
- Use standard pattern: Long par 5s and 4s get low numbers
- Par 3s usually get high numbers
- Or leave as 1-18 in order

---

## 💾 Working with JSON Files

### Import Existing JSON

If someone shares a course JSON file:

1. Open `course-database.html`
2. Go to Import tab
3. Open JSON file in text editor
4. Copy entire contents
5. Paste into import box
6. Click Import

### Export Your Courses

To share with friends:

1. Open `course-database.html`
2. Go to Export tab
3. Click "Download Database (JSON)"
4. Share file via email/text/cloud

### Pre-Made Course Files

Golf4us includes:
- `deerfield-course-data.json` - Deerfield CC (complete)
- More courses can be added by community

---

## 🎯 Tips for Accuracy

### GPS Coordinates
- ✅ Use clubhouse or first tee location
- ✅ Coordinates will be refined by Course Mapper
- ❌ Don't worry about exact precision initially

### Tee Box Data
- ✅ Enter all tee boxes you might use
- ✅ Get ratings from official sources
- ✅ Ratings affect handicap calculations

### Hole Data
- ✅ Double-check par values
- ✅ Verify stroke index matches scorecard
- ✅ Use yardages from your preferred tees
- ✅ GPS coordinates will be estimated (refine with Course Mapper)

### Verification
- ✅ Total par should equal course par (usually 70-72)
- ✅ Stroke index should use each number 1-18 once
- ✅ Yardages should be reasonable (par 3: 100-250, par 4: 250-500, par 5: 450-650)

---

## 🔧 Troubleshooting

### "Invalid JSON" Error
**Problem:** JSON format is incorrect

**Solution:**
- Use Scorecard Importer tool instead
- Or validate JSON at jsonlint.com
- Check for missing commas or brackets

### Course Not Appearing in GPS App
**Problem:** Course not showing up

**Solutions:**
1. Refresh GPS app page
2. Check localStorage in browser console
3. Re-import course data
4. Verify GPS coordinates are correct

### Wrong Yardages
**Problem:** Distances don't match scorecard

**Solutions:**
1. Verify you entered correct yardages
2. Check you're using correct tee box
3. Use Course Mapper to record actual GPS positions

### Missing Course Ratings
**Problem:** Don't have rating/slope data

**Solutions:**
1. Check course website
2. Call pro shop
3. Use USGA database
4. Estimate: Rating ≈ Par + 1-3, Slope ≈ 113-135

---

## 📱 After Import

### Test the Course
1. Open `gps-app.html`
2. Select your imported course
3. Verify hole data looks correct
4. Check distances are reasonable

### Refine with GPS
1. Take phone to course
2. Open `course-mapper.html`
3. Record actual tee and green positions
4. Re-import updated data

### Share with Friends
1. Export your database
2. Send JSON file
3. Friends import into their database
4. Everyone has accurate data!

---

## 🎓 Best Practices

### For Tournament Directors
1. Import course data before tournament
2. Share with all participants
3. Verify data is accurate
4. Have backup scorecards ready

### For Regular Players
1. Import your home course first
2. Add courses as you play them
3. Refine with Course Mapper over time
4. Share with regular playing partners

### For Golf Groups
1. Assign one person per course
2. Create shared folder for JSON files
3. Everyone imports all courses
4. Update when courses change

---

## 📚 Related Tools

- **scorecard-importer.html** - Import from scorecard (this tool)
- **course-database.html** - Manage all courses
- **course-mapper.html** - Record GPS coordinates
- **gps-app.html** - Use during play

---

## ✅ Checklist

Before importing:
- [ ] Have scorecard or course info
- [ ] Know GPS coordinates
- [ ] Have course ratings/slopes
- [ ] Have hole-by-hole data

After importing:
- [ ] Course appears in database
- [ ] GPS app shows course
- [ ] Hole data looks correct
- [ ] Exported backup JSON

---

## 🚀 Quick Reference

**Import from scorecard:** 15-20 minutes
```
scorecard-importer.html → Fill form → Add to Database
```

**Import from JSON:** 2 minutes
```
course-database.html → Import tab → Paste JSON → Import
```

**Refine with GPS:** 60 minutes (one-time)
```
course-mapper.html → Walk course → Export → Import
```

**Share with friends:** 2 minutes
```
course-database.html → Export → Send file
```

---

## 📞 Need Help?

1. Check HYBRID_DATA_APPROACH.md for system overview
2. Check QUICK_GPS_GUIDE.md for quick tips
3. Use gps-test.html to verify GPS working
4. Verify HTTPS connection for GPS features

**Happy importing! ⛳**