# Golf4us - Hybrid Course Data Approach

## Overview

Golf4us now uses a **hybrid approach** for golf course data, combining multiple sources to provide the best possible experience:

1. **Custom Course Database** - Manually mapped courses with accurate hole data
2. **OpenStreetMap** - Dynamic course discovery based on GPS location
3. **USGA Database** - Course ratings and slope information
4. **Manual Mapping Tool** - Create your own accurate course data

This approach gives you accurate data for courses you play regularly while still discovering new courses automatically.

---

## 🎯 How It Works

### Data Priority System

When you use the GPS app, it loads courses in this order:

1. **Custom Courses** (from Course Database Manager) - Highest priority
2. **OpenStreetMap Courses** (dynamically discovered) - Medium priority
3. **Fallback Courses** (pre-configured popular courses) - Lowest priority

Custom courses with accurate hole data will always be used first if available.

---

## 📱 Tools Included

### 1. GPS App (`gps-app.html`)
**Main tournament tracking application**

- Real-time GPS tracking during play
- Distance to green calculations
- Shot recording and statistics
- Automatic course detection
- Works with all data sources

**How to use:**
1. Open in mobile browser (HTTPS required)
2. Allow location access
3. Select your course from nearby options
4. Choose tee box
5. Start playing!

### 2. Course Database Manager (`course-database.html`)
**Manage your custom course library**

Features:
- ➕ Add courses manually with scorecard data
- 📥 Import courses from JSON files
- 📋 View all saved courses
- ✏️ Edit existing courses
- 🗑️ Delete courses
- 💾 Export database for backup
- 📱 Export for GPS app integration

**How to use:**
1. Open `course-database.html` in any browser
2. Add courses using the manual entry form
3. Or import from Course Mapper tool
4. Data saves automatically to browser localStorage
5. GPS app will automatically load your custom courses

### 3. Course Mapper (`course-mapper.html`)
**Walk the course and record accurate GPS data**

Features:
- Record tee box and green coordinates for each hole
- Enter par, stroke index, and yardage from scorecard
- Export as JSON for import into database
- Works offline after initial load

**How to use:**
1. Take your phone to the golf course
2. Open `course-mapper.html` in mobile browser
3. Walk to each tee box and tap "Record Tee Box"
4. Walk to each green and tap "Record Green"
5. Enter hole details (par, stroke index, yardage)
6. Export JSON when complete
7. Import into Course Database Manager

### 4. GPS Test Tool (`gps-test.html`)
**Verify GPS functionality**

- Check if GPS is working
- View current coordinates
- Test accuracy
- Troubleshoot location issues

---

## 🗺️ Data Sources Explained

### Custom Course Database (Recommended)
**Accuracy: ⭐⭐⭐⭐⭐ (Perfect)**

- Manually mapped courses with exact GPS coordinates
- Accurate par, yardage, and stroke index for each hole
- Multiple tee box support
- Stored locally in browser
- Works offline

**Best for:** Courses you play regularly

**How to get data:**
1. Use Course Mapper tool to walk the course
2. Enter data manually from scorecard
3. Import from other golfers who mapped the course

### OpenStreetMap (Automatic)
**Accuracy: ⭐⭐⭐ (Good for discovery)**

- Automatically discovers courses near your location
- Provides course name, location, and basic info
- Hole data is estimated if not available
- Free and open source
- Updates regularly

**Best for:** Discovering new courses, traveling

**Limitations:**
- Hole-by-hole data may be estimated
- Yardages may not match scorecard
- Tee box ratings are generic

### USGA Database (Future Enhancement)
**Accuracy: ⭐⭐⭐⭐ (Official ratings)**

- Official course ratings and slope
- Verified by USGA
- Updated annually
- Free to access

**Status:** Can be manually added to custom courses

**How to use:**
1. Look up course on USGA website
2. Add ratings to custom course entry

### Professional APIs (Optional - Paid)
**Accuracy: ⭐⭐⭐⭐⭐ (Perfect)**

If you need professional-grade data for many courses:

- **Golf Genius API**: $500-2000/month
- **Golfshot API**: $200-1000/month  
- **SwingU API**: $200-800/month

See `GOLF_DATA_SOURCES.md` for details.

---

## 📊 Comparison Table

| Data Source | Accuracy | Coverage | Cost | Offline | Setup Time |
|-------------|----------|----------|------|---------|------------|
| Custom Database | ⭐⭐⭐⭐⭐ | Your courses | Free | ✅ Yes | 30-60 min/course |
| OpenStreetMap | ⭐⭐⭐ | Worldwide | Free | ❌ No | Automatic |
| USGA Database | ⭐⭐⭐⭐ | US courses | Free | Manual | 5 min/course |
| Professional APIs | ⭐⭐⭐⭐⭐ | Worldwide | $200-2000/mo | ✅ Yes | Immediate |

---

## 🚀 Quick Start Guide

### For Casual Use (5 minutes)
1. Open `gps-app.html` on your phone
2. Allow location access
3. Select course from nearby list
4. Start playing!

**Note:** Hole data will be estimated from OpenStreetMap

### For Accurate Data (1 hour per course)
1. Open `course-mapper.html` on your phone
2. Walk the course and record GPS coordinates
3. Export JSON file
4. Open `course-database.html` on computer
5. Import JSON file
6. Use `gps-app.html` - your course now has accurate data!

### For Multiple Courses (Ongoing)
1. Map your home course first (most important)
2. Add courses as you play them
3. Share JSON files with playing partners
4. Build your course library over time

---

## 💾 Data Storage

### Where is data stored?
- **Browser localStorage** - All custom courses
- **24-hour cache** - OpenStreetMap results
- **No server** - Everything is local

### Data persistence
- ✅ Survives browser restart
- ✅ Survives phone restart
- ❌ Lost if browser data cleared
- ❌ Lost if browser uninstalled

### Backup recommendations
1. Export database monthly (`course-database.html` → Export tab)
2. Save JSON files to cloud storage (Google Drive, Dropbox)
3. Share with friends for redundancy

---

## 🔧 Advanced Features

### Multiple Tee Boxes
Custom courses support multiple tee boxes with different:
- Total yardage
- Course rating
- Slope rating

Example:
```json
{
  "teeBoxes": {
    "blue": { "totalYards": 6650, "rating": 72.8, "slope": 131 },
    "white": { "totalYards": 6250, "rating": 70.5, "slope": 125 },
    "gold": { "totalYards": 5750, "rating": 68.0, "slope": 117 },
    "red": { "totalYards": 5100, "rating": 65.8, "slope": 112 }
  }
}
```

### Hole Data Format
Each hole includes:
```json
{
  "number": 1,
  "par": 5,
  "strokeIndex": 1,
  "yardage": 520,
  "teeBox": { "lat": 43.1234, "lon": -77.5678 },
  "green": { "lat": 43.1240, "lon": -77.5670 }
}
```

### Course Detection
GPS app automatically:
1. Finds courses within 5 miles
2. Sorts by distance
3. Shows nearest courses first
4. Detects which hole you're on based on tee box proximity

---

## 🤝 Sharing Course Data

### Export for sharing
1. Open `course-database.html`
2. Go to Export tab
3. Click "Download Database (JSON)"
4. Share file with friends

### Import shared data
1. Receive JSON file from friend
2. Open `course-database.html`
3. Go to Import tab
4. Paste JSON content
5. Click Import

### Community building
Consider creating a shared repository:
- Google Drive folder for your golf group
- GitHub repository for public courses
- Discord/Slack channel for sharing

---

## 📱 Mobile Setup

### iOS (Safari)
1. Open `gps-app.html` in Safari
2. Tap Share button
3. Select "Add to Home Screen"
4. App icon appears on home screen
5. Opens like native app

### Android (Chrome)
1. Open `gps-app.html` in Chrome
2. Tap menu (⋮)
3. Select "Add to Home Screen"
4. App icon appears on home screen
5. Opens like native app

### Requirements
- HTTPS connection (required for GPS)
- Location permission enabled
- Modern browser (Safari 11+, Chrome 50+)

---

## 🐛 Troubleshooting

### GPS not working
1. Check HTTPS connection (required)
2. Enable location in browser settings
3. Enable location services on device
4. Try `gps-test.html` to diagnose

### Course not found
1. Check if within 5 miles of course
2. Add course manually to database
3. Verify GPS coordinates are correct

### Inaccurate hole data
1. Use Course Mapper to record accurate data
2. Import into Course Database Manager
3. Verify tee box and green coordinates

### Data lost
1. Export database regularly
2. Don't clear browser data
3. Keep backup JSON files

---

## 🎓 Best Practices

### For Tournament Directors
1. Map your course before tournament
2. Share course data with participants
3. Test GPS app at course beforehand
4. Have backup scorecards ready

### For Regular Players
1. Map your home course first
2. Add courses as you travel
3. Share data with regular playing partners
4. Export database monthly

### For Golf Groups
1. Designate one person to map each course
2. Create shared Google Drive folder
3. Import all courses into each member's database
4. Update when courses change

---

## 🔮 Future Enhancements

### Planned Features
- [ ] Cloud sync for course database
- [ ] Course sharing marketplace
- [ ] Automatic USGA rating lookup
- [ ] Integration with professional APIs
- [ ] Course condition notes
- [ ] Weather integration
- [ ] Scorecard photos

### Community Contributions
Want to help? Consider:
- Mapping popular courses
- Sharing course data
- Testing on different devices
- Reporting bugs
- Suggesting features

---

## 📞 Support

### Documentation
- `README.md` - Main project documentation
- `GPS_GUIDE.md` - GPS feature details
- `GOLF_DATA_SOURCES.md` - Data source comparison
- `HOSTING_OPTIONS.md` - Deployment guide

### Getting Help
1. Check documentation first
2. Test with `gps-test.html`
3. Verify browser compatibility
4. Check HTTPS requirement

---

## ✅ Summary

**You now have a complete golf course data system that:**

✅ Works with accurate custom data when available  
✅ Automatically discovers new courses via OpenStreetMap  
✅ Allows manual mapping for perfect accuracy  
✅ Stores everything locally (no server needed)  
✅ Works offline after initial setup  
✅ Supports multiple tee boxes  
✅ Includes all necessary tools  
✅ Can be enhanced with paid APIs if needed  

**Start with the GPS app, add custom courses as needed, and enjoy accurate golf tracking!**