# Golf4us GPS - Quick Reference Guide

## 🚀 5-Minute Setup

### For Immediate Use (No Setup)
1. Open `public/gps-app.html` on your phone
2. Allow location access
3. Select course from nearby list
4. Start playing!

**Note:** Hole data will be estimated from OpenStreetMap

---

## 📱 The Three Tools

### 1. GPS App (`gps-app.html`)
**What it does:** Track your round with GPS  
**When to use:** During your round  
**Requires:** HTTPS, Location permission

**Quick actions:**
- View distance to green
- Record shots
- Track score
- See compass direction

### 2. Course Database (`course-database.html`)
**What it does:** Manage your course library  
**When to use:** Before/after rounds  
**Requires:** Any browser

**Quick actions:**
- Add new courses
- Import course data
- Export for backup
- Edit existing courses

### 3. Course Mapper (`course-mapper.html`)
**What it does:** Record accurate GPS data  
**When to use:** Walk the course once  
**Requires:** HTTPS, Location permission

**Quick actions:**
- Record tee boxes
- Record greens
- Enter hole details
- Export JSON

---

## 🎯 Common Tasks

### Task: Play a Round (Estimated Data)
1. Open `gps-app.html`
2. Allow location
3. Select course
4. Choose tee box
5. Play!

**Time:** 2 minutes  
**Accuracy:** ⭐⭐⭐ (Good)

### Task: Play with Accurate Data
**First time (one-time setup):**
1. Open `course-mapper.html` at the course
2. Walk each hole, record tee and green
3. Enter par, stroke index, yardage
4. Export JSON
5. Open `course-database.html`
6. Import JSON

**Every time after:**
1. Open `gps-app.html`
2. Select your mapped course
3. Play with accurate data!

**Setup time:** 60 minutes (one time)  
**Accuracy:** ⭐⭐⭐⭐⭐ (Perfect)

### Task: Share Course with Friends
1. Open `course-database.html`
2. Go to Export tab
3. Click "Download Database (JSON)"
4. Send file to friends
5. Friends import in their database

**Time:** 2 minutes

### Task: Backup Your Data
1. Open `course-database.html`
2. Go to Export tab
3. Click "Download Database (JSON)"
4. Save to Google Drive/Dropbox

**Time:** 1 minute  
**Frequency:** Monthly recommended

---

## 🔧 Troubleshooting

### GPS Not Working
**Problem:** "GPS Error" or "Permission Denied"

**Solutions:**
1. ✅ Check HTTPS (required for GPS)
2. ✅ Enable location in browser settings
3. ✅ Enable location services on device
4. ✅ Try `gps-test.html` to diagnose

### Course Not Found
**Problem:** Can't find my course

**Solutions:**
1. ✅ Check if within 5 miles
2. ✅ Add course manually to database
3. ✅ Verify GPS coordinates

### Inaccurate Distances
**Problem:** Yardages don't match scorecard

**Solutions:**
1. ✅ Use Course Mapper to record accurate data
2. ✅ Import into Course Database
3. ✅ Verify tee box and green coordinates

### Data Lost
**Problem:** My courses disappeared

**Solutions:**
1. ✅ Import from backup JSON file
2. ✅ Don't clear browser data
3. ✅ Export database regularly

---

## 📊 Data Accuracy Levels

| Method | Accuracy | Setup Time | Best For |
|--------|----------|------------|----------|
| OpenStreetMap Auto | ⭐⭐⭐ | 0 min | Discovering new courses |
| Manual Entry | ⭐⭐⭐⭐ | 15 min | Quick setup |
| Course Mapper | ⭐⭐⭐⭐⭐ | 60 min | Regular courses |
| Professional API | ⭐⭐⭐⭐⭐ | Instant | Many courses ($$$) |

---

## 💡 Pro Tips

### For Best Results
1. **Map your home course first** - Most important
2. **Export database monthly** - Backup protection
3. **Share with playing partners** - Build library together
4. **Test before tournament** - Verify everything works

### Battery Saving
1. Close other apps
2. Reduce screen brightness
3. Use airplane mode (after loading course)
4. Bring portable charger

### Accuracy Tips
1. Wait for GPS accuracy < 10m
2. Stand still when recording positions
3. Record from center of tee box
4. Record from center of green

---

## 📖 Full Documentation

- **HYBRID_DATA_APPROACH.md** - Complete system overview
- **GPS_GUIDE.md** - Technical GPS details
- **GOLF_DATA_SOURCES.md** - Data source comparison
- **HOSTING_OPTIONS.md** - Deployment guide
- **README.md** - Full project documentation

---

## ✅ Checklist for First Use

### Before Your Round
- [ ] Open `gps-app.html` on phone
- [ ] Test GPS with `gps-test.html`
- [ ] Add to home screen for easy access
- [ ] Charge phone fully
- [ ] Bring portable charger

### At the Course
- [ ] Allow location access
- [ ] Wait for GPS lock (< 10m accuracy)
- [ ] Select correct course
- [ ] Choose correct tee box
- [ ] Verify hole #1 information

### After Your Round
- [ ] Review shot history
- [ ] Export scores if needed
- [ ] Consider mapping course for next time

---

## 🎓 Learning Path

### Beginner (Day 1)
1. Open `gps-app.html`
2. Play one round with estimated data
3. Learn the interface

### Intermediate (Week 1)
1. Add home course to database manually
2. Use Course Mapper on one hole
3. Import into database

### Advanced (Month 1)
1. Map entire home course
2. Share with friends
3. Build course library
4. Set up regular backups

---

## 📞 Quick Help

### Can't find a file?
All files are in the `public/` directory:
- `public/gps-app.html`
- `public/course-database.html`
- `public/course-mapper.html`
- `public/gps-test.html`

### Need HTTPS?
See `HOSTING_OPTIONS.md` for free hosting:
- GitHub Pages
- Vercel
- Netlify
- Firebase

### Want accurate data?
Three options:
1. Use Course Mapper (free, 60 min)
2. Manual entry from scorecard (free, 15 min)
3. Professional API (paid, instant)

---

## 🎯 Success Metrics

**You're ready when:**
- ✅ GPS app opens and gets location
- ✅ Can see nearby courses
- ✅ Distance to green updates in real-time
- ✅ Can record shots
- ✅ Data persists between sessions

**You're advanced when:**
- ✅ Home course fully mapped
- ✅ Regular backup routine
- ✅ Sharing courses with friends
- ✅ Multiple courses in database
- ✅ Using offline at course

---

## 🚀 Next Steps

1. **Try it now:** Open `gps-app.html` and test
2. **Map one course:** Use Course Mapper this weekend
3. **Share:** Send this guide to playing partners
4. **Backup:** Export database today
5. **Explore:** Read full documentation

**Happy golfing! ⛳**